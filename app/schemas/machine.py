from pydantic import BaseModel, Field
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from .prediction import PredictionOutputSchema


class MachineType(str, Enum):
    """Tipe mesin yang tersedia."""
    LOW = "L"
    MEDIUM = "M"
    HIGH = "H"


class MachineStatus(str, Enum):
    """Status mesin."""
    NORMAL = "Normal"
    WARNING = "Warning"
    FAILURE = "Failure"


class MachineSensorData(BaseModel):
    """Data sensor dari sebuah mesin."""
    air_temperature: float = Field(..., description="Suhu udara dalam Kelvin", ge=250, le=350)
    process_temperature: float = Field(..., description="Suhu proses dalam Kelvin", ge=250, le=350)
    rotational_speed: float = Field(..., description="Kecepatan rotasi dalam RPM", ge=0, le=3000)
    torque: float = Field(..., description="Torsi dalam Nm", ge=0, le=100)
    tool_wear: int = Field(..., description="Keausan alat dalam menit", ge=0, le=500)

    class Config:
        json_schema_extra = {
            "example": {
                "air_temperature": 298.5,
                "process_temperature": 308.8,
                "rotational_speed": 1550,
                "torque": 45.5,
                "tool_wear": 120
            }
        }


class MachineInfo(BaseModel):
    """Informasi dasar sebuah mesin."""
    machine_id: str = Field(..., description="ID unik mesin")
    machine_type: MachineType = Field(..., description="Tipe mesin (L/M/H)")
    location: Optional[str] = Field(None, description="Lokasi mesin")
    name: Optional[str] = Field(None, description="Nama mesin")

    class Config:
        json_schema_extra = {
            "example": {
                "machine_id": "M14860",
                "machine_type": "M",
                "location": "Workshop A",
                "name": "CNC Machine 1"
            }
        }


class MachineStatusResponse(BaseModel):
    """Response untuk status mesin."""
    machine_id: str = Field(..., description="ID unik mesin")
    machine_type: MachineType = Field(..., description="Tipe mesin")
    sensor_data: MachineSensorData = Field(..., description="Data sensor real-time")
    status: MachineStatus = Field(..., description="Status kesehatan mesin")
    failure_probability: float = Field(..., description="Probabilitas kerusakan", ge=0.0, le=1.0)
    last_updated: datetime = Field(..., description="Waktu terakhir update data")
    recommendation: Optional[str] = Field(None, description="Rekomendasi maintenance")

    class Config:
        json_schema_extra = {
            "example": {
                "machine_id": "M14860",
                "machine_type": "M",
                "sensor_data": {
                    "air_temperature": 298.5,
                    "process_temperature": 308.8,
                    "rotational_speed": 1550,
                    "torque": 45.5,
                    "tool_wear": 120
                },
                "status": "Normal",
                "failure_probability": 0.15,
                "last_updated": "2024-01-15T10:30:00Z",
                "recommendation": None
            }
        }


class AllMachinesResponse(BaseModel):
    """Response untuk endpoint all machines."""
    total_machines: int = Field(..., description="Total jumlah mesin")
    machines: List[MachineStatusResponse] = Field(..., description="List semua mesin dengan statusnya")
    high_risk_machines: List[str] = Field(..., description="List ID mesin berisiko tinggi")
    summary: dict = Field(..., description="Ringkasan status semua mesin")

    class Config:
        json_schema_extra = {
            "example": {
                "total_machines": 20,
                "machines": [],
                "high_risk_machines": ["M14860", "L4718"],
                "summary": {
                    "normal": 15,
                    "warning": 4,
                    "failure": 1
                }
            }
        }


class MachinePredictionInput(BaseModel):
    """Input untuk prediksi mesin tertentu."""
    machine_id: str = Field(..., description="ID mesin yang akan diprediksi")
    sensor_data: MachineSensorData = Field(..., description="Data sensor untuk prediksi")

    class Config:
        json_schema_extra = {
            "example": {
                "machine_id": "M14860",
                "sensor_data": {
                    "air_temperature": 298.5,
                    "process_temperature": 308.8,
                    "rotational_speed": 1550,
                    "torque": 45.5,
                    "tool_wear": 120
                }
            }
        }