from fastapi import FastAPI
from app.api.router_register import router as register_router
from app.api.router_search import router as search_router

app = FastAPI()

app.include_router(register_router, prefix="/register")
app.include_router(search_router, prefix="/search")
