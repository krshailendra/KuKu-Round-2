#!/usr/bin/env python3
"""Generate the 2-page KuKu assignment submission PDF (dense, code-accurate)."""

from pathlib import Path

from reportlab.lib.colors import HexColor, white, Color
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Flowable,
    KeepTogether,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "KuKu_Promo_Finder_Submission.pdf"

INK = HexColor("#0f172a")
MUTED = HexColor("#334155")
SOFT = HexColor("#64748b")
LINE = HexColor("#cbd5e1")
BAND = HexColor("#eef2ff")
BAND2 = HexColor("#f8fafc")
ACCENT = HexColor("#4f46e5")
ACCENT_DK = HexColor("#1e1b4b")
TEAL = HexColor("#0f766e")
TEAL_BG = HexColor("#ecfdf5")
BLUE = HexColor("#1d4ed8")
BLUE_BG = HexColor("#eff6ff")
AMBER = HexColor("#b45309")
AMBER_BG = HexColor("#fffbeb")
ROSE = HexColor("#9f1239")
ROSE_BG = HexColor("#fff1f2")
LLM = HexColor("#7c3aed")
LLM_BG = HexColor("#f5f3ff")
GOOD = HexColor("#065f46")


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def _round_box(c, x, y, w, h, r, fill, stroke, sw=0.8):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(sw)
    c.roundRect(x, y, w, h, r, fill=1, stroke=1)


def _arrow_right(c, x0, y, x1, color=SOFT):
    """Filled chevron arrow from x0→x1 at height y."""
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(1.1)
    c.line(x0, y, x1 - 1.6 * mm, y)
    path = c.beginPath()
    path.moveTo(x1, y)
    path.lineTo(x1 - 1.8 * mm, y + 1.1 * mm)
    path.lineTo(x1 - 1.8 * mm, y - 1.1 * mm)
    path.close()
    c.drawPath(path, fill=1, stroke=0)


def _arrow_down(c, x, y0, y1, color=SOFT):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(1.0)
    c.line(x, y0, x, y1 + 1.5 * mm)
    path = c.beginPath()
    path.moveTo(x, y1)
    path.lineTo(x - 1.1 * mm, y1 + 1.8 * mm)
    path.lineTo(x + 1.1 * mm, y1 + 1.8 * mm)
    path.close()
    c.drawPath(path, fill=1, stroke=0)


class SectionBar(Flowable):
    def __init__(self, text, width, fill=ACCENT):
        super().__init__()
        self.text = text
        self.box_width = width
        self.fill = fill
        self.height = 5.8 * mm

    def wrap(self, aw, ah):
        return self.box_width, self.height

    def draw(self):
        self.canv.setFillColor(self.fill)
        self.canv.roundRect(0, 0, self.box_width, self.height, 1.5, fill=1, stroke=0)
        self.canv.setFillColor(HexColor("#a5b4fc") if self.fill == ACCENT else white)
        self.canv.rect(0, 0, 1.2 * mm, self.height, fill=1, stroke=0)
        self.canv.setFillColor(white)
        self.canv.setFont("Helvetica-Bold", 7.0)
        self.canv.drawString(2.6 * mm, 1.8 * mm, self.text.upper())


