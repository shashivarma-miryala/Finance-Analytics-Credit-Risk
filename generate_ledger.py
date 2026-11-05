"""
DA-04 | Synthetic company ledger generator (Faker + NumPy)

Creates a fictional consumer-lending company ("Nexvia Credit Ltd") with 24 months
of data (Jan 2024 - Dec 2025):
  accounts.csv         chart of accounts (P&L)
  gl_transactions.csv  transaction-level ledger (actuals), by region
  budget_monthly.csv   monthly budget by account and region
  drivers_monthly.csv  budget vs actual business drivers (for variance analysis)
  bs_monthly.csv       month-end balance sheet (actuals)

Assumptions (document these in your report):
  * Everything is synthetic and generated with a fixed seed (reproducible).
  * Revenue and expense amounts are stored as positive numbers; the account
    category tells you whether it adds to or reduces profit.
  * Income tax = 25% of pre-tax profit each month (a loss gives a tax credit).
  * Cash on the balance sheet is the balancing figure.
Run:  python generate_ledger.py
"""
import os
import numpy as np
import pandas as pd
from faker import Faker

SEED = 42
rng = np.random.default_rng(SEED)
fake = Faker()
Faker.seed(SEED)

OUT = os.path.join("data", "synthetic")
os.makedirs(OUT, exist_ok=True)

MONTHS = [str(p) for p in pd.period_range("2024-01", "2025-12", freq="M")]
N = len(MONTHS)
REGIONS = ["North", "South", "East", "West"]
REGION_W = np.array([0.30, 0.25, 0.25, 0.20])

# ------------------------------------------------------------------ chart of accounts
ACCOUNTS = [
    (4000, "Interest Income",           "Revenue"),
    (4100, "Fee Income",                "Revenue"),
    (5000, "Interest Expense",          "Cost of Funds"),
    (5100, "Provision for Loan Losses", "Credit Cost"),
    (6000, "Salaries & Benefits",       "Operating Expense"),
    (6100, "Marketing",                 "Operating Expense"),
    (6200, "Technology",                "Operating Expense"),
    (6300, "Rent & Facilities",         "Operating Expense"),
    (6400, "Professional Fees",         "Operating Expense"),
    (6500, "Other Operating Expenses",  "Operating Expense"),
    (7000, "Income Tax",                "Tax"),
]
accounts = pd.DataFrame(ACCOUNTS, columns=["account_code", "account_name", "category"])

# ------------------------------------------------------------------ BUDGET drivers
OPEN_LOANS = 200e6
G_BUD = 0.012                       # budgeted monthly portfolio growth
BUD_YIELD, BUD_COF, BUD_PROV = 0.135, 0.065, 0.030
FEE_RATE, BORROW_RATIO, TAX_RATE = 0.02, 0.78, 0.25
SAL_PER_HEAD = 7000

bud_end = np.array([OPEN_LOANS * (1 + G_BUD) ** (i + 1) for i in range(N)])
bud_open = np.concatenate([[OPEN_LOANS], bud_end[:-1]])
bud_avg = (bud_open + bud_end) / 2
bud_orig = bud_open * 0.07
bud_hc = 60 + np.arange(N) // 4

# ------------------------------------------------------------------ ACTUAL drivers (with realistic "stories")
idx = np.arange(N)
vol_factor = 1 + rng.normal(0, 0.04, N)
vol_factor[6:9] -= 0.10             # Jul-Sep 2024 weak demand
vol_factor[18:21] += 0.06           # Jul-Sep 2025 strong demand
act_orig = bud_orig * vol_factor

act_end = np.zeros(N)
prev = OPEN_LOANS
for i in range(N):
    growth = G_BUD + (act_orig[i] / bud_orig[i] - 1) * 0.25 + rng.normal(0, 0.002)
    act_end[i] = prev * (1 + growth)
    prev = act_end[i]
act_open = np.concatenate([[OPEN_LOANS], act_end[:-1]])
act_avg = (act_open + act_end) / 2

act_yield = BUD_YIELD + rng.normal(0, 0.0015, N) - 0.0015 * (idx >= 12)   # pricing pressure in 2025
act_cof = BUD_COF + 0.00025 * idx + rng.normal(0, 0.0005, N)               # rising funding cost
act_prov = BUD_PROV + rng.normal(0, 0.0015, N)
act_prov[14:20] += 0.008                                                   # credit deterioration Mar-Aug 2025
act_hc = bud_hc + rng.integers(-1, 2, N)
act_hc[12:] -= 2                                                           # vacancies in 2025
act_sal_head = SAL_PER_HEAD * (1 + 0.03 * (idx >= 12))                     # pay rise in 2025


