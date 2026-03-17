"""
app.py — Flask backend for the Gaming Leaderboard System.
Provides HTML views and JSON API endpoints for leaderboard features.
"""

import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super_secret_gaming_key_2026")

# ────────────────────────────────────────────────────────────────
# Database helper
# ────────────────────────────────────────────────────────────────

def get_db():
    """Return a MySQL connection or None."""
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "gaming_leaderboard"),
        )
    except mysql.connector.Error as err:
        print(f"[DB ERROR] {err}")
        return None


def _period_filter(period: str) -> str:
    """Return a SQL WHERE clause fragment for the requested time period."""
    mapping = {
        "daily": "AND s.timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY)",
        "weekly": "AND s.timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)",
        "monthly": "AND s.timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)",
    }
    return mapping.get(period, "")  # 'all' or unknown → no filter


# ────────────────────────────────────────────────────────────────
# HTML Views
# ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Main leaderboard page."""
    conn = get_db()
    if not conn:
        flash("Could not connect to database. Please run schema.sql and check credentials.", "error")
        return render_template("index.html", scores=[])

    cursor = conn.cursor(dictionary=True)

    # Global top scores — one row per player (their best single score)
    query = """
        SELECT p.username, g.title AS game, best.score, best.timestamp
        FROM players p
        JOIN (
            SELECT s.player_id, s.game_id, s.score, s.timestamp
            FROM scores s
            INNER JOIN (
                SELECT player_id, MAX(score) AS max_score
                FROM scores
                GROUP BY player_id
            ) mx ON s.player_id = mx.player_id AND s.score = mx.max_score
            GROUP BY s.player_id
        ) best ON p.player_id = best.player_id
        JOIN games g ON best.game_id = g.game_id
        ORDER BY best.score DESC, best.timestamp ASC
        LIMIT 50
    """
    cursor.execute(query)
    scores = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template("index.html", scores=scores)


@app.route("/add", methods=["GET", "POST"])
def add_score():
    """Submit a new score (anti-cheat: only via server-side form POST)."""
    conn = get_db()
    if not conn:
        flash("Could not connect to database.", "error")
        return redirect(url_for("index"))

    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        game_id = request.form.get("game_id")
        score_str = request.form.get("score", "")

        if not username:
            flash("Username cannot be empty!", "error")
            return redirect(url_for("add_score"))

        try:
            score = int(score_str)
            if score < 0:
                raise ValueError
        except (ValueError, TypeError):
            flash("Invalid score. Please enter a non-negative number.", "error")
            return redirect(url_for("add_score"))

        try:
            # Ensure player exists
            cursor.execute("SELECT player_id FROM players WHERE username = %s", (username,))
            player = cursor.fetchone()
            if not player:
                cursor.execute("INSERT INTO players (username) VALUES (%s)", (username,))
                conn.commit()
                player_id = cursor.lastrowid
            else:
                player_id = player["player_id"]

            # Insert score
            cursor.execute(
                "INSERT INTO scores (player_id, game_id, score) VALUES (%s, %s, %s)",
                (player_id, game_id, score),
            )
            conn.commit()
            flash("Score added successfully!", "success")
            return redirect(url_for("index"))

        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")
            conn.rollback()

    # GET — load games for dropdown
    cursor.execute("SELECT game_id, title FROM games ORDER BY title")
    games = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("add_score.html", games=games)


