-- Database Schema for Nutrition App
-- Run this in Supabase SQL Editor or via psql

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    age INTEGER NOT NULL,
    sex VARCHAR(10) NOT NULL,
    height_cm NUMERIC NOT NULL,
    weight_kg NUMERIC NOT NULL,
    activity_level VARCHAR(20) DEFAULT 'moderate',
    goal VARCHAR(20) DEFAULT 'maintain',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Food table
CREATE TABLE IF NOT EXISTS food (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    calories NUMERIC NOT NULL,
    protein NUMERIC NOT NULL,
    carbs NUMERIC NOT NULL,
    fat NUMERIC NOT NULL,
    serving_unit VARCHAR(50) DEFAULT 'g',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User intake table
CREATE TABLE IF NOT EXISTS user_intake (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    food_id INTEGER NOT NULL REFERENCES food(id) ON DELETE CASCADE,
    quantity NUMERIC NOT NULL,
    intake_date DATE NOT NULL,
    meal_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_intake_user_id ON user_intake(user_id);
CREATE INDEX IF NOT EXISTS idx_user_intake_date ON user_intake(intake_date);
CREATE INDEX IF NOT EXISTS idx_food_name ON food(name);

-- Add comments
COMMENT ON TABLE users IS 'User profiles and authentication';
COMMENT ON TABLE food IS 'Food items with nutrition data';
COMMENT ON TABLE user_intake IS 'User food intake logs';




