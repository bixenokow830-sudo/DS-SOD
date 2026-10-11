from __future__ import annotations

import html
import re
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    LongTable,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "paper" / "DS-SOD-Hybrid_论文稿_2026-10-10.md"
OUTPUT = ROOT / "output" / "pdf" / "DS-SOD-Hybrid_论文稿_2026-10-10.pdf"

PAGE_W, PAGE_H = A4
LEFT = 2.25 * cm
RIGHT = 2.25 * cm
TOP = 2.05 * cm
BOTTOM = 1.85 * cm
CONTENT_W = PAGE_W - LEFT - RIGHT


def register_fonts() -> None:
    candidates = {
        "CJK": Path(r"C:\Windows\Fonts\Deng.ttf"),
        "CJK-Bold": Path(r"C:\Windows\Fonts\Dengb.ttf"),
        "CJK-Light": Path(r"C:\Windows\Fonts\Dengl.ttf"),
        "CJK-Black": Path(r"C:\Windows\Fonts\simhei.ttf"),
    }
    for name, path in candidates.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing required font: {path}")
        pdfmetrics.registerFont(TTFont(name, str(path)))
    pdfmetrics.registerFontFamily(
        "CJK", normal="CJK", bold="CJK-Bold", italic="CJK", boldItalic="CJK-Bold"
    )


def make_styles():
    base = getSampleStyleSheet()
    styles = {}
    styles["title"] = ParagraphStyle(
        "TitleCJK",
        parent=base["Title"],
        fontName="CJK-Bold",
        fontSize=18,
        leading=25,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#142A43"),
        spaceAfter=8,
    )
    styles["subtitle"] = ParagraphStyle(
        "SubtitleCJK",
        parent=base["Normal"],
        fontName="CJK",
        fontSize=10.5,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#44546A"),
        spaceAfter=8,
    )
    styles["version"] = ParagraphStyle(
        "VersionCJK",
        parent=base["Normal"],
        fontName="CJK",
        fontSize=9,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#5C6773"),
        spaceBefore=2,
        spaceAfter=8,
    )
    styles["h1"] = ParagraphStyle(
        "H1CJK", parent=base["Heading1"], fontName="CJK-Bold", fontSize=15,
        leading=20, textColor=colors.HexColor("#17365D"), spaceBefore=14,
        spaceAfter=8, keepWithNext=True,
    )
    styles["h2"] = ParagraphStyle(
        "H2CJK", parent=base["Heading2"], fontName="CJK-Bold", fontSize=12.5,
        leading=17, textColor=colors.HexColor("#1F4E79"), spaceBefore=11,
        spaceAfter=6, keepWithNext=True,
    )
    styles["h3"] = ParagraphStyle(
        "H3CJK", parent=base["Heading3"], fontName="CJK-Bold", fontSize=10.8,
        leading=15, textColor=colors.HexColor("#2F5597"), spaceBefore=9,
        spaceAfter=5, keepWithNext=True,
    )
    styles["body"] = ParagraphStyle(
        "BodyCJK", parent=base["BodyText"], fontName="CJK", fontSize=9.6,
        leading=15.2, alignment=TA_JUSTIFY, firstLineIndent=19.2,
        textColor=colors.HexColor("#20262E"), spaceAfter=5.5,
        allowWidows=0, allowOrphans=0, wordWrap="CJK",
    )
    styles["abstract"] = ParagraphStyle(
        "AbstractCJK", parent=styles["body"], fontSize=8.8, leading=13.6,
        leftIndent=0.25*cm, rightIndent=0.25*cm,
    )
    styles["list"] = ParagraphStyle(
        "ListCJK", parent=styles["body"], firstLineIndent=-17, leftIndent=17,
        spaceAfter=4.5,
    )
    styles["quote"] = ParagraphStyle(
        "QuoteCJK", parent=styles["body"], firstLineIndent=0,
        leftIndent=0.45*cm, rightIndent=0.35*cm,
        borderColor=colors.HexColor("#9FBAD0"), borderWidth=0,
        borderPadding=(5, 7, 5, 9), backColor=colors.HexColor("#F4F8FB"),
        textColor=colors.HexColor("#3F4B59"),
    )
    styles["caption"] = ParagraphStyle(
        "CaptionCJK", parent=base["Normal"], fontName="CJK", fontSize=8.3,
        leading=12, alignment=TA_CENTER, textColor=colors.HexColor("#4D5966"),
        spaceBefore=4, spaceAfter=8,
    )
    styles["table"] = ParagraphStyle(
        "TableCJK", parent=base["Normal"], fontName="CJK", fontSize=7.3,
        leading=10.3, alignment=TA_LEFT, wordWrap="CJK",
    )
    styles["table_header"] = ParagraphStyle(
        "TableHeaderCJK", parent=styles["table"], fontName="CJK-Bold",
        textColor=colors.white, alignment=TA_CENTER,
    )
    styles["reference"] = ParagraphStyle(
        "ReferenceCJK", parent=base["Normal"], fontName="CJK", fontSize=8.5,
        leading=13, leftIndent=16, firstLineIndent=-16, alignment=TA_LEFT,
        wordWrap="CJK", spaceAfter=4,
    )
    return styles


