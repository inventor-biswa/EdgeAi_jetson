import os
import glob
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader, UnstructuredPowerPointLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

DOCS_DIR = "input_docs"
CHROMA_PATH = "chroma_db"

def main():
    files = glob.glob(f"{DOCS_DIR}/*.*")
    if not files:
        print("No files found in 'input_docs/' directory.")
        return

    print(f"Loading {len(files)} files...")
    docs = []
    for file in files:
        ext = os.path.splitext(file)[1].lower()
        try:
            if ext in ['.txt', '.md', '.js']:
                loader = TextLoader(file)
            elif ext == '.pdf':
                loader = PyPDFLoader(file)
            elif ext == '.docx':
                loader = Docx2txtLoader(file)
            elif ext == '.pptx':
                loader = UnstructuredPowerPointLoader(file)
            else:
                print(f"Skipping unsupported file type: {file}")
                continue
            
            docs.extend(loader.load())
            print(f"Loaded: {file}")
        except Exception as e:
            print(f"Error loading {file}: {e}")
    
    print("Chunking documents...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(docs)
    print(f"Created {len(chunks)} chunks.")

    print("Loading embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print(f"Storing vectors in {CHROMA_PATH}...")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )
    print("Done! Documents successfully ingested.")

if __name__ == "__main__":
    main()
