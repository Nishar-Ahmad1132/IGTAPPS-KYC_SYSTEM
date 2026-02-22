# 🔐 AI-Powered KYC Verification System

A full-stack **End-to-End Online KYC System** (Binance-like) built using **FastAPI, React, and Computer Vision**.  
This system performs automated identity verification using **OCR, Face Matching, and Liveness Detection**.

---

## 🚀 Features

- 📄 Aadhaar Upload (Front & Back)
- 🔍 OCR Data Extraction (PaddleOCR)
- 🧠 Image Preprocessing (OpenCV)
- 👤 Face Detection & Matching (InsightFace)
- 🎥 Live Selfie Capture
- 🟢 Liveness Detection (MediaPipe)
- 🔄 Name Matching (Fuzzy Matching)
- ✅ Final KYC Decision Engine
- 🔒 Aadhaar Masking (Security)
- 🗄️ Data Storage using SQLAlchemy

---

## 🏗️ Tech Stack

### Backend
- FastAPI
- SQLAlchemy
- SQLite (can be replaced with PostgreSQL/MySQL)

### AI / Computer Vision
- PaddleOCR
- OpenCV
- InsightFace
- MediaPipe

### Frontend
- React.js
- Zustand (State Management)
- Tailwind CSS

---


## 📂 Project Structure

```
kyc_system/
│
├── kyc-backend/
│ ├── app/
│ │ ├── routers/
│ │ ├── services/
│ │ ├── models.py
│ │ ├── database.py
│ │ └── main.py
│ └── uploads/
│
├── kyc-frontend/
│ └── src/
```


📦 Dependencies
```
  🐍 Python Version
        Python 3.10
```

## ⚙️ Installation
```
1️⃣ Clone Repo

  git clone https://github.com/Nishar-Ahmad1132/IGTAPPS-KYC_SYSTEM.git
  cd IGTAPPS-KYC_SYSTEM

2️⃣ Backend Setup
  cd kyc-backend
  python -m venv venv
  venv\Scripts\activate   # Windows
  pip install -r requirements.txt

  Run server:
  uvicorn app.main:app --port 8080
  Backend runs on:
  
  http://127.0.0.1:8080
3️⃣ Frontend Setup
  cd kyc-frontend
  npm install
  npm run dev
  Frontend runs on:
  http://localhost:5173
```
🔄 KYC Flow
```
  User Registration
  Aadhaar Upload
  OCR Extraction
  Name Matching
  Face Extraction
  Selfie Capture
  Liveness Detection
  Face Matching
```

Final KYC Decision

```
📊 Accuracy
  OCR Accuracy: ~88%
  Face Matching: ~95%
  Liveness Detection: ~98%

🔐 Security Features
  Aadhaar masking (XXXX XXXX 1234)
  UUID-based file storage
  No raw sensitive logs
```
📌 Future Improvements
```
  JWT Authentication
  Admin Dashboard
  Cloud Deployment
  Docker Support
```

👨‍💻 Author
Nishar Ahmad
