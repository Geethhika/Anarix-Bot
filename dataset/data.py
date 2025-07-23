# import sqlite3
# import pandas as pd
# import os
# import logging

# # Setup logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

# # Paths (relative)
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DATASET_FOLDER = BASE_DIR
# DB_PATH = os.path.join(BASE_DIR, "ecommerce.db")

# # Expected schemas for validation
# EXPECTED_SCHEMAS = {
#     "eligibility": ["eligibility_datetime_utc", "item_id", "eligibility", "message"],
#     "ad_sales": ["date", "item_id", "ad_sales", "impressions", "ad_spend", "clicks", "units_sold"],
#     "total_sales": ["date", "item_id", "total_sales", "total_units_ordered"]
# }

# files = {
#     "eligibility": "Product-Level Eligibility Table.xlsx",
#     "ad_sales": "Product-Level Ad Sales and Metrics.xlsx",
#     "total_sales": "Product-Level Total Sales and Metrics.xlsx"
# }

# def validate_schema(df, expected_cols, table_name):
#     actual = set(df.columns)
#     expected = set(expected_cols)
#     if actual != expected:
#         missing = expected - actual
#         extra = actual - expected
#         msg = f"Schema mismatch in {table_name}:\nMissing: {missing}\nExtra: {extra}"
#         logging.error(msg)
#         raise ValueError(msg)

# try:
#     conn = sqlite3.connect(DB_PATH)
#     for table, filename in files.items():
#         path = os.path.join(DATASET_FOLDER, filename)
#         if not os.path.exists(path):
#             logging.error(f"File not found: {path}")
#             continue
#         logging.info(f"Loading {filename} into table '{table}'")
#         try:
#             df = pd.read_excel(path)
#             df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
#             validate_schema(df, EXPECTED_SCHEMAS[table], table)
#             df = df.fillna("nil")
#             df.to_sql(table, conn, if_exists='replace', index=False)
#             logging.info(f"Loaded {filename} into '{table}' successfully.")
#         except Exception as e:
#             logging.error(f"Failed to load {filename} into '{table}': {e}")
#     conn.close()
#     logging.info("✅ All tables loaded (with errors above if any).")
# except Exception as e:
#     logging.critical(f"Database connection failed: {e}")

import sqlite3
import pandas as pd
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "ecommerce.db")

# Expected schema definitions
EXPECTED_SCHEMAS = {
    "eligibility": {
        "columns": ["eligibility_datetime_utc", "item_id", "eligibility", "message"],
        "types": {
            "eligibility_datetime_utc": "datetime64[ns]",
            "item_id": "str",
            "eligibility": "str",
            "message": "str"
        }
    },
    "ad_sales": {
        "columns": ["date", "item_id", "ad_sales", "impressions", "ad_spend", "clicks", "units_sold"],
        "types": {
            "date": "datetime64[ns]",
            "item_id": "str",
            "ad_sales": "float",
            "impressions": "int",
            "ad_spend": "float",
            "clicks": "int",
            "units_sold": "int"
        }
    },
    "total_sales": {
        "columns": ["date", "item_id", "total_sales", "total_units_ordered"],
        "types": {
            "date": "datetime64[ns]",
            "item_id": "str",
            "total_sales": "float",
            "total_units_ordered": "int"
        }
    }
}

# Filenames
FILES = {
    "eligibility": "Product-Level Eligibility Table.xlsx",
    "ad_sales": "Product-Level Ad Sales and Metrics.xlsx",
    "total_sales": "Product-Level Total Sales and Metrics.xlsx"
}

def validate_and_clean(df: pd.DataFrame, schema: dict, table: str) -> pd.DataFrame:
    # Standardize column names
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    # Validate schema
    expected = set(schema["columns"])
    actual = set(df.columns)
    if actual != expected:
        missing = expected - actual
        extra = actual - expected
        msg = f"[{table}] Schema mismatch:\n Missing: {missing}\n Extra: {extra}"
        logging.error(msg)
        raise ValueError(msg)

    # Clean & convert column types
    for col, dtype in schema["types"].items():
        if dtype == "datetime64[ns]":
            df[col] = pd.to_datetime(df[col], errors="coerce")
        else:
            df[col] = df[col].fillna("nil" if dtype == "str" else 0)
            df[col] = df[col].astype(dtype, errors="ignore")

    # Count nulls
    null_counts = df.isnull().sum()
    if null_counts.sum() > 0:
        logging.warning(f"[{table}] Nulls after cleaning:\n{null_counts[null_counts > 0]}")

    return df

def load_tables_to_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        for table, filename in FILES.items():
            path = os.path.join(BASE_DIR, filename)
            if not os.path.exists(path):
                logging.warning(f"⚠️ File not found: {path}")
                continue

            logging.info(f"📄 Loading {filename} into '{table}'")

            try:
                df = pd.read_excel(path)
                df = validate_and_clean(df, EXPECTED_SCHEMAS[table], table)
                df.to_sql(table, conn, if_exists='replace', index=False)
                logging.info(f"✅ Successfully loaded '{table}' ({len(df)} rows)")

            except Exception as e:
                logging.error(f"❌ Failed to load {table}: {e}")

        conn.close()
        logging.info("🏁 All table operations completed.")
    except Exception as e:
        logging.critical(f"🔥 Database connection failed: {e}")

if __name__ == "__main__":
    load_tables_to_db()