def seasonal_marketing(i):
    return 1.30 if (i % 12) >= 9 else 1.0   # Q4 campaign uplift


# ------------------------------------------------------------------ monthly totals: BUDGET and ACTUAL
bud, act = {}, {}
bud_borrow_avg = BORROW_RATIO * bud_avg
act_borrow_end = BORROW_RATIO * act_end
act_borrow_open = BORROW_RATIO * act_open
act_borrow_avg = (act_borrow_open + act_borrow_end) / 2

bud[4000] = bud_avg * BUD_YIELD / 12
act[4000] = act_avg * act_yield / 12
bud[4100] = bud_orig * FEE_RATE
act[4100] = act_orig * FEE_RATE * (1 + rng.normal(0, 0.03, N))
bud[5000] = bud_borrow_avg * BUD_COF / 12
act[5000] = act_borrow_avg * act_cof / 12
bud[5100] = bud_avg * BUD_PROV / 12
act[5100] = act_avg * act_prov / 12
bud[6000] = bud_hc * SAL_PER_HEAD
act[6000] = act_hc * act_sal_head
bud[6100] = np.array([130_000 * seasonal_marketing(i) for i in range(N)])
act[6100] = bud[6100] * (1 + rng.normal(0, 0.05, N))
act[6100][9:12] *= 1.25                                                    # Q4 2024 overspend
bud[6200] = np.full(N, 95_000.0)
act[6200] = bud[6200] * (1 + rng.normal(0, 0.04, N)) * np.where(idx >= 13, 1.15, 1.0)  # new platform from Feb 2025
bud[6300] = np.full(N, 45_000.0)
act[6300] = np.full(N, 45_000.0)
bud[6400] = np.full(N, 32_000.0)
act[6400] = bud[6400] * (1 + rng.normal(0, 0.12, N))
act[6400][17] *= 2.3                                                       # annual audit, Jun 2025
bud[6500] = np.full(N, 38_000.0)
act[6500] = bud[6500] * (1 + rng.normal(0, 0.08, N))

for d in (bud, act):
    pretax = d[4000] + d[4100] - d[5000] - d[5100] - sum(d[c] for c in (6000, 6100, 6200, 6300, 6400, 6500))
    d[7000] = TAX_RATE * pretax
    d["pretax"] = pretax

# ------------------------------------------------------------------ budget table (by region)
rows = []
for code in accounts["account_code"]:
    for i, m in enumerate(MONTHS):
        for r, w in zip(REGIONS, REGION_W):
            rows.append((m, code, r, round(bud[code][i] * w, 2)))
budget_df = pd.DataFrame(rows, columns=["month", "account_code", "region", "budget_amount"])

# ------------------------------------------------------------------ transaction-level actuals (Faker)
LEDGER_TEXT = {
    4000: ("Loan portfolio", "Interest accrued on loan book"),
    4100: ("Loan portfolio", "Origination and servicing fees"),
    5000: (None, "Interest on wholesale borrowing"),
    5100: ("Credit risk model", "Expected credit loss provision"),
    6000: ("Payroll", "Payroll run"),
    6100: (None, "Marketing campaign invoice"),
    6200: (None, "Software / cloud invoice"),
    6300: (None, "Office rent and utilities"),
    6400: (None, "Professional services invoice"),
    6500: (None, "General operating expense"),
    7000: ("Tax authority", "Income tax provision"),
}
N_TXN = {4000: 4, 4100: 4, 5000: 2, 5100: 1, 6000: 2, 6100: 5, 6200: 4, 6300: 1, 6400: 3, 6500: 6, 7000: 1}

txn_rows, tid = [], 1
for i, m in enumerate(MONTHS):
    year, mon = int(m[:4]), int(m[5:])
    days = pd.Period(m).days_in_month
    for code in accounts["account_code"]:
        wj = REGION_W * (1 + rng.normal(0, 0.03, 4))
        wj = wj / wj.sum()
        for r, w in zip(REGIONS, wj):
            total = round(float(act[code][i] * w), 2)
            k = N_TXN[code]
            shares = rng.dirichlet(np.ones(k)) if k > 1 else np.array([1.0])
            amts = np.round(total * shares, 2)
            amts[-1] = round(total - amts[:-1].sum(), 2)          # make the split add up exactly
            fixed, desc = LEDGER_TEXT[code]
            for a in amts:
                party = fixed if fixed else fake.company()
                d = pd.Timestamp(year, mon, int(rng.integers(1, days + 1)))
                txn_rows.append((tid, d.date().isoformat(), m, code, r, party, desc, float(a)))
                tid += 1
gl = pd.DataFrame(txn_rows, columns=["txn_id", "txn_date", "month", "account_code", "region",
                                     "counterparty", "description", "amount"])

