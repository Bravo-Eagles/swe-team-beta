-- Table definitions for the attendance tracker
-- Every table should use CREATE TABLE IF NOT EXISTS so this
-- file is safe to run every time the app starts

--Primary key means student_id must be unique, only exist once
--Text is sql data type, store column as a string
--create student table
CREATE TABLE IF NOT EXISTS students(
        student_id TEXT PRIMARY KEY, --defines column in students table, 
        first_name TEXT NOT NULL, --not null mean column is required to have a value
        last_name TEXT NOT NULL, --column for last name
        course TEXT NOT NULL --course column must have a value, 
);

CREATE TABLE IF NOT EXISTS teachers(
    teacher_id TEXT PRIMARY KEY,
    first_name  TEXT NOT NULL,
    last_name   TEXT NOT NULL

);

-- Create user accounts for students and teachers
CREATE TABLE IF NOT EXISTS users ( --stores account info for both students and teachers
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('student', 'teacher'))
);