"""
Populate database with demo data for testing and demonstration.
Generates 200+ random player records with scores, games, and friendships.
"""

import os
import random
from datetime import datetime, timedelta
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'gaming_leaderboard'),
}

# Demo data
FIRST_NAMES = [
    'Alex', 'Blake', 'Casey', 'Dakota', 'Emma', 'Falcon', 'Ghost', 'Hunter',
    'Iris', 'Jack', 'Kai', 'Logan', 'Maya', 'Nova', 'Oscar', 'Phoenix',
    'Quinn', 'Raven', 'Shadow', 'Tiger', 'Ursa', 'Viper', 'Wolf', 'Xenon',
    'Yuki', 'Zephyr', 'Ace', 'Blade', 'Comet', 'Dragon', 'Echo', 'Frost',
]

LAST_NAMES = [
    'Striker', 'Master', 'Runner', 'Slayer', 'Ninja', 'Warrior', 'Knight',
    'Titan', 'Phoenix', 'Vixen', 'Hawk', 'Eagle', 'Storm', 'Frost', 'Blaze',
    'Thunder', 'Shadow', 'Ghost', 'Reaper', 'Hunter', 'Ranger', 'Scout',
]

BIOS = [
    'Competitive FPS player | 10+ years experience',
    'Speedrunner | World record chaser',
    'Casual gamer | Just here for fun',
    'Esports aspirant | Grinding daily',
    'Retro game enthusiast | Classic arcade fan',
    'Mobile gamer turned console | New to competitive',
    'Streamer | Content creator',
    'Tournament veteran | Multiple championships',
    'Practice makes perfect | Always improving',
    'Social gamer | Love playing with friends',
    'Solo player | High score hunter',
    'Variety gamer | Play everything',
    'Hardcore mode only',
    'Achievement collector',
    'Leaderboard hunter',
]

AVATARS = [
    'https://i.pravatar.cc/150?u=player1',
    'https://i.pravatar.cc/150?u=player2',
    'https://i.pravatar.cc/150?u=player3',
]

def get_db_connection():
    """Connect to PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as err:
        print(f"[ERROR] Database connection failed: {err}")
        return None

def generate_random_username():
    """Generate a random username."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    number = random.randint(1, 999)
    return f"{first}{last}{number}".replace(' ', '')

def populate_players(conn, count=200):
    """Insert random player records."""
    cursor = conn.cursor()
    
    print(f"[•] Inserting {count} players...")
    
    usernames = set()
    players_data = []
    
    # Generate unique usernames
    while len(usernames) < count:
        username = generate_random_username()
        if username not in usernames:
            usernames.add(username)
    
    # Insert players
    try:
        for username in sorted(usernames):
            bio = random.choice(BIOS)
            avatar = f"https://i.pravatar.cc/150?u={username}"
            created_at = datetime.now() - timedelta(days=random.randint(1, 365))
            
            cursor.execute(
                "INSERT INTO players (username, bio, avatar_url, created_at) VALUES (%s, %s, %s, %s) RETURNING player_id",
                (username, bio, avatar, created_at)
            )
            player_id = cursor.fetchone()[0]
            players_data.append((player_id, username))
        
        conn.commit()
        print(f"[✓] Inserted {count} players")
    except Exception as err:
        print(f"[ERROR] Failed to insert players: {err}")
        conn.rollback()
        raise
    
    return players_data

def populate_scores(conn, players_data):
    """Insert random score records."""
    cursor = conn.cursor()
    
    # Get game IDs
    cursor.execute("SELECT game_id FROM games")
    games = [row[0] for row in cursor.fetchall()]
    
    if not games:
        print("[ERROR] No games found in database")
        return
    
    print(f"[•] Inserting scores (5-15 per player)...")
    
    score_count = 0
    try:
        for player_id, _ in players_data:
            # Random number of scores per player (5-15)
            num_scores = random.randint(5, 15)
            
            for _ in range(num_scores):
                game_id = random.choice(games)
                score = random.randint(100, 50000)
                timestamp = datetime.now() - timedelta(days=random.randint(0, 90))
                
                cursor.execute(
                    "INSERT INTO scores (player_id, game_id, score, timestamp) VALUES (%s, %s, %s, %s)",
                    (player_id, game_id, score, timestamp)
                )
                score_count += 1
        
        conn.commit()
        print(f"[✓] Inserted {score_count} score records")
    except Exception as err:
        print(f"[ERROR] Failed to insert scores: {err}")
        conn.rollback()
        raise

def populate_friendships(conn, players_data):
    """Insert random friendship records."""
    cursor = conn.cursor()
    
    print(f"[•] Creating friendships...")
    
    player_ids = [p[0] for p in players_data]
    friendship_count = 0
    
    try:
        # Create random friendships
        # Each player gets 3-8 friends on average
        for player_id in player_ids:
            num_friends = random.randint(3, 8)
            potential_friends = [f for f in player_ids if f != player_id]
            friends = random.sample(potential_friends, min(num_friends, len(potential_friends)))
            
            for friend_id in friends:
                try:
                    # Insert bidirectional friendship
                    cursor.execute(
                        "INSERT INTO friends (user_id, friend_id) VALUES (%s, %s)",
                        (player_id, friend_id)
                    )
                    friendship_count += 1
                except psycopg2.IntegrityError:
                    # Friendship already exists, skip
                    conn.rollback()
                    conn.begin()
        
        conn.commit()
        print(f"[✓] Created {friendship_count} friendships")
    except Exception as err:
        print(f"[ERROR] Failed to create friendships: {err}")
        conn.rollback()
        raise

def get_stats(conn):
    """Print database statistics."""
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM players")
    player_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM scores")
    score_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM friends")
    friend_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM games")
    game_count = cursor.fetchone()[0]
    
    print(".".center(65, "="))
    print(f"│ Players:    {player_count:6d}".ljust(64) + "│")
    print(f"│ Games:      {game_count:6d}".ljust(64) + "│")
    print(f"│ Scores:     {score_count:6d}".ljust(64) + "│")
    print(f"│ Friendships: {friend_count:6d}".ljust(64) + "│")
    print("'".center(65, "="))

def main():
    print()
    print("╔" + "═" * 63 + "╗")
    print("║" + " Demo Data Population Script".center(63) + "║")
    print("╚" + "═" * 63 + "╝")
    print()
    
    # Connect to database
    print("[•] Connecting to database...")
    conn = get_db_connection()
    if not conn:
        print("[ERROR] Could not connect to database")
        return
    print("[✓] Connected successfully")
    print()
    
    try:
        # Populate data
        players = populate_players(conn, count=200)
        populate_scores(conn, players)
        populate_friendships(conn, players)
        
        print()
        print("Database Statistics:".center(65))
        get_stats(conn)
        
        print()
        print("[✓] Database population complete!")
        print()
        
    except Exception as err:
        print(f"[ERROR] Population failed: {err}")
        conn.rollback()
    finally:
        conn.close()
        print("[•] Database connection closed")

if __name__ == "__main__":
    main()
