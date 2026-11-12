"""Prepara sys.path y genera los documentos dentro de docs/."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.makedirs(DOCS, exist_ok=True)
os.chdir(DOCS)
