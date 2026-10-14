# 日文史料信息抽取与地名核验

项目计划将史料中的日期、人物、地点与事件提取为结构化记录，关联历史地名坐标，并将研究记录及核验信息存入 MySQL，供后续接入 ArcGIS Pro 进行地图标注与空间分析。

## 这个项目能做什么

- 输入史料，按文本块调用可配置模型接口；默认使用 MiniMax-M2.5／ModelScope 配置。
- 解析 JSON、检查字段类型，并核查模型返回的原文引文是否存在于输入中。
- 导入公开地名主表与可选别名表到 MySQL，按名称或别名查询候选。
- 保留全部已返回的同名候选、资料出处和空坐标，不自动确认历史地点。
- 查看原文、选择候选，并把抽取结果与人工选择导出为 JSON 文件。
- 不配置模型和数据库也可查看固定人工演示；演示不能证明真实抽取准确率。

当前程序支持信息抽取、结构校验、MySQL 地名库查询、同名候选保留及出处展示，并支持对照史料原文进行人工选择、导出 JSON。候选出处来自地名数据本身，人工选择不代表已经完成历史地点考证。

史料研究记录、人工选择及进一步考证依据写入 MySQL，以及后续 ArcGIS Pro 接入，尚未实现。完整研究目标及范围调整见[项目目标与研究复盘](docs/project-history.md)。

## 技术环境

Python 3.11+；FastAPI、Uvicorn；Pydantic 2、JSON；OpenAI Python SDK（兼容接口客户端）、ModelScope API、MiniMax-M2.5（可配置模型）；MySQL 8.4、PyMySQL；HTML、CSS、原生 JavaScript；pytest／HTTPX。

## 快速开始：只查看人工演示

下载或克隆本仓库，在终端进入项目根目录。安装 Python 3.11 或更高版本后运行以下命令（适用于 macOS／Linux）：

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

浏览器打开 <http://127.0.0.1:8000>，点击“查看人工演示”。示例句子、人物、地名和坐标均为人工测试材料。

## 配置真实模型和 MySQL

1. 若人工演示服务仍在运行，先按 Ctrl+C 停止。复制 `.env.example` 为 `.env`，在本地填写模型密钥与自选数据库密码，完成配置后重新启动服务。
2. 模型入口和模型 ID 都可配置。在线调用取决于服务商账号、授权和当前模型可用性；真实模型调用与史料抽取效果仍需测试核验。
3. 运行 MySQL。已安装 MySQL 时直接填写连接信息；已安装 Docker 时可使用本仓库的 Compose：

```sh
cp .env.example .env
# 用编辑器填写 .env 中的密钥与密码，再运行：
docker compose up -d --wait
python -m scripts.manage init-db
```

上述 Compose 配置默认将 MySQL 的 3306 端口映射到本机 3307 端口。若使用已有 MySQL，请先准备数据库及有权建表和导入数据的账号，再按实际端口和连接信息修改 `.env`。

可选：使用独立的测试数据库，先用附带的人工数据验证导入与查询（请勿与正式地名库混用）：

```sh
python -m scripts.manage import --places examples/places_synthetic.csv --aliases examples/aliases_synthetic.csv
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

查询“例示寺”应保留两个候选，查询“レイジデラ”应通过别名找到同样的两个候选。“坐标未定”的坐标仍为空。

## 导入真实历史地名数据

如已导入人工测试数据，请先准备一个空的正式数据库，并将 `.env` 中的连接信息切换至该库。Compose 中的数据库创建配置仅在数据卷首次初始化时生效，修改 `MYSQL_DATABASE` 不会自动在已有数据卷中创建新库；详见 [MySQL 镜像说明](https://github.com/docker-library/docs/blob/master/mysql/README.md)。

来源为[人间文化研究机构（NIHU）的历史地名数据发布页](https://www.nihu.jp/ja/database/source_map.html)，编制机构为 NIHU 与 H-GIS 研究会。

从官方发布页取得数据并解压，把主表与别名表放进 `data/`（该目录内容不会提交）。原始扩展名可能为 TXT，内容实为 UTF-8 CSV；下载后的文件名也可能乱码，依照表头识别即可：

| 文件 | 必要字段 |
| --- | --- |
| 地名主表 | ID、地名、緯度、経度；推荐保留全部原始列 |
| 地名别名表 | ID、地名ID、別名 |

```sh
python -m scripts.manage import --places data/地名.txt --aliases data/地名_別名.txt
```

导入命令同时输出输入记录数与数据库实际记录数。按 ID 更新，不按名称去重；同名地点可能是不同实体。数据导入失败会回滚本次数据写入；表结构创建不参与该回滚。重复运行不复制同一 ID，但不会自动删除旧版本中已消失的记录。换版本时建议使用新的数据库。

本仓库不附带完整公开数据，也不附带作者（@Fuyusaka-Johnny）课题研究与论文撰写所使用的未确认可公开史料。使用公开数据集时请遵循[来源及加工说明要求](https://www.nihu.jp/ja/database/source_map/about.html)；以官方发布页链接的最新使用说明为准。对外说明应注明“利用 NIHU 与 H-GIS 研究会的历史地名辞书数据，本项目进行了数据库导入与候选检索处理”。

导入完成后，重新运行前述 `uvicorn` 启动命令，在页面粘贴史料正文并点击“抽取信息并查询 MySQL”。“查看人工演示”始终使用固定人工材料，不会验证真实模型或数据库连接。

## 进一步阅读

- [技术流程、接口与字段](docs/technical.md)
- [项目目标、研究流程与未接入 ArcGIS 的原因](docs/project-history.md)

## 运行验证

```sh
pip install -r requirements-dev.txt
pytest -q
# 连接独立的测试 MySQL 库后再运行，测试会写入人工数据：
RUN_MYSQL_TESTS=1 pytest -q
```

已提供 GitHub Actions，使用独立 MySQL 服务运行集成测试；工作流是否通过以仓库实际运行结果为准。真实模型效果需要具体测试核验。

## 写在最后
本工程需求分析、程序实现感谢@TKFTNU 的支持。本工程代码撰写均由Codex完成。
