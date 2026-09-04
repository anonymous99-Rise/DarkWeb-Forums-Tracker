# 更新日志 (CHANGELOG)


## [V1.0.10b] - 2026-09-04
- 修复多个问题： - should_sleep()时间计算改用timedelta正确计算北京时间 - 周报日期范围从SQL改为Python计算（修正+7days错误） - RSS feed添加XML entity转义（xml.sax.saxutils.escape） - index.html RSS订阅链接添加/DarkWeb-Forums-Tracker前缀 - 修复template.html拼写错误'Gne' - 删除重复的regex清理代码 - 主workflow改为每30分钟执行一次 - 禁用Daily_Report定时调度避免冲突
## [V1.0.9b] - 2026-01-05

### 新增
- **Zeabur 镜像部署支持**：增加 `Dockerfile` 和 GitHub Actions 工作流，支持自动构建镜像并推送到 GHCR。
- **部署文档更新**：在 `README.md` 中增加了 Zeabur 和 Docker 的部署指南。

### 优化
- **GitHub Actions**：调整了 `docker-publish.yml` 以支持多平台和自动标签提取。
