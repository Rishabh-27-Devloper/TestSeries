"""
Tools: Practice Sheets PDF Parser for CBT Offline Simulator.
Extracts individual practice questions from 6 subject DPP PDFs in Downloads:
  1. Digital Electronics Practice Sheet.pdf
  2. Control System Practice Sheet.pdf
  3. Analog Electronics Practice Sheet.pdf
  4. Signal and System Practice Sheet.pdf
  5. Communication Systems Practice Sheet.pdf
  6. Networks Practice Sheet.pdf

Outputs:
  - Individual question JSONs in:
      data/practice/questions/<questionId>.json
      web/public/data/practice/questions/<questionId>.json
  - Question image slices in:
      data/practice/assets/<subject_slug>/<topic_slug>/q{num}.png
      web/public/data/practice/assets/<subject_slug>/<topic_slug>/q{num}.png
  - Unified practice index in:
      data/practice/practice_index.json
      web/public/data/practice/practice_index.json
"""

import os
import re
import json
import shutil
from typing import List, Dict, Any, Optional, Tuple
import pymupdf
from PIL import Image
import io


def clean_slug(text: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z0-9]+', '_', text.strip()).strip('_').lower()
    return cleaned or "default"


def parse_ak_page(text: str) -> Dict[int, str]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    ak = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^(\d+)\.\s*(.*)', line)
        if m:
            q_num = int(m.group(1))
            ans = m.group(2).strip()
            if not ans and i + 1 < len(lines):
                if not re.match(r'^\d+\.', lines[i+1]) and 'any issue' not in lines[i+1].lower() and 'for more' not in lines[i+1].lower():
                    ans = lines[i+1].strip()
                    i += 1
            # Clean ans
            ans_clean = ans.strip('() ')
            ak[q_num] = ans_clean
        i += 1
    return ak


def detect_dpps(doc: pymupdf.Document, subject_name: str) -> List[Dict[str, Any]]:
    """
    Detects all DPP units in a subject PDF.
    Returns list of dicts: { dpp_num, start_page, end_page, ak_page, chapter, topic }
    """
    dpps = []
    current_dpp = None

    for p_idx in range(len(doc)):
        page = doc[p_idx]
        text = page.get_text()
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        is_ak = bool(re.search(r'answer\s*key', text, re.I))
        is_p1 = False
        if lines and lines[0] in ['1', '01']:
            is_p1 = True
        elif any(re.search(r'practice\s*sheet\s*[-:]?\s*0?(\d+)', l, re.I) for l in lines[:10]):
            is_p1 = True
        elif any(re.search(r'chapter\s*:', l, re.I) for l in lines[:10]):
            is_p1 = True
        elif any(re.search(r'topic\s*:', l, re.I) for l in lines[:10]) and p_idx > 0 and (dpps and p_idx > dpps[-1]['end_page']):
            is_p1 = True

        if is_ak:
            if current_dpp:
                current_dpp['ak_page'] = p_idx
                current_dpp['end_page'] = p_idx
        elif is_p1 and (not current_dpp or p_idx > current_dpp['start_page']):
            if current_dpp and current_dpp['end_page'] is None:
                current_dpp['end_page'] = p_idx - 1

            top = ""
            chap = ""
            sheet_title = ""
            for l in lines[:15]:
                m_top = re.search(r'topic\s*[-:]\s*(.*)', l, re.I)
                if m_top:
                    top = m_top.group(1).strip()
                m_chap = re.search(r'chapter\s*[-:]\s*(.*)', l, re.I)
                if m_chap:
                    chap = m_chap.group(1).strip()
                m_sheet = re.search(r'(practice\s*sheet\s*[-:]?\s*\d+|dpp\s*[-:]?\s*\d+)', l, re.I)
                if m_sheet:
                    sheet_title = m_sheet.group(1).strip()

            if not top and not chap:
                cand_lines = [l for l in lines[1:8] if not any(x in l.lower() for x in [
                    'hinglish', 'batch', 'ee/ec', 'ec/in', 'ee, ec', 'mcq', 'msq', 'nat', 'easy', 'medium', 'hard', 'branch'
                ])]
                if cand_lines:
                    if len(cand_lines) > 1 and cand_lines[0].lower() in [subject_name.lower(), 'control system', 'signal and system', 'communications', 'network theory', 'analog electronics']:
                        top = cand_lines[1]
                    else:
                        top = cand_lines[0]

            dpp_num = len(dpps) + 1
            current_dpp = {
                'dpp_num': dpp_num,
                'start_page': p_idx,
                'end_page': None,
                'ak_page': None,
                'chapter': chap or subject_name,
                'topic': top or f"{subject_name} Practice Sheet {dpp_num:02d}",
                'sheet_title': sheet_title or f"DPP {dpp_num:02d}"
            }
            dpps.append(current_dpp)

    if current_dpp and current_dpp['end_page'] is None:
        current_dpp['end_page'] = len(doc) - 1

    return dpps


