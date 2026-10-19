PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    age INTEGER CHECK (age IS NULL OR age BETWEEN 13 AND 110),
    height_cm REAL CHECK (height_cm IS NULL OR height_cm BETWEEN 80 AND 250),
    weight_kg REAL CHECK (weight_kg IS NULL OR weight_kg BETWEEN 20 AND 400),
    fitness_level TEXT NOT NULL DEFAULT 'beginner' CHECK (fitness_level IN ('beginner', 'intermediate', 'advanced')),
    goal TEXT,
    weekly_frequency INTEGER CHECK (weekly_frequency IS NULL OR weekly_frequency BETWEEN 1 AND 7),
    location TEXT,
    equipment TEXT,
    limitations TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    instructions TEXT NOT NULL,
    equipment TEXT,
    difficulty TEXT NOT NULL DEFAULT 'beginner',
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);
CREATE TABLE IF NOT EXISTS training_plans (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    goal TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived'))
);
CREATE TABLE IF NOT EXISTS plan_exercises (
    id INTEGER PRIMARY KEY,
    plan_id INTEGER NOT NULL REFERENCES training_plans(id) ON DELETE CASCADE,
    exercise_id INTEGER NOT NULL REFERENCES exercises(id),
    day_number INTEGER NOT NULL CHECK (day_number BETWEEN 1 AND 7),
    position INTEGER NOT NULL CHECK (position > 0),
    sets INTEGER NOT NULL CHECK (sets > 0),
    repetitions TEXT NOT NULL,
    rest_seconds INTEGER NOT NULL DEFAULT 60 CHECK (rest_seconds >= 0),
    UNIQUE (plan_id, day_number, position)
);
CREATE TABLE IF NOT EXISTS workout_sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id INTEGER REFERENCES training_plans(id) ON DELETE SET NULL,
    scheduled_date TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    status TEXT NOT NULL DEFAULT 'planned' CHECK (status IN ('planned', 'in_progress', 'completed', 'incomplete')),
    notes TEXT
);
CREATE TABLE IF NOT EXISTS workout_results (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    plan_exercise_id INTEGER REFERENCES plan_exercises(id) ON DELETE SET NULL,
    exercise_id INTEGER NOT NULL REFERENCES exercises(id),
    set_number INTEGER NOT NULL CHECK (set_number > 0),
    repetitions_done INTEGER CHECK (repetitions_done IS NULL OR repetitions_done >= 0),
    weight_kg REAL CHECK (weight_kg IS NULL OR weight_kg >= 0),
    notes TEXT
);
CREATE TABLE IF NOT EXISTS body_measurements (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    measured_on TEXT NOT NULL,
    height_cm REAL,
    weight_kg REAL,
    notes TEXT,
    CHECK (height_cm IS NOT NULL OR weight_kg IS NOT NULL)
);
CREATE TABLE IF NOT EXISTS daily_habits (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    entry_date TEXT NOT NULL,
    water_ml INTEGER NOT NULL DEFAULT 0 CHECK (water_ml >= 0),
    steps INTEGER NOT NULL DEFAULT 0 CHECK (steps >= 0),
    UNIQUE (user_id, entry_date)
);
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_plans_user ON training_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_date ON workout_sessions(user_id, scheduled_date);
CREATE INDEX IF NOT EXISTS idx_habits_user_date ON daily_habits(user_id, entry_date);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
