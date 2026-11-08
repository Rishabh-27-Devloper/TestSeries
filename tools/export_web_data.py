"""
Export data for the React web application:
- Copies 103 paper JSON files to web/public/data/papers/
- Generates web/public/data/papers_index.json (lightweight manifest for fast loading)
- Copies sample attempts to web/public/data/attempts/
- Copies UI icons to web/public/assets/
"""

import os
import glob
import json
import shutil
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_PAPERS = os.path.join(BASE_DIR, "data", "papers")
SRC_ATTEMPTS = os.path.join(BASE_DIR, "data", "attempts")
SRC_ASSETS = os.path.join(BASE_DIR, "assets")

WEB_PUBLIC = os.path.join(BASE_DIR, "web", "public")
DEST_PAPERS = os.path.join(WEB_PUBLIC, "data", "papers")
DEST_ATTEMPTS = os.path.join(WEB_PUBLIC, "data", "attempts")
DEST_ASSETS = os.path.join(WEB_PUBLIC, "assets")


def export_data():
    os.makedirs(DEST_PAPERS, exist_ok=True)
    os.makedirs(DEST_ATTEMPTS, exist_ok=True)
    os.makedirs(DEST_ASSETS, exist_ok=True)

    # 1. Copy UI assets
    for chk in ["checkbox_checked.png", "checkbox_unchecked.png"]:
        src_chk = os.path.join(SRC_ASSETS, chk)
        if os.path.exists(src_chk):
            shutil.copy2(src_chk, os.path.join(DEST_ASSETS, chk))

    # 2. Process all papers
    paper_files = sorted(glob.glob(os.path.join(SRC_PAPERS, "**", "*.json"), recursive=True))
    print(f"Processing {len(paper_files)} exam papers...")

    index_entries = []

    for fpath in paper_files:
        rel_path = os.path.relpath(fpath, SRC_PAPERS).replace("\\", "/")
        dest_fpath = os.path.join(DEST_PAPERS, rel_path)
        os.makedirs(os.path.dirname(dest_fpath), exist_ok=True)

        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Standardize question imageUrl for web
        # Web app can serve images or fallback to GitHub raw repository
        for sec in data.get("sections", []):
            for q in sec.get("questions", []):
                img = q.get("imageUrl")
                if img:
                    img_clean = img.replace("\\", "/")
                    if "data/papers/" in img_clean:
                        q["imageUrl"] = img_clean[img_clean.index("data/papers/"):]
                    elif img_clean.startswith("assets/"):
                        # E.g. assets/gate_ec_2024/...
                        parent_dir = os.path.basename(os.path.dirname(fpath))
                        q["imageUrl"] = f"data/papers/{parent_dir}/{img_clean}"

        with open(dest_fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Extract subject and chapter
        title = data.get("title", "")
        category = data.get("category", "Mock Paper")
        chapter = "Full Length"
        subject = "Electronics & Communication"

        if "topic" in category.lower():
            m = re.search(r'GATE EC - (.+?)(?: \((.+?)\))?$', title)
            if m:
                chapter = m.group(1).strip()
                if m.group(2):
                    subject = m.group(2).strip()

        total_q = sum(len(s.get("questions", [])) for s in data.get("sections", []))

        index_entries.append({
            "paperId": data.get("paperId", os.path.splitext(os.path.basename(fpath))[0]),
            "title": title,
            "category": category,
            "year": data.get("year"),
            "examType": data.get("examType", "GATE"),
            "durationMinutes": int(data.get("durationMinutes", 180)),
            "totalMarks": float(data.get("totalMarks", 100)),
            "totalQuestions": total_q,
            "chapter": chapter,
            "subject": subject,
            "sectionsCount": len(data.get("sections", [])),
            "description": data.get("description", ""),
            "jsonPath": f"data/papers/{rel_path}"
        })

    # Sort index: Full Length by year desc, Topic-wise by title asc
    full_length = [p for p in index_entries if "topic" not in p["category"].lower()]
    topic_wise = [p for p in index_entries if "topic" in p["category"].lower()]
    full_length.sort(key=lambda p: (p.get("year") or 0), reverse=True)
    topic_wise.sort(key=lambda p: p["title"])
    sorted_index = full_length + topic_wise

    index_out = os.path.join(WEB_PUBLIC, "data", "papers_index.json")
    with open(index_out, "w", encoding="utf-8") as f:
        json.dump(sorted_index, f, indent=2, ensure_ascii=False)
    print(f"Generated {index_out} with {len(sorted_index)} papers.")

    # 3. Copy sample attempts
    attempt_files = glob.glob(os.path.join(SRC_ATTEMPTS, "*.json"))
    attempts_list = []
    for af in attempt_files:
        dest_af = os.path.join(DEST_ATTEMPTS, os.path.basename(af))
        shutil.copy2(af, dest_af)
        with open(af, "r", encoding="utf-8") as f:
            att_data = json.load(f)
            att_data["_filePath"] = f"data/attempts/{os.path.basename(af)}"
            attempts_list.append(att_data)

    attempts_manifest = os.path.join(WEB_PUBLIC, "data", "attempts_manifest.json")
    with open(attempts_manifest, "w", encoding="utf-8") as f:
        json.dump(attempts_list, f, indent=2, ensure_ascii=False)
    print(f"Exported {len(attempts_list)} attempts.")


if __name__ == "__main__":
    export_data()
