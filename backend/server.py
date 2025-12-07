# server.py
import os
import uuid
import hashlib
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv(".env")

from ingest import extract_text_from_bytes, ingest_file_chunks
from embeddings import get_embeddings
from pinecone_client import get_or_create_index
from models import QueryRequest


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------
# HASH FILES TO AVOID DUPLICATES
# --------------------------
def file_hash(raw_bytes: bytes):
    return hashlib.md5(raw_bytes).hexdigest()




@app.get("/", include_in_schema=False)
def home():
    return {"status": "Backend running"}

@app.head("/", include_in_schema=False)
def home_head():
    return {}


# ============================================================
#                      MULTI-FILE UPLOAD
# ============================================================

@app.post("/api/upload")
async def upload(files: list[UploadFile] = File(...)):
    try:
        print("\n===== FILE UPLOAD START =====\n")

        index = get_or_create_index()
        file_chunks = []
        print(f"Files received: {len(files)}")

        for file in files:
            print(f"\nProcessing: {file.filename}")

            raw_bytes = await file.read()
            f_hash = file_hash(raw_bytes)

            # Check if file was already uploaded
            check = index.query(
                vector=[0] * 384,
                filter={"file_id": {"$eq": f_hash}},
                top_k=1,
                include_metadata=True
            )
            if check["matches"]:
                print(f"Skipping (already indexed): {file.filename}")
                continue

            text = extract_text_from_bytes(raw_bytes, file.content_type or "")
            if not text.strip():
                print(f"No readable text: {file.filename}")
                continue

            chunks = ingest_file_chunks(file.filename, text)
            print(f"Chunks: {len(chunks)}")

            for c in chunks:
                file_chunks.append((c, file.filename, f_hash))

        if not file_chunks:
            return JSONResponse(status_code=400, content={"error": "No new files to index."})

        print(f"\nTotal NEW chunks: {len(file_chunks)}")
        print("Generating embeddings...")

        texts_only = [c[0] for c in file_chunks]
        embeddings = get_embeddings(texts_only)

        doc_id = str(uuid.uuid4())
        vectors = []

        for i, ((chunk, fname, f_hash), emb) in enumerate(zip(file_chunks, embeddings)):
            vectors.append({
                "id": f"{doc_id}-{i}",
                "values": emb,
                "metadata": {
                    "text": chunk[:1000],
                    "source": fname,
                    "file_id": f_hash,
                }
            })

        print("Uploading to Pinecone...")
        index.upsert(vectors=vectors)
        print("DONE.")

        return {
            "message": "Upload completed",
            "chunks_indexed": len(file_chunks),
            "new_files_indexed": len(set([x[2] for x in file_chunks])),
        }

    except Exception as e:
        print("❌ ERROR:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})



# ============================================================
#                       QUERY (RAG + LLM)
# ============================================================

@app.post("/api/query")
async def query_api(data: QueryRequest):
    try:
        question = data.question
        history = data.history

        print("\n===== NEW QUERY =====")
        print("Question:", question)

        q_emb = get_embeddings([question])[0]

        index = get_or_create_index()

        result = index.query(
            vector=q_emb,
            top_k=40,
            include_metadata=True,
        )

        matches = [
            f"[SOURCE: {m['metadata'].get('source')}] {m['metadata']['text']}"
            for m in result["matches"]
        ]

        context = "\n---\n".join(matches)

        # Lazy import Gemini (saves RAM)
        from llm import answer_with_context
        answer = answer_with_context(history, context, question)

        return {
            "answer": answer,
            "source_count": len(matches),
            "matches": matches
        }

    except Exception as e:
        print("❌ Query error:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))  # Render assigns dynamic port
    uvicorn.run(app, host="0.0.0.0", port=port)
