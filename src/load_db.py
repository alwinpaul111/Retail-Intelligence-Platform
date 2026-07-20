"""Load generated CSVs into a SQLite database using the defined schema."""
import sqlite3
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DB_PATH = ROOT / "retail.db"
SCHEMA_SQL = ROOT / "sql" / "01_schema.sql"

def main():
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_SQL.read_text())

    table_files = {
        "stores": "stores.csv",
        "products": "products.csv",
        "customers": "customers.csv",
        "holidays": "holidays.csv",
        "weather": "weather.csv",
        "promotions": "promotions.csv",
        "transactions": "transactions.csv",
        "inventory": "inventory.csv",
    }

    for table, fname in table_files.items():
        df = pd.read_csv(DATA / fname)
        df.to_sql(table, conn, if_exists="append", index=False)
        print(f"Loaded {len(df):>8,} rows -> {table}")

    conn.commit()

    # Sanity check + build the views / stored-procedure-equivalents
    views_sql = (ROOT / "sql" / "02_views.sql").read_text()
    conn.executescript(views_sql)
    conn.commit()
    print("Views created.")
    conn.close()
    print("\nDatabase ready at", DB_PATH)

if __name__ == "__main__":
    main()
