"""
Tools: Topic-wise ExamGOAL PDF Parser for GATE EC.
Parses all 72 chapter-wise PYQ PDFs in assets/EC_Topicwise/ into:
  - JSON exam papers in data/papers/gate_ec_topicwise/{paper_id}.json
  - Whole-question 160 DPI image slices in data/papers/gate_ec_topicwise/assets/{paper_id}/q{q_num}_slice.png
"""

import os
import re
import sys
import json
import glob
from typing import List, Dict, Any, Optional, Tuple
import pymupdf
from PIL import Image
import io


def clean_slug(text: str) -> str:
    """Converts a title to a clean snake_case identifier."""
    cleaned = re.sub(r'[^a-zA-Z0-9]+', '_', text.strip()).strip('_').lower()
    return cleaned


def parse_answer_key_page(doc: pymupdf.Document, first_ak_page: int) -> Dict[int, Dict[str, Any]]:
    """
    Parses the Answer Key section from first_ak_page to len(doc) - 2.
    Returns mapping: q_num -> {
       'raw': str,
       'type': 'MCQ' | 'MSQ' | 'NAT',
       'correct_answer': Any,
       'tolerance_min': Optional[float],
       'tolerance_max': Optional[float],
       'positive_marks': float,
       'negative_marks': float
    }
    """
    ak_text_lines = []
    for pno in range(first_ak_page, len(doc) - 1):
        txt = doc[pno].get_text()
        for line in txt.splitlines():
            s = line.strip()
            if s:
                ak_text_lines.append(s)

    answers: Dict[int, Dict[str, Any]] = {}
    current_marks = 1.0
    i = 0
    n = len(ak_text_lines)

    while i < n:
        line = ak_text_lines[i]
        
        # Check marks section header
        m_marks = re.match(r'^Marks\s+(\d+)', line, re.IGNORECASE)
        if m_marks:
            current_marks = float(m_marks.group(1))
            i += 1
            continue

        # Stop at disclaimer footer
        if line.startswith("For numerical answers") or line.startswith("Keep practising"):
            i += 1
            continue

        # Check question answer entry: e.g. "1. B" or "1."
        m_q = re.match(r'^(\d+)\.\s*(.*)', line)
        if m_q:
            q_num = int(m_q.group(1))
            ans_raw = m_q.group(2).strip()
            
            # If answer is on subsequent line(s)
            extra_lines = []
            j = i + 1
            while j < n:
                next_line = ak_text_lines[j]
                if re.match(r'^Marks\s+\d+', next_line, re.IGNORECASE):
                    break
                if re.match(r'^\d+\.', next_line):
                    break
                if next_line.startswith("For numerical") or next_line.startswith("Keep practising") or next_line.startswith("ExamGOAL"):
                    break
                extra_lines.append(next_line)
                j += 1
            
            if not ans_raw and extra_lines:
                ans_raw = " ".join(extra_lines).strip()
            elif extra_lines and not re.match(r'^[A-D]$', ans_raw):
                ans_raw = (ans_raw + " " + " ".join(extra_lines)).strip()
            
            i = j
            
            # Parse type and details
            q_type = "MCQ"
            correct_ans = ans_raw
            tol_min = None
            tol_max = None
            pos_marks = current_marks if current_marks > 0 else 1.0
            neg_marks = 0.0

            clean_ans = ans_raw.strip().strip("()")
            
            # 1. MSQ check: Multiple comma/space separated single capital letters (e.g. "A, B", "A, C, D")
            m_msq = re.match(r'^([A-D])(?:\s*,\s*([A-D]))+$', clean_ans)
            if m_msq or ("," in clean_ans and all(part.strip() in ("A", "B", "C", "D") for part in clean_ans.split(",") if part.strip())):
                q_type = "MSQ"
                letters = [part.strip() for part in clean_ans.split(",") if part.strip()]
                correct_ans = letters
                neg_marks = 0.0

            # 2. MCQ check: Single letter A, B, C, D
            elif clean_ans in ("A", "B", "C", "D") or re.match(r'^[a-d]$', clean_ans, re.IGNORECASE):
                q_type = "MCQ"
                correct_ans = clean_ans.upper()
                neg_marks = round(pos_marks / 3.0, 2)

            # 3. NAT range check: e.g. "(5) (4.90 to 5.10)" or "30.5 to 30.8" or "0.24 to 0.25"
            elif " to " in clean_ans:
                q_type = "NAT"
                m_range = re.findall(r'[-+]?\d*\.?\d+', clean_ans)
                if len(m_range) >= 2:
                    val1 = float(m_range[-2])
                    val2 = float(m_range[-1])
                    tol_min = min(val1, val2)
                    tol_max = max(val1, val2)
                    correct_ans = round((tol_min + tol_max) / 2.0, 4)
                else:
                    correct_ans = 0.0
                    tol_min = 0.0
                    tol_max = 0.0
                neg_marks = 0.0

            # 4. NAT single numeric check: e.g. "5.65", "-0.5", "2047", "1.59 Hz"
            else:
                m_num = re.findall(r'[-+]?\d*\.?\d+', clean_ans)
                if m_num:
                    q_type = "NAT"
                    num_val = float(m_num[0])
                    correct_ans = num_val
                    tol_min = round(num_val - 0.01, 4)
                    tol_max = round(num_val + 0.01, 4)
                    neg_marks = 0.0
                else:
                    # Descriptive / unparsed
                    q_type = "MCQ"
                    correct_ans = clean_ans[:10] if clean_ans else "A"
                    neg_marks = 0.0

            answers[q_num] = {
                'raw': ans_raw,
                'type': q_type,
                'correct_answer': correct_ans,
                'tolerance_min': tol_min,
                'tolerance_max': tol_max,
                'positive_marks': pos_marks,
                'negative_marks': neg_marks
            }
        else:
            i += 1

    return answers