@app.route("/profile/<username>")
def profile(username):
    """Player profile page with detailed stats."""
    conn = get_db()
    if not conn:
        flash("Could not connect to database.", "error")
        return redirect(url_for("index"))

    cursor = conn.cursor(dictionary=True)

    # Player info
    cursor.execute("SELECT * FROM players WHERE username = %s", (username,))
    player = cursor.fetchone()
    if not player:
        flash("Player not found.", "error")
        cursor.close()
        conn.close()
        return redirect(url_for("index"))

    # Stats: total points, games played, global rank, percentile
    cursor.execute("""
        WITH PlayerTotals AS (
            SELECT
                p.player_id,
                p.username,
                COALESCE(SUM(mx.best), 0) AS total_points
            FROM players p
            LEFT JOIN (
                SELECT player_id, game_id, MAX(score) AS best
                FROM scores GROUP BY player_id, game_id
            ) mx ON p.player_id = mx.player_id
            GROUP BY p.player_id, p.username
        ),
        Ranked AS (
            SELECT *,
                RANK() OVER (ORDER BY total_points DESC) AS global_rank,
                PERCENT_RANK() OVER (ORDER BY total_points DESC) AS pct_rank
            FROM PlayerTotals
        )
        SELECT * FROM Ranked WHERE player_id = %s
    """, (player["player_id"],))
    stats = cursor.fetchone()

    # Games played count
    cursor.execute(
        "SELECT COUNT(DISTINCT game_id) AS games_played FROM scores WHERE player_id = %s",
        (player["player_id"],),
    )
    gp = cursor.fetchone()

    # Total submissions
    cursor.execute(
        "SELECT COUNT(*) AS total_submissions FROM scores WHERE player_id = %s",
        (player["player_id"],),
    )
    ts = cursor.fetchone()

    # Recent scores
    cursor.execute("""
        SELECT g.title AS game, s.score, s.timestamp
        FROM scores s
        JOIN games g ON s.game_id = g.game_id
        WHERE s.player_id = %s
        ORDER BY s.timestamp DESC
        LIMIT 20
    """, (player["player_id"],))
    recent_scores = cursor.fetchall()

    # Friend count
    cursor.execute(
        "SELECT COUNT(*) AS friend_count FROM friends WHERE user_id = %s",
        (player["player_id"],),
    )
    fc = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "profile.html",
        player=player,
        stats=stats,
        games_played=gp["games_played"] if gp else 0,
        total_submissions=ts["total_submissions"] if ts else 0,
        recent_scores=recent_scores,
        friend_count=fc["friend_count"] if fc else 0,
    )


# ────────────────────────────────────────────────────────────────
# JSON API Endpoints
# ────────────────────────────────────────────────────────────────

@app.route("/api/rankings")
def api_rankings():
    """
    Global top-100 leaderboard.
    Query params:
      ?period=daily|weekly|monthly|all (default: all)
      ?limit=N (default: 100)
    Tie-breaking: same score → earlier timestamp ranks higher.
    """
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    period = request.args.get("period", "all")
    limit = min(int(request.args.get("limit", 100)), 500)
    time_filter = _period_filter(period)

    cursor = conn.cursor(dictionary=True)
    query = f"""
        SELECT
            p.player_id,
            p.username,
            SUM(mx.best) AS total_points,
            MIN(mx.earliest) AS first_achieved
        FROM players p
        JOIN (
            SELECT player_id, game_id,
                   MAX(score) AS best,
                   MIN(timestamp) AS earliest
            FROM scores s
            WHERE 1=1 {time_filter}
            GROUP BY player_id, game_id
        ) mx ON p.player_id = mx.player_id
        GROUP BY p.player_id, p.username
        ORDER BY total_points DESC, first_achieved ASC
        LIMIT %s
    """
    cursor.execute(query, (limit,))
    rankings = cursor.fetchall()

    # Serialize datetime
    for r in rankings:
        if r.get("first_achieved"):
            r["first_achieved"] = r["first_achieved"].isoformat()

    cursor.close()
    conn.close()
    return jsonify({"rankings": rankings, "period": period, "timestamp": datetime.now().isoformat()})


