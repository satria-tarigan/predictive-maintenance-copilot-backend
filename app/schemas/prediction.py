"""
Modul skema untuk API prediksi.

File ini berisi model data (input dan output)
yang digunakan pada fitur predikasi kesehatan mesin.
"""

from pydantic import BaseModel, Field


class PredictionInputSchema(BaseModel):
    """ Data masukan (input) untuk melakukan prediksi kondisi mesin. """
    air_temperature: float = Field(..., description="Suhu udara (dalam derajat Celsius).")
    process_temperature: float = Field(..., description="Suhu proses (dalam derajat Celsius).")
    rotational_speed: float = Field(..., description="Kecepatan rotasi mesin (dalam RPM).")
    torque: float = Field(..., description="Torsi mesin (dalam Nm).")
    tool_wear: int = Field(..., description="Tingkat keausan alat (dalam menit).")
    
    class Config:
        json_schema_extra = {
            "example": {
                "air_temperature": 301.5,
                "process_temperature": 310.8,
                "rotational_speed": 1500,
                "torque": 40.5,
                "tool_wear": 50
            }
        }

class PredictionOutputSchema(BaseModel):
    """ Data keluaran (output) dari hasil prediksi kondisi mesin. """
    machine_status: str = Field(..., description="Status kesehatan mesin (Normal atau Perlu Perawatan).")
    probability: float = Field(..., description="Probabilitas kerusakan mesin.")
    message: str = Field(..., description="Penjelasan singkat hasil prediksi.")