def extract_questions_and_slices(
    doc: pymupdf.Document,
    first_ak_page: int,
    paper_id: str,
    output_assets_dir: str
) -> List[Dict[str, Any]]:
    """
    Locates each Q{k}. across question pages (1 to first_ak_page - 1).
    Renders 160 DPI whole-question image slices without any answer leaks.
    Stitches multi-page questions vertically.
    """
    os.makedirs(output_assets_dir, exist_ok=True)
    
    # 1. Collect all question header locations: (q_num, pno, y0, origin_str)
    q_locs = []
    
    for pno in range(1, first_ak_page):
        page = doc[pno]
        blocks = page.get_text("blocks")
        for b in blocks:
            # b: (x0, y0, x1, y1, text, block_no, block_type)
            text = b[4].strip()
            # Match "Q1." or "Q1.\nGATE ECE 2016"
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            if not lines:
                continue
            m = re.match(r'^Q(\d+)\.', lines[0])
            if m:
                q_num = int(m.group(1))
                origin = lines[1] if len(lines) > 1 else ""
                q_locs.append({
                    'q_num': q_num,
                    'pno': pno,
                    'y0': b[1],
                    'origin': origin
                })
    
    # Sort by question number
    q_locs.sort(key=lambda x: x['q_num'])
    
    # Build per-page question list
    page_q_map: Dict[int, List[Dict[str, Any]]] = {}
    for q in q_locs:
        page_q_map.setdefault(q['pno'], []).append(q)
    for pno in page_q_map:
        page_q_map[pno].sort(key=lambda x: x['y0'])

    questions_data = []
    zoom = 160.0 / 72.0
    mat = pymupdf.Matrix(zoom, zoom)

    for idx, q_info in enumerate(q_locs):
        q_num = q_info['q_num']
        pno = q_info['pno']
        page = doc[pno]
        pw = page.rect.width
        ph = page.rect.height
        
        # Calculate vertical bounds for this question on page pno
        y0 = max(65.0, q_info['y0'] - 5.0)
        
        # Check if there is a next question on the same page
        page_qs = page_q_map[pno]
        curr_idx = page_qs.index(q_info)
        
        slices_to_stitch = []

        if curr_idx + 1 < len(page_qs):
            # Next question is on the same page
            next_q = page_qs[curr_idx + 1]
            y1 = max(y0 + 35.0, next_q['y0'] - 6.0)
            rect = pymupdf.Rect(25.0, y0, pw - 25.0, y1)
            pix = page.get_pixmap(matrix=mat, clip=rect)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            slices_to_stitch.append(img)
        else:
            # Last question on this page: slice down to bottom banner
            y1 = ph - 72.0
            rect = pymupdf.Rect(25.0, y0, pw - 25.0, y1)
            pix = page.get_pixmap(matrix=mat, clip=rect)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            slices_to_stitch.append(img)

            # Check if question continues on subsequent page(s)
            next_pno = pno + 1
            if next_pno < first_ak_page:
                next_page_qs = page_q_map.get(next_pno, [])
                if not next_page_qs:
                    # Next page has NO new questions -> entire page is continuation
                    p_next = doc[next_pno]
                    rect_cont = pymupdf.Rect(25.0, 65.0, p_next.rect.width - 25.0, p_next.rect.height - 72.0)
                    pix_c = p_next.get_pixmap(matrix=mat, clip=rect_cont)
                    slices_to_stitch.append(Image.open(io.BytesIO(pix_c.tobytes("png"))))
                elif next_page_qs[0]['y0'] > 135.0:
                    # First question on next page starts lower down -> top part is continuation
                    p_next = doc[next_pno]
                    y1_cont = next_page_qs[0]['y0'] - 6.0
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
            'q_num': q_num,
            'origin': q_info['origin'],
            'image_rel_url': f"assets/{paper_id}/{img_filename}",
            'image_full_path': img_full_path
        })

    return questions_data