def parse_and_slice_dpp(
    doc: pymupdf.Document,
    subject_name: str,
    subject_slug: str,
    dpp: Dict[str, Any],
    data_dir: str,
    web_dir: str
) -> List[Dict[str, Any]]:
    """
    Parses questions and generates image slices for a single DPP.
    """
    start_page = dpp['start_page']
    end_page = dpp['end_page']
    ak_page = dpp['ak_page']
    topic_name = dpp['topic']
    chapter_name = dpp['chapter']
    dpp_num = dpp['dpp_num']
    topic_slug = f"dpp_{dpp_num:02d}_{clean_slug(topic_name)}"[:45]

    # Directories for assets
    assets_rel_path = f"assets/practice/{subject_slug}/{topic_slug}"
    fs_assets_dir = os.path.join(data_dir, "practice", assets_rel_path.replace("/", os.sep))
    web_assets_dir = os.path.join(web_dir, "data", "practice", assets_rel_path.replace("/", os.sep))
    os.makedirs(fs_assets_dir, exist_ok=True)
    os.makedirs(web_assets_dir, exist_ok=True)

    # Directories for question json files
    fs_questions_dir = os.path.join(data_dir, "practice", "questions")
    web_questions_dir = os.path.join(web_dir, "data", "practice", "questions")
    os.makedirs(fs_questions_dir, exist_ok=True)
    os.makedirs(web_questions_dir, exist_ok=True)

    # Parse answer key
    ak: Dict[int, str] = {}
    if ak_page is not None and ak_page < len(doc):
        ak = parse_ak_page(doc[ak_page].get_text())

    # Detect questions sequentially
    q_locs = []
    expected_q = 1

    for pno in range(start_page, end_page + 1):
        if pno == ak_page:
            continue
        page = doc[pno]
        y_top = 145.0 if pno == start_page else 55.0
        y_bot = page.rect.height - 65.0

        words = page.get_text("words")
        # Separate Left and Right columns
        left_words = [w for w in words if w[0] < 305 and w[1] >= y_top - 15 and w[3] <= y_bot + 15]
        right_words = [w for w in words if w[0] >= 305 and w[1] >= y_top - 15 and w[3] <= y_bot + 15]

        left_words.sort(key=lambda w: (w[1], w[0]))
        right_words.sort(key=lambda w: (w[1], w[0]))

        for col_name, col_words in [('L', left_words), ('R', right_words)]:
            for w in col_words:
                target_str = f"{expected_q}."
                if w[4] == target_str:
                    col_margin = 30.0 if col_name == 'L' else 310.0
                    if abs(w[0] - col_margin) < 55.0:
                        q_locs.append({
                            'q_num': expected_q,
                            'pno': pno,
                            'col': col_name,
                            'x0': col_margin,
                            'y0': w[1],
                            'y1': w[3]
                        })
                        expected_q += 1

    if not q_locs:
        # Fallback if strict sequence missed: try regex on blocks
        for pno in range(start_page, end_page + 1):
            if pno == ak_page:
                continue
            page = doc[pno]
            blocks = page.get_text("blocks")
            for b in blocks:
                txt = b[4].strip()
                m = re.match(r'^(?:\[(?:MCQ|MSQ|NAT)\]|(?:MCQ|MSQ|NAT)|(?:EASY|MEDIUM|HARD|BRAIN TEASER))?\s*(\d+)\.\s+', txt)
                if m:
                    qn = int(m.group(1))
                    col_name = 'L' if b[0] < 305 else 'R'
                    col_margin = 30.0 if col_name == 'L' else 310.0
                    q_locs.append({
                        'q_num': qn,
                        'pno': pno,
                        'col': col_name,
                        'x0': col_margin,
                        'y0': b[1],
                        'y1': b[3]
                    })
        # Remove duplicates
        seen = set()
        dedup = []
        for q in q_locs:
            if q['q_num'] not in seen:
                seen.add(q['q_num'])
                dedup.append(q)
        dedup.sort(key=lambda x: x['q_num'])
        q_locs = dedup

    mat = pymupdf.Matrix(2.0, 2.0)
    questions_list = []

    for idx, q in enumerate(q_locs):
        q_num = q['q_num']
        pno = q['pno']
        col = q['col']
        page = doc[pno]
        pw = page.rect.width
        ph = page.rect.height

        y_top = 145.0 if pno == start_page else 55.0
        y_bot = ph - 65.0
        x_left = 30.0 if col == 'L' else 310.0
        x_right = 300.0 if col == 'L' else 585.0

        y0 = max(y_top, q['y0'] - 4.0)

        # Check for common data header right above y0
        blocks = page.get_text("blocks")
        for b in blocks:
            if b[0] >= x_left - 10 and b[2] <= x_right + 10:
                if (y0 - b[3]) >= 0 and (y0 - b[3]) <= 50:
                    if re.search(r'common data|statement for', b[4], re.I):
                        y0 = max(y_top, b[1] - 4.0)

        # Determine y1 bound
        if idx + 1 < len(q_locs) and q_locs[idx+1]['pno'] == pno and q_locs[idx+1]['col'] == col:
            y1 = max(y0 + 20.0, q_locs[idx+1]['y0'] - 4.0)
        else:
            y1 = y_bot

        rect = pymupdf.Rect(x_left, y0, x_right, y1)
        pix = page.get_pixmap(matrix=mat, clip=rect)
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        # Save slice
        img_filename = f"q{q_num}.png"
        img_fs_path = os.path.join(fs_assets_dir, img_filename)
        img_web_path = os.path.join(web_assets_dir, img_filename)
        img.save(img_fs_path, "PNG", optimize=True)
        shutil.copyfile(img_fs_path, img_web_path)

        # Question text extraction
        q_text_raw = page.get_text("text", clip=rect).strip()
        lines = [l.strip() for l in q_text_raw.splitlines() if l.strip()]
        # Strip leading question number
        question_text = re.sub(r'^(?:\[(?:MCQ|MSQ|NAT)\]|(?:MCQ|MSQ|NAT)|(?:EASY|MEDIUM|HARD|BRAIN TEASER))?\s*\d+\.\s*', '', q_text_raw).strip()

        # Extract Options if available
        options = []
        for opt_id in ['(a)', '(b)', '(c)', '(d)', '(A)', '(B)', '(C)', '(D)']:
            m = re.search(rf'{re.escape(opt_id)}\s*([^\n\(\)]+)', q_text_raw)
            if m:
                clean_id = opt_id.strip('() ').upper()
                options.append({
                    'id': clean_id,
                    'text': m.group(1).strip()
                })

        # Answer & Type
        raw_ans = ak.get(q_num, "")
        q_type = "MCQ"
        correct_answer: Any = None
        tol_min = None
        tol_max = None

        if raw_ans:
            if "," in raw_ans:
                q_type = "MSQ"
                correct_answer = [x.strip().upper() for x in raw_ans.split(",")]
            elif re.match(r'^[a-dA-D]$', raw_ans):
                q_type = "MCQ"
                correct_answer = raw_ans.upper()
            elif re.match(r'^-?\d+(?:\.\d+)?$', raw_ans.replace('–', '-')):
                q_type = "NAT"
                val = float(raw_ans.replace('–', '-'))
                correct_answer = str(val if not val.is_integer() else int(val))
                tol_min = val - 0.05 if abs(val) < 1 else val * 0.99
                tol_max = val + 0.05 if abs(val) < 1 else val * 1.01
            else:
                correct_answer = raw_ans.upper()
        else:
            # When Answer Key was not provided in PDF (e.g. Analog / Comm)
            if len(options) >= 2:
                q_type = "MCQ"
            else:
                q_type = "NAT"

        # Determine Marks
        marks = 1
        if "hard" in q_text_raw.lower() or "brain teaser" in q_text_raw.lower() or q_type == "NAT":
            marks = 2
        elif q_num > 5:
            marks = 2

        question_id = f"PR_{subject_slug.upper()[:3]}_D{dpp_num:02d}_Q{q_num:02d}"

        q_obj = {
            'questionId': question_id,
            'subject': subject_name,
            'chapter': chapter_name,
            'topic': topic_name,
            'dppNumber': dpp_num,
            'questionNumber': q_num,
            'marks': marks,
            'type': q_type,
            'questionText': question_text or f"{subject_name} - {topic_name} - Question {q_num}",
            'imageUrl': f"{assets_rel_path}/{img_filename}",
            'options': options if options else None,
            'correctAnswer': correct_answer,
            'toleranceMin': tol_min,
            'toleranceMax': tol_max,
            'explanation': f"Practice Question from {subject_name} DPP-{dpp_num:02d} ({topic_name})."
        }

        # Save individual JSON
        json_fs_path = os.path.join(fs_questions_dir, f"{question_id}.json")
        json_web_path = os.path.join(web_questions_dir, f"{question_id}.json")
        with open(json_fs_path, 'w', encoding='utf-8') as f:
            json.dump(q_obj, f, indent=2)
        shutil.copyfile(json_fs_path, json_web_path)

        questions_list.append(q_obj)

    return questions_list