def inline_markup(text: str) -> str:
    # ReportLab/CJK font combinations may silently drop typographic minus signs.
    # Normalize dashes to an ASCII hyphen so negative table values remain visible.
    text = text.replace("−", "-").replace("–", "-").replace("—", "-")
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r'<font name="CJK" color="#7A1F1F">\1</font>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)
    return text


def is_separator_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", c.strip()) for c in cells)


def weighted_len(s: str) -> float:
    total = 0.0
    for ch in re.sub(r"[*_`]", "", s):
        total += 1.0 if ord(ch) > 127 else 0.52
    return max(total, 3.0)


def table_widths(rows: list[list[str]]) -> list[float]:
    n = max(len(r) for r in rows)
    maxima = []
    for j in range(n):
        values = [weighted_len(r[j]) if j < len(r) else 3 for r in rows]
        maxima.append(min(max(values), 28.0))
    total = sum(maxima)
    widths = [CONTENT_W * m / total for m in maxima]
    min_w = 1.35 * cm if n >= 6 else 1.65 * cm
    widths = [max(min_w, w) for w in widths]
    scale = CONTENT_W / sum(widths)
    return [w * scale for w in widths]


def build_table(rows: list[list[str]], styles):
    n = max(len(r) for r in rows)
    normalized = [r + [""] * (n - len(r)) for r in rows]
    data = []
    for i, row in enumerate(normalized):
        style = styles["table_header"] if i == 0 else styles["table"]
        data.append([Paragraph(inline_markup(c.strip()), style) for c in row])
    table = LongTable(
        data,
        colWidths=table_widths(normalized),
        repeatRows=1,
        splitByRow=1,
        hAlign="CENTER",
        spaceBefore=4,
        spaceAfter=8,
    )
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#9BA8B4")),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#4C6175")),
        ("LEFTPADDING", (0, 0), (-1, -1), 3.2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3.2),
        ("TOPPADDING", (0, 0), (-1, -1), 4.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.2),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            commands.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F2F6FA")))
    table.setStyle(TableStyle(commands))
    return table


def image_flowable(src: str, alt: str, md_dir: Path, styles):
    path = (md_dir / src).resolve()
    if not path.exists():
        return [Paragraph(f"[图像缺失：{inline_markup(src)}]", styles["caption"])]
    with PILImage.open(path) as im:
        w, h = im.size
    max_w = CONTENT_W
    max_h = 11.2 * cm
    scale = min(max_w / w, max_h / h)
    img = Image(str(path), width=w * scale, height=h * scale)
    img.hAlign = "CENTER"
    return [Spacer(1, 4), img, Paragraph(inline_markup(alt), styles["caption"])]


