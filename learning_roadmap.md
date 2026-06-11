# 🧠 Jetson Edge AI — Learning Roadmap
### Understand Every Line of THIS Project (JetRAG v1)

> This roadmap is written specifically for the RAG system you have already built.
> Every concept here maps directly to a file or line of code in this folder.
> Read this like a story — each chapter unlocks the next.

---

## 🎯 What This Project Actually Does

You built an **offline, private AI financial analyst** that runs entirely on your Jetson Orin Nano.

```
[Mo Ambulance Excel File]
        ↓  convert_xlsx.py
[Plain Text / Markdown Files]
        ↓  ingest.py
[ChromaDB Vector Database]   ← Knowledge stored as math
        ↓  query.py
[Nemotron 4B LLM]            ← Running inside Docker on your Jetson's GPU
        ↓
[Financial Answer in plain English]
```

No internet. No OpenAI fees. No data leaves your device.
This is production-grade edge AI.

---

## 🗂️ Your Project Files — What Each One Does

| File | Role | Status |
|------|------|--------|
| `convert_xlsx.py` | Converts Excel (`.xlsx`) → readable text | You wrote this |
| `ingest.py` | Reads docs → chunks → embeds → saves to ChromaDB | You wrote this |
| `query.py` | Takes a question → searches DB → asks LLM → prints answer | You wrote this |
| `start_llm.sh` | Launches the Nemotron model inside Docker on the GPU | You wrote this |
| `stop_llm.sh` | Kills the Docker container and frees GPU RAM | You wrote this |
| `chroma_db/` | The actual vector database (just files on disk) | Auto-generated |
| `input_docs/` | Drop documents here to be ingested | You manage this |
| `rag_env/` | Isolated Python environment with all ML libraries | Auto-generated |

---

## 📍 PHASE 1 — The Language: Python Basics
### Goal: Read `ingest.py` and understand every single line

---

### 1.1 Imports — Using Other People's Code

```python
# ingest.py — lines 1-6
import os
import glob
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
```

**What is `import`?**
Python cannot do everything by itself. `import` loads a **library** — a bundle of
pre-written code made by someone else.

| Import | What library it is | What it gives you |
|--------|-------------------|-------------------|
| `os` | Built into Python | File system operations (`os.path`, `os.listdir`) |
| `glob` | Built into Python | Find files by pattern (`*.pdf`, `*.txt`) |
| `langchain_*` | LangChain (installed via pip) | AI pipeline building blocks |
| `HuggingFaceEmbeddings` | HuggingFace (installed via pip) | Converts text to vectors |
| `Chroma` | ChromaDB (installed via pip) | Vector database interface |

**Mental model**: `import` is like loading a plugin. The plugin is already installed
in your `rag_env/` — it was put there when you ran `pip install langchain`.

---

### 1.2 Variables & Constants

```python
# ingest.py — lines 8-9
DOCS_DIR = "input_docs"
CHROMA_PATH = "chroma_db"
```

**What is a variable?**
A name that points to a value. `DOCS_DIR` is just a label for the text `"input_docs"`.

**Why UPPERCASE?** Convention. ALL_CAPS means "this doesn't change — it's a constant."

**Why do this instead of typing `"input_docs"` everywhere?**
If you ever rename the folder, you change it in ONE place instead of ten.

---

### 1.3 Functions — Reusable Blocks

```python
# ingest.py — line 11
def main():
    ...
```

`def` creates a function. `main()` is the convention for the "starting point" of a script.
The code inside is only executed when the function is *called*.

```python
# ingest.py — lines 59-60
if __name__ == "__main__":
    main()
```

**This is the entry point.** When you run `python3 ingest.py` in the terminal,
Python sets `__name__` to `"__main__"` and this triggers `main()`.

---

### 1.4 Loops — Repeating Actions

```python
# ingest.py — lines 19-37
for file in files:
    ext = os.path.splitext(file)[1].lower()
    if ext in ['.txt', '.md', '.js']:
        loader = TextLoader(file)
    elif ext == '.pdf':
        loader = PyPDFLoader(file)
    ...
    docs.extend(loader.load())
```

**`for file in files:`** — go through every file path one by one.
**`if / elif / else`** — make a decision based on conditions.
**`ext = os.path.splitext(file)[1].lower()`** — get the file extension:
  - `"report.pdf"` → `os.path.splitext` → `("report", ".pdf")` → `[1]` → `".pdf"` → `.lower()` → `".pdf"`

