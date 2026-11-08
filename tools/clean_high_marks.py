"""
Clean up older-format conventional / subjective questions with marks > 2.0 (e.g. 4, 5, 8, 10 marks).
Updates all 103 paper JSON files in data/papers/ and any student attempt files in data/attempts/.
"""

import os
import glob
import json


def clean_papers(base_dir: str):
    papers_dir = os.path.join(base_dir, "data", "papers")
    json_files = sorted(glob.glob(os.path.join(papers_dir, "**", "*.json"), recursive=True))
    
    total_cleaned_papers = 0
    total_removed_questions = 0

    for fpath in json_files:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        dirty = False
        sections = data.get("sections", [])
        new_sections = []
        global_q_counter = 1

        for sec in sections:
            old_qs = sec.get("questions", [])
            kept_qs = []
            for q in old_qs:
                pos_m = float(q.get("positiveMarks", q.get("positive marks", 1.0)))
                if pos_m <= 2.0:
                    # Renumber sequentially
                    q["questionNumber"] = global_q_counter
                    q["questionId"] = global_q_counter
                    kept_qs.append(q)
                    global_q_counter += 1
                else:
                    dirty = True
                    total_removed_questions += 1

            sec["questions"] = kept_qs
            sec["totalQuestions"] = len(kept_qs)
            new_sections.append(sec)

        if dirty:
            data["sections"] = new_sections
            total_qs = sum(len(s["questions"]) for s in new_sections)
            new_total_marks = round(sum(float(q.get("positiveMarks", 1.0)) for s in new_sections for q in s["questions"]), 2)
            data["totalMarks"] = new_total_marks

            if data.get("category") == "Topic-wise":
                data["durationMinutes"] = max(30, min(180, total_qs * 3))

            if "totalQuestions" in data:
                data["totalQuestions"] = total_qs

            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            total_cleaned_papers += 1
            print(f"[CLEANED] {os.path.basename(fpath)}: remaining {total_qs} questions, totalMarks: {new_total_marks}")

    print(f"\nPapers cleanup complete: {total_cleaned_papers} papers updated, {total_removed_questions} >2-mark questions removed.")


def clean_attempt_file(attempt_path: str):
    if not os.path.exists(attempt_path):
        print(f"Attempt file {attempt_path} not found.")
        return

    with open(attempt_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    evals = data.get("evaluations", [])
    kept_evals = []
    global_q = 1

    for ev in evals:
        max_m = float(ev.get("maxMarks", 1.0))
        if max_m <= 2.0:
            ev["questionNumber"] = global_q
            ev["questionId"] = global_q
            kept_evals.append(ev)
            global_q += 1

    removed_cnt = len(evals) - len(kept_evals)
    total_q = len(kept_evals)
    total_marks = round(sum(float(ev.get("maxMarks", 1.0)) for ev in kept_evals), 2)
    score_obtained = round(sum(float(ev.get("marksAwarded", 0.0)) for ev in kept_evals), 2)
    pos_marks = round(sum(float(ev.get("marksAwarded", 0.0)) for ev in kept_evals if float(ev.get("marksAwarded", 0.0)) > 0), 2)
    neg_marks = round(sum(float(ev.get("penalty", 0.0)) for ev in kept_evals), 2)
    attempted = sum(1 for ev in kept_evals if ev.get("isAttempted"))
    correct = sum(1 for ev in kept_evals if ev.get("isCorrect"))
    incorrect = sum(1 for ev in kept_evals if ev.get("isAttempted") and not ev.get("isCorrect"))
    unattempted = total_q - attempted
    acc = round((correct / attempted * 100.0), 2) if attempted > 0 else 0.0
    pct = round((score_obtained / total_marks * 100.0), 2) if total_marks > 0 else 0.0

    data["evaluations"] = kept_evals
    data["totalQuestions"] = total_q
    data["totalMarks"] = total_marks
    data["scoreObtained"] = score_obtained
    data["positiveMarks"] = pos_marks
    data["negativeMarks"] = neg_marks
    data["attemptedCount"] = attempted
    data["correctCount"] = correct
    data["incorrectCount"] = incorrect
    data["unattemptedCount"] = unattempted
    data["accuracyPercentage"] = acc
    data["percentageScore"] = pct

    # Update sectionScores
    sec_scores = {}
    for sec_name in set(ev.get("sectionName", "General") for ev in kept_evals):
        s_evals = [ev for ev in kept_evals if ev.get("sectionName") == sec_name]
        s_tot_q = len(s_evals)
        s_att = sum(1 for ev in s_evals if ev.get("isAttempted"))
        s_cor = sum(1 for ev in s_evals if ev.get("isCorrect"))
        s_inc = sum(1 for ev in s_evals if ev.get("isAttempted") and not ev.get("isCorrect"))
        s_sc = round(sum(float(ev.get("marksAwarded", 0.0)) for ev in s_evals), 2)
        s_mm = round(sum(float(ev.get("maxMarks", 1.0)) for ev in s_evals), 2)
        sec_scores[sec_name] = {
            "total_questions": s_tot_q,
            "attempted": s_att,
            "correct": s_cor,
            "incorrect": s_inc,
            "score": s_sc,
            "max_marks": s_mm
        }
    data["sectionScores"] = sec_scores

    with open(attempt_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n[UPDATED ATTEMPT] {os.path.basename(attempt_path)}")
    print(f"  Removed {removed_cnt} conventional questions")
    print(f"  totalQuestions: {total_q}")
    print(f"  totalMarks: {total_marks}")
    print(f"  scoreObtained: {score_obtained}")
    print(f"  percentageScore: {pct}% (was 37.29%)")
    print(f"  accuracyPercentage: {acc}%")


def clean_all_attempts(base_dir: str):
    attempts_dir = os.path.join(base_dir, "data", "attempts")
    json_files = glob.glob(os.path.join(attempts_dir, "*.json"))
    for fpath in json_files:
        clean_attempt_file(fpath)


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"Base Directory: {base_dir}")
    clean_papers(base_dir)
    clean_all_attempts(base_dir)
