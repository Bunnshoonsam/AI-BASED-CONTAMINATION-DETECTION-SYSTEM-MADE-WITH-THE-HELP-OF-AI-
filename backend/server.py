import os
import json
import requests

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from starlette.requests import Request
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from fastapi.responses import FileResponse

BASE_DIR = Path(__file__).resolve().parent

FRONTEND_PATH = (BASE_DIR / "../frontend/capture.html").resolve()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found")

GEMINI_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"


# FRONTEND SERVE ROUTE
@app.get("/")
def serve_frontend():
    return FileResponse(FRONTEND_PATH)


@app.get("/health")
def test():
    return {"status": "alive"}


@app.post("/predict")
async def predict(req: Request):

    try:
        body = await req.json()
    except:
        raise HTTPException(400, "Invalid JSON")

    if "image" not in body:
        raise HTTPException(400, "Missing image")

    # Clean Base64
    img_raw = body["image"]

    if "," in img_raw:
        img_raw = img_raw.split(",", 1)[1]

    prompt = """
    You are a microbiology expert.
    Look at the culture image and respond ONLY with:

    {
        "contaminated": true/false,
        "confidence": 0.0-1.0,
        "reason": "short explanation"
    }
    """

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": img_raw
                        }
                    },
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }

    try:
        r = requests.post(
            GEMINI_URL,
            headers=headers,
            json=payload
        )

        r_json = r.json()

        text = r_json["candidates"][0]["content"]["parts"][0]["text"]

        result = json.loads(text)

        return result

    except Exception as e:
        raise HTTPException(500, f"AI error: {str(e)}")
