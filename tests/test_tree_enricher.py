import os
import tempfile
import pytest

from src.database import DatabaseHelper
from src.tree_enricher import TreeEnricher


@pytest.fixture
def db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    helper = DatabaseHelper(path)
    yield helper
    helper.close()
    os.unlink(path)


def test_infer_gender_from_father_role(db):
    db.add_individual({"id": "1", "name": "Child", "gender": "U", "url": "http://x/?i=1"})
    db.add_individual({"id": "2", "name": "Parent", "gender": "U", "url": "http://x/?i=2"})
    db.add_relationship("1", "2", "father")

    enricher = TreeEnricher(db)
    n = enricher.infer_genders()
    assert n >= 1
    assert db.get_individual("2")["gender"] == "M"


def test_canonicalize_bidirectional_spouse(db):
    db.add_individual({"id": "1", "name": "A", "gender": "M", "url": "http://x/?i=1"})
    db.add_individual({"id": "2", "name": "B", "gender": "F", "url": "http://x/?i=2"})
    db.add_relationship("1", "2", "spouse")

    enricher = TreeEnricher(db)
    result = enricher.canonicalize_relationships()
    assert result["added"] >= 1
    rels = {(r["person_id"], r["related_id"], r["type"]) for r in db.get_relationships("2")}
    assert ("2", "1", "spouse") in rels


def test_resolve_parent_to_mother(db):
    db.add_individual({"id": "1", "name": "Child", "gender": "U", "url": "http://x/?i=1"})
    db.add_individual({"id": "2", "name": "Mom", "gender": "F", "url": "http://x/?i=2"})
    db.add_relationship("1", "2", "parent")

    enricher = TreeEnricher(db)
    result = enricher.canonicalize_relationships()
    assert result["resolved_parents"] >= 1
    rels = {(r["person_id"], r["related_id"], r["type"]) for r in db.get_relationships("1")}
    assert ("1", "2", "mother") in rels


def test_discover_orphans(db):
    db.add_individual({"id": "1", "name": "A", "gender": "M", "url": "http://example.com/path/?i=1"})
    db.add_relationship("1", "999", "child")

    enricher = TreeEnricher(db)
    n = enricher.discover_orphans()
    assert n >= 1
    pending = db.get_pending_urls()
    ids = {p["id"] for p in pending}
    assert "999" in ids


def test_quality_report(db):
    db.add_individual({"id": "1", "name": "A", "gender": "M", "url": "http://x/?i=1"})
    enricher = TreeEnricher(db)
    q = enricher.quality_report()
    assert q["total_individuals"] == 1
    assert q["gender_M"] == 1
