# app/db/vectordb.py

from pinecone import Pinecone
from app.config.config import settings

_pc = None
_index = None


def get_index():
    global _pc, _index

    if _index is not None:
        return _index

    api_key = getattr(settings, "PINECONE_API_KEY", None)
    index_name = getattr(settings, "PINECONE_INDEX", None)
    host = getattr(settings, "PINECONE_HOST", None)

    if not api_key:
        raise RuntimeError("PINECONE_API_KEY missing in .env")

    if not index_name and not host:
        raise RuntimeError("Set PINECONE_INDEX or PINECONE_HOST in .env")

    _pc = Pinecone(api_key=api_key)

    # If host provided, it’s the most stable (no describe call needed)
    if host:
        _index = _pc.Index(host=host)
    else:
        _index = _pc.Index(index_name)

    return _index
