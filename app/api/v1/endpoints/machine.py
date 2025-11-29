from fastapi import APIRouter, HTTPException, Query
from app.schemas.machine import (
    MachineStatusResponse, AllMachinesResponse, MachinePredictionInput,
    MachineStatus
)
from app.schemas.prediction import PredictionOutputSchema
from app.services.machine_service import machine_service
from app.services.prediction_service import prediction_service
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get(
    "/status/{machine_id}",
    response_model=MachineStatusResponse,
    summary="Status Mesin Tertentu",
    description="Mengembalikan status real-time dari mesin tertentu.",
    responses={
        200: {"description": "Status mesin berhasil didapatkan"},
        404: {"description": "Machine ID tidak ditemukan"}
    }
)
async def get_machine_status(machine_id: str) -> MachineStatusResponse:
    """
    Mendapatkan status mesin tertentu dengan data sensor real-time.

    Args:
        machine_id (str): ID unik mesin

    Returns:
        MachineStatusResponse: Status mesin dengan data sensor

    Raises:
        HTTPException: Jika machine_id tidak valid
    """
    try:
        if machine_id not in settings.MACHINE_IDS:
            raise HTTPException(
                status_code=404,
                detail=f"Machine ID {machine_id} tidak ditemukan. "
                        f"Machine IDs yang tersedia: {', '.join(settings.MACHINE_IDS[:5])}..."
            )

        machine_status = machine_service.get_machine_status(machine_id)
        if not machine_status:
            raise HTTPException(
                status_code=404,
                detail=f"Data untuk mesin {machine_id} tidak tersedia"
            )

        return machine_status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error mendapatkan status mesin {machine_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Terjadi kesalahan: {str(e)}"
        )

@router.get(
    "/status",
    response_model=AllMachinesResponse,
    summary="Status Semua Mesin",
    description="Mengembalikan status dari semua mesin yang tersedia.",
)
async def get_all_machines_status() -> AllMachinesResponse:
    """
    Mendapatkan status semua mesin.

    Returns:
        AllMachinesResponse: Status semua mesin dengan summary
    """
    try:
        return machine_service.get_all_machines_status()

    except Exception as e:
        logger.error(f"Error mendapatkan status semua mesin: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Terjadi kesalahan: {str(e)}"
        )

@router.get(
    "/high-risk",
    summary="Mesin Berisiko Tinggi",
    description="Mengembalikan daftar mesin dengan risiko kerusakan tinggi.",
)
async def get_high_risk_machines():
    """
    Mendapatkan daftar mesin dengan status Warning atau Failure.

    Returns:
        Dict: Daftar mesin berisiko tinggi dengan analisis
    """
    try:
        high_risk_machines = machine_service.get_high_risk_machines()

        return {
            "count": len(high_risk_machines),
            "machines": [
                {
                    "machine_id": m.machine_id,
                    "machine_type": m.machine_type.value,
                    "status": m.status.value,
                    "failure_probability": m.failure_probability,
                    "last_updated": m.last_updated.isoformat(),
                    "recommendation": m.recommendation
                }
                for m in high_risk_machines
            ],
            "message": f"Ditemukan {len(high_risk_machines)} mesin dengan risiko tinggi"
        }

    except Exception as e:
        logger.error(f"Error mendapatkan mesin berisiko tinggi: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Terjadi kesalahan: {str(e)}"
        )

@router.post(
    "/predict/{machine_id}",
    response_model=PredictionOutputSchema,
    summary="Prediksi Mesin Tertentu",
    description="Melakukan prediksi kerusakan untuk mesin tertentu dengan data sensor.",
    responses={
        200: {"description": "Prediksi berhasil"},
        404: {"description": "Machine ID tidak ditemukan"}
    }
)
async def predict_machine_failure(machine_id: str, data: MachinePredictionInput) -> PredictionOutputSchema:
    """
    Melakukan prediksi kerusakan untuk mesin tertentu.

    Args:
        machine_id (str): ID mesin yang akan diprediksi
        data (MachinePredictionInput): Data sensor untuk prediksi

    Returns:
        PredictionOutputSchema: Hasil prediksi

    Raises:
        HTTPException: Jika machine_id tidak valid
    """
    try:
        if machine_id not in settings.MACHINE_IDS:
            raise HTTPException(
                status_code=404,
                detail=f"Machine ID {machine_id} tidak ditemukan"
            )

        if data.machine_id != machine_id:
            raise HTTPException(
                status_code=400,
                detail="Machine ID di path dan body harus sama"
            )

        input_data = PredictionInputSchema(
            air_temperature=data.sensor_data.air_temperature,
            process_temperature=data.sensor_data.process_temperature,
            rotational_speed=data.sensor_data.rotational_speed,
            torque=data.sensor_data.torque,
            tool_wear=data.sensor_data.tool_wear
        )

        result = prediction_service.predict(input_data)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error prediksi mesin {machine_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Terjadi kesalahan: {str(e)}"
        )

@router.get(
    "/by-status/{status}",
    summary="Filter Mesin Berdasarkan Status",
    description="Mendapatkan mesin-mesin berdasarkan status tertentu.",
)
async def get_machines_by_status(status: MachineStatus) -> dict:
    """
    Mendapatkan mesin berdasarkan status.

    Args:
        status (MachineStatus): Status mesin yang dicari

    Returns:
        Dict: Daftar mesin dengan status tersebut
    """
    try:
        machines = machine_service.get_machines_by_status(status)

        return {
            "status": status.value,
            "count": len(machines),
            "machines": [
                {
                    "machine_id": m.machine_id,
                    "machine_type": m.machine_type.value,
                    "failure_probability": m.failure_probability,
                    "last_updated": m.last_updated.isoformat()
                }
                for m in machines
            ]
        }

    except Exception as e:
        logger.error(f"Error filter mesin berdasarkan status {status}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Terjadi kesalahan: {str(e)}"
        )

@router.get(
    "/list",
    summary="Daftar Semua Machine ID",
    description="Mengembalikan daftar semua machine ID yang tersedia.",
)
async def list_machine_ids() -> dict:
    """
    Mendapatkan daftar semua machine ID yang tersedia.

    Returns:
        Dict: Daftar machine ID
    """
    return {
        "total_machines": len(settings.MACHINE_IDS),
        "machine_ids": settings.MACHINE_IDS,
        "available_endpoints": [
            f"/machines/status/{{machine_id}}",
            "/machines/status",
            "/machines/high-risk",
            f"/machines/predict/{{machine_id}}",
            f"/machines/by-status/{{status}}"
        ]
    }