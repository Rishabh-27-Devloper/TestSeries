"""
Comprehensive GATE EC Paper Parser and Sanitizer.
Extracts questions, text, diagrams, and official answer keys for digital & slice papers.
Ensures zero answer leaks, full margin preservation, and complete auto-grading support.
"""

import os
import sys
import re
import json
import pymupdf
import io
from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR = os.path.join(BASE_DIR, "assets", "EC")
OUTPUT_PAPERS_DIR = os.path.join(BASE_DIR, "data", "papers", "gate_ec")
ASSETS_DIR = os.path.join(OUTPUT_PAPERS_DIR, "assets")

os.makedirs(OUTPUT_PAPERS_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)


def parse_external_key_pdf(pdf_path: str) -> dict:
    """
    Parses any official GATE answer key PDF.
    Returns: {global_q_num: {'type': ..., 'key': ..., 'marks': ..., 'min': ..., 'max': ...}}
    """
    if not os.path.exists(pdf_path):
        return {}

    doc = pymupdf.open(pdf_path)
    text = ""
    for p in doc:
        text += p.get_text() + "\n"
    
    lines = [l.replace("\xa0", " ").strip() for p in doc for l in p.get_text().split("\n") if l.replace("\xa0", " ").strip()]
    key_dict = {}

    # Format: GATE 2013 (ORS code A)
    if "ORS code A" in text or "ORS Code A" in text:
        for i, l in enumerate(lines):
            if l == "EC" and i + 5 < len(lines) and lines[i+1].isdigit():
                q_num = int(lines[i+1])
                key_a = lines[i+2]
                key_dict[q_num] = {
                    "type": "MCQ",
                    "key": key_a,
                    "marks": 1.0 if (q_num <= 25 or 56 <= q_num <= 60) else 2.0
                }
        return _enrich_keys(key_dict)

    # Format: GATE 2012 (Question Booklet Code : A)
    if "Code : A" in text or "Code  :  A" in text or "Code : A" in text or "Code\xa0:\xa0A" in text:
        for i, l in enumerate(lines):
            if l == "EC" and i + 5 < len(lines) and lines[i+1].isdigit():
                q_num = int(lines[i+1])
                key_a = lines[i+2]
                key_dict[q_num] = {
                    "type": "MCQ",
                    "key": key_a,
                    "marks": 1.0 if (q_num <= 25 or 56 <= q_num <= 60) else 2.0
                }
        return _enrich_keys(key_dict)

    # Format: GATE 2014 Sessions (GA 1-10, EC 1-55)
    if "2014" in pdf_path:
        i = 0
        while i < len(lines):
            l = lines[i]
            if l in ("GA", "EC"):
                if i + 3 < len(lines) and lines[i+1].isdigit():
                    sec = l
                    q_sec = int(lines[i+1])
                    key_val = lines[i+2]
                    marks = float(lines[i+3]) if lines[i+3].replace(".", "", 1).isdigit() else (1.0 if q_sec <= 25 else 2.0)
                    global_q = q_sec if sec == "GA" else q_sec + 10
                    qtype = "NAT" if ("to" in key_val or re.match(r"^-?\d+(\.\d+)?$", key_val)) else "MCQ"
                    key_dict[global_q] = {
                        "type": qtype,
                        "key": key_val,
                        "marks": marks,
                        "sec": sec
                    }
                    i += 4
                    continue
            i += 1
        return _enrich_keys(key_dict)

    # Format: Modern TCS iON (2022 through 2026)
    for i, l in enumerate(lines):
        if l in ("GA", "EC"):
            sec = l
            q_num = None
            q_type = "MCQ"
            if i >= 3 and lines[i-1] in ("MCQ", "MSQ", "NAT") and lines[i-3].isdigit():
                q_num = int(lines[i-3])
                q_type = lines[i-1]
            elif i >= 2 and any(t in lines[i-1] for t in ["MCQ", "MSQ", "NAT"]) and lines[i-2].isdigit():
                q_num = int(lines[i-2])
                q_type = "MSQ" if "MSQ" in lines[i-1] else ("NAT" if "NAT" in lines[i-1] else "MCQ")
            
            if q_num is not None and 1 <= q_num <= 65:
                key_val = lines[i+1] if i + 1 < len(lines) else ""
                marks = 1.0
                if i + 2 < len(lines) and lines[i+2].replace(".", "", 1).isdigit():
                    marks = float(lines[i+2])
                key_dict[q_num] = {
                    "type": q_type,
                    "key": key_val,
                    "marks": marks,
                    "sec": sec
                }

    return _enrich_keys(key_dict)


