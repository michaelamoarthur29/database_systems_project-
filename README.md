# Grade Book Database System

A SQLite-backed grade book that tracks students, courses, categories, assignments, and scores for a professor. Implements all 12 required tasks using Python 3 and the standard `sqlite3` module — no third-party packages required.

---

## Requirements

| Tool    | Version  |
|---------|----------|
| Python  | 3.8+     |
| sqlite3 | Built-in |

No `pip install` needed.

---

## Files

```
gradebook/
├── gradebook.py       # Main source code (all 12 tasks)
├── gradebook.db       # SQLite database (auto-created on first run)
└── README.md          # This file
```

---

## How to Run

### 1. Clone / download the project

```bash
cd gradebook
```

### 2. Run the full demo (all 12 tasks)

```bash
python gradebook.py
```

This will:
- Delete any existing `gradebook.db` and start fresh
- Create all tables (Task 2)
- Insert sample data — 2 courses, 8 students, categories, assignments, scores (Task 2)
- Print every table with contents (Task 3)
- Run Tasks 4–12 and print results to stdout

### 3. Use the API in your own script

```python
from gradebook import get_connection, assignment_stats, compute_grade

conn = get_connection()
assignment_stats(conn, "Midterm Exam")
compute_grade(conn, "Alice", "Anderson", "3380", "Fall", 2024)
conn.close()
```

---

## Database Schema

| Table      | Purpose                                        |
|------------|------------------------------------------------|
| Course     | Courses (dept, number, name, semester, year)   |
| Student    | Students (name, email)                         |
| Enrollment | Many-to-many: Course ↔ Student                 |
| Category   | Grading categories per course with weights     |
| Assignment | Individual assignments within a category       |
| Score      | One row per (student, assignment)              |

**Category weights** must sum to 100% per course (enforced in `update_category_weights`).

---

## Function Reference (Tasks)

| Function                     | Task | Description                                    |
|------------------------------|------|------------------------------------------------|
| `create_tables(conn)`        | 2    | Creates all 6 tables                          |
| `insert_sample_data(conn)`   | 2    | Loads demo data                               |
| `show_tables(conn)`          | 3    | Prints all tables                             |
| `assignment_stats(conn, title)` | 4 | Avg/highest/lowest for one assignment        |
| `list_students(conn, ...)`   | 5    | All students in a course                      |
| `list_students_scores(conn, ...)` | 6 | All students + all scores in a course       |
| `add_assignment(conn, ...)`  | 7    | Add a new assignment to a category            |
| `update_category_weights(conn, ...)` | 8 | Change category weights (must sum to 100) |
| `add_points_all(conn, ...)`  | 9    | +N pts to every student on an assignment      |
| `add_points_q_students(conn, ...)` | 10 | +N pts only to students with 'Q' in surname |
| `compute_grade(conn, ...)`   | 11   | Weighted final grade for a student            |
| `compute_grade_drop_lowest(conn, ...)` | 12 | Same but drop 1 lowest per category    |

---

## Grade Calculation

For each category:

```
category_contribution = (weight / 100) × (avg_earned / avg_max_points × 100)
```

Final grade = sum of all category contributions.

The **drop-lowest** variant (Task 12) sorts scores by `points/max_points` ascending and removes the first entry before averaging, only when the category has more than one assignment.

---

## Sample Courses & Data

**CS 3380 – Database Management (Fall 2024)**
- 8 students
- Categories: Participation 5%, Homework 25%, Tests 50%, Projects 20%
- 11 assignments (2 participation, 5 homework, 2 tests, 2 projects)

**CS 2210 – Data Structures (Spring 2024)**
- 5 students
- Categories: Homework 20%, Tests 40%, Projects 40%
- 5 assignments

---

## Notes

- The database is re-created from scratch every time `gradebook.py` is run directly.
- `PRAGMA foreign_keys = ON` is set on every connection to enforce referential integrity.
- Bonus points (Tasks 9, 10) are capped at `max_points` so scores never exceed 100%.
