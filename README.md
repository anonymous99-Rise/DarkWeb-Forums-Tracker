# DarkWeb Forums Tracker

一个基于Python的DarkWeb论坛数据泄露监控工具，可以定期检查DarkWeb论坛的更新，并通过多种渠道推送通知。

## 版本信息

当前版本：**V1.0.11b**

版本创建时间：2026-09-04

## 功能特点

- 支持多个RSS源监控
- 多种推送渠道：钉钉、飞书、Telegram Bot、Discard
- **Discord Embed推送**：使用卡片式推送，卡片颜色随机
- **支持数据源开关**：可通过配置文件启用/禁用各个RSS数据源
- **日报和周报生成**：自动生成日报和周报，包含实际数据统计
- **RSS feed生成**：支持生成每日和每周的RSS feed
- 支持夜间休眠（北京时间0-7点），避免打扰
- 支持通过GitHub Action定时运行
- 支持通过提交Issue添加新的RSS源
- 环境变量优先级高于配置文件
- 数据持久化存储
- **周报自动推送**：每周五15:00北京时区自动生成并推送周报

## 安装

1. 克隆仓库
```bash
git clone https://github.com/adminlove520/DarkWeb-Forums-Tracker.git
cd DarkWeb-Forums-Tracker
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

## 配置

### 1. 配置文件 (`config.yaml`)

```yaml
# 配置推送
push:
  dingding:
    webhook: "https://oapi.dingtalk.com/robot/send?access_token=你的token"
    secret_key: "你的Key"
    app_name: "钉钉"
    switch: "ON"  # 设置开关为 "ON" 进行推送，设置为其他值则不进行推送
  feishu:
    webhook: "飞书的webhook地址"
    app_name: "飞书"
    switch: "OFF"
  tg_bot:
    token: "Telegram Bot的token"
    group_id: "Telegram Bot的group_id"
    app_name: "Telegram Bot"
    switch: "OFF"
  discard:
    webhook: "discard的webhook地址"
    app_name: "Discard"
    switch: "OFF"  # 总开关
    send_daily_report: "OFF"  # 推送日报开关（日报默认只存储不推送）
    send_normal_msg: "ON"  # 推送普通消息开关
    send_weekly_report: "ON"  # 推送周报开关

# 代理配置
proxy:
  enable: "OFF"  # 设置为 "ON" 启用代理
  http_proxy: "http://proxy.example.com:8080"  # HTTP代理地址
  https_proxy: "https://proxy.example.com:8080"  # HTTPS代理地址
  no_proxy: "localhost,127.0.0.1"  # 不使用代理的地址列表

# 夜间休眠配置
night_sleep:
  switch: "ON"  # 设置开关为 "ON" 开启夜间休眠，设置为其他值则关闭

# 日报配置
daily_report:
  switch: "ON"  # 是否生成日报
  push_switch: "OFF"  # 日报只存储不推送，固定为OFF

# 周报配置
weekly_report:
  switch: "ON"  # 是否生成周报
  push_switch: "ON"  # 是否推送周报
  time: "15:00"  # 推送时间（北京时区）
  day: 5  # 推送日期（周五）

# RSS数据源开关配置
datasources:
  "Xforums.st": 1  # 1启用, 0禁用
  "gerki": 1
  "blackbones": 1
  "hard-tm": 1
  "ascarding": 1
  "htdark": 1
  "niflheim": 1
  "mipped": 1
  "leakbase": 1
  "dublikat": 1
  "darkforums.io": 1
  "sinister": 1
  "cardforum": 1
  "ipbmafia": 1
```

#### 代理配置说明

- **enable**: 代理总开关，设置为 "ON" 启用代理，"OFF" 禁用代理
- **http_proxy**: HTTP代理地址，格式为 `http://proxy.example.com:8080`
- **https_proxy**: HTTPS代理地址，格式为 `https://proxy.example.com:8080`
- **no_proxy**: 不使用代理的地址列表，多个地址用逗号分隔

代理配置支持所有推送渠道，包括：
- 钉钉
- 飞书
- Telegram Bot
- Discard

### 2. RSS源配置 (`rss_dataleak.yaml`)

```yaml
"Xforums.st":
  "rss_url": "https://xforums.st/forums/-/index.rss"
  "website_name": "Xforums.st"
"gerki":
  "rss_url": "https://forum.gerki.ws/forums/-/index.rss"
  "website_name": "gerki"
"blackbones":
  "rss_url": "https://blackbones.net/forums/-/index.rss"
  "website_name": "blackbones"
```

