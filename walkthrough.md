# Jetson Edge RAG System Walkthrough

We have successfully turned your headless Jetson Orin Nano into a completely offline, private AI research assistant that can read your documents!

## What We Built

1. **Python Virtual Environment**: Created an isolated `rag_env` environment holding all machine learning dependencies (`langchain`, `chromadb`, `sentence-transformers`, `torch`) tailored for ARM64.
2. **Ingestion Pipeline (`ingest.py`)**: A script that reads all `.txt` and `.md` files from a directory, chunks them into pieces, converts them to mathematical vectors using the tiny `all-MiniLM-L6-v2` model, and saves them to a permanent ChromaDB database on your SSD.
3. **Query Pipeline (`query.py`)**: A script that searches your database for the most relevant text to your question, injects that text into a prompt, and streams it to your local `llama-server` (running Nemotron-3 4B) to generate a conversational answer.

---

## 🎯 The Final Test Result

To prove it worked, we created a fake file containing "Top Secret" project information that the AI couldn't possibly know from its training data.

We then ran the query script:
```bash
python3 query.py 'What is the security code for the main vault?'
```

**The LLM's Exact Offline Response:**
> *"The security code for the main laboratory vault is **7-4-9-9-Omega**."*

The Jetson successfully found the information in the vector database, fed it to the LLM, and correctly answered the question in less than 3 seconds!

---

## How to Use It Moving Forward

Both scripts are located in your `/home/biswa/` directory on the Jetson.

### 1. Add Your Own Documents
Place any `.txt` or `.md` files you want the AI to learn from into the `input_docs` folder on your Jetson.

### 2. Run the Ingestion
Whenever you add new files, activate the environment and run the ingestion script to update the database:
```bash
source rag_env/bin/activate
python3 ingest.py
```

### 3. Ask Questions!
Ask the model anything about your documents:
```bash
source rag_env/bin/activate
python3 query.py "What does the documentation say about X?"
```

### 4. Stopping and Starting the AI
I have created two convenience scripts in your `/home/biswa/` directory so you never have to type the massive Docker command again:

**To Start the AI:**
```bash
./start_llm.sh
```
*(This will launch the AI silently in the background, freeing up your terminal window!)*

**To Stop the AI (and free up your RAM):**
```bash
./stop_llm.sh
```

> [!TIP]
> **Performance Note**
> Running this entirely headless was the perfect choice. Between the 2.4 GB used by the 4B LLM model, the ~100 MB used by the embedding model, and the RAM used by the Vector Database, we comfortably fit everything inside the Orin Nano's 8GB limit with plenty of room to spare for massive context windows!
