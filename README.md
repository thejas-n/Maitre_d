# Concierge Agent Platform 🤖

An AI-powered concierge platform for restaurants and similar venues. It supports multiple concierge profiles (e.g., MG Cafe, Amber, Maya) with per-venue knowledge, avatars, and voices. The agent handles table reservations/waitlists and guest interactions via voice and text.

## 🚀 Features

### Core AI Capabilities
- **LLM-Powered Agent**: Built with Google Gemini API for natural language understanding and conversation
- **Function Calling**: Automatic tool execution for restaurant operations
- **Voice Interaction**: Real-time speech-to-text recognition and text-to-speech synthesis
- **Multi-modal Avatar**: Dynamic video avatar that responds to conversation states (idle, listening, speaking)

### Venue Operations
- **Table Management**: Real-time tracking of table availability across different seating types
- **Waitlist System**: Automatic waitlist management with FIFO assignment
- **Guest Services**: Seamless check-in and checkout processes
- **Dashboard**: Live visualization of restaurant status

### Technical Implementation
- **Custom Tools**: Three specialized tools for restaurant operations
- **Session Management**: Persistent conversation state across interactions
- **REST API**: Clean API endpoints for all operations
- **Web Interface**: Modern responsive UI with real-time updates
- **Runtime Logs**: Agent and TTS timing logs in `logs/agent.log` and `logs/tts.log`
- **Profiles**: Pluggable concierge profiles (model, voice, avatars, prompt) via `CONCIERGE_ID`
- **Knowledge Packs**: Per-concierge knowledge files under `concierge_app/knowledge/` (e.g., `mg_cafe.md`)
- **Observability**: Request logging + Prometheus metrics (`/metrics`)

### Current Defaults
- **Model**: `gemini-2.5-flash` with automatic function calling
- **TTS**: Google Cloud Text-to-Speech voice `en-IN-Standard-E` (MP3)
- **Avatar**: Rectangular video panel with rounded edges and glassy “Interact” button
- **Profile**: Configurable via `CONCIERGE_ID` (see `concierge_app/profiles.py`); avatars resolve from `concierge_app/static/media/<profile_id>/...`

## 🏗️ Architecture

```
.
├── app.py                     # Flask application entry point
├── concierge_app/
│   ├── __init__.py            # Flask app factory + observability hooks
│   ├── agent.py               # Gemini-powered concierge agent
│   ├── profiles.py            # Concierge profiles (model/voice/prompt/assets/knowledge)
│   ├── knowledge/             # Per-venue knowledge packs (e.g., mg_cafe.md)
│   ├── routes.py              # API endpoints
│   ├── tts.py                 # Text-to-speech service
│   ├── config.py              # Configuration management
│   ├── static/
│   │   ├── js/app.js          # Frontend JavaScript
│   │   └── media/             # Avatar videos under each profile id (e.g., amber/, maya/)
│   └── templates/
│       └── index.html         # Main UI
├── services/
│   └── hotel.py               # Restaurant state management
├── logs/                      # Runtime logs (agent/tts/requests)
├── venv/                      # Python virtual environment
├── requirements.txt           # Python dependencies
└── .env                       # Environment variables
```

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.13+
- Google Cloud Project with Gemini API enabled
- Google Cloud Text-to-Speech API enabled
- Service account key for Google Cloud APIs

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/hotel_concierge.git
cd hotel_concierge
```

### 2. Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Google Cloud Configuration

#### Create a Service Account
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gemini API and Text-to-Speech API
4. Create a service account with necessary permissions
5. Download the JSON key file

#### Environment Variables
Create a `.env` file in the project root:
```bash
GOOGLE_API_KEY=your_gemini_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
CONCIERGE_ID=amber  # or another profile id
PORT=5001
```

### 4. Avatar Videos Setup
Place avatar videos under `concierge_app/static/media/<profile_id>/` matching the filenames in the profile:
- `avatar-idle.mp4` - Avatar in idle state
- `avatar-listening.mp4` - Avatar when listening to guest
- `avatar-speaking.mp4` - Avatar when speaking to guest

## 🚀 Running the Application

### Development Mode
```bash
# From project root
source venv/bin/activate
python app.py
```

The application will be available at:
- **Local**: http://127.0.0.1:5001
- **Network**: http://your-ip:5001

### Production Deployment
```bash
# Using Gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 "concierge_app:create_app()"

# Or using Docker
docker build -t hotel-concierge .
docker run -p 5001:5001 hotel-concierge
```

## 📋 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main application interface |
| `/api/status` | GET | Get current restaurant status |
| `/api/chat` | POST | Send message to concierge agent |
| `/api/tts` | POST | Generate speech from text |
| `/api/checkout` | POST | Check out guest and assign from waitlist |

## 🧑‍🍳 Creating Additional Concierge Profiles

- Add a new entry to `concierge_app/profiles.py` with a unique `id`, `model`, `tts_voice`, `prompt`, `avatars`, and knowledge file reference (drop the knowledge file under `concierge_app/knowledge/`).
- Set `CONCIERGE_ID=<your_id>` in `.env` to boot that concierge.
- Place avatar video files in `concierge_app/static/media/<profile_id>/` matching the filenames you set in the profile.
- Restart the app to load the new profile.

## 📈 Observability
- Request logging: `logs/requests.log` (method/path/status/duration_ms, X-Request-ID header).
- Metrics: Prometheus endpoint at `/metrics` (request counters/histograms).
- Agent log: `logs/agent.log` for Gemini response timings.
- TTS log: `logs/tts.log` for synthesis timings and sizes.

## 🎯 Usage

### For Guests
1. Click "Interact" button to start conversation
2. Speak naturally: "I'd like a table for 4 people"
3. The AI concierge will:
   - Check table availability
   - Assign table or add to waitlist
   - Provide confirmation

### For Staff
- **Dashboard**: View real-time table and waitlist status
- **Table Checkout**: Click occupied tables to check out guests
- **Waitlist Management**: Automatic assignment when tables become available

## 🔧 Configuration

### Restaurant Layout
Edit `hotel.py` to customize table configuration:

```python
# Bar seats (1 person each)
for i in range(5):
    self.tables.append(Table(f"BAR-{i+1}", 1, "bar"))

# Standard tables
for prefix, count, seats in (("T2", 5, 2), ("T4", 5, 4), ("T6", 2, 6)):
    for i in range(count):
        self.tables.append(Table(f"{prefix}-{i+1}", seats, "standard"))
```

### Agent Behavior
Modify the system prompt in `agent.py` to customize concierge personality and behavior.

## 🎨 Avatar States

The concierge uses three distinct video states:
- **Idle**: Default state when not interacting
- **Listening**: Activated during speech recognition
- **Speaking**: Shows when agent is responding

## 🔍 Troubleshooting

### Common Issues

**Microphone Permission Errors**
```
"not-allowed" error
```
- Ensure running on localhost or HTTPS
- Grant microphone permissions in browser
- Check browser compatibility (Chrome recommended)

**API Connection Issues**
```
Foundation model unavailable
```
- Verify Google API keys are set correctly
- Check service account permissions
- Ensure APIs are enabled in Google Cloud Console

**Avatar Not Switching States**
- Verify video files exist in correct location
- Check browser console for video loading errors
- Ensure videos are MP4 format

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google Gemini API for conversational AI
- Google Cloud Text-to-Speech for voice synthesis
- Flask framework for web application
- Web Speech API for speech recognition

## 📞 Support

For questions or issues:
- Open an issue on GitHub
- Check the troubleshooting section
- Review API documentation

---

**Built with ❤️ for the future of restaurant hospitality**
