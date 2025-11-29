from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings
import uvicorn


def create_app() -> FastAPI:
    """
    Membuat instance FastAPI utama.
    Menyimpan konfigurasi dasar aplikasi dan route yang digunakan.
    """
    app = FastAPI(
        title="Predictive Maintenance Copilot API",
        description="API untuk deteksi anomali, prediksi kerusakan mesin, dan agent chatbot dengan LangChain.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    @app.get('/favicon.ico', include_in_schema=False)
    async def favicon():
        """
        Mengembalikan respons 204 No Content untuk permintaan favicon.
        """
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.get("/", tags=["Root"])
    def root():
        """
        Endpoint sederhana untuk mengecek apakah server berjalan.
        """
        return {
            "status": "ok",
            "message": "Predictive Maintenance BE Server is running!",
            "version": "0.1.0",
            "endpoints": {
                "api_docs": "/docs",
                "redoc": "/redoc",
                "prediction_api": "/api/v1/prediction",
                "chatbot_api": "/api/v1/chat",
                "machine_monitoring": "/api/v1/machines"
            },
            "available_machine_ids": settings.MACHINE_IDS[:5]
        }

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)