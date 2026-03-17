-- ============================================================
-- Gaming Leaderboard System — Database Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS gaming_leaderboard;
USE gaming_leaderboard;

-- ─── Players ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS players (
    player_id   INT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(50)  UNIQUE NOT NULL,
    avatar_url  VARCHAR(255) DEFAULT NULL,
    bio         VARCHAR(255) DEFAULT NULL,
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- ─── Games ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS games (
    game_id     INT AUTO_INCREMENT PRIMARY KEY,
    title       VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

-- ─── Scores (Audit Log) ─────────────────────────────────────
-- Every game completion is recorded here.
-- This is the single source of truth for all rankings.
CREATE TABLE IF NOT EXISTS scores (
    score_id    INT AUTO_INCREMENT PRIMARY KEY,
    player_id   INT       NOT NULL,
    game_id     INT       NOT NULL,
    score       INT       NOT NULL CHECK (score >= 0),
    timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(player_id) ON DELETE CASCADE,
    FOREIGN KEY (game_id)  REFERENCES games(game_id)     ON DELETE CASCADE
);

-- ─── Friends ─────────────────────────────────────────────────
-- Bidirectional friendship: insert (A,B) AND (B,A).
CREATE TABLE IF NOT EXISTS friends (
    user_id     INT NOT NULL,
    friend_id   INT NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, friend_id),
    FOREIGN KEY (user_id)   REFERENCES players(player_id) ON DELETE CASCADE,
    FOREIGN KEY (friend_id) REFERENCES players(player_id) ON DELETE CASCADE
);

-- ─── Performance Indexes ─────────────────────────────────────
-- Fast top-N with tie-breaking (highest score first, earliest timestamp first)
CREATE INDEX idx_score_desc      ON scores (score DESC, timestamp ASC);
-- Fast per-player lookups
CREATE INDEX idx_player_game     ON scores (player_id, game_id, score);
-- Fast time-range queries
CREATE INDEX idx_timestamp       ON scores (timestamp);
-- Fast friend lookups
CREATE INDEX idx_friend_lookup   ON friends (user_id, friend_id);

-- ─── Seed Data ───────────────────────────────────────────────
INSERT IGNORE INTO players (username, bio) VALUES
    ('GamerX',       'FPS veteran. 10 years of grinding.'),
    ('NoobMaster99',  'Just started. Watch me climb.'),
    ('ProSlayer',     'Competitive esports player.'),
    ('SpeedRunner',   'World record chaser.');

INSERT IGNORE INTO games (title, description) VALUES
    ('Space Invaders', 'Classic arcade shooter'),
    ('Doom Eternal',   'Fast-paced FPS action'),
    ('Tetris',         'Puzzle matching game');

INSERT INTO scores (player_id, game_id, score) VALUES
    (1, 1, 15000), (2, 1, 8000),  (3, 1, 22000), (4, 1, 35000),
    (1, 2, 45000), (3, 2, 80000),
    (2, 3, 5000),  (4, 3, 12000);

-- Seed friendships (bidirectional)
INSERT IGNORE INTO friends (user_id, friend_id) VALUES
    (1, 2), (2, 1),
    (1, 3), (3, 1),
    (2, 4), (4, 2);
