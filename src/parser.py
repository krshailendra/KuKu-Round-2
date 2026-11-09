"""Parser v4 - Correctly handles the real episode format.

Format observed:
- EPISODE NUMBER / LOGLINE / CONTINUITY NOTES
- SCENE XX
- Scene heading + start/end
- Then blocks like:
    **CAMERA:**
    Start: (00:xx) | End: (00:yy)
    description...

    **ACTION:**
    Start: ...
    ...

    **LADY JULIANA (emotion):**
    Start: ...
    "dialogue"
"""
import re
import glob
import os
from typing import List, Optional
from src.schemas import Beat, Scene, Episode, SeriesContext, to_json

RAW_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "I Married a Broken Soldier. He was a Duke"))
PROCESSED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "processed"))

TS_RE = re.compile(r'Start:\s*\((\d{1,2}:\d{2}\.\d{2})\)\s*\|\s*End:\s*\((\d{1,2}:\d{2}\.\d{2})\)')
BLOCK_RE = re.compile(r'^\*\*([A-Z][A-Z\s]+?)\*\*:\s*$')
DIALOGUE_RE = re.compile(r'^\*\*([A-Z][A-Za-z\s]+?)(?:\s*\(([^)]+)\))?\*\*:\s*$')


def _to_seconds(ts: str) -> float:
    if not ts or ":" not in ts:
        return 0.0
    try:
        m, s = ts.split(":")
        return int(m) * 60 + float(s)
    except:
        return 0.0


def parse_episode(path: str) -> Optional[Episode]:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = [ln.rstrip() for ln in f]
    except:
        return None

    ep_num = None
    title = None
    logline = ""
    continuity = ""
    scenes: List[Scene] = []
    current_scene: Optional[Scene] = None
    current_beats: List[Beat] = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line:
            continue

        # Episode header
        if line.upper().startswith("EPISODE NUMBER:"):
            if current_scene and current_beats:
                current_scene.beats = current_beats
                scenes.append(current_scene)
            m = re.search(r"Episode\s+(\d+)", line, re.I)
            ep_num = int(m.group(1)) if m else None
            title = line.split(":", 1)[1].strip() if ":" in line else None
            current_scene = None
            current_beats = []
            continue

        if line.upper().startswith("EPISODE LOGLINE:"):
            logline = line.split(":", 1)[1].strip()
            continue

        if line.upper().startswith("CONTINUITY NOTES:"):
            continuity = line.split(":", 1)[1].strip()
            while i < len(lines) and lines[i].strip() and not lines[i].strip().upper().startswith(("SCENE", "EPISODE")):
                continuity += " " + lines[i].strip()
                i += 1
            continue

        # New scene
        if re.match(r"^SCENE\s+\d+", line, re.I):
            if current_scene and current_beats:
                current_scene.beats = current_beats
                scenes.append(current_scene)
            current_scene = Scene(id=f"scene_{len(scenes)+1}", start="00:00.00", end="00:00.00", start_sec=0, end_sec=0)
            current_beats = []
            continue

        # Scene timing
        if "Scene start:" in line and current_scene:
            m = re.search(r"(\d{1,2}:\d{2}\.\d{2})", line)
            if m:
                current_scene.start = m.group(1)
                current_scene.start_sec = _to_seconds(m.group(1))
            continue
        if "Scene end:" in line and current_scene:
            m = re.search(r"(\d{1,2}:\d{2}\.\d{2})", line)
            if m:
                current_scene.end = m.group(1)
                current_scene.end_sec = _to_seconds(m.group(1))
            continue

        # Timestamp line (comes after block header)
        ts_m = TS_RE.search(line)
        if ts_m and current_scene is not None:
            # Next non-empty line(s) are the content
            start_ts, end_ts = ts_m.group(1), ts_m.group(2)
            start_s, end_s = _to_seconds(start_ts), _to_seconds(end_ts)

            # Look ahead for the actual text
            text_lines = []
            j = i
            while j < len(lines) and not lines[j].strip().startswith("**") and not lines[j].strip().upper().startswith("SCENE"):
                if lines[j].strip():
                    text_lines.append(lines[j].strip())
                j += 1

            text = " ".join(text_lines).strip()
            if not text:
                i = j
                continue

            # Determine type from previous line
            prev = lines[i-2].strip() if i >= 2 else ""
            btype = "ACTION"
            char = None
            emo = None

            dm = DIALOGUE_RE.match(prev)
            if dm:
                btype = "DIALOGUE"
                char = dm.group(1).strip()
                emo = dm.group(2).strip() if dm.group(2) else None
            else:
                bm = BLOCK_RE.match(prev)
                if bm:
                    btype = bm.group(1).strip().upper().split()[0]

            current_beats.append(Beat(
                type=btype,
                start=start_ts,
                end=end_ts,
                start_sec=start_s,
                end_sec=end_s,
                character=char,
                emotion=emo,
                text=text,
                raw=text[:200]
            ))
            i = j
            continue

    # Final flush
    if current_scene and current_beats:
        current_scene.beats = current_beats
        scenes.append(current_scene)

    if ep_num is None:
        return None

    return Episode(
        id=f"ep_{ep_num:03d}",
        number=ep_num,
        title=title,
        logline=logline.strip(),
        continuity_notes=continuity.strip(),
        scenes=scenes,
        parse_warnings=[],
    )


def parse_all(raw_dir: str = RAW_DIR, out_dir: str = PROCESSED_DIR):
    os.makedirs(out_dir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(raw_dir, "episode-*.txt")))
    if not files:
        raise FileNotFoundError(f"No episode files in {raw_dir}")

    episodes = []
    loglines = []
    chars = set()
    cont = []

    for f in files:
        ep = parse_episode(f)
        if ep and ep.scenes:
            episodes.append(ep)
            loglines.append({"ep": ep.number, "logline": ep.logline})
            cont.append(f"EP{ep.number}: {ep.continuity_notes}")
            for s in ep.scenes:
                for b in s.beats:
                    if b.character:
                        chars.add(b.character)
            to_json(ep, os.path.join(out_dir, f"{ep.id}.json"))
            print(f"Parsed {ep.id}: {len(ep.scenes)} scenes, {sum(len(s.beats) for s in ep.scenes)} beats")

    ctx = SeriesContext(total_episodes=len(episodes), loglines=loglines,
                        continuity_summary="\n".join(cont)[:12000], characters=sorted(chars))
    to_json(ctx, os.path.join(out_dir, "series_context.json"))

    report = {"total": len(files), "parsed": len(episodes)}
    to_json(report, os.path.join(out_dir, "parse_report.json"))
    print(f"\nDone: {len(episodes)} episodes parsed.")
    return episodes, ctx


if __name__ == "__main__":
    parse_all()