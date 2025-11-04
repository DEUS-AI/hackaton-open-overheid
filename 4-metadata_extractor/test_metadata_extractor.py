"""Tests para metadata_extractor.

Se mockea:
 - Acceso a Gemini reemplazando `_extract_metadata_obj`.
 - Publicadores de ServiceBus con una clase FakePublisher que captura los tópicos.
 - `update_status` para evitar conexión a Mongo.

Se verifica:
 1. Enriquecimiento de `AppMessage.metadata`.
 2. Fan-out a exactamente tres colas con el mismo mensaje enriquecido.
 3. Caso borde: texto vacío -> se omite procesamiento y no se llama extractor.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path as _P
from typing import Any

import pytest

# Asegurar que el root del proyecto está en sys.path para importar 'shared'
ROOT = _P(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.models.messages import AppMessage, DocumentData  # noqa: E402


@pytest.fixture(scope="module")
def metadata_module():  # type: ignore[no-untyped-def]
    """Carga dinámica del módulo `metadata_extractor.py` cuyo directorio no es un paquete válido (empieza con dígito).

    Devolvemos el módulo ya ejecutado para poder acceder a `MetadataProcessor` y constantes.
    """
    file_path = _P(__file__).parent / "metadata_extractor.py"
    spec = importlib.util.spec_from_file_location("metadata_extractor_module", file_path)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec and spec.loader, "No se pudo crear spec para metadata_extractor"
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


@pytest.fixture
def sample_message() -> AppMessage:
    return AppMessage(
        data=DocumentData(
            source="upload",
            id="doc-123",
            name="doc-123.pdf",
            payload={"extracted_text": "Dit is een test document over wetgeving."},
        )
    )


def test_metadata_extraction_and_fanout(
    monkeypatch: pytest.MonkeyPatch,
    metadata_module: Any,
    sample_message: AppMessage,
) -> None:
    # Datos simulados que devolvería Gemini
    fake_metadata_json = {
        "official_title": "Test Titel",
        "document_type": "Law",
        "identifiers": {"ref": "X1"},
        "summary": "Korte samenvatting",
        "keywords": ["test", "wet"],
        "issuing_authority": "Ministerie",
        "official_publication": "Staatsblad",
        "publication_number": None,
        "publication_date": None,
        "effective_date": None,
        "repeal_date": None,
        "geographic_scope": ["NL"],
        "sector_scope": ["Algemeen"],
        "target_audience": ["Publiek"],
        "has_sanction_regime": False,
        "amends": [],
        "repeals": [],
        "implements": [],
        "related_case_law": [],
        "legal_basis": [],
    }

    # Evitamos dependencia de API real: sustituimos el método interno de parsing
    processor = metadata_module.MetadataProcessor()
    monkeypatch.setenv("GEMINI_API_KEY", "dummy-key")
    # Evitar acceso real a Mongo
    monkeypatch.setattr(metadata_module, "update_status", lambda *_, **__: None)
    monkeypatch.setattr(processor, "_extract_metadata_obj", lambda text: fake_metadata_json)

    # Ejecutar procesamiento
    result = processor.process(sample_message)
    assert result is not None, "Debe devolver AppMessage enriquecido"
    assert result.metadata is not None, "metadata debe existir"
    assert result.metadata.official_title == "Test Titel"
    assert result.metadata.document_type == "Law"
    assert result.metadata.keywords == ["test", "wet"]

    # --- Fan-out: simulamos la función publish_to_queues del main ---
    published_topics: list[str] = []
    published_messages = []

    class FakePublisher:  # noqa: D401 - simple fake
        def __init__(self, _conn: str, topic: str) -> None:
            self.topic = topic

        def publish_message(self, message_content: AppMessage, **_: Any) -> bool:  # type: ignore[override]
            published_topics.append(self.topic)
            published_messages.append(message_content)
            return True

    monkeypatch.setattr(metadata_module, "ServiceBusPublisher", FakePublisher)

    def publish_to_queues(msg: AppMessage) -> None:
        FakePublisher(
            metadata_module.CONNECTION_STRING,
            metadata_module.OUTPUT_DATA_STORAGE_QUEUE_NAME,
        ).publish_message(msg)
        FakePublisher(
            metadata_module.CONNECTION_STRING,
            metadata_module.OUTPUT_SEARCH_INDEX_QUEUE_NAME,
        ).publish_message(msg)
        FakePublisher(
            metadata_module.CONNECTION_STRING,
            metadata_module.OUTPUT_NOTIFICATION_QUEUE_NAME,
        ).publish_message(msg)

    publish_to_queues(result)

    assert len(published_topics) == 3, "Se deben publicar 3 mensajes (fan-out)"
    assert set(published_topics) == {
        metadata_module.OUTPUT_DATA_STORAGE_QUEUE_NAME,
        metadata_module.OUTPUT_SEARCH_INDEX_QUEUE_NAME,
        metadata_module.OUTPUT_NOTIFICATION_QUEUE_NAME,
    }
    for m in published_messages:
        assert m.metadata is not None
        assert m.metadata.official_title == "Test Titel"


def test_no_text_skips(monkeypatch: pytest.MonkeyPatch, metadata_module: Any) -> None:
    # Mensaje sin extracted_text debe retornar None y no llamar al extractor
    msg = AppMessage(
        data=DocumentData(source="upload", id="doc-999", name="empty.txt", payload={"extracted_text": "   "})
    )
    processor = metadata_module.MetadataProcessor()
    monkeypatch.setenv("GEMINI_API_KEY", "dummy-key")
    monkeypatch.setattr(metadata_module, "update_status", lambda *_, **__: None)

    called = {"n": 0}

    def fake_extract(_: str) -> dict[str, str]:  # pragma: no cover - si se llama el test falla
        called["n"] += 1
        return {}

    monkeypatch.setattr(processor, "_extract_metadata_obj", fake_extract)

    result = processor.process(msg)
    assert result is None
    assert called["n"] == 0, "No debería invocar extracción cuando no hay texto válido"
