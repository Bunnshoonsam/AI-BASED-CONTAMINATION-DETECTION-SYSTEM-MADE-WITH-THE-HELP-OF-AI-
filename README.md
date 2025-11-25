# Microbiology Culture Contamination Detection System

A full-stack application that uses Google Gemini Vision API to detect contamination in microbiology cultures captured via phone camera.

## 🎯 Project Overview

This system allows users to:
- Capture microbiology culture images using a phone camera
- Analyze images in real-time using AI
- Get structured JSON responses with contamination status, confidence, and reasoning

## 📁 Project Structure

```
project/
├── backend/
│   ├── server.py          # FastAPI backend server
│   ├── requirements.txt   # Python dependencies
│   ├── .env.example       # Environment variables template
│   └── .env               # Your actual API key (create this)
├── frontend/
│   └── capture.html       # Mobile-friendly camera interface
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- Modern web browser with camera access (Chrome, Safari, Firefox)
- Mobile device or computer with camera

### Step 1: Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   
   Then edit `.env` and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

5. **Run the server:**
   ```bash
   python server.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn server:app --host 0.0.0.0 --port 8080 --reload
   ```

   The server will start on `http://localhost:8080`

### Step 2: Frontend Setup

1. **Open `capture.html` in a web browser:**
   - For local testing: Open `frontend/capture.html` directly in your browser
   - For mobile access: See "Accessing from Phone" section below

2. **Allow camera permissions** when prompted

3. **Use the interface:**
   - Position your microbiology culture in view
   - Tap "Snap" to capture the image
   - Tap "Analyze" to send to the server
   - View results with contamination status

## 📱 Accessing from Phone

### Option 1: Local Network (LAN)

1. **Find your computer's IP address:**
   - **Linux/Mac:** Run `ip addr show` or `ifconfig`
   - **Windows:** Run `ipconfig`
   - Look for IPv4 address (e.g., `192.168.1.100`)

2. **Update API endpoint in capture.html:**
   - Open `frontend/capture.html`
   - Change the default API endpoint input field to: `http://YOUR_IP:8080/predict`
   - Or edit the JavaScript: change `value="http://localhost:8080/predict"` to your IP

