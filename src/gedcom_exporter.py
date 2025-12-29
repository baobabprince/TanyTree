import sqlite3

class GedcomExporter:
    def __init__(self, db_helper):
        self.db = db_helper

    def export(self, output_path):
        # Fetch data
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM individuals")
        individuals = cursor.fetchall()
        
        id_map = {} # db_id -> gedcom_id
        for i, row in enumerate(individuals):
            id_map[row['id']] = f"I{i+1}"
            
        # Group into families
        # A simple approach: group by parents
        families = {} # (father_id, mother_id) -> [children_ids]
        
        # Track spouses that aren't necessarily in a "parents" relationship yet
        # or handle them separately.
        # For this scraper, we mainly get parent/child.
        
        person_famc = {} # child_id -> fam_id
        person_fams = {} # parent_id -> [fam_ids]
        
        cursor.execute("SELECT * FROM relationships")
        rels = cursor.fetchall()
        
        # Temporary storage to build families
        child_parents = {} # child_id -> {'father': id, 'mother': id}
        
        for rel in rels:
            p_id = rel['person_id']
            r_id = rel['related_id']
            r_type = rel['type']
            
            if r_type in ['father', 'mother']:
                if p_id not in child_parents:
                    child_parents[p_id] = {}
                child_parents[p_id][r_type] = r_id
            elif r_type == 'spouse':
                # For now, let's treat spouse as a family with no children (yet)
                # if not already in one
                pass

        # Build families from child_parents
        fam_list = []
        parents_to_fam = {} # (father, mother) -> fam_id
        
        for child_id, parents in child_parents.items():
            f_id = parents.get('father')
            m_id = parents.get('mother')
            key = (f_id, m_id)
            if key not in parents_to_fam:
                fam_id = f"F{len(fam_list) + 1}"
                parents_to_fam[key] = fam_id
                fam_list.append({'id': fam_id, 'father': f_id, 'mother': m_id, 'children': []})
            
            fam_id = parents_to_fam[key]
            for f in fam_list:
                if f['id'] == fam_id:
                    f['children'].append(child_id)
                    person_famc[child_id] = fam_id
                    if f_id:
                        if f_id not in person_fams: person_fams[f_id] = []
                        if fam_id not in person_fams[f_id]: person_fams[f_id].append(fam_id)
                    if m_id:
                        if m_id not in person_fams: person_fams[m_id] = []
                        if fam_id not in person_fams[m_id]: person_fams[m_id].append(fam_id)
                    break

        self._write_gedcom(output_path, individuals, id_map, fam_list, person_famc, person_fams)

    def _write_gedcom(self, output_path, individuals, id_map, families, person_famc, person_fams):
        with open(output_path, "w", encoding="utf-8") as f:
            # Header
            f.write("0 HEAD\n")
            f.write("1 GEDC\n")
            f.write("2 VERS 5.5.1\n")
            f.write("2 FORM LINEAGE-LINKED\n")
            f.write("1 CHAR UTF-8\n")
            
            # Individuals
            for row in individuals:
                db_id = row['id']
                ged_id = id_map[db_id]
                f.write(f"0 @{ged_id}@ INDI\n")
                if row['first_name'] and row['last_name']:
                    f.write(f"1 NAME {row['first_name']} /{row['last_name']}/\n")
                elif row['name']:
                    f.write(f"1 NAME {row['name']}\n")

                if row['gender']:
                    sex = "M" if row['gender'] in ["זכר", "M", "male"] else "F"
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

            # Families
            for fam in families:
                f.write(f"0 @{fam['id']}@ FAM\n")
                if fam['father'] and fam['father'] in id_map:
                    f.write(f"1 HUSB @{id_map[fam['father']]}@\n")
                if fam['mother'] and fam['mother'] in id_map:
                    f.write(f"1 WIFE @{id_map[fam['mother']]}@\n")
                for c_id in fam['children']:
                    if c_id in id_map:
                        f.write(f"1 CHIL @{id_map[c_id]}@\n")

            # Trailer
            f.write("0 TRLR\n")
