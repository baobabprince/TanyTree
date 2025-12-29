import sqlite3
import threading


class DatabaseHelper:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS individuals (
                id TEXT PRIMARY KEY,
                name TEXT,
                first_name TEXT,
                last_name TEXT,
                prefix TEXT,
                suffix TEXT,
                birth_date TEXT,
                birth_date_civil TEXT,
                birth_place TEXT,
                death_date TEXT,
                death_date_civil TEXT,
                death_place TEXT,
                gender TEXT,
                url TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS discovered_urls (
                id TEXT PRIMARY KEY,
                url TEXT
            )
        """)

        # Ensure all columns exist (simple migration)
        cursor.execute("PRAGMA table_info(individuals)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        required_columns = [
            ("birth_date_civil", "TEXT"),
            ("death_date_civil", "TEXT"),
            ("first_name", "TEXT"),
            ("last_name", "TEXT"),
            ("prefix", "TEXT"),
            ("suffix", "TEXT"),
        ]
        for col_name, col_type in required_columns:
            if col_name not in existing_columns:
                cursor.execute(f"ALTER TABLE individuals ADD COLUMN {col_name} {col_type}")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                person_id TEXT,
                related_id TEXT,
                type TEXT,
                PRIMARY KEY (person_id, related_id, type)
            )
        """)
        self.conn.commit()

    def add_individual(self, data):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO individuals
                (id, name, first_name, last_name, prefix, suffix, birth_date, birth_date_civil, birth_place, death_date, death_date_civil, death_place, gender, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get("id"),
                data.get("name"),
                data.get("first_name"),
                data.get("last_name"),
                data.get("prefix"),
                data.get("suffix"),
                data.get("birth_date"),
                data.get("birth_date_civil"),
                data.get("birth_place"),
                data.get("death_date"),
                data.get("death_date_civil"),
                data.get("death_place"),
                data.get("gender"),
                data.get("url")
            ))
            self.conn.commit()

    def get_individual(self, individual_id):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM individuals WHERE id = ?", (individual_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_relationship(self, person_id, related_id, rel_type):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO relationships (person_id, related_id, type)
                VALUES (?, ?, ?)
            """, (person_id, related_id, rel_type))
            self.conn.commit()

    def get_relationships(self, person_id):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM relationships WHERE person_id = ?", (person_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_all_ids(self):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM individuals")
            return [row[0] for row in cursor.fetchall()]

    def add_discovered_url(self, person_id, url):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO discovered_urls (id, url)
                VALUES (?, ?)
            """, (person_id, url))
            self.conn.commit()

    def get_pending_urls(self):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT d.id, d.url 
                FROM discovered_urls d
                LEFT JOIN individuals i ON d.id = i.id
                WHERE i.id IS NULL
            """)
            return [dict(row) for row in cursor.fetchall()]

    def close(self):
        self.conn.close()
