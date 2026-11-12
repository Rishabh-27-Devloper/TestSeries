"""
Tools: NEET UG ExamGOAL PDF Parser.
Parses all 146 NEET UG PDFs in C:\\Users\\Anand Shukla\\Downloads\\NEET into:
  - JSON exam papers in data/papers/neet/{paper_id}.json
  - Whole-question 160 DPI image slices in data/papers/neet/assets/{paper_id}/q{q_num}_slice.png
Supports 15 Out-of-Syllabus chapters, full length PYQs (AIPMT 1988-2015, NEET 2013-2026),
and topic-wise question banks for Physics, Chemistry, and Biology.
"""

import os
import re
import sys
import json
import glob
import time
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
import pymupdf
from PIL import Image
import io

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_NEET_DIR = r"C:\Users\Anand Shukla\Downloads\NEET"
DEST_PAPERS_DIR = os.path.join(BASE_DIR, "data", "papers", "neet")
DEST_ASSETS_DIR = os.path.join(DEST_PAPERS_DIR, "assets")

# The 15 Out-of-Syllabus chapters explicitly designated by the user
OUT_OF_SYLLABUS_CHAPTERS = {
    "gaseous state": {
        "chapter": "Gaseous State",
        "subject": "Chemistry",
        "section": "Physical Chemistry",
        "expected_q": 64
    },
    "solid state": {
        "chapter": "Solid State",
        "subject": "Chemistry",
        "section": "Physical Chemistry",
        "expected_q": 66
    },
    "surface chemistry": {
        "chapter": "Surface Chemistry",
        "subject": "Chemistry",
        "section": "Physical Chemistry",
        "expected_q": 34
    },
    "processes of isolation of elements": {
        "chapter": "Processes of Isolation of Elements",
        "subject": "Chemistry",
        "section": "Inorganic Chemistry",
        "expected_q": 33
    },
    "s-block elements": {
        "chapter": "s-Block Elements",
        "subject": "Chemistry",
        "section": "Inorganic Chemistry",
        "expected_q": 59
    },
    "hydrogen": {
        "chapter": "Hydrogen",
        "subject": "Chemistry",
        "section": "Inorganic Chemistry",
        "expected_q": 24
    },
    "environmental chemistry": {
        "chapter": "Environmental Chemistry",
        "subject": "Chemistry",
        "section": "Inorganic Chemistry",
        "expected_q": 18
    },
    "polymers": {
        "chapter": "Polymers",
        "subject": "Chemistry",
        "section": "Organic Chemistry",
        "expected_q": 40
    },
    "chemistry in everyday life": {
        "chapter": "Chemistry in Everyday Life",
        "subject": "Chemistry",
        "section": "Organic Chemistry",
        "expected_q": 26
    },
    "transport in plants": {
        "chapter": "Transport in Plants",
        "subject": "Biology",
        "section": "Botany",
        "expected_q": 69
    },
    "mineral nutrition": {
        "chapter": "Mineral Nutrition",
        "subject": "Biology",
        "section": "Botany",
        "expected_q": 62
    },
    "strategies for enhancement in food production": {
        "chapter": "Strategies for Enhancement in Food Production",
        "subject": "Biology",
        "section": "Botany",
        "expected_q": 73
    },
    "environmental issues": {
        "chapter": "Environmental Issues",
        "subject": "Biology",
        "section": "Botany",
        "expected_q": 152
    },
    "digestion and absorption": {
        "chapter": "Digestion and Absorption",
        "subject": "Biology",
        "section": "Zoology",
        "expected_q": 89
    },
    "reproduction in organisms": {
        "chapter": "Reproduction in Organisms",
        "subject": "Biology",
        "section": "Zoology",
        "expected_q": 27
    }
}


def clean_slug(text: str) -> str:
    """Converts a title to a clean snake_case identifier."""
    cleaned = re.sub(r'[^a-zA-Z0-9]+', '_', text.strip()).strip('_').lower()
    return cleaned


