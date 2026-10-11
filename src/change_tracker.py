import os


class ChangeTracker:
    """Tracks database changes before and after a scrape session and generates Hebrew summary reports."""

    def __init__(self, db_helper):
        self.db = db_helper
        self.pre_snapshot = None

    def take_snapshot(self):
        """Captures a snapshot of the current database state."""
        cursor = self.db.conn.cursor()

        # Capture individuals
        cursor.execute("SELECT * FROM individuals")
        individuals = {row["id"]: dict(row) for row in cursor.fetchall()}

        # Capture relationships
        cursor.execute("SELECT person_id, related_id, type FROM relationships")
        relationships = set((row["person_id"], row["related_id"], row["type"]) for row in cursor.fetchall())

        # Capture discovered_urls and failure counts
        cursor.execute("SELECT id, url, failure_count FROM discovered_urls")
        discovered_urls = {row["id"]: {"url": row["url"], "failure_count": row["failure_count"]} for row in cursor.fetchall()}

        self.pre_snapshot = {
            "individuals": individuals,
            "relationships": relationships,
            "discovered_urls": discovered_urls,
        }
        return self.pre_snapshot

    def compute_changes(self, pre_snapshot=None):
        """Compares current DB state against the pre-run snapshot and computes all changes."""
        if pre_snapshot is None:
            pre_snapshot = self.pre_snapshot

        if pre_snapshot is None:
            raise ValueError("No snapshot available to compute changes against.")

        pre_inds = pre_snapshot.get("individuals", {})
        pre_rels = pre_snapshot.get("relationships", set())
        pre_urls = pre_snapshot.get("discovered_urls", {})

        is_initial_run = len(pre_inds) == 0

        cursor = self.db.conn.cursor()

        # Get post-run individuals
        cursor.execute("SELECT * FROM individuals")
        post_inds = {row["id"]: dict(row) for row in cursor.fetchall()}

        # Get post-run relationships
        cursor.execute("SELECT person_id, related_id, type FROM relationships")
        post_rels = set((row["person_id"], row["related_id"], row["type"]) for row in cursor.fetchall())

        # Get post-run discovered_urls
        cursor.execute("SELECT id, url, failure_count FROM discovered_urls")
        post_urls = {row["id"]: {"url": row["url"], "failure_count": row["failure_count"]} for row in cursor.fetchall()}

        # 1. Added individuals
        added_inds = []
        for p_id, p_data in post_inds.items():
            if p_id not in pre_inds:
                added_inds.append(p_data)

        # Sort added individuals by numeric ID if possible
        added_inds.sort(key=lambda x: int(x["id"]) if str(x["id"]).isdigit() else str(x["id"]))

        # 2. Updated individuals
        updated_inds = []
        added_dates_count = 0

        # For added individuals, count birth/death dates added
        for ind in added_inds:
            if ind.get("birth_date") or ind.get("birth_date_civil"):
                added_dates_count += 1
            if ind.get("death_date") or ind.get("death_date_civil"):
                added_dates_count += 1

        for p_id, post_data in post_inds.items():
            if p_id in pre_inds:
                pre_data = pre_inds[p_id]
                field_changes = {}
                for field, val in post_data.items():
                    old_val = pre_data.get(field)
                    if (val or old_val) and val != old_val:
                        field_changes[field] = {"old": old_val, "new": val}
                        if field in ["birth_date", "birth_date_civil", "death_date", "death_date_civil"] and not old_val and val:
                            added_dates_count += 1

                if field_changes:
                    updated_inds.append({
                        "id": p_id,
                        "person": post_data,
                        "changes": field_changes,
                    })

        # 3. Added relationships
        raw_added_rels = post_rels - pre_rels
        added_rels = []
        for person_id, related_id, rel_type in raw_added_rels:
            p_name = post_inds.get(person_id, {}).get("name") or post_inds.get(person_id, {}).get("first_name") or f"מזהה {person_id}"
            r_name = post_inds.get(related_id, {}).get("name") or post_inds.get(related_id, {}).get("first_name") or f"מזהה {related_id}"
            added_rels.append({
                "person_id": person_id,
                "person_name": p_name,
                "related_id": related_id,
                "related_name": r_name,
                "type": rel_type,
            })

        # 4. Scrape status / URLs
        newly_failed_urls = []
        for u_id, u_info in post_urls.items():
            pre_info = pre_urls.get(u_id)
            if u_info["failure_count"] > 0:
                if pre_info is None or u_info["failure_count"] > pre_info.get("failure_count", 0):
                    newly_failed_urls.append({
                        "id": u_id,
                        "url": u_info["url"],
                        "failure_count": u_info["failure_count"],
                    })

        pending_urls = [u for u_id, u in post_urls.items() if u_id not in post_inds and u["failure_count"] < 3]

        # 5. Tree-wide statistics
        total_individuals = len(post_inds)
        males = sum(1 for p in post_inds.values() if p.get("gender") == "M")
        females = sum(1 for p in post_inds.values() if p.get("gender") == "F")
        unknown_gender = total_individuals - (males + females)
        total_rels = len(post_rels)
        total_failed_urls = sum(1 for u in post_urls.values() if u["failure_count"] >= 3)
        total_pending_urls = len(pending_urls)

        return {
            "is_initial_run": is_initial_run,
            "added_individuals": added_inds,
            "updated_individuals": updated_inds,
            "added_relationships": added_rels,
            "added_dates_count": added_dates_count,
            "newly_failed_urls": newly_failed_urls,
            "stats": {
                "total_individuals": total_individuals,
                "males": males,
                "females": females,
                "unknown_gender": unknown_gender,
                "total_relationships": total_rels,
                "total_pending_urls": total_pending_urls,
                "total_failed_urls": total_failed_urls,
            },
            "summary_counts": {
                "added_people_count": len(added_inds),
                "updated_people_count": len(updated_inds),
                "added_relationships_count": len(added_rels),
                "added_dates_count": added_dates_count,
                "newly_failed_count": len(newly_failed_urls),
            },
        }

    @staticmethod
    def _format_person_name(person):
        name = person.get("name")
        if name:
            return name
        fn = person.get("first_name", "")
        ln = person.get("last_name", "")
        full = f"{fn} {ln}".strip()
        return full if full else f"מזהה {person.get('id')}"

    @staticmethod
    def _format_gender(gender_code):
        if gender_code == "M":
            return "זכר"
        elif gender_code == "F":
            return "נקבה"
        return "לא ידוע"

    @staticmethod
    def _format_rel_type(rel_type):
        mapping = {
            "parent": "הורה של",
            "child": "ילד/ה של",
            "spouse": "בן/בת זוג של",
        }
        return mapping.get(rel_type, f"קשר ({rel_type}) עם")

    def generate_report(self, changes, output_file="changes_summary.md"):
        """Generates Hebrew Markdown report and console text."""

        if changes.get("is_initial_run"):
            msg = (
                "### סיכום הרצה ראשונה\n\n"
                "זוהי הרצה ראשונה על מסד נתונים חדש (לא הייתה גירסה קודמת להשוואה).\n"
                f"נאספו **{changes['stats']['total_individuals']}** אנשים ו-**{changes['stats']['total_relationships']}** קשרים בעץ."
            )
            return msg

        stats = changes["stats"]
        summary = changes["summary_counts"]

        lines = []

        lines.append("# תקציר שינויים בעץ היחס ביחס לגירסה הקודמת")
        lines.append("")
        lines.append("## סקירה כללית של השינויים בריצה זו")
        lines.append("")

        overview_text = (
            f"בריצה זו נוספו **{summary['added_people_count']}** אנשים חדשים לעץ, "
            f"ועודכנו פרטיהם של **{summary['updated_people_count']}** אנשים קיימים. "
            f"בסה\"כ הוגדרו **{summary['added_relationships_count']}** קשרים משפחתיים חדשים, "
            f"ונוספו **{summary['added_dates_count']}** תאריכי לידה/פטירה חדשים. "
        )
        if summary["newly_failed_count"] > 0:
            overview_text += f"כמו כן, נרשמו **{summary['newly_failed_count']}** דפים שכשלו בטעינה במהלך הריצה."
        else:
            overview_text += "כל הניסיונות לגרידת דפים בריצה זו הושלמו בהצלחה ללא כשלים חדשים."

        lines.append(overview_text)
        lines.append("")

        lines.append("## נתונים סטטיסטיים כלליים של העץ")
        lines.append("")
        lines.append(f"- **סה\"כ אנשים בעץ:** {stats['total_individuals']} ({stats['males']} זכרים, {stats['females']} נקבות, {stats['unknown_gender']} ללא ציון מגדר)")
        lines.append(f"- **סה\"כ קשרים משפחתיים בעץ:** {stats['total_relationships']}")
        lines.append(f"- **דפים ממתינים לגרידה:** {stats['total_pending_urls']}")
        lines.append(f"- **דפים שנכשלו באופן קבוע (3 ניסיונות+):** {stats['total_failed_urls']}")
        lines.append("")

        # Added individuals
        added_inds = changes.get("added_individuals", [])
        lines.append(f"## אנשים שנוספו לעץ ({len(added_inds)})")
        lines.append("")
        if not added_inds:
            lines.append("לא נוספו אנשים חדשים בריצה זו.")
        else:
            for ind in added_inds:
                p_name = self._format_person_name(ind)
                gender_str = self._format_gender(ind.get("gender"))
                details = [f"מזהה: {ind['id']}", f"מגדר: {gender_str}"]

                b_date = ind.get("birth_date") or ind.get("birth_date_civil")
                if b_date:
                    details.append(f"לידה: {b_date}")
                    if ind.get("birth_place"):
                        details.append(f"מקום לידה: {ind['birth_place']}")

                d_date = ind.get("death_date") or ind.get("death_date_civil")
                if d_date:
                    details.append(f"פטירה: {d_date}")
                    if ind.get("death_place"):
                        details.append(f"מקום פטירה: {ind['death_place']}")

                lines.append(f"- **{p_name}** ({', '.join(details)})")

        lines.append("")

        # Updated individuals
        updated_inds = changes.get("updated_individuals", [])
        lines.append(f"## אנשים שעודכנו ({len(updated_inds)})")
        lines.append("")
        if not updated_inds:
            lines.append("לא עודכנו פרטים של אנשים קיימים בריצה זו.")
        else:
            for item in updated_inds:
                p_data = item["person"]
                p_name = self._format_person_name(p_data)
                chg_desc = []
                for field, val_info in item["changes"].items():
                    old_v = val_info["old"] or "ריק"
                    new_v = val_info["new"] or "ריק"
                    chg_desc.append(f"{field}: מ-'{old_v}' ל-'{new_v}'")
                lines.append(f"- **{p_name}** (מזהה: {item['id']}): {'; '.join(chg_desc)}")

        lines.append("")

        # Added relationships
        added_rels = changes.get("added_relationships", [])
        lines.append(f"## קשרים משפחתיים חדשים ({len(added_rels)})")
        lines.append("")
        if not added_rels:
            lines.append("לא הוגדרו קשרים משפחתיים חדשים בריצה זו.")
        else:
            for rel in added_rels:
                rel_str = self._format_rel_type(rel["type"])
                lines.append(f"- **{rel['person_name']}** (מזהה: {rel['person_id']}) הוגדר/ה כ**{rel_str}** **{rel['related_name']}** (מזהה: {rel['related_id']})")

        lines.append("")

        # Failed URLs / Status
        failed_urls = changes.get("newly_failed_urls", [])
        lines.append(f"## סטטוס טעינת דפים וכשלים בריצה זו ({len(failed_urls)})")
        lines.append("")
        if not failed_urls:
            lines.append("אין דפים שנכשלו במהלך ריצה זו.")
        else:
            for f in failed_urls:
                lines.append(f"- **מזהה {f['id']}** ({f['url']}) — נכשל {f['failure_count']} פעמים")

        lines.append("")

        report_md = "\n".join(lines)

        # Save to markdown file if specified and not initial run
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report_md)

        return report_md
