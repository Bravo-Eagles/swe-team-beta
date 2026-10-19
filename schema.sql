-- Table definitions for the attendance tracker
-- Every table should use CREATE TABLE IF NOT EXISTS so this
-- file is safe to run every time the app starts


CREATE TABLE IF NOT EXISTS classes (
    class_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL,
    class_name TEXT NOT NULL,
    professor_id TEXT NOT NULL,
    semester TEXT NOT NULL,
    year INTEGER NOT NULL,
    join_code TEXT NOT NULL UNIQUE
);


CREATE TABLE IF NOT EXISTS class_registrations (
    registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL,
    student_id TEXT NOT NULL,
    registered_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (class_id) REFERENCES classes(class_id),
    UNIQUE(class_id, student_id)
);
