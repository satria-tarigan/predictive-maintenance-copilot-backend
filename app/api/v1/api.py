"""
Modul pengelola router API versi 1 (v1)
File ini menggabungkan semua endpoint yang ada dalam versi API ini.

"""

from fastapi import APIRouter
from app.api.v1.endpoints import prediction, chat, machine

api_router = APIRouter()

api_router.include_router(
    prediction.router,
    prefix="/prediction",
    tags=["Prediction"]
)

api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chatbot"]
)

api_router.include_router(
    machine.router,
    prefix="/machines",
    tags=["Machine Monitoring"]
)