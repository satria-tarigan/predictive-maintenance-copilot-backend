from pydantic import BaseModel, Field
from typing import Optional
from .machine import MachineStatus


class PredictionInputSchema(BaseModel):
    """ Data masukan (input) untuk melakukan prediksi kondisi mesin. """
    machine_id: Optional[str] = Field(None, description="ID Mesin untuk lookup data sensor spesifik.")
    air_temperature: Optional[float] = Field(None, description="Suhu udara (dalam Kelvin).", ge=250, le=350)
    process_temperature: Optional[float] = Field(None, description="Suhu proses (dalam Kelvin).", ge=250, le=350)
    rotational_speed: Optional[float] = Field(None, description="Kecepatan rotasi mesin (dalam RPM).", ge=0, le=3000)
    torque: Optional[float] = Field(None, description="Torsi mesin (dalam Nm).", ge=0, le=100)
    tool_wear: Optional[int] = Field(None, description="Tingkat keausan alat (dalam menit).", ge=0, le=500)

    def get_sensor_values(self):
        """Get sensor values, gunakan fixed data jika machine_id ada."""
        if self.machine_id:
            from app.core.config import settings
            sensor_data = settings.get_machine_sensor_data(self.machine_id)
            return {
                'air_temperature': sensor_data['air_temperature'],
                'process_temperature': sensor_data['process_temperature'],
                'rotational_speed': sensor_data['rotational_speed'],
                'torque': sensor_data['torque'],
                'tool_wear': sensor_data['tool_wear']
            }
        else:
            return {
                'air_temperature': self.air_temperature,
                'process_temperature': self.process_temperature,
                'rotational_speed': self.rotational_speed,
                'torque': self.torque,
                'tool_wear': self.tool_wear
            }

    class Config:
        json_schema_extra = {
            "example": {
                "machine_id": "L47257",
                "air_temperature": 298.5,
                "process_temperature": 308.8,
                "rotational_speed": 1550,
                "torque": 45.5,
                "tool_wear": 120
            }
        }

class PredictionOutputSchema(BaseModel):
    """ Data keluaran (output) dari hasil prediksi kondisi mesin. """
    machine_status: MachineStatus = Field(..., description="Status kesehatan mesin.")
    probability: float = Field(..., description="Probabilitas kerusakan mesin.", ge=0.0, le=1.0)
    failure_type: int = Field(0, description="Tipe kerusakan (0=No Failure, 1=Heat Dissipation, 2=Overstrain, 3=Power, 4=Random, 5=Tool Wear).")
    failure_type_name: str = Field("No Failure", description="Nama tipe kerusakan.")
    message: str = Field(..., description="Penjelasan singkat hasil prediksi.")

    class Config:
        json_schema_extra = {
            "example": {
                "machine_status": "Normal",
                "probability": 0.15,
                "failure_type": 0,
                "failure_type_name": "No Failure",
                "message": "Mesin dalam kondisi normal dan stabil."
            }
        }