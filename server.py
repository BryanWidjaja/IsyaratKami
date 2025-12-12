from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = "sibi_model.pkl"

classifier = None

@app.on_event("startup")
async def startup_event():
    global classifier
    print(f"Loading model from {MODEL_PATH}...")
    if os.path.exists(MODEL_PATH):
        try:
            classifier = joblib.load(MODEL_PATH)
            print("Model loaded successfully.")
        except Exception as e:
            print(f"Error loading model: {e}", file=sys.stderr)
    else:
        print(f"Warning: {MODEL_PATH} not found. Prediction endpoint will fail.", file=sys.stderr)

class PredictionRequest(BaseModel):
    landmarks: list[float]

@app.get("/")
def read_root():
    return {"status": "running", "model_loaded": classifier is not None}

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Initialize OpenRouter client
client = None
if OPENROUTER_API_KEY:
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
        print("OpenRouter client initialized.")
    except Exception as e:
        print(f"Error initializing OpenRouter client: {e}", file=sys.stderr)
else:
    print("Warning: OPENROUTER_API_KEY not found. Autocomplete will be disabled.", file=sys.stderr)

class SuggestionRequest(BaseModel):
    context: str

@app.post("/suggest")
def suggest(request: SuggestionRequest):
    print(f"DEBUG: Suggestion request received. Context: '{request.context}'")
    
    if not client:
        print("DEBUG: OpenRouter client not initialized.")
        return {"suggestions": []}
    
    if not request.context.strip():
        print("DEBUG: Empty context.")
        return {"suggestions": []}

    try:
        # Prompt engineering for sentence completion
        # We want 3 simple continuation options
        prompt = f"""
        Lengkapi kalimat Bahasa Indonesia berikut ini dengan SANGAT singkat dan natural.
        Kalimat: "{request.context}"
        Berikan 3 opsi kata atau frasa (maksimal 2 kata per opsi) untuk melanjutkan kalimat tersebut.
        Format output: Comma separated values only, no numbering, no explanation.
        Contoh: makan, minum, tidur
        """
        
        completion = client.chat.completions.create(
            model="tngtech/deepseek-r1t2-chimera:free",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        text = completion.choices[0].message.content.strip()
        print(f"DEBUG: OpenRouter response: {text}")
        
        # Clean up result (handle potential formatting variations)
        suggestions = [s.strip() for s in text.split(',') if s.strip()]
        
        # Fallback if split didn't work well (e.g. newlines)
        if len(suggestions) == 1 and '\n' in text:
             suggestions = [s.strip() for s in text.split('\n') if s.strip()]

        return {"suggestions": suggestions[:3]}
    except Exception as e:
        print(f"DEBUG: OpenRouter API Error: {e}", file=sys.stderr)
        return {"suggestions": []}

@app.post("/predict")
def predict(request: PredictionRequest):
    if classifier is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if len(request.landmarks) != 63: # 21 points * 3 coords
        raise HTTPException(status_code=400, detail=f"Expected 63 landmarks, got {len(request.landmarks)}")
    
    # Reshape or just pass list? Classifier expects (n_samples, n_features)
    # The landmarks list is [x1, y1, z1, x2, y2, z2, ...] length 63.
    # We need to wrap it in a list of samples: [[...]]
    data = np.array([request.landmarks])
    
    try:
        prediction = classifier.predict(data)
        return {"prediction": prediction[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
