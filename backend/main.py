from fastapi import FastAPI
from .routers.receipts import router as receipts_router

app = FastAPI()

app.include_router(receipts_router)

@app.get("/")
def main():
    return {"message": "Hello World"}
