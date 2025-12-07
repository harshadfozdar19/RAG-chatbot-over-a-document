# server.py

import os
import uuid
import hashlib
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv("C:/Users/harsh/Desktop/rag-app/backend/.env")

# UPDATED IMPORTS
from ingest import extract_text_from_bytes, ingest_file_chunks
from embeddings import get_embeddings
from pinecone_client import get_or_create_index, clear_index_on_startup
from models import QueryRequest
from llm import answer_with_context


app = FastAPI()

# Allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# HASH FUNCTION FOR FILE CHECKING
# -------------------------------
def file_hash(raw_bytes: bytes):
    return hashlib.md5(raw_bytes).hexdigest()


# -------------------------------
# CLEAR INDEX ON SERVER START
# -------------------------------
@app.on_event("startup")
def startup_event():
    clear_index_on_startup()


@app.get("/")
def home():
    return {"status": "Backend running"}


# ============================================================
#                   MULTI-FILE UPLOAD
# ============================================================

@app.post("/api/upload")
async def upload(files: list[UploadFile] = File(...)):
    try:
        print("\n================= 📤 FILE UPLOAD START ==================\n")

        index = get_or_create_index()
        new_chunks = []
        file_count = len(files)

        print(f"📄 Files received: {file_count}")

        for file in files:

            print(f"\n📘 Processing: {file.filename}")

            raw_bytes = await file.read()
            f_hash = file_hash(raw_bytes)

            # -------------------------------
            # CHECK IF FILE ALREADY INDEXED
            # -------------------------------
            check = index.query(
                vector=[0] * 384,
                top_k=1,
                include_metadata=True,
                filter={"file_id": {"$eq": f_hash}}
            )

            if check["matches"]:
                print(f"⏭ SKIPPED (Already Indexed): {file.filename}\n")
                continue

            # Extract text
            text = extract_text_from_bytes(raw_bytes, file.content_type or "")
            if not text.strip():
                print(f"⚠ No text extracted from {file.filename}")
                continue

            # Chunk file
            chunks = ingest_file_chunks(file.filename, text)
            print(f"🧩 Chunks created: {len(chunks)}")

            for c in chunks:
                new_chunks.append((c, file.filename, f_hash))

        # No new files
        if len(new_chunks) == 0:
            return JSONResponse(status_code=400, content={"error": "No new files to index."})

        print(f"\n🔢 Total NEW chunks to index: {len(new_chunks)}")
        print("🔧 Generating embeddings...")

        embeddings = get_embeddings([c[0] for c in new_chunks])
        print("✔ Embeddings generated.\n")

        # Make vector objects
        doc_id = str(uuid.uuid4())
        vectors = []

        for i, ((chunk_text, filename, f_hash), emb) in enumerate(zip(new_chunks, embeddings)):
            vectors.append({
                "id": f"{doc_id}-{i}",
                "values": emb,
                "metadata": {
                    "text": chunk_text[:1000],
                    "source": filename,
                    "file_id": f_hash
                }
            })

        print("📌 Upserting vectors to Pinecone...")
        index.upsert(vectors=vectors)
        print("✔ Upload completed.\n")

        print("================= 📤 FILE UPLOAD DONE ==================\n")

        return {
            "message": "Upload complete",
            "files_processed": file_count,
            "new_files_indexed": len(set([x[2] for x in new_chunks])),
            "chunks_indexed": len(new_chunks),
        }

    except Exception as e:
        print("❌ ERROR during upload:", str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})



# ============================================================
#                       QUERY (RAG + LLM)
# ============================================================

@app.post("/api/query")
async def query_api(data: QueryRequest):
    try:
        print("\n================= 🤖 NEW QUERY =================")

        question = data.question
        history = data.history

        print(f"📝 Question: {question}")

        # 1️⃣ Embedding
        q_emb = get_embeddings([question])[0]
        print("✔ Embedding ready.")

        index = get_or_create_index()

        # 2️⃣ Query Pinecone
        print("\n📡 Fetching context from Pinecone...")

        result = index.query(
            vector=q_emb,
            top_k=50,
            include_metadata=True
        )

        matches = [
            f"[SOURCE: {m['metadata'].get('source', 'UNKNOWN')}] {m['metadata']['text']}"
            for m in result["matches"]
        ]

        print(f"🔍 Retrieved {len(matches)} chunks.")

        for i, m in enumerate(matches[:5]):
            print(f"\n--- MATCH {i+1} ---")
            print(m[:180] + " ...")

        context = "\n---\n".join(matches)

        # 3️⃣ LLM
        print("\n🤖 Sending to Gemini for final answer...")
        answer = answer_with_context(history, context, question)

        print("\n✅ FINAL ANSWER:")
        print(answer)
        print("=================================================\n")

        return {
            "answer": answer,
            "matches": matches,
            "source_count": len(matches),
        }

    except Exception as e:
        print("❌ ERROR during query:", str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
