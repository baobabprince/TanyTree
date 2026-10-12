"""Offline enrichment: gender inference, relationship canonicalization, orphan discovery, quality report."""

from urllib.parse import urlparse, urlunparse, parse_qs, urlencode


class TreeEnricher:
    def __init__(self, db_helper):
        self.db = db_helper

    def infer_genders(self):
        """Infer M/F from father/mother roles and spouse pairing. Returns count updated."""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id, gender FROM individuals")
        genders = {row["id"]: row["gender"] for row in cursor.fetchall()}

        cursor.execute("SELECT person_id, related_id, type FROM relationships")
        rels = [dict(row) for row in cursor.fetchall()]

        updated = 0

        # Pass 1: role-based
        for rel in rels:
            r_type = rel["type"]
            related_id = rel["related_id"]
            person_id = rel["person_id"]

            if r_type == "father":
                # related is father of person
                if related_id in genders and genders[related_id] not in ("M", "F"):
                    self.db.update_gender(related_id, "M")
                    genders[related_id] = "M"
                    updated += 1
            elif r_type == "mother":
                if related_id in genders and genders[related_id] not in ("M", "F"):
                    self.db.update_gender(related_id, "F")
                    genders[related_id] = "F"
                    updated += 1
            elif r_type == "child":
                # person is parent of related; use person's known gender to set reverse later
                pass

        # Pass 2: if A is child of B and B has known gender, ensure father/mother type consistency
        # (handled in canonicalize)

        # Pass 3: spouse of known gender
        for rel in rels:
            if rel["type"] != "spouse":
                continue
            a, b = rel["person_id"], rel["related_id"]
            ga = genders.get(a)
            gb = genders.get(b)
            if ga == "M" and b in genders and gb not in ("M", "F"):
                self.db.update_gender(b, "F")
                genders[b] = "F"
                updated += 1
            elif ga == "F" and b in genders and gb not in ("M", "F"):
                self.db.update_gender(b, "M")
                genders[b] = "M"
                updated += 1
            elif gb == "M" and a in genders and ga not in ("M", "F"):
                self.db.update_gender(a, "F")
                genders[a] = "F"
                updated += 1
            elif gb == "F" and a in genders and ga not in ("M", "F"):
                self.db.update_gender(a, "M")
                genders[a] = "M"
                updated += 1

        return updated

    def canonicalize_relationships(self):
        """Make relationships bidirectional and resolve parent -> father/mother when possible.

        Returns dict with counts of added/resolved relationships.
        """
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id, gender FROM individuals")
        genders = {row["id"]: row["gender"] for row in cursor.fetchall()}

        cursor.execute("SELECT person_id, related_id, type FROM relationships")
        rels = [(row["person_id"], row["related_id"], row["type"]) for row in cursor.fetchall()]
        existing = set(rels)

        added = 0
        resolved = 0

        for person_id, related_id, r_type in list(rels):
            # Resolve generic parent using related person's gender
            if r_type == "parent":
                g = genders.get(related_id)
                new_type = None
                if g == "M":
                    new_type = "father"
                elif g == "F":
                    new_type = "mother"
                if new_type:
                    self.db.add_relationship(person_id, related_id, new_type)
                    # Keep parent as historical; new typed edge is what GEDCOM uses
                    if (person_id, related_id, new_type) not in existing:
                        existing.add((person_id, related_id, new_type))
                        resolved += 1

            # Bidirectional spouse
            if r_type == "spouse":
                if (related_id, person_id, "spouse") not in existing:
                    self.db.add_relationship(related_id, person_id, "spouse")
                    existing.add((related_id, person_id, "spouse"))
                    added += 1

            # child -> parent: if person is parent of related, add reverse based on person's gender
            if r_type == "child":
                g = genders.get(person_id)
                reverse = None
                if g == "M":
                    reverse = "father"
                elif g == "F":
                    reverse = "mother"
                if reverse and (related_id, person_id, reverse) not in existing:
                    self.db.add_relationship(related_id, person_id, reverse)
                    existing.add((related_id, person_id, reverse))
                    added += 1

            # father/mother -> child reverse
            if r_type in ("father", "mother"):
                if (related_id, person_id, "child") not in existing:
                    self.db.add_relationship(related_id, person_id, "child")
                    existing.add((related_id, person_id, "child"))
                    added += 1
                # Also set gender on related if unknown
                if related_id in genders and genders[related_id] not in ("M", "F"):
                    self.db.update_gender(related_id, "M" if r_type == "father" else "F")
                    genders[related_id] = "M" if r_type == "father" else "F"

        return {"added": added, "resolved_parents": resolved}

    def discover_orphans(self, limit=5000):
        """Find related_ids referenced in relationships but missing from individuals/discovered_urls.

        Adds constructed URLs to discovered_urls. Returns number added.
        """
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT r.related_id AS oid, i.url AS sample_url
            FROM relationships r
            JOIN individuals i ON r.person_id = i.id
            LEFT JOIN individuals i2 ON r.related_id = i2.id
            LEFT JOIN discovered_urls d ON r.related_id = d.id
            WHERE i2.id IS NULL AND d.id IS NULL AND i.url IS NOT NULL
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()

        # Also orphans that appear as person_id side with no individual (shouldn't happen often)
        cursor.execute(
            """
            SELECT DISTINCT r.person_id AS oid, i.url AS sample_url
            FROM relationships r
            JOIN individuals i ON r.related_id = i.id
            LEFT JOIN individuals i2 ON r.person_id = i2.id
            LEFT JOIN discovered_urls d ON r.person_id = d.id
            WHERE i2.id IS NULL AND d.id IS NULL AND i.url IS NOT NULL
            LIMIT ?
            """,
            (limit,),
        )
        rows = list(rows) + list(cursor.fetchall())

        added = 0
        seen = set()
        for row in rows:
            oid = row["oid"]
            if not oid or oid in seen:
                continue
            seen.add(oid)
            sample_url = row["sample_url"]
            if not sample_url:
                continue
            parsed = urlparse(sample_url)
            query = parse_qs(parsed.query)
            query["i"] = [oid]
            new_query = urlencode(query, doseq=True)
            new_url = urlunparse(
                (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
            )
            self.db.add_discovered_url(oid, new_url)
            added += 1

        return added

    def quality_report(self):
        """Return a dict of data-quality metrics."""
        cursor = self.db.conn.cursor()

        cursor.execute("SELECT COUNT(*) AS c FROM individuals")
        total = cursor.fetchone()["c"]

        cursor.execute("SELECT gender, COUNT(*) AS c FROM individuals GROUP BY gender")
        by_gender = {row["gender"] or "NULL": row["c"] for row in cursor.fetchall()}

        cursor.execute(
            """
            SELECT COUNT(DISTINCT r.related_id) AS c
            FROM relationships r
            LEFT JOIN individuals i ON r.related_id = i.id
            WHERE i.id IS NULL
            """
        )
        orphan_related = cursor.fetchone()["c"]

        cursor.execute(
            """
            SELECT COUNT(*) AS c FROM individuals i
            WHERE NOT EXISTS (
                SELECT 1 FROM relationships r
                WHERE r.person_id = i.id OR r.related_id = i.id
            )
            """
        )
        isolated = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) AS c FROM relationships WHERE type = 'parent'")
        unresolved_parents = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) AS c FROM relationships WHERE type = 'spouse'")
        spouses = cursor.fetchone()["c"]

        cursor.execute(
            """
            SELECT COUNT(*) AS c FROM discovered_urls d
            LEFT JOIN individuals i ON d.id = i.id
            WHERE i.id IS NULL AND d.failure_count < 3
            """
        )
        pending = cursor.fetchone()["c"]

        cursor.execute(
            """
            SELECT COUNT(*) AS c FROM discovered_urls WHERE failure_count >= 3
            """
        )
        failed = cursor.fetchone()["c"]

        return {
            "total_individuals": total,
            "gender_M": by_gender.get("M", 0),
            "gender_F": by_gender.get("F", 0),
            "gender_U": by_gender.get("U", 0) + by_gender.get("NULL", 0),
            "orphan_related_ids": orphan_related,
            "isolated_individuals": isolated,
            "unresolved_parent_links": unresolved_parents,
            "spouse_links": spouses,
            "pending_urls": pending,
            "failed_urls": failed,
        }

    def enrich(self):
        """Run full offline enrichment pipeline."""
        genders = self.infer_genders()
        rels = self.canonicalize_relationships()
        # Second gender pass after new father/mother edges
        genders += self.infer_genders()
        orphans = self.discover_orphans()
        report = self.quality_report()
        return {
            "genders_updated": genders,
            "relationships_added": rels["added"],
            "parents_resolved": rels["resolved_parents"],
            "orphans_discovered": orphans,
            "quality": report,
        }
