
USE project;

SELECT
    assets.total_assets,
    liabilities.total_liabilities,
    equity.opening_equity,
    profit.current_year_net_profit,

    equity.opening_equity
        + profit.current_year_net_profit
        AS total_equity,

    liabilities.total_liabilities
        + equity.opening_equity
        + profit.current_year_net_profit
        AS liabilities_plus_equity,

    ROUND(
        assets.total_assets
        - liabilities.total_liabilities
        - equity.opening_equity
        - profit.current_year_net_profit,
        2
    ) AS balance_check

FROM
(
    SELECT
        ROUND(SUM(
            CASE
                WHEN account_code IN (1000, 1100, 1200)
                THEN debit - credit
                ELSE 0
            END
        ), 2) AS total_assets
    FROM general_ledger
    WHERE transaction_date < '2026-01-01'
) AS assets

CROSS JOIN
(
    SELECT
        ROUND(SUM(
            CASE
                WHEN account_code IN (2000, 2100)
                THEN credit - debit
                ELSE 0
            END
        ), 2) AS total_liabilities
    FROM general_ledger
    WHERE transaction_date < '2026-01-01'
) AS liabilities

CROSS JOIN
(
    SELECT
        ROUND(SUM(
            CASE
                WHEN account_code = 3000
                THEN credit - debit
                ELSE 0
            END
        ), 2) AS opening_equity
    FROM general_ledger
    WHERE transaction_date < '2026-01-01'
) AS equity

CROSS JOIN
(
    SELECT
        ROUND(
            SUM(CASE
                WHEN account_code IN (4000, 4100)
                THEN credit - debit ELSE 0
            END)
            -
            SUM(CASE
                WHEN account_code IN
                    (5000, 5100, 5200, 5300, 5400, 5500)
                THEN debit - credit ELSE 0
            END),
            2
        ) AS current_year_net_profit
    FROM general_ledger
    WHERE transaction_date >= '2025-01-01'
      AND transaction_date < '2026-01-01'
) AS profit;