**What `docs.extend(loader.load())` does:**
- `loader.load()` reads the file and returns a list of `Document` objects
- `docs.extend(...)` adds all those documents into the `docs` list
- After the loop, `docs` contains ALL documents from ALL files

---

### 1.5 Handling Errors — Try/Except

```python
# ingest.py — lines 36-37
        except Exception as e:
            print(f"Error loading {file}: {e}")
```

If loading a file crashes (corrupt PDF, wrong encoding), the `except` block catches
the crash, prints a message, and the loop continues to the next file.
Without this, one bad file would stop the entire script.

---

## 📍 PHASE 2 — Core AI Concepts: What is an Embedding?
### Goal: Understand why ChromaDB exists and what it stores

---

### 2.1 The Core Problem RAG Solves

Your LLM (Nemotron) was trained on data up to a certain date.
It knows nothing about:
- Mo Ambulance's financial data
- Clino Health Innovation's reports
- Any `.xlsx` file on your device

**RAG's solution**: Before the LLM answers, secretly inject the relevant data
from your own database into the prompt.

```
❌ Without RAG:
You: "What was ambulance revenue in FY2024?"
LLM: "I have no data on this."

✅ With RAG (what query.py does):
System grabs from ChromaDB: "FY2024 Ambulance Revenue: Rs 45,23,000"
You: "What was ambulance revenue in FY2024?"
LLM sees: [context: "FY2024 Ambulance Revenue: Rs 45,23,000"] + [your question]
LLM: "Ambulance revenue in FY2024 was Rs 45,23,000."
```

---

### 2.2 What is an Embedding?

**The most important concept in your entire stack.**

An embedding is a way to convert a sentence into a **list of numbers** (a vector)
where sentences with similar *meaning* produce *similar numbers*.

```
"Monthly ambulance revenue"   → [0.21, 0.87, 0.04, 0.55, 0.91, ...]  384 numbers
"Revenue from ambulance trips"→ [0.20, 0.86, 0.05, 0.54, 0.90, ...]  ← very similar
"Weather forecast tomorrow"   → [0.91, 0.03, 0.78, 0.12, 0.04, ...]  ← totally different
```

**This is how the system finds the right data for your question.**
When you ask `"What was revenue in April?"`, that question is also converted to
384 numbers. The system then finds which stored chunks have the closest numbers.
That is "semantic search" — searching by meaning, not keywords.

---

### 2.3 The Model Doing This: `all-MiniLM-L6-v2`

```python
# ingest.py — line 49
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
```

- `all-MiniLM-L6-v2` is a small neural network (~80MB)
- It was trained specifically to convert sentences to 384-dimensional vectors
- It runs on your **CPU** (not GPU) — fast enough for this task
- It is downloaded from HuggingFace and cached in `~/.cache/huggingface/`

**Why 384 dimensions?** It's a design choice by the model creators. More dimensions
= more expressive but slower. 384 is a good balance for sentence similarity.

---

### 2.4 Chunking — Why You Can't Feed the Whole Document

```python
# ingest.py — lines 40-45
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", " ", ""]
)
chunks = text_splitter.split_documents(docs)
```

**Why not embed the whole document at once?**

1. **The embedding model has a maximum input length** (~512 tokens / ~350 words).
   A full financial report is thousands of words. It won't fit.

2. **Precision**: If you embed a 50-page document as one vector, the vector becomes
   an average of everything. It loses the ability to point to specific facts.
   Smaller chunks = more precise retrieval.

**What `chunk_overlap=50` means:**
```
Chunk 1: "...total revenue was Rs 45,23,000. Operating costs..."
Chunk 2: "Operating costs were Rs 31,00,000. Net profit..."
                ↑ this part repeats from chunk 1's end
```
The overlap ensures a sentence split across two chunks doesn't lose context.

**`separators=["\n\n", "\n", " ", ""]`**:
Try to split at paragraph breaks first. If a paragraph is still too long, split
at line breaks. Then at spaces. Never cut mid-word.

---

### 2.5 ChromaDB — Storing the Vectors

```python
# ingest.py — lines 52-56
vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=CHROMA_PATH
)
```

**What is ChromaDB?**
A database, but instead of storing rows/columns like Excel or SQL, it stores
**vectors** and lets you search by mathematical similarity.

