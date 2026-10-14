"""Real MySQL tests: opt in locally, enabled in GitHub Actions."""
import os
from pathlib import Path
import pytest
from app.config import Settings
from app.database import MySQLRepository, connection
from scripts.manage import import_dataset

pytestmark = pytest.mark.skipif(os.getenv("RUN_MYSQL_TESTS") != "1", reason="requires a real MySQL service")
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def config():
    config = Settings.from_env()
    import_dataset(config, ROOT / "examples/places_synthetic.csv", ROOT / "examples/aliases_synthetic.csv")
    return config


def test_mysql_alias_homonyms_and_null_coordinates(config):
    repo = MySQLRepository(config)
    rows, truncated = repo.candidates("レイジデラ")
    assert {row["id"] for row in rows} == {1, 2}
    assert all(row["matched_by"] == "alias" for row in rows)
    assert not truncated
    rows, _ = repo.candidates("坐标未定")
    assert rows[0]["lat"] is None
    rows, _ = repo.candidates("例示川")
    assert rows[0]["lat2"] is not None


def test_mysql_query_does_not_execute_input_as_sql(config):
    rows, _ = MySQLRepository(config).candidates("' OR 1=1 --")
    assert rows == []


def test_repeat_import_keeps_stable_ids(config):
    result = import_dataset(config, ROOT / "examples/places_synthetic.csv", ROOT / "examples/aliases_synthetic.csv")
    assert result["input_places"] == 4
    assert result["database_places"] >= 4
    assert {r["id"] for r in MySQLRepository(config).candidates("例示寺")[0]} == {1, 2}


def test_invalid_batch_rolls_back(config, tmp_path):
    path = tmp_path / "invalid.csv"
    # First row would change an existing record. Second row must abort the whole import.
    content = "ID,地名,緯度,経度\n1,不应保存的改动,35,135\n"
    content += "".join(f"{1000000 + i},临时行{i},35,135\n" for i in range(999))
    content += "2000000,无效,100,135\n"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError):
        import_dataset(config, path)
    assert MySQLRepository(config).candidates("不应保存的改动")[0] == []
    assert MySQLRepository(config).candidates("临时行0")[0] == []