# ------------------------------------------------------------------ balance sheet (actuals, month-end)
act_net_income = act["pretax"] - act[7000]
opex_total = sum(act[c] for c in (6000, 6100, 6200, 6300, 6400, 6500))

allowance = np.zeros(N)
prev_allow = 0.03 * OPEN_LOANS
for i in range(N):
    writeoff = 0.95 * BUD_PROV / 12 * act_avg[i]                       # steady write-off run-rate
    allowance[i] = prev_allow + act[5100][i] - writeoff
    prev_allow = allowance[i]

SHARE_CAPITAL, OPEN_RE, OTHER_ASSETS = 45e6, 12e6, 6e6
retained = OPEN_RE + np.cumsum(act_net_income)
accrued = 1.5 * opex_total
tax_payable = np.maximum(act[7000], 0)
borrowings = act_borrow_end

total_le = borrowings + accrued + tax_payable + SHARE_CAPITAL + retained
cash = total_le - (act_end - allowance + OTHER_ASSETS)

bs_rows = []
for i, m in enumerate(MONTHS):
    items = [
        ("1000", "Cash",                       "Assets",      cash[i]),
        ("1100", "Gross Loans Receivable",     "Assets",      act_end[i]),
        ("1150", "Allowance for Loan Losses",  "Assets",      -allowance[i]),
        ("1200", "Other Assets",               "Assets",      OTHER_ASSETS),
        ("2000", "Borrowings",                 "Liabilities", borrowings[i]),
        ("2100", "Accrued Liabilities",        "Liabilities", accrued[i]),
        ("2200", "Taxes Payable",              "Liabilities", tax_payable[i]),
        ("3000", "Share Capital",              "Equity",      SHARE_CAPITAL),
        ("3100", "Retained Earnings",          "Equity",      retained[i]),
    ]
    for code, name, section, bal in items:
        bs_rows.append((m, code, name, section, round(float(bal), 2)))
bs = pd.DataFrame(bs_rows, columns=["month", "bs_code", "bs_name", "section", "balance"])

# ------------------------------------------------------------------ drivers table
drivers = pd.DataFrame({
    "month": MONTHS,
    "avg_gross_loans_budget": bud_avg.round(0), "avg_gross_loans_actual": act_avg.round(0),
    "originations_budget": bud_orig.round(0),   "originations_actual": act_orig.round(0),
    "portfolio_yield_budget": BUD_YIELD,        "portfolio_yield_actual": act_yield.round(5),
    "cost_of_funds_budget": BUD_COF,            "cost_of_funds_actual": act_cof.round(5),
    "provision_rate_budget": BUD_PROV,          "provision_rate_actual": act_prov.round(5),
    "headcount_budget": bud_hc,                 "headcount_actual": act_hc,
    "salary_per_head_budget": SAL_PER_HEAD,     "salary_per_head_actual": act_sal_head.round(0),
})

# ------------------------------------------------------------------ checks
chk = bs.pivot_table(index="month", columns="section", values="balance", aggfunc="sum")
assert np.allclose(chk["Assets"], chk["Liabilities"] + chk["Equity"], atol=1.0), "Balance sheet does not balance"
assert (cash > 0).all(), "Cash went negative - raise SHARE_CAPITAL"
assert (allowance > 0).all(), "Allowance went negative"
gl_tot = gl.groupby(["month", "account_code"])["amount"].sum().round(2)
exp_tot = pd.Series({(m, c): round(float(act[c][i]), 2) for i, m in enumerate(MONTHS) for c in accounts["account_code"]})
assert (gl_tot.sub(exp_tot.reindex(gl_tot.index)).abs() < 0.05).all(), "Ledger does not match monthly totals"

# ------------------------------------------------------------------ save
accounts.to_csv(f"{OUT}/accounts.csv", index=False)
gl.to_csv(f"{OUT}/gl_transactions.csv", index=False)
budget_df.to_csv(f"{OUT}/budget_monthly.csv", index=False)
drivers.to_csv(f"{OUT}/drivers_monthly.csv", index=False)
bs.to_csv(f"{OUT}/bs_monthly.csv", index=False)

print("Saved to", OUT)
print("gl_transactions rows:", len(gl))
print("Balance sheet balances for all", N, "months. Min cash: %.1fM" % (cash.min() / 1e6))
print("Total 2024 net income: %.2fM | 2025: %.2fM" % (act_net_income[:12].sum() / 1e6, act_net_income[12:].sum() / 1e6))
print("Budget 2024 net income: %.2fM | 2025: %.2fM" % (((bud["pretax"] - bud[7000])[:12].sum()) / 1e6, ((bud["pretax"] - bud[7000])[12:].sum()) / 1e6))
