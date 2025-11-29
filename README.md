# [AC-02] Predictive Maintenance Copilot - Backend API

Repositori ini berisi Backend API untuk Proyek Capstone [AC-02]. API ini dibangun menggunakan **FastAPI** (Python) dengan integrasi **LangChain** dan **OpenAI** untuk memberikan solusi prediktif maintenance yang cerdas.

## ✨ Fitur Utama

- **Prediksi Kerusakan Mesin**: Menggunakan model LSTM yang sudah dilatih (`LSTM_Model.h5`)
- **Monitoring Real-time**: Simulasi data sensor untuk 20 mesin industri
- **AI Chatbot**: Agent cerdas dengan LangChain untuk menjawab query maintenance
- **RESTful API**: Dokumentasi otomatis dengan FastAPI (Swagger/ReDoc)
- **Data Dummy**: Realistis sensor simulation untuk development & testing

## 🏗️ Struktur Proyek

```
predictive-maintenance-copilot-backend/
├── app/
│   ├── api/                    # API routers
│   │   └── v1/
│   │       ├── api.py         # Router aggregation
│   │       └── endpoints/
│   │           ├── prediction.py  # /predict endpoints
│   │           ├── chat.py        # /chat endpoints
│   │           └── machine.py     # /machines endpoints
│   ├── core/                   # Configuration
│   │   └── config.py         # Settings & env variables
│   ├── models/                 # ML models storage
│   │   └── LSTM_Model.h5     # Trained LSTM model
│   ├── schemas/                # Pydantic models
│   │   ├── prediction.py     # Prediction schemas
│   │   ├── machine.py        # Machine data schemas
│   │   └── chat.py           # Chat schemas
│   ├── services/              # Business logic
│   │   ├── prediction_service.py  # ML prediction logic
│   │   ├── machine_service.py     # Machine monitoring logic
│   │   └── agent_service.py       # LangChain agent logic
│   └── main.py               # FastAPI app initialization
├── tests/                    # Unit tests
├── .env.example              # Environment template
├── .gitignore
├── Dockerfile               # Container configuration
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🚀 Setup Lokal

### 1. Prerequisites

- Python 3.11+
- pip
- Git

### 2. Clone Repository

```bash
git clone <repository-url>
cd predictive-maintenance-copilot-backend
```

### 3. Setup Virtual Environment

```bash
# Buat virtual environment
python -m venv venv

# Aktivasi environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Environment Configuration

Buat file `.env` di root folder:

```bash
cp .env.example .env
```

Edit `.env` file:

```env
# OpenAI Configuration
OPENAI_API_KEY="sk-your-openai-api-key-here"

# Server Configuration (optional)
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

### 6. Model ML Setup

Letakkan file model (`LSTM_Model.h5`) dari tim ML ke dalam folder `app/models/`:

```bash
# Pastikan LSTM_Model.h5 ada di lokasi ini
app/models/LSTM_Model.h5
```

### 7. Jalankan Server

```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Atau menggunakan script
python -m app.main
```

### 8. Akses API

- **API Documentation**: http://127.0.0.1:8000/docs (Swagger UI)
- **ReDoc**: http://127.0.0.1:8000/redoc
- **Health Check**: http://127.0.0.1:8000/

## 📡 API Endpoints

### Health & Root
- `GET /` - Server status
- `GET /favicon.ico` - Favicon (no content)

### Prediction API (`/api/v1/prediction`)
- `POST /predict` - Prediksi kerusakan mesin
- `GET /model-status` - Status model ML

**Request Body (/predict):**
```json
{
  "air_temperature": 298.5,
  "process_temperature": 308.8,
  "rotational_speed": 1550,
  "torque": 45.5,
  "tool_wear": 120
}
```

**Response:**
```json
{
  "machine_status": "Normal",
  "probability": 0.15,
  "message": "Mesin dalam kondisi normal dan stabil."
}
```

### Machine Monitoring API (`/api/v1/machines`)
- `GET /status` - Status semua mesin
- `GET /status/{machine_id}` - Status mesin spesifik
- `GET /high-risk` - Mesin berisiko tinggi
- `POST /predict/{machine_id}` - Prediksi untuk mesin spesifik
- `GET /by-status/{status}` - Filter berdasarkan status
- `GET /list` - Daftar semua machine ID

**Available Machine IDs:**
- M14860, M14865, M14868, M14869, M14872
- M14873, M14876, M14877, M14879
- L4718, L47182, L47183, L47184, L47186
- L47187, L47194, L47195
- H29424, H29425, H29432, H29434

### Chatbot API (`/api/v1/chat`)
- `POST /` - Interaksi dengan chatbot AI
- `GET /status` - Status chatbot

**Request Body:**
```json
{
  "query": "Mesin mana yang paling berisiko?"
}
```

**Response:**
```json
{
  "response": "Berdasarkan analisis data terkini, mesin M14860 menunjukkan..."
}
```

**Example Queries:**
- "Prediksi mesin M14860"
- "Mesin mana yang paling berisiko?"
- "Bagaimana cara mengecek status semua mesin?"
- "Apa penyebab kerusakan mesin jika suhu tinggi?"
- "Berikan rekomendasi maintenance untuk mesin dengan torsi tinggi"

## 🐳 Docker Deployment

### Build Docker Image

```bash
docker build -t predictive-maintenance-api .
```

### Run Container

```bash
docker run -p 8000:8000 \
  -e OPENAI_API_KEY="your-api-key" \
  -v $(pwd)/app/models:/app/app/models \
  predictive-maintenance-api
