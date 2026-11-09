"""Data schemas for parsed episodes and series context.

Design rationale in DECISIONS.md under 'Output Schema for Structured Data'
and 'Parser Implementation Details'.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import json


@dataclass
class Beat:
    type: str  # CAMERA | ACTION | DIALOGUE | SOUND | UNKNOWN
    start: str  # original timestamp string e.g. "00:01:23.000"
    end: str
    start_sec: float
    end_sec: float
    character: Optional[str] = None
    emotion: Optional[str] = None
    text: str = ""
    raw: str = ""  # original line for debugging


@dataclass
class Scene:
    id: str
    start: str
    end: str
    start_sec: float
    end_sec: float
    beats: List[Beat] = field(default_factory=list)


@dataclass
class Episode:
    id: str
    number: int
    title: Optional[str]
    logline: str
    continuity_notes: str
    scenes: List[Scene] = field(default_factory=list)
    parse_warnings: List[str] = field(default_factory=list)


@dataclass
class SeriesContext:
    total_episodes: int
    loglines: List[Dict[str, Any]]  # [{"ep": 1, "logline": "..."}]
    continuity_summary: str
    characters: List[str]
    key_events: List[str] = field(default_factory=list)


def to_json(obj: Any, path: str) -> None:
    """Serialize dataclass (or list) to pretty JSON."""
    if hasattr(obj, "__dataclass_fields__"):
        data = asdict(obj)
    elif isinstance(obj, list):
        data = [asdict(o) if hasattr(o, "__dataclass_fields__") else o for o in obj]
    else:
        data = obj
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)