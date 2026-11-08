"""
Validation test suite for all parsed GATE EC JSON papers.
Checks schema compliance, storage loading, question counts, marks, and image path validity.
"""

import os
import glob
import json
import pytest
from core.storage import StorageManager
from core.models import ExamPaper, QuestionType


class TestEcPapersValidation:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.storage = StorageManager(self.base_dir)
        self.papers_dir = os.path.join(self.base_dir, "data", "papers", "gate_ec")

    def test_all_json_papers_parse_and_load(self):
        json_files = glob.glob(os.path.join(self.papers_dir, "*.json"))
        assert len(json_files) >= 16, f"Expected at least 16 papers, found {len(json_files)}"
        
        for file_path in json_files:
            paper = self.storage.load_paper_from_file(file_path)
            assert paper is not None, f"Failed to load ExamPaper from {file_path}"
            assert paper.exam_type.upper() == "GATE"
            assert len(paper.sections) >= 1
            assert len(paper.all_questions) > 0, f"Paper {paper.paper_id} has 0 questions!"

    def test_all_question_images_exist_on_disk(self):
        json_files = glob.glob(os.path.join(self.papers_dir, "*.json"))
        missing_images = []
        
        for file_path in json_files:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            paper_dir = os.path.dirname(file_path)
            for sec in data.get("sections", []):
                for q in sec.get("questions", []):
                    img_url = q.get("imageUrl")
                    if img_url:
                        # Resolve path
                        target = os.path.join(paper_dir, img_url) if not os.path.isabs(img_url) else img_url
                        if not os.path.exists(target):
                            missing_images.append(f"{os.path.basename(file_path)} Q{q.get('questionId')}: {img_url}")
                            
        assert len(missing_images) == 0, f"Found missing images: {missing_images[:10]}"

    def test_2015_question_fixes(self):
        from PIL import Image
        file_path = os.path.join(self.papers_dir, "gate_ec_2015.json")
        paper = self.storage.load_paper_from_file(file_path)
        assert paper is not None
        assert len(paper.all_questions) == 65
        
        q_map = {q.question_number: q for q in paper.all_questions}
        
        # Test Q3: non-empty image (> 150px height), MCQ, correct answer C
        q3 = q_map[3]
        assert q3.type == QuestionType.MCQ
        assert q3.correct_answer == "C"
        assert len(q3.options) == 4
        q3_img = os.path.join(self.papers_dir, q3.image_url)
        assert os.path.exists(q3_img)
        assert Image.open(q3_img).height > 150, "Q3 image must be non-empty and properly stitched"
        
        # Test Q9: non-empty image (> 150px height), MCQ, correct answer C
        q9 = q_map[9]
        assert q9.type == QuestionType.MCQ
        assert q9.correct_answer == "C"
        assert len(q9.options) == 4
        q9_img = os.path.join(self.papers_dir, q9.image_url)
        assert os.path.exists(q9_img)
        assert Image.open(q9_img).height > 150, "Q9 image must be non-empty and properly stitched"
        
        # Test Q11: NAT type, zero negative marks, correct answer 2.0
        q11 = q_map[11]
        assert q11.type == QuestionType.NAT, f"Q11 should be NAT, found {q11.type}"
        assert q11.negative_marks == 0.0, f"Q11 NAT must have 0 negative marks, found {q11.negative_marks}"
        assert q11.correct_answer == 2.0
        assert q11.tolerance_min == 2.0
        assert q11.tolerance_max == 2.0
        q11_img = os.path.join(self.papers_dir, q11.image_url)
        assert os.path.exists(q11_img)
        assert Image.open(q11_img).height > 150, "Q11 image must be non-empty"

        # Test Q8: NAT type, zero negative marks, correct answer 3.0
        q8 = q_map[8]
        assert q8.type == QuestionType.NAT
        assert q8.negative_marks == 0.0
        assert q8.correct_answer == 3.0

    def test_2020_and_2017_fixes(self):
        from PIL import Image
        
        # 2020 Paper Verification
        p2020 = self.storage.load_paper_from_file(os.path.join(self.papers_dir, "gate_ec_2020.json"))
        assert p2020 is not None
        assert len(p2020.all_questions) == 65
        for q in p2020.all_questions:
            assert q.correct_answer is not None, f"2020 Q{q.question_number} must have official answer key"
            img_path = os.path.join(self.papers_dir, q.image_url)
            assert os.path.exists(img_path), f"2020 Q{q.question_number} image missing"
            assert Image.open(img_path).height >= 100, f"2020 Q{q.question_number} image too small"

        # 2017 Set 2 Verification
        p2017_2 = self.storage.load_paper_from_file(os.path.join(self.papers_dir, "gate_ec_2017_set2.json"))
        assert len(p2017_2.all_questions) == 65
        for q in p2017_2.all_questions:
            assert q.correct_answer is not None, f"2017 Set 2 Q{q.question_number} must have answer key"

        # 2017 Set 1 Verification
        p2017_1 = self.storage.load_paper_from_file(os.path.join(self.papers_dir, "gate_ec_2017_set1.json"))
        assert len(p2017_1.all_questions) == 65
        nat_count = sum(1 for q in p2017_1.all_questions if q.type == QuestionType.NAT)
        mcq_count = sum(1 for q in p2017_1.all_questions if q.type == QuestionType.MCQ)
        assert nat_count == 23, f"Expected 23 NAT questions in 2017 Set 1, found {nat_count}"
        assert mcq_count == 42, f"Expected 42 MCQ questions in 2017 Set 1, found {mcq_count}"
        for q in p2017_1.all_questions:
            if q.type == QuestionType.NAT:
                assert q.negative_marks == 0.0

    def test_marks_and_types_consistency(self):
        json_files = glob.glob(os.path.join(self.papers_dir, "*.json"))
        for file_path in json_files:
            paper = self.storage.load_paper_from_file(file_path)
            for q in paper.all_questions:
                assert q.positive_marks > 0, f"Q{q.question_number} in {paper.paper_id} has invalid positive marks: {q.positive_marks}"
                assert q.negative_marks >= 0, f"Q{q.question_number} in {paper.paper_id} has invalid negative marks: {q.negative_marks}"
                assert q.type in (QuestionType.MCQ, QuestionType.MSQ, QuestionType.NAT)

    def test_zero_page_fallbacks_and_all_questions_have_images(self):
        """Validates that across all 31 papers, zero questions use fallback page_X.png images and every question has an image."""
        json_files = glob.glob(os.path.join(self.papers_dir, "*.json"))
        assert len(json_files) == 31, f"Expected 31 papers, found {len(json_files)}"
        
        fallback_questions = []
        missing_images = []
        for file_path in json_files:
            paper = self.storage.load_paper_from_file(file_path)
            for q in paper.all_questions:
                if not q.image_url:
                    missing_images.append(f"{paper.paper_id} Q{q.question_number} has no image")
                elif "page_" in q.image_url:
                    fallback_questions.append(f"{paper.paper_id} Q{q.question_number}: {q.image_url}")
                else:
                    target = os.path.join(self.papers_dir, q.image_url) if not os.path.isabs(q.image_url) else q.image_url
                    if not os.path.exists(target):
                        missing_images.append(f"{paper.paper_id} Q{q.question_number}: {q.image_url}")
                        
        assert len(fallback_questions) == 0, f"Found {len(fallback_questions)} questions with fallback page_X images: {fallback_questions[:10]}"
        assert len(missing_images) == 0, f"Found {len(missing_images)} missing question images: {missing_images[:10]}"

    def test_older_papers_counts_and_keys(self):
        """Validates legacy papers 2000-2011, 2019, 2021 have correct question counts and official keys."""
        # 2000, 2001, 2002 have 50 questions and 50 keys
        for yr in [2000, 2001, 2002]:
            p = self.storage.load_paper_from_file(os.path.join(self.papers_dir, f"gate_ec_{yr}.json"))
            assert len(p.all_questions) == 50, f"GATE {yr} should have 50 questions, found {len(p.all_questions)}"
            keys_count = sum(1 for q in p.all_questions if q.correct_answer is not None)
            assert keys_count == 50, f"GATE {yr} should have 50 official keys, found {keys_count}"

        # 2003 to 2008 have 85 questions
        for yr in [2003, 2004, 2005, 2006, 2007, 2008]:
            p = self.storage.load_paper_from_file(os.path.join(self.papers_dir, f"gate_ec_{yr}.json"))
            assert len(p.all_questions) == 85, f"GATE {yr} should have 85 questions, found {len(p.all_questions)}"

        # 2009 has 60 questions
        p2009 = self.storage.load_paper_from_file(os.path.join(self.papers_dir, "gate_ec_2009.json"))
        assert len(p2009.all_questions) == 60, f"GATE 2009 should have 60 questions, found {len(p2009.all_questions)}"

        # 2010, 2011, 2019, 2021 have 65 questions
        for yr in [2010, 2011, 2019, 2021]:
            p = self.storage.load_paper_from_file(os.path.join(self.papers_dir, f"gate_ec_{yr}.json"))
            assert len(p.all_questions) == 65, f"GATE {yr} should have 65 questions, found {len(p.all_questions)}"

    def test_modern_papers_whole_question_slices(self):
        """Validates modern papers (2012-2026) have whole-question slices and 65/65 keys for 2016, 2017_set2, 2018."""
        p2016 = self.storage.load_paper_from_file(os.path.join(self.papers_dir, "gate_ec_2016.json"))
        assert len(p2016.all_questions) == 65
        k2016 = sum(1 for q in p2016.all_questions if q.correct_answer is not None)
        assert k2016 == 65, f"2016 should have 65 keys, found {k2016}"

        p2018 = self.storage.load_paper_from_file(os.path.join(self.papers_dir, "gate_ec_2018.json"))
        assert len(p2018.all_questions) == 65
        k2018 = sum(1 for q in p2018.all_questions if q.correct_answer is not None)
        assert k2018 == 65, f"2018 should have 65 keys, found {k2018}"

        p2017_2 = self.storage.load_paper_from_file(os.path.join(self.papers_dir, "gate_ec_2017_set2.json"))
        assert len(p2017_2.all_questions) == 65
        k2017_2 = sum(1 for q in p2017_2.all_questions if q.correct_answer is not None)
        assert k2017_2 == 65, f"2017 Set 2 should have 65 keys, found {k2017_2}"

    def test_all_topicwise_papers_validation(self):
        """Validates that all 72 topicwise papers parse, load, have images on disk, and keys set."""
        tw_dir = os.path.join(self.base_dir, "data", "papers", "gate_ec_topicwise")
        json_files = glob.glob(os.path.join(tw_dir, "*.json"))
        assert len(json_files) == 72, f"Expected 72 topicwise papers, found {len(json_files)}"
        
        total_questions = 0
        missing_images = []
        for f in json_files:
            paper = self.storage.load_paper_from_file(f)
            assert paper is not None, f"Failed to load {f}"
            assert paper.category == "Topic-wise"
            assert len(paper.all_questions) > 0, f"Paper {f} has 0 questions"
            total_questions += len(paper.all_questions)
            for q in paper.all_questions:
                if not q.image_url or not os.path.exists(q.image_url):
                    missing_images.append(f"{paper.paper_id} Q{q.question_number}: {q.image_url}")
        
        assert len(missing_images) == 0, f"Found missing topicwise images: {missing_images[:5]}"
        assert total_questions > 1000, f"Expected >1000 questions, got {total_questions}"

    def test_no_questions_exceed_two_marks_across_all_papers(self):
        """Verifies that across all 103 papers, zero questions have positiveMarks > 2.0."""
        all_papers = self.storage.load_all_papers()
        assert len(all_papers) >= 103
        exceeding = []
        for p in all_papers:
            for q in p.all_questions:
                if q.positive_marks > 2.0:
                    exceeding.append((p.paper_id, q.question_number, q.positive_marks))
        assert len(exceeding) == 0, f"Found {len(exceeding)} questions with marks > 2.0: {exceeding[:10]}"

    def test_boolean_algebra_cleaned_attempt(self):
        """Verifies that the Boolean Algebra attempt has unanswerable >2 mark questions removed."""
        att_path = os.path.join(
            self.base_dir, "data", "attempts",
            "gate_ec_topicwise_boolean_algebra_GATE25-TST01_2026-10-18_06-22-00.json"
        )
        assert os.path.exists(att_path)
        res = self.storage.load_attempt_result(att_path)
        assert res is not None
        assert res.total_questions == 28, f"Expected 28 questions, got {res.total_questions}"
        assert res.total_marks == 42.0, f"Expected 42.0 total marks, got {res.total_marks}"
        assert res.score_obtained == 28.34, f"Expected 28.34 score, got {res.score_obtained}"
        assert res.percentage_score == 67.48, f"Expected 67.48% score, got {res.percentage_score}"
        assert res.accuracy_percentage == 74.07, f"Expected 74.07% accuracy, got {res.accuracy_percentage}"
        for ev in res.evaluations:
            assert ev.max_marks <= 2.0, f"Question {ev.question_number} max_marks {ev.max_marks} > 2.0"


if __name__ == "__main__":
    pytest.main(["-v", __file__])


