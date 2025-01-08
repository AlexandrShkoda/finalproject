from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List
import sqlite3
import hashlib

app = FastAPI()
DB_PATH = "data/shorturl.db"

class URLData(BaseModel):
    url: str

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                short_id TEXT PRIMARY KEY,
                full_url TEXT NOT NULL
            )
        """)
        conn.commit()

@app.on_event("startup")
def startup():
    init_db()


@app.get("/list_urls")
def get_all_urls():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT * FROM urls")
        urls = cursor.fetchall()
    return [{'short_id':short_id, 'full_url' : full_url,}
            for short_id, full_url in urls]

@app.post("/shorten")
def shorten_url(url_data: URLData):
    short_id = hashlib.md5(url_data.url.encode()).hexdigest()[:6]
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO urls (short_id, full_url) VALUES (?, ?)", (short_id, url_data.url))
    return {"short_id": short_id}

@app.get("/{short_id}")
def redirect_url(short_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT full_url FROM urls WHERE short_id = ?", (short_id,))
        url = cursor.fetchone()
    if url is None:
        raise HTTPException(status_code=404, detail="URL not found")
    return RedirectResponse(url = url[0])


@app.get("/stats/{short_id}")
def get_url_stats(short_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT full_url FROM urls WHERE short_id = ?", (short_id,))
        url = cursor.fetchone()
    if url is None:
        raise HTTPException(status_code=404, detail="URL not found")
    return {"short_id": short_id, "full_url": url[0]}

