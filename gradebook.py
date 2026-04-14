"""
Grade Book Database System
Uses SQLite for storage and provides all required query operations.
"""

import sqlite3
import os

DB_FILE = "gradebook.db"


# ─────────────────────────────────────────────
#  Connection helper
# ─────────────────────────────────────────────
def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


# ─────────────────────────────────────────────
#  Task 2 – Create tables
# ─────────────────────────────────────────────
CREATE_TABLES_SQL = """
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

-- Grading categories per course (participation, homework, tests, …)
-- sum of weight across a course must equal 100 (enforced by application logic)
CREATE TABLE IF NOT EXISTS Category (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id   INTEGER NOT NULL REFERENCES Course(course_id) ON DELETE CASCADE,
    name        TEXT    NOT NULL,
    weight      REAL    NOT NULL CHECK(weight > 0),   -- percentage, e.g. 20.0
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
    student_id    INTEGER NOT NULL REFERENCES Student(student_id)       ON DELETE CASCADE,
    points        REAL    NOT NULL CHECK(points >= 0),
    UNIQUE(assignment_id, student_id)
);
"""


def create_tables(conn):
    conn.executescript(CREATE_TABLES_SQL)
    conn.commit()
    print("Tables created successfully.")


# ─────────────────────────────────────────────
#  Task 2 – Insert sample data
# ─────────────────────────────────────────────
def insert_sample_data(conn):
    cur = conn.cursor()

    # --- Courses ---
    courses = [
        ("CS", "3380", "Database Management", "Fall",   2024),
        ("CS", "2210", "Data Structures",      "Spring", 2024),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO Course(department,course_num,course_name,semester,year) VALUES(?,?,?,?,?)",
        courses
    )

    # --- Students ---
    students = [
        ("Alice",   "Anderson", "alice@uni.edu"),
        ("Bob",     "Quintero", "bob@uni.edu"),
        ("Carol",   "Chen",     "carol@uni.edu"),
        ("David",   "Quinn",    "david@uni.edu"),
        ("Eva",     "Martinez", "eva@uni.edu"),
        ("Frank",   "Nguyen",   "frank@uni.edu"),
        ("Grace",   "Qian",     "grace@uni.edu"),
        ("Henry",   "Smith",    "henry@uni.edu"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO Student(first_name,last_name,email) VALUES(?,?,?)",
        students
    )

    # --- Enrollments (course 1: all 8 students; course 2: first 5) ---
    cur.execute("SELECT course_id FROM Course WHERE course_num='3380'")
    c1 = cur.fetchone()[0]
    cur.execute("SELECT course_id FROM Course WHERE course_num='2210'")
    c2 = cur.fetchone()[0]
    cur.execute("SELECT student_id FROM Student")
    all_ids = [r[0] for r in cur.fetchall()]

    for sid in all_ids:
        cur.execute("INSERT OR IGNORE INTO Enrollment(course_id,student_id) VALUES(?,?)", (c1, sid))
    for sid in all_ids[:5]:
        cur.execute("INSERT OR IGNORE INTO Enrollment(course_id,student_id) VALUES(?,?)", (c2, sid))

    # --- Categories for course 1: 10% participation, 20% homework, 50% tests, 20% projects ---
    cats_c1 = [
        (c1, "Participation", 10.0),
        (c1, "Homework",      20.0),
        (c1, "Tests",         50.0),
        (c1, "Projects",      20.0),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO Category(course_id,name,weight) VALUES(?,?,?)",
        cats_c1
    )

    # --- Categories for course 2: 20% homework, 40% tests, 40% projects ---
    cats_c2 = [
        (c2, "Homework", 20.0),
        (c2, "Tests",    40.0),
        (c2, "Projects", 40.0),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO Category(course_id,name,weight) VALUES(?,?,?)",
        cats_c2
    )

    # --- Helper to get category_id ---
    def cat_id(cid, name):
        cur.execute("SELECT category_id FROM Category WHERE course_id=? AND name=?", (cid, name))
        return cur.fetchone()[0]

    # --- Assignments for course 1 ---
    asgns_c1 = [
        (cat_id(c1,"Participation"), "Participation Week 1-7",  10),
        (cat_id(c1,"Participation"), "Participation Week 8-15", 10),
        (cat_id(c1,"Homework"),      "HW1 – ER Diagrams",       100),
        (cat_id(c1,"Homework"),      "HW2 – SQL Basics",        100),
        (cat_id(c1,"Homework"),      "HW3 – Normalization",     100),
        (cat_id(c1,"Homework"),      "HW4 – Transactions",      100),
        (cat_id(c1,"Homework"),      "HW5 – Indexes",           100),
        (cat_id(c1,"Tests"),         "Midterm Exam",            100),
        (cat_id(c1,"Tests"),         "Final Exam",              100),
        (cat_id(c1,"Projects"),      "Project 1",               100),
        (cat_id(c1,"Projects"),      "Project 2",               100),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO Assignment(category_id,title,max_points) VALUES(?,?,?)",
        asgns_c1
    )

    # --- Assignments for course 2 ---
    asgns_c2 = [
        (cat_id(c2,"Homework"), "HW1 – Arrays & Lists", 100),
        (cat_id(c2,"Homework"), "HW2 – Trees",          100),
        (cat_id(c2,"Tests"),    "Midterm",               100),
        (cat_id(c2,"Tests"),    "Final",                 100),
        (cat_id(c2,"Projects"), "Project – BST",         100),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO Assignment(category_id,title,max_points) VALUES(?,?,?)",
        asgns_c2
    )

    conn.commit()

    # --- Scores for course 1 ---
    cur.execute("""
        SELECT a.assignment_id, a.title
        FROM Assignment a
        JOIN Category c ON a.category_id=c.category_id
        WHERE c.course_id=?
        ORDER BY a.assignment_id
    """, (c1,))
    c1_asgns = cur.fetchall()

    # Raw scores per student (indexed same order as c1_asgns)
    raw_c1 = {
        "Alice":  [9,  8,  88, 92, 85, 90, 78, 82, 88,  90, 85],
        "Bob":    [7,  6,  75, 80, 70, 68, 72, 65, 70,  72, 68],
        "Carol":  [10, 9,  95, 98, 92, 96, 99, 94, 97,  95, 98],
        "David":  [8,  7,  60, 65, 58, 70, 62, 55, 60,  65, 58],
        "Eva":    [9,  8,  82, 78, 80, 85, 79, 75, 80,  82, 78],
        "Frank":  [6,  5,  55, 60, 52, 58, 50, 48, 52,  55, 50],
        "Grace":  [10, 10, 90, 95, 88, 92, 94, 91, 95,  93, 96],
        "Henry":  [8,  7,  72, 75, 70, 68, 74, 65, 68,  70, 72],
    }

    cur.execute("SELECT student_id, first_name FROM Student")
    smap = {r["first_name"]: r["student_id"] for r in cur.fetchall()}

    for fname, scores in raw_c1.items():
        sid = smap[fname]
        for (aid, _), pts in zip(c1_asgns, scores):
            cur.execute(
                "INSERT OR IGNORE INTO Score(assignment_id,student_id,points) VALUES(?,?,?)",
                (aid, sid, pts)
            )

    # --- Scores for course 2 (first 5 students) ---
    cur.execute("""
        SELECT a.assignment_id FROM Assignment a
        JOIN Category c ON a.category_id=c.category_id
        WHERE c.course_id=?
        ORDER BY a.assignment_id
    """, (c2,))
    c2_aids = [r[0] for r in cur.fetchall()]

    raw_c2 = {
        "Alice": [85, 90, 80, 88, 92],
        "Bob":   [70, 75, 65, 72, 68],
        "Carol": [95, 98, 92, 96, 99],
        "David": [60, 65, 55, 62, 58],
        "Eva":   [78, 82, 75, 80, 85],
    }

    for fname, scores in raw_c2.items():
        sid = smap[fname]
        for aid, pts in zip(c2_aids, scores):
            cur.execute(
                "INSERT OR IGNORE INTO Score(assignment_id,student_id,points) VALUES(?,?,?)",
                (aid, sid, pts)
            )

    conn.commit()
    print("Sample data inserted successfully.")


# ─────────────────────────────────────────────
#  Task 3 – Show tables
# ─────────────────────────────────────────────
def show_tables(conn):
    tables = ["Course", "Student", "Enrollment", "Category", "Assignment", "Score"]
    for t in tables:
        print(f"\n{'='*60}")
        print(f"  TABLE: {t}")
        print('='*60)
        cur = conn.execute(f"SELECT * FROM {t}")
        rows = cur.fetchall()
        if rows:
            headers = [d[0] for d in cur.description]
            col_w = [max(len(h), max((len(str(r[i])) for r in rows), default=0)) for i, h in enumerate(headers)]
            header_line = "  " + " | ".join(h.ljust(col_w[i]) for i, h in enumerate(headers))
            print(header_line)
            print("  " + "-+-".join("-"*w for w in col_w))
            for row in rows:
                print("  " + " | ".join(str(row[i]).ljust(col_w[i]) for i in range(len(headers))))
        else:
            print("  (empty)")


# ─────────────────────────────────────────────
#  Task 4 – Avg / highest / lowest for an assignment
# ─────────────────────────────────────────────
def assignment_stats(conn, assignment_title):
    sql = """
        SELECT
            a.title,
            ROUND(AVG(s.points), 2)  AS average,
            MAX(s.points)            AS highest,
            MIN(s.points)            AS lowest,
            COUNT(s.score_id)        AS num_scores
        FROM Assignment a
        JOIN Score s ON a.assignment_id = s.assignment_id
        WHERE a.title = ?
        GROUP BY a.assignment_id
    """
    row = conn.execute(sql, (assignment_title,)).fetchone()
    if row:
        print(f"\nStats for '{row['title']}':")
        print(f"  Average : {row['average']}")
        print(f"  Highest : {row['highest']}")
        print(f"  Lowest  : {row['lowest']}")
        print(f"  # Scores: {row['num_scores']}")
    else:
        print(f"Assignment '{assignment_title}' not found or has no scores.")
    return row


# ─────────────────────────────────────────────
#  Task 5 – List all students in a course
# ─────────────────────────────────────────────
def list_students(conn, course_num, semester, year):
    sql = """
        SELECT st.student_id, st.first_name, st.last_name, st.email
        FROM Student st
        JOIN Enrollment e  ON st.student_id = e.student_id
        JOIN Course     co ON e.course_id    = co.course_id
        WHERE co.course_num = ? AND co.semester = ? AND co.year = ?
        ORDER BY st.last_name, st.first_name
    """
    rows = conn.execute(sql, (course_num, semester, year)).fetchall()
    print(f"\nStudents in {course_num} ({semester} {year}):")
    if rows:
        for r in rows:
            print(f"  [{r['student_id']}] {r['first_name']} {r['last_name']} <{r['email']}>")
    else:
        print("  No students found.")
    return rows


# ─────────────────────────────────────────────
#  Task 6 – Students + all their scores in a course
# ─────────────────────────────────────────────
def list_students_scores(conn, course_num, semester, year):
    sql = """
        SELECT
            st.first_name || ' ' || st.last_name AS student,
            cat.name        AS category,
            a.title         AS assignment,
            a.max_points,
            s.points
        FROM Student st
        JOIN Enrollment e  ON st.student_id   = e.student_id
        JOIN Course     co ON e.course_id      = co.course_id
        JOIN Category   cat ON cat.course_id   = co.course_id
        JOIN Assignment a   ON a.category_id   = cat.category_id
        LEFT JOIN Score s   ON s.assignment_id = a.assignment_id
                            AND s.student_id   = st.student_id
        WHERE co.course_num=? AND co.semester=? AND co.year=?
        ORDER BY st.last_name, cat.name, a.assignment_id
    """
    rows = conn.execute(sql, (course_num, semester, year)).fetchall()
    print(f"\nAll scores in {course_num} ({semester} {year}):")
    cur_student = None
    for r in rows:
        if r["student"] != cur_student:
            cur_student = r["student"]
            print(f"\n  {cur_student}")
        pts = r["points"] if r["points"] is not None else "N/A"
        print(f"    [{r['category']}] {r['assignment']:40s} {pts}/{r['max_points']}")
    return rows


# ─────────────────────────────────────────────
#  Task 7 – Add an assignment to a course
# ─────────────────────────────────────────────
def add_assignment(conn, course_num, semester, year, category_name, title, max_points=100.0):
    cur = conn.cursor()
    cur.execute("""
        SELECT cat.category_id FROM Category cat
        JOIN Course co ON cat.course_id=co.course_id
        WHERE co.course_num=? AND co.semester=? AND co.year=? AND cat.name=?
    """, (course_num, semester, year, category_name))
    row = cur.fetchone()
    if not row:
        print(f"Category '{category_name}' not found in {course_num} {semester} {year}.")
        return None
    cur.execute(
        "INSERT INTO Assignment(category_id,title,max_points) VALUES(?,?,?)",
        (row[0], title, max_points)
    )
    conn.commit()
    aid = cur.lastrowid
    print(f"Assignment '{title}' added (id={aid}) to category '{category_name}'.")
    return aid


# ─────────────────────────────────────────────
#  Task 8 – Change category weights for a course
# ─────────────────────────────────────────────
def update_category_weights(conn, course_num, semester, year, new_weights: dict):
    """new_weights: {category_name: new_weight_float}  — must sum to 100."""
    total = sum(new_weights.values())
    if abs(total - 100.0) > 0.001:
        print(f"ERROR: weights sum to {total}, must equal 100.")
        return False

    cur = conn.cursor()
    cur.execute("""
        SELECT co.course_id FROM Course co
        WHERE co.course_num=? AND co.semester=? AND co.year=?
    """, (course_num, semester, year))
    row = cur.fetchone()
    if not row:
        print("Course not found.")
        return False
    cid = row[0]

    for cat_name, weight in new_weights.items():
        cur.execute(
            "UPDATE Category SET weight=? WHERE course_id=? AND name=?",
            (weight, cid, cat_name)
        )
    conn.commit()
    print(f"Category weights updated for {course_num} {semester} {year}:")
    for k, v in new_weights.items():
        print(f"  {k}: {v}%")
    return True


# ─────────────────────────────────────────────
#  Task 9 – Add 2 points to every student on an assignment
# ─────────────────────────────────────────────
def add_points_all(conn, assignment_title, bonus=2.0):
    sql = """
        UPDATE Score
        SET points = MIN(points + ?,
                         (SELECT max_points FROM Assignment
                          WHERE assignment_id = Score.assignment_id))
        WHERE assignment_id = (
            SELECT assignment_id FROM Assignment WHERE title=? LIMIT 1
        )
    """
    conn.execute(sql, (bonus, assignment_title))
    conn.commit()
    n = conn.execute(
        "SELECT changes()"
    ).fetchone()[0]
    print(f"+{bonus} pts added to all {n} scores on '{assignment_title}'.")


# ─────────────────────────────────────────────
#  Task 10 – Add 2 points only to students whose last name contains 'Q'
# ─────────────────────────────────────────────
def add_points_q_students(conn, assignment_title, bonus=2.0):
    sql = """
        UPDATE Score
        SET points = MIN(points + ?,
                         (SELECT max_points FROM Assignment
                          WHERE assignment_id = Score.assignment_id))
        WHERE assignment_id = (
            SELECT assignment_id FROM Assignment WHERE title=? LIMIT 1
        )
        AND student_id IN (
            SELECT student_id FROM Student WHERE last_name LIKE '%Q%'
        )
    """
    conn.execute(sql, (bonus, assignment_title))
    conn.commit()
    n = conn.execute("SELECT changes()").fetchone()[0]
    print(f"+{bonus} pts added to {n} 'Q'-lastname student(s) on '{assignment_title}'.")


# ─────────────────────────────────────────────
#  Task 11 – Compute final grade for a student
# ─────────────────────────────────────────────
def compute_grade(conn, first_name, last_name, course_num, semester, year):
    """
    Grade = sum over categories of:
        category_weight/100 * (avg_score_in_category / avg_max_points_in_category * 100)
    """
    sql = """
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
        WHERE st.first_name=? AND st.last_name=?
          AND co.course_num=? AND co.semester=? AND co.year=?
        GROUP BY cat.category_id
    """
    rows = conn.execute(sql, (first_name, last_name, course_num, semester, year)).fetchall()
    if not rows:
        print("No data found for that student/course combination.")
        return None

    print(f"\nGrade for {first_name} {last_name} in {course_num} ({semester} {year}):")
    total_grade = 0.0
    for r in rows:
        pct = (r["avg_earned"] / r["avg_max"]) * 100 if r["avg_max"] else 0
        contribution = (r["cat_weight"] / 100) * pct
        total_grade += contribution
        print(f"  {r['category']:15s} weight={r['cat_weight']}%  "
              f"score={r['avg_earned']:.2f}/{r['avg_max']:.2f}  "
              f"pct={pct:.2f}%  contribution={contribution:.2f}%")

    letter = grade_letter(total_grade)
    print(f"  {'─'*60}")
    print(f"  FINAL GRADE: {total_grade:.2f}%  ({letter})")
    return total_grade


# ─────────────────────────────────────────────
#  Task 12 – Grade with lowest score dropped per category
# ─────────────────────────────────────────────
def compute_grade_drop_lowest(conn, first_name, last_name, course_num, semester, year):
    """
    Same as Task 11, but for each category the single lowest score is excluded
    before computing the average (only drops if category has > 1 assignment).
    """
    # Get all categories for the course
    cat_sql = """
        SELECT cat.category_id, cat.name, cat.weight
        FROM Category cat
        JOIN Course co ON cat.course_id=co.course_id
        WHERE co.course_num=? AND co.semester=? AND co.year=?
    """
    categories = conn.execute(cat_sql, (course_num, semester, year)).fetchall()

    # Get student id
    st_row = conn.execute(
        "SELECT student_id FROM Student WHERE first_name=? AND last_name=?",
        (first_name, last_name)
    ).fetchone()
    if not st_row:
        print("Student not found.")
        return None
    sid = st_row["student_id"]

    print(f"\nGrade (drop-lowest) for {first_name} {last_name} in {course_num} ({semester} {year}):")
    total_grade = 0.0

    for cat in categories:
        scores_sql = """
            SELECT s.points, a.max_points
            FROM Score s
            JOIN Assignment a ON s.assignment_id=a.assignment_id
            WHERE a.category_id=? AND s.student_id=?
            ORDER BY (s.points / a.max_points) ASC
        """
        scores = conn.execute(scores_sql, (cat["category_id"], sid)).fetchall()
        if not scores:
            continue

        # Drop the lowest only if more than one score exists
        if len(scores) > 1:
            scores = scores[1:]   # lowest is first (ORDER BY ratio ASC)

        avg_earned = sum(r["points"]     for r in scores) / len(scores)
        avg_max    = sum(r["max_points"] for r in scores) / len(scores)
        pct = (avg_earned / avg_max) * 100 if avg_max else 0
        contribution = (cat["weight"] / 100) * pct
        total_grade += contribution
        dropped = "  [lowest dropped]" if len(scores) >= 1 else ""
        print(f"  {cat['name']:15s} weight={cat['weight']}%  "
              f"score={avg_earned:.2f}/{avg_max:.2f}  "
              f"pct={pct:.2f}%  contribution={contribution:.2f}%{dropped}")

    letter = grade_letter(total_grade)
    print(f"  {'─'*60}")
    print(f"  FINAL GRADE (drop-lowest): {total_grade:.2f}%  ({letter})")
    return total_grade


def grade_letter(pct):
    if pct >= 90: return "A"
    if pct >= 80: return "B"
    if pct >= 70: return "C"
    if pct >= 60: return "D"
    return "F"


# ─────────────────────────────────────────────
#  Main demo / test runner
# ─────────────────────────────────────────────
def main():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    conn = get_connection()

    print("\n" + "="*60)
    print("  TASK 2 – Creating Tables")
    print("="*60)
    create_tables(conn)

    print("\n" + "="*60)
    print("  TASK 2 – Inserting Sample Data")
    print("="*60)
    insert_sample_data(conn)

    print("\n" + "="*60)
    print("  TASK 3 – Show Tables")
    print("="*60)
    show_tables(conn)

    print("\n" + "="*60)
    print("  TASK 4 – Assignment Statistics")
    print("="*60)
    assignment_stats(conn, "Midterm Exam")
    assignment_stats(conn, "HW1 – ER Diagrams")

    print("\n" + "="*60)
    print("  TASK 5 – List Students in a Course")
    print("="*60)
    list_students(conn, "3380", "Fall", 2024)

    print("\n" + "="*60)
    print("  TASK 6 – Students + All Scores")
    print("="*60)
    list_students_scores(conn, "3380", "Fall", 2024)

    print("\n" + "="*60)
    print("  TASK 7 – Add Assignment")
    print("="*60)
    add_assignment(conn, "3380", "Fall", 2024, "Homework", "HW6 – Query Optimization", 100)

    print("\n" + "="*60)
    print("  TASK 8 – Update Category Weights")
    print("="*60)
    update_category_weights(conn, "3380", "Fall", 2024, {
        "Participation": 5.0,
        "Homework":      25.0,
        "Tests":         50.0,
        "Projects":      20.0,
    })

    print("\n" + "="*60)
    print("  TASK 9 – Add 2 Points to All Students")
    print("="*60)
    add_points_all(conn, "Midterm Exam", bonus=2.0)

    print("\n" + "="*60)
    print("  TASK 10 – Add 2 Points to 'Q' Students")
    print("="*60)
    add_points_q_students(conn, "Final Exam", bonus=2.0)
    # Verify
    cur = conn.execute("""
        SELECT st.first_name, st.last_name, s.points
        FROM Score s
        JOIN Student st ON s.student_id=st.student_id
        JOIN Assignment a ON s.assignment_id=a.assignment_id
        WHERE a.title='Final Exam' AND st.last_name LIKE '%Q%'
    """)
    print("  Q-lastname students on Final Exam after bonus:")
    for r in cur.fetchall():
        print(f"    {r['first_name']} {r['last_name']}: {r['points']}")

    print("\n" + "="*60)
    print("  TASK 11 – Compute Final Grade")
    print("="*60)
    compute_grade(conn, "Alice", "Anderson", "3380", "Fall", 2024)
    compute_grade(conn, "Carol", "Chen",     "3380", "Fall", 2024)
    compute_grade(conn, "Frank", "Nguyen",   "3380", "Fall", 2024)

    print("\n" + "="*60)
    print("  TASK 12 – Compute Final Grade (Drop Lowest)")
    print("="*60)
    compute_grade_drop_lowest(conn, "Alice", "Anderson", "3380", "Fall", 2024)
    compute_grade_drop_lowest(conn, "Frank", "Nguyen",   "3380", "Fall", 2024)

    conn.close()
    print("\n✓ All tasks completed. Database saved to:", DB_FILE)


if __name__ == "__main__":
    main()
