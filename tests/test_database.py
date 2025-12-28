import pytest
import os
from src.database import DatabaseHelper


@pytest.fixture
def db_helper():
    db_path = "test_genealogy.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    helper = DatabaseHelper(db_path)
    yield helper
    helper.close()
    if os.path.exists(db_path):
        os.remove(db_path)


def test_add_individual(db_helper):
    individual = {
        "id": "p123",
        "name": "Abraham",
        "birth_date": "1745",
        "birth_date_civil": "1745",
        "death_date": "1812",
        "death_date_civil": "1812",
        "gender": "M",
        "url": "https://baalhatanya.org.il/p123"
    }
    db_helper.add_individual(individual)
    result = db_helper.get_individual("p123")
    assert result is not None
    assert result["name"] == "Abraham"
    assert result["gender"] == "M"
    assert result["birth_date_civil"] == "1745"


def test_add_relationship(db_helper):
    p1 = {"id": "p1", "name": "Father"}
    p2 = {"id": "p2", "name": "Son"}
    db_helper.add_individual(p1)
    db_helper.add_individual(p2)

    db_helper.add_relationship("p1", "p2", "parent")

    relationships = db_helper.get_relationships("p1")
    assert len(relationships) == 1
    assert relationships[0]["related_id"] == "p2"
    assert relationships[0]["type"] == "parent"