class PipelineDiagram(Flowable):
    """Two-row pipeline with LLM badges and dense labels — matches live code."""

    def __init__(self, width):
        super().__init__()
        self.box_width = width
        self.height = 44 * mm

    def wrap(self, aw, ah):
        return self.box_width, self.height

    def draw(self):
        c = self.canv
        w = self.box_width

        row1 = [
            ("1  PARSE", "Scripts → scenes,\nbeats, times, loglines", BAND, ACCENT, False),
            ("2  WINDOWS", "Trigger + expand\nback/forward ~15–60s", BAND, ACCENT, False),
            ("3  MINI-ARC", "Keep hook→build→cliff\n(rule gate live)", BAND, ACCENT, False),
            ("4  SCORE + TYPE", "Rule all; hybrid polish\n/ llm re-score top-N/ep", LLM_BG, LLM, True),
        ]
        row2 = [
            ("5  TOP-K / EP", "Floor weak opens;\nspace; keep Top-K", BLUE_BG, BLUE, False),
            ("6  CONTINUITY", "Spine map: people,\nthemes, arc phases", TEAL_BG, TEAL, False),
            ("7  SERIES RANK", "Global score +\ndiversity (max 2/ep)", TEAL_BG, TEAL, False),
            ("8  MARKETER", "Protect stars; cut\nthin hooks; ~12–20", AMBER_BG, AMBER, False),
        ]

        def draw_row(items, y, box_h):
            n = len(items)
            gap = 2.8 * mm
            usable = w - 1 * mm
            bw = (usable - gap * (n - 1)) / n
            centers = []
            for i, (title, body, fill, stroke, is_llm) in enumerate(items):
                x = 0.5 * mm + i * (bw + gap)
                _round_box(c, x, y, bw, box_h, 2.0, fill, stroke, 1.0)
                c.setFillColor(stroke)
                c.roundRect(x, y + box_h - 4.6 * mm, bw, 4.6 * mm, 2.0, fill=1, stroke=0)
                c.rect(x, y + box_h - 4.6 * mm, bw, 2.3 * mm, fill=1, stroke=0)
                c.setFillColor(white)
                c.setFont("Helvetica-Bold", 6.0)
                c.drawCentredString(x + bw / 2, y + box_h - 3.2 * mm, title)
                if is_llm:
                    c.setFillColor(HexColor("#4c1d95"))
                    c.setFont("Helvetica-Bold", 4.8)
                    c.drawCentredString(x + bw / 2, y + box_h - 6.4 * mm, "◆ LLM here")
                    body_top = y + box_h - 8.8 * mm
                else:
                    body_top = y + box_h - 7.2 * mm
                c.setFillColor(MUTED)
                c.setFont("Helvetica", 5.35)
                for j, line in enumerate(body.split("\n")):
                    c.drawCentredString(x + bw / 2, body_top - j * 2.7 * mm, line)
                centers.append(x + bw / 2)
                if i < n - 1:
                    _arrow_right(c, x + bw + 0.25 * mm, y + box_h / 2, x + bw + gap - 0.25 * mm, stroke)
            return centers

        c.setFillColor(ACCENT_DK)
        c.setFont("Helvetica-Bold", 6.1)
        c.drawString(0.5 * mm, self.height - 3.0 * mm, "PIPELINE  ·  how a show becomes a promo pack")

        y1 = 23.5 * mm
        h1 = 16.0 * mm
        c1 = draw_row(row1, y1, h1)

        y2 = 2.8 * mm
        h2 = 16.0 * mm
        draw_row(row2, y2, h2)

        _arrow_down(c, c1[-1], y1 - 0.2 * mm, y2 + h2 + 0.15 * mm, ACCENT)
        c.setFillColor(SOFT)
        c.setFont("Helvetica", 4.8)
        c.drawRightString(c1[-1] - 1.5 * mm, y1 - 2.4 * mm, "then")