@app.route("/api/rankings/nearby/<username>")
def api_rankings_nearby(username):
    """
    "Near Me" — returns 3 players above, the target player, and 3 below.
    Uses ?period= query param for time filtering.
    """
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    period = request.args.get("period", "all")
    time_filter = _period_filter(period)

    cursor = conn.cursor(dictionary=True)
    query = f"""
        WITH RankedPlayers AS (
            SELECT
                p.player_id,
                p.username,
                SUM(mx.best) AS total_points,
                RANK() OVER (ORDER BY SUM(mx.best) DESC, MIN(mx.earliest) ASC) AS player_rank
            FROM players p
            JOIN (
                SELECT player_id, game_id,
                       MAX(score) AS best,
                       MIN(timestamp) AS earliest
                FROM scores s
                WHERE 1=1 {time_filter}
                GROUP BY player_id, game_id
            ) mx ON p.player_id = mx.player_id
            GROUP BY p.player_id, p.username
        )
        SELECT * FROM RankedPlayers
    """
    cursor.execute(query)
    all_ranked = cursor.fetchall()
    cursor.close()
    conn.close()

    # Find target
    target_idx = None
    for i, p in enumerate(all_ranked):
        if p["username"].lower() == username.lower():
            target_idx = i
            break

    if target_idx is None:
        return jsonify({"error": "User not found in rankings", "rankings": []}), 404

    start = max(0, target_idx - 3)
    end = min(len(all_ranked), target_idx + 4)
    nearby = all_ranked[start:end]

    # Convert Decimals for JSON
    for r in nearby:
        r["total_points"] = int(r["total_points"])
        r["player_rank"] = int(r["player_rank"])

    return jsonify({
        "rankings": nearby,
        "target_user": username,
        "target_rank": int(all_ranked[target_idx]["player_rank"]),
        "total_players": len(all_ranked),
        "timestamp": datetime.now().isoformat(),
    })


@app.route("/api/rankings/friends/<username>")
def api_rankings_friends(username):
    """Friend-only leaderboard for a given user."""
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    period = request.args.get("period", "all")
    time_filter = _period_filter(period)

    cursor = conn.cursor(dictionary=True)

    # Get the player's ID
    cursor.execute("SELECT player_id FROM players WHERE username = %s", (username,))
    player = cursor.fetchone()
    if not player:
        cursor.close()
        conn.close()
        return jsonify({"error": "User not found", "rankings": []}), 404

    pid = player["player_id"]

    query = f"""
        SELECT
            p.player_id,
            p.username,
            SUM(mx.best) AS total_points
        FROM players p
        JOIN (
            SELECT player_id, game_id, MAX(score) AS best
            FROM scores s
            WHERE 1=1 {time_filter}
            GROUP BY player_id, game_id
        ) mx ON p.player_id = mx.player_id
        WHERE p.player_id IN (
            SELECT friend_id FROM friends WHERE user_id = %s
        ) OR p.player_id = %s
        GROUP BY p.player_id, p.username
        ORDER BY total_points DESC
    """
    cursor.execute(query, (pid, pid))
    rankings = cursor.fetchall()

    # Convert Decimal
    for r in rankings:
        r["total_points"] = int(r["total_points"])

    cursor.close()
    conn.close()
    return jsonify({
        "rankings": rankings,
        "target_user": username,
        "timestamp": datetime.now().isoformat(),
    })


@app.route("/api/player/<username>")
def api_player_stats(username):
    """Individual player stats: rank, percentile, total points, games played."""
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        WITH PlayerTotals AS (
            SELECT
                p.player_id,
                p.username,
                COALESCE(SUM(mx.best), 0) AS total_points
            FROM players p
            LEFT JOIN (
                SELECT player_id, game_id, MAX(score) AS best
                FROM scores GROUP BY player_id, game_id
            ) mx ON p.player_id = mx.player_id
            GROUP BY p.player_id, p.username
        ),
        Ranked AS (
            SELECT *,
                RANK() OVER (ORDER BY total_points DESC) AS global_rank,
                ROUND(PERCENT_RANK() OVER (ORDER BY total_points ASC) * 100, 1) AS percentile
            FROM PlayerTotals
        )
        SELECT * FROM Ranked WHERE LOWER(username) = LOWER(%s)
    """, (username,))
    stats = cursor.fetchone()

    if not stats:
        cursor.close()
        conn.close()
        return jsonify({"error": "Player not found"}), 404

    # Additional stats
    cursor.execute(
        "SELECT COUNT(DISTINCT game_id) AS games_played, COUNT(*) AS total_submissions "
        "FROM scores WHERE player_id = %s",
        (stats["player_id"],),
    )
    extra = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify({
        "username": stats["username"],
        "total_points": int(stats["total_points"]),
        "global_rank": int(stats["global_rank"]),
        "percentile": float(stats["percentile"]),
        "games_played": extra["games_played"] if extra else 0,
        "total_submissions": extra["total_submissions"] if extra else 0,
    })


# ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
