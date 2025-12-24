# 🧾 Invoice Processing API (OCR + LLM)

A production-ready **FastAPI-based Invoice Processing API** that extracts structured invoice data from images using **OCR (Tesseract)** and a **local LLM (Ollama – Qwen 2.5)**, with metadata stored in **MongoDB**.

---

## ✨ Features

- 📤 Upload invoice images (`png`, `jpg`, `jpeg`)
- 🔍 OCR text extraction using **Tesseract**
- 🧠 Intelligent field extraction via **Ollama (Qwen 2.5 3B)**
- 📦 Stores invoices & extracted fields in **MongoDB**
- ⚡ FastAPI with auto-generated Swagger docs
- 🐳 Docker & Docker Compose support
- 🧪 Isolated test scripts for OCR, LLM, Mongo, and config

---

## 📁 Project Structure

```
invoice-api/
├── app/
│   ├── main.py
│   ├── config/
|   ├── routers/
│   ├── services/
│   ├── db/
│   └── utils/
├── invoices/
├── sample_invoices/
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── run.py
└── README.md
```

---

## 🚀 API Endpoint

### Upload Invoice
```
POST /invoices/upload
```

Swagger UI:
👉 http://127.0.0.1:8001/docs

---

## ⚙️ Environment Setup

```bash
git clone https://github.com/zainab-noor-25/invoice-api.git
cd invoice-api
cp .env.example .env
```

---

## 🐍 Run Locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

---

## 🐳 Run with Docker

```bash
docker compose up --build
```

Ensure Ollama model is available:
```bash
ollama pull qwen2.5:3b-instruct
```

---

## 🧪 Testing

```bash
python test_ocr.py
python test_ollama.py
python test_mongo.py
python test_config.py
```

---

## 👤 Author

**Zainab Noor**  
GitHub: https://github.com/zainab-noor-25
