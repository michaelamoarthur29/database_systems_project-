# Grade Book Database – Project Report

---

## 1. ER Diagram Description

The ER diagram contains six entities connected by four relationships:

**Entities and their attributes:**

- **Course** — `course_id (PK)`, department, course_num, course_name, semester, year
- **Student** — `student_id (PK)`, first_name, last_name, email
- **Enrollment** — `enrollment_id (PK)`, `course_id (FK)`, `student_id (FK)`  — resolves the many-to-many relationship between Course and Student
- **Category** — `category_id (PK)`, `course_id (FK)`, name, weight (percentage 0–100)
- **Assignment** — `assignment_id (PK)`, `category_id (FK)`, title, max_points
- **Score** — `score_id (PK)`, `assignment_id (FK)`, `student_id (FK)`, points

**Relationships:**

| Relationship | Cardinality | Notes |
|---|---|---|
| Course — Enrollment | 1 to many | One course has many enrollments |
| Student — Enrollment | 1 to many | One student has many enrollments |
| Course — Category | 1 to many | Each course defines its own categories |
| Category — Assignment | 1 to many | Each category contains 0-or-more assignments |
| Assignment — Score | 1 to many | Each assignment has one score per enrolled student |
| Student — Score | 1 to many | One student receives many scores |

**Design decisions:**

The number of assignments per category is intentionally unbounded (one-to-many). Category weights are stored as REAL values in the Category table and their sum across a course must equal 100%, which is enforced by application logic in `update_category_weights`. Storing weights at the category level (not the assignment level) means adding or removing assignments automatically adjusts each assignment's effective contribution without any schema change: if there are N homework assignments each worth (homework_weight / N)% of the total.

---

## 2. Table Creation Commands (Task 2)

```sql
-- Courses taught by the professor
CREATE TABLE IF NOT EXISTS Course (
    course_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    department  TEXT    NOT NULL,
    course_num  TEXT    NOT NULL,
    course_name TEXT    NOT NULL,
    semester    TEXT    NOT NULL CHECK(semester IN ('Spring','Summer','Fall','Winter')),
    year        INTEGER NOT NULL
);

-- Students
CREATE TABLE IF NOT EXISTS Student (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name  TEXT NOT NULL,
    email      TEXT UNIQUE
);

-- Enrollment: many-to-many Course <-> Student
CREATE TABLE IF NOT EXISTS Enrollment (
    enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id     INTEGER NOT NULL REFERENCES Course(course_id) ON DELETE CASCADE,
    student_id    INTEGER NOT NULL REFERENCES Student(student_id) ON DELETE CASCADE,
    UNIQUE(course_id, student_id)
);

-- Grading categories per course (participation, homework, tests, ...)
CREATE TABLE IF NOT EXISTS Category (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id   INTEGER NOT NULL REFERENCES Course(course_id) ON DELETE CASCADE,
    name        TEXT    NOT NULL,
    weight      REAL    NOT NULL CHECK(weight > 0),
    UNIQUE(course_id, name)
);

-- Individual assignments within a category
CREATE TABLE IF NOT EXISTS Assignment (
    assignment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id     INTEGER NOT NULL REFERENCES Category(category_id) ON DELETE CASCADE,
    title           TEXT    NOT NULL,
    max_points      REAL    NOT NULL DEFAULT 100.0
);

-- Scores: one row per (student, assignment)
CREATE TABLE IF NOT EXISTS Score (
    score_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER NOT NULL REFERENCES Assignment(assignment_id) ON DELETE CASCADE,
    student_id    INTEGER NOT NULL REFERENCES Student(student_id) ON DELETE CASCADE,
    points        REAL    NOT NULL CHECK(points >= 0),
    UNIQUE(assignment_id, student_id)
);
```

---

## 3. Sample INSERT Statements (Task 2 – excerpt)

