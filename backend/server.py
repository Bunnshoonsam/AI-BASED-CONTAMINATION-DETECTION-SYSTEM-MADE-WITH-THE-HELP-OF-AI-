"""
FastAPI Backend Server for Microbiology Culture Contamination Detection
Uses Google Gemini Vision API for image analysis
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import json
import re
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Microbiology Contamination Detection API",
    description="API for detecting contamination in microbiology cultures using Gemini Vision",
    version="1.0.0"
)

# Enable CORS for frontend access from any origin (important for mobile devices)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get Gemini API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://api.generativeai.googleapis.com/v1/models/gemini-1.5-flash-latest:generateContent"

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found in environment variables. "
        "Please create a .env file with your API key."
    )


class ImageRequest(BaseModel):
    """Request model for image prediction"""
    image: str  # Base64 encoded image data URL


def strip_data_url_prefix(image_data: str) -> str:
    """
    Strip the data URL prefix from base64 image string.
    
    Example: "data:image/jpeg;base64,/9j/4AAQ..." -> "/9j/4AAQ..."
    
    Args:
        image_data: Base64 image string with optional data URL prefix
        
    Returns:
        Clean base64 string without prefix
    """
    # Remove data URL prefix if present
    if image_data.startswith("data:image"):
        # Find the comma that separates prefix from base64 data
        comma_index = image_data.find(",")
        if comma_index != -1:
            return image_data[comma_index + 1:]
    return image_data


def call_gemini_vision_api(base64_image: str) -> dict:
    """
    Call Google Gemini Vision API with base64 image.
    
    Forces the model to return strict JSON format:
    {
        "contaminated": true/false,
        "confidence": 0.0-1.0,
        "reason": "string"
    }
    
    Args:
        base64_image: Base64 encoded image string (without data URL prefix)
        
    Returns:
        Dictionary with API response
        
    Raises:
        Exception: If API call fails
    """
    # Prepare the request payload
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": """Analyze this microbiology culture image for contamination.

You MUST respond with ONLY valid JSON in this exact format (no markdown, no code blocks, no extra text):
{
    "contaminated": true or false,
    "confidence": a number between 0.0 and 1.0,
    "reason": "a detailed explanation of your analysis"
}

Look for:
- Visible contaminants (foreign particles, debris, unwanted growth)
- Signs of contamination (unusual colors, textures, or patterns)
- Overall culture health and purity

Return ONLY the JSON object, nothing else."""
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": base64_image
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,  # Lower temperature for more consistent JSON output
            "response_mime_type": "application/json"  # Force JSON response
        }
    }
    
    # Set headers
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }
    
    # Make API request
    try:
        response = requests.post(
            GEMINI_API_URL,
            headers=headers,
            json=payload,
            timeout=30  # 30 second timeout
        )
        response.raise_for_status()  # Raise exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Gemini API request failed: {str(e)}")


def extract_json_from_response(gemini_response: dict) -> dict:
    """
    Extract and parse JSON from Gemini API response.
    
    The response structure is:
    {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": "{...json...}"
                        }
                    ]
                }
            }
        ]
    }
    
    Args:
        gemini_response: Raw response from Gemini API
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        ValueError: If JSON cannot be extracted or parsed
    """
    try:
        # Navigate through response structure
        candidates = gemini_response.get("candidates", [])
        if not candidates:
            raise ValueError("No candidates in Gemini response")
        
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if not parts:
            raise ValueError("No parts in candidate content")
        
        text = parts[0].get("text", "")
        if not text:
            raise ValueError("No text in response parts")
        
        # Clean the text - remove markdown code blocks if present
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]  # Remove ```json
        elif text.startswith("```"):
            text = text[3:]  # Remove ```
        if text.endswith("```"):
            text = text[:-3]  # Remove closing ```
        text = text.strip()
        
        # Try to parse JSON
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON using regex
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                raise ValueError(f"Could not parse JSON from response: {text[:200]}")
        
        # Validate required fields
        required_fields = ["contaminated", "confidence", "reason"]
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate types
        if not isinstance(result["contaminated"], bool):
            raise ValueError("'contaminated' must be a boolean")
        
        if not isinstance(result["confidence"], (int, float)):
            raise ValueError("'confidence' must be a number")
        
        if not isinstance(result["reason"], str):
            raise ValueError("'reason' must be a string")
        
        # Clamp confidence to 0.0-1.0 range
        result["confidence"] = max(0.0, min(1.0, float(result["confidence"])))
        
        return result
        
    except Exception as e:
        raise ValueError(f"Failed to extract JSON from response: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "status": "healthy",
        "service": "Microbiology Contamination Detection API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}


@app.post("/predict")
async def predict_contamination(request: ImageRequest):
    """
    Main prediction endpoint.
    
    Accepts base64 encoded image (with or without data URL prefix),
    calls Gemini Vision API, and returns structured JSON response.
    
    Request body:
    {
        "image": "data:image/jpeg;base64,/9j/4AAQ..." or "/9j/4AAQ..."
    }
    
    Response:
    {
        "contaminated": true/false,
        "confidence": 0.0-1.0,
        "reason": "detailed explanation"
    }
    """
    try:
        # Step 1: Strip data URL prefix from image
        base64_image = strip_data_url_prefix(request.image)
        
        if not base64_image:
            raise HTTPException(
                status_code=400,
                detail="Empty image data provided"
            )
        
        # Step 2: Call Gemini Vision API
        try:
            gemini_response = call_gemini_vision_api(base64_image)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to call Gemini API: {str(e)}"
            )
        
        # Step 3: Extract and validate JSON from response
        try:
            result = extract_json_from_response(gemini_response)
        except ValueError as e:
            # If JSON extraction fails, return error with raw response
            raw_text = ""
            try:
                candidates = gemini_response.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    if parts:
                        raw_text = parts[0].get("text", "")
            except:
                pass
            
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Failed to parse JSON from Gemini response",
                    "message": str(e),
                    "raw_response": raw_text[:500]  # First 500 chars
                }
            )
        
        # Step 4: Return successful response
        return JSONResponse(content=result)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

