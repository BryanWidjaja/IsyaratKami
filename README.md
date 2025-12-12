# IsyaratKami - Real-time SIBI Sign Language Translator

IsyaratKami is a real-time SIBI (Sistem Isyarat Bahasa Indonesia) sign language translator application. It uses computer vision and machine learning to detect hand gestures and translate them into text, assisting in communication for the deaf and hard of hearing.

## Features

- **Real-time Sign Detection**: Uses MediaPipe and OpenCV to detect hand landmarks and classify SIBI gestures.
- **Sentence Formation**: Accumulates detected characters into words and sentences with debounce logic.
- **AI Autocomplete**: Integrates OpenRouter API (DeepSeek) to suggest next words and correct sentences contextually.
- **Dual Interface**:
  - **Web App**: A modern React-based web interface.
  - **Desktop Overlay**: A PyQt5-based transparent overlay for using the sign translator on top of other applications (e.g., Zoom, Google Meet).

## Technology Stack

- **Backend**: Python, FastAPI, uvicorn
- **Frontend**: JavaScript, React, Vite, MediaPipe
- **Machine Learning**: OpenCV, MediaPipe Hands, scikit-learn (Random Forest Classifier)
- **AI/LLM**: OpenRouter API (DeepSeek Model)

## Progress List

- [x] Input screen
- [x] Input screen resizeable
- [x] Output resizeable
- [x] Debounce timer on detection to caption
- [ ] New Dataset, clearer, more words, atleast all commonly used words
- [ ] Sentence prediction model comparison based on current sign vs predicted word
- [ ] Mobile version

## How to Run

### Option 1: Docker

This gives you the full web application experience.

1. Install Docker Desktop.
2. Run the following command in the root directory:
   ```bash
   docker-compose up --build
   ```
3. Open `http://localhost:5173` in your browser.

### Option 2: Manual Setup

#### Backend

1. Create and activate a virtual environment (optional but recommended):
   ```bash
   uv venv
   .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```
3. Run the server:
   ```bash
   uv run server.py
   ```
   The backend runs on `http://localhost:8000`.

#### Frontend

1. Navigate to the web directory:
   ```bash
   cd web
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
   The frontend runs on `http://localhost:5173`.

## How to Train / Update the Model

The machine learning model (`sibi_model.pkl`) is trained using the dataset located in the `SIBI` folder. To retrain the model with a new or improved dataset:

1. **Prepare Dataset**: Organize your images in the `SIBI` directory. Each subfolder should be named after the class (e.g., `A`, `B`, `Hello`) and contain the corresponding images.
2. **Delete Existing Model**: Delete the file `sibi_model.pkl` in the root directory.
3. **Run Training**: Execute the application script:
   ```bash
   uv run app.py
   ```
   The script checks for the model file. If missing, it will automatically iterate through the `SIBI` folder, extract landmarks, and train a new Random Forest model.
4. **Completion**: Once you see "Model saved as sibi_model.pkl" in the console, the training is complete. You can then close the application window.
