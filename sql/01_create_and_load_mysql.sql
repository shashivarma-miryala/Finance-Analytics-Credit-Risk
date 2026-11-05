-- DA-04 | Step 1: create the database and load the synthetic ledger (MySQL 8 / Workbench)
-- Change the folder in each LOAD DATA line to where your CSV files are (use forward slashes).
-- If you get a local_infile error:  SET GLOBAL local_infile = 1;  and add OPT_LOCAL_INFILE=1
-- under Connection > Advanced > Others.

CREATE DATABASE IF NOT EXISTS da04_finance;
USE da04_finance;

DROP TABLE IF EXISTS gl_transactions;
DROP TABLE IF EXISTS budget_monthly;
DROP TABLE IF EXISTS bs_monthly;
DROP TABLE IF EXISTS drivers_monthly;
DROP TABLE IF EXISTS accounts;

CREATE TABLE accounts (
  account_code INT PRIMARY KEY,
  account_name VARCHAR(60),
  category     VARCHAR(30)
);

CREATE TABLE gl_transactions (
  txn_id       INT PRIMARY KEY,
  txn_date     DATE,
  month        CHAR(7),
  account_code INT,
  region       VARCHAR(10),
  counterparty VARCHAR(120),
  description  VARCHAR(120),
  amount       DECIMAL(14,2),
  FOREIGN KEY (account_code) REFERENCES accounts(account_code)
);

CREATE TABLE budget_monthly (
  month         CHAR(7),
  account_code  INT,
  region        VARCHAR(10),
  budget_amount DECIMAL(14,2)
);

CREATE TABLE bs_monthly (
  month   CHAR(7),
  bs_code VARCHAR(6),
  bs_name VARCHAR(40),
  section VARCHAR(12),
  balance DECIMAL(16,2)
);

CREATE TABLE drivers_monthly (
  month                    CHAR(7),
  avg_gross_loans_budget   DECIMAL(16,0),
  avg_gross_loans_actual   DECIMAL(16,0),
  originations_budget      DECIMAL(16,0),
  originations_actual      DECIMAL(16,0),
  portfolio_yield_budget   DECIMAL(8,5),
  portfolio_yield_actual   DECIMAL(8,5),
  cost_of_funds_budget     DECIMAL(8,5),
  cost_of_funds_actual     DECIMAL(8,5),
  provision_rate_budget    DECIMAL(8,5),
  provision_rate_actual    DECIMAL(8,5),
  headcount_budget         INT,
  headcount_actual         INT,
  salary_per_head_budget   DECIMAL(10,0),
  salary_per_head_actual   DECIMAL(10,0)
);

LOAD DATA LOCAL INFILE 'D:/DA-04/data/synthetic/accounts.csv' INTO TABLE accounts
  FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS;
LOAD DATA LOCAL INFILE 'D:/DA-04/data/synthetic/gl_transactions.csv' INTO TABLE gl_transactions
  FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS;
LOAD DATA LOCAL INFILE 'D:/DA-04/data/synthetic/budget_monthly.csv' INTO TABLE budget_monthly
  FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS;
LOAD DATA LOCAL INFILE 'D:/DA-04/data/synthetic/bs_monthly.csv' INTO TABLE bs_monthly
  FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS;
LOAD DATA LOCAL INFILE 'D:/DA-04/data/synthetic/drivers_monthly.csv' INTO TABLE drivers_monthly
  FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS;

-- Row-count check (expected: 11, 3168, 1056, 216, 24)
SELECT 'accounts' t, COUNT(*) n FROM accounts UNION ALL
SELECT 'gl_transactions', COUNT(*) FROM gl_transactions UNION ALL
SELECT 'budget_monthly', COUNT(*) FROM budget_monthly UNION ALL
SELECT 'bs_monthly', COUNT(*) FROM bs_monthly UNION ALL
SELECT 'drivers_monthly', COUNT(*) FROM drivers_monthly;