### 3. 环境变量

环境变量优先级高于配置文件，可以通过环境变量覆盖配置：

| 环境变量名 | 说明 |
| --- | --- |
| DINGDING_WEBHOOK | 钉钉机器人Webhook |
| DINGDING_SECRET | 钉钉机器人密钥 |
| DINGDING_SWITCH | 钉钉推送开关（ON/OFF） |
| FEISHU_WEBHOOK | 飞书机器人Webhook |
| FEISHU_SWITCH | 飞书推送开关（ON/OFF） |
| TELEGRAM_TOKEN | Telegram Bot Token |
| TELEGRAM_GROUP_ID | Telegram群组ID |
| TELEGRAM_SWITCH | Telegram推送开关（ON/OFF） |
| DISCARD_WEBHOOK | Discard Webhook |
| DISCARD_SWITCH | Discard总推送开关（ON/OFF） |
| DISCARD_SEND_DAILY_REPORT | Discard推送日报开关（ON/OFF） |
| DISCARD_SEND_NORMAL_MSG | Discard推送普通消息开关（ON/OFF） |
| DISCARD_SEND_WEEKLY_REPORT | Discard推送周报开关（ON/OFF） |
| PROXY_ENABLE | 是否启用代理（ON/OFF） |
| HTTP_PROXY | HTTP代理地址 |
| HTTPS_PROXY | HTTPS代理地址 |
| NO_PROXY | 不使用代理的地址列表 |
| NIGHT_SLEEP_SWITCH | 夜间休眠开关（ON/OFF） |
| DAILY_REPORT_SWITCH | 是否生成日报（ON/OFF） |
| WEEKLY_REPORT_SWITCH | 是否生成周报（ON/OFF） |
| WEEKLY_REPORT_PUSH_SWITCH | 是否推送周报（ON/OFF） |
| DATASOURCE_Xforums.st | Xforums.st数据源开关（1启用/0禁用） |
| DATASOURCE_gerki | gerki数据源开关（1启用/0禁用） |
| DATASOURCE_blackbones | blackbones数据源开关（1启用/0禁用） |
| DATASOURCE_hard-tm | hard-tm数据源开关（1启用/0禁用） |
| DATASOURCE_ascarding | ascarding数据源开关（1启用/0禁用） |
| DATASOURCE_htdark | htdark数据源开关（1启用/0禁用） |
| DATASOURCE_niflheim | niflheim数据源开关（1启用/0禁用） |
| DATASOURCE_mipped | mipped数据源开关（1启用/0禁用） |
| DATASOURCE_leakbase | leakbase数据源开关（1启用/0禁用） |
| DATASOURCE_dublikat | dublikat数据源开关（1启用/0禁用） |
| DATASOURCE_darkforums.io | darkforums.io数据源开关（1启用/0禁用） |
| DATASOURCE_sinister | sinister数据源开关（1启用/0禁用） |
| DATASOURCE_cardforum | cardforum数据源开关（1启用/0禁用） |
| DATASOURCE_ipbmafia | ipbmafia数据源开关（1启用/0禁用） |

### 4. GitHub Action 环境变量配置

对于GitHub Action工作流来说，配置非常轻量，**只需配置推送相关的环境变量**即可，其余配置项都已在`config.yaml`中预先配置好：

#### 必要的环境变量

| 环境变量名 | 说明 | 工作流使用场景 |
| --- | --- | --- |
| DISCARD_WEBHOOK | Discard Webhook地址 | 所有工作流 |
| DISCARD_SWITCH | Discard总推送开关 | 所有工作流 |
| DISCARD_SEND_NORMAL_MSG | 普通消息推送开关 | 主工作流 |
| DISCARD_SEND_WEEKLY_REPORT | 周报推送开关 | 周报工作流 |

#### 可选的环境变量

| 环境变量名 | 说明 | 工作流使用场景 |
| --- | --- | --- |
| DINGDING_WEBHOOK | 钉钉机器人Webhook | 所有工作流 |
| DINGDING_SECRET | 钉钉机器人密钥 | 所有工作流 |
| DINGDING_SWITCH | 钉钉推送开关 | 所有工作流 |
| FEISHU_WEBHOOK | 飞书机器人Webhook | 所有工作流 |
| FEISHU_SWITCH | 飞书推送开关 | 所有工作流 |
| TELEGRAM_TOKEN | Telegram Bot Token | 所有工作流 |
| TELEGRAM_GROUP_ID | Telegram群组ID | 所有工作流 |
| TELEGRAM_SWITCH | Telegram推送开关 | 所有工作流 |

