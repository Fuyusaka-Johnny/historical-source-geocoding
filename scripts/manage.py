"""Initialize MySQL and import NIHU UTF-8 CSV/TXT files without changing sources."""
import argparse
import csv
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from app.config import Settings
from app.database import connection, initialize

PLACE_SQL = """INSERT INTO places
(id,name,attribute_code,shape_code,lat,lng,lat2,lng2,source,source_detail,notes)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE name=VALUES(name),attribute_code=VALUES(attribute_code),
shape_code=VALUES(shape_code),lat=VALUES(lat),lng=VALUES(lng),lat2=VALUES(lat2),
lng2=VALUES(lng2),source=VALUES(source),source_detail=VALUES(source_detail),notes=VALUES(notes)"""
ALIAS_SQL = """INSERT INTO place_aliases (id,place_id,alias,alias_type)
VALUES (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE
place_id=VALUES(place_id),alias=VALUES(alias),alias_type=VALUES(alias_type)"""


def optional_int(value):
    return int(value) if value and value.strip() else None


def coordinate(value, limit):
    if not value or not value.strip():
        return None
    try:
        number = Decimal(value)
        if not number.is_finite() or not -limit <= number <= limit:
            raise ValueError("坐标超出合法范围")
        return number
    except InvalidOperation as exc:
        raise ValueError("坐标不是数字") from exc


def place_row(row):
    lat, lng = coordinate(row.get("緯度"), 90), coordinate(row.get("経度"), 180)
    lat2, lng2 = coordinate(row.get("緯度2"), 90), coordinate(row.get("経度2"), 180)
    if (lat is None) != (lng is None) or (lat2 is None) != (lng2 is None):
        raise ValueError("经纬度必须成对出现，不能用 0 替代缺失值")
    name = row["地名"]
    if not name or len(name) > 255:
        raise ValueError("地名为空或超过数据库字段长度")
    return (int(row["ID"]), name, optional_int(row.get("属性")), optional_int(row.get("形状")),
            lat, lng, lat2, lng2, row.get("出典", ""), row.get("出典詳細", ""), row.get("備考", ""))


def alias_row(row):
    alias = row["別名"]
    if not alias or len(alias) > 255:
        raise ValueError("别名为空或超过数据库字段长度")
    return (int(row["ID"]), int(row["地名ID"]), alias, row.get("種別", ""))


def import_file(cur, path, sql, parser, required):
    count, batch = 0, []
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"{Path(path).name} 缺少字段：{sorted(required)}")
        for row in reader:
            if None in row:
                raise ValueError(f"{Path(path).name} 第 {reader.line_num} 行列数异常")
            try:
                batch.append(parser(row))
            except (ValueError, TypeError, KeyError) as exc:
                raise ValueError(f"{Path(path).name} 第 {reader.line_num} 行无效：{exc}") from exc
            count += 1
            if len(batch) >= 1000:
                cur.executemany(sql, batch)
                batch.clear()
        if batch:
            cur.executemany(sql, batch)
    return count


def import_dataset(settings, places, aliases=None):
    initialize(settings)
    with connection(settings) as conn:
        try:
            with conn.cursor() as cur:
                count = import_file(cur, places, PLACE_SQL, place_row, {"ID", "地名", "緯度", "経度"})
                alias_count = import_file(cur, aliases, ALIAS_SQL, alias_row,
                    {"ID", "地名ID", "別名"}) if aliases else 0
                cur.execute("SELECT COUNT(*) AS count FROM places")
                total = cur.fetchone()["count"]
                cur.execute("SELECT COUNT(*) AS count FROM place_aliases")
                alias_total = cur.fetchone()["count"]
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return {"input_places": count, "input_aliases": alias_count,
            "database_places": total, "database_aliases": alias_total}


def main():
    parser = argparse.ArgumentParser(description="MySQL 地名库管理")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-db")
    imp = sub.add_parser("import")
    imp.add_argument("--places", required=True, help="地名主表 TXT/CSV 路径")
    imp.add_argument("--aliases", help="地名_別名 TXT/CSV 路径（可选）")
    args = parser.parse_args()
    config = Settings.from_env()
    if args.command == "init-db":
        initialize(config)
        print("MySQL 表已准备好；此操作不代表已导入数据。")
    else:
        print(json.dumps(import_dataset(config, args.places, args.aliases), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
