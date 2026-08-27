# TourMateAI 🌴

*An Intelligent AI-Based Travel Companion for Sri Lanka.*

TourMateAI is a comprehensive full-stack web application designed to give tourists personalized, context-aware travel assistance. It leverages modern AI capabilities to provide recommendations based on user preferences, weather, and location, alongside an intelligent RAG chatbot, a multi-agent itinerary planner, and landmark image recognition.

> **Note:** University final project — CIS6035, Cardiff Metropolitan / ICBT. Academic MVP, free-tier tooling.

---

## 🌟 Key Features

- **Personalized Recommendations**: Content-based recommendation engine (scikit-learn) that suggests attractions and hotels based on user interests, real-time weather, and location.
- **AI RAG Chatbot**: Powered by Google Gemini and ChromaDB vector store to answer travel and transport queries with Sri Lanka-specific context.
- **Multi-Agent Itinerary Planner**: Uses LangGraph and LangChain to automatically generate day-by-day optimal travel plans and schedules.
- **Landmark Image Recognition**: Upload a photo of a Sri Lankan landmark, and our custom MobileNetV2 CNN identifies it and links to attraction details.
- **Multi-Language Support**: Real-time localized interface with dynamic Sinhala and Italian translations.
- **Interactive Maps & Weather**: Route optimization and weather forecasting via Google Maps Routes API and OpenWeather API.
- **Admin Portal**: Manage attractions, hotels, view uploaded images, and inspect analytics.

---

## 🏗️ Architecture & Tech Stack

```
TourMateAI/
├── frontend/       # React 19 SPA + Vite + Vanilla CSS
├── backend/        # Python Flask modular monolith + SQLAlchemy + Alembic
│   ├── app/
│   │   ├── ai/     # AI Engine (Vision CNN, LangGraph planner, RAG chatbot, Recommender)
│   │   ├── routes/ # REST API endpoints
│   │   └── models/ # Database schema models
│   ├── data/       # Datasets & ChromaDB vector stores
│   └── scripts/    # Database seeding & ingestion scripts
└── docs/           # Architecture and API documentation
```

### Tech Stack:
- **Frontend**: React 19, Vite, React Router, i18next, Axios, Vanilla CSS
- **Backend**: Python 3.10+, Flask, SQLAlchemy, Flask-Migrate, PyMySQL, Firebase Admin SDK
- **Database**: MySQL 8.0+
- **AI & ML**: TensorFlow / Keras, Scikit-Learn, LangGraph, LangChain, Google Generative AI (Gemini), ChromaDB, Sentence-Transformers

---

## 🚀 Complete Step-by-Step Run Instructions

Follow these instructions to set up and run TourMateAI locally from scratch.

### 📋 Prerequisites