def _enrich_keys(key_dict: dict) -> dict:
    """Computes tolerance ranges and parsed correct answers for NAT/MCQ/MSQ."""
    for q_num, info in key_dict.items():
        raw_k = str(info.get("key", "")).strip()
        q_type = info.get("type", "MCQ")
        
        info["correctAnswer"] = None
        info["toleranceMin"] = None
        info["toleranceMax"] = None
        
        if q_type == "MCQ":
            info["correctAnswer"] = raw_k.strip().upper()
        elif q_type == "MSQ":
            # Can be multiple like 'A,C' or 'A;D' or 'B,D'
            split_keys = [x.strip().upper() for x in re.split(r"[,;]", raw_k) if x.strip()]
            info["correctAnswer"] = sorted(split_keys) if split_keys else [raw_k.strip().upper()]
        elif q_type == "NAT":
            if "to" in raw_k:
                pts = raw_k.split("to")
                try:
                    t_min = float(pts[0].strip())
                    t_max = float(pts[1].strip())
                    info["toleranceMin"] = t_min
                    info["toleranceMax"] = t_max
                    info["correctAnswer"] = round((t_min + t_max) / 2.0, 3)
                except ValueError:
                    info["correctAnswer"] = raw_k
            else:
                try:
                    val = float(raw_k.strip())
                    info["toleranceMin"] = val
                    info["toleranceMax"] = val
                    info["correctAnswer"] = val
                except ValueError:
                    info["correctAnswer"] = raw_k
                    
    return key_dict


GATE_2015_EC_OFFICIAL_KEYS = {
    1: {"type": "MCQ", "key": "A", "marks": 1.0},
    2: {"type": "MCQ", "key": "A", "marks": 1.0},
    3: {"type": "MCQ", "key": "C", "marks": 1.0},
    4: {"type": "MCQ", "key": "C", "marks": 1.0},
    5: {"type": "MCQ", "key": "A", "marks": 1.0},
    6: {"type": "MCQ", "key": "A", "marks": 2.0},
    7: {"type": "MCQ", "key": "B", "marks": 2.0},
    8: {"type": "NAT", "key": "3", "marks": 2.0},
    9: {"type": "MCQ", "key": "C", "marks": 2.0},
    10: {"type": "MCQ", "key": "B", "marks": 2.0},
    11: {"type": "NAT", "key": "2", "marks": 1.0},
    12: {"type": "MCQ", "key": "B", "marks": 1.0},
    13: {"type": "MCQ", "key": "C", "marks": 1.0},
    14: {"type": "MCQ", "key": "D", "marks": 1.0},
    15: {"type": "NAT", "key": "16.5 to 17.5", "marks": 1.0},
    16: {"type": "NAT", "key": "24 to 26", "marks": 1.0},
    17: {"type": "NAT", "key": "99.5 to 100.5", "marks": 1.0},
    18: {"type": "MCQ", "key": "A", "marks": 1.0},
    19: {"type": "MCQ", "key": "A", "marks": 1.0},
    20: {"type": "NAT", "key": "0.50 to 0.54", "marks": 1.0},
    21: {"type": "MCQ", "key": "C", "marks": 1.0},
    22: {"type": "NAT", "key": "5", "marks": 1.0},
    23: {"type": "MCQ", "key": "C", "marks": 1.0},
    24: {"type": "MCQ", "key": "B", "marks": 1.0},
    25: {"type": "NAT", "key": "7", "marks": 1.0},
    26: {"type": "NAT", "key": "0.93 to 0.94", "marks": 1.0},
    27: {"type": "MCQ", "key": "D", "marks": 1.0},
    28: {"type": "NAT", "key": "2", "marks": 1.0},
    29: {"type": "MCQ", "key": "B", "marks": 1.0},
    30: {"type": "NAT", "key": "12", "marks": 1.0},
    31: {"type": "MCQ", "key": "A", "marks": 1.0},
    32: {"type": "MCQ", "key": "A", "marks": 1.0},
    33: {"type": "MCQ", "key": "C", "marks": 1.0},
    34: {"type": "MCQ", "key": "C", "marks": 2.0},
    35: {"type": "NAT", "key": "8.85 to 8.92", "marks": 2.0},
    36: {"type": "MCQ", "key": "B", "marks": 2.0},
    37: {"type": "MCQ", "key": "A", "marks": 2.0},
    38: {"type": "MCQ", "key": "B", "marks": 2.0},
    39: {"type": "NAT", "key": "0.95 to 1.05", "marks": 2.0},
    40: {"type": "MCQ", "key": "C", "marks": 2.0},
    41: {"type": "NAT", "key": "2.48 to 2.58", "marks": 2.0},
    42: {"type": "NAT", "key": "1.6 to 1.7", "marks": 2.0},
    43: {"type": "NAT", "key": "2.4 to 2.6", "marks": 2.0},
    44: {"type": "NAT", "key": "19 to 21", "marks": 2.0},
    45: {"type": "NAT", "key": "28 to 30", "marks": 2.0},
    46: {"type": "MCQ", "key": "A", "marks": 2.0},
    47: {"type": "NAT", "key": "40", "marks": 2.0},
    48: {"type": "MCQ", "key": "B", "marks": 2.0},
    49: {"type": "MCQ", "key": "A", "marks": 2.0},
    50: {"type": "NAT", "key": "249 to 251", "marks": 2.0},
    51: {"type": "MCQ", "key": "D", "marks": 2.0},
    52: {"type": "NAT", "key": "83.5 to 84.0", "marks": 2.0},
    53: {"type": "MCQ", "key": "C", "marks": 2.0},
    54: {"type": "MCQ", "key": "C", "marks": 2.0},
    55: {"type": "MCQ", "key": "A", "marks": 2.0},
    56: {"type": "NAT", "key": "25 to 26", "marks": 2.0},
    57: {"type": "NAT", "key": "0.5", "marks": 2.0},
    58: {"type": "MCQ", "key": "A", "marks": 2.0},
    59: {"type": "NAT", "key": "0.39 to 0.41", "marks": 2.0},
    60: {"type": "NAT", "key": "400", "marks": 2.0},
    61: {"type": "NAT", "key": "349 to 350", "marks": 2.0},
    62: {"type": "MCQ", "key": "D", "marks": 2.0},
    63: {"type": "MCQ", "key": "C", "marks": 2.0},
    64: {"type": "NAT", "key": "53 to 54", "marks": 2.0},
    65: {"type": "NAT", "key": "0.08 to 0.12", "marks": 2.0},
}


