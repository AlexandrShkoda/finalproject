from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3

app = FastAPI()
DB_PATH = "data/todo.db"

class Item(BaseModel):
    id: int = None  
    title: str
    description: str = None
    completed: bool = False

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                completed BOOLEAN NOT NULL DEFAULT 0
            )
        """)
        conn.commit()

@app.on_event("startup")
def startup():
    init_db()

@app.post("/items", response_model=Item)
def create_item(item: Item):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            INSERT INTO items (title, description, completed) VALUES (?, ?, ?)
        """, (item.title, item.description, item.completed))
        item_id = cursor.lastrowid
    return {"id": item_id, **item.dict()}

@app.get("/items", response_model=List[Item])
def get_items():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT id, title, description, completed FROM items")
        items = cursor.fetchall()
    return [{"id": id_, "title": title, "description": description, "completed": completed}
            for id_, title, description, completed in items]

@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT id, title, description, completed FROM items WHERE id = ?", (item_id,))
        item = cursor.fetchone()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": item[0], "title": item[1], "description": item[2], "completed": item[3]}

@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: int, item: Item):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            UPDATE items SET title = ?, description = ?, completed = ?
            WHERE id = ?
        """, (item.title, item.description, item.completed, item_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")
    item_dict = item.dict()
    item_dict["id"] = item_id
    return item_dict

@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")
    return {"detail": "Item deleted"}