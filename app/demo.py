"""Invented examples, deliberately separate from NIHU and real diary records."""
from .models import ExtractionResult, DayRecord, Person
from .matching import enrich

DEMO_TEXT = "【人工编写演示句，非历史原文】\n十二日 晴。太郎、例示寺に参る。夕に宅内へ帰る。"


class DemoRepository:
    def candidates(self, name, limit=50):
        rows = []
        if name == "例示寺":
            for number, lat in [(1, 35.0), (2, 35.1)]:
                rows.append(dict(id=number, name=name, lat=lat, lng=135.7,
                    lat2=None, lng2=None, shape_code=1, attribute_code=13,
                    source="人工测试数据，非历史坐标", source_detail="", notes="用于展示同名候选", matched_by="name"))
        return rows[:limit], len(rows) > limit


def demo_result():
    record = DayRecord(day="十二日", weather="晴", locations=["例示寺", "宅内"],
        people=[Person(name="太郎", action="例示寺に参る。夕に宅内へ帰る。")],
        events=["太郎、例示寺に参る", "夕に宅内へ帰る"],
        original_text=DEMO_TEXT.split("\n", 1)[1])
    result = {"records": [{**record.model_dump(), "date_index": 1, "segment_index": 1}],
              "segment_count": 1, "failures": [], "extraction_status": "complete"}
    return {**enrich(result, DemoRepository()), "demo": True, "input_text": DEMO_TEXT,
            "notice": "固定人工示例；未调用模型，未连接 MySQL；不得用于准确率或性能声明"}