def parse_topicwise_pdf(
    pdf_path: str,
    output_json_dir: str,
    output_base_assets_dir: str
) -> Tuple[bool, str]:
    """
    Parses a single topic-wise PDF into a complete ExamPaper JSON and image slices.
    """
    fname = os.path.basename(pdf_path)
    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:
        return False, f"Failed to open PDF {fname}: {e}"

    # Extract subject & topic
    p0_text = doc[0].get_text()
    
    # Topic from filename
    topic = fname.replace("GATE ECE ", "").replace(" Previous Year Questions with Answer Key", "").replace(".pdf", "").strip()
    
    # Subject from page 0
    m_sub = re.search(r'GATE ECE\s*[\u2022\-\.\*\ufffd]\s*([A-Z\s]+?)\s*[\u2022\-\.\*\ufffd]\s*CHAPTER-WISE PYQS', p0_text, re.IGNORECASE)
    if m_sub:
        subject = m_sub.group(1).strip()
    else:
        # Fallback keyword matching
        t_low = topic.lower()
        if any(k in t_low for k in ["calculus", "differential", "complex variable", "linear algebra", "numerical methods", "probability", "vector"]):
            subject = "ENGINEERING MATHEMATICS"
        elif any(k in t_low for k in ["verbal", "numerical ability", "logical"]):
            subject = "GENERAL APTITUDE"
        elif any(k in t_low for k in ["control", "compensators", "root locus", "stability", "state space", "time response", "frequency response"]):
            subject = "CONTROL SYSTEMS"
        elif any(k in t_low for k in ["diode", "bjt", "fet", "pn junction", "semiconductor", "ic basics"]):
            subject = "ELECTRONIC DEVICES"
        elif any(k in t_low for k in ["555 timer", "opamp", "operational", "amplifier", "feedback", "oscillator", "power amplifier"]):
            subject = "ANALOG CIRCUITS"
        elif any(k in t_low for k in ["boolean", "combinational", "sequential", "logic", "number system", "semiconductor memories", "8085", "converter"]):
            subject = "DIGITAL CIRCUITS"
        elif any(k in t_low for k in ["network", "sinusoidal", "transient", "two port", "graph"]):
            subject = "NETWORKS"
        elif any(k in t_low for k in ["communication", "information theory", "noise", "sampling"]):
            subject = "COMMUNICATIONS"
        elif any(k in t_low for k in ["antenna", "maxwell", "transmission line", "wave", "waveguide"]):
            subject = "ELECTROMAGNETICS"
        elif any(k in t_low for k in ["signal", "fourier", "laplace", "z transform"]):
            subject = "SIGNALS AND SYSTEMS"
        else:
            subject = "ELECTRONICS & COMMUNICATION"

    slug = clean_slug(topic)
    paper_id = f"gate_ec_topicwise_{slug}"
    paper_assets_dir = os.path.join(output_base_assets_dir, paper_id)

    # Find first answer key page
    first_ak_page = None
    for pno in range(len(doc) - 1, 0, -1):
        if "Answer Key" in doc[pno].get_text():
            first_ak_page = pno

    if first_ak_page is None:
        return False, f"No Answer Key found in {fname}"

    # Parse answer key
    answers_dict = parse_answer_key_page(doc, first_ak_page)

    # Extract questions and render slices
    questions_info = extract_questions_and_slices(doc, first_ak_page, paper_id, paper_assets_dir)

    if not questions_info:
        return False, f"0 questions extracted from {fname}"

    # Assemble questions
    q_objects = []
    total_marks = 0.0

    for q_meta in questions_info:
        q_num = q_meta['q_num']
        ak_data = answers_dict.get(q_num, {
            'type': 'MCQ',
            'correct_answer': 'A',
            'tolerance_min': None,
            'tolerance_max': None,
            'positive_marks': 1.0,
            'negative_marks': 0.33
        })

        q_type = ak_data['type']
        pos_m = float(ak_data['positive_marks'])
        neg_m = float(ak_data['negative_marks'])

        # Skip older-format conventional / subjective questions (> 2.0 marks)
        if pos_m > 2.0:
            continue

        total_marks += pos_m
        sequential_num = len(q_objects) + 1

        # Build clean options
        options = []
        if q_type in ("MCQ", "MSQ"):
            options = [
                {"id": "A", "text": "Option (A)"},
                {"id": "B", "text": "Option (B)"},
                {"id": "C", "text": "Option (C)"},
                {"id": "D", "text": "Option (D)"}
            ]

        # Origin reference
        origin_str = q_meta['origin'] if q_meta['origin'] else f"GATE EC PYQ"
        title_text = f"{topic} - Question {sequential_num} ({origin_str})"

        q_entry = {
            "questionId": sequential_num,
            "questionNumber": sequential_num,
            "sectionId": "sec_topic",
            "sectionName": f"{topic} Questions",
            "type": q_type,
            "questionText": title_text,
            "imageUrl": q_meta['image_rel_url'],
            "positiveMarks": pos_m,
            "negativeMarks": neg_m,
            "correctAnswer": ak_data['correct_answer'],
            "toleranceMin": ak_data['tolerance_min'],
            "toleranceMax": ak_data['tolerance_max'],
            "options": options
        }
        q_objects.append(q_entry)

    # Duration: 3 mins per question, clamped between 30 and 180 mins
    duration_mins = max(30, min(180, len(q_objects) * 3))

    paper_json = {
        "paperId": paper_id,
        "title": f"GATE EC - {topic} ({subject.title()})",
        "examType": "GATE",
        "category": "Topic-wise",
        "year": None,
        "durationMinutes": duration_mins,
        "totalMarks": round(total_marks, 2),
        "description": f"Chapter-wise Previous Year Questions for {topic} in {subject.title()}.",
        "instructions": [
            "Total duration of this topic-wise examination is specified on the timer.",
            "The question palette on the right shows question status (Answered, Not Answered, Marked for Review).",
            "Each question has whole-question graphics displaying problem statements, equations, and diagrams.",
            "Standard GATE marking scheme applies: negative marks for wrong MCQs, no negative marks for MSQ / NAT."
        ],
        "sections": [
            {
                "sectionId": "sec_topic",
                "sectionName": f"{topic} Questions",
                "totalQuestions": len(q_objects),
                "questions": q_objects
            }
        ]
    }

    out_json_path = os.path.join(output_json_dir, f"{paper_id}.json")
    os.makedirs(output_json_dir, exist_ok=True)
    with open(out_json_path, "w", encoding="utf-8") as fp:
        json.dump(paper_json, fp, indent=2, ensure_ascii=False)

    return True, f"Successfully parsed {len(q_objects)} questions ({q_objects[0]['type']}) -> {paper_id}.json"