```sql
-- Courses
INSERT INTO Course(department,course_num,course_name,semester,year)
VALUES ('CS','3380','Database Management','Fall',2024);
INSERT INTO Course(department,course_num,course_name,semester,year)
VALUES ('CS','2210','Data Structures','Spring',2024);

-- Students (8 total; 3 shown)
INSERT INTO Student(first_name,last_name,email)
VALUES ('Alice','Anderson','alice@uni.edu');
INSERT INTO Student(first_name,last_name,email)
VALUES ('Bob','Quintero','bob@uni.edu');
INSERT INTO Student(first_name,last_name,email)
VALUES ('Grace','Qian','grace@uni.edu');

-- Categories for CS 3380 (weights sum to 100)
INSERT INTO Category(course_id,name,weight) VALUES (1,'Participation',10.0);
INSERT INTO Category(course_id,name,weight) VALUES (1,'Homework',20.0);
INSERT INTO Category(course_id,name,weight) VALUES (1,'Tests',50.0);
INSERT INTO Category(course_id,name,weight) VALUES (1,'Projects',20.0);

-- Assignments (excerpt)
INSERT INTO Assignment(category_id,title,max_points) VALUES (2,'HW1 – ER Diagrams',100);
INSERT INTO Assignment(category_id,title,max_points) VALUES (3,'Midterm Exam',100);

-- Score example
INSERT INTO Score(assignment_id,student_id,points) VALUES (8,1,82.0);
```

---

## 4. Task 4 – Assignment Statistics Query

```sql
SELECT
    a.title,
    ROUND(AVG(s.points), 2)  AS average,
    MAX(s.points)            AS highest,
    MIN(s.points)            AS lowest,
    COUNT(s.score_id)        AS num_scores
FROM Assignment a
JOIN Score s ON a.assignment_id = s.assignment_id
WHERE a.title = 'Midterm Exam'
GROUP BY a.assignment_id;
```

**Result:**

| title        | average | highest | lowest | num_scores |
|---|---|---|---|---|
| Midterm Exam | 71.88   | 94.0    | 48.0   | 8          |

---

## 5. Task 5 – List Students in a Course

```sql
SELECT st.student_id, st.first_name, st.last_name, st.email
FROM Student st
JOIN Enrollment e  ON st.student_id = e.student_id
JOIN Course     co ON e.course_id   = co.course_id
WHERE co.course_num = '3380'
  AND co.semester   = 'Fall'
  AND co.year       = 2024
ORDER BY st.last_name, st.first_name;
```

**Result (CS 3380 Fall 2024):** Alice Anderson, Carol Chen, Eva Martinez, Frank Nguyen, Grace Qian, David Quinn, Bob Quintero, Henry Smith.

---

## 6. Task 6 – Students + All Scores

```sql
SELECT
    st.first_name || ' ' || st.last_name AS student,
    cat.name        AS category,
    a.title         AS assignment,
    a.max_points,
    s.points
FROM Student st
JOIN Enrollment e   ON st.student_id   = e.student_id
JOIN Course     co  ON e.course_id     = co.course_id
JOIN Category   cat ON cat.course_id   = co.course_id
JOIN Assignment a   ON a.category_id   = cat.category_id
LEFT JOIN Score s   ON s.assignment_id = a.assignment_id
                   AND s.student_id    = st.student_id
WHERE co.course_num='3380' AND co.semester='Fall' AND co.year=2024
ORDER BY st.last_name, cat.name, a.assignment_id;
```

Uses `LEFT JOIN` on Score so students with missing scores (NULL) are still shown.

---

## 7. Task 7 – Add an Assignment

```sql
-- Step 1: find the category
SELECT cat.category_id FROM Category cat
JOIN Course co ON cat.course_id=co.course_id
WHERE co.course_num='3380' AND co.semester='Fall' AND co.year=2024
  AND cat.name='Homework';

-- Step 2: insert
INSERT INTO Assignment(category_id, title, max_points)
VALUES (2, 'HW6 – Query Optimization', 100.0);
```

---

## 8. Task 8 – Change Category Weights

```sql
UPDATE Category SET weight=5.0
WHERE course_id=(SELECT course_id FROM Course
                 WHERE course_num='3380' AND semester='Fall' AND year=2024)
  AND name='Participation';

UPDATE Category SET weight=25.0
WHERE course_id=... AND name='Homework';

UPDATE Category SET weight=50.0
WHERE course_id=... AND name='Tests';

UPDATE Category SET weight=20.0
WHERE course_id=... AND name='Projects';
-- (Application validates sum=100 before issuing any UPDATE)
```

---

## 9. Task 9 – Add 2 Points to All Students on an Assignment

```sql
UPDATE Score
SET points = MIN(points + 2,
                 (SELECT max_points FROM Assignment
                  WHERE assignment_id = Score.assignment_id))
WHERE assignment_id = (
    SELECT assignment_id FROM Assignment
    WHERE title = 'Midterm Exam' LIMIT 1
);
```

The `MIN(...)` expression caps scores at `max_points` so no student exceeds 100%.

---

## 10. Task 10 – Add 2 Points Only to 'Q'-Lastname Students

