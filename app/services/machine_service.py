import random
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from app.core.config import settings
from app.schemas.machine import (
    MachineInfo, MachineStatus, MachineStatusResponse,
    MachineSensorData, AllMachinesResponse, MachineType
)


class MachineService:
    """
    Service untuk mengelola data mesin dan simulasi sensor data.

    Menyediakan data dummy yang realistis untuk mensimulasikan
    kondisi mesin-mesin industri secara real-time.
    """

    def __init__(self):
        """Inisialisasi machine service dengan data mesin."""
        self.machines = self._initialize_machines()

    def _initialize_machines(self) -> Dict[str, MachineInfo]:
        """
        Inisialisasi data mesin dasar.

        Returns:
            Dict[str, MachineInfo]: Mapping machine_id ke MachineInfo
        """
        machines = {}

        # Generate machine info dari machine IDs
        for machine_id in settings.MACHINE_IDS:
            # Extract type dari prefix
            if machine_id.startswith('H'):
                machine_type = MachineType.HIGH
            elif machine_id.startswith('M'):
                machine_type = MachineType.MEDIUM
            else:
                machine_type = MachineType.LOW

            machines[machine_id] = MachineInfo(
                machine_id=machine_id,
                machine_type=machine_type,
                location=f"Workshop {machine_id[-4:]}",
                name=f"Machine {machine_id}"
            )

        return machines

    def _generate_sensor_data(self, machine_type: MachineType) -> MachineSensorData:
        """
        Generate realistic sensor data berdasarkan tipe mesin.

        Args:
            machine_type: Tipe mesin (L/M/H)

        Returns:
            MachineSensorData: Data sensor yang digenerate
        """
        base_temp = 298.0

        if machine_type == MachineType.HIGH:
            base_temp += random.uniform(0, 5)
        elif machine_type == MachineType.MEDIUM:
            base_temp += random.uniform(0, 3)

        air_temp = base_temp + np.random.normal(0, 2)

        process_temp = air_temp + random.uniform(8, 12) + np.random.normal(0, 1)

        if machine_type == MachineType.HIGH:
            speed = random.gauss(2000, 300)
        elif machine_type == MachineType.MEDIUM:
            speed = random.gauss(1550, 200)
        else:
            speed = random.gauss(1300, 150)

        speed = max(0, min(3000, speed))

        base_torque = 40.0
        if speed > 1500:
            base_torque -= (speed - 1500) * 0.01

        torque = max(0, base_torque + np.random.normal(0, 10))

        tool_wear = random.randint(0, 250)

        return MachineSensorData(
            air_temperature=round(air_temp, 1),
            process_temperature=round(process_temp, 1),
            rotational_speed=round(speed, 0),
            torque=round(torque, 1),
            tool_wear=tool_wear
        )

    def _determine_machine_status(self, sensor_data: MachineSensorData,
                                 machine_type: MachineType) -> Tuple[MachineStatus, float]:
        """
        Tentukan status mesin berdasarkan sensor data.

        Args:
            sensor_data: Data sensor dari mesin
            machine_type: Tipe mesin

        Returns:
            Tuple[MachineStatus, float]: Status dan probabilitas failure
        """
        risk_score = 0

        if sensor_data.air_temperature > settings.TEMP_THRESHOLD:
            risk_score += 2
        if sensor_data.process_temperature > settings.TEMP_THRESHOLD + 10:
            risk_score += 2

        if sensor_data.rotational_speed > settings.SPEED_THRESHOLD:
            risk_score += 3

        if sensor_data.torque > settings.TORQUE_THRESHOLD:
            risk_score += 2

        if sensor_data.tool_wear > settings.TOOL_WEAR_THRESHOLD:
            risk_score += 2

        if machine_type == MachineType.HIGH:
            risk_score *= 0.8
        elif machine_type == MachineType.LOW:
            risk_score *= 1.2

        if risk_score <= 3:
            status = MachineStatus.NORMAL
            probability = min(0.05 + (risk_score * 0.05), 0.25)
        elif risk_score <= 6:
            status = MachineStatus.WARNING
            probability = min(0.25 + ((risk_score - 3) * 0.1), 0.6)
        else:
            status = MachineStatus.FAILURE
            probability = min(0.6 + ((risk_score - 6) * 0.07), 0.95)

        return status, probability

    def _generate_recommendation(self, status: MachineStatus,
                                sensor_data: MachineSensorData) -> Optional[str]:
        """
        Generate maintenance recommendation.

        Args:
            status: Status mesin
            sensor_data: Data sensor

        Returns:
            Optional[str]: Rekomendasi maintenance
        """
        if status == MachineStatus.NORMAL:
            return None

        recommendations = []

        if sensor_data.air_temperature > settings.TEMP_THRESHOLD:
            recommendations.append("Periksa sistem pendingin mesin")

        if sensor_data.process_temperature > settings.TEMP_THRESHOLD + 10:
            recommendations.append("Monitor suhu proses dan material yang digunakan")

        if sensor_data.rotational_speed > settings.SPEED_THRESHOLD:
            recommendations.append("Kurangi kecepatan operasional atau periksa balancing")

        if sensor_data.torque > settings.TORQUE_THRESHOLD:
            recommendations.append("Periksa beban mesin dan komponen mekanis")

        if sensor_data.tool_wear > settings.TOOL_WEAR_THRESHOLD:
            recommendations.append("Segera ganti tool/komponen yang aus")

        if not recommendations:
            recommendations.append("Lakukan inspeksi menyeluruh dan maintenance preventif")

        return "; ".join(recommendations)

    def get_machine_status(self, machine_id: str) -> Optional[MachineStatusResponse]:
        """
        Dapatkan status mesin tertentu dengan sensor data real-time.

        Args:
            machine_id: ID mesin yang dicari

        Returns:
            Optional[MachineStatusResponse]: Status mesin atau None jika tidak ditemukan
        """
        if machine_id not in self.machines:
            return None

        machine_info = self.machines[machine_id]
        sensor_data = self._generate_sensor_data(machine_info.machine_type)
        status, probability = self._determine_machine_status(sensor_data, machine_info.machine_type)
        recommendation = self._generate_recommendation(status, sensor_data)

        return MachineStatusResponse(
            machine_id=machine_id,
            machine_type=machine_info.machine_type,
            sensor_data=sensor_data,
            status=status,
            failure_probability=round(probability, 2),
            last_updated=datetime.utcnow(),
            recommendation=recommendation
        )

    def get_all_machines_status(self) -> AllMachinesResponse:
        """
        Dapatkan status semua mesin.

        Returns:
            AllMachinesResponse: Status semua mesin dengan summary
        """
        machines_status = []
        high_risk_machines = []
        status_count = {
            MachineStatus.NORMAL: 0,
            MachineStatus.WARNING: 0,
            MachineStatus.FAILURE: 0
        }

        for machine_id in self.machines.keys():
            machine_status = self.get_machine_status(machine_id)
            if machine_status:
                machines_status.append(machine_status)
                status_count[machine_status.status] += 1

                if machine_status.status in [MachineStatus.WARNING, MachineStatus.FAILURE]:
                    high_risk_machines.append(machine_id)

        return AllMachinesResponse(
            total_machines=len(machines_status),
            machines=machines_status,
            high_risk_machines=high_risk_machines,
            summary={
                "normal": status_count[MachineStatus.NORMAL],
                "warning": status_count[MachineStatus.WARNING],
                "failure": status_count[MachineStatus.FAILURE]
            }
        )

    def get_machines_by_status(self, status: MachineStatus) -> List[MachineStatusResponse]:
        """
        Dapatkan mesin berdasarkan status tertentu.

        Args:
            status: Status mesin yang dicari

        Returns:
            List[MachineStatusResponse]: List mesin dengan status tersebut
        """
        all_status = self.get_all_machines_status()
        return [machine for machine in all_status.machines if machine.status == status]

    def get_high_risk_machines(self) -> List[MachineStatusResponse]:
        """
        Dapatkan mesin-mesin dengan risiko tinggi (Warning/Failure).

        Returns:
            List[MachineStatusResponse]: List mesin berisiko tinggi
        """
        all_status = self.get_all_machines_status()
        return [machine for machine in all_status.machines
                if machine.status in [MachineStatus.WARNING, MachineStatus.FAILURE]]


machine_service = MachineService()