import pickle
import tensorflow as tf
from tensorflow import keras
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any
import os
import logging
from app.core.config import settings
from app.schemas.prediction import PredictionInputSchema, PredictionOutputSchema
from app.schemas.machine import MachineStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PredictionService:
    """
    Service class untuk prediksi maintenance mesin.

    Menggunakan model LSTM yang sudah dilatih (LSTM_Model.h5)
    untuk memprediksi kemungkinan kerusakan mesin berdasarkan data sensor.
    """

    def __init__(self):
        """Inisialisasi service dengan loading model ML."""
        self.model = None
        self.feature_columns = settings.FEATURE_COLS
        self.load_model()

    def load_model(self) -> None:
        """
        Load model LSTM dari file LSTM_Model.h5.

        Raises:
            FileNotFoundError: Jika file model tidak ditemukan
            Exception: Jika terjadi kesalahan saat loading model
        """
        try:
            model_path = settings.MODEL_FILE_PATH
            if not os.path.exists(model_path):
                logger.warning(f"Model file not found at {model_path}. Using fallback logic.")
                self.model = None
                return

            self.model = keras.models.load_model(model_path)
            logger.info(f"LSTM Model loaded successfully from {model_path}")

        except Exception as e:
            logger.error(f"Error loading LSTM model: {e}")
            self.model = None

    def preprocess_input(self, data: PredictionInputSchema) -> pd.DataFrame:
        """
        Preprocess input data untuk model ML.

        Args:
            data: Input schema dari user

        Returns:
            pd.DataFrame: Data yang sudah di-preprocess
        """
        if not data.machine_id:
            if not all([data.air_temperature is not None, data.process_temperature is not None,
                      data.rotational_speed is not None, data.torque is not None, data.tool_wear is not None]):
                raise ValueError("Jika machine_id tidak disediakan, semua data sensor (air_temperature, process_temperature, rotational_speed, torque, tool_wear) harus diisi")

        if data.machine_id:
            sensor_data = settings.get_machine_sensor_data(data.machine_id)

            logger.info(f"Machine ID: {data.machine_id}")
            logger.info(f"Sensor data retrieved: {sensor_data}")

            air_temperature = sensor_data["air_temperature"]
            process_temperature = sensor_data["process_temperature"]
            rotational_speed = sensor_data["rotational_speed"]
            torque = sensor_data["torque"]
            tool_wear = sensor_data["tool_wear"]

            logger.info(f"Using sensor values - Temp: {air_temperature}, Process: {process_temperature}, Speed: {rotational_speed}, Torque: {torque}, Wear: {tool_wear}")
        else:
            air_temperature = data.air_temperature
            process_temperature = data.process_temperature
            rotational_speed = data.rotational_speed
            torque = data.torque
            tool_wear = data.tool_wear

        input_dict = {
            'Air temperature [K]': air_temperature,
            'Process temperature [K]': process_temperature,
            'Rotational speed [rpm]': rotational_speed,
            'Torque [Nm]': torque,
            'Tool wear [min]': tool_wear
        }

        df = pd.DataFrame([input_dict])

        if self.model and self.feature_columns:
            expected_features = self.feature_columns
            for col in expected_features:
                if col not in df.columns:
                    df[col] = 0

            df = df[expected_features]

        return df

    def predict_with_model(self, input_data: pd.DataFrame) -> Tuple[bool, float, int]:
        """
        Lakukan prediksi menggunakan model LSTM.

        Args:
            input_data: Data yang sudah di-preprocess

        Returns:
            Tuple[bool, float, int]: (will_fail, probability, failure_type)
        """
        if self.model is None:
            will_fail, probability = self._fallback_prediction(input_data)
            failure_type = 0
            return will_fail, probability, failure_type

        try:
            if len(input_data.shape) == 2:
                input_array = input_data.values.reshape(1, 1, -1)
            else:
                input_array = input_data

            prediction = self.model.predict(input_array)[0]

            if len(prediction.shape) == 0:
                failure_type = int(np.round(prediction))
                probability = float(abs(prediction))
            else:
                failure_type = int(np.argmax(prediction))
                probability = float(np.max(prediction))

            failure_type = max(0, min(failure_type, 5))
            will_fail = failure_type > 0

            probability = max(0.0, min(1.0, probability))

            return will_fail, probability, failure_type

        except Exception as e:
            logger.error(f"Error during LSTM prediction: {e}")
            will_fail, probability = self._fallback_prediction(input_data)
            failure_type = 0
            return will_fail, probability, failure_type

    def _fallback_prediction(self, input_data: pd.DataFrame) -> Tuple[bool, float]:
        """
        Fallback prediction logic jika model tidak tersedia.

        Args:
            input_data: Data sensor

        Returns:
            Tuple[bool, float]: (will_fail, probability)
        """
        row = input_data.iloc[0]

        risk_score = 0

        if row.get('Air temperature [K]', 0) > settings.TEMP_THRESHOLD:
            risk_score += 2

        if row.get('Process temperature [K]', 0) > settings.TEMP_THRESHOLD + 10:
            risk_score += 2

        if row.get('Rotational speed [rpm]', 0) > settings.SPEED_THRESHOLD:
            risk_score += 3

        if row.get('Torque [Nm]', 0) > settings.TORQUE_THRESHOLD:
            risk_score += 2

        if row.get('Tool wear [min]', 0) > settings.TOOL_WEAR_THRESHOLD:
            risk_score += 2

        if risk_score <= 3:
            will_fail = False
            probability = min(0.1 + (risk_score * 0.1), 0.4)
        elif risk_score <= 6:
            will_fail = False
            probability = min(0.4 + ((risk_score - 3) * 0.1), 0.7)
        else:
            will_fail = True
            probability = min(0.7 + ((risk_score - 6) * 0.05), 0.95)

        return will_fail, probability

    def determine_status(self, will_fail: bool, probability: float, failure_type: int) -> Tuple[MachineStatus, str]:
        """
        Menentukan status dan pesan berdasarkan hasil prediksi.

        Args:
            will_fail: Prediksi kerusakan
            probability: Probabilitas kerusakan
            failure_type: Tipe kerusakan (0-5)

        Returns:
            Tuple[MachineStatus, str]: Status dan pesan
        """
        failure_name = settings.FAILURE_TYPE_MAPPING.get(failure_type, "Unknown Failure")

        if probability < 0.3:
            status = MachineStatus.NORMAL
            message = "Mesin dalam kondisi normal dan stabil."
        elif probability < 0.7:
            status = MachineStatus.WARNING
            if failure_type == 0:
                message = "Waspada, kondisi mesin menunjukkan tanda keausan. Perlu monitoring lebih lanjut."
            else:
                message = f"Waspada, kondisi mesin menunjukkan tanda keausan ({failure_name}). Perlu monitoring lebih lanjut."
        else:
            status = MachineStatus.FAILURE
            if failure_type == 0:
                message = "Kemungkinan besar mesin akan mengalami kerusakan. Segera lakukan maintenance."
            else:
                message = f"Kemungkinan besar mesin akan mengalami {failure_name}. Segera lakukan maintenance."

        return status, message

    def predict(self, data: PredictionInputSchema) -> PredictionOutputSchema:
        """
        Metode utama untuk melakukan prediksi.

        Args:
            data: Input data dari user

        Returns:
            PredictionOutputSchema: Hasil prediksi
        """
        try:
            input_data = self.preprocess_input(data)

            will_fail, probability, failure_type = self.predict_with_model(input_data)

            failure_type_name = settings.FAILURE_TYPE_MAPPING.get(failure_type, "Unknown Failure")

            status, message = self.determine_status(will_fail, probability, failure_type)

            return PredictionOutputSchema(
                machine_status=status,
                probability=probability,
                failure_type=failure_type,
                failure_type_name=failure_type_name,
                message=message
            )

        except Exception as e:
            logger.error(f"Error in predict method: {e}")
            debug_response = PredictionOutputSchema(
                machine_status=MachineStatus.WARNING,
                probability=0.5,
                failure_type=0,
                failure_type_name="No Failure",
                message=f"Terjadi kesalahan saat prediksi: {str(e)}"
            )
            logger.info(f"Debug response: {debug_response.model_dump()}")
            logger.info(f"Debug response JSON: {debug_response.model_dump_json()}")
            return debug_response


prediction_service = PredictionService()