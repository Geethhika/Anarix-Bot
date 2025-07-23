def get_prompt(user_question: str) -> str:
    return f"""
You are a helpful assistant. Convert the following natural language question into an SQL query using these tables:

- ad_sales(date, item_id, ad_sales, impressions, ad_spend, clicks, units_sold)
- total_sales(date, item_id, total_sales, total_units_ordered)
- eligibility(eligibility_datetime_utc, item_id, eligibility, message)

Guidelines:
- Only use the columns and tables provided above.
- Use SQL syntax compatible with SQLite.
- Do not hallucinate columns or tables.
- If the question is ambiguous, make a reasonable assumption.
- If the user asks for a date (e.g., "1st June") without a year, match any year for that day and month (e.g., use strftime to extract month and day).
- If the user requests a table, return all relevant columns. Otherwise, summarize the result in natural language.
- **Never include comments (--) in the SQL query.**

Examples:
Question: What is the total ad spend for item_id 123?
SQL:
SELECT SUM(ad_spend) AS total_ad_spend FROM ad_sales WHERE item_id = 123;

Question: What are the ad sales on 1st June?
SQL:
SELECT * FROM ad_sales WHERE strftime('%m-%d', date) = '06-01';

---

Question: {user_question}
SQL:
""".strip()
