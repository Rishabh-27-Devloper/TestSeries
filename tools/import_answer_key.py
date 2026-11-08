"""
Answer Key Import Utility for GATE Papers.
Allows updating correct answers, NAT tolerance ranges, and solutions
for any JSON exam paper.

Usage:
  python tools/import_answer_key.py --paper gate_ec_2024 --keyfile answers.txt
  OR directly in Python by providing a dictionary.
"""

import os
import sys
import json
import argparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPERS_DIR = os.path.join(BASE_DIR, "data", "papers")


def update_paper_answers(paper_filename, answers_dict, solutions_dict=None):
    """
    Updates a paper's questions with correct answers and explanations.
    answers_dict format:
      {
        1: "A",
        2: "B",
        15: {"min": 2.8, "max": 2.85},   # or 2.82 or "2.80 to 2.85"
        16: ["A", "C"]                   # for MSQ
      }
    """
    # Find the paper file
    target_path = None
    for root, dirs, files in os.walk(PAPERS_DIR):
        for f in files:
            if f.lower() == paper_filename.lower() or f.lower() == f"{paper_filename.lower()}.json":
                target_path = os.path.join(root, f)
                break
        if target_path:
            break
            
    if not target_path:
        print(f"Error: Paper file '{paper_filename}' not found in {PAPERS_DIR}")
        return False
        
    with open(target_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    updated_count = 0
    for sec in data.get("sections", []):
        for q in sec.get("questions", []):
            qid = q.get("questionId")
            if qid in answers_dict or str(qid) in answers_dict:
                ans = answers_dict.get(qid) or answers_dict.get(str(qid))
                
                # Check format
                if isinstance(ans, dict) and ("min" in ans or "max" in ans):
                    q["toleranceMin"] = ans.get("min")
                    q["toleranceMax"] = ans.get("max")
                    q["correctAnswer"] = round((ans.get("min", 0) + ans.get("max", 0)) / 2.0, 3)
                elif isinstance(ans, str) and "to" in ans:
                    pts = ans.split("to")
                    try:
                        q["toleranceMin"] = float(pts[0].strip())
                        q["toleranceMax"] = float(pts[1].strip())
                        q["correctAnswer"] = round((q["toleranceMin"] + q["toleranceMax"]) / 2.0, 3)
                    except ValueError:
                        q["correctAnswer"] = ans
                else:
                    q["correctAnswer"] = ans
                    if q.get("type") == "NAT" and isinstance(ans, (int, float)):
                        q["toleranceMin"] = float(ans)
                        q["toleranceMax"] = float(ans)
                        
                if solutions_dict and (qid in solutions_dict or str(qid) in solutions_dict):
                    q["explanation"] = solutions_dict.get(qid) or solutions_dict.get(str(qid))
                    
                updated_count += 1
                
    data["answerKeyAvailable"] = True
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully updated {updated_count} questions in '{os.path.basename(target_path)}'.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import answer keys into GATE paper JSON files.")
    parser.add_argument("--paper", required=True, help="Paper JSON filename e.g. gate_ec_2024")
    parser.add_argument("--keyfile", required=False, help="Path to text or JSON file with question-to-answer mappings")
    args = parser.parse_args()
    
    if args.keyfile and os.path.exists(args.keyfile):
        with open(args.keyfile, "r", encoding="utf-8") as f:
            if args.keyfile.endswith(".json"):
                kdata = json.load(f)
            else:
                # Text format: 1: A, 2: B, etc.
                kdata = {}
                for line in f:
                    if ":" in line:
                        parts = line.strip().split(":", 1)
                        kdata[parts[0].strip()] = parts[1].strip()
        update_paper_answers(args.paper, kdata)
    else:
        print("Specify a valid --keyfile or import update_paper_answers() in Python.")
