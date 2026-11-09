"""Schemas for storytelling promo generation.

New pipeline (2025-04):
- Generates 20-60s hook → cliffhanger promos
- Supports 3 Mini-Arc Validation modes
- Includes multi-criteria LLM scoring + Promo Type classification
"""

from dataclasses import dataclass, asdict, field
from typing import List, Optional, Literal
from enum import Enum
import json
import os


class MiniArcMode(str, Enum):
    RULE = "rule"
    LLM = "llm"
    HYBRID = "hybrid"


class PromoType(str, Enum):
    ROMANTIC = "romantic"
    DRAMATIC = "dramatic"
    THRILLING = "thrilling"
    REVENGE = "revenge"
    MYSTERY = "mystery"
    HEROIC = "heroic"
    DARK = "dark"
    WITTY = "witty"
    FAMILY_CONFLICT = "family_conflict"
    BETRAYAL = "betrayal"


@dataclass
class StoryPromoCandidate:
    """A candidate 20-60s storytelling promo clip."""
    episode: int
    scene_ids: List[str]                    # Can span multiple scenes
    start_sec: float
    end_sec: float
    duration_sec: float

    # Source info
    trigger_beat_index: int
    trigger_text: str
    window_text: str = ""  # full dialogue across the window (for validation/scoring)

    # Mini-arc validation
    mini_arc_valid: bool = False
    mini_arc_mode: Optional[str] = None
    mini_arc_reason: Optional[str] = None

    # LLM Scoring (Step 4)
    hook_strength: Optional[float] = None           # 0-10
    cliffhanger_strength: Optional[float] = None    # 0-10
    emotional_escalation: Optional[float] = None    # 0-10
    narrative_completeness: Optional[float] = None  # 0-10
    pacing: Optional[float] = None                  # 0-10
    dialogue_impact: Optional[float] = None         # 0-10
    character_stakes: Optional[float] = None        # 0-10
    overall_score: Optional[float] = None           # weighted final score
    llm_rationale: Optional[str] = None

    # Step 6: Promo Type Classification
    promo_types: List[str] = field(default_factory=list)   # e.g. ["dramatic", "family_conflict"]

    # Final selection
    rank: Optional[int] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class PromoReport:
    total_candidates: int
    episodes_scanned: int
    top_promos: List["StoryPromoCandidate"]
    mini_arc_mode_used: str
    summary: str

    def to_dict(self):
        return {
            "total_candidates": self.total_candidates,
            "episodes_scanned": self.episodes_scanned,
            "mini_arc_mode_used": self.mini_arc_mode_used,
            "top_promos": [p.to_dict() for p in self.top_promos],
            "summary": self.summary
        }


def save_json(obj, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj.to_dict() if hasattr(obj, "to_dict") else obj, f, indent=2)


# Backward compatibility alias (old brand placement schema)
@dataclass
class PromoCandidate:
    """Legacy schema for brand placement (kept for compatibility)."""
    episode: int
    scene_id: str
    beat_start: str
    beat_end: str
    start_sec: float
    end_sec: float
    character: Optional[str] = None
    text: str = ""
    detected_brand: Optional[str] = None
    trigger_reason: str = ""
    confidence: float = 0.0
    llm_score: Optional[float] = None
    llm_reason: Optional[str] = None
    final_score: Optional[float] = None
    beat_index: Optional[int] = None

    def to_dict(self):
        return asdict(self)