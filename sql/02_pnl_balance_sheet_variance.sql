-- DA-04 | Steps 2-3: P&L, balance sheet, budget vs actual, variance drivers
-- Run after 01_create_and_load_mysql.sql (works in MySQL 8; also tested in SQLite).
-- Sign convention: all amounts are positive in the ledger; the account CATEGORY decides
-- whether an amount adds to profit (Revenue) or reduces it (everything else).

-- =========================== VIEWS ===========================

-- 1) Actuals by account and month
DROP VIEW IF EXISTS v_pnl_account_month;
CREATE VIEW v_pnl_account_month AS
SELECT t.month, t.account_code, a.account_name, a.category,
       ROUND(SUM(t.amount), 2) AS actual
FROM gl_transactions t
JOIN accounts a ON a.account_code = t.account_code
GROUP BY t.month, t.account_code, a.account_name, a.category;

-- 2) Monthly P&L summary
DROP VIEW IF EXISTS v_pnl_monthly;
CREATE VIEW v_pnl_monthly AS
SELECT s.*, ROUND(s.pretax_profit - s.income_tax, 2) AS net_income
FROM (
  SELECT month,
    SUM(CASE WHEN category = 'Revenue'           THEN actual ELSE 0 END) AS total_revenue,
    SUM(CASE WHEN category = 'Cost of Funds'     THEN actual ELSE 0 END) AS interest_expense,
    SUM(CASE WHEN category = 'Credit Cost'       THEN actual ELSE 0 END) AS provision,
    SUM(CASE WHEN category = 'Operating Expense' THEN actual ELSE 0 END) AS operating_expense,
    SUM(CASE WHEN category = 'Revenue' THEN actual
             WHEN category IN ('Cost of Funds','Credit Cost','Operating Expense') THEN -actual
             ELSE 0 END) AS pretax_profit,
    SUM(CASE WHEN category = 'Tax'               THEN actual ELSE 0 END) AS income_tax
  FROM v_pnl_account_month
  GROUP BY month
) s;

-- 3) Balance sheet summary with an accounting check (check_diff must be 0.00)
DROP VIEW IF EXISTS v_bs_summary;
CREATE VIEW v_bs_summary AS
SELECT s.*, ROUND(s.total_assets - s.total_liabilities - s.total_equity, 2) AS check_diff
FROM (
  SELECT month,
    SUM(CASE WHEN section = 'Assets'      THEN balance ELSE 0 END) AS total_assets,
    SUM(CASE WHEN section = 'Liabilities' THEN balance ELSE 0 END) AS total_liabilities,
    SUM(CASE WHEN section = 'Equity'      THEN balance ELSE 0 END) AS total_equity
  FROM bs_monthly
  GROUP BY month
) s;

-- 4) Budget vs actual by account and month
--    variance_fav > 0 means FAVOURABLE (more revenue than planned, or less cost than planned)
DROP VIEW IF EXISTS v_budget_vs_actual;
CREATE VIEW v_budget_vs_actual AS
SELECT a.month, a.account_code, a.account_name, a.category,
       a.actual, b.budget,
       ROUND(CASE WHEN a.category = 'Revenue' THEN a.actual - b.budget
                  ELSE b.budget - a.actual END, 2) AS variance_fav,
       ROUND(100 * CASE WHEN a.category = 'Revenue' THEN a.actual - b.budget
                        ELSE b.budget - a.actual END / b.budget, 1) AS variance_pct
FROM v_pnl_account_month a
JOIN (SELECT month, account_code, SUM(budget_amount) AS budget
      FROM budget_monthly GROUP BY month, account_code) b
  ON b.month = a.month AND b.account_code = a.account_code;

-- =========================== QUERIES ===========================

-- Q1. Monthly P&L
SELECT * FROM v_pnl_monthly ORDER BY month;

-- Q2. Annual P&L
SELECT SUBSTR(month, 1, 4) AS year,
       ROUND(SUM(total_revenue), 0)     AS revenue,
       ROUND(SUM(interest_expense), 0)  AS interest_expense,
       ROUND(SUM(provision), 0)         AS provision,
       ROUND(SUM(operating_expense), 0) AS opex,
       ROUND(SUM(pretax_profit), 0)     AS pretax_profit,
       ROUND(SUM(net_income), 0)        AS net_income
