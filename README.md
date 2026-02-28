# 🎯 Placement Prep AI Assistant

> An intelligent RAG-powered Q&A assistant that helps engineering students prepare for placement interviews using **Endee Vector Database** + **Google Gemini**.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red?logo=streamlit)
![Endee](https://img.shields.io/badge/Vector%20DB-Endee-6C3483)
![Gemini](https://img.shields.io/badge/LLM-Gemini%201.5%20Flash-orange?logo=google)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📖 Problem Statement

Engineering students preparing for campus placements face a fragmented learning experience — DSA, system design, HR rounds, and company-specific preparation are scattered across hundreds of resources. There's no single intelligent tool that:

- Answers placement questions with **context-grounded accuracy**
- Understands **semantic similarity** (not just keyword matching)
- Covers **all interview domains** in one place

This project solves that by building a **Retrieval-Augmented Generation (RAG)** assistant where Endee serves as the high-performance semantic memory layer.

---

## 🏗️ System Design & Technical Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PLACEMENT PREP AI ASSISTANT                  │
│                                                                 │
│  ┌──────────────┐    ┌──────────────────────────────────────┐  │
│  │  Streamlit   │    │         RAG Pipeline                 │  │
│  │     UI       │◄───┤                                      │  │
│  │              │    │  User Query                          │  │
│  │  - Chat      │    │      │                               │  │
│  │  - Browse    │    │      ▼                               │  │
│  │  - Ingest    │    │  Gemini text-embedding-004           │  │
│  └──────────────┘    │      │ (3078-dim query vector)        │  │
│                       │      ▼                               │  │
│                       │  ┌────────────────────┐             │  │
│                       │  │   ENDEE VECTOR DB  │             │  │
│                       │  │                    │             │  │
│                       │  │  Index: cosine     │             │  │
│                       │  │  Precision: INT8   │             │  │
│                       │  │  Dim: 768          │             │  │
│                       │  │  ~25 Q&A vectors   │             │  │
│                       │  └────────────────────┘             │  │
│                       │      │ top-k similar chunks         │  │
│                       │      ▼                               │  │
│                       │  Retrieved Context                   │  │
│                       │      │                               │  │
│                       │      ▼                               │  │
│                       │  Gemini 1.5 Flash (generation)       │  │
│                       │      │                               │  │
│                       │      ▼                               │  │
│                       │  Grounded Answer + Source Citations  │  │
│                       └──────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

| Component        | Technology                     | Purpose                                                       |
| ---------------- | ------------------------------ | ------------------------------------------------------------- |
| **Vector Store** | Endee (self-hosted via Docker) | Store and retrieve 768-dim embeddings using cosine similarity |
| **Embeddings**   | Google `text-embedding-004`    | Convert Q&A pairs and queries to dense vectors                |
| **Generation**   | Google `gemini-1.5-flash`      | Generate context-grounded answers                             |
| **UI**           | Streamlit                      | Chat interface, topic browser, ingestion panel                |
| **Retrieval**    | Endee Python SDK               | Semantic top-k search over knowledge base                     |

---

## 🔍 How Endee is Used

Endee is the **core semantic memory** of this application. Here's exactly how:

### 1. Index Creation

```python
client.create_index(
    name="placement_prep",
    dimension=768,         # text-embedding-004 output size
    space_type="cosine",   # cosine similarity for semantic search
    precision=Precision.INT8  # memory-efficient quantization
)
```

### 2. Ingesting the Knowledge Base

Each Q&A pair is embedded using Gemini and stored in Endee with metadata:

```python
index.upsert([{
    "id": "dsa_001",
    "vector": gemini_embedding,  # 768-dim float list
    "meta": {
        "topic": "DSA & Algorithms",
        "question": "What is dynamic programming?",
        "answer": "Dynamic Programming (DP)..."
    }
}])
```

### 3. Semantic Retrieval at Query Time

```python
query_vector = gemini_embed(user_question)
results = index.query(vector=query_vector, top_k=5)
# Returns most semantically similar Q&A pairs
```

Unlike keyword search, Endee retrieves answers based on **meaning** — asking _"explain memoization"_ correctly surfaces the dynamic programming answer because the concepts are semantically related.

### 4. RAG Generation

Retrieved context is injected into a Gemini prompt:

```
Retrieved Context: [top-k Q&A pairs from Endee]
Student Question: [user's question]
→ Grounded, accurate answer
```

---

## 📚 Knowledge Base

The pre-loaded dataset covers **25 Q&A pairs** across 6 placement domains:

| Topic                  | # of Q&As | Examples                                                 |
| ---------------------- | --------- | -------------------------------------------------------- |
| DSA & Algorithms       | 6         | DP, BFS/DFS, HashMap internals, Sliding Window           |
| System Design          | 5         | URL Shortener, CAP theorem, Twitter Feed, Load Balancing |
| OOPs & Design Patterns | 4         | SOLID, Singleton, Polymorphism, Abstract vs Interface    |
| HR & Behavioural       | 4         | Tell me about yourself, STAR method, weakness question   |
| Company-Specific       | 2         | Amazon Leadership Principles, Google hiring process      |
| Core CS Subjects       | 3         | Deadlocks, TCP vs UDP, Virtual Memory                    |

---

## � Live Demo

> **Deployed application:** _<[HERE](https://om-suman-placement-prep-ai-app-yx3diy.streamlit.app/)>_

## �🚀 Setup & Running the Project

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- Google Gemini API key (free at [aistudio.google.com](https://aistudio.google.com))

### Step 1: Clone and Fork

```bash
# Fork https://github.com/endee-io/endee on GitHub, then:
git clone https://github.com/<your-username>/endee
cd endee

# Clone this project separately
git clone https://github.com/<your-username>/placement-prep-ai
cd placement-prep-ai
```

### Step 2: Start Endee Vector Database

```bash
# From the placement-prep-ai directory:
docker compose up -d

# Verify it's running:
curl http://localhost:8080/api/v1/index/list
# Expected: {"indexes": []}
```

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run the Streamlit App

```bash
# Option A: Pass API key via environment variable (recommended)
export GEMINI_API_KEY="your_gemini_api_key_here"
streamlit run app.py

# Option B: Enter API key directly in the sidebar
streamlit run app.py
```

The app opens at **http://localhost:8501**

### Step 5: Load Knowledge Base

1. Open the **"📥 Load Knowledge Base"** tab
2. Enter your Gemini API key in the sidebar
3. Click **"🚀 Ingest Knowledge Base"**
4. Wait ~30 seconds for all 25 Q&As to be embedded and stored in Endee

### Step 6: Start Asking!

Go to the **"💬 Ask Questions"** tab and ask anything:

- _"Explain dynamic programming with examples"_
- _"How do I design a URL shortener?"_
- _"What are Amazon's leadership principles?"_

---

## 📁 Project Structure

```
placement-prep-ai/
├── app.py               # Main Streamlit application
├── requirements.txt     # Python dependencies
├── docker-compose.yml   # Endee vector DB setup
└── README.md            # This file
```

---

## 🎨 Features

- ✅ **Semantic Search** — Finds relevant answers by meaning, not just keywords
- ✅ **RAG Pipeline** — Gemini generates answers grounded in retrieved context
- ✅ **Source Citations** — See which knowledge chunks were used with similarity scores
- ✅ **Topic Filtering** — Focus questions on specific interview domains
- ✅ **Quick Question Chips** — One-click common interview questions
- ✅ **Chat History** — Full conversation context maintained in session
- ✅ **Browse Mode** — Explore all Q&As organised by topic
- ✅ **Adjustable top-k** — Control how many chunks feed into generation

---

## 🔧 Configuration

| Setting            | Default                 | Description                |
| ------------------ | ----------------------- | -------------------------- |
| `GEMINI_API_KEY`   | -                       | Google Gemini API key      |
| `ENDEE_URL`        | `http://localhost:8080` | Endee server URL           |
| `ENDEE_AUTH_TOKEN` | empty                   | Optional auth token        |
| top-k              | 5                       | Number of retrieved chunks |

---

## 🤝 Contributing

Pull requests welcome! Potential improvements:

- Add PDF upload support for custom study material
- Implement conversation memory across sessions using Endee metadata filters
- Add more company-specific Q&As
- Build a quiz/flashcard mode using random Endee vector retrieval

---

## 📜 License

MIT License — see [LICENSE](LICENSE)

---

_Built as part of Endee.io SDE Internship Application | Placement Prep AI uses Endee as the vector database for all semantic retrieval operations._
