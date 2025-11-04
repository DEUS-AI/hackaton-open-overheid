import datetime as _dt
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)
# Pipeline order derived from README and code
pipeline_order: list[str] = [
    "ingestion",
    "validation",
    "pii-scanning",
    "extractor",
    # fan-out to:
    "data-storage",
    "search-index",
    "notification",
]


def _to_iso(dt: _dt.date | _dt.datetime | None) -> str | None:
    """Return ISO-8601 string for a date or datetime (or None)."""
    if dt is None:
        return None
    # Use tuple of types at runtime; union is not supported by isinstance
    if isinstance(dt, (_dt.datetime, _dt.date)):  # noqa: UP038
        return dt.isoformat()
    return None


def _to_dt(value: Any) -> _dt.datetime | None:
    """Coerce a value to datetime if possible (ISO string or datetime)."""
    if isinstance(value, _dt.datetime):
        return value
    if isinstance(value, str):
        try:
            # Accept date-only by promoting to midnight
            if "T" not in value and len(value) == 10:
                return _dt.datetime.fromisoformat(value + "T00:00:00")
            return _dt.datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def _to_date(value: Any) -> _dt.date | None:
    if isinstance(value, _dt.date) and not isinstance(value, _dt.datetime):
        return value
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return _dt.date.fromisoformat(value.split("T")[0])
        except ValueError:
            return None
    return None


def _coerce_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    if isinstance(value, (int, float)):  # noqa: UP038
        return bool(value)
    return default


def _coerce_list_str(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if x is not None]
    if isinstance(value, str):
        return [s.strip() for s in value.split(",") if s.strip()]
    return []


@dataclass
class DocumentData:
    """
    Core document fields produced at ingestion and enriched along the way.
    """

    # Who/where the doc comes from
    source: str
    # Unchanging identifiers
    id: str | None = None
    name: str | None = None
    url: str | None = None
    extension: str | None = None

    # Payload accumulates processing outputs
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationInfo:
    timestamp: _dt.datetime
    status: str  # "valid" | "invalid"
    message: str | None = None


@dataclass
class PiiScanInfo:
    has_pii: bool
    engine: str | None = None
    matches: dict[str, list[str]] | None = None
    timestamp: _dt.datetime | None = None


@dataclass
class MetadataInfo:
    """Structured metadata extracted from the document."""

    # Core descriptive attributes
    official_title: str
    document_type: str  # e.g., "Law", "Royal Decree", "Ministerial Order"
    # Administrative core (non-defaults must come before defaults)
    issuing_authority: str
    official_publication: str  # e.g., "Boletín Oficial del Estado"
    # Optional/descriptive attributes
    identifiers: dict[str, str] = field(default_factory=dict)
    summary: str | None = None
    keywords: list[str] = field(default_factory=list)

    # --- Administrative and Publication Attributes ---
    publication_number: str | None = None
    publication_date: _dt.datetime | None = None
    effective_date: _dt.datetime | None = None
    repeal_date: _dt.datetime | None = None

    # --- Legal and Applicability Attributes ---
    geographic_scope: list[str] = field(default_factory=list)  # e.g., ["National", "Regional"]
    sector_scope: list[str] = field(default_factory=list)  # e.g., ["Health", "Technology"]
    target_audience: list[str] = field(default_factory=list)  # e.g., ["Citizens", "Businesses"]
    has_sanction_regime: bool = False

    # --- Relational Attributes ---
    amends: list[str] = field(default_factory=list)
    repeals: list[str] = field(default_factory=list)
    implements: list[str] = field(default_factory=list)
    related_case_law: list[str] = field(default_factory=list)
    legal_basis: list[str] = field(default_factory=list)  # Higher-level regulation enabling it

    timestamp: _dt.datetime | None = None


