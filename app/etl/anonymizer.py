import hashlib
from typing import Dict, Optional
from app.config import settings


class NameAnonymizer:
    def __init__(self):
        self._exec_map: Dict[str, str] = {}
        self._client_map: Dict[str, str] = {}
        self._do_map: Dict[str, str] = {}

    def _get_hash_index(self, text: str, modulo: int = 1000) -> int:
        clean = text.strip().lower()
        h = int(hashlib.sha256(clean.encode("utf-8")).hexdigest(), 16)
        return (h % modulo) + 1

    def anonymize_executive(self, name: str, role: Optional[str] = None) -> str:
        if not settings.ANONYMIZE_NAMES:
            return name
        if not name or name.strip() == "":
            return "Unknown"
        clean = name.strip()
        if clean not in self._exec_map:
            # Deterministic sequential or hash index
            idx = len(self._exec_map) + 1
            self._exec_map[clean] = f"Exec-{idx:02d}"

        pseudonym = self._exec_map[clean]
        if role and role != "Executive":
            return f"{pseudonym} ({role})"
        return pseudonym

    def anonymize_client(self, name: str) -> str:
        if not settings.ANONYMIZE_NAMES:
            return name
        if not name or name.strip() == "":
            return "Unknown Client"
        clean = name.strip()
        if clean not in self._client_map:
            idx = len(self._client_map) + 1
            self._client_map[clean] = f"Client-{idx:04d}"
        return self._client_map[clean]

    def anonymize_do(self, name: str) -> str:
        if not settings.ANONYMIZE_NAMES:
            return name
        if not name or name.strip() == "":
            return "Unknown DO"
        clean = name.strip()
        if clean not in self._do_map:
            idx = len(self._do_map) + 1
            self._do_map[clean] = f"DO-{idx:02d}"
        return self._do_map[clean]

    def reset(self):
        """Reset dictionaries (useful in test suites)"""
        self._exec_map.clear()
        self._client_map.clear()
        self._do_map.clear()


anonymizer = NameAnonymizer()