#### 配置说明

1. **配置轻量**：GitHub Action只需要配置推送相关的环境变量，其余配置都在`config.yaml`中预先设置
2. **优先级**：环境变量会覆盖`config.yaml`中的配置，便于在不同环境下灵活调整
3. **安全性**：建议在GitHub仓库的`Settings > Secrets and variables > Actions`中配置环境变量，避免泄露敏感信息
4. **工作流自动使用**：配置完成后，GitHub Action工作流会自动使用这些环境变量

## 使用

### 1. 本地运行

#### 单次执行模式
```bash
python DarkWeb-Forums-Tracker.py --once
```

#### 循环执行模式
```bash
python DarkWeb-Forums-Tracker.py
```

### 2. Docker / Zeabur 部署 (推荐)

代码推送到 `main` 分支后会触发 GitHub Actions 自动构建并打包镜像至 GHCR (`ghcr.io/adminlove520/darkweb-forums-tracker:latest`)。

#### 方式一：Zeabur 部署 (云端)
1. **创建服务**：在 Zeabur 平台选择 **GitHub** 导入本仓库，或从 **容器镜像** 导入 `ghcr.io/adminlove520/darkweb-forums-tracker:latest`。
2. **环境变量**：在 Zeabur 服务设置中配置以下环境变量（至少需配置一种推送方式）：
   - `DISCARD_WEBHOOK`: Discord Webhook 地址
   - `DISCARD_SWITCH`: `ON`
   - `TZ`: `Asia/Shanghai`
3. **数据持久化 (关键)**：
   - 默认情况下容器重启会导致 `data_leaks.db` 重置。
   - 在 Zeabur 服务页面点击 **Storage** (或 **Volumes**)。
   - 点击 **Add Volume**，挂载路径填写 `/app/data_leaks.db`（挂载到文件）。
   - 重启服务即可。

#### 方式二：Docker 手动运行 (本地/服务器)
```bash
docker run -d \
  --name darkweb-tracker \
  -e DISCARD_WEBHOOK="你的Webhook" \
  -e DISCARD_SWITCH="ON" \
  -v $(pwd)/data_leaks.db:/app/data_leaks.db \
  ghcr.io/adminlove520/darkweb-forums-tracker:latest
```

### 3. GitHub Action 部署

项目包含三个GitHub Action工作流：

1. **DarkWeb-Forums-Tracker.yml**：定期运行DarkWeb论坛监控
   - 执行时间：北京时间9:00-23:00，每小时执行一次
   - 运行时长：每个工作流运行59分钟
   - 夜间休眠：完全跳过北京时间0-7点的触发
   - 运行模式：默认使用循环模式，每2小时检查一次

2. **DarkWeb-Forums-Tracker-Weekly.yml**：每周生成并推送周报
   - 执行时间：每周五15:00北京时区
   - 生成周报并推送
   - 更新周报RSS feed

3. **add-rss-from-issue.yml**：通过提交Issue添加新的RSS源
   - 支持两种格式提交
   - 自动更新rss.yaml
   - 自动回复并关闭Issue

### 3. 夜间休眠功能

- **默认开启**：在北京时间0-7点之间自动休眠
- **双重保障**：
  1. GitHub Action工作流在0-7点不触发
  2. 脚本内置夜间休眠功能
- **灵活控制**：支持通过配置文件和环境变量控制

### 4. 数据存储

监控的数据会存储在 `data_leaks.db` SQLite数据库中，包含以下字段：
- id：自增主键
- title：数据泄露信息标题
- link：数据泄露信息链接
- timestamp：添加时间

### 5. 推送格式

