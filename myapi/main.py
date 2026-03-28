from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import time
import httpx
import asyncio

app = FastAPI(
    title="Homelab API",
    description="ML-monitored REST API",
    version="1.0.0"
)

# ── MODELS ─────────────────────────────────────────
class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float

class User(BaseModel):
    username: str
    email: str

# ── IN-MEMORY STORAGE (replace with postgres later) ─
items_db = {}
users_db = {}

# ── MONITORING MIDDLEWARE ───────────────────────────
@app.middleware("http")
async def monitoring_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    # Fire and forget to ML detector
    asyncio.create_task(log_request({
        "endpoint": str(request.url.path),
        "method": request.method,
        "status_code": response.status_code,
        "response_time": duration,
        "payload_size": int(response.headers.get("content-length", 0)),
        "hour_of_day": time.localtime().tm_hour,
    }))

    return response

async def log_request(data: dict):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://ml-detector:8000/log",
                json=data,
                timeout=0.5
            )
    except:
        pass  # Never let monitoring break the API

# ── HEALTH CHECK ────────────────────────────────────
@app.get("/")
async def root():
    return {"status": "running", "service": "Homelab API"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": time.time()}

# ── ITEMS ENDPOINTS ─────────────────────────────────
@app.get("/items")
async def get_items():
    return {"items": list(items_db.values())}

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]

@app.post("/items/{item_id}")
async def create_item(item_id: int, item: Item):
    items_db[item_id] = item.dict()
    return {"message": "Item created", "item": item}

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    del items_db[item_id]
    return {"message": "Item deleted"}

# ── USERS ENDPOINTS ─────────────────────────────────
@app.get("/users")
async def get_users():
    return {"users": list(users_db.values())}

@app.post("/users")
async def create_user(user: User):
    users_db[user.username] = user.dict()
    return {"message": "User created", "user": user}

@app.get("/users/{username}")
async def get_user(username: str):
    if username not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[username]
