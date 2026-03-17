"""
populate_db.py — Seed the gaming_leaderboard database with 200 realistic
players, random scores across games, and friend relationships.
"""

import os
import random
from datetime import datetime, timedelta

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# ── Realistic gamer-tag fragments ────────────────────────────
PREFIXES = [
    "Shadow", "Dark", "Blaze", "Ice", "Storm", "Neo", "Cyber", "Nova",
    "Phantom", "Ghost", "Venom", "Titan", "Iron", "Fury", "Void",
    "Alpha", "Omega", "Hyper", "Neon", "Pixel", "Rogue", "Apex",
    "Turbo", "Ultra", "Savage", "Frost", "Thunder", "Crimson", "Mystic",
    "Silent", "Rapid", "Solar", "Lunar", "Cosmic", "Atomic", "Quantum",
]
SUFFIXES = [
    "Hunter", "Slayer", "Knight", "Ninja", "Sniper", "Raider", "Wolf",
    "Hawk", "Viper", "Dragon", "Phoenix", "Reaper", "Mage", "Tank",
    "Ace", "King", "Lord", "Bolt", "Fang", "Claw", "Blade", "Strike",
    "Flame", "Surge", "Drift", "Core", "Byte", "Glitch", "Spark", "Pulse",
]
BIOS = [
    "Born to game.", "Competitive FPS grinder.", "Speedrun enthusiast.",
    "Casual gamer, hardcore heart.", "Esports hopeful.",
    "Night owl gamer.", "Strategy mastermind.", "Achievement hunter.",
    "Stream sniping since 2020.", "Controller > Keyboard.",
    "Top 1% in ranked.", "Battle royale legend.", "Puzzle solver.",
    None, None, None,  # some players have no bio
]


def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "gaming_leaderboard"),
        )
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        return None


def random_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def populate_database(num_players: int = 200):
    conn = get_db_connection()
    if not conn:
        print("Could not connect. Aborting.")
        return

    cursor = conn.cursor()

    try:
        # ── Verify games exist ────────────────────────────────
        cursor.execute("SELECT game_id FROM games")
        games = cursor.fetchall()
        if not games:
            print("No games found! Please run schema.sql first.")
            return
        game_ids = [g[0] for g in games]

        # ── Generate players ──────────────────────────────────
        print(f"Inserting {num_players} players...")
        used_names: set[str] = set()
        players_data = []
        for _ in range(num_players):
            while True:
                name = f"{random.choice(PREFIXES)}{random.choice(SUFFIXES)}{random.randint(1, 999)}"
                if name not in used_names:
                    used_names.add(name)
                    break
            bio = random.choice(BIOS)
            players_data.append((name, bio))

        cursor.executemany(
            "INSERT IGNORE INTO players (username, bio) VALUES (%s, %s)",
            players_data,
        )
        conn.commit()

        # ── Fetch all player IDs ──────────────────────────────
        cursor.execute("SELECT player_id FROM players")
        player_ids = [p[0] for p in cursor.fetchall()]

        # ── Generate scores ───────────────────────────────────
        now = datetime.now()
        start_date = now - timedelta(days=365)
        scores_data = []

        print(f"Generating scores for {len(player_ids)} players across {len(game_ids)} games...")
        for p_id in player_ids:
            num_scores = random.randint(1, 5)
            for _ in range(num_scores):
                g_id = random.choice(game_ids)
                score = random.randint(10, 1000) * 100  # 1 000 – 100 000
                ts = random_date(start_date, now)
                scores_data.append(
                    (p_id, g_id, score, ts.strftime("%Y-%m-%d %H:%M:%S"))
                )

        cursor.executemany(
            "INSERT INTO scores (player_id, game_id, score, timestamp) VALUES (%s, %s, %s, %s)",
            scores_data,
        )
        conn.commit()

        # ── Generate friendships ──────────────────────────────
        print("Creating random friendships...")
        friendships: set[tuple[int, int]] = set()
        for p_id in player_ids:
            num_friends = random.randint(0, 8)
            potential = [x for x in player_ids if x != p_id]
            chosen = random.sample(potential, min(num_friends, len(potential)))
            for f_id in chosen:
                pair = (min(p_id, f_id), max(p_id, f_id))
                if pair not in friendships:
                    friendships.add(pair)

        friend_rows = []
        for a, b in friendships:
            friend_rows.append((a, b))
            friend_rows.append((b, a))

        if friend_rows:
            cursor.executemany(
                "INSERT IGNORE INTO friends (user_id, friend_id) VALUES (%s, %s)",
                friend_rows,
            )
            conn.commit()

        print(
            f"Done! Inserted {len(players_data)} players, "
            f"{len(scores_data)} scores, "
            f"{len(friendships)} friendships."
        )

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    populate_database(200)