**What `Chroma.from_documents()` does, step by step:**
1. Takes your list of `chunks` (500-char text pieces)
2. Calls `embeddings.embed_documents(chunk.page_content)` for EACH chunk → gets 384 numbers
3. Stores: {`text`, `embedding`, `metadata (filename, page number)`} in `chroma_db/` folder
4. The folder is just files on your SSD — no separate server needed

**After running `ingest.py`**, the `chroma_db/` folder contains your entire
knowledge base as mathematical vectors, permanently stored on disk.

---

## 📍 PHASE 3 — The Query Pipeline: `query.py` Line by Line
### Goal: Understand exactly how a question becomes an answer

---

### 3.1 The Full Flow

```
python3 query.py "What was net profit in FY25?"
          ↓
Step 1: Load ChromaDB from disk
Step 2: Convert question → 384-number vector (same model as ingest)
Step 3: Find top-6 most similar chunks in ChromaDB
Step 4: Build a structured prompt: [System Role] + [6 chunks] + [Question]
Step 5: HTTP POST to http://127.0.0.1:8080/v1/chat/completions
Step 6: Docker container runs Nemotron on GPU, returns JSON response
Step 7: Parse JSON, print the answer
```

---

### 3.2 Reading Command Line Arguments

```python
# query.py — lines 10-14
if len(sys.argv) < 2:
    print("Usage: python3 query.py 'Your question here'")
    return

query_text = sys.argv[1]
```

When you run `python3 query.py "What is revenue?"`:
- `sys.argv` = `["query.py", "What is revenue?"]` — a list
- `sys.argv[0]` = `"query.py"` (script name, always index 0)
- `sys.argv[1]` = `"What is revenue?"` (your question, index 1)
- If the user forgets to type a question, `len(sys.argv) < 2` catches it

---

### 3.3 Similarity Search

```python
# query.py — line 21
results = vector_store.similarity_search(query_text, k=6)
```

- `k=6` means: return the 6 most relevant chunks
- Internally: converts `query_text` → embedding → compares to all stored embeddings → returns top 6

**Why k=6 for financial data?**
Financial reports have many related metrics spread across chunks.
`k=6` captures more context (revenue, costs, profit, year-on-year comparison)
and gives the LLM enough data to reason with.

---

### 3.4 The System Prompt — You Are the Financial Analyst

```python
# query.py — lines 28-34
system_prompt = (
    "You are a precise financial analyst AI for Clino Health Innovation and Mo Ambulance. "
    "Answer questions using ONLY the data from the provided context. "
    "Format financial figures clearly with rupee amounts (Rs X,XX,XXX). "
    "If data for a specific year or metric is missing from the context, say so explicitly. "
    "Never guess or hallucinate numbers."
)
```

**This is the most important part of any LLM application.**
The system prompt defines the LLM's **persona and constraints**.

- `"ONLY the data from the provided context"` → prevents hallucination
- `"Rs X,XX,XXX"` → forces Indian number formatting
- `"Never guess"` → critical for financial data (a wrong number is worse than no number)

**Prompt engineering** is the skill of writing system prompts that reliably
produce accurate, formatted, useful output. This is what separates a toy demo
from a real product.

---

### 3.5 Making the HTTP Request to the LLM

```python
# query.py — lines 37-50
payload = {
    "model": "my_model",
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    "max_tokens": 1000,
    "temperature": 0.1,
    "stream": False
}
response = requests.post(LLM_API_URL, json=payload, timeout=180)
```

**This is identical to calling OpenAI's ChatGPT API**, just with a different URL.

| Parameter | What It Does | Your Setting |
|-----------|-------------|--------------|
| `messages` | The conversation so far (system + user) | Your prompt |
| `max_tokens` | Maximum length of the response | 1000 tokens (~750 words) |
| `temperature` | Randomness (0=deterministic, 1=creative) | 0.1 (near-zero for factual accuracy) |
| `stream` | Stream tokens as they generate | False (wait for full answer) |

**Why `temperature: 0.1`?**
Financial data requires precision. A temperature of 0 means the model always
picks the most probable next word. This eliminates creative "hallucination".
For storytelling you'd use 0.7–0.9. For facts, stay near 0.

---

### 3.6 Parsing the Response

```python
# query.py — lines 52-53
data = response.json()
answer = data["choices"][0]["message"]["content"]
```

