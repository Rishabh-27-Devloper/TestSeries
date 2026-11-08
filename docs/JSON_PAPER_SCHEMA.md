# CBT Exam Paper JSON Schema Guide

This document specifies the exact JSON schema used by the National CBT Examination Simulator. You can create your own test papers (Full Length Mocks, Previous Year Papers, or Topic-wise Practice Tests) by creating `.json` files and placing them in the `data/papers/<exam_category>/` folder or using the **"Import JSON Paper"** button in Layer 2.

---

## 1. Top-Level Paper Structure

```json
{
  "paperId": "UNIQUE_IDENTIFIER_STRING",
  "title": "Title of the Exam Paper",
  "examType": "GATE",
  "durationMinutes": 180,
  "totalMarks": 100,
  "category": "Mock Paper",
  "year": 2024,
  "description": "Optional description of syllabus or pattern",
  "instructions": [
    "Instruction line 1",
    "Instruction line 2"
  ],
  "sections": [
    {
      "sectionId": "GA",
      "sectionName": "General Aptitude",
      "questions": []
    },
    {
      "sectionId": "CS",
      "sectionName": "Computer Science & IT",
      "questions": []
    }
  ]
}
```

### Top-Level Fields

| Field | Type | Description |
|---|---|---|
| `paperId` | String | Unique identifier (e.g., `"GATE_CS_2024_SET1"`) |
| `title` | String | Human-readable name displayed in the UI |
| `examType` | String | Target exam: `"GATE"`, `"JEE_MAIN"`, `"NEET"`, or custom |
| `durationMinutes`| Integer | Total test duration in minutes (e.g., `180` for 3 hours) |
| `totalMarks` | Number | Maximum possible score (e.g., `100` for GATE, `300` for JEE) |
| `category` | String | `"Mock Paper"`, `"PYQ"` (Previous Year), or `"Topic-wise"` |
| `year` | Integer | (Optional) Exam year (e.g., `2024`) |
| `description` | String | Summary of topics covered |
| `sections` | Array | List of section objects containing questions |

---

## 2. Question Object Specification with Diagrams

Questions can include diagrams for the main question text, as well as diagrams for individual choices (Option A, Option B, etc.).

```json
{
  "questionId": 1,
  "type": "MCQ",
  "positiveMarks": 2.0,
  "negativeMarks": 0.67,
  "questionText": "Consider the logic circuit shown in the diagram below. What is output Y?",
  "imageUrl": "assets/circuit_diagram.png",
  "options": [
    {
      "id": "A",
      "text": "Option A text",
      "image": "assets/option_a_diagram.png"
    },
    {
      "id": "B",
      "text": "Option B text"
    }
  ],
  "correctAnswer": "A",
  "explanation": "Step-by-step solution shown during post-exam review."
}
```

### Image / Diagram Options:
1. **Question Diagram**:
   - Supported keys: `"imageUrl"`, `"ImageURL"`, `"image"`, `"diagram"`, `"questionImage"`.
   - Relative path: e.g. `"assets/circuit.png"` (relative to the JSON file's folder).
   - Absolute path: e.g. `"C:/ExamAssets/diagram.png"`.
   - Embedded Base64 Data URI: e.g. `"data:image/png;base64,iVBORw0KGgoAAAANSUhEUg..."` (enables 100% self-contained JSON test papers with zero external file dependencies).
   - Click-to-Zoom: In the exam interface, students can click any diagram to open a high-resolution zoom viewer.

2. **Option Diagrams**:
   - Each option inside `"options"` can have an `"image"`, `"imageUrl"`, or `"diagram"` key.
   - Ideal for questions where options are different graphs, trees, or circuit diagrams.


---

## 3. Supported Question Types & Examples

### A. MCQ (Multiple Choice Question - Single Correct)

- Candidate selects **one** radio button.
- Negative marking applies (-1/3 of positive marks for 1-mark question, -2/3 for 2-mark question in GATE).

```json
{
  "questionId": 1,
  "type": "MCQ",
  "positiveMarks": 1.0,
  "negativeMarks": 0.33,
  "questionText": "What is the time complexity of searching an element in a balanced Binary Search Tree with $n$ nodes?",
  "options": [
    {"id": "A", "text": "O(1)"},
    {"id": "B", "text": "O(log n)"},
    {"id": "C", "text": "O(n)"},
    {"id": "D", "text": "O(n log n)"}
  ],
  "correctAnswer": "B",
  "explanation": "A balanced BST has height bounded by log(n), so lookup requires O(log n)."
}
```

---

### B. MSQ (Multiple Select Question - One or More Correct)

- Candidate selects **one or more** checkboxes.
- **GATE Rules:** Full marks are awarded **ONLY** if all correct choices are checked and no wrong choice is checked.
- **Zero negative marking** for MSQ.

```json
{
  "questionId": 2,
  "type": "MSQ",
  "positiveMarks": 2.0,
  "negativeMarks": 0.0,
  "questionText": "Which of the following sorting algorithms is/are STABLE?",
  "options": [
    {"id": "A", "text": "Merge Sort"},
    {"id": "B", "text": "Quick Sort"},
    {"id": "C", "text": "Counting Sort"},
    {"id": "D", "text": "Heap Sort"}
  ],
  "correctAnswer": ["A", "C"],
  "explanation": "Merge Sort and Counting Sort preserve relative order of identical keys; Quick Sort and Heap Sort do not."
}
```

---

### C. NAT (Numerical Answer Type)

- Candidate enters a numerical value (using physical keyboard or the **On-Screen Virtual Keypad**).
- **Zero negative marking** for NAT.
- You can specify exact value or a numerical tolerance range (`toleranceMin` and `toleranceMax`).

```json
{
  "questionId": 3,
  "type": "NAT",
  "positiveMarks": 2.0,
  "negativeMarks": 0.0,
  "questionText": "Consider a system with 3 processes sharing 4 resource units. What is the maximum value of $k$ requests per process to guarantee deadlock freedom?",
  "correctAnswer": 2,
  "toleranceMin": 2.0,
  "toleranceMax": 2.0,
  "explanation": "Using formula R >= N*(k-1) + 1: 4 >= 3*(k-1) + 1 => k <= 2."
}
```

For questions with a range (e.g. 5.10 to 5.20):
```json
{
  "correctAnswer": 5.15,
  "toleranceMin": 5.10,
  "toleranceMax": 5.20
}
```

---

## 4. Where to Store JSON Papers

Place your paper files in:
- `data/papers/gate_cs/` (for GATE CS & IT)
- `data/papers/gate_da/` (for GATE Data Science & AI)
- `data/papers/jee_main/` (for JEE Main)
- Or simply import them via the **"➕ Import JSON Paper"** button inside the app.