推送内容格式示例：
```
Xforums.st今日更新
标题: Blockchain Log
链接: `https://xforums.st/threads/blockchain-log.225/`
推送时间：2026-01-03 15:30:00
```

### 6. 通过Issue添加RSS源

您可以通过提交Issue来添加新的RSS源，支持两种格式：

#### 格式1
```
论坛名称: Xforums.st
RSS URL: https://xforums.st/forums/-/index.rss
```

#### 格式2
直接在标题或正文中包含论坛名称和URL，例如：

标题：添加Xforums.st
正文：https://xforums.st/forums/-/index.rss

### 7. 配置优先级

配置项的优先级从高到低：
1. 命令行参数
2. 环境变量
3. 配置文件 (`config.yaml`)
4. 默认值

### 8. 异常处理

- 出现异常时，等待1分钟后继续执行
- 确保数据库连接正确关闭
- 详细的错误日志输出

### 9. 性能优化

- 每2小时检查一次所有RSS源
- 夜间自动休眠，节省资源
- 数据库缓存，避免重复推送
- 高效的异常处理机制

### 10. 资源消耗

- 内存占用：约50-100MB
- CPU使用率：低，主要在检查RSS源时占用
- 网络请求：每次检查RSS源时发送请求
- 存储占用：随着时间增长，data_leaks.db会逐渐增大

### 11. RSS Feed 使用说明

#### RSS文件位置

生成的RSS文件存储在 `rss/` 目录下：

```
├── rss/
│   ├── daily_rss_YYYY-MM-DD.xml       # 特定日期的日报RSS
│   ├── weekly_rss_YYYY-MM-DD_YYYY-MM-DD.xml  # 特定时间段的周报RSS
│   ├── latest_daily_rss.xml          # 固定链接，始终指向最新的日报RSS（推荐订阅）
│   └── latest_weekly_rss.xml         # 固定链接，始终指向最新的周报RSS（推荐订阅）
```

#### 如何使用RSS Feed

1. **获取RSS链接**
   - 如果在本地使用，RSS文件路径为：`http://localhost:PORT/rss/latest_daily_rss.xml`
   - 如果部署在GitHub Pages，RSS文件URL为：`https://yourusername.github.io/DarkWeb-Forums-Tracker/rss/latest_daily_rss.xml`

2. **订阅RSS**
   - 使用任意RSS阅读器（如Feedly、Inoreader、Reeder等）
   - 复制RSS文件的URL
   - 在RSS阅读器中添加订阅
   - 阅读器会自动更新，推送最新的数据泄露信息

3. **推荐订阅**
   - 对于普通用户，推荐订阅 `latest_daily_rss.xml` 获取每日更新
   - 对于需要定期总结的用户，可以同时订阅 `latest_weekly_rss.xml`
   - 开发者可以将这些RSS源集成到其他系统中，实现自动化监控

4. **RSS内容说明**
   - 每个RSS条目包含标题、链接和发布时间
   - 内容与Discord推送的内容保持一致
   - 支持RSS 2.0格式
   - 支持Atom阅读器订阅

5. **自动更新机制**
   - 日报RSS：每日自动更新
   - 周报RSS：每周五自动更新
   - `latest_*` 文件：每次生成新报告时自动更新

#### RSS Feed优势

- **实时更新**：第一时间获取最新数据泄露信息
- **跨平台支持**：支持各种RSS阅读器和平台
- **无广告干扰**：纯净的信息推送
- **灵活订阅**：可根据需求选择订阅类型
- **便于集成**：易于与其他系统集成

### 12. 支持的RSS阅读器

以下是一些推荐的RSS阅读器：

- **桌面端**：
  - Feedly（跨平台）
  - Inoreader（跨平台）
  - Reeder（macOS）
  - NewsBlur（跨平台）
  - FreshRSS（自托管）

- **移动端**：
  - Feedly（iOS/Android）
  - Inoreader（iOS/Android）
  - Reeder（iOS）
  - NewsBlur（iOS/Android）
  - Feeder（Android）

- **浏览器扩展**：
  - RSS Feed Reader（Chrome）
  - RSS Guard（Firefox）
  - Feedbro（Chrome/Firefox）

## 开发说明

### 1. 目录结构

```
DarkWeb-Forums-Tracker/
├── DarkWeb-Forums-Tracker.py         # 主脚本
├── add_rss_from_issue.py  # Issue处理脚本
├── config.yaml            # 配置文件
├── rss_dataleak.yaml      # 数据泄露RSS源配置
├── data_leaks.db          # 数据存储
├── requirements.txt       # 依赖列表
├── .gitignore            # Git忽略文件
├── README.md             # 项目说明
├── archive/              # 日报和周报存储目录
├── rss/                  # RSS feed存储目录
└── .github/
    └── workflows/
        ├── DarkWeb-Forums-Tracker.yml           # 主工作流
        ├── DarkWeb-Forums-Tracker-Weekly.yml    # 周报工作流
        └── add-rss-from-issue.yml               # Issue处理工作流
```

### 2. 依赖管理

- 使用pip管理依赖
- 依赖列表存储在requirements.txt中
- 定期更新依赖版本

### 3. 测试

- 本地测试：使用--once参数进行单次测试
- 手动触发：通过GitHub Action的workflow_dispatch手动触发
- 日志检查：查看GitHub Action的运行日志

