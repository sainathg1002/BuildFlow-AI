# 🤖 Coder App — AI Agent-Based Application Generator

> Describe what you want to build. The AI agent figures out the rest.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![LLaMA](https://img.shields.io/badge/LLaMA--3.1-Groq-orange.svg)](https://groq.com)
[![FAISS](https://img.shields.io/badge/FAISS-Vector%20Search-red.svg)](https://faiss.ai)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-ff4b4b.svg)](https://streamlit.io)

---

---

## What Is This?

Coder App is an **autonomous AI agent** that generates complete application code from a plain English description.

You describe what you want → the agent plans, researches, writes, and self-corrects the code → you get a working application.

**It doesn't just generate code once. It loops, evaluates, and fixes itself.**
**Live Link**: https://build-flow-53i81efot-sainathg1002s-projects.vercel.app/


---

## How It Works

```
Your Description ("Build a REST API for a todo app")
          │
          ▼
┌──────────────────────┐
│   Planning Agent     │  ← Breaks task into steps
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Research Layer     │  ← Searches similar code patterns
│   (FAISS + Web)      │    using vector similarity
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Code Generator     │  ← LLaMA-3.1 writes the code
│   (LLaMA-3.1/Groq)   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Feedback Loop      │  ← Detects hallucinations/errors,
│   (Self-correction)  │    re-prompts automatically
└──────────┬───────────┘
           │
           ▼
    Complete Application Code
```

**Key design decision:** The agent has a self-correction loop. When it detects broken logic or hallucinated APIs, it re-runs with adjusted context — mimicking how a human developer debugs.

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | LLaMA-3.1 via Groq API |
| Agent Framework | Custom multi-step orchestration |
| Vector Search | FAISS + Sentence Transformers |
| Web Scraping | BeautifulSoup |
| Backend | FastAPI, REST APIs |
| Frontend | Streamlit |

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/coder-app.git
cd coder-app
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up your API key

Create a `.env` file in the root folder:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Get a free Groq API key at [console.groq.com](https://console.groq.com)

### 4. Run the app

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`

---

## Example Usage

```
Input: "Build a Python FastAPI app with CRUD operations for a bookstore"

Agent Step 1 → Plans: routes needed, models, database schema
Agent Step 2 → Searches: similar FastAPI patterns in vector store
Agent Step 3 → Generates: complete working code
Agent Step 4 → Detects: hallucinated library name in import
Agent Step 5 → Self-corrects: re-generates with fix

Output: Complete, runnable FastAPI application with:
  ├── main.py
  ├── models.py
  ├── routes/
  └── requirements.txt
```

---

## Project Structure

```
coder-app/
├── app.py                  # Streamlit UI
├── agent/
│   ├── planner.py          # Task decomposition
│   ├── researcher.py       # FAISS-based code search
│   ├── generator.py        # LLM code generation
│   └── feedback.py         # Self-correction loop
├── api/
│   └── routes.py           # FastAPI endpoints
├── scraper/
│   └── web_scraper.py      # BeautifulSoup scraping
├── requirements.txt
└── .env.example
```

---

## What Makes This Different

| Basic Code Generator | Coder App Agent |
|---|---|
| One-shot generation | Multi-step planning + generation |
| No error handling | Self-correction feedback loop |
| No context retrieval | FAISS vector search for patterns |
| Static output | Iterative refinement |

---

## The Hard Problem This Solves

LLMs hallucinate — especially library names, function signatures, and API methods. Most code generators ignore this.

Coder App detects hallucination patterns in generated code (nonexistent imports, wrong function calls) and automatically re-prompts with corrected context. This makes the output significantly more reliable for real use.

---

## Requirements

```
Python 3.10+
groq
faiss-cpu
sentence-transformers
streamlit
fastapi
uvicorn
beautifulsoup4
requests
python-dotenv
```

---

## Run with Docker

```bash
docker build -t coder-app .
docker run -p 8501:8501 --env-file .env coder-app
```

---

## Author

**Venkata Sainath Ganta**
[GitHub](https://github.com/sainathg1002) • [LinkedIn](https://www.linkedin.com/in/venkata-sai-ganta-c300b200a100/) • [Portfolio](https://sainathg1002.github.io/sainath_portfolio/)
