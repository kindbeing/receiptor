from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.receipts import router as receipts_router
from routers.invoices import router as invoices_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(receipts_router)
app.include_router(invoices_router)

@app.get("/")
def main():
    return {"message": "Hello World"}