def parse_answer_key_table(doc, is_2020: bool = False) -> dict:
    """Parses embedded answer key tables from the back pages of question paper PDFs."""
    key_dict = {}
    full_text = ""
    for pno in range(max(0, len(doc) - 7), len(doc)):
        full_text += "\n" + doc[pno].get_text()

    lines = [l.strip() for l in full_text.split("\n") if l.strip()]
    for i, l in enumerate(lines):
        if l in ("GA", "EC", "EC-1", "EC-2", "EC-3", "EC-4") and i >= 2 and i + 2 < len(lines):
            sec_type = l
            que_type = lines[i-1] if lines[i-1] in ("MCQ", "NAT", "MSQ") else "MCQ"
            if is_2020:
                q_num_sec = int(lines[i-3]) if (i >= 3 and lines[i-3].isdigit()) else None
            else:
                q_num_sec = int(lines[i-2]) if (i >= 2 and lines[i-2].isdigit()) else None
                
            if q_num_sec is None:
                continue
            raw_key = lines[i+1]
            raw_marks = lines[i+2]
            try:
                marks = float(raw_marks)
            except ValueError:
                marks = 1.0
            
            if "GA" in sec_type:
                global_q = q_num_sec
            else:
                global_q = q_num_sec + 10 if q_num_sec <= 55 else q_num_sec
            key_dict[global_q] = {"type": que_type, "key": raw_key, "marks": marks}

    return _enrich_keys(key_dict)