class DualOutputDiagram(Flowable):
    def __init__(self, width):
        super().__init__()
        self.box_width = width
        self.height = 20 * mm

    def wrap(self, aw, ah):
        return self.box_width, self.height

    def draw(self):
        c = self.canv
        w = self.box_width

        cx = w / 2
        hw, hh = 40 * mm, 9.5 * mm
        _round_box(c, cx - hw / 2, 9.2 * mm, hw, hh, 2.2, BAND, ACCENT, 1.0)
        c.setFillColor(ACCENT)
        c.roundRect(cx - hw / 2, 9.2 * mm + hh - 3.8 * mm, hw, 3.8 * mm, 2.2, fill=1, stroke=0)
        c.rect(cx - hw / 2, 9.2 * mm + hh - 3.8 * mm, hw, 1.9 * mm, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 6.0)
        c.drawCentredString(cx, 9.2 * mm + hh - 2.7 * mm, "SCORED FINALS HARVEST")
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 5.1)
        c.drawCentredString(cx, 10.5 * mm, "All Top-K windows · one pool → two jobs")

        lw = 46 * mm
        _round_box(c, 1 * mm, 1.2 * mm, lw, 11.5 * mm, 2.2, BLUE_BG, BLUE, 1.0)
        c.setFillColor(BLUE)
        c.roundRect(1 * mm, 1.2 * mm + 7.5 * mm, lw, 4.0 * mm, 2.2, fill=1, stroke=0)
        c.rect(1 * mm, 1.2 * mm + 7.5 * mm, lw, 2.0 * mm, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 6.0)
        c.drawCentredString(1 * mm + lw / 2, 1.2 * mm + 8.8 * mm, "BY EPISODE  (catalogue)")
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 5.0)
        c.drawCentredString(1 * mm + lw / 2, 5.8 * mm, "Best windows inside each episode")
        c.drawCentredString(1 * mm + lw / 2, 3.4 * mm, "Editor archive · rank_and_select")

        _round_box(c, w - lw - 1 * mm, 1.2 * mm, lw, 11.5 * mm, 2.2, TEAL_BG, TEAL, 1.0)
        c.setFillColor(TEAL)
        c.roundRect(w - lw - 1 * mm, 1.2 * mm + 7.5 * mm, lw, 4.0 * mm, 2.2, fill=1, stroke=0)
        c.rect(w - lw - 1 * mm, 1.2 * mm + 7.5 * mm, lw, 2.0 * mm, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 6.0)
        c.drawCentredString(w - lw / 2 - 1 * mm, 1.2 * mm + 8.8 * mm, "PRIORITY  (campaign pack)")
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 5.0)
        c.drawCentredString(w - lw / 2 - 1 * mm, 5.8 * mm, "What to post first for the show")
        c.drawCentredString(w - lw / 2 - 1 * mm, 3.4 * mm, "global score · diversity · marketer")

        c.setStrokeColor(ACCENT)
        c.setLineWidth(0.9)
        c.line(cx - hw / 2, 11.5 * mm, 1 * mm + lw / 2, 13.0 * mm)
        c.line(cx + hw / 2, 11.5 * mm, w - 1 * mm - lw / 2, 13.0 * mm)


class StudioStrip(Flowable):
    def __init__(self, width):
        super().__init__()
        self.box_width = width
        self.height = 8.5 * mm

    def wrap(self, aw, ah):
        return self.box_width, self.height

    def draw(self):
        c = self.canv
        roles = [
            ("Editor", "windows + mini-arc"),
            ("Scorer", "quality + types"),
            ("Producer", "continuity map"),
            ("Growth", "series rank"),
            ("Marketer", "protect / reject"),
            ("Board", "web review UI"),
        ]
        n = len(roles)
        gap = 1.2 * mm
        bw = (self.box_width - gap * (n - 1)) / n
        for i, (a, b) in enumerate(roles):
            x = i * (bw + gap)
            _round_box(c, x, 0.3 * mm, bw, 7.8 * mm, 1.5, BAND2, LINE, 0.55)
            c.setFillColor(ACCENT_DK)
            c.setFont("Helvetica-Bold", 5.4)
            c.drawCentredString(x + bw / 2, 5.2 * mm, a)
            c.setFillColor(MUTED)
            c.setFont("Helvetica", 4.8)
            c.drawCentredString(x + bw / 2, 2.3 * mm, b)
            if i < n - 1:
                _arrow_right(c, x + bw + 0.12 * mm, 4.2 * mm, x + bw + gap - 0.12 * mm, SOFT)


