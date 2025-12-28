import pytest
from src.gedcom_exporter import GedcomExporter
from src.database import DatabaseHelper
import os

@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test.db"
    return DatabaseHelper(str(db_path))

def test_export_empty_gedcom(db, tmp_path):
    output_path = tmp_path / "test.ged"
    exporter = GedcomExporter(db)
    exporter.export(str(output_path))
    
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "0 HEAD" in content
        assert "1 GEDC" in content
        assert "2 VERS 5.5.1" in content
        assert "0 TRLR" in content

def test_export_individual(db, tmp_path):
    db.add_individual({
        "id": "p1",
        "name": "שניאור זלמן",
        "birth_date": "תק\"ה",
        "birth_date_civil": "1745",
        "death_date": "תקע\"ג",
        "death_date_civil": "1813",
        "gender": "M",
        "url": "http://example.com/p1"
    })
    
    output_path = tmp_path / "test_indiv.ged"
    exporter = GedcomExporter(db)
    exporter.export(str(output_path))
    
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "0 @I1@ INDI" in content
        assert "1 NAME שניאור זלמן" in content
        assert "1 BIRT" in content
        assert "2 DATE 1745" in content
        assert "2 NOTE תק\"ה" in content
        assert "1 DEAT" in content
        assert "2 DATE 1813" in content
        assert "2 NOTE תקע\"ג" in content

def test_export_relationships(db, tmp_path):
    # Father, Mother, Child
    db.add_individual({"id": "f1", "name": "Father", "gender": "M", "birth_date": "", "death_date": "", "url": ""})
    db.add_individual({"id": "m1", "name": "Mother", "gender": "F", "birth_date": "", "death_date": "", "url": ""})
    db.add_individual({"id": "c1", "name": "Child", "gender": "M", "birth_date": "", "death_date": "", "url": ""})
    
    db.add_relationship("c1", "f1", "father")
    db.add_relationship("c1", "m1", "mother")
    
    output_path = tmp_path / "test_fam.ged"
    exporter = GedcomExporter(db)
    exporter.export(str(output_path))
    
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "0 @F1@ FAM" in content
        assert "1 HUSB @I1@" in content # f1
        assert "1 WIFE @I2@" in content # m1
        assert "1 CHIL @I3@" in content # c1
        
        # Verify individual links back to family
        assert "0 @I3@ INDI" in content
        assert "1 FAMC @F1@" in content