FROM v_pnl_monthly
GROUP BY SUBSTR(month, 1, 4);

-- Q3. Balance sheet at each year-end, plus the balancing check for all months
SELECT * FROM v_bs_summary ORDER BY month;
SELECT month, bs_name, balance FROM bs_monthly WHERE month IN ('2024-12', '2025-12') ORDER BY month, bs_code;

-- Q4. Full-year budget vs actual by account (2025)
SELECT account_name,
       ROUND(SUM(actual), 0)       AS actual,
       ROUND(SUM(budget), 0)       AS budget,
       ROUND(SUM(variance_fav), 0) AS variance_fav,
       ROUND(100 * SUM(variance_fav) / SUM(budget), 1) AS variance_pct
FROM v_budget_vs_actual
WHERE month LIKE '2025-%'
GROUP BY account_code, account_name
ORDER BY variance_fav;

-- Q5. Net income: budget vs actual by month
SELECT p.month, p.net_income AS actual_net_income,
       ROUND(b.pretax_budget * 0.75, 2) AS budget_net_income,
       ROUND(p.net_income - b.pretax_budget * 0.75, 2) AS variance
FROM v_pnl_monthly p
JOIN (SELECT month,
             SUM(CASE WHEN category = 'Revenue' THEN budget
                      WHEN category IN ('Cost of Funds','Credit Cost','Operating Expense') THEN -budget
                      ELSE 0 END) AS pretax_budget
      FROM v_budget_vs_actual GROUP BY month) b ON b.month = p.month
ORDER BY p.month;

-- Q6. Variance DRIVERS (price / volume bridges). The last column is rounding only.
--     Interest income: volume = bigger or smaller loan book, rate = yield earned on it
--     Provision: volume = loan book, rate = provision rate (credit quality)
--     Salaries: volume = headcount, rate = cost per head
SELECT SUBSTR(d.month, 1, 4) AS year,
       ROUND(SUM((d.avg_gross_loans_actual - d.avg_gross_loans_budget) * d.portfolio_yield_budget / 12), 0) AS int_income_volume_effect,
       ROUND(SUM((d.portfolio_yield_actual - d.portfolio_yield_budget) * d.avg_gross_loans_actual / 12), 0) AS int_income_rate_effect,
       ROUND(SUM(v.variance_fav) - SUM((d.avg_gross_loans_actual - d.avg_gross_loans_budget) * d.portfolio_yield_budget / 12)
                                 - SUM((d.portfolio_yield_actual - d.portfolio_yield_budget) * d.avg_gross_loans_actual / 12), 0) AS rounding_residual
FROM drivers_monthly d
JOIN v_budget_vs_actual v ON v.month = d.month AND v.account_code = 4000
GROUP BY SUBSTR(d.month, 1, 4);

SELECT SUBSTR(d.month, 1, 4) AS year,
       ROUND(-SUM((d.avg_gross_loans_actual - d.avg_gross_loans_budget) * d.provision_rate_budget / 12), 0) AS provision_volume_effect,
       ROUND(-SUM((d.provision_rate_actual - d.provision_rate_budget) * d.avg_gross_loans_actual / 12), 0) AS provision_rate_effect
FROM drivers_monthly d
GROUP BY SUBSTR(d.month, 1, 4);

SELECT SUBSTR(d.month, 1, 4) AS year,
       ROUND(-SUM((d.headcount_actual - d.headcount_budget) * d.salary_per_head_budget), 0) AS salary_headcount_effect,
       ROUND(-SUM(d.headcount_actual * (d.salary_per_head_actual - d.salary_per_head_budget)), 0) AS salary_rate_effect
FROM drivers_monthly d
GROUP BY SUBSTR(d.month, 1, 4);

-- Q7. Regional net contribution before tax (2025)
SELECT t.region,
       ROUND(SUM(CASE WHEN a.category = 'Revenue' THEN t.amount
                      WHEN a.category IN ('Cost of Funds','Credit Cost','Operating Expense') THEN -t.amount
                      ELSE 0 END), 0) AS pretax_profit
FROM gl_transactions t
JOIN accounts a ON a.account_code = t.account_code
WHERE t.month LIKE '2025-%'
GROUP BY t.region
ORDER BY pretax_profit DESC;
