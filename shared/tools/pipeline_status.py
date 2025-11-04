"""Utility helpers to update pipeline processing status for a document.

Each microservice calls update_status(service_name, document_id, status_dict)
so the webapp can show a consolidated per-document view.

Schema (Mongo collection 'pipeline_status'):
{
  _id: <document_id>,            # Provided by ingestion (or web upload)
  created_at: <iso datetime>,
  updated_at: <iso datetime>,
  states: {
     ingestion: { status: str, ts: <iso>, extra: {...} },
     validation: { ... },
     pii-scanning: { ... },
     extractor: { ... },
     data-storage: { ... },
     search-index: { ... },
     notification: { ... }
  }
}

If the document record does not exist it is created on first update.
"""

from __future__ import annotations

import datetime as dt
import os
from typing import Any

from pymongo import MongoClient, ReturnDocument
from pymongo.collection import Collection

__all__ = ["get_status_collection", "update_status", "upsert_initial"]

_mongo_client: MongoClient | None = None


def _mongo_uri() -> str:
    uri = os.getenv("MONGO_URI")
    if uri:
        return uri
    host = os.getenv("MONGO_HOST", "mongodb")
    port = os.getenv("MONGO_PORT", "27017")
    db = os.getenv("MONGO_DB", "overheid")
    user = os.getenv("MONGO_USER", "mongoadmin")
    pwd = os.getenv("MONGO_PASSWORD", "mongopass")
    auth_db = os.getenv("MONGO_AUTH_DB", "admin")
    return f"mongodb://{user}:{pwd}@{host}:{port}/{db}?authSource={auth_db}"


def _client() -> MongoClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(_mongo_uri())
    return _mongo_client


_DEF_COLL = os.getenv("MONGO_STATUS_COLLECTION", "pipeline_status")


def get_status_collection() -> Collection[Any]:
    db_name = os.getenv("MONGO_DB", "overheid")
    return _client()[db_name][_DEF_COLL]


def upsert_initial(document_id: str, initial_state: str = "uploaded", **extra: Any) -> dict[str, Any]:
    col = get_status_collection()
    now = dt.datetime.utcnow().isoformat()
    doc = col.find_one_and_update(
        {"_id": document_id},
        {
            "$setOnInsert": {"_id": document_id, "created_at": now},
            "$set": {"updated_at": now, "states.ingestion": {"status": initial_state, "ts": now, "extra": extra}},
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return doc


def update_status(service: str, document_id: str, status: str, **extra: Any) -> dict[str, Any]:
    """Set/update status for a service stage.

    Parameters
    ----------
    service: canonical service key (e.g. 'validation', 'pii-scanning').
    document_id: id of the document (same used across pipeline)
    status: short status string (e.g. 'started', 'ok', 'error')
    extra: any additional serialisable info (stored under 'extra').
    """
    if not document_id:
        raise ValueError("document_id required for update_status")
    col = get_status_collection()
    now = dt.datetime.now(tz=dt.UTC).isoformat()
    stage_field = f"states.{service}"
    update = {
        "$set": {stage_field: {"status": status, "ts": now, "extra": extra}, "updated_at": now},
        "$setOnInsert": {"created_at": now, "_id": document_id},
    }
    doc = col.find_one_and_update(
        {"_id": document_id},
        update,
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return doc