@dataclass
class AppMessage:
    """Composite application message with all sections defaulting to None.

    This provides a unified structure for the whole pipeline and can be
    serialized to the same dict shape used across services.
    """

    data: DocumentData | None = None
    validation: ValidationInfo | None = None
    pii: PiiScanInfo | None = None
    metadata: MetadataInfo | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "data": None,
            "validation": None,
            "pii": None,
            "metadata": None,
        }

        if self.data is not None:
            out["data"] = {
                "id": self.data.id,
                "source": self.data.source,
                "name": self.data.name,
                "url": self.data.url,
                "extension": self.data.extension,
                "payload": self.data.payload,
            }

        if self.validation is not None:
            out["validation"] = {
                "timestamp": _to_iso(self.validation.timestamp),
                "status": self.validation.status,
                "message": self.validation.message,
            }

        if self.pii is not None:
            out["pii"] = {
                "has_pii": self.pii.has_pii,
                "engine": self.pii.engine,
                "matches": self.pii.matches,
                "timestamp": _to_iso(self.pii.timestamp),
            }

        if self.metadata is not None:
            out["metadata"] = {
                "official_title": self.metadata.official_title,
                "document_type": self.metadata.document_type,
                "identifiers": self.metadata.identifiers,
                "summary": self.metadata.summary,
                "keywords": self.metadata.keywords,
                "issuing_authority": self.metadata.issuing_authority,
                "official_publication": self.metadata.official_publication,
                "publication_number": self.metadata.publication_number,
                "publication_date": _to_iso(self.metadata.publication_date),
                "effective_date": _to_iso(self.metadata.effective_date),
                "repeal_date": _to_iso(self.metadata.repeal_date),
                "geographic_scope": self.metadata.geographic_scope,
                "sector_scope": self.metadata.sector_scope,
                "target_audience": self.metadata.target_audience,
                "has_sanction_regime": self.metadata.has_sanction_regime,
                "amends": self.metadata.amends,
                "repeals": self.metadata.repeals,
                "implements": self.metadata.implements,
                "related_case_law": self.metadata.related_case_law,
                "legal_basis": self.metadata.legal_basis,
                "timestamp": _to_iso(self.metadata.timestamp),
            }

        return out

    @classmethod
    def parse(cls, msg: dict[str, Any]) -> "AppMessage":
        """Parse a raw envelope or content dict/string into an AppMessage.

        Accepts either a string (JSON), a dict envelope with `content`, or a
        direct content dict. Missing sections remain None.
        """
        # Data
        data_block = msg.get("data") or {}
        if isinstance(data_block, dict):
            payload = data_block.get("payload") or {}
            if not isinstance(payload, dict):
                payload = {}
            data = DocumentData(
                source=data_block.get("source") or "unknown",
                id=data_block.get("id"),
                name=data_block.get("name"),
                url=data_block.get("url"),
                extension=data_block.get("extension"),
                payload=payload,
            )
        else:
            data = None

        # Validation
        vinfo: ValidationInfo | None = None
        v_raw = msg.get("validation") or {}
        if isinstance(v_raw, dict):
            ts = _to_dt(v_raw.get("timestamp"))
            status = v_raw.get("status")
            if ts and isinstance(status, str):
                vinfo = ValidationInfo(timestamp=ts, status=status, message=v_raw.get("message"))

        # PII
        pii: PiiScanInfo | None = None
        p_raw = msg.get("pii") or {}
        if isinstance(p_raw, dict):
            has_pii = p_raw.get("has_pii")
            if isinstance(has_pii, bool):
                matches = p_raw.get("matches")
                if isinstance(matches, list):
                    matches = {} if not matches else {"generic": [str(x) for x in matches]}
                elif isinstance(matches, dict):
                    matches = {str(k): [str(x) for x in (v or [])] for k, v in matches.items()}
                else:
                    matches = None
                pii = PiiScanInfo(
                    has_pii=has_pii,
                    engine=(p_raw.get("engine") if isinstance(p_raw.get("engine"), str) else None),
                    matches=matches,
                    timestamp=_to_dt(p_raw.get("timestamp")),
                )

        # Metadata (build only if present)
        meta: MetadataInfo | None = None
        m_raw = msg.get("metadata") or {}
        if isinstance(m_raw, dict) and m_raw:
            meta = MetadataInfo(
                official_title=str(m_raw.get("official_title") or "Unknown"),
                document_type=str(m_raw.get("document_type") or "Unknown"),
                identifiers=dict(m_raw.get("identifiers") or {}),
                summary=(m_raw.get("summary") if m_raw.get("summary") is not None else None),
                keywords=_coerce_list_str(m_raw.get("keywords")),
                issuing_authority=str(m_raw.get("issuing_authority") or "Unknown"),
                official_publication=str(m_raw.get("official_publication") or "Unknown"),
                publication_number=(m_raw.get("publication_number") if m_raw.get("publication_number") else None),
                publication_date=_to_dt(m_raw.get("publication_date")),
                effective_date=_to_dt(m_raw.get("effective_date")),
                repeal_date=_to_dt(m_raw.get("repeal_date")),
                geographic_scope=_coerce_list_str(m_raw.get("geographic_scope")),
                sector_scope=_coerce_list_str(m_raw.get("sector_scope")),
                target_audience=_coerce_list_str(m_raw.get("target_audience")),
                has_sanction_regime=_coerce_bool(m_raw.get("has_sanction_regime"), False),
                amends=_coerce_list_str(m_raw.get("amends")),
                repeals=_coerce_list_str(m_raw.get("repeals")),
                implements=_coerce_list_str(m_raw.get("implements")),
                related_case_law=_coerce_list_str(m_raw.get("related_case_law")),
                legal_basis=_coerce_list_str(m_raw.get("legal_basis")),
                timestamp=_to_dt(m_raw.get("timestamp")) or _dt.datetime.now(),
            )

        return cls(data=data, validation=vinfo, pii=pii, metadata=meta)
