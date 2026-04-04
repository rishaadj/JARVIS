# 🤖 JARVIS — I built my own AI assistant that actually runs on my PC

![Status](https://img.shields.io/badge/status-active-success)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![Architecture](https://img.shields.io/badge/architecture-multi--agent-purple)
![License](https://img.shields.io/badge/license-MIT-green)
![Free](https://img.shields.io/badge/cost-100%25%20free-brightgreen)

> It can open apps, send emails, search the web, control your mouse/keyboard, analyse your screen, send WhatsApp messages, run shell commands, and synthesise new skills on its own — all from voice or text. Inspired by Tony Stark's JARVIS.

---

## 🎥 What it looks like

The HUD is a real-time Heads-Up Display that runs in your browser. It shows:
- **Live system telemetry** (CPU, RAM, battery)
- **Neural state** (thinking / executing / speaking)
- **A full conversation transcript**
- **Visual awareness feed** (what JARVIS last looked at)
- **Multi-brain selector** to switch AI providers on the fly

---

## 🧠 How it works

JARVIS is not a chatbot wrapper. It's a **multi-agent autonomous system**:

```
You speak / type
      ↓
Autonomous Core (decides what to do)
      ↓
Planner → Executor → Skills
      ↓
Memory ← Evaluator (was it right?)
```

Every response goes through a full agent loop: plan → execute → evaluate → remember.

---

## 🛰️ The "Neural Switchboard" — 100% Free, 100% Uptime

JARVIS never goes offline because it has four AI "brains" in a failover chain:

| Priority | Provider | Why |
|---|---|---|
| 1st | **Google Gemini 2.5 Flash Lite** | Native vision, 1.5M context, free tier |
| 2nd | **Groq Cloud (Llama 3.2 Vision)** | 800+ tokens/sec, free tier |
| 3rd | **Ollama (Local Llama 3.2)** | 100% offline, private |
| 4th | **Ollama Dolphin** | Uncensored, unrestricted local model |

If Gemini hits a rate limit → automatic switch to Groq → if offline → Ollama. You never notice.

> You can also manually force any brain from the HUD sidebar. The Arc Reactor changes colour (Blue/Gold/Green/Pink) to show which brain is active.

---

## ⚡ What it can do

### 💬 Communication
- Send emails (Gmail SMTP)
- Send WhatsApp messages (browser automation or Twilio API)

### 💻 PC Control  
- Open any application
- Control mouse & keyboard
- Run shell commands
- File management

### 🔍 Intelligence
- Web search & research
- Screen analysis (takes a screenshot, tells you what's on it)
- **Drag & drop any image** onto the HUD for instant AI analysis
- Long-term semantic memory (remembers things across sessions)

### 🤖 Self-Evolution
- Generates new Python skills when it doesn't know how to do something
- Tests and integrates them automatically

### 🎤 Voice
- Offline speech recognition via Vosk (no cloud, no latency)
- Neural voice output via Edge-TTS (sounds human)
- Smart barge-in: say "stop" or "cancel" to interrupt mid-sentence

---

## 🚀 Setup (5 minutes)

### Requirements
- Python 3.10+
- A free [Google AI Studio](https://aistudio.google.com) key (Gemini)
- Optionally: [Groq](https://console.groq.com) key, [Ollama](https://ollama.com)

```bash
git clone https://github.com/rishaadj/JARVIS.git
cd JARVIS
pip install -r requirements.txt
```

To configure JARVIS, you'll need to set up your environment variables. Simply create a copy of the `.env.example` file and rename it to `.env` (or just remove the `.example` extension). Then, open your new `.env` file and replace the placeholder values with your actual API keys and preferences.

```bash
cp .env.example .env
```

Download the voice recognition model:
```bash
python setup_indian_vosk.py
```

Run it:
```bash
python main.py
```

Open your browser at `http://localhost:5000` — that's the HUD.

---

## 🔧 Configuration (`.env`)

```env
# AI Brains (at least one required)
GEMINI_API_KEYS=key1,key2,key3   # Comma-separate multiple for rotation
GROQ_API_KEY=your_groq_key

# Email (optional)
EMAIL_USER=your_gmail@gmail.com
EMAIL_PASS=your_app_password       # Gmail App Password, not your real password

# WhatsApp via Twilio (optional — falls back to browser if not set)
TWILIO_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_WHATSAPP_FROM=+14155238886

# Security
JARVIS_PIN=1234                    # PIN for remote HUD access
```

---

## 🔒 Privacy & Security

All processing is local by default:
- `.env` — never committed (API keys stay on your machine)
- `screenshots/` — local only
- `memory.json` / `conversation_log.json` — local only
- Voice recognition runs fully offline via Vosk

---

## 📊 Current Status

| Feature | Status |
|---|---|
| Multi-Agent Autonomous Core | ✅ |
| Neural Switchboard (4 providers) | ✅ |
| Voice In + Voice Out | ✅ |
| Email & WhatsApp | ✅ |
| Screen Vision | ✅ |
| Image Drag & Drop Analysis | ✅ |
| Self-Evolving Skill Synthesis | ✅ |
| Gesture Control | 🚧 In Progress |

---

## 🧩 Architecture

```
main.py
├── Flask + SocketIO (HUD server)
├── Vosk (voice recognition)
└── AutonomousCore
    ├── PlannerAgent      — breaks goals into steps
    ├── ExecutorAgent     — runs skills
    ├── MonitorAgent      — tracks system health
    ├── EvaluatorAgent    — validates outcomes
    ├── GoalAgent         — generates autonomous goals
    ├── MemoryManager     — semantic long-term memory
    ├── VisualObserver    — passive screen awareness
    └── skills/           — 27 plug-and-play Python modules
```

---

## ❓ FAQ

**Q: Does this cost anything?**  
A: No. Gemini and Groq both have generous free tiers. Ollama is completely free and local.

**Q: Does it always listen to my microphone?**  
A: Yes, but voice recognition runs fully offline via Vosk — nothing is sent to a server.

**Q: Can I add my own skills?**  
A: Yes. Drop a Python file with an `execute(params)` function into the `skills/` folder. JARVIS picks it up automatically.

**Q: Is this the movie JARVIS?**  
A: No, but it tries its best. Not affiliated with Marvel.

---

## ⚠️ Disclaimer

This is an educational and experimental project. Use responsibly. The shell execution and file management skills operate within a sandboxed safety policy — review `safety_manager.py` before deploying.

---

> *"Sometimes you gotta run before you can walk."* — Tony Stark
