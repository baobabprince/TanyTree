from src.utils import normalize_whitespace

class GedcomExporter:
    def __init__(self, db_helper):
        self.db = db_helper

    def export(self, output_path):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM individuals")
        individuals = cursor.fetchall()

        id_map = {}
        for i, row in enumerate(individuals):
            id_map[row['id']] = f"I{i+1}"

        person_famc = {}
        person_fams = {}

        cursor.execute("SELECT * FROM relationships")
        rels = cursor.fetchall()

        child_parents = {}  # child_id -> {'father': id, 'mother': id}
        spouse_pairs = set()

        for rel in rels:
            p_id = rel['person_id']
            r_id = rel['related_id']
            r_type = rel['type']

            if r_type in ('father', 'mother'):
                if p_id not in child_parents:
                    child_parents[p_id] = {}
                # Prefer first; do not overwrite if already set
                if r_type not in child_parents[p_id]:
                    child_parents[p_id][r_type] = r_id
            elif r_type == 'spouse':
                # Normalize pair order for uniqueness
                pair = tuple(sorted([p_id, r_id]))
                spouse_pairs.add(pair)

        fam_list = []
        parents_to_fam = {}  # (father, mother) -> fam_id

        def _register_parent_fams(f_id, m_id, fam_id):
            if f_id:
                person_fams.setdefault(f_id, [])
                if fam_id not in person_fams[f_id]:
                    person_fams[f_id].append(fam_id)
            if m_id:
                person_fams.setdefault(m_id, [])
                if fam_id not in person_fams[m_id]:
                    person_fams[m_id].append(fam_id)

        # Families from parent/child
        for child_id, parents in child_parents.items():
            f_id = parents.get('father')
            m_id = parents.get('mother')
            key = (f_id, m_id)
            if key not in parents_to_fam:
                fam_id = f"F{len(fam_list) + 1}"
                parents_to_fam[key] = fam_id
                fam_list.append({'id': fam_id, 'father': f_id, 'mother': m_id, 'children': []})
                _register_parent_fams(f_id, m_id, fam_id)

            fam_id = parents_to_fam[key]
            for f in fam_list:
                if f['id'] == fam_id:
                    if child_id not in f['children']:
                        f['children'].append(child_id)
                    person_famc[child_id] = fam_id
                    break

        # Families from spouse pairs not already covered as a parent couple
        existing_couples = set(parents_to_fam.keys())
        # Also match unordered: (a,b) vs father/mother assignment
        covered_pairs = set()
        for f_id, m_id in existing_couples:
            if f_id and m_id:
                covered_pairs.add(tuple(sorted([f_id, m_id])))

        cursor.execute("SELECT id, gender FROM individuals")
        genders = {row['id']: row['gender'] for row in cursor.fetchall()}

        for a, b in spouse_pairs:
            pair_key = tuple(sorted([a, b]))
            if pair_key in covered_pairs:
                continue
            # Assign HUSB/WIFE by gender when possible
            ga, gb = genders.get(a), genders.get(b)
            if ga == 'M' or gb == 'F':
                father, mother = a, b
            elif gb == 'M' or ga == 'F':
                father, mother = b, a
            else:
                father, mother = a, b

            fam_id = f"F{len(fam_list) + 1}"
            fam_list.append({'id': fam_id, 'father': father, 'mother': mother, 'children': []})
            _register_parent_fams(father, mother, fam_id)
            covered_pairs.add(pair_key)

        self._write_gedcom(output_path, individuals, id_map, fam_list, person_famc, person_fams)

    def _write_gedcom(self, output_path, individuals, id_map, families, person_famc, person_fams):
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("0 HEAD\n")
            f.write("1 GEDC\n")
            f.write("2 VERS 5.5.1\n")
            f.write("2 FORM LINEAGE-LINKED\n")
            f.write("1 CHAR UTF-8\n")

            for row in individuals:
                db_id = row['id']
                ged_id = id_map[db_id]
                f.write(f"0 @{ged_id}@ INDI\n")

                first_name = row['first_name'] or ""
                last_name = row['last_name'] or ""
                prefix = row['prefix'] or ""
                suffix = row['suffix'] or ""

                if first_name or last_name:
                    name_line = normalize_whitespace(f"1 NAME {first_name} /{last_name}/")
                    if suffix:
                        name_line += f" {suffix}"
                    f.write(f"{name_line}\n")

                    if first_name:
                        f.write(f"2 GIVN {first_name}\n")
                    if last_name:
                        f.write(f"2 SURN {last_name}\n")
                    if prefix:
                        f.write(f"2 NPFX {prefix}\n")
                    if suffix:
                        f.write(f"2 NSFX {suffix}\n")
                elif row['name']:
                    f.write(f"1 NAME {row['name']}\n")

                if row['gender']:
                    if row['gender'] in ["זכר", "M", "male"]:
                        sex = "M"
                    elif row['gender'] in ["נקבה", "F", "female"]:
                        sex = "F"
                    else:
                        sex = "U"
                    f.write(f"1 SEX {sex}\n")

                if row['birth_date'] or row['birth_date_civil']:
                    f.write("1 BIRT\n")
                    if row['birth_date_civil']:
                        f.write(f"2 DATE {row['birth_date_civil']}\n")
                    if row['birth_date']:
                        f.write(f"2 NOTE {row['birth_date']}\n")
                    if row['birth_place']:
                        f.write(f"2 PLAC {row['birth_place']}\n")

                if row['death_date'] or row['death_date_civil']:
                    f.write("1 DEAT\n")
                    if row['death_date_civil']:
                        f.write(f"2 DATE {row['death_date_civil']}\n")
                    if row['death_date']:
                        f.write(f"2 NOTE {row['death_date']}\n")
                    if row['death_place']:
                        f.write(f"2 PLAC {row['death_place']}\n")

                if db_id in person_famc:
                    f.write(f"1 FAMC @{person_famc[db_id]}@\n")

                if db_id in person_fams:
                    for f_id in person_fams[db_id]:
                        f.write(f"1 FAMS @{f_id}@\n")

            for fam in families:
                f.write(f"0 @{fam['id']}@ FAM\n")
                if fam['father'] and fam['father'] in id_map:
                    f.write(f"1 HUSB @{id_map[fam['father']]}@\n")
                if fam['mother'] and fam['mother'] in id_map:
                    f.write(f"1 WIFE @{id_map[fam['mother']]}@\n")
                for c_id in fam['children']:
                    if c_id in id_map:
                        f.write(f"1 CHIL @{id_map[c_id]}@\n")

            f.write("0 TRLR\n")
