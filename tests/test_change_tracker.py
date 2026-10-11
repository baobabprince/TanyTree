import pytest
import os
from src.database import DatabaseHelper
from src.change_tracker import ChangeTracker


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_tracker.db"
    helper = DatabaseHelper(str(db_file))
    yield helper
    helper.close()


def test_initial_run_detection(temp_db):
    tracker = ChangeTracker(temp_db)
    tracker.take_snapshot()

    # Add a person to DB after snapshot
    temp_db.add_individual({
        "id": "100",
        "name": "שניאור זלמן",
        "gender": "M",
        "birth_date": "ה'תקנ\"ח",
    })

    changes = tracker.compute_changes()
    assert changes["is_initial_run"] is True
    assert changes["stats"]["total_individuals"] == 1

    report = tracker.generate_report(changes, output_file=None)
    assert "הרצה ראשונה" in report


def test_added_individuals_and_dates(temp_db, tmp_path):
    # Setup pre-existing person
    temp_db.add_individual({
        "id": "100",
        "name": "אברהם",
        "gender": "M",
        "birth_date": "ה'תק\"ן",
    })

    tracker = ChangeTracker(temp_db)
    tracker.take_snapshot()

    # Add new person in post-run
    temp_db.add_individual({
        "id": "101",
        "name": "יצחק",
        "gender": "M",
        "birth_date": "ה'תקע\"ה",
        "death_date": "ה'תרכ\"ה",
    })

    changes = tracker.compute_changes()
    assert changes["is_initial_run"] is False
    assert len(changes["added_individuals"]) == 1
    assert changes["added_individuals"][0]["name"] == "יצחק"
    assert changes["added_dates_count"] == 2  # birth and death date for new person

    report_file = tmp_path / "test_report.md"
    report = tracker.generate_report(changes, output_file=str(report_file))

    assert "תקציר שינויים בעץ היחס" in report
    assert "יצחק" in report
    assert os.path.exists(report_file)

    with open(report_file, "r", encoding="utf-8") as f:
        file_content = f.read()
        assert "יצחק" in file_content


def test_updated_individual_detection(temp_db):
    temp_db.add_individual({
        "id": "100",
        "name": "מנחם מענדל",
        "gender": "M",
        "birth_date": None,
    })

    tracker = ChangeTracker(temp_db)
    tracker.take_snapshot()

    # Update person
    temp_db.add_individual({
        "id": "100",
        "name": "מנחם מענדל",
        "gender": "M",
        "birth_date": "ה'תקמ\"ט",
    })

    changes = tracker.compute_changes()
    assert len(changes["updated_individuals"]) == 1
    assert changes["updated_individuals"][0]["id"] == "100"
    assert "birth_date" in changes["updated_individuals"][0]["changes"]
    assert changes["added_dates_count"] == 1


def test_added_relationships_detection(temp_db):
    temp_db.add_individual({"id": "100", "name": "אבא", "gender": "M"})
    temp_db.add_individual({"id": "101", "name": "בן", "gender": "M"})

    tracker = ChangeTracker(temp_db)
    tracker.take_snapshot()

    # Add relationship
    temp_db.add_relationship("100", "101", "parent")

    changes = tracker.compute_changes()
    assert len(changes["added_relationships"]) == 1
    rel = changes["added_relationships"][0]
    assert rel["person_id"] == "100"
    assert rel["related_id"] == "101"
    assert rel["type"] == "parent"

    report = tracker.generate_report(changes, output_file=None)
    assert "הורה של" in report


def test_failed_urls_tracking(temp_db):
    temp_db.add_discovered_url("200", "http://example.com/?i=200")

    tracker = ChangeTracker(temp_db)
    tracker.take_snapshot()

    # Increment failure count
    temp_db.increment_failure_count("200")

    changes = tracker.compute_changes()
    assert len(changes["newly_failed_urls"]) == 1
    assert changes["newly_failed_urls"][0]["id"] == "200"
    assert changes["newly_failed_urls"][0]["failure_count"] == 1
