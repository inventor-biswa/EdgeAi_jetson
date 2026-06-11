import sys
import requests
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

CHROMA_PATH = "chroma_db"
LLM_API_URL = "http://127.0.0.1:8080/v1/chat/completions"

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 query.py 'Your question here'")
        return

    query_text = sys.argv[1]

    print("Loading database...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

    print("Searching documents for relevance...")
    results = vector_store.similarity_search(query_text, k=6)

    if not results:
        context_text = "No context available."
    else:
        context_text = "\n\n---\n\n".join([doc.page_content for doc in results])

    system_prompt = (
        "You are a precise financial analyst AI for Clino Health Innovation and Mo Ambulance. "
        "Answer questions using ONLY the data from the provided context. "
        "Format financial figures clearly with rupee amounts (Rs X,XX,XXX). "
        "If data for a specific year or metric is missing from the context, say so explicitly. "
        "Never guess or hallucinate numbers."
    )
    user_prompt = f"Context:\n{context_text}\n\nQuestion: {query_text}"

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

    print("Asking the LLM...")
    try:
        response = requests.post(LLM_API_URL, json=payload, timeout=180)
        response.raise_for_status()
        data = response.json()
        answer = data["choices"][0]["message"]["content"]

        print("\n\n" + "="*60)
        print("ANSWER:")
        print("="*60)
        print(answer)
        print("="*60)

        usage = data.get("usage", {})
        finish = data["choices"][0].get("finish_reason", "?")
        print(f"\n[Stats] Prompt: {usage.get('prompt_tokens')} tokens | Generated: {usage.get('completion_tokens')} tokens | Stop: {finish}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
