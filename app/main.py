from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .config import Settings
from .database import MySQLRepository
from .demo import demo_result
from .extraction import ModelExtractor, extract_segments
from .matching import enrich, match_locations
from .models import ExtractRequest

ROOT = Path(__file__).resolve().parents[1]
app = FastAPI(title="日文史料信息抽取与地名核验", version="0.1.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


def settings():
    return Settings.from_env()


def repository(config=Depends(settings)):
    return MySQLRepository(config)


def extractor(config=Depends(settings)):
    try:
        return ModelExtractor(config)
    except ValueError as exc:
        raise HTTPException(503, str(exc)) from exc


@app.get("/")
def index():
    return FileResponse(ROOT / "static/index.html")


@app.get("/api/health")
def health():
    # Process readiness only; this is deliberately not a DB/model health claim.
    return {"application": "ready", "database": "not_checked", "model": "not_checked"}


@app.get("/api/demo")
def demo():
    return demo_result()


@app.get("/api/geocode")
def geocode(name: str, repo=Depends(repository)):
    if not name.strip() or len(name) > 255:
        raise HTTPException(422, "请输入不超过 255 字的地名")
    try:
        return match_locations([name.strip()], repo)[0]
    except Exception as exc:
        raise HTTPException(503, "地名库查询失败，请检查 MySQL 服务、配置及数据导入状态") from exc


@app.post("/api/extract")
def extract(request: ExtractRequest, config=Depends(settings),
            model=Depends(extractor), repo=Depends(repository)):
    result = extract_segments(request.text, model, config.chunk_chars)
    result.update(input_text=request.text, model=config.llm_model)
    if result["extraction_status"] == "failed":
        return {**result, "geocode_summary": [], "demo": False, "matching_status": "not_attempted"}
    try:
        return {**enrich(result, repo), "demo": False, "matching_status": "complete"}
    except Exception:
        # Keep successfully extracted records when the independent database step fails.
        return {**result, "demo": False, "geocode_summary": [], "matching_status": "failed",
                "matching_message": "抽取结果已保留；MySQL 查询失败，尚未完成地点匹配"}
