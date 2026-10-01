# Quickstart Guide: AI Incident Investigation Agent

## Prerequisites
- **Python**: 3.11 or higher
- **Virtual Environment**: Recommended (`venv` or `conda`)
- **LLM API Key (Optional)**: OpenAI (`OPENAI_API_KEY`), Google Gemini (`GEMINI_API_KEY`), or Anthropic (`ANTHROPIC_API_KEY`). If no API key is provided, the application runs in **deterministic rule-based fallback mode**.

---

## Installation & Setup

### 1. Navigate to Project Directory
```bash
cd C:\Users\sanjana.smarigoudar\.gemini\antigravity\scratch\incident-agent
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file from `.env.example`:
```bash
cp .env.example .env
```
Edit `.env` to configure your preferred LLM provider:
```env
# Database URL
DATABASE_URL=sqlite:///./incident_agent.db

# LLM Provider Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-proj-...

# Optional Alternative Providers:
# LLM_MODEL=gemini/gemini-1.5-pro
# GEMINI_API_KEY=...
```

---

## Running the Application

### 1. Start FastAPI Server
```bash
uvicorn app.main:app --reload --port 8000
```

### 2. Access Web Console & API Docs
- **Interactive Dashboard UI**: Open [http://localhost:8000/](http://localhost:8000/) in your browser.
- **Interactive OpenAPI Docs**: Open [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Running Test Suite

Execute all 83 automated unit and integration tests:
```bash
python -m pytest tests/ -v
```

Run test suite with code coverage:
```bash
python -m pytest tests/ --cov=app --cov-report=term-missing
```

---

## End-to-End Investigation Walkthrough via cURL

### Step 1: Create Incident INC-001
```bash
curl -X POST http://localhost:8000/incidents \
  -H "Content-Type: application/json" \
  -d @artefacts/incidents/INC-001.json
```

### Step 2: Trigger Investigation
```bash
curl -X POST http://localhost:8000/incidents/INC-001/investigate
```

### Step 3: Fetch Final Structured Report
```bash
curl http://localhost:8000/incidents/INC-001/report
```

### Step 4: Record Approval for High-Risk Recommendation
```bash
curl -X POST http://localhost:8000/incidents/INC-001/actions/<action_id>/approve \
  -H "Content-Type: application/json" \
  -d '{"approved": true, "approved_by": "sre-lead@company.com"}'
```
