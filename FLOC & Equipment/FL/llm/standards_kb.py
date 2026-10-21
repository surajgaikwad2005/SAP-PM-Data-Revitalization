"""Standards knowledge base: Claude extracts validation rules from the STANDARDS markdown files."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import settings
from .llm_graph_agent import run_standards_kb_graph
from .llm_model import LLMModel


KB_SOURCE = "claude_built_standards_kb"

RULE_TYPES = {
    "functional_location_structure",
    "functional_location_hierarchy",
    "inventory_number_level",
    "technical_ident_no",
    "process_subprocess",
    "catalog_profile",
    "abc_indicator",
    "equipment_master_data",
}


@dataclass(frozen=True)
class StandardsChunk:
    document_name: str
    source_ref: str
    text: str


class StandardsKB:
    def __init__(
        self,
        standards_dir: str = settings.STANDARDS_DIR,
        kb_file: str = settings.STANDARDS_KB_FILE,
        env_file: str = settings.ENV_FILE,
        model: str | None = None,
        chunk_chars: int = 3500,
        max_chunks: int = 0,
    ):
        self.standards_dir = Path(standards_dir)
        self.kb_file = Path(kb_file)
        self.env_file = env_file
        self.model = model
        self.chunk_chars = chunk_chars
        self.max_chunks = max_chunks
        self.usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    def ensure(self, force_rebuild: bool = False) -> list[dict[str, Any]]:
        if self.kb_file.exists() and not force_rebuild and self.is_claude_built(self.kb_file):
            return self.load()
        logging.info("Building standards KB with Claude: %s", self.kb_file)
        return self.build()

    @staticmethod
    def is_claude_built(kb_file: Path) -> bool:
        try:
            return json.loads(Path(kb_file).read_text(encoding="utf-8")).get("source") == KB_SOURCE
        except (OSError, json.JSONDecodeError):
            return False

    def load(self) -> list[dict[str, Any]]:
        payload = json.loads(self.kb_file.read_text(encoding="utf-8"))
        records = payload.get("records", [])
        return [record for record in records if isinstance(record, dict)]

    def build(self) -> list[dict[str, Any]]:
        chunks = self._load_chunks()
        if self.max_chunks:
            chunks = chunks[: self.max_chunks]
        llm = LLMModel(env_file=self.env_file, model=self.model).create_client()
        records: list[dict[str, Any]] = []
        for index, chunk in enumerate(chunks, start=1):
            logging.info("Building standards KB chunk %s/%s: %s %s", index, len(chunks), chunk.document_name, chunk.source_ref)
            response = run_standards_kb_graph(llm, chunk.__dict__)
            self._capture_usage(response)
            records.extend(self._parse_records(response, chunk))

        records = self._deduplicate(records)
        self.kb_file.parent.mkdir(parents=True, exist_ok=True)
        self.kb_file.write_text(
            json.dumps(
                {
                    "records": records,
                    "usage": self.usage,
                    "source": KB_SOURCE,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return records

    def _load_chunks(self) -> list[StandardsChunk]:
        files = sorted(self.standards_dir.rglob("*.md")) if self.standards_dir.exists() else []
        chunks: list[StandardsChunk] = []
        for path in files:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            buffer: list[str] = []
            start_line = 1
            char_count = 0
            for line_no, line in enumerate(lines, start=1):
                if not buffer:
                    start_line = line_no
                buffer.append(line)
                char_count += len(line) + 1
                if char_count >= self.chunk_chars:
                    chunks.append(StandardsChunk(path.name, f"lines {start_line}-{line_no}", "\n".join(buffer)))
                    buffer = []
                    char_count = 0
            if buffer:
                chunks.append(StandardsChunk(path.name, f"lines {start_line}-{len(lines)}", "\n".join(buffer)))
        return chunks

    def _parse_records(self, response: Any, chunk: StandardsChunk) -> list[dict[str, Any]]:
        data = response.data.get("rules", []) if isinstance(response.data, dict) else None
        if not isinstance(data, list):
            logging.warning("Skipping empty standards KB response for %s %s", chunk.document_name, chunk.source_ref)
            return []

        records: list[dict[str, Any]] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            rule_type = str(item.get("rule_type", "")).strip()
            if rule_type not in RULE_TYPES:
                continue
            rule_text = str(item.get("rule_text", "")).strip()
            interpretation = str(item.get("interpretation", "")).strip()
            if not rule_text and not interpretation:
                continue
            rule_id = str(item.get("rule_id", "")).strip() or self._rule_id(rule_type, chunk, rule_text, interpretation)
            records.append(
                {
                    "evidence_type": "standards_kb",
                    "key": rule_id,
                    "value": rule_type,
                    "source_name": str(item.get("document_name", "") or chunk.document_name),
                    "source_ref": str(item.get("page_or_line", "") or chunk.source_ref),
                    "evidence_text": rule_text[:1200],
                    "interpretation": interpretation[:1200],
                    "related_fields": item.get("related_fields", []),
                    "keywords": item.get("keywords", []),
                    "confidence_base": 0.90,
                }
            )
        return records

    @staticmethod
    def _deduplicate(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        output = {}
        for record in records:
            key = (
                record.get("value", ""),
                record.get("source_name", ""),
                record.get("source_ref", ""),
                record.get("evidence_text", ""),
                record.get("interpretation", ""),
            )
            output[key] = record
        return list(output.values())

    @staticmethod
    def _rule_id(rule_type: str, chunk: StandardsChunk, rule_text: str, interpretation: str) -> str:
        digest = hashlib.sha1(f"{chunk.document_name}:{chunk.source_ref}:{rule_text}:{interpretation}".encode()).hexdigest()[:10]
        return f"{rule_type.upper()}_{digest}"

    def _capture_usage(self, response: Any) -> None:
        for key, value in (getattr(response, "usage", None) or {}).items():
            if key in self.usage and isinstance(value, int):
                self.usage[key] += value
