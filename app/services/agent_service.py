import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from app.core.config import settings
from app.services.prediction_service import prediction_service
from app.services.machine_service import machine_service
from app.schemas.prediction import PredictionInputSchema
from app.schemas.machine import MachineStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentService:
    """
    Service untuk AI Agent dengan LangChain integration.

    Agent ini dapat:
    - Menjawab general knowledge tentang predictive maintenance
    - Melakukan prediksi kerusakan mesin
    - Memberikan status mesin real-time
    - Menganalisis mesin mana yang paling berisiko
    """

    def __init__(self):
        """Inisialisasi agent dengan LLM dan tools."""
        self.llm = None
        self.agent_executor = None
        self._initialize_agent()

    def _initialize_agent(self) -> None:
        """Inisialisasi agent OpenAI dengan tools."""
        try:
            if not settings.OPENAI_API_KEY:
                logger.warning("OPENAI_API_KEY not found. Agent will not be available.")
                return

            self.llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0.1,
                openai_api_key=settings.OPENAI_API_KEY
            )

            tools = [
                self._create_prediction_tool(),
                self._create_machine_status_tool(),
                self._create_all_machines_tool(),
                self._create_high_risk_tool()
            ]

            prompt = ChatPromptTemplate.from_messages([
                ("system", self._get_system_prompt()),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ])

            agent = create_openai_functions_agent(
                llm=self.llm,
                tools=tools,
                prompt=prompt
            )

            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )

            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                memory=memory,
                verbose=True,
                handle_parsing_errors=True
            )

            logger.info("Agent initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing agent: {e}")
            self.agent_executor = None

    def _get_system_prompt(self) -> str:
        """Dapatkan system prompt untuk agent."""
        return f"""
        Anda adalah AI Assistant untuk Predictive Maintenance Copilot.
        Tugas utama Anda adalah membantu user memantau dan memprediksi kondisi mesin industri.

        **Kemampuan Anda:**
        1. Prediksi kerusakan mesin menggunakan data sensor (gunakan tool predict_machine_failure)
        2. Dapatkan status mesin real-time (gunakan tool get_machine_status)
        3. Lihat status semua mesin (gunakan tool get_all_machines_status)
        4. Identifikasi mesin berisiko tinggi (gunakan tool get_high_risk_machines)

        **Machine IDs yang tersedia:**
        {', '.join(settings.MACHINE_IDS)}

        **Threshold yang digunakan:**
        - Temperature: {settings.TEMP_THRESHOLD}K
        - Speed: {settings.SPEED_THRESHOLD} RPM
        - Torque: {settings.TORQUE_THRESHOLD} Nm
        - Tool Wear: {settings.TOOL_WEAR_THRESHOLD} minutes

        **Status Mesin:**
        - Normal: Mesin dalam kondisi baik
        - Warning: Perlu monitoring lebih lanjut
        - Failure: Kemungkinan besar akan rusak, segera maintenance

        **Format respons:**
        - Gunakan bahasa Indonesia yang jelas dan profesional
        - Berikan rekomendasi maintenance yang spesifik
        - Sertakan data pendukung (probabilitas, nilai sensor)
        - Jangan membuat asumsi yang tidak didukung data

        Jika user menanyakan sesuatu di luar scope maintenance mesin,
        berikan jawaban general dengan arahkan kembali ke topik maintenance.
        """

    def _create_prediction_tool(self):
        """Buat tool untuk prediksi kerusakan mesin."""

        @tool
        def predict_machine_failure(
            air_temperature: float,
            process_temperature: float,
            rotational_speed: float,
            torque: float,
            tool_wear: int
        ) -> Dict[str, Any]:
            """
            Prediksi kerusakan mesin berdasarkan data sensor.

            Args:
                air_temperature: Suhu udara dalam Kelvin (250-350)
                process_temperature: Suhu proses dalam Kelvin (250-350)
                rotational_speed: Kecepatan rotasi dalam RPM (0-3000)
                torque: Torsi dalam Nm (0-100)
                tool_wear: Keausan alat dalam menit (0-500)

            Returns:
                Dict dengan prediksi status dan probabilitas
            """
            try:
                input_data = PredictionInputSchema(
                    air_temperature=air_temperature,
                    process_temperature=process_temperature,
                    rotational_speed=rotational_speed,
                    torque=torque,
                    tool_wear=tool_wear
                )

                result = prediction_service.predict(input_data)

                return {
                    "status": result.machine_status.value,
                    "probability": result.probability,
                    "message": result.message
                }

            except Exception as e:
                logger.error(f"Error in prediction tool: {e}")
                return {
                    "status": "Error",
                    "probability": 0.0,
                    "message": f"Terjadi kesalahan: {str(e)}"
                }

        return predict_machine_failure

    def _create_machine_status_tool(self):
        """Buat tool untuk mendapatkan status mesin tertentu."""

        @tool
        def get_machine_status(machine_id: str) -> Dict[str, Any]:
            """
            Dapatkan status real-time dari mesin tertentu.

            Args:
                machine_id: ID mesin yang akan dicek (contoh: M14860, L4718)

            Returns:
                Dict dengan status mesin dan data sensor
            """
            try:
                if machine_id not in settings.MACHINE_IDS:
                    return {
                        "error": f"Machine ID {machine_id} tidak valid. "
                                f"Gunakan salah satu: {', '.join(settings.MACHINE_IDS[:5])}..."
                    }

                status = machine_service.get_machine_status(machine_id)
                if not status:
                    return {"error": "Mesin tidak ditemukan"}

                return {
                    "machine_id": status.machine_id,
                    "machine_type": status.machine_type.value,
                    "status": status.status.value,
                    "failure_probability": status.failure_probability,
                    "sensor_data": {
                        "air_temperature": status.sensor_data.air_temperature,
                        "process_temperature": status.sensor_data.process_temperature,
                        "rotational_speed": status.sensor_data.rotational_speed,
                        "torque": status.sensor_data.torque,
                        "tool_wear": status.sensor_data.tool_wear
                    },
                    "last_updated": status.last_updated.isoformat(),
                    "recommendation": status.recommendation
                }

            except Exception as e:
                logger.error(f"Error in machine status tool: {e}")
                return {"error": f"Terjadi kesalahan: {str(e)}"}

        return get_machine_status

    def _create_all_machines_tool(self):
        """Buat tool untuk mendapatkan status semua mesin."""

        @tool
        def get_all_machines_status() -> Dict[str, Any]:
            """
            Dapatkan status dari semua mesin yang tersedia.

            Returns:
                Dict dengan summary dan detail semua mesin
            """
            try:
                result = machine_service.get_all_machines_status()

                machines_summary = []
                for machine in result.machines[:5]:
                    machines_summary.append({
                        "machine_id": machine.machine_id,
                        "status": machine.status.value,
                        "probability": machine.failure_probability
                    })

                return {
                    "total_machines": result.total_machines,
                    "summary": result.summary,
                    "high_risk_count": len(result.high_risk_machines),
                    "sample_machines": machines_summary,
                    "high_risk_machines": result.high_risk_machines[:5]
                }

            except Exception as e:
                logger.error(f"Error in all machines tool: {e}")
                return {"error": f"Terjadi kesalahan: {str(e)}"}

        return get_all_machines_status

    def _create_high_risk_tool(self):
        """Buat tool untuk mendapatkan mesin berisiko tinggi."""

        @tool
        def get_high_risk_machines() -> Dict[str, Any]:
            """
            Identifikasi mesin-mesin dengan risiko kerusakan tinggi.

            Returns:
                Dict dengan daftar mesin berisiko tinggi dan analysis
            """
            try:
                high_risk = machine_service.get_high_risk_machines()

                if not high_risk:
                    return {
                        "message": "Tidak ada mesin dengan risiko tinggi saat ini",
                        "count": 0,
                        "machines": []
                    }

                high_risk.sort(key=lambda x: x.failure_probability, reverse=True)

                risk_analysis = []
                for machine in high_risk:
                    risk_analysis.append({
                        "machine_id": machine.machine_id,
                        "machine_type": machine.machine_type.value,
                        "status": machine.status.value,
                        "probability": machine.failure_probability,
                        "main_issue": self._identify_main_issue(machine.sensor_data),
                        "recommendation": machine.recommendation
                    })

                return {
                    "count": len(high_risk),
                    "highest_risk": risk_analysis[0] if risk_analysis else None,
                    "machines": risk_analysis,
                    "message": f"Ditemukan {len(high_risk)} mesin dengan risiko tinggi yang memerlukan perhatian"
                }

            except Exception as e:
                logger.error(f"Error in high risk tool: {e}")
                return {"error": f"Terjadi kesalahan: {str(e)}"}

        return get_high_risk_machines

    def _identify_main_issue(self, sensor_data) -> str:
        """Identifikasi masalah utama dari sensor data."""
        issues = []

        if sensor_data.air_temperature > settings.TEMP_THRESHOLD:
            issues.append("suhu udara tinggi")

        if sensor_data.process_temperature > settings.TEMP_THRESHOLD + 10:
            issues.append("suhu proses tinggi")

        if sensor_data.rotational_speed > settings.SPEED_THRESHOLD:
            issues.append("kecepatan rotasi tinggi")

        if sensor_data.torque > settings.TORQUE_THRESHOLD:
            issues.append("torsi tinggi")

        if sensor_data.tool_wear > settings.TOOL_WEAR_THRESHOLD:
            issues.append("keausan tool tinggi")

        return issues[0] if issues else "parameter normal"

    async def chat(self, query: str) -> str:
        """
        Metode utama untuk chat dengan agent.

        Args:
            query: Pertanyaan dari user

        Returns:
            str: Jawaban dari agent
        """
        if not self.agent_executor:
            return "Maaf, AI Agent tidak tersedia. Pastikan OPENAI_API_KEY sudah dikonfigurasi dengan benar."

        try:
            response = await self.agent_executor.ainvoke({
                "input": query
            })

            return response.get("output", "Maaf, tidak dapat memproses permintaan Anda.")

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return f"Maaf, terjadi kesalahan: {str(e)}"

    def is_available(self) -> bool:
        """Check apakah agent tersedia."""
        return self.agent_executor is not None


agent_service = AgentService()