The LLM server returns JSON that looks like:
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "The net profit for FY25 was Rs 14,23,000."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 892,
    "completion_tokens": 47
  }
}
```

`data["choices"][0]["message"]["content"]` navigates this structure to get the answer text.

---

## 📍 PHASE 4 — The LLM Server: `start_llm.sh` Explained
### Goal: Understand what happens when you run `./start_llm.sh`

---

### 4.1 What Docker Does Here

```bash
# start_llm.sh — line 7
sudo docker run -d --rm \
  --name llm-server \
  --runtime=nvidia \
  --network host \
  -v $HOME/.cache/huggingface:/root/.cache/huggingface \
  ghcr.io/nvidia-ai-iot/llama_cpp:latest-jetson-orin \
  llama-server \
  --hf-repo nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF \
  --hf-file NVIDIA-Nemotron3-Nano-4B-Q4_K_M.gguf \
  --ctx-size 8196 \
  --alias my_model \
  --n-gpu-layers 999
```

**Breaking down every flag:**

| Flag | What It Means |
|------|--------------|
| `docker run` | Start a new container |
| `-d` | Run in background (detached) — your terminal stays free |
| `--rm` | Auto-delete the container when it stops |
| `--name llm-server` | Give it a name so you can reference it later |
| `--runtime=nvidia` | Give Docker access to the Jetson's GPU |
| `--network host` | Container shares the host's network (port 8080 is directly accessible) |
| `-v $HOME/.cache/...` | Mount your model cache folder (so it doesn't re-download every time) |
| `ghcr.io/nvidia-ai-iot/llama_cpp:latest-jetson-orin` | The Docker image (pre-compiled llama.cpp for ARM64 Jetson) |
| `llama-server` | The command to run inside the container |
| `--hf-repo nvidia/...` | Download the model from this HuggingFace repository |
| `--hf-file ...Q4_K_M.gguf` | The specific quantized model file |
| `--ctx-size 8196` | Maximum context window (how many tokens the LLM can "see" at once) |
| `--n-gpu-layers 999` | Push ALL model layers onto the GPU (maximum speed) |

**What is `.gguf`?**
A file format for storing quantized LLM models. `Q4_K_M` means:
- `Q4` = 4-bit quantization (weights compressed from 32-bit to 4-bit)
- `K_M` = Medium quality within Q4 (a balance of speed and accuracy)
- Result: A 4B parameter model in ~2.4GB instead of ~16GB

---

### 4.2 What Quantization Means (Simplified)

```
Full precision weight:  0.384729281 (32 bits of storage)
4-bit quantized:        6            (4 bits of storage, one of 16 values)

Storage reduction: 32-bit → 4-bit = 8x smaller
Quality loss: ~1-3% accuracy drop — acceptable for most tasks
```

This is why a model requiring a $10,000 server can run on your $200 Jetson.

---

## 📍 PHASE 5 — The Data Pipeline: `convert_xlsx.py`
### Goal: Understand why you need to convert Excel before ingesting

---

### 5.1 Why Excel Files Can't Go Directly Into ChromaDB

ChromaDB works with **plain text**. Excel files (`.xlsx`) are binary files —
a ZIP archive containing XML files. The LangChain `TextLoader` cannot read them.

`convert_xlsx.py` acts as a **preprocessing step**:

```
Mo Ambulance_MIS_21_26.xlsx  →  convert_xlsx.py  →  .txt / .md files
(binary Excel, unreadable)                           (plain text, ready for ingest.py)
```

**The pipeline order is:**
```bash
python3 convert_xlsx.py   # Step 1: Excel → text files in input_docs/
python3 ingest.py         # Step 2: text files → ChromaDB vectors
python3 query.py "..."    # Step 3: question → search → LLM → answer
```

---

## 📍 PHASE 6 — The Infrastructure: Jetson + Docker + GPU
### Goal: Understand WHY this runs where it does

---

### 6.1 Why NVIDIA Jetson Orin Nano?

| Requirement | How Jetson Meets It |
|-------------|-------------------|
| Must run a 4B LLM | 8GB shared RAM, 1024 CUDA GPU cores |
| Must be private (no cloud) | Fully offline, self-contained |
| Must be affordable | ~$200 (vs thousands for a GPU server) |
| Must run 24/7 | Low power consumption (~10-15W) |
| Must use NVIDIA CUDA | Native CUDA/cuDNN support |

### 6.2 The Memory Budget

```
Total RAM: 8GB
├── Ubuntu OS:              ~1.0 GB
├── Nemotron 4B (Q4_K_M):  ~2.4 GB  ← LLM in Docker
├── Embedding model:        ~0.1 GB  ← all-MiniLM-L6-v2
├── ChromaDB in memory:     ~0.1 GB  ← vector index
├── Python runtime:         ~0.2 GB
└── Headroom:               ~4.2 GB  ← large context windows, future models
```

Running headless (no desktop GUI) saves ~1.5GB, which is why you SSH in
instead of using a monitor.

---

## 📍 PHASE 7 — What to Learn Next (Expansion Path)
### This project can grow significantly

---

### 7.1 Immediate Next Steps

**Option A: FastAPI Web Server**
Wrap `query.py` in a web server so any browser can query your Jetson:
```python
from fastapi import FastAPI
app = FastAPI()

