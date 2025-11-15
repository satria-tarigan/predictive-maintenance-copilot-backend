# [AC-02] Predictive Maintenance Copilot - Backend API

Repositori ini berisi Backend API untuk Proyek Capstone [AC-02]. API ini dibangun menggunakan **FastAPI** (Python) dan berfungsi sebagai otak di balik aplikasi web.

## 🚀 Setup Lokal

1.  **Buat Virtual Environment**
    ```bash
    python -m venv venv
    ```

2.  **Aktifkan Environment**
    ```bash
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Buat File `.env`**
    Buat file `.env` di root folder untuk menyimpan API key Anda.
    ```.env
    OPENAI_API_KEY="sk-..."
    ```
    
5.  **Dapatkan Model ML**
    Letakkan file model (`anomaly_model.pkl`) dari tim ML ke dalam folder `app/models/`.
    *(Jika Anda belum memilikinya, jalankan `python create_dummy_model.py` untuk membuat file placeholder)*.

6.  **Jalankan Server**
    ```bash
    uvicorn app.main:app --reload
    ```

7.  **Buka Dokumentasi**
    Buka browser Anda dan navigasi ke `http://127.0.0.1:8000/docs`.