3. **Start the backend server** (make sure it's running on `0.0.0.0`):
   ```bash
   uvicorn server:app --host 0.0.0.0 --port 8080
   ```

4. **Access from phone:**
   - Make sure phone and computer are on the same Wi-Fi network
   - On your phone, open a browser and go to: `http://YOUR_IP:8080` (if serving HTML) or use a local file server
   - Or use a simple HTTP server to serve the HTML file

5. **Serve HTML file (optional):**
   ```bash
   # From project root
   cd frontend
   python -m http.server 8000
   ```
   Then access: `http://YOUR_IP:8000/capture.html`

### Option 2: Using ngrok (External Access)

1. **Install ngrok:**
   - Download from [ngrok.com](https://ngrok.com/)
   - Or install via package manager: `brew install ngrok` (Mac) or `sudo apt install ngrok` (Linux)

2. **Start your backend server:**
   ```bash
   cd backend
   uvicorn server:app --host 0.0.0.0 --port 8080
   ```

3. **Create ngrok tunnel:**
   ```bash
   ngrok http 8080
   ```

4. **Copy the forwarding URL** (e.g., `https://abc123.ngrok.io`)

5. **Update API endpoint:**
   - In `capture.html`, change the API endpoint to: `https://YOUR_NGROK_URL/predict`
   - Or update it in the input field on the page

6. **Access from anywhere:**
   - Serve `capture.html` via ngrok or another service
   - Or use a simple file server and update the API endpoint in the HTML

## 🔧 API Endpoints

### `GET /`
Health check endpoint.

**Response:**
```json
{
    "status": "healthy",
    "service": "Microbiology Contamination Detection API",
    "version": "1.0.0"
}
```

### `GET /health`
Simple health check.

**Response:**
```json
{
    "status": "ok"
}
```

### `POST /predict`
Main prediction endpoint.

**Request Body:**
```json
{
    "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

**Response:**
```json
{
    "contaminated": true,
    "confidence": 0.85,
    "reason": "The culture shows visible signs of contamination including foreign particles and unusual coloration patterns that are not consistent with pure culture growth."
}
```

**Error Response:**
```json
{
    "detail": "Error message here"
}
```

## 🧪 Testing

### Test with cURL

```bash
# Convert image to base64
IMAGE_BASE64=$(base64 -i your_image.jpg)

# Send request
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d "{\"image\": \"data:image/jpeg;base64,$IMAGE_BASE64\"}"
```

### Test with Python

```python
import requests
import base64

# Read and encode image
with open("test_image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()
    data_url = f"data:image/jpeg;base64,{image_data}"

# Send request
response = requests.post(
    "http://localhost:8080/predict",
    json={"image": data_url}
)

print(response.json())
```

## 🐛 Troubleshooting

### Camera Not Working

- **Issue:** Camera access denied
  - **Solution:** Check browser permissions, ensure HTTPS (or localhost) for camera access
  - **Mobile:** Some browsers require HTTPS for camera access (use ngrok)

### API Connection Failed

- **Issue:** "Failed to call Gemini API"
  - **Solution:** 
    - Verify your API key is correct in `.env`
    - Check internet connection
    - Ensure API key has proper permissions

### CORS Errors

- **Issue:** CORS policy blocking requests
  - **Solution:** The backend already has CORS enabled for all origins. If issues persist, check that the server is running and accessible.

### JSON Parsing Errors

- **Issue:** "Failed to parse JSON from Gemini response"
  - **Solution:** This is rare but can happen. The backend will return the raw response in the error detail. Check the Gemini API status.

### Port Already in Use

- **Issue:** Port 8080 is already in use
  - **Solution:** Change the port in `server.py` or use: `uvicorn server:app --port 8081`

### Mobile Camera Not Showing

- **Issue:** Camera preview not displaying on phone
  - **Solution:** 
    - Ensure you're using HTTPS (via ngrok) or localhost
    - Check browser compatibility (Chrome/Safari recommended)
    - Verify camera permissions are granted

## 📝 Code Structure

### Backend (`server.py`)

- **`strip_data_url_prefix()`**: Removes data URL prefix from base64 strings
- **`call_gemini_vision_api()`**: Makes API call to Gemini Vision API
- **`extract_json_from_response()`**: Parses and validates JSON from Gemini response
- **`/predict` endpoint**: Main prediction endpoint with full error handling

### Frontend (`capture.html`)

- **Camera initialization**: Requests back camera access
- **Snapshot capture**: Captures frame from video stream
- **Image analysis**: Sends base64 image to backend API
- **Results display**: Shows contamination status, confidence, and reasoning

## 🔒 Security Notes

- **API Key**: Never commit `.env` file to version control
- **CORS**: Currently allows all origins. In production, restrict to specific domains
- **HTTPS**: Use HTTPS in production for secure camera access

## 📚 Dependencies

### Backend
- `fastapi`: Modern web framework
- `uvicorn`: ASGI server
- `python-dotenv`: Environment variable management
- `requests`: HTTP client for Gemini API

### Frontend
- Pure HTML/CSS/JavaScript (no frameworks required)
- Uses browser MediaDevices API for camera access
- Fetch API for HTTP requests

## 🎨 Features

- ✅ Real-time camera preview
- ✅ Mobile-optimized interface
- ✅ Automatic base64 encoding
- ✅ Structured JSON responses
- ✅ Error handling and validation
- ✅ Confidence scoring
- ✅ Detailed reasoning from AI

## 📄 License

This project is provided as-is for educational and research purposes.

## 🤝 Support

For issues or questions:
- Check the troubleshooting section above
- Review Gemini API documentation: https://ai.google.dev/docs
- Check FastAPI documentation: https://fastapi.tiangolo.com/

# AI-BASED-CONTAMINATION-DETECTION-SYSTEM-MADE-WITH-THE-HELP-OF-AI-
