from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from app.llm import get_sql_query_from_llm
from app.sql import execute_sql_query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
import matplotlib.pyplot as plt
import io
import base64
from fastapi.responses import StreamingResponse
import re
import numpy as np
import json
import time
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    question: str
    fetch_table: bool = False

class VizQuery(Query):
    chart_type: str = "bar"  # default to bar chart

def is_table_request(question: str) -> bool:
    # Only return a table if the exact word 'table' is present
    return bool(re.search(r"\b(table)\b", question, re.I))


def to_markdown_table(rows):
    if not rows or not isinstance(rows, list) or not rows[0]:
        return "No data found."
    headers = list(rows[0].keys())
    md = "| " + " | ".join(headers) + " |\n"
    md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    for row in rows:
        md += "| " + " | ".join(str(row[h]) for h in headers) + " |\n"
    return md

def summarize_result(question, rows):
    if not rows:
        return "Sorry, I couldn't find any relevant data for your request."
    row = rows[0]
    # Try to detect a single numeric answer (e.g., RoAS)
    if len(row) == 1:
        key, value = list(row.items())[0]
        try:
            num = float(value)
            rounded = round(num, 2)
            # Custom explanation for RoAS
            if 'roas' in key.lower():
                return f"The Return on Ad Spend (RoAS) is {rounded}, which means you earn ${rounded} in revenue for every $1 spent on ads."
            # General numeric answer
            return f"The {key.replace('_', ' ')} is {rounded}."
        except Exception:
            pass
    # For other cases, summarize the first row in a friendly way
    details = ', '.join(f"{k.replace('_', ' ')}: {v}" for k, v in row.items())
    if len(rows) == 1:
        return f"Here is the result: {details}."
    return (
        f"I found {len(rows)} records. For example, the first record has {details}."
    )

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/schema")
def get_schema():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../dataset/ecommerce.db")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        schema = {}
        for (table_name,) in tables:
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            schema[table_name] = [col[1] for col in columns]
        conn.close()
        return schema
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
def ask_question(query: Query):
    try:
        sql = get_sql_query_from_llm(query.question)
        result = execute_sql_query(sql)
        if getattr(query, 'fetch_table', False):
            answer = to_markdown_table(result)
            return {
                "question": query.question,
                "generated_sql": sql,
                "result": result,
                "answer": answer,
                "tableData": result
            }
        else:
            answer = summarize_result(query.question, result)
            return {
                "question": query.question,
                "generated_sql": sql,
                "result": result,
                "answer": answer
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {e}")

# @app.post("/ask")
# def ask_question(query: Query):
#     try:
#         sql = get_sql_query_from_llm(query.question)
#         result = execute_sql_query(sql)

#         if getattr(query, 'fetch_table', False):
#             answer = to_markdown_table(result)
#         else:
#             answer = summarize_result(query.question, result)

#         def generate():
#             # ✅ Simulate streaming the answer (token by token or sentence by sentence)
#             for word in answer.split():
#                 yield word + " "
#                 time.sleep(0.05)  # simulate typing delay

#             # ✅ Once answer is streamed, send a special end marker with the rest
#             final_payload = {
#                 "generated_sql": sql,
#                 "result": result,
#                 "tableData": result if getattr(query, 'fetch_table', False) else None
#             }
#             yield "\n[[END_JSON]]" + json.dumps(final_payload)

#         return StreamingResponse(generate(), media_type="text/plain")

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error processing question: {e}")

@app.post("/ask_stream")
def ask_stream(query: Query):
    import time
    import json
    def event_stream():
        sql = get_sql_query_from_llm(query.question)
        result = execute_sql_query(sql)
        response = {
            "question": query.question,
            "generated_sql": sql,
            "result": result
        }
        text = json.dumps(response, indent=2)
        for char in text:
            yield char
            time.sleep(0.01)  # Simulate typing
    return StreamingResponse(event_stream(), media_type="text/plain")

@app.post("/visualize")
def visualize(viz_query: VizQuery):
    try:
        sql = get_sql_query_from_llm(viz_query.question)
        data = execute_sql_query(sql)
        if not data or "error" in data:
            raise ValueError(data.get("error", "No data returned."))
        # Assume first column is x, second is y
        x, y = list(data[0].keys())[0], list(data[0].keys())[1]
        x_vals = [row[x] for row in data]
        y_vals = [row[y] for row in data]
        plt.figure(figsize=(8, 4))
        if viz_query.chart_type == "bar":
            plt.bar(x_vals, y_vals)
        elif viz_query.chart_type == "line":
            plt.plot(x_vals, y_vals)
        else:
            plt.bar(x_vals, y_vals)
        plt.xlabel(x)
        plt.ylabel(y)
        plt.title(viz_query.question)
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        plt.close()
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
        return {"image_base64": img_base64, "question": viz_query.question, "generated_sql": sql}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Visualization error: {e}")