def find_first_ak_page(doc: pymupdf.Document) -> Optional[int]:
    """Finds the first page index of the Answer Key section."""
    first_ak_page = None
    for pno in range(len(doc) - 1, 0, -1):
        txt = doc[pno].get_text()
        if "Answer Key" in txt:
            first_ak_page = pno
    return first_ak_page


def parse_answer_key(doc: pymupdf.Document, first_ak_page: int) -> Dict[int, str]:
    """
    Parses Answer Key section from first_ak_page to end of doc.
    Matches all Q_num -> Correct Option (e.g. 'A', 'B', 'A, C', etc.).
    """
    ak_text = ""
    for pno in range(first_ak_page, len(doc)):
        ak_text += doc[pno].get_text() + "\n"

    matches = re.findall(r'(\d+)\.\s*([A-D](?:\s*,\s*[A-D])*)', ak_text)
    answers: Dict[int, str] = {}
    for q_str, ans in matches:
        q_num = int(q_str)
        # In case duplicate matches appear across columns, keep first or most complete
        if q_num not in answers:
            answers[q_num] = ans.strip()
    return answers


def extract_questions_and_slices(
    doc: pymupdf.Document,
    first_ak_page: int,
    paper_id: str,
    output_assets_dir: str,
    is_full_length: bool,
    default_section: str,
    is_out_of_syllabus_paper: bool = False
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Locates each Q{k}. across question pages (1 to first_ak_page - 1).
    Renders 160 DPI whole-question image slices.
    Stitches multi-page questions vertically.
    Detects section changes and Out-of-Syllabus markers.
    """
    os.makedirs(output_assets_dir, exist_ok=True)

    # 1. Collect question locations and section transition markers
    # In each page, examine text blocks to detect Section headers or Out-of-Syllabus banners
    q_locs = []
    
    current_sec = default_section
    current_oos = is_out_of_syllabus_paper

    for pno in range(1, first_ak_page):
        page = doc[pno]
        blocks = page.get_text("blocks")
        for b in blocks:
            text = b[4].strip()
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            if not lines:
                continue

            t_head = lines[0].lower()

            if is_full_length:
                if t_head in ["biology", "botany", "zoology", "chemistry", "physics"]:
                    current_sec = lines[0].title()
                    current_oos = False
                elif "out of syllabus" in t_head or (len(lines) > 1 and "out of syllabus" in lines[1].lower()):
                    current_oos = True

            # Check question header "Q1."
            m = re.match(r'^Q(\d+)\.', lines[0])
            if m:
                q_num = int(m.group(1))
                origin = lines[1] if len(lines) > 1 else ""
                q_locs.append({
                    "q_num": q_num,
                    "pno": pno,
                    "y0": b[1],
                    "origin": origin,
                    "section_name": current_sec,
                    "is_out_of_syllabus": current_oos
                })

    # Deduplicate by q_num (keep first) and sort
    seen_q = set()
    unique_q_locs = []
    for q in q_locs:
        if q["q_num"] not in seen_q:
            seen_q.add(q["q_num"])
            unique_q_locs.append(q)

    unique_q_locs.sort(key=lambda x: x["q_num"])

    # Per-page map
    page_q_map: Dict[int, List[Dict[str, Any]]] = {}
    for q in unique_q_locs:
        page_q_map.setdefault(q["pno"], []).append(q)
    for pno in page_q_map:
        page_q_map[pno].sort(key=lambda x: x["y0"])

    zoom = 160.0 / 72.0
    mat = pymupdf.Matrix(zoom, zoom)

    questions_data = []

    for idx, q_info in enumerate(unique_q_locs):
        q_num = q_info["q_num"]
        pno = q_info["pno"]
        page = doc[pno]
        pw = page.rect.width
        ph = page.rect.height

        y0 = max(65.0, q_info["y0"] - 5.0)

        page_qs = page_q_map[pno]
        curr_idx = page_qs.index(q_info)

        slices_to_stitch = []

        if curr_idx + 1 < len(page_qs):
            # Next question on same page
            next_q = page_qs[curr_idx + 1]
            y1 = max(y0 + 35.0, next_q["y0"] - 6.0)
            rect = pymupdf.Rect(25.0, y0, pw - 25.0, y1)
            pix = page.get_pixmap(matrix=mat, clip=rect)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            slices_to_stitch.append(img)
        else:
            # Last question on this page
            y1 = ph - 72.0
            rect = pymupdf.Rect(25.0, y0, pw - 25.0, y1)
            pix = page.get_pixmap(matrix=mat, clip=rect)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            slices_to_stitch.append(img)

            # Check if continues on next page
            next_pno = pno + 1
            if next_pno < first_ak_page:
                next_page_qs = page_q_map.get(next_pno, [])
                if not next_page_qs:
                    # Entire next page is continuation
                    p_next = doc[next_pno]
                    rect_cont = pymupdf.Rect(25.0, 65.0, p_next.rect.width - 25.0, p_next.rect.height - 72.0)
                    pix_c = p_next.get_pixmap(matrix=mat, clip=rect_cont)
                    slices_to_stitch.append(Image.open(io.BytesIO(pix_c.tobytes("png"))))
                elif next_page_qs[0]["y0"] > 135.0:
                    # Top part of next page is continuation
                    p_next = doc[next_pno]
                    y1_cont = next_page_qs[0]["y0"] - 6.0
                    rect_cont = pymupdf.Rect(25.0, 65.0, p_next.rect.width - 25.0, y1_cont)
                    pix_c = p_next.get_pixmap(matrix=mat, clip=rect_cont)
                    slices_to_stitch.append(Image.open(io.BytesIO(pix_c.tobytes("png"))))

        # Stitch slices vertically if needed
        if len(slices_to_stitch) == 1:
            final_img = slices_to_stitch[0]
        else:
            total_w = max(im.width for im in slices_to_stitch)
            total_h = sum(im.height for im in slices_to_stitch)
            final_img = Image.new("RGB", (total_w, total_h), (255, 255, 255))
            y_offset = 0
            for im in slices_to_stitch:
                final_img.paste(im, (0, y_offset))
                y_offset += im.height

        img_filename = f"q{q_num}_slice.png"
        img_full_path = os.path.join(output_assets_dir, img_filename)
        final_img.save(img_full_path, "PNG", optimize=True)

        questions_data.append({
            "q_num": q_num,
            "origin": q_info["origin"],
            "section_name": q_info["section_name"],
            "is_out_of_syllabus": q_info["is_out_of_syllabus"],
            "image_rel_url": f"assets/{paper_id}/{img_filename}",
            "image_full_path": img_full_path
        })

    meta = {
        "total_questions": len(questions_data),
        "out_of_syllabus_count": sum(1 for q in questions_data if q["is_out_of_syllabus"])
    }
    return questions_data, meta


def parse_single_neet_pdf(pdf_path: str) -> Tuple[bool, str]:
    """
    Parses a single NEET PDF into ExamPaper JSON and image assets.
    """
    fname = os.path.basename(pdf_path)
    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:
        return False, f"Failed to open {fname}: {e}"

    p0_text = doc[0].get_text()

    # Determine if Full Length or Topic-wise
    is_full_length = bool(re.search(r'(AIPMT|NEET \d{4})', fname))

    # Find Answer Key page
    first_ak_page = find_first_ak_page(doc)
    if first_ak_page is None:
        return False, f"No answer key page found in {fname}"

    answers_map = parse_answer_key(doc, first_ak_page)

    if is_full_length:
        # Full Length Paper
        # Title e.g. "NEET 2024 Question Paper with Answer Key.pdf" -> "NEET 2024"
        title = fname.replace(" Question Paper with Answer Key.pdf", "").replace(".pdf", "").strip()
        slug = clean_slug(title)
        paper_id = f"neet_full_{slug}"
        category = "PYQ Full Length"

        # Year extraction
        m_yr = re.search(r'\b(19\d\d|20\d\d)\b', title)
        year = int(m_yr.group(1)) if m_yr else None

        # Duration & Marks
        # NEET full length is typically 200 minutes, 720 marks (or total_q * 4)
        duration_minutes = 200
        default_section = "Biology"
        is_out_of_syllabus_paper = False
        subject = "NEET Comprehensive"
        chapter = "Full Length PYQ"

    else:
        # Topic-wise Paper
        # Title e.g. "NEET Gaseous State Previous Year Questions with Answer Key.pdf" -> "Gaseous State"
        raw_topic = fname.replace("NEET ", "").replace(" Previous Year Questions with Answer Key", "").replace("(1)", "").replace(".pdf", "").strip()
        category = "Topic-wise PYQ"
        year = None

        # Check Subject from Cover Page
        if "CHEMISTRY" in p0_text:
            cover_sub = "Chemistry"
        elif "PHYSICS" in p0_text:
            cover_sub = "Physics"
        elif "BIOLOGY" in p0_text:
            cover_sub = "Biology"
        else:
            cover_sub = "General"

        # Check if Out of Syllabus
        topic_lower = raw_topic.lower()
        if topic_lower in OUT_OF_SYLLABUS_CHAPTERS:
            oos_info = OUT_OF_SYLLABUS_CHAPTERS[topic_lower]
            chapter = oos_info["chapter"]
            subject = oos_info["subject"]
            default_section = oos_info["section"]
            is_out_of_syllabus_paper = True
        else:
            chapter = raw_topic
            subject = cover_sub
            default_section = cover_sub
            is_out_of_syllabus_paper = False

        # Biomolecules disambiguation
        if raw_topic.lower() == "biomolecules":
            if "BIOLOGY" in p0_text:
                subject = "Biology"
                default_section = "Botany"
                paper_id = "neet_topicwise_biology_biomolecules"
            else:
                subject = "Chemistry"
                default_section = "Organic Chemistry"
                paper_id = "neet_topicwise_chemistry_biomolecules"
        else:
            paper_id = f"neet_topicwise_{clean_slug(subject)}_{clean_slug(chapter)}"

        title = f"NEET - {chapter} ({subject})"
        duration_minutes = 60  # Will be adjusted by question count (1 min per question, min 45)

    out_file = os.path.join(DEST_PAPERS_DIR, f"{paper_id}.json")
    if os.path.exists(out_file):
        return True, f"Already parsed {paper_id} (skipping)"

    paper_assets_dir = os.path.join(DEST_ASSETS_DIR, paper_id)

    # Extract questions and slice images
    questions_data, meta = extract_questions_and_slices(
        doc=doc,
        first_ak_page=first_ak_page,
        paper_id=paper_id,
        output_assets_dir=paper_assets_dir,
        is_full_length=is_full_length,
        default_section=default_section,
        is_out_of_syllabus_paper=is_out_of_syllabus_paper
    )

    if not questions_data:
        return False, f"No questions extracted for {fname}"

    # Recalculate duration & marks for topic-wise
    if not is_full_length:
        duration_minutes = max(30, int(len(questions_data) * 1.0))
        total_marks = float(len(questions_data) * 4.0)
    else:
        total_marks = float(len(questions_data) * 4.0)

    # Group questions by section
    sections_map: Dict[str, List[Dict[str, Any]]] = {}
    
    for q in questions_data:
        q_num = q["q_num"]
        sec_name = q["section_name"]
        correct_ans = answers_map.get(q_num, "A")
        q_oos = q["is_out_of_syllabus"]

        # Option list for standard MCQ
        options = [
            {"id": "A", "text": "(A)"},
            {"id": "B", "text": "(B)"},
            {"id": "C", "text": "(C)"},
            {"id": "D", "text": "(D)"}
        ]

        q_json = {
            "questionId": q_num,
            "questionNumber": q_num,
            "type": "MCQ",
            "sectionId": clean_slug(sec_name),
            "sectionName": sec_name,
            "questionText": f"Question {q_num}" + (f" ({q['origin']})" if q["origin"] else ""),
            "imageUrl": q["image_rel_url"],
            "positiveMarks": 4.0,
            "negativeMarks": 1.0,
            "correctAnswer": correct_ans,
            "options": options,
            "isOutOfSyllabus": q_oos,
            "is_out_of_syllabus": q_oos
        }
        sections_map.setdefault(sec_name, []).append(q_json)

    # Build sections list
    sections_list = []
    for sec_name, sec_questions in sections_map.items():
        sections_list.append({
            "sectionId": clean_slug(sec_name),
            "sectionName": sec_name,
            "totalQuestions": len(sec_questions),
            "questions": sec_questions
        })

    # Build final paper JSON
    paper_json = {
        "paperId": paper_id,
        "title": title,
        "category": category,
        "year": year,
        "examType": "NEET",
        "durationMinutes": duration_minutes,
        "totalMarks": total_marks,
        "totalQuestions": len(questions_data),
        "isOutOfSyllabus": is_out_of_syllabus_paper,
        "is_out_of_syllabus": is_out_of_syllabus_paper,
        "hasOutOfSyllabusQuestions": meta["out_of_syllabus_count"] > 0,
        "outOfSyllabusCount": meta["out_of_syllabus_count"],
        "subject": subject,
        "chapter": chapter,
        "description": f"NEET UG {title} - {len(questions_data)} Questions (+4/-1 marking scheme)",
        "instructions": [
            "This test contains multiple-choice questions with 4 options each.",
            "Each question carries +4.0 marks for the correct answer.",
            "There is a negative marking of -1.0 marks for each incorrect response.",
            "Unattempted questions will not be evaluated and carry 0 marks.",
            "Questions marked with 'Out of Syllabus' are from removed chapters kept for practice."
        ],
        "sections": sections_list
    }

    # Save JSON
    os.makedirs(DEST_PAPERS_DIR, exist_ok=True)
    out_file = os.path.join(DEST_PAPERS_DIR, f"{paper_id}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(paper_json, f, indent=2, ensure_ascii=False)

    return True, f"Parsed {paper_id}: {len(questions_data)} Qs ({meta['out_of_syllabus_count']} OOS) -> {out_file}"


def main():
    files = sorted(glob.glob(os.path.join(SRC_NEET_DIR, "*.pdf")))
    print(f"Found {len(files)} NEET PDFs in {SRC_NEET_DIR}")

    os.makedirs(DEST_PAPERS_DIR, exist_ok=True)
    os.makedirs(DEST_ASSETS_DIR, exist_ok=True)

    t0 = time.time()
    success_count = 0
    fail_count = 0
    total_qs = 0
    total_oos_qs = 0

    print("Beginning extraction across 4 worker processes...")
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(parse_single_neet_pdf, fpath): fpath for fpath in files}
        for idx, fut in enumerate(as_completed(futures), 1):
            fpath = futures[fut]
            fname = os.path.basename(fpath)
            try:
                ok, msg = fut.result()
                if ok:
                    success_count += 1
                    print(f"[{idx}/{len(files)}] [OK] {msg}")
                else:
                    fail_count += 1
                    print(f"[{idx}/{len(files)}] [FAIL] {fname}: {msg}")
            except Exception as e:
                fail_count += 1
                print(f"[{idx}/{len(files)}] [ERROR] {fname}: {e}")

    elapsed = time.time() - t0
    print("\n" + "=" * 60)
    print(f"Completed in {elapsed:.1f} seconds.")
    print(f"Success: {success_count}/{len(files)} | Failed: {fail_count}")
    print("=" * 60)


if __name__ == "__main__":
    main()
