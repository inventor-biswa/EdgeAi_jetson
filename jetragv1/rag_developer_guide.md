# Jetson Edge AI: RAG Developer Guide

This guide details exactly what was built on your Jetson Orin Nano, where all the files are located, and how to interact with the underlying components (like ChromaDB) as a developer.

---

## 📂 Directory Structure

Everything is located in your home directory on the Jetson (`/home/biswa/`):

```text
/home/biswa/
├── rag_env/                 # The Python virtual environment holding all ML dependencies
├── input_docs/              # Folder where you drop PDFs, DOCX, PPTX, and TXT files
├── chroma_db/               # The actual Vector Database (ChromaDB) storage directory
├── ingest.py                # Script to parse documents and embed them into ChromaDB
├── query.py                 # Script to search ChromaDB and ask the LLM a question
├── start_llm.sh             # Shortcut script to boot the Nemotron LLM in the background
└── stop_llm.sh              # Shortcut script to kill the LLM and free GPU memory
```

---

## 🧠 The LLM Server

The AI model (Nemotron-3-Nano-4B) runs as an OpenAI-compatible API server using `llama.cpp`. 

* **To Start**: Run `./start_llm.sh`
* **To Stop**: Run `./stop_llm.sh`
* **API Endpoint**: Once started, the LLM listens locally on `http://127.0.0.1:8080/v1/chat/completions`. You can interact with it using any OpenAI-compatible client just by pointing the base URL to `http://localhost:8080/v1`.

---

## 📚 The Vector Database (ChromaDB)

ChromaDB is a lightweight vector database. Unlike heavy databases (like PostgreSQL), ChromaDB stores its data as simple files in the `/home/biswa/chroma_db/` directory. 

### How to Access and Inspect ChromaDB

If you want to view what is inside your database, see how many chunks there are, or clear it out, you can run a simple Python script on the Jetson.

**1. Activate the environment:**
```bash
source ~/rag_env/bin/activate
```

**2. Open the Python console:**
```bash
python3
```

**3. Run this Python code to inspect the database:**
```python
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Connect to the database
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
db = Chroma(persist_directory="chroma_db", embedding_function=embeddings)

# 1. Get the total number of chunks stored
print("Total chunks in DB:", len(db.get()["ids"]))

# 2. View the metadata of the stored files (shows what files have been ingested)
print("Files ingested:", set([meta["source"] for meta in db.get()["metadatas"]]))

# 3. Perform a manual similarity search (without asking the LLM)
results = db.similarity_search("Emergency Stack Solution", k=2)
for doc in results:
    print(f"\nFound in {doc.metadata['source']}:")
    print(doc.page_content)
```

### How to Reset the Database
If you ever want to completely wipe the AI's memory and start fresh with new documents:
1. Delete the folder: `rm -rf ~/chroma_db/`
2. Put your new documents in `~/input_docs/`
3. Run the ingestion script again: `python3 ingest.py`

---

## ⚙️ The Python Scripts

### 1. `ingest.py`
This script reads the `input_docs` folder. It uses `LangChain` to:
1. Detect the file type (PDF, DOCX, PPTX, TXT, JS, MD).
2. Extract the raw text.
3. Split the text into overlapping 500-character chunks.
4. Convert those chunks into mathematical vectors using `all-MiniLM-L6-v2`.
5. Save the vectors to the `chroma_db` folder.

**Usage:**
```bash
source ~/rag_env/bin/activate
python3 ingest.py
```

### 2. `query.py`
This script executes the actual "Retrieval-Augmented Generation" (RAG).
1. Converts your question into a vector.
2. Searches `chroma_db` for the 3 most mathematically similar chunks of text.
3. Packages your question and those 3 chunks into a prompt.
4. Sends the prompt to the `llama-server` on port 8080.
5. Prints the AI's generated answer.

**Usage:**
```bash
source ~/rag_env/bin/activate
python3 query.py "Your question goes inside quotes"
```

---

## 🚀 Next Steps for Production

Right now, everything runs via the terminal. To turn this into a product you could:
1. Wrap `query.py` in a **FastAPI** Python web server.
2. Build a sleek front-end (React/Next.js) that talks to your FastAPI server.
3. Access the Jetson's AI from your Mac's web browser!
