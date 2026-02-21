from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class LinkInfoIssue:
    code: str
    message: str
    context: Optional[Dict[str, Any]] = None


class LinkInfoParseError(Exception):
    """Fatal parsing error for linkinfo.xml."""

    pass
