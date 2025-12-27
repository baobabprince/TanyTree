import sqlite3


class DatabaseHelper:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS individuals (
                id TEXT PRIMARY KEY,
                name TEXT,
                birth_date TEXT,
                death_date TEXT,
                gender TEXT,
                url TEXT
            )
        """)
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
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO individuals
            (id, name, birth_date, death_date, gender, url)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.get("id"),
            data.get("name"),
            data.get("birth_date"),
            data.get("death_date"),
            data.get("gender"),
            data.get("url")
        ))
        self.conn.commit()

    def get_individual(self, individual_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM individuals WHERE id = ?", (individual_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def add_relationship(self, person_id, related_id, rel_type):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO relationships (person_id, related_id, type)
            VALUES (?, ?, ?)
        """, (person_id, related_id, rel_type))
        self.conn.commit()

    def get_relationships(self, person_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM relationships WHERE person_id = ?", (person_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        self.conn.close()
