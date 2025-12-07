# ingest.py
from pypdf import PdfReader
import io

# ----------------------------------------------
# Extract text from uploaded file bytes
# ----------------------------------------------
def extract_text_from_bytes(content: bytes, content_type: str) -> str:
    """Extract raw text from PDF or TXT bytes."""

    # ---- PDF Extraction ----
    if "pdf" in content_type.lower():
        try:
            reader = PdfReader(io.BytesIO(content))
            text = ""

            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"

            return text

        except Exception as e:
            print("PDF extract error:", e)
            return ""

    # ---- Plain text fallback ----
    try:
        return content.decode("utf-8", errors="ignore")
    except:
        return ""


# --------------------------------------------------------
# Smart Chunking — Adjusts size for TXT vs PDF
# --------------------------------------------------------
def chunk_text(text: str, chunk_size=750, overlap=150):
    """
    Splits text into overlapping chunks.
    Overlap ensures context continuity for RAG.
    """

    text = text.replace("\n", " ").strip()
    chunks = []
    start = 0
    N = len(text)

    while start < N:
        end = min(start + chunk_size, N)
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


# --------------------------------------------------------
# NEW — Adaptive chunking based on file type
# --------------------------------------------------------
def ingest_file_chunks(filename, text):
    """
    Converts text into properly sized chunks.
    Short files (.txt) use smaller chunk size so
    Pinecone does NOT ignore them.
    """

    # ⭐ BOOST TXT ACCURACY
    if filename.lower().endswith(".txt"):
        chunk_size = 350     # smaller chunks rank higher
        overlap = 120
    else:
        chunk_size = 750     # resumes / PDFs
        overlap = 150

    # Generate raw chunks using adaptive size
    raw_chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)

    # prefix filename for source-aware RAG
    prefixed_chunks = [
        f"[SOURCE: {filename}] {chunk}"
        for chunk in raw_chunks
    ]

    return prefixed_chunks
