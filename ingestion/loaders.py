"""Extract raw text from the enterprise document formats the capstone brief
requires: PDF, TXT, CSV and Excel."""

from pathlib import Path

import pandas as pd
from pypdf import PdfReader


def load_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def load_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def load_csv(path: Path) -> str:
    df = pd.read_csv(path)
    return df.to_string(index=False)


def load_excel(path: Path) -> str:
    sheets = pd.read_excel(path, sheet_name=None)
    parts = []
    for sheet_name, df in sheets.items():
        parts.append(f"--- Sheet: {sheet_name} ---\n{df.to_string(index=False)}")
    return "\n\n".join(parts)


_LOADERS = {
    ".pdf": load_pdf,
    ".txt": load_txt,
    ".csv": load_csv,
    ".xlsx": load_excel,
    ".xls": load_excel,
}


def load_document(path: Path) -> str:
    ext = Path(path).suffix.lower()
    loader = _LOADERS.get(ext)
    if loader is None:
        raise ValueError(f"Unsupported file type: {ext}")
    return loader(Path(path))