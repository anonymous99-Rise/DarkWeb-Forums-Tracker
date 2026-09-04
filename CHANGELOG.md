# 更新日志 (CHANGELOG)


## [V1.0.12b] - 2026-09-04
- 修复workflow重复push定义

## [V1.0.11b] - 2026-09-04
- 修复workflow配置： - 夜间休眠默认关闭（NIGHT_SLEEP_SWITCH='OFF'） - 添加push trigger，代码推送自动触发workflow

## [V1.0.10b] - 2026-09-04
- 重构前端：全新现代化UI设计
## [V1.0.9b] - 2026-01-05

### 新增
- **Zeabur 镜像部署支持**：增加 `Dockerfile` 和 GitHub Actions 工作流，支持自动构建镜像并推送到 GHCR。
- **部署文档更新**：在 `README.md` 中增加了 Zeabur 和 Docker 的部署指南。

### 优化
- **GitHub Actions**：调整了 `docker-publish.yml` 以支持多平台和自动标签提取。