def parse_slice_based_gate_paper(pdf_path: str, paper_id: str, year: int) -> str:
    """
    Parses TCS iON slice-based papers (2015, 2017_1, 2017_2, 2020).
    Features:
    1. Robust Regex matches Q.No. 1, Question Number : 1, Q.No 27 (without picking up instruction banners).
    2. Accurate section partitioning:
       - 2020: Pages 0-1 are GA (Q1-10), Pages 2-17 are EC (Q1-55 -> Global 11-65).
       - 2015 & 2017: Global Q1-65.
    3. Cross-Page Continuation Stitching (2015 & TCS iON):
       - Questions starting at bottom of page P (e.g. Q3, Q9, Q12, Q15, Q18, etc.) whose body/diagram
         continues onto page P+1 are sliced from both pages and seamlessly stitched vertically.
    4. Zero Answer Leaks:
       - Crops are strictly clamped above 'Options :' and 'Correct Answer\s*:'.
    5. Complete Answer Key Integration:
       - 2015: Uses official GATE 2015 EC key (MCQ keys + NAT exact ranges).
       - 2020: Parses Pages 18 & 19 (65 of 65 keys).
       - 2017 Set 2: Parses Pages 30 & 31 (65 of 65 keys).
       - 2017 Set 1: Extracts types from 'Wrong : 0' (NAT) vs 'Wrong : -0.33' (MCQ).
    """
    doc = pymupdf.open(pdf_path)
    paper_assets_dir = os.path.join(ASSETS_DIR, paper_id)
    os.makedirs(paper_assets_dir, exist_ok=True)
    
    is_2015 = ("2015" in paper_id)
    is_2020 = ("2020" in paper_id)
    is_2017_1 = ("2017_SET1" in paper_id)
    is_2017_2 = ("2017_SET2" in paper_id)

    # 1. Answer Keys
    if is_2015:
        answer_keys = _enrich_keys(dict(GATE_2015_EC_OFFICIAL_KEYS))
    elif is_2020:
        answer_keys = parse_answer_key_table(doc, is_2020=True)
    elif is_2017_2:
        answer_keys = parse_answer_key_table(doc, is_2020=False)
        ga_keys_2017 = {
            1: {"type": "MCQ", "key": "C", "marks": 1.0},
            2: {"type": "MCQ", "key": "A", "marks": 1.0},
            3: {"type": "MCQ", "key": "B", "marks": 1.0},
            4: {"type": "MCQ", "key": "A", "marks": 1.0},
            5: {"type": "MCQ", "key": "D", "marks": 1.0},
            6: {"type": "MCQ", "key": "A", "marks": 2.0},
            7: {"type": "MCQ", "key": "D", "marks": 2.0},
            8: {"type": "MCQ", "key": "C", "marks": 2.0},
            9: {"type": "MCQ", "key": "C", "marks": 2.0},
            10: {"type": "MCQ", "key": "B", "marks": 2.0},
        }
        answer_keys.update(_enrich_keys(ga_keys_2017))
    else:
        answer_keys = {}

    # 2. Extract Types and Slices
    questions_dict = {}
    regex = re.compile(r'(?:Question\s*Number|uestion\s*Number|Q\s*\.?\s*No\.?)\s*(?::|\.)?\s*(\d+)', re.IGNORECASE)

    max_pages = len(doc)
    if is_2015:
        max_pages = min(max_pages, 25)
    elif is_2020:
        max_pages = min(max_pages, 18)
    elif is_2017_2:
        max_pages = min(max_pages, 30)

    # Pre-map headers across pages
    page_q_map = {}
    for pno in range(max_pages):
        page = doc[pno]
        txt = page.get_text()
        offset = 0
        if is_2020:
            offset = 0 if pno <= 1 else 10

        headers = []
        for m in regex.finditer(txt):
            q_raw = int(m.group(1))
            gq = q_raw + offset
            matched = m.group(0)
            rects = page.search_for(matched)
            if rects:
                headers.append({"q_raw": q_raw, "global_q": gq, "rect": rects[0]})

        headers = sorted(headers, key=lambda x: x["rect"].y0)
        uniq = []
        seen = set()
        for h in headers:
            if h["global_q"] not in seen and 1 <= h["global_q"] <= 65:
                seen.add(h["global_q"])
                uniq.append(h)
        page_q_map[pno] = uniq

    for pno in range(max_pages):
        page = doc[pno]
        headers = page_q_map.get(pno, [])
        blocks = sorted(page.get_text("blocks"), key=lambda b: b[1])

        for idx, h in enumerate(headers):
            gq = h["global_q"]
            y0 = max(0, h["rect"].y0 - 5)

            has_next_q_on_page = (idx < len(headers) - 1)
            next_q_y0 = headers[idx + 1]["rect"].y0 - 5 if has_next_q_on_page else None

            # Find Options: or Correct Answer: between y0 and next question / bottom
            stop_y = next_q_y0 if next_q_y0 is not None else page.rect.height - 15
            found_stop = False
            for b in blocks:
                b_y0 = b[1]
                if y0 < b_y0 < stop_y:
                    btxt = b[4].strip()
                    if "Options :" in btxt or re.search(r'Correct\s*Answer\s*:', btxt, re.IGNORECASE):
                        stop_y = b_y0 - 2
                        found_stop = True
                        break

            # Handle cross-page continuation (2015, 2020, and other TCS iON formats)
            continues_next_page = (not has_next_q_on_page) and (pno + 1 < max_pages)
            if continues_next_page:
                next_headers = page_q_map.get(pno + 1, [])
                p2_first_y = next_headers[0]["rect"].y0 if next_headers else doc[pno + 1].rect.height
                if p2_first_y > 80 and (not found_stop or stop_y >= page.rect.height - 30):
                    # Part 1 on page pno
                    r1 = pymupdf.Rect(0, y0, page.rect.width, page.rect.height)
                    pix1 = page.get_pixmap(clip=r1, dpi=160)
                    im1 = Image.open(io.BytesIO(pix1.tobytes()))

                    # Part 2 on page pno + 1
                    next_page = doc[pno + 1]
                    next_blocks = sorted(next_page.get_text("blocks"), key=lambda b: b[1])
                    p2_stop = p2_first_y - 5
                    for b in next_blocks:
                        b_y0 = b[1]
                        if 0 <= b_y0 < p2_stop:
                            btxt = b[4].strip()
                            if "Options :" in btxt or re.search(r'Correct\s*Answer\s*:', btxt, re.IGNORECASE):
                                p2_stop = b_y0 - 2
                                break

                    r2 = pymupdf.Rect(0, 0, next_page.rect.width, max(20, p2_stop))
                    pix2 = next_page.get_pixmap(clip=r2, dpi=160)
                    im2 = Image.open(io.BytesIO(pix2.tobytes()))

                    stitched = Image.new("RGB", (max(im1.width, im2.width), im1.height + im2.height), (255, 255, 255))
                    stitched.paste(im1, (0, 0))
                    stitched.paste(im2, (0, im1.height))
                    out_img = stitched
                else:
                    r = pymupdf.Rect(0, y0, page.rect.width, max(y0 + 50, stop_y)) & page.rect
                    pix = page.get_pixmap(clip=r, dpi=160)
                    out_img = Image.open(io.BytesIO(pix.tobytes()))
            else:
                r = pymupdf.Rect(0, y0, page.rect.width, max(y0 + 50, stop_y)) & page.rect
                pix = page.get_pixmap(clip=r, dpi=160)
                out_img = Image.open(io.BytesIO(pix.tobytes()))

            img_filename = f"q{gq}_slice.png"
            out_img_path = os.path.join(paper_assets_dir, img_filename)
            out_img.save(out_img_path)

            # Metadata and typing
            sec_id = "GA" if gq <= 10 else "EC"
            sec_name = "General Aptitude" if gq <= 10 else "Electronics and Communication Engineering"
            pos_marks = 1.0 if (gq <= 5 or 11 <= gq <= 35) else 2.0
            neg_marks = round(pos_marks / 3.0, 2)

            q_type = "MCQ"
            corr_ans = None
            tol_min = None
            tol_max = None

            if gq in answer_keys:
                ak = answer_keys[gq]
                q_type = ak.get("type", "MCQ")
                pos_marks = ak.get("marks", pos_marks)
                corr_ans = ak.get("correctAnswer")
                tol_min = ak.get("toleranceMin")
                tol_max = ak.get("toleranceMax")
                neg_marks = round(pos_marks / 3.0, 2) if q_type == "MCQ" else 0.0
            elif is_2017_1:
                # Detect from header Wrong : 0 -> NAT
                txt_after = page.get_text()
                m_type = re.search(rf'(?:Q\s*\.?\s*No\.?|Q?uestion\s*Number)\s*:\s*{h["q_raw"]}.*?Wrong\s*:\s*(-?[\d\.]+)', txt_after)
                if m_type and float(m_type.group(1)) == 0.0:
                    q_type = "NAT"
                    neg_marks = 0.0

            options = []
            if q_type == "MCQ":
                for o in ["A", "B", "C", "D"]:
                    options.append({"id": o, "text": f"Option ({o}) - refer to question statement above"})
            elif q_type == "MSQ":
                for o in ["A", "B", "C", "D"]:
                    options.append({"id": o, "text": f"Option ({o})"})

            questions_dict[gq] = {
                "questionId": gq,
                "type": q_type,
                "sectionId": sec_id,
                "sectionName": sec_name,
                "questionText": f"GATE {year} EC - Question {gq} (Refer to the official question diagram below):",
                "positiveMarks": pos_marks,
                "negativeMarks": neg_marks,
                "imageUrl": f"assets/{paper_id}/{img_filename}",
                "options": options,
                "correctAnswer": corr_ans,
                "toleranceMin": tol_min,
                "toleranceMax": tol_max,
                "explanation": f"Official GATE {year} Electronics and Communication Engineering Question {gq}."
            }

    questions = []
    for gq in range(1, 66):
        if gq in questions_dict:
            questions.append(questions_dict[gq])
        else:
            sec_id = "GA" if gq <= 10 else "EC"
            sec_name = "General Aptitude" if gq <= 10 else "Electronics and Communication Engineering"
            pos_marks = 1.0 if (gq <= 5 or 11 <= gq <= 35) else 2.0
            neg_marks = round(pos_marks / 3.0, 2)
            ak = answer_keys.get(gq, {})
            questions.append({
                "questionId": gq,
                "type": ak.get("type", "MCQ"),
                "sectionId": sec_id,
                "sectionName": sec_name,
                "questionText": f"GATE {year} EC - Question {gq}:",
                "positiveMarks": pos_marks,
                "negativeMarks": neg_marks,
                "imageUrl": f"assets/{paper_id}/q{gq}_slice.png",
                "options": [{"id": o, "text": f"Option ({o})"} for o in ["A", "B", "C", "D"]],
                "correctAnswer": ak.get("correctAnswer"),
                "toleranceMin": ak.get("toleranceMin"),
                "toleranceMax": ak.get("toleranceMax"),
                "explanation": f"Official GATE {year} EC Question {gq}."
            })

    ga_questions = [q for q in questions if q["sectionId"] == "GA"]
    ec_questions = [q for q in questions if q["sectionId"] == "EC"]

    paper_json = {
        "paperId": paper_id,
        "title": f"GATE EC {year} Official Examination Paper",
        "examType": "GATE",
        "durationMinutes": 180,
        "totalMarks": 100,
        "category": "PYQ",
        "year": year,
        "description": f"Official GATE {year} Electronics and Communication Engineering (EC) examination paper with full question diagrams and official answers.",
        "answerKeyAvailable": any(q["correctAnswer"] is not None for q in questions),
        "sections": [
            {"sectionId": "GA", "sectionName": "General Aptitude", "questions": ga_questions},
            {"sectionId": "EC", "sectionName": "Electronics and Communication Engineering", "questions": ec_questions}
        ]
    }
    
    out_file = os.path.join(OUTPUT_PAPERS_DIR, f"{paper_id.lower()}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(paper_json, f, indent=2, ensure_ascii=False)
        
    print(f"Slice parser: {paper_id} ({year}) -> {len(questions)} questions. AnsKey: {paper_json['answerKeyAvailable']}")
    return out_file


def parse_modern_gate_paper(pdf_path: str, paper_id: str, year: int, key_pdf_path: str = None) -> str:
    """
    Parses digital text layer GATE papers (2012-2014, 2016, 2018, 2022-2026).
    Extracts high-resolution WHOLE question slices (question + equations + diagrams + options),
    links official answer keys, and creates clean CBT JSON papers.
    """
    doc = pymupdf.open(pdf_path)
    paper_assets_dir = os.path.join(ASSETS_DIR, paper_id)
    os.makedirs(paper_assets_dir, exist_ok=True)
    
    # Load answer key
    answer_keys = {}
    if key_pdf_path and os.path.exists(key_pdf_path):
        answer_keys = parse_external_key_pdf(key_pdf_path)
    if not answer_keys:
        answer_keys = parse_answer_key_table(doc)

    # Detect if two-section split (GA Q1-10 + Core EC Q1-55) or linear (Q1-65)
    ec_start_pno = None
    for pno in range(len(doc)):
        txt = doc[pno].get_text()
        if ("Q. 1 – Q. 25 carry one mark" in txt or "Q. 1 - Q. 25 carry one mark" in txt or "Q.1 - Q.25 carry one mark" in txt or "ELECTRONICS AND" in txt or "SET1            ELECTRONICS" in txt):
            ec_start_pno = pno
            break

    is_two_section_split = (ec_start_pno is not None and ec_start_pno > 0)
    questions = _slice_and_build_modern_questions(doc, is_two_section_split, ec_start_pno, year, paper_id, paper_assets_dir, answer_keys)

    ga_questions = [q for q in questions if q["sectionId"] == "GA"]
    ec_questions = [q for q in questions if q["sectionId"] == "EC"]

    paper_json = {
        "paperId": paper_id,
        "title": f"GATE EC {year} Official Examination Paper",
        "examType": "GATE",
        "durationMinutes": 180,
        "totalMarks": 100,
        "category": "PYQ",
        "year": year,
        "description": f"Official GATE {year} Electronics and Communication Engineering (EC) examination paper with General Aptitude and Core EC sections.",
        "answerKeyAvailable": any(q["correctAnswer"] is not None for q in questions),
        "sections": [
            {"sectionId": "GA", "sectionName": "General Aptitude", "questions": ga_questions},
            {"sectionId": "EC", "sectionName": "Electronics and Communication Engineering", "questions": ec_questions}
        ]
    }
    
    out_file = os.path.join(OUTPUT_PAPERS_DIR, f"{paper_id.lower()}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(paper_json, f, indent=2, ensure_ascii=False)
        
    slice_count = len([q for q in questions if q.get("imageUrl")])
    print(f"Modern whole-question parser: {paper_id} ({year}) -> {len(questions)} questions, {slice_count} slices. AnsKey: {paper_json['answerKeyAvailable']}")
    return out_file


def _slice_and_build_modern_questions(doc, is_two_section_split, ec_start_pno, year, paper_id, paper_assets_dir, answer_keys):
    """
    Slices the WHOLE question statement, diagrams, equations, and options directly as high-DPI images.
    Preserves all mathematical equations and circuit diagrams exactly as rendered in the official PDF.
    Zero raw equations in questionText.
    """
    questions = []
    page_headers = {}
    
    for pno in range(len(doc)):
        page = doc[pno]
        txt = page.get_text()
        if "Answer Key" in txt or "Key/Range" in txt:
            continue
        
        matches = list(re.finditer(r'Q\.\s*(\d+)\b', txt))
        p_headers = []
        for m in matches:
            local_q = int(m.group(1))
            rects = page.search_for(m.group(0))
            valid = [r for r in rects if r.x0 < 140]
            if not valid:
                continue
            r = valid[0]
            
            if is_two_section_split:
                if ec_start_pno is not None and pno < ec_start_pno:
                    if 1 <= local_q <= 10:
                        p_headers.append({"local_q": local_q, "global_q": local_q, "sec_id": "GA", "rect": r})
                else:
                    if 1 <= local_q <= 55:
                        p_headers.append({"local_q": local_q, "global_q": local_q + 10, "sec_id": "EC", "rect": r})
            else:
                if 1 <= local_q <= 65:
                    sec_id = "GA" if local_q <= 10 else "EC"
                    p_headers.append({"local_q": local_q, "global_q": local_q, "sec_id": sec_id, "rect": r})
                    
        p_headers = sorted(p_headers, key=lambda x: x["rect"].y0)
        uniq_p = []
        seen = set()
        for h in p_headers:
            if h["global_q"] not in seen:
                seen.add(h["global_q"])
                uniq_p.append(h)
        if uniq_p:
            page_headers[pno] = uniq_p

    global_map = {}
    for pno in sorted(page_headers.keys()):
        for h in page_headers[pno]:
            if h["global_q"] not in global_map:
                global_map[h["global_q"]] = (pno, h)

    for gq in range(1, 66):
        sec_id = "GA" if gq <= 10 else "EC"
        sec_name = "General Aptitude" if sec_id == "GA" else "Electronics and Communication Engineering"
        pos_marks = 1.0 if (gq <= 5 or (11 <= gq <= 35)) else 2.0
        
        ak = answer_keys.get(gq, {})
        q_type = ak.get("type", "MCQ")
        corr_ans = ak.get("correctAnswer")
        tol_min = ak.get("toleranceMin")
        tol_max = ak.get("toleranceMax")
        pos_marks = ak.get("marks", pos_marks)
        neg_marks = round(pos_marks / 3.0, 2) if q_type == "MCQ" else 0.0

        img_filename = f"q{gq}_slice.png"
        out_img_path = os.path.join(paper_assets_dir, img_filename)

        if gq in global_map:
            pno, h = global_map[gq]
            page = doc[pno]
            y0 = max(25, h["rect"].y0 - 6)

            same_page_next = [other for other in page_headers[pno] if other["rect"].y0 > h["rect"].y0 + 10]
            if same_page_next:
                y1 = max(y0 + 40, same_page_next[0]["rect"].y0 - 6)
            else:
                y1 = page.rect.height - 35
                for b in page.get_text("blocks"):
                    if b[1] > page.rect.height - 50 and ("Page " in b[4] or "Organizing" in b[4]):
                        y1 = min(y1, b[1] - 4)

            crop_rect = pymupdf.Rect(20, y0, page.rect.width - 20, y1) & page.rect
            pix = page.get_pixmap(clip=crop_rect, dpi=160)
            pix.save(out_img_path)
        else:
            target_pno = min(len(doc) - 1, max(0, gq - 1))
            page = doc[target_pno]
            crop_rect = pymupdf.Rect(20, 40, page.rect.width - 20, page.rect.height - 40)
            pix = page.get_pixmap(clip=crop_rect, dpi=160)
            pix.save(out_img_path)

        options = []
        if q_type in ("MCQ", "MSQ"):
            for o in ["A", "B", "C", "D"]:
                options.append({"id": o, "text": f"Option ({o})"})

        questions.append({
            "questionId": gq,
            "type": q_type,
            "sectionId": sec_id,
            "sectionName": sec_name,
            "questionText": f"GATE {year} EC - Question {gq}",
            "positiveMarks": pos_marks,
            "negativeMarks": neg_marks,
            "imageUrl": f"assets/{paper_id}/{img_filename}",
            "options": options,
            "correctAnswer": corr_ans,
            "toleranceMin": tol_min,
            "toleranceMax": tol_max,
            "explanation": f"Official GATE {year} EC Question {gq}."
        })

    return questions


def parse_all_digital_and_slice_papers():
    print("=== Processing Digital & Slice GATE EC Papers ===")
    
    # 1. Slice-based papers (with margin & leak fixes)
    slice_specs = [
        ("EC2020.pdf", "GATE_EC_2020", 2020),
        ("EC2017_2.pdf", "GATE_EC_2017_SET2", 2017),
        ("EC2017_1.pdf", "GATE_EC_2017_SET1", 2017),
        ("EC2015.pdf", "GATE_EC_2015", 2015),
    ]
    for fname, pid, yr in slice_specs:
        fpath = os.path.join(PDF_DIR, fname)
        if os.path.exists(fpath):
            parse_slice_based_gate_paper(fpath, pid, yr)
            
    # 2. Modern & Digital Papers with External / Embedded Keys
    modern_specs = [
        ("EC2026.pdf", "GATE_EC_2026", 2026, "EC_Keys_2026.pdf"),
        ("EC2025.pdf", "GATE_EC_2025", 2025, "2025_EC_Keys.pdf"),
        ("EC2024.pdf", "GATE_EC_2024", 2024, "ECKey_2024.pdf"),
        ("EC2023.pdf", "GATE_EC_2023", 2023, "EC_2023key.pdf"),
        ("EC2022.pdf", "GATE_EC_2022", 2022, "EC_2022key.pdf"),
        ("EC2018.pdf", "GATE_EC_2018", 2018, None),
        ("EC2016.pdf", "GATE_EC_2016", 2016, None),
        ("EC2014.pdf", "GATE_EC_2014_S1", 2014, "EC_2014key.pdf"),
        ("EC_2014_S2.pdf", "GATE_EC_2014_S2", 2014, "EC_2014_S2_key.pdf"),
        ("EC_2014_S3.pdf", "GATE_EC_2014_S3", 2014, "EC_2014_S3key.pdf"),
        ("EC_2014_S4.pdf", "GATE_EC_2014_S4", 2014, "EC_2014_S4key.pdf"),
        ("EC2013.pdf", "GATE_EC_2013", 2013, "EC_2013key.pdf"),
        ("EC2012.pdf", "GATE_EC_2012", 2012, "EC_2012key.pdf"),
    ]
    for fname, pid, yr, kfname in modern_specs:
        fpath = os.path.join(PDF_DIR, fname)
        kpath = os.path.join(PDF_DIR, kfname) if kfname else None
        if os.path.exists(fpath):
            parse_modern_gate_paper(fpath, pid, yr, kpath)


if __name__ == "__main__":
    parse_all_digital_and_slice_papers()