### 4. 贡献指南

- 提交Issue：报告问题或建议
- 提交PR：修复bug或添加新功能
- 遵循Python代码规范
- 添加必要的注释
- 测试通过后提交

## 更新日志

- 2023.10.10：初始版本
- 2025.10.11：
  - 增加夜间休眠功能
  - 支持通过Issue添加RSS源
  - 完善配置文件支持
  - 优化推送逻辑
- 2025.10.15：
  - 调整GitHub Action执行时间为北京时间9:00-23:00
  - 优化工作流运行时长为59分钟
  - 移除--once参数，默认使用循环模式
  - 完善README文档
  - 添加Issue模板
- 2025.12.25：
  - 移除Server酱和PushPlus推送方式
  - 新增Discard推送渠道
  - 支持Discard推送日报功能
  - 支持Discard单独开关控制日报和普通消息推送
  - 更新GitHub Action工作流配置
  - 修复代码缩进问题
  - 完善README文档
- 2026.1.1：
  - 实现Discord Embed推送，卡片颜色随机
  - 新增数据源开关配置，支持通过配置文件启用/禁用各RSS数据源
  - 实现日报和周报RSS feed生成
  - 新增周报生成功能，每周五15:00北京时区自动生成并推送
  - 支持每日推送和周报分离推送，可独立配置
  - 新增weekly_report配置项
  - 更新GitHub Action工作流，添加周报生成工作流
  - 优化统计功能，只显示指定统计项
  - 完善README文档

- 2026.1.5：
  - **支持 Zeabur 镜像部署**：提供 Dockerfile 和自动构建工作流。
  - **持久化改进**：明确了容器化环境下的 SQLite 数据持久化方案。
  - **文档同步**：同步更新 README 中的部署指南和系统版本。

- 2026.1.3：
  - 改进RSS解析逻辑，支持更多文件类型和链接格式
  - 优化日报和周报的UI设计，采用现代化渐变色彩和动画效果
  - 更新index.html模板，提升视觉体验
  - 优化RSS链接提取，增加无效链接过滤
  - 完善内容清理，移除更多无用信息
  - 更新README.md，添加详细的RSS使用说明
  - 更新add_rss_source.yml模板，优化DarkWeb论坛RSS源提交流程
  - 支持更多语言的登录提示处理
  - 优化下载链接提取正则表达式
  - 增加常见文件托管服务支持
  - 改进响应式设计，适配更多设备
  - 实现平滑的加载动画效果
  - 优化代码结构，提高可维护性
  - 优化Discord 429速率限制处理，实现指数退避+随机抖动重试策略
  - 添加动态版本管理功能，从Git仓库自动获取版本信息
  - 实现GitHub Action自动版本更新，每次提交到main分支自动递增版本号
  - 优化启动卡片显示，动态展示推送渠道和运行模式

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

如有问题或建议，欢迎通过以下方式联系：
- GitHub Issue：提交到项目仓库
- 邮箱：your-email@example.com

## 致谢

感谢所有贡献者和使用本项目的用户！

## 通过Issue添加RSS源

您可以通过提交Issue来添加新的RSS源，支持两种格式：

### 格式1
```
网站名称: 示例网站
RSS URL: https://example.com/feed.xml
```

### 格式2
直接在标题或正文中包含网站名称和URL，例如：

标题：添加示例网站
正文：https://example.com/feed.xml

## 夜间休眠功能

默认情况下，脚本会在北京时间0-7点之间自动休眠，跳过推送。您可以通过以下方式控制：

1. 修改 `config.yaml` 中的 `night_sleep.switch` 配置
2. 设置环境变量 `NIGHT_SLEEP_SWITCH`

## 数据存储

监控的数据会存储在 `data_leaks.db` SQLite数据库中，包含以下字段：
- id：自增主键
- title：数据泄露信息标题
- link：数据泄露信息链接
- timestamp：添加时间

## 推送渠道

### 1. 钉钉

- 支持签名验证
- 发送文本消息

### 2. 飞书

- 支持飞书机器人API
- 发送文本消息

### 3. Telegram Bot

- 支持Telegram群组推送
- 需创建Bot获取Token

### 4. Discard

- 支持两种推送方式：
  - 普通消息推送（与钉钉格式相同）
  - 日报推送（HTML格式）
- 支持单独开关控制日报和普通消息推送
- 需配置Webhook地址

## 日志

- 控制台输出执行日志
- 错误信息会打印到控制台

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！