# 发布到 GitHub

建议仓库名称：`historical-source-geocoding`。先完整检查工程，再决定公开或私有；此说明不代表已经创建远程仓库。

## 仓库内容

提交本项目源文件、README、docs、人工示例与测试。完整地名数据放在被忽略的 `data/`，真实配置只保存在 `.env`。原文件的真实密钥、数据库密码与服务器地址不在本项目中。

说明项目由研究者提供应用背景、协作者及 AI 辅助实现；原项目和重写版贡献分别描述。若要加入朋友编写的原代码，先与朋友确认许可与署名。当前没有擅自给朋友代码设置开源许可证；公开可读也不等于授予任意再使用许可。

## 有 Git 和 GitHub CLI 时

以下命令在项目目录运行。先通过 GitHub 登录，并确认账户与仓库可见性。没有授权用户账号之前不要代填作者身份。

```sh
git init -b main
git add .
git status --short
git diff --cached
git commit -m "Add MySQL historical-source review prototype"
gh auth login
gh repo create historical-source-geocoding --private --source=. --remote=origin --push
```

准备公开展示时，再在 GitHub 仓库设置中修改可见性，并确认没有提交配置或受限史料。`.github/workflows/tests.yml` 会在推送后运行；查看运行结果后再声称 CI 通过。

## 网页上传时

在 GitHub 新建空仓库，选择可见性，再用“上传文件”上传工程源文件。上传前展开压缩包，确保不是只提交一个 ZIP，也不要上传本地 `.venv`。网页对隐藏目录处理有限，建议优先用 Git 提交以保留 `.github` 和 `.gitignore`。

可使用仓库简介：

> 日文史料结构化与历史地名核验原型：可配置 LLM、MySQL 地名库、多候选保留与人工核验。ArcGIS 接入仍为后续计划。
