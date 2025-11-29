from fastapi import APIRouter, HTTPException
from app.schemas.chat import ChatInputSchema, ChatOutputSchema
from app.services.agent_service import agent_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/",
    response_model=ChatOutputSchema,
    summary="Interaksi dengan Chatbot AI",
    description="Mengirimkan pertanyaan ke Agent AI dan menerima respons. "
                "Chatbot dapat membantu memprediksi kerusakan mesin, "
                "memberikan status mesin, dan menjawab query tentang maintenance.",
    responses={
        200: {"description": "Chatbot berhasil merespons"},
        503: {"description": "AI Agent tidak tersedia"}
    }
)
async def handle_chat(data: ChatInputSchema) -> ChatOutputSchema:
    """
    Fungsi utama untuk memproses input pengguna dan menghasilkan respons chatbot.

    Args:
        data (ChatInputSchema): Input query dari pengguna

    Returns:
        ChatOutputSchema: Respons dari chatbot

    Raises:
        HTTPException: Jika agent tidak tersedia atau terjadi kesalahan
    """
    try:
        if not agent_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="AI Agent tidak tersedia. Pastikan OPENAI_API_KEY sudah dikonfigurasi."
            )

        response = await agent_service.chat(data.query)

        return ChatOutputSchema(response=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pada endpoint chat: {e}")
        raise HTTPException(
            status_code=500,
            detail="Terjadi kesalahan saat berkomunikasi dengan AI Agent."
        )

@router.get(
    "/status",
    summary="Status Chatbot",
    description="Mengembalikan status ketersediaan chatbot AI."
)
async def get_chatbot_status() -> dict:
    """
    Endpoint untuk mengecek status chatbot AI.

    Returns:
        Dict: Status chatbot dan konfigurasi
    """
    try:
        return {
            "agent_available": agent_service.is_available(),
            "model": "gpt-4o-mini" if agent_service.is_available() else None,
            "tools_available": [
                "predict_machine_failure",
                "get_machine_status",
                "get_all_machines_status",
                "get_high_risk_machines"
            ] if agent_service.is_available() else [],
            "example_queries": [
                "Prediksi mesin M14860",
                "Mesin mana yang paling berisiko?",
                "Bagaimana cara mengecek status semua mesin?",
                "Apa penyebab kerusakan mesin jika suhu tinggi?",
                "Berikan rekomendasi maintenance untuk mesin dengan torsi tinggi"
            ]
        }

    except Exception as e:
        logger.error(f"Error mendapatkan status chatbot: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Terjadi kesalahan: {str(e)}"
        )