```sql
UPDATE Score
SET points = MIN(points + 2,
                 (SELECT max_points FROM Assignment
                  WHERE assignment_id = Score.assignment_id))
WHERE assignment_id = (
    SELECT assignment_id FROM Assignment
    WHERE title = 'Final Exam' LIMIT 1
)
AND student_id IN (
    SELECT student_id FROM Student WHERE last_name LIKE '%Q%'
);
```

**Affected students:** Bob Quintero, David Quinn, Grace Qian.

---

## 11. Task 11 – Compute Final Grade

```sql
SELECT
    cat.name           AS category,
    cat.weight         AS cat_weight,
    AVG(s.points)      AS avg_earned,
    AVG(a.max_points)  AS avg_max
FROM Score s
JOIN Assignment a  ON s.assignment_id = a.assignment_id
JOIN Category cat  ON a.category_id   = cat.category_id
JOIN Course co     ON cat.course_id    = co.course_id
JOIN Student st    ON s.student_id     = st.student_id
WHERE st.first_name='Alice' AND st.last_name='Anderson'
  AND co.course_num='3380' AND co.semester='Fall' AND co.year=2024
GROUP BY cat.category_id;
```

Then in Python:
```python
grade = sum((row["cat_weight"]/100) * (row["avg_earned"]/row["avg_max"]*100)
            for row in rows)
```

**Alice Anderson result:** 86.40% (B)

---

## 12. Task 12 – Grade with Lowest Score Dropped

For each category, scores are fetched ordered by `(points / max_points) ASC`. If the category has more than one assignment, the first row (lowest ratio) is discarded before computing the average.

```sql
SELECT s.points, a.max_points
FROM Score s
JOIN Assignment a ON s.assignment_id=a.assignment_id
WHERE a.category_id=? AND s.student_id=?
ORDER BY (s.points / a.max_points) ASC;
-- Python: if len(scores) > 1: scores = scores[1:]
```

**Alice Anderson result (drop-lowest):** 88.69% (B) — up from 86.40%.

---

## 13. Test Cases and Results

### Test Case 1 – Assignment statistics (Task 4)

| Assignment        | Average | Highest | Lowest |
|---|---|---|---|
| Midterm Exam      | 71.88   | 94.0    | 48.0   |
| HW1 – ER Diagrams | 77.13   | 95.0    | 55.0   |

### Test Case 2 – Task 10: 'Q' students bonus

Before bonus (Final Exam):

| Student      | Points |
|---|---|
| Bob Quintero | 70.0   |
| David Quinn  | 60.0   |
| Grace Qian   | 95.0   |

After +2 bonus:

| Student      | Points |
|---|---|
| Bob Quintero | 72.0   |
| David Quinn  | 62.0   |
| Grace Qian   | 97.0   |

Non-Q students (Alice Anderson, etc.) were unaffected — verified by querying Score directly.

### Test Case 3 – Final grades (Task 11 vs 12)

| Student       | Normal grade | Drop-lowest | Difference |
|---|---|---|---|
| Alice Anderson | 86.40% (B)  | 88.69% (B)  | +2.29%     |
| Carol Chen     | 96.30% (A)  | 97.20% (A)  | +0.90%     |
| Frank Nguyen   | 52.50% (F)  | 54.06% (F)  | +1.56%     |

Drop-lowest always improves or maintains the grade, as expected.

### Test Case 4 – Add assignment and verify category

After calling `add_assignment(..., "HW6 – Query Optimization")`, the Assignment table gains row id=17 with category_id=2 (Homework). This assignment has no scores yet — Task 6's LEFT JOIN correctly shows it as NULL for all students.

### Test Case 5 – Weight update validation

Calling `update_category_weights` with weights summing to 99 returns an error message and makes no database changes. Weights summing to exactly 100 succeed.

---

## 14. Source Code Notes

All logic lives in `gradebook.py`. Key design choices:

- **`PRAGMA foreign_keys = ON`** — ensures cascading deletes work and referential integrity is enforced at the SQLite level.
- **`conn.row_factory = sqlite3.Row`** — allows column access by name (e.g. `row["avg_earned"]`) for readability.
- **Parameterized queries** — all user-supplied values go through `?` placeholders, preventing SQL injection.
- **Cap on bonus points** — `MIN(points + bonus, max_points)` in one SQL expression; no application-side loop needed.
- **Drop-lowest in Python, not SQL** — sorting and slicing in Python is cleaner than a window function for this use case, and SQLite's window function support is version-dependent.
