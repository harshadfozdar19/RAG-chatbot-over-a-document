
# import uuid
# from fastapi import FastAPI, File, UploadFile
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# from dotenv import load_dotenv
# load_dotenv()

# from ingest import extract_text_from_bytes, chunk_text
# from embeddings import get_embeddings
# from pinecone_client import get_or_create_index
# from models import QueryRequest
# from llm import answer_with_context


# app = FastAPI()

# # CORS (allow React Dev Server)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# @app.get("/")
# def home():
#     return {"status": "Backend running"}


# @app.post("/api/upload")
# async def upload_file(file: UploadFile = File(...)):
#     try:
#         content = await file.read()
#         text = extract_text_from_bytes(content, file.content_type or "")

#         if not text.strip():
#             return JSONResponse(status_code=400, content={"error": "No text extracted"})

#         chunks = chunk_text(text)

#         # embed chunks using FREE HF embeddings
#         embeddings = get_embeddings(chunks)

#         index = get_or_create_index()
#         doc_id = str(uuid.uuid4())

#         vectors = []
#         for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
#             vectors.append({
#                 "id": f"{doc_id}-{i}",
#                 "values": emb,
#                 "metadata": {"text": chunk[:1000]},
#             })

#         index.upsert(vectors=vectors)

#         return {"message": "Document indexed", "chunks": len(chunks)}

#     except Exception as e:
#         return JSONResponse(status_code=500, content={"error": str(e)})


# @app.post("/api/query")
# async def query_api(data: QueryRequest):
#     try:
#         question = data.question
#         top_k = data.top_k

#         q_emb = get_embeddings([question])[0]

#         index = get_or_create_index()

#         result = index.query(
#             vector=q_emb,
#             top_k=top_k,
#             include_metadata=True
#         )

#         matches = [m["metadata"]["text"] for m in result["matches"]]

#         context = "\n---\n".join(matches)

#         answer = answer_with_context(context, question)

#         return {
#             "answer": answer,
#             "source_count": len(matches),
#             "matches": matches
#         }

#     except Exception as e:
#         return JSONResponse(status_code=500, content={"error": str(e)})