def _worker(args):
    pdf_path, output_json_dir, output_assets_dir = args
    return pdf_path, parse_topicwise_pdf(pdf_path, output_json_dir, output_assets_dir)


def main():
    import concurrent.futures
    import time

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf_dir = os.path.join(base_dir, "assets", "EC_Topicwise")
    output_json_dir = os.path.join(base_dir, "data", "papers", "gate_ec_topicwise")
    output_assets_dir = os.path.join(output_json_dir, "assets")

    pdf_files = sorted(glob.glob(os.path.join(pdf_dir, "*.pdf")))
    print(f"Found {len(pdf_files)} topic-wise PDFs to parse.")

    t0 = time.time()
    max_workers = min(8, os.cpu_count() or 4)
    print(f"Starting parallel processing with {max_workers} worker processes...")

    tasks = [(p, output_json_dir, output_assets_dir) for p in pdf_files]
    success_count = 0
    failed = []

    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_worker, t): t[0] for t in tasks}
        completed = 0
        for f in concurrent.futures.as_completed(futures):
            completed += 1
            pdf_path, (ok, msg) = f.result()
            fname = os.path.basename(pdf_path)
            if ok:
                success_count += 1
                print(f"[{completed:02d}/{len(pdf_files):02d}] [OK] {fname[:40]}: {msg}", flush=True)
            else:
                failed.append((fname, msg))
                print(f"[{completed:02d}/{len(pdf_files):02d}] [FAIL] {fname[:40]}: {msg}", flush=True)

    elapsed = time.time() - t0
    print("\n" + "=" * 70)
    print(f"Parsing complete in {elapsed:.1f}s: {success_count}/{len(pdf_files)} PDFs parsed successfully.")
    if failed:
        print(f"Failures ({len(failed)}):")
        for f_name, f_msg in failed:
            print(f"  - {f_name}: {f_msg}")
    print("=" * 70)


if __name__ == "__main__":
    main()

