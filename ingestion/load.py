"""Load the REAL UCI "Default of Credit Card Clients" file into DuckDB bronze, unchanged except for column names.

Source: Yeh, I.-C. (2009). Default of Credit Card Clients [Dataset]. UCI Machine Learning Repository.
https://doi.org/10.24432/C55S3H (CC BY 4.0). 30,000 credit card holders in Taiwan, April to September 2005: credit
limit, demographics, six months of repayment status, bill and payment amounts (NT$), and whether they defaulted.

Usage: python ingestion/load.py --zip data/raw/dccc.zip --db warehouse/credit.duckdb
"""
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

import duckdb
import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zip", type=Path, default=Path("data/raw/dccc.zip"))
    ap.add_argument("--db", default="warehouse/credit.duckdb")
    args = ap.parse_args()
    with zipfile.ZipFile(args.zip) as z:
        name = next(n for n in z.namelist() if n.endswith(".xls"))
        df = pd.read_excel(z.open(name), header=1, engine="xlrd")
    df = df.rename(columns={"default payment next month": "DEFAULT_NEXT_MONTH"})
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(args.db)
    con.execute("create schema if not exists bronze")
    con.execute("create or replace table bronze.uci_credit_clients as select * from df")
    print(f"bronze.uci_credit_clients {con.execute('select count(*) from bronze.uci_credit_clients').fetchone()[0]:,} rows")


if __name__ == "__main__":
    main()