def styles():
    s = {}
    s["title"] = ParagraphStyle(
        "title", fontName="Helvetica-Bold", fontSize=11.2, leading=12.8,
        textColor=ACCENT_DK, spaceAfter=0.2 * mm,
    )
    s["sub"] = ParagraphStyle(
        "sub", fontName="Helvetica", fontSize=6.6, leading=8.0,
        textColor=MUTED, spaceAfter=0.7 * mm,
    )
    s["body"] = ParagraphStyle(
        "body", fontName="Helvetica", fontSize=6.55, leading=7.95,
        textColor=INK, alignment=TA_JUSTIFY, spaceAfter=0.55 * mm,
    )
    s["body2"] = ParagraphStyle(
        "body2", fontName="Helvetica", fontSize=6.35, leading=7.7,
        textColor=INK, alignment=TA_JUSTIFY, spaceAfter=0.45 * mm,
    )
    s["tiny"] = ParagraphStyle(
        "tiny", fontName="Helvetica", fontSize=5.9, leading=7.1,
        textColor=MUTED, alignment=TA_LEFT, spaceAfter=0.25 * mm,
    )
    s["bullet"] = ParagraphStyle(
        "bullet", fontName="Helvetica", fontSize=6.25, leading=7.55,
        textColor=INK, leftIndent=2.0 * mm, spaceAfter=0.18 * mm,
    )
    s["call"] = ParagraphStyle(
        "call", fontName="Helvetica-Oblique", fontSize=6.2, leading=7.5,
        textColor=ACCENT_DK, alignment=TA_LEFT, spaceAfter=0.35 * mm,
    )
    s["side"] = ParagraphStyle(
        "side", fontName="Helvetica-Oblique", fontSize=6.1, leading=7.35,
        textColor=HexColor("#4338ca"), alignment=TA_JUSTIFY,
        borderPadding=1, spaceAfter=0.4 * mm, leftIndent=0.8 * mm, rightIndent=0.8 * mm,
    )
    s["foot"] = ParagraphStyle(
        "foot", fontName="Helvetica", fontSize=5.8, leading=7.0,
        textColor=SOFT, alignment=TA_CENTER,
    )
    s["th"] = ParagraphStyle(
        "th", fontName="Helvetica-Bold", fontSize=6.15, leading=7.4,
        textColor=ACCENT_DK, alignment=TA_LEFT,
    )
    s["td"] = ParagraphStyle(
        "td", fontName="Helvetica", fontSize=6.05, leading=7.35,
        textColor=INK, alignment=TA_LEFT,
    )
    s["good"] = ParagraphStyle(
        "good", fontName="Helvetica", fontSize=6.5, leading=7.9,
        textColor=GOOD, alignment=TA_LEFT, spaceAfter=0.4 * mm,
    )
    return s


def section(title, width, fill=ACCENT):
    return SectionBar(title, width, fill=fill)


def bullets(items, st):
    return [Paragraph(f"• {it}", st["bullet"]) for it in items]


def mini_table(data, col_widths, st):
    rows = []
    for i, row in enumerate(data):
        style = st["th"] if i == 0 else st["td"]
        rows.append([Paragraph(str(c), style) for c in row])
    t = Table(rows, colWidths=col_widths, hAlign="LEFT")
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), BAND),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.0),
        ("TOPPADDING", (0, 0), (-1, -1), 1.3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.3),
    ]
    for r in range(1, len(data)):
        bg = BAND2 if r % 2 else white
        style_cmds.append(("BACKGROUND", (0, r), (-1, r), bg))
    t.setStyle(TableStyle(style_cmds))
    return t


