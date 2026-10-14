import json
from dataclasses import replace
import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.demo import DemoRepository
from app.extraction import parse_output, split_text, extract_segments
from app.main import app, extractor, repository, settings
from app.matching import match_locations
from scripts.manage import place_row


def output(text, locations=None):
    return {"records": [{"day": "十二日", "original_text": text, "locations": locations or []}]}


def test_split_bounds_long_ocr_line_without_dropping_characters():
    text = "甲" * 1040 + "\n" + "乙" * 100 + "\n"
    chunks = split_text(text, 500)
    assert max(map(len, chunks)) <= 500
    assert "".join(chunks) == text


def test_source_quote_must_really_exist():
    with pytest.raises(ValueError, match="原文片段"):
        parse_output(json.dumps(output("史料里没有这句话")), "十二日 晴")


def test_json_fence_and_missing_optional_fields():
    result = parse_output('```json\n' + json.dumps(output("十二日 晴")) + '\n```', "十二日 晴")
    assert result.records[0].people == []


def test_partial_failure_does_not_disappear_as_success():
    class Model:
        def extract(self, text):
            if text == "乙":
                raise RuntimeError("provider error")
            return parse_output(json.dumps(output(text)), text)
    result = extract_segments("甲乙", Model(), 1)
    assert result["extraction_status"] == "partial"
    assert len(result["records"]) == 1
    assert result["failures"][0]["segment_index"] == 2


def test_all_homonyms_retained_and_never_auto_selected():
    group = match_locations(["例示寺", "例示寺"], DemoRepository())
    assert len(group) == 1
    assert len(group[0]["candidates"]) == 2
    assert group[0]["selected_place_id"] is None
    assert group[0]["status"] == "needs_review"


def test_unknown_reference_stays_unresolved():
    group = match_locations(["宅内"], DemoRepository())[0]
    assert group["status"] == "unmatched"
    assert group["candidates"] == []


def test_missing_coordinates_are_not_zero():
    row = {"ID": "4", "地名": "坐标未定", "緯度": "", "経度": ""}
    assert place_row(row)[4:6] == (None, None)
    with pytest.raises(ValueError, match="成对"):
        place_row({**row, "緯度": "35"})


def test_invalid_coordinate_is_not_imported():
    with pytest.raises(ValueError):
        place_row({"ID": "5", "地名": "例示", "緯度": "NaN", "経度": "135"})


@pytest.fixture
def client():
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_demo_is_explicitly_synthetic_and_has_no_external_dependencies(client):
    response = client.get("/api/demo")
    assert response.status_code == 200
    assert response.json()["demo"] is True
    assert "未调用模型" in response.json()["notice"]
    assert client.get("/").status_code == 200


def test_missing_model_key_is_an_error_not_a_demo_fallback(client):
    config = replace(Settings.from_env(), llm_api_key="")
    app.dependency_overrides[settings] = lambda: config
    assert client.post("/api/extract", json={"text": "十二日 晴"}).status_code == 503


def test_database_failure_preserves_extraction(client):
    class Model:
        def extract(self, text):
            return parse_output(json.dumps(output(text, ["例示寺"])), text)
    class BrokenDB:
        def candidates(self, name):
            raise ConnectionError("database password should never appear")
    app.dependency_overrides[extractor] = Model
    app.dependency_overrides[repository] = BrokenDB
    result = client.post("/api/extract", json={"text": "十二日 晴"})
    assert result.status_code == 200
    data = result.json()
    assert data["matching_status"] == "failed"
    assert len(data["records"]) == 1
    assert "password" not in result.text


def test_geocode_outage_is_reported(client):
    class BrokenDB:
        def candidates(self, name):
            raise ConnectionError()
    app.dependency_overrides[repository] = BrokenDB
    assert client.get("/api/geocode", params={"name": "例示寺"}).status_code == 503