```

### Docker Compose

```bash
docker-compose up -d
```

## 🧪 Testing

### Run Unit Tests

```bash
# Install test dependencies (already in requirements.txt)
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_predictions.py -v
```

### API Testing

```bash
# Test prediction endpoint
curl -X POST "http://localhost:8000/api/v1/prediction/predict" \
  -H "Content-Type: application/json" \
  -d '{"air_temperature": 298.5, "process_temperature": 308.8, "rotational_speed": 1550, "torque": 45.5, "tool_wear": 120}'

# Test machine status
curl "http://localhost:8000/api/v1/machines/status/M14860"

# Test chatbot
curl -X POST "http://localhost:8000/api/v1/chat/" \
  -H "Content-Type: application/json" \
  -d '{"query": "Mesin mana yang paling berisiko?"}'
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key untuk chatbot | Required |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `DEBUG` | Debug mode | `false` |
| `MODEL_FILE_PATH` | Path ke model ML | `app/models/LSTM_Model.h5` |

### Machine Status Thresholds

- **Temperature**: 300K
- **Rotational Speed**: 1500 RPM
- **Torque**: 50 Nm
- **Tool Wear**: 200 minutes

## 📊 Machine Status Types

- **Normal**: Mesin dalam kondisi baik (probability < 0.3)
- **Warning**: Perlu monitoring lanjut (0.3 ≤ probability < 0.7)
- **Failure**: Risiko kerusakan tinggi (probability ≥ 0.7)

## 🤖 AI Agent Capabilities

Chatbot AI dapat:
- Prediksi kerusakan mesin berdasarkan data sensor
- Analisis status mesin real-time
- Identifikasi mesin berisiko tinggi
- Memberikan rekomendasi maintenance
- Menjawab general knowledge tentang predictive maintenance

## 🐛 Troubleshooting

### Common Issues

1. **OpenAI API Key Error**
   ```
   Solution: Pastikan OPENAI_API_KEY valid di file .env
   ```

2. **Model Not Found**
   ```
   Solution: Letakkan LSTM_Model.h5 di app/models/
   ```

3. **Port Already in Use**
   ```bash
   Solution: Kill process atau ganti port
   # Windows
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F
   # Linux/macOS
   lsof -ti:8000 | xargs kill -9
   ```

4. **Import Errors**
   ```bash
   Solution: Install ulang dependencies
   pip install -r requirements.txt --force-reinstall
   ```

### Debug Mode

Enable debug mode di `.env`:
```env
DEBUG=true
```

## 📚 API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🚀 Production Deployment

### Environment Setup

1. Set production environment variables
2. Configure proper CORS origins
3. Setup reverse proxy (nginx/Apache)
4. Enable HTTPS
5. Setup monitoring and logging

### Platform Deployment

- **Render**: Connect repository dan set build command
- **Railway**: Deploy via GitHub integration
- **AWS ECS**: Use Dockerfile for container deployment
- **Google Cloud Run**: Serverless container deployment

## 🤝 Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

Untuk pertanyaan atau support, hubungi tim development atau buka issue di repository.