def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_dir = os.path.join(root_dir, "data")
    web_dir = os.path.join(root_dir, "web", "public")

    pdf_map = [
        ("Digital Electronics", "de", r"C:\Users\Anand Shukla\Downloads\Digital Electronics Practice Sheet.pdf"),
        ("Control System", "cs", r"C:\Users\Anand Shukla\Downloads\Control System Practice Sheet.pdf"),
        ("Signal and System", "ss", r"C:\Users\Anand Shukla\Downloads\Signal and System Practice Sheet.pdf"),
        ("Network Theory", "nt", r"C:\Users\Anand Shukla\Downloads\Networks Practice Sheet.pdf"),
        ("Analog Electronics", "ae", r"C:\Users\Anand Shukla\Downloads\Analog Electronics Practice Sheet.pdf"),
        ("Communication Systems", "comm", r"C:\Users\Anand Shukla\Downloads\Communication Systems Practice Sheet.pdf"),
    ]

    subjects_summary = []
    total_all_questions = 0

    print("=" * 70)
    print("STARTING PRACTICE SHEETS EXTRACTION PIPELINE")
    print("=" * 70)

    for subject_name, subject_slug, pdf_path in pdf_map:
        if not os.path.exists(pdf_path):
            print(f"Warning: File not found: {pdf_path}")
            continue

        doc = pymupdf.open(pdf_path)
        print(f"\nProcessing {subject_name} ({len(doc)} pages)...")
        dpps = detect_dpps(doc, subject_name)
        print(f"  Found {len(dpps)} DPP topics")

        subject_topics = []
        subject_q_count = 0

        for dpp in dpps:
            topic_name = dpp['topic']
            dpp_num = dpp['dpp_num']
            topic_id = f"{subject_slug}_dpp{dpp_num:02d}_{clean_slug(topic_name)}"[:50]

            qs = parse_and_slice_dpp(doc, subject_name, subject_slug, dpp, data_dir, web_dir)
            one_mark = sum(1 for q in qs if q['marks'] == 1)
            two_mark = sum(1 for q in qs if q['marks'] == 2)
            has_ak = bool(dpp['ak_page'] is not None)

            subject_topics.append({
                'topicId': topic_id,
                'topicName': topic_name,
                'chapter': dpp['chapter'],
                'subject': subject_name,
                'dppNumber': dpp_num,
                'questionCount': len(qs),
                'oneMarkCount': one_mark,
                'twoMarkCount': two_mark,
                'hasAnswerKey': has_ak,
                'questionIds': [q['questionId'] for q in qs]
            })

            subject_q_count += len(qs)
            total_all_questions += len(qs)

        subjects_summary.append({
            'subjectId': subject_slug,
            'subjectName': subject_name,
            'topicsCount': len(subject_topics),
            'totalQuestions': subject_q_count,
            'topics': subject_topics
        })

        print(f"  --> {subject_name} Complete: {len(subject_topics)} topics, {subject_q_count} questions sliced.")

    practice_index = {
        'totalSubjects': len(subjects_summary),
        'totalQuestions': total_all_questions,
        'subjects': subjects_summary
    }

    # Save index to both data/practice and web/public/data/practice
    idx_fs = os.path.join(data_dir, "practice", "practice_index.json")
    idx_web = os.path.join(web_dir, "data", "practice", "practice_index.json")
    os.makedirs(os.path.dirname(idx_fs), exist_ok=True)
    os.makedirs(os.path.dirname(idx_web), exist_ok=True)

    with open(idx_fs, 'w', encoding='utf-8') as f:
        json.dump(practice_index, f, indent=2)
    shutil.copyfile(idx_fs, idx_web)

    print("\n" + "=" * 70)
    print(f"EXTRACTION COMPLETE: {total_all_questions} Total Questions Processed across {len(subjects_summary)} Subjects!")
    print(f"Index written to {idx_fs} and {idx_web}")
    print("=" * 70)


if __name__ == "__main__":
    main()
