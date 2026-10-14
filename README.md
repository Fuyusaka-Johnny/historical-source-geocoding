# 日文史料信息抽取与地名核验

将日文史料中的日期、人物、地点与事件整理为可检查的记录，再查询历史地名库，保留同名候选及出处供人工判断。

这是 2026 年 10 月基于原项目记录重写的 MySQL 版本。原项目使用 PostgreSQL；本仓库不代表原项目当时已实现这些新增功能。原项目没有完成 ArcGIS 接入，本版也不实现地图导入。

## 这个项目能做什么

- 输入史料，按文本块调用可配置模型接口；默认保留原项目的 MiniMax-M2.5／ModelScope 配置。
- 解析 JSON、检查字段类型，并核查模型返回的原文引文是否存在于输入中。
- 导入公开地名主表与可选别名表到 MySQL，按名称或别名查询候选。
- 保留全部已返回的同名候选、资料出处和空坐标，不自动确认历史地点。
- 查看原文、选择候选，并把抽取结果与人工选择导出为 JSON 文件。
- 不配置模型和数据库也可查看固定人工演示；演示不能证明真实抽取准确率。

结构校验和原文存在检查不能证明语义理解正确。所有候选都待人工核验；至多显示前 50 条并标记截断。人工选择记录仅表示选择了候选，不代表完成历史地点考证。

## 技术环境

Python 3.11+；FastAPI、Uvicorn；Pydantic 2、JSON；OpenAI Python SDK（兼容接口客户端）、ModelScope API、MiniMax-M2.5（可配置模型）；MySQL 8.4、PyMySQL；HTML、CSS、原生 JavaScript；pytest／HTTPX。

MiniMax 是模型系列，ModelScope 是本项目调用模型的服务入口，OpenAI SDK 是客户端工具。它们不是同一种东西。原工程使用 Tailwind CSS 和 PostgreSQL／psycopg2；本次前端改用本地 CSS，数据库改用 MySQL／PyMySQL。

## 快速开始：只查看人工演示

在终端进入解压后的项目目录，安装 Python 3.11 或更高版本后运行：

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

浏览器打开 <http://127.0.0.1:8000>，点击“查看人工演示”。示例句子、人物、地名和坐标均为人工测试材料，不是《后法兴院记》原文，也不是 NIHU 数据。

## 配置真实模型和 MySQL

1. 复制 `.env.example` 为 `.env`，在本地填写模型密钥与自选数据库密码。
2. 模型入口和模型 ID 都可配置。历史配置能否继续使用，取决于服务商账号、授权和当前模型目录；本次未用真实密钥验证在线模型调用。
3. 运行 MySQL。已安装 MySQL 时直接填写连接信息；已安装 Docker 时可使用本仓库的 Compose：

```sh
cp .env.example .env
# 用编辑器填写 .env 中的密钥与密码，再运行：
docker compose up -d --wait
python -m scripts.manage init-db
```

默认只在本机 3307 端口暴露数据库。若使用已有数据库，请让管理员创建数据库及有权建表和导入数据的账号，再修改 `.env`。原工程中的密码、主机和密钥没有复制到本仓库。

先用附带的人工数据验证链路（不要和正式地名库混用）：

```sh
python -m scripts.manage import --places examples/places_synthetic.csv --aliases examples/aliases_synthetic.csv
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

查询“例示寺”应保留两个候选，查询“レイジデラ”应通过别名找到同样的两个候选。“坐标未定”的坐标仍为空。

## 导入真实历史地名数据

来源为[人间文化研究机构（NIHU）的历史地名数据发布页](https://www.nihu.jp/ja/database/source_map.html)，编制机构为 NIHU 与 H-GIS 研究会。之前上传的版本中，主表有 **298,914 条记录**，不是唯一地点数量，也不是本仓库默认已导入的数据量。

从官方发布页取得数据并解压，把主表与别名表放进 `data/`（该目录内容不会提交）。原始扩展名可能为 TXT，内容实为 UTF-8 CSV；下载后的文件名也可能乱码，依照表头识别即可：

| 文件 | 必要字段 |
| --- | --- |
| 地名主表 | ID、地名、緯度、経度；推荐保留全部原始列 |
| 地名别名表 | ID、地名ID、別名 |

```sh
python -m scripts.manage import --places data/地名.txt --aliases data/地名_別名.txt
```

导入命令同时输出输入记录数与数据库实际记录数。按 ID 更新，不按名称去重；同名地点可能是不同实体。数据导入失败会回滚本次数据写入；表结构创建不参与该回滚。重复运行不复制同一 ID，但不会自动删除旧版本中已消失的记录。换版本时建议使用新的数据库。

本仓库不附带完整公开数据，也不附带轮读会整理的未确认可公开史料。使用公开数据时须遵循[来源及加工说明要求](https://www.nihu.jp/ja/database/source_map/about.html)；以官方发布页链接的最新使用说明为准。对外说明应注明“利用 NIHU 与 H-GIS 研究会的历史地名辞书数据，本项目进行了数据库导入与候选检索处理”。

## 进一步阅读

- [技术流程、接口与字段](docs/technical.md)
- [原项目与重写版的边界、未接入 ArcGIS 的原因](docs/project-history.md)
- [简历 STAR 文案与职责说明](docs/resume.md)
- [GitHub 发布步骤与提交说明](docs/github.md)
- [验证记录](docs/verification.md)

## 运行验证

```sh
pip install -r requirements-dev.txt
pytest -q
# 连接独立的测试 MySQL 库后再运行，测试会写入人工数据：
RUN_MYSQL_TESTS=1 pytest -q
```

已提供 GitHub Actions，使用独立 MySQL 服务运行集成测试；工作流是否通过以仓库实际运行结果为准。真实模型效果需要使用有权处理的史料样本另行验收，不能由人工演示或接口测试替代。
