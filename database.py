
import json
import sqlite3
from pathlib import Path

# Paths relative to this Python file
BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
DATABASE_PATH = BASE_DIR / "data" / "greenlight.db"


def connect_db():
    """Connect to the SQLite database."""
    DATABASE_PATH.parent.mkdir(exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def create_tables():
    """Create the database tables if needed."""
    with connect_db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS discoveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                description TEXT,
                evidence_strength TEXT,
                research_date TEXT,
                source_file TEXT NOT NULL,
                details_json TEXT NOT NULL,
                UNIQUE(source_file, name)
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discovery_id INTEGER NOT NULL,
                platform TEXT,
                url TEXT NOT NULL,
                relevance TEXT,
                FOREIGN KEY (discovery_id)
                    REFERENCES discoveries(id)
            )
        """)

    print("Database tables are ready.")


def import_results():
    """Import all Scout JSON files into SQLite."""
    json_files = sorted(RESULTS_DIR.glob("*.json"))

    if not json_files:
        print("No JSON files found in results/")
        return

    with connect_db() as connection:
        for file_path in json_files:
            with open(file_path, encoding="utf-8") as file:
                data = json.load(file)

            discoveries = data.get("discoveries", [])

            # Example: scout_2026-10-30.json
            research_date = file_path.stem.replace("scout_", "")[:10]

            for discovery in discoveries:
                name = discovery["name"]

                # Skip discoveries already imported from this file
                existing = connection.execute(
                    """
                    SELECT id FROM discoveries
                    WHERE source_file = ? AND name = ?
                    """,
                    (file_path.name, name)
                ).fetchone()

                if existing:
                    continue

                cursor = connection.execute(
                    """
                    INSERT INTO discoveries (
                        name,
                        category,
                        description,
                        evidence_strength,
                        research_date,
                        source_file,
                        details_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        discovery.get("category"),
                        discovery.get("description"),
                        discovery.get("evidence_strength"),
                        research_date,
                        file_path.name,
                        json.dumps(discovery)
                    )
                )

                discovery_id = cursor.lastrowid

                for source in discovery.get("sources", []):
                    connection.execute(
                        """
                        INSERT INTO sources (
                            discovery_id,
                            platform,
                            url,
                            relevance
                        )
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            discovery_id,
                            source.get("platform"),
                            source.get("url"),
                            source.get("relevance")
                        )
                    )

            print(f"Processed {file_path.name}")

    print("Import complete.")


def show_discoveries():
    """Display saved discoveries."""
    with connect_db() as connection:
        rows = connection.execute("""
            SELECT
                d.id,
                d.name,
                d.category,
                d.research_date,
                COUNT(s.id) AS source_count
            FROM discoveries d
            LEFT JOIN sources s
                ON s.discovery_id = d.id
            GROUP BY d.id
            ORDER BY d.research_date DESC, d.id DESC
        """).fetchall()

    print(f"\n{len(rows)} discoveries in database:\n")

    for row in rows:
        print(
            f"{row['id']}. {row['name']} "
            f"({row['category'] or 'Uncategorized'}) "
            f"— {row['source_count']} sources"
        )


def create_report_table():
    """Create a table for Cultural Intelligence Reports."""

    with connect_db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS research_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                research_request TEXT NOT NULL,
                research_approach TEXT,
                summary TEXT,
                research_date TEXT,
                report_json TEXT NOT NULL
            )
        """)


def save_report(report):
    """Save a complete Scout report to SQLite."""

    with connect_db() as connection:
        cursor = connection.execute("""
            INSERT INTO research_reports (
                research_request,
                research_approach,
                summary,
                research_date,
                report_json
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            report.get("research_request", ""),
            report.get("research_approach", ""),
            report.get("summary", ""),
            report.get("research_date", ""),
            json.dumps(report, ensure_ascii=False)
        ))

        return cursor.lastrowid


def get_reports():
    """Retrieve reports, newest first."""

    with connect_db() as connection:
        rows = connection.execute("""
            SELECT *
            FROM research_reports
            ORDER BY id DESC
        """).fetchall()

    return [dict(row) for row in rows]


if __name__ == "__main__":
    create_tables()
    import_results()
    show_discoveries()
    create_report_table()
    save_report()
    get_reports()

    
