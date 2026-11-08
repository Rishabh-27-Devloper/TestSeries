# National CBT Examination Simulator - User Guide

## Overview

The **National CBT Examination Simulator** is a complete, offline, desktop-grade Computer-Based Test application that replicates the exact look, feel, security features, and evaluation criteria of the official NTA / TCS iON examination platform (specifically designed for **GATE**, with native extensibility for **JEE Main**, **NEET**, and custom exams).

---

## Key Features

1. **Layered 3-Tier Architecture**:
   - **Layer 1: Exam Selection Portal**: Select your target exam stream (GATE, JEE Main, NEET, etc.) and manage candidate profile (Name, Roll Number).
   - **Layer 2: Paper Inventory Browser**: Browse Full Length Mocks, Previous Year Papers (PYQ), and Topic-wise practice tests. Filter by category, search by keyword, view question blueprint, and import custom JSON test papers.
   - **Layer 3: CBT Examination Environment**:
     - Pre-exam Instructions & Declaration screen with mandatory agreement before exam entry.
     - **Strict Fullscreen Kiosk Mode**: Fullscreen is enforced ONLY during the active exam session.
     - Live countdown timer with auto-submission at `00:00:00`.
     - **Official GATE / TCS iON Virtual Scientific Calculator**: Complete with trigonometric, inverse trig, hyperbolic, logarithmic, power, root, memory (`MC`, `MR`, `MS`, `M+`, `M-`), and angle modes (`Deg`/`Rad`).
     - **Authentic Question Palette & Legend**: Real-time status counts with official TCS iON color badges (Not Visited, Not Answered, Answered, Marked for Review, Answered & Marked for Review).
     - **Multiple Question Formats**:
       - **MCQ** (Single choice with negative marking penalty)
       - **MSQ** (Multiple choices with zero negative marking and full-match requirement)
       - **NAT** (Numerical answer with physical keyboard or on-screen numeric keypad)
     - Collapsible side palette, Question Paper preview modal, and Submit confirmation summary table.
   - **Student Dashboard & Performance Analytics**: Detailed scorecard, section-wise analysis, question-by-question review with official answers and step-by-step explanations, and historical test attempts logging.

2. **Security & Anti-Cheat Proctoring**:
   - Enforces fullscreen kiosk mode when exam starts.
   - Monitors window focus loss (Alt+Tab, Windows key, clicking second monitor, or opening external software).
   - Issues warnings on unauthorized focus changes (maximum 3 strikes).
   - Automatically submits and locks the exam if 3 strikes are reached.
   - Traps Alt+F4 and context menus during the exam.

3. **100% Offline & Windows Compatible**:
   - Runs completely offline without internet or server dependencies.
   - Stores papers and past attempts locally on disk.

---

## How to Run the Application

In your terminal or PowerShell:

```powershell
python run_app.py
```

---

## Directory Structure

```
TestSeries/
├── run_app.py                      # Main entrypoint
├── core/
│   ├── models.py                   # Exam models & data structures
│   ├── evaluator.py                # Official GATE & extensible evaluation rules
│   ├── security.py                 # Fullscreen kiosk & proctoring manager
│   └── storage.py                  # Paper loading and attempt history persistence
├── ui/
│   ├── main_window.py              # Main window & layer transitions
│   ├── layer1_exam_selection.py    # Layer 1: Exam Selection Portal
│   ├── layer2_paper_selection.py   # Layer 2: Test Paper Inventory
│   ├── layer3_instructions.py      # Layer 3: Candidate Instructions & Agreement
│   ├── layer3_cbt_exam.py          # Layer 3: Live Fullscreen CBT Exam
│   ├── layer_dashboard.py          # Post-exam Analytics & Scorecard
│   └── widgets/
│       ├── calculator.py           # TCS iON Scientific Virtual Calculator
│       ├── palette.py              # Question Palette & Legend
│       ├── question_display.py     # Question renderer (MCQ/MSQ/NAT)
│       ├── timer_widget.py         # Countdown timer
│       └── popups.py               # Question Paper & Submission dialogs
├── data/
│   ├── papers/                     # JSON test papers organized by exam
│   │   ├── gate_cs/
│   │   ├── gate_da/
│   │   └── jee_main/
│   └── attempts/                   # Saved student test submissions
└── docs/
    ├── JSON_PAPER_SCHEMA.md        # Guide on creating custom test papers
    └── USER_GUIDE.md               # User guide
```