def build():
    page_w, page_h = A4
    margin = 8.5 * mm
    width = page_w - 2 * margin
    height = page_h - 2 * margin
    st = styles()
    story = []

    # =====================================================================
    # PAGE 1
    # =====================================================================
    story.append(Paragraph("KuKu — Find the Promos: System Submission", st["title"]))
    story.append(
        Paragraph(
            "Track: <b>Find the Promos</b>  ·  Default mode: <b>Hybrid</b>  ·  "
            "Outputs: <b>By-episode catalogue</b> + <b>Campaign Priority pack</b>  ·  "
            "Built with <b>Grok</b> (xAI) as the main coding partner",
            st["sub"],
        )
    )

    # --- 1 problem ---
    story.append(section("1. Problem I picked — and why", width))
    story.append(Spacer(1, 0.7 * mm))
    story.append(
        Paragraph(
            "I chose <b>Find the Promos</b>. Kuku’s shows win attention in the feed: a short cut has seconds to stop "
            "a thumb, tell a tiny complete story, and leave an open loop. Hand-picking across ~50 episodes is slow, "
            "uneven, and biased toward whatever the editor watched last. The job is not “find spicy lines” — it is "
            "<b>find shippable storytelling windows</b>, then decide <b>what the whole series should post first</b>.",
            st["body"],
        )
    )
    story.append(
        Paragraph(
            "<b>Side note — human psychology behind the approach.</b> When I watch a short or promo for a show or "
            "web series, I rarely care if that moment is from the pilot or episode 30. If it <i>feels</i> good — clear "
            "open, rising pressure, unfinished ending — I jump to the show. Cold audiences buy a feeling and a question, "
            "not a plot lecture. So we built for <b>standalone mini-stories that still sound like this series</b>, not "
            "first-scene-only trailers and not raw dialogue dumps.",
            st["side"],
        )
    )

    # --- 2 assumptions ---
    story.append(section("2. Assumptions (incomplete info → keep moving)", width, fill=HexColor("#4338ca")))
    story.append(Spacer(1, 0.7 * mm))
    story.append(
        Paragraph(
            "The brief leaves ops gaps. I treated that as the job: make a sensible call, write it down, ship.",
            st["body2"],
        )
    )
    story.extend(
        bullets(
            [
                "<b>Scripts are source of truth</b> for structure/timing (video is downstream).",
                "<b>Most viewers are cold</b> — standalone clarity ranks with drama heat.",
                "<b>Target ~15–60s</b> storytelling windows (pack QA ~14–62s).",
                "<b>Two questions, two lists:</b> best-in-episode ≠ post-first for the show.",
                "<b>Labels are tags, not gates</b> — strong soft beats can still win.",
                "<b>API keys/quotas can vanish</b> — default must run on rules and degrade honestly.",
                "<b>One project = one show</b>; <b>humans stay final</b> on ship decisions.",
            ],
            st,
        )
    )
    story.append(Spacer(1, 0.4 * mm))

    # --- 3 how it works ---
    story.append(section("3. How the solution works", width, fill=HexColor("#3730a3")))
    story.append(Spacer(1, 0.6 * mm))
    story.append(
        Paragraph(
            "Studio line we mirrored: editor marks every episode → pool fills → series memory informs taste → "
            "growth ranks the feed → marketer protects stars / kills weak cuts → board reviews.",
            st["body2"],
        )
    )
    story.append(StudioStrip(width))
    story.append(Spacer(1, 0.8 * mm))
    story.append(PipelineDiagram(width))
    story.append(Spacer(1, 0.6 * mm))

    story.append(
        Paragraph(
            "<b>1 · Parse.</b> Scripts → scenes/beats with characters, dialogue, timestamps — timed ranges, not loose quotes.<br/>"
            "<b>2 · Windows (always rule).</b> Find triggers, expand <b>backward and forward</b> into ~15–60s storytelling "
            "spans (sub-windows inside long scenes). Mode never shrinks search — coverage stays complete and cheap.<br/>"
            "<b>3 · Mini-arc gate.</b> Keep only windows that play <b>hook → escalation → cliff</b>. Live runs use the "
            "fast rule validator; LLM mini-arc code is ready when paid capacity is wired (page 2).<br/>"
            "<b>4 · Score + type ◆ LLM (optional).</b> Rule baseline for everyone (0–10 hook/cliff/emotion/narrative/overall + types). "
            "<b>Hybrid default:</b> keep rule numbers; LLM polishes top-N/ep (reason, hook_type, types) for human review. "
            "<b>LLM mode:</b> model may re-score that top-N. No key/errors → pure rule. Long tail stays rule — we do not "
            "LLM-score every weak window.<br/>"
            "<b>5 · Top-K per episode.</b> Floor weak opens/ends; prefer spaced moments; keep Top-K (often 5). Feeds "
            "<b>By episode</b> and the campaign harvest pool.<br/>"
            "<b>6 · Continuity map.</b> Derived from this show’s episodes: people, spine themes, arc phases, spoiler guidance — "
            "living memory, not a one-title hand bible.<br/>"
            "<b>7 · Series rank + diversity.</b> Each final gets <b>series_global_score</b> (quality + hook/cliff + continuity fit + "
            "clarity + role + duration − spoiler; <b>types excluded</b>). Diversity pack (max 2/ep, soft type/theme spacing) → ~20–30 shortlist.<br/>"
            "<b>8 · Marketer (rule in web path).</b> On enriched hook/cliff text: protect top/high-global rows; hard-cut thin hooks "
            "and broken segments; soft multi-fail drops; size-trim ~12–20 → <b>Priority</b>.",
            st["body2"],
        )
    )
    story.append(Spacer(1, 0.5 * mm))
    story.append(DualOutputDiagram(width))
    story.append(Spacer(1, 0.5 * mm))
    story.append(
        Paragraph(
            "<b>Global score weights (code):</b> 0.26 overall · 0.16 hook · 0.16 cliff · 0.08 emotion · 0.06 narrative · "
            "0.14 continuity fit · 0.10 clarity · 0.04 role · 0.04 duration · −0.06 spoiler (+ small acquisition/fit bonuses). "
            "Generate writes artifacts; reopening a project reloads the last save — no silent full re-score.",
            st["tiny"],
        )
    )

    story.append(PageBreak())

    # =====================================================================
    # PAGE 2
    # =====================================================================
    story.append(Paragraph("KuKu — Find the Promos: System Submission (page 2)", st["title"]))
    story.append(
        Paragraph(
            "How we got here · modes & paid LLM path · scaling · proof · AI use · next improvements",
            st["sub"],
        )
    )

    # --- 4 evolution ---
    story.append(section("4. How the design evolved (incomplete info → decisions)", width))
    story.append(Spacer(1, 0.65 * mm))
    story.append(
        Paragraph(
            "Early AI drafts leaned “smart agents everywhere.” Elegant on a whiteboard; painful at season volume. Path we walked:",
            st["body2"],
        )
    )
    story.append(
        mini_table(
            [
                ["Stage", "Tried", "Learned → decision"],
                [
                    "Agent-per-step",
                    "Sequential LLM: expand→validate→score→classify→rank",
                    "Latency/cost explode. Structure stays rule-first; no agent chain on every beat.",
                ],
                [
                    "Score-only rules",
                    "Pure heuristics end-to-end",
                    "Great coverage/uptime; cards can feel flat → optional LLM polish.",
                ],
                [
                    "Full LLM scoring",
                    "Model judges everything",
                    "High ceiling, brittle on keys/quotas; overkill for long-tail windows.",
                ],
                [
                    "Hybrid (landed)",
                    "Rule core + LLM top-N/ep polish (or re-score in LLM mode)",
                    "Default: always ships, bounded spend, better review cards when API is up.",
                ],
                [
                    "Types as filters",
                    "Kill “wrong” genres early",
                    "Burials strong oddballs. Types = tags; formula ignores them; soft pack diversity only.",
                ],
                [
                    "One ranked list",
                    "Single scoreboard for UI",
                    "Confuses archive vs feed → By-episode catalogue + Priority campaign pack.",
                ],
            ],
            [22 * mm, 52 * mm, width - 74 * mm],
            st,
        )
    )
    story.append(Spacer(1, 0.55 * mm))

    # --- 5 modes + paid ---
    story.append(section("5. Rule · Hybrid · LLM — paid capacity raises the ceiling", width, fill=HexColor("#4338ca")))
    story.append(Spacer(1, 0.65 * mm))
    story.append(
        mini_table(
            [
                ["Mode", "Scores", "LLM role", "When"],
                ["Rule", "Heuristics all", "—", "Bulk / offline / zero spend"],
                ["Hybrid ★", "Stay rule", "Polish top-N/ep (reason, types, hook_type)", "Default product path + auto fallback"],
                ["LLM", "May re-score top-N/ep", "Full score pass on shortlist", "Paid capacity + launch taste pass"],
            ],
            [16 * mm, 28 * mm, 58 * mm, width - 102 * mm],
            st,
        )
    )
    story.append(Spacer(1, 0.45 * mm))
    story.append(
        Paragraph(
            "<b>Why Hybrid is default.</b> A promo tool that dies without a key is not a product. Rule floor on every "
            "window; tokens only where humans read (top few/ep); clean fallback if Groq is missing or rate-limited. "
            "Full eps 1–50 head-to-head: <b>[LINK: MODE_REPORT — output/full_compare/MODE_REPORT.md]</b>.",
            st["body2"],
        )
    )
    story.append(
        Paragraph(
            "<b>Paid LLM path (turn the dial, don’t rewrite).</b> Scoring uses Groq when <font face='Courier'>GROQ_API_KEY</font> "
            "exists. Free/low tiers fine for Hybrid polish; full-season LLM mode hits RPM/TPM and daily caps (we already "
            "saw quota-shaped degradation). With paid capacity:",
            st["body2"],
        )
    )
    story.extend(
        bullets(
            [
                "<b>Groq paid / higher limits (Performance or Batch-style):</b> raise concurrency + "
                "<font face='Courier'>llm_per_episode</font>; true LLM re-score on a larger shortlist; wire existing "
                "mini-arc LLM/hybrid for borderline structure. Fast open-weight models keep 50-ep harvest cost sane.",
                "<b>Batch / Flex-style (Groq Batch, or OpenAI Batch ~half realtime):</b> overnight full-catalogue taste "
                "passes — score + mini-arc offline, packs ready by morning. Best for every-show weekly ops.",
                "<b>Frontier model (OpenAI/Anthropic) on final Priority only (~20–30):</b> brand voice, spoiler nuance, "
                "copy quality after rule harvest + global rank — never on thousands of raw windows.",
                "<b>Still rule-first:</b> window expansion + long tail. Paid LLM multiplies shortlist judgment; it must "
                "not revive sequential agents on every beat.",
            ],
            st,
        )
    )
    story.append(Spacer(1, 0.35 * mm))

    # --- 6 scale ---
    story.append(section("6. Scaling to every show we make", width, fill=HexColor("#3730a3")))
    story.append(Spacer(1, 0.55 * mm))
    story.append(
        Paragraph(
            "Shape fixed; content per-title. <b>Projects</b> isolate scripts/outputs (create / generate / delete) — one "
            "app, many shows. Structure-first intake (scenes/beats) plugs new packs without a stack rewrite. Continuity "
            "is <b>derived from that show’s episodes</b>. Campaign role scales with season length (early acquisition / "
            "late payoff as soft prior). Mode dial: rule bulk · hybrid daily · llm when paid capacity + launch week. "
            "By-episode + Priority stay the two operator surfaces. Per-show care is intentional: light theme lexicon + "
            "gold slices as genre mix grows — localization of memory/eval, not a pipeline fork.",
            st["body2"],
        )
    )

    # --- 7 proof ---
    story.append(section("7. How we know it’s working", width, fill=HexColor("#0f766e")))
    story.append(Spacer(1, 0.55 * mm))
    story.append(
        Paragraph(
            "Each promo is a window with hook, cliff, rationale, scores, campaign context — argument-ready, not a "
            "keyword dump. Dual lists are real separate paths (episode Top-K vs full-finals pack + marketer). Mode "
            "compare on eps 1–50 covers agreement, unique finds, quota degradation (<b>[LINK: MODE_REPORT]</b>). "
            "<font face='Courier'>evaluation/</font> supports gold-style checks beyond UI vibes. Web Generate runs the "
            "real orchestrator + deliverable writers, so UI surfaces match emitted objects. Bar: a cold teammate opens "
            "Priority, gets why #1 is first, checks By episode coverage, glances Continuity, exports — no tribal sheet.",
            st["body2"],
        )
    )

    # --- 8 AI tools ---
    story.append(section("8. How I used AI — and where it got it wrong", width, fill=HexColor("#6d28d9")))
    story.append(Spacer(1, 0.55 * mm))
    story.append(
        Paragraph(
            "Primary partner: <b>Grok (xAI)</b> for implementation, refactors, web UI, mode plumbing, marketer/ranker "
            "iteration, and dense docs — always re-checked against <font face='Courier'>src/</font>.",
            st["body2"],
        )
    )
    story.extend(
        bullets(
            [
                "<b>Sequential agents everywhere.</b> Early Grok lean: LLM expand→validate→score→classify→rank. That "
                "would crawl on full seasons. I forced rule structure + bounded LLM only on top-N polish.",
                "<b>Score-only or pure-LLM defaults.</b> AI collapsed “good promo” into one scoreboard or full model "
                "taste. We tried both; neither is product default. Hybrid won for uptime + honest fallback + peak polish.",
                "<b>Types as hard filters.</b> Demo-convenient, growth-wrong. I kept types as tags; global formula excludes them.",
                "<b>Over-claiming docs.</b> Drafts said hybrid “re-scored judgment” and mini-arc LLM was live. Code "
                "audit fixed it: hybrid polishes copy/types; live mini-arc is rule-wired. Verify against code, not vibes.",
                "<b>UI scope creep.</b> Asked for one control (e.g. project delete); agent rewrote unrelated surfaces. "
                "I enforced narrow diffs only.",
            ],
            st,
        )
    )
    story.append(
        Paragraph(
            "Pattern: AI accelerates scaffolding; I own architecture, constraints, and “does the code match the sentence?”",
            st["call"],
        )
    )

    # --- 9 improvements ---
    story.append(section("9. What’s solid · natural next improvements", width, fill=HexColor("#1e3a8a")))
    story.append(Spacer(1, 0.55 * mm))
    story.append(
        Paragraph(
            "Solid today: storytelling windows end-to-end, dual catalogue/campaign layers, continuity-aware global "
            "rank with explicit weights, marketer protect/reject, projectized web app, Hybrid default with true rule "
            "fallback, mode-compare on full 1–50 harvest. <b>Next investments (same architecture, higher ceiling):</b> "
            "wire mini-arc LLM on paid capacity for borderline saves · batch overnight catalogue taste passes · "
            "frontier pass only on final Priority shortlist · per-genre continuity lexicons + gold sets · tighter "
            "timing robustness and optional handoff into edit tools.",
            st["body2"],
        )
    )
    story.append(Spacer(1, 0.45 * mm))

    story.append(section("10. Pointers", width, fill=HexColor("#312e81")))
    story.append(Spacer(1, 0.5 * mm))
    story.append(
        mini_table(
            [
                ["Artifact", "Where"],
                ["This 2-page submission", "docs/KuKu_Promo_Finder_Submission.pdf"],
                ["Code-verified overview", "docs/SYSTEM_OVERVIEW.md"],
                ["Mode comparison (eps 1–50)", "[LINK: MODE_REPORT — output/full_compare/MODE_REPORT.md]"],
                ["Decision log", "DECISIONS.md"],
                [
                    "Pipeline core",
                    "src/orchestrator · candidate_generator · mini_arc_validator · llm_agents · series_ranker · marketer_agent · final_deliverable",
                ],
                ["Web + eval", "web/app.py · web/services/data_layer.py · web/static/ · evaluation/"],
            ],
            [38 * mm, width - 38 * mm],
            st,
        )
    )
    story.append(Spacer(1, 0.7 * mm))
    story.append(
        Paragraph(
            "Bottom line: promos are mini-stories; catalogue ≠ campaign; Hybrid is the honest default; paid LLM raises "
            "shortlist ceiling without slow agent chains. Grok sped the build — human judgment set constraints and "
            "caught over-claims.",
            st["call"],
        )
    )
    story.append(
        Paragraph(
            "KuKu AI Generalist Assignment · Find the Promos · 2-page submission · diagrams verified against live pipeline code",
            st["foot"],
        )
    )

    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.45)
        canvas.line(margin, page_h - 6.2 * mm, page_w - margin, page_h - 6.2 * mm)
        canvas.line(margin, 7.2 * mm, page_w - margin, 7.2 * mm)
        canvas.setFont("Helvetica", 5.8)
        canvas.setFillColor(SOFT)
        canvas.drawString(margin, page_h - 5.0 * mm, "KuKu · Find the Promos · Hybrid default")
        canvas.drawRightString(page_w - margin, page_h - 5.0 * mm, f"Page {doc.page} / 2")
        canvas.drawCentredString(
            page_w / 2, 4.2 * mm,
            "Assignment submission — assumptions noted · AI use disclosed · code-verified claims",
        )
        canvas.restoreState()

    doc = BaseDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin + 0.8 * mm,
        bottomMargin=margin + 0.8 * mm,
        title="KuKu Find the Promos — Submission",
        author="KuKu Promo Finder Prototype",
    )
    frame = Frame(margin, margin + 0.8 * mm, width, height - 0.6 * mm, id="normal")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=on_page)])
    doc.build(story)
    print(f"Wrote {OUT}")
    return OUT


if __name__ == "__main__":
    build()
