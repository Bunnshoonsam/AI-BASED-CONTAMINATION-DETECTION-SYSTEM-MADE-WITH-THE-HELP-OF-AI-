import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import requests

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

app = FastAPI()

class ImageRequest(BaseModel):
    image: str  # base64 data URL

GEMINI_URL = "https://api.generativeai.googleapis.com/v1/models/gemini-1.5-flash-latest:generateContent"

@app.post("/predict")
async def predict(req: ImageRequest):
    # Strip the "data:image/jpeg;base64," prefix
    if "," in req.image:
        b64_img = req.image.split(",", 1)[1]
    else:
        raise HTTPException(status_code=400, detail="Invalid image format")

    prompt = """
    You are an expert microbiology inspector. Analyze this culture image.
    Respond ONLY in valid JSON:
    {
      "contaminated": true/false,
      "confidence": 0.0-1.0,
      "reason": "string"
    }
    """

    payload = {
        "contents": [
            {
                "parts": [
                    {"inline_data": {"mime_type": "image/jpeg", "data": b64_img}},
                    {"text": prompt}
                ]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }

    try:
        response = requests.post(GEMINI_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        # Extract model text output
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except:
            raise HTTPException(status_code=500, detail="Invalid response from Gemini")

        # Parse JSON from text
        try:
            clean_json = json.loads(text)
        except:
            raise HTTPException(status_code=500, detail="Gemini did not return valid JSON")

        return clean_json

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))