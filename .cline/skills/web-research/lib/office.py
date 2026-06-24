"""Detect and extract text from Office documents (DOCX via mammoth, XLSX via openpyxl).

Both libraries are optional; each extractor raises a clear install hint when its package is missing.
"""
import io


def looks_like_office(url, content_type, first_bytes):
    """Return "docx", "xlsx", or None based on URL extension / Content-Type."""
    path = url.lower().split("?")[0]
    ct = (content_type or "").lower()
    if path.endswith(".docx") or "wordprocessingml" in ct:
        return "docx"
    if path.endswith(".xlsx") or "spreadsheetml" in ct:
        return "xlsx"
    return None


def extract_office(content_bytes, kind):
    if kind == "docx":
        return _extract_docx(content_bytes)
    if kind == "xlsx":
        return _extract_xlsx(content_bytes)
    raise ValueError(f"Unsupported office type: {kind}")


def _extract_docx(content_bytes):
    try:
        import mammoth
    except ImportError:
        raise RuntimeError("Reading DOCX needs mammoth. Install it with:  pip install mammoth")
    result = mammoth.convert_to_markdown(io.BytesIO(content_bytes))
    return {"title": "", "content": (result.value or "").strip(), "kind": "docx"}


def _extract_xlsx(content_bytes):
    try:
        import openpyxl
    except ImportError:
        raise RuntimeError("Reading XLSX needs openpyxl. Install it with:  pip install openpyxl")
    workbook = openpyxl.load_workbook(io.BytesIO(content_bytes), read_only=True, data_only=True)
    lines = []
    for sheet in workbook.worksheets:
        lines.append(f"## Sheet: {sheet.title}")
        for row in sheet.iter_rows(values_only=True):
            cells = ["" if cell is None else str(cell) for cell in row]
            if any(cells):
                lines.append(" | ".join(cells))
    workbook.close()
    return {"title": "", "content": "\n".join(lines).strip(), "kind": "xlsx"}