Make sure you have the following installed on your machine:
- **[Node.js](https://nodejs.org/)** (v18 or v20+ recommended) & `npm`
- **[Python 3.10+](https://www.python.org/downloads/)** & `pip`
- **[MySQL Server](https://dev.mysql.com/downloads/mysql/)** (Running locally on port 3306)
- **API Keys & Credentials**:
  - [Google Gemini API Key](https://aistudio.google.com/)
  - [Google Maps API Key](https://console.cloud.google.com/) *(Enable Maps JavaScript API and Routes API)*
  - [OpenWeather API Key](https://openweathermap.org/api)
  - Firebase Web Config & `serviceAccountKey.json` from [Firebase Console](https://console.firebase.google.com/)

---

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/TourMateAI.git
cd TourMateAI
```

---

### 2. Database Setup

1. Start your MySQL service.
2. Open your MySQL client or terminal and create the database:
   ```sql
   CREATE DATABASE tourmateai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

---

### 3. Backend Setup

1. Navigate into the `backend` folder:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Install the required Python dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Configure backend environment variables:
   - Create a `.env` file inside the `backend/` directory (or copy from root `.env.example`):
     ```env
     FLASK_ENV=development
     FLASK_APP=run.py
     SECRET_KEY=your-flask-secret-key-12345

     # Database configuration
     DB_HOST=localhost
     DB_PORT=3306
     DB_NAME=tourmateai
     DB_USER=root
     DB_PASSWORD=your_mysql_password

     # External APIs
     GEMINI_API_KEY=your_gemini_api_key
     GOOGLE_MAPS_API_KEY=your_google_maps_api_key
     OPENWEATHER_API_KEY=your_openweather_api_key

     # Firebase Admin SDK (Place your serviceAccountKey.json in the backend/ directory)
     FIREBASE_CREDENTIALS=serviceAccountKey.json

     # AI Engine toggle: set to false to use real trained AI models
     USE_MOCK_AI=false
     ```

5. Run database migrations:
   ```bash
   flask db upgrade
   ```

6. Seed initial attractions, hotels, and admin user:
   ```bash
   # Seeds attractions & creates default admin account
   flask seed-db

   # Seeds sample hotels
   python scripts/seed_hotels.py
   ```

---

### 4. Train the Landmark Vision Model 🤖

The CNN vision model (`landmark_cnn.keras`) is trained locally on the Sri Lankan landmark dataset located in `backend/data/dataset`.

1. Ensure your virtual environment is activated and your terminal is in the `backend` folder.
2. Execute the training pipeline as a module:
   ```bash
   python -m app.ai.vision.train
   ```
3. Once training completes, the model is saved to `backend/app/ai/vision/landmark_cnn.keras` and ready for inference.

---

### 5. Frontend Setup

1. Open a **new** terminal window and navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```

2. Install the JavaScript dependencies:
   ```bash
   npm install
   ```

3. Configure frontend environment variables:
   - Create or edit `frontend/.env`:
     ```env
     # Points directly to the Flask backend
     VITE_API_BASE_URL=http://localhost:5000/api

     # Google Maps key for frontend map view
     VITE_GOOGLE_MAPS_API_KEY=your_google_maps_api_key

     # Firebase Web App Config
     VITE_FIREBASE_API_KEY=your_firebase_api_key
     VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
     VITE_FIREBASE_PROJECT_ID=your_project_id
     VITE_FIREBASE_STORAGE_BUCKET=your_project.firebasestorage.app
     VITE_FIREBASE_MESSAGING_SENDER_ID=your_messaging_sender_id
     VITE_FIREBASE_APP_ID=your_app_id
     ```

---

### 6. Running the Application

You will need **two terminal windows** running simultaneously:

#### Terminal 1: Backend Server
```bash
cd backend
# Activate venv if not active:
# .\venv\Scripts\Activate.ps1  (Windows) or source venv/bin/activate (Linux/Mac)
python run.py
```
> Backend runs at: **`http://localhost:5000`**

#### Terminal 2: Frontend Server
```bash
cd frontend
npm run dev
```
> Frontend runs at: **`http://localhost:5173`**

Open your web browser and navigate to **`http://localhost:5173`**.

---

## 🔑 Default Accounts & Access

- **Admin Account**: 
  - The `flask seed-db` command creates an admin user with the email `admin@tourmate.ai`.
  - To log in as admin, create a user in your Firebase Authentication console (or sign up via the app) with the email `admin@tourmate.ai`.
  - Once logged in, the **Admin** navigation tab will appear in the top bar (`/admin/attractions`, `/admin/hotels`, `/admin/analytics`).

---

## 🛠️ Common Troubleshooting

| Issue | Cause | Solution |
|---|---|---|
| `ModuleNotFoundError: No module named 'deep_translator'` | Python environment missing package or venv not activated. | Run `.\venv\Scripts\Activate.ps1` and run `pip install -r requirements.txt`. |
| `ImportError: attempted relative import with no known parent package` | Running `python app/ai/vision/train.py` directly. | Run `python -m app.ai.vision.train` from the `backend` folder. |
| `404 Not Found on /api/...` | `VITE_API_BASE_URL` set to `/api` without proxy. | Set `VITE_API_BASE_URL=http://localhost:5000/api` in `frontend/.env` and restart Vite. |
| `TypeError: Cannot read properties of undefined (reading 'length')` | Cached error state or backend is not connected. | Ensure backend is running at `http://localhost:5000` and hard refresh browser (`Ctrl + Shift + R`). |
| Database connection error | MySQL service not running or wrong credentials in `.env`. | Verify MySQL is running on port 3306 and check `DB_USER` / `DB_PASSWORD` in `backend/.env`. |

---

## 📄 License & Attribution

This project was developed for academic purposes.
- Datasets and photos are attributed to their respective owners.
- Free-tier APIs from Google Gemini, Google Maps, OpenWeather, and Firebase.
"# TourMateAI" 
