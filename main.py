from fastapi import FastAPI
from nicegui import ui
from supertracer import SuperTracer
import uvicorn
from typing import Optional

app = FastAPI()

# Initialize SuperTracer
# This will create 'requests.db' in the current directory and add the /logs endpoint
tracer = SuperTracer(app, db_path="requests.db", use_nicegui=False) # toggle use_nicegui as needed 

# Mount NiceGUI onto this FastAPI app so /logs works
ui.run_with(app)

@app.get("/")
def read_root():
    return {"Hello": "World", "message": "Visit /logs to see the requests!"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

@app.post("/users")
def create_user(user_data: dict):
    return {"status": "created", "data": user_data}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
