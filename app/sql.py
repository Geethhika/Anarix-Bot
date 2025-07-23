import sqlite3
import re
import logging
import os
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

def clean_sql(sql_string):
    # Remove markdown SQL fences and strip
    return re.sub(r"```sql\s*([\s\S]*?)```", r"\1", sql_string).strip()

def strip_sql_comments_and_whitespace(sql):
    # Remove all SQL single-line comments and leading/trailing whitespace
    lines = sql.splitlines()
    cleaned = [line for line in lines if not line.strip().startswith('--')]
    cleaned_sql = '\n'.join(cleaned).strip()
    return cleaned_sql


BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # /agent/app
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, "../dataset/ecommerce.db"))
logging.info(f"Using DB_PATH: {DB_PATH}")
# DB_PATH = "F:/code/project/writ/agent/database/ecommerce.db"
LIMIT_REGEX = re.compile(r"\blimit\b", re.IGNORECASE)

def execute_sql_query(sql: str, limit: int = 100, offset: int = 0):
    try:
        query = clean_sql(sql)
        query_no_comments = strip_sql_comments_and_whitespace(query)
        # Find the first non-empty line
        for line in query_no_comments.splitlines():
            if line.strip():
                first_line = line.strip().lower()
                break
        else:
            first_line = ''
        if not first_line.startswith('select'):
            logging.warning(f"Blocked potentially unsafe SQL: {query}")
            return {"error": "Only SELECT queries are allowed."}
        # Only append LIMIT/OFFSET if not already present
        if LIMIT_REGEX.search(query_no_comments):
            paginated_query = query.strip().rstrip(';') + ";"
        else:
            paginated_query = query.strip().rstrip(';') + f" LIMIT {limit} OFFSET {offset};"
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        logging.info(f"Executing SQL: {paginated_query}")
        cursor.execute(paginated_query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        result = [dict(zip(columns, row)) for row in rows]
        return result
    except Exception as e:
        logging.error(f"SQL execution error: {e}")
        return {"error": str(e)}
