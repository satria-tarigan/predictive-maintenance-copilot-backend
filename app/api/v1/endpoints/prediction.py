from fastapi import APIRouter, HTTPException
from app.schemas.prediction import PredictionInputSchema, PredictionOutputSchema
from app.services.prediction_service import prediction_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/predict",
    response_model=PredictionOutputSchema,
    summary="Prediksi Kondisi Mesin",
    description="Mengembalikan hasil prediksi kondisi mesin berdasarkan data sensor menggunakan model LSTM.",
)

async def predict_failure(data: PredictionInputSchema) -> PredictionOutputSchema:
    """
    Fungsi utama untuk memproses data sensor dan menghasilkan prediksi kondisi mesin.

    Args:
        data (PredictionInputSchema): Data masukan dari sensor mesin.

    Returns:
        PredictionOutputSchema: Hasil prediksi kondisi mesin beserta probabilitas dan pesan penjelasan.

    Raises:
        HTTPException: Jika terjadi kesalahan saat prediksi
    """
    try:
        result = prediction_service.predict(data)

        logger.info(f"Prediction result: {result.model_dump()}")

        return result

    except Exception as e:
        logger.error(f"Error dalam prediksi: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Terjadi kesalahan saat melakukan prediksi: {str(e)}"
        )

@router.get(
    "/model-status",
    summary="Status Model LSTM",
    description="Mengembalikan status model LSTM yang digunakan."
)
async def get_model_status():
    """
    Endpoint untuk mengecek status model LSTM.
    """
    try:
        model_loaded = prediction_service.model is not None
        model_path = prediction_service.settings.MODEL_FILE_PATH

        return {
            "model_loaded": model_loaded,
            "model_path": model_path,
            "feature_columns": prediction_service.feature_columns,
            "message": "Model loaded successfully" if model_loaded else "Using fallback prediction logic"
        }

    except Exception as e:
        logger.error(f"Error mendapatkan status model: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Terjadi kesalahan: {str(e)}"
        )