def parse_markdown(md_text: str, md_dir: Path, styles):
    lines = md_text.splitlines()
    story = []
    para_buf: list[str] = []
    in_abstract = False
    first_h3 = True

    def flush_para():
        nonlocal para_buf
        if not para_buf:
            return
        raw = " ".join(s.strip() for s in para_buf).strip()
        para_buf = []
        if not raw:
            return
        if re.match(r"^\[\d+\]\s", raw):
            story.append(Paragraph(inline_markup(raw), styles["reference"]))
        else:
            style = styles["abstract"] if in_abstract else styles["body"]
            story.append(Paragraph(inline_markup(raw), style))

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        if not stripped:
            flush_para()
            i += 1
            continue

        if stripped.startswith("|"):
            flush_para()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not is_separator_row(cells):
                    rows.append(cells)
                i += 1
            if rows:
                story.append(build_table(rows, styles))
            continue

        m_img = re.fullmatch(r"!\[([^]]*)\]\(([^)]+)\)", stripped)
        if m_img:
            flush_para()
            story.extend(image_flowable(m_img.group(2), m_img.group(1), md_dir, styles))
            i += 1
            continue

        if stripped == "---":
            flush_para()
            story.append(Spacer(1, 2))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#A9B7C4")))
            story.append(Spacer(1, 5))
            i += 1
            continue

        m_head = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if m_head:
            flush_para()
            level = len(m_head.group(1))
            title = m_head.group(2)
            if level == 1:
                story.append(Paragraph(inline_markup(title), styles["title"]))
            elif level == 3 and first_h3:
                story.append(Paragraph(inline_markup(title), styles["subtitle"]))
                first_h3 = False
            else:
                if title in {"参考文献", "References"}:
                    story.append(PageBreak())
                key = "h1" if level == 2 else "h2" if level == 3 else "h3"
                story.append(Paragraph(inline_markup(title), styles[key]))
                in_abstract = title in {"摘要", "Abstract"}
            i += 1
            continue

        if stripped.startswith(">"):
            flush_para()
            q = stripped.lstrip("> ")
            style = styles["quote"]
            story.append(Paragraph(inline_markup(q), style))
            i += 1
            continue

        m_list = re.match(r"^(\d+)\.\s+(.+)$", stripped)
        if m_list:
            flush_para()
            content = f"{m_list.group(1)}. {m_list.group(2)}"
            story.append(Paragraph(inline_markup(content), styles["list"]))
            i += 1
            continue

        m_bullet = re.match(r"^[-*]\s+(.+)$", stripped)
        if m_bullet:
            flush_para()
            story.append(Paragraph("• " + inline_markup(m_bullet.group(1)), styles["list"]))
            i += 1
            continue

        para_buf.append(stripped)
        i += 1

    flush_para()
    return story


class ReviewDocTemplate(BaseDocTemplate):
    pass


def draw_header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#C7D0D8"))
    canvas.setLineWidth(0.35)
    canvas.line(LEFT, 1.22 * cm, PAGE_W - RIGHT, 1.22 * cm)
    canvas.setFont("CJK", 7.8)
    canvas.setFillColor(colors.HexColor("#6B7682"))
    canvas.drawCentredString(PAGE_W / 2, 0.78 * cm, f"第 {doc.page} 页")
    canvas.restoreState()


def main():
    register_fonts()
    styles = make_styles()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    md = SOURCE.read_text(encoding="utf-8")
    story = parse_markdown(md, SOURCE.parent, styles)

    frame = Frame(LEFT, BOTTOM, CONTENT_W, PAGE_H - TOP - BOTTOM, id="main")
    template = PageTemplate(id="paper", frames=[frame], onPage=draw_header_footer)
    doc = ReviewDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=LEFT,
        rightMargin=RIGHT,
        topMargin=TOP,
        bottomMargin=BOTTOM,
        title="面向光学遥感显著性检测的噪声语义提示无任务训练修复",
        author="DS-SOD-Hybrid",
        subject="论文稿",
    )
    doc.addPageTemplates([template])
    doc.build(story)
    print(OUTPUT)


if __name__ == "__main__":
    main()
