from datetime import datetime
from typing import Any, Protocol, TypedDict, TypeVar

from shared.models.messages import AppMessage


class AzureSBMessage(TypedDict):
    """Typed dict envelope for Service Bus messages passed to processors.

    Keys mirror Azure Service Bus metadata; ``content`` carries the payload.
    """

    sequence_number: int | None
    message_id: str | None
    content_type: str | None
    subject: str | None
    enqueued_time: datetime | None
    delivery_count: int | None
    content: Any
    properties: dict[str, Any]


# Generic type variables for processors
TIn = TypeVar("TIn")
TOut = TypeVar("TOut")


class MessageProcessor(Protocol):
    """Protocol para procesadores de mensajes.

    Se flexibiliza el tipo de entrada a ``Any`` para permitir que capas
    inferiores (por ejemplo el consumer) entreguen aún un ``dict`` sin forzar
    dependencia en ``AppMessage``; las implementaciones concretas pueden
    inmediatamente convertir/validar (p.ej. ``AppMessage.parse``) y retornar
    un ``AppMessage`` procesado o ``None`` para descartar.
    """

    def process(self, message: Any) -> AppMessage | None:  # noqa: D401
        ...
