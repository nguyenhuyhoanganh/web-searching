"""Detect and extract text from PDF responses. Extraction needs the optional `pypdf` package."""
import io


def looks_like_pdf(url, content_type, first_bytes):
    if first_bytes[:5] == b"%PDF-":
        return True
    if "application/pdf" in (content_type or "").lower():
        return True
    return url.lower().split("?")[0].endswith(".pdf")


def extract_pdf(content_bytes):
    """Return {title, author, content, pages}. Raises RuntimeError with a hint if pypdf is missing."""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise RuntimeError(
            "Reading PDFs needs the 'pypdf' package. Install it with:  pip install pypdf"
        )
    reader = PdfReader(io.BytesIO(content_bytes))
    meta = reader.metadata or {}
    pages = [(p.extract_text() or "") for p in reader.pages]
    return {
        "title": (meta.get("/Title") or "") if hasattr(meta, "get") else "",
        "author": (meta.get("/Author") or "") if hasattr(meta, "get") else "",
        "content": "\n\n".join(pages).strip(),
        "pages": len(reader.pages),
    }