@app.post("/ask")
async def ask(question: str):
    answer = run_rag_pipeline(question)
    return {"answer": answer}

# Access from Mac: http://jetson-ip:8000/ask
```

**Option B: Auto-Ingest on File Drop**
Watch `input_docs/` for new files and auto-ingest them:
```python
import watchdog  # pip install watchdog
# Detect new .xlsx, run convert_xlsx.py, then ingest.py automatically
```

**Option C: Web UI**
A simple HTML+JS frontend that calls your FastAPI server, displayed in your
Mac's browser — giving you a ChatGPT-like interface to your financial data.

---

### 7.2 Concepts to Study (In Order)

| # | Concept | Why It Matters for THIS Project |
|---|---------|--------------------------------|
| 1 | Python functions & classes | Refactor `ingest.py` and `query.py` into reusable modules |
| 2 | HTTP & REST APIs | How `query.py` talks to `llama-server` |
| 3 | JSON | The format the LLM server returns |
| 4 | Virtual environments | Why `rag_env/` exists |
| 5 | Docker basics | What `start_llm.sh` is really doing |
| 6 | Prompt engineering | Making the LLM more accurate with better system prompts |
| 7 | FastAPI | Wrapping your RAG as a web service |
| 8 | CUDA & GPU basics | Understanding why `--n-gpu-layers 999` matters |

---

## 🔑 Key Terms — Quick Reference

| Term | Plain English Definition |
|------|--------------------------|
| **RAG** | Feeding your own documents to an LLM before it answers |
| **Embedding** | A sentence converted to ~384 numbers, where similar sentences get similar numbers |
| **Vector DB** | A database that finds similar embeddings by math, not exact text matching |
| **Chunking** | Splitting large documents into 500-character pieces for the vector DB |
| **Inference** | Running a trained AI model to get a prediction (opposite of training) |
| **Quantization** | Compressing a model's weights (32-bit → 4-bit) to fit on small devices |
| **GGUF** | File format for quantized LLM models (used by llama.cpp) |
| **llama.cpp** | C++ program that runs LLMs efficiently on consumer hardware |
| **Docker** | Packages software + dependencies in a container that runs anywhere |
| **Context window** | Maximum text the LLM can "see" at once (your setting: 8196 tokens) |
| **Temperature** | LLM randomness: 0 = deterministic/factual, 1 = creative/random |
| **Prompt** | The full text sent to the LLM (system role + retrieved context + question) |
| **Hallucination** | When an LLM invents plausible-sounding but false information |
| **Edge AI** | AI running locally on a device, not in the cloud |

---

## ✅ Understanding Checklist

Work through these in order. Don't move to the next until you can answer confidently.

- [ ] I can explain what `ingest.py` does in 2 sentences without looking at it
- [ ] I can explain what an embedding is to a non-technical person
- [ ] I understand why chunking at 500 characters is necessary
- [ ] I know what `chroma_db/` contains and how it was created
- [ ] I can explain what `query.py` does step by step (7 steps)
- [ ] I understand what `temperature: 0.1` does and why it's set that way
- [ ] I can explain what `start_llm.sh` does line by line
- [ ] I understand why the Jetson's unified memory matters for running LLMs
- [ ] I can run the full pipeline end-to-end from a fresh start
- [ ] I can modify the system prompt and explain why the output changed

---

> **Start here:** Open `ingest.py`. Read it line by line.
> For every line you don't understand, find the section in this document that explains it.
> When you can read that file top to bottom without confusion, you understand RAG.
