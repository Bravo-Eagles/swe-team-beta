-- Table definitions for the attendance tracker
-- Every table should use CREATE TABLE IF NOT EXISTS so this
-- file is safe to run every time the app starts

-- Account Table
CREATE TABLE IF NOT EXISTS accounts(
    id INTEGER PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL DEFAULT('STUDENT')
);

--Login Sessions
CREATE TABLE IF NOT EXISTS sessions(
    token_hash TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES accounts(id) ON DELETE CASCADE,
    expires TEXT NOT NULL
);

-- Teacher Account
CREATE TABLE IF NOT EXISTS teacher(
    id BIGINT PRIMARY KEY,
    first_name VARCHAR(70) NOT NULL,
    middle_name VARCHAR(70),
    last_name VARCHAR(70) NOT NULL,
    account_id NOT NULL REFERENCES accounts(id)
);

-- Student Account
CREATE TABLE IF NOT EXISTS student(
    id BIGINT PRIMARY KEY,
    first_name VARCHAR(70) NOT NULL,
    middle_name VARCHAR(70),
    last_name VARCHAR(70) NOT NULL,
    account_id NOT NULL REFERENCES accounts(id),
    active TINYINT NOT NULL
);

-- A class that could exist
CREATE TABLE IF NOT EXISTS class(
    id BIGINT PRIMARY KEY,
    name VARCHAR(70) NOT NULL,
    course_id VARCHAR(10) NOT NULL
);

-- A class that is taught
CREATE TABLE IF NOT EXISTS teaching(
    id BIGINT PRIMARY KEY,
    teacher_id BIGINT NOT NULL REFERENCES teacher(id),
    class_id BIGINT NOT NULL REFERENCES class(id),
    semester VARCHAR(8) NOT NULL,
    year INT NOT NULL
);

-- When a class is scheduled to be taught
CREATE TABLE IF NOT EXISTS scheduled(
    id BIGINT PRIMARY KEY,
    teaching_id BIGINT NOT NULL REFERENCES teaching(id),
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME
);

-- When a student is enrolled in a course
CREATE TABLE IF NOT EXISTS enrolled(
    teaching_id BIGINT NOT NULL REFERENCES teaching(id),
    student_id BIGINT NOT NULL REFERENCES student(id),
    PRIMARY KEY (teaching_id, student_id)
);

-- When a class is attended by a student
CREATE TABLE IF NOT EXISTS attendance(
    scheduled_id BIGINT NOT NULL REFERENCES scheduled(id),
    student_id BIGINT NOT NULL REFERENCES student(id),
    check_in_time DATE NOT NULL,
    is_delted BOOLEAN NOT NULL DEFAULT 0,
    PRIMARY KEY (scheduled_id, student_id)
);
