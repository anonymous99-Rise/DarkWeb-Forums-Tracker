import sqlite3
import feedparser
import yaml
import requests
import time
import os
import argparse
import random
from datetime import datetime, timedelta
import dingtalkchatbot.chatbot as cb
from jinja2 import Template
from xml.sax.saxutils import escape

# 版本信息
__version__ = "V1.0.9b"

# 从Git仓库动态获取版本信息
def get_git_version():
    """
    从Git仓库获取当前版本信息
    优先使用Git tag，如果没有tag则使用提交哈希
    """
    try:
        import subprocess
        
        # 尝试获取最近的Git tag
        tag_result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if tag_result.returncode == 0:
            tag = tag_result.stdout.strip()
            return tag
        else:
            # 如果没有tag，使用提交哈希
            commit_result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if commit_result.returncode == 0:
                commit_hash = commit_result.stdout.strip()
                return f"V1.0.3b-{commit_hash}"
            else:
                # 如果无法获取Git信息，使用默认版本
                return __version__
    except Exception as e:
        # 任何异常都返回默认版本
        print(f"获取Git版本信息失败: {str(e)}")
        return __version__

# 站点名称到URL的映射字典
site_url_map = {
    "Xforums.st": "https://Xforums.st",
    "gerki": "https://gerki",
    "blackbones": "https://blackbones",
    "hard-tm": "https://hard-tm",
    "ascarding": "https://ascarding",
    "htdark": "https://htdark",
    "niflheim": "https://niflheim",
    "mipped": "https://mipped",
    "leakbase": "https://leakbase",
    "dublikat": "https://dublikat",
    "darkforums.io": "https://darkforums.io",
    "sinister": "https://sinister",
    "cardforum": "https://cardforum",
    "ipbmafia": "https://ipbmafia"
}

# 检查网站可用性的函数
def check_site_availability(site_name):
    """
    检查网站可用性
    根据site_name映射到实际URL进行真实的HTTP请求检查
    """
    # 获取站点对应的URL
    site_url = site_url_map.get(site_name)
    if not site_url:
        # 如果没有找到对应的URL，默认返回可用
        return True
    
    try:
        # 发送HEAD请求检查网站可用性，将超时时间减少到2秒
        # 添加代理支持和其他优化
        proxies = get_proxies()
        response = requests.head(
            site_url, 
            timeout=2, 
            proxies=proxies,
            allow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        # 如果状态码在200-399之间，认为网站可用
        return 200 <= response.status_code < 400
    except requests.RequestException as e:
        # 任何异常都认为网站不可用，不打印详细错误
        return False

# 加载配置文件
def load_config():
    # 从文件加载配置
    config = {}
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    except FileNotFoundError:
        print("未找到config.yaml文件，将使用环境变量配置")
    except Exception as e:
        print(f"加载config.yaml文件出错: {str(e)}")
    
    # 初始化push配置
    push_config = config.get('push', {})
    
    # 钉钉推送配置 - 环境变量优先级高于配置文件
    if 'dingding' not in push_config:
        push_config['dingding'] = {}
    
    push_config['dingding']['webhook'] = os.environ.get('DINGDING_WEBHOOK', push_config['dingding'].get('webhook', ''))
    push_config['dingding']['secret_key'] = os.environ.get('DINGDING_SECRET', push_config['dingding'].get('secret_key', ''))
    push_config['dingding']['switch'] = os.environ.get('DINGDING_SWITCH', push_config['dingding'].get('switch', 'OFF'))
    
    # 飞书推送配置 - 环境变量优先级高于配置文件
    if 'feishu' not in push_config:
        push_config['feishu'] = {}
    
    push_config['feishu']['webhook'] = os.environ.get('FEISHU_WEBHOOK', push_config['feishu'].get('webhook', ''))
    push_config['feishu']['switch'] = os.environ.get('FEISHU_SWITCH', push_config['feishu'].get('switch', 'OFF'))
    
    # Telegram Bot推送配置 - 环境变量优先级高于配置文件
    if 'tg_bot' not in push_config:
        push_config['tg_bot'] = {}
    
    push_config['tg_bot']['token'] = os.environ.get('TELEGRAM_TOKEN', push_config['tg_bot'].get('token', ''))
    push_config['tg_bot']['group_id'] = os.environ.get('TELEGRAM_GROUP_ID', push_config['tg_bot'].get('group_id', ''))
    push_config['tg_bot']['switch'] = os.environ.get('TELEGRAM_SWITCH', push_config['tg_bot'].get('switch', 'OFF'))
    
    # Discard推送配置 - 环境变量优先级高于配置文件
    if 'discard' not in push_config:
        push_config['discard'] = {}
    
    push_config['discard']['webhook'] = os.environ.get('DISCARD_WEBHOOK', push_config['discard'].get('webhook', ''))
    push_config['discard']['switch'] = os.environ.get('DISCARD_SWITCH', push_config['discard'].get('switch', 'OFF'))
    push_config['discard']['send_daily_report'] = os.environ.get('DISCARD_SEND_DAILY_REPORT', push_config['discard'].get('send_daily_report', 'OFF'))
    push_config['discard']['send_normal_msg'] = os.environ.get('DISCARD_SEND_NORMAL_MSG', push_config['discard'].get('send_normal_msg', 'ON'))
    push_config['discard']['send_weekly_report'] = os.environ.get('DISCARD_SEND_WEEKLY_REPORT', push_config['discard'].get('send_weekly_report', 'ON'))
    
    # 添加夜间休眠配置
    config['night_sleep'] = {
        'switch': os.environ.get('NIGHT_SLEEP_SWITCH', config.get('night_sleep', {}).get('switch', 'ON'))
    }
    
    # 添加生成日报配置
    config['daily_report'] = {
        'switch': os.environ.get('DAILY_REPORT_SWITCH', config.get('daily_report', {}).get('switch', 'ON')),
        'push_switch': 'OFF'  # 日报只存储不推送，固定为OFF
    }
    
    # 添加周报配置
    config['weekly_report'] = {
        'switch': os.environ.get('WEEKLY_REPORT_SWITCH', config.get('weekly_report', {}).get('switch', 'ON')),
        'push_switch': os.environ.get('WEEKLY_REPORT_PUSH_SWITCH', config.get('weekly_report', {}).get('push_switch', 'ON')),
        'time': config.get('weekly_report', {}).get('time', '15:00'),
        'day': config.get('weekly_report', {}).get('day', 5)
    }
    
    # 添加RSS数据源开关配置
    config['datasources'] = config.get('datasources', {
        "Xforums.st": 1,
        "gerki": 1,
        "blackbones": 1,
        "hard-tm": 1,
        "ascarding": 1,
        "htdark": 1,
        "niflheim": 1,
        "mipped": 1,
        "leakbase": 1,
        "dublikat": 1,
        "darkforums.io": 1,
        "sinister": 1,
        "cardforum": 1,
        "ipbmafia": 1
    })
    
    # 加载代理配置
    proxy_config = config.get('proxy', {})
    config['proxy'] = {
        'enable': os.environ.get('PROXY_ENABLE', proxy_config.get('enable', 'OFF')),
        'http_proxy': os.environ.get('HTTP_PROXY', proxy_config.get('http_proxy', '')),
        'https_proxy': os.environ.get('HTTPS_PROXY', proxy_config.get('https_proxy', '')),
        'no_proxy': os.environ.get('NO_PROXY', proxy_config.get('no_proxy', ''))
    }
    
    config['push'] = push_config
    return config

# 判断是否应该进行夜间休眠
def should_sleep():
    # 加载配置
    config = load_config()
    # 检查是否开启夜间休眠功能
    sleep_switch = os.environ.get('NIGHT_SLEEP_SWITCH', config.get('night_sleep', {}).get('switch', 'ON'))
    if sleep_switch != 'ON':
        return False
    
    # 判断当前时间（北京时间）是否在0-7点之间
    # 获取当前UTC时间，转换为北京时间（UTC+8）
    now_utc = datetime.utcnow()
    # 正确转换为北京时间
    now_bj = now_utc + timedelta(hours=8)

    return now_bj.hour < 7

# 初始化数据库

def init_database():
    conn = sqlite3.connect('data_leaks.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        link TEXT,
        pub_date TEXT,
        author TEXT,
        category TEXT,
        content TEXT,
        download_links TEXT,
        site_name TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    return conn

# 获取数据并检查更新
def check_for_updates(feed_url, site_name, cursor, conn, send_push=True):
    print(f"{site_name} 监控中... ")
    data_list = []
    file_data = feedparser.parse(feed_url)
    data = file_data.entries
    
    for entry in data:
        data_title = entry.get('title', '')
        data_link = entry.get('link', '')
        
        if not data_title or not data_link:
            continue
        
        # 查询数据库中是否存在相同链接的数据泄露信息
        cursor.execute("SELECT * FROM items WHERE link = ?", (data_link,))
        result = cursor.fetchone()
        if result is None:
            # 提取更多字段
            pub_date = entry.get('published', '')
            author = entry.get('author', entry.get('dc_creator', ''))
            category = ''
            if 'tags' in entry:
                category = ', '.join([tag.get('term', '') for tag in entry['tags']])
            elif 'category' in entry:
                category = entry['category']
            
            # 提取内容
            content = ''
            if 'content' in entry:
                # 处理RSS 2.0和Atom格式的content字段
                if isinstance(entry['content'], list):
                    content = entry['content'][0].get('value', '')
                else:
                    content = entry['content'].get('value', '')
            elif 'summary' in entry:
                content = entry['summary']
            elif 'description' in entry:
                content = entry['description']
            
            # 清理内容，移除登录提示等无用信息
            import re
            # 移除登录提示（英文和俄文）
            content = re.sub(r'<div class="block-mhhide block-mhhide--link">.*?</div>', '', content, flags=re.DOTALL)
            # 移除需要注册才能查看的链接提示
            content = re.sub(r'<div class="messageHide messageHide--link">.*?</div>', '', content, flags=re.DOTALL)
            # 移除需要注册才能查看的图片/附件提示
            content = re.sub(r'<div class="messageHide messageHide--attach">.*?</div>', '', content, flags=re.DOTALL)
            # 移除按钮和其他交互元素
            content = re.sub(r'<input[^>]+>', '', content, flags=re.DOTALL)
            # 移除需要注册才能查看链接的文本（英文）
            content = re.sub(r'You must be registered for see links', '', content, flags=re.IGNORECASE)
            content = re.sub(r'You must be registered for see images attach', '', content, flags=re.IGNORECASE)
            # 移除需要注册才能查看链接的文本（俄文）
            content = re.sub(r'Для просмотра скрытого содержимого вы должны.*?</div>', '', content, flags=re.DOTALL)
            # 移除Read more链接
            content = re.sub(r'<a[^>]+>Read more</a>', '', content, flags=re.DOTALL)
            # 移除HTML标签，只保留文本内容用于提取下载链接
            text_content = re.sub(r'<[^>]+>', '', content)
            # 清理空白字符
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            # 提取下载链接（改进版，支持更多格式）
            download_links = ''
            # 匹配常见的下载链接格式
            # 1. 直接的URL链接，支持更多文件类型
            # 2. HTML href属性中的链接
            # 3. 带有download前缀的链接
            # 4. 包含download或file路径的链接
            download_patterns = [
                # 匹配直接的URL链接，捕获完整URL，支持更多文件类型
                r'(https?://[^\s"<>]+\.(?:zip|rar|7z|txt|csv|xlsx|pdf|exe|dmg|pkg|iso|img|torrent|json|xml))',
                # 匹配HTML href属性中的链接
                r'href=["\'](https?://[^\s"<>]+)["\']',
                # 匹配带有download前缀的链接
                r'[Dd]ownload\s*[:：]\s*(https?://[^\s"<>]+)',
                # 匹配包含download或file路径的链接
                r'(https?://[^\s"<>]+/download/[^\s"<>]+)',
                r'(https?://[^\s"<>]+/file/[^\s"<>]+)',
                r'(https?://[^\s"<>]+/files/[^\s"<>]+)',
                # 匹配常见文件托管服务的链接
                r'(https?://(?:mega\.nz|mediafire\.com|sendspace\.com|z-upload\.com|uploadfiles\.com|filefactory\.com|fileshare\.cz|rapidshare\.com|hotfile\.com|depositfiles\.com|4shared\.com)/[^\s"<>]+)',
                # 匹配带有download参数的链接
                r'(https?://[^\s"<>]+\?.*download=.*)'        
            ]
            
            all_matches = []
            # 首先从原始HTML内容中提取所有可能的链接，包括href属性
            for pattern in download_patterns:
                # 同时从原始content和text_content中提取链接
                for source in [content, text_content]:
                    matches = re.findall(pattern, source, re.IGNORECASE)
                    if matches:
                        for match in matches:
                            # 确保只添加完整的URL
                            if match and (match.startswith('http://') or match.startswith('https://')):
                                all_matches.append(match)
            
            # 去重并合并下载链接
            if all_matches:
                unique_links = list(set(all_matches))
                # 过滤掉可能的无效链接，保留真正的下载链接
                valid_links = []
                for link in unique_links:
                    # 排除可能的图片链接和其他非下载链接
                    if not any(exclude in link.lower() for exclude in ['/login/', '/register/', '/signin/', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg']):
                        valid_links.append(link)
                
                if valid_links:
                    download_links = ', '.join(valid_links)
            
            # 如果没有找到下载链接，添加提示
            if not download_links:
                download_links = '需要登录或注册才能查看下载链接'
            
            # 如果内容为空或只包含清理后的少量文本，添加提示
            if not content or len(text_content) < 10:
                content = '需要登录或注册才能查看详细内容'
            
            # 存储到数据库 with a timestamp
            cursor.execute("""
                INSERT INTO items (title, link, pub_date, author, category, content, download_links, site_name, timestamp) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (data_title, data_link, pub_date, author, category, content, download_links, site_name))
            conn.commit()
            
            # 只有在send_push为True时才发送推送
            if send_push:
                push_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                push_message(f"{site_name}今日更新", f"标题: {data_title}\n链接: {data_link}\n推送时间：{push_time}")
            
            data_list.append(data_title)
            data_list.append(data_link)
    return data_list

# 获取代理配置

def get_proxies():
    config = load_config()
    proxy_config = config.get('proxy', {})
    
    if proxy_config.get('enable', 'OFF') == 'OFF':
        return None
    
    proxies = {}
    if proxy_config.get('http_proxy'):
        proxies['http'] = proxy_config.get('http_proxy')
    if proxy_config.get('https_proxy'):
        proxies['https'] = proxy_config.get('https_proxy')
    
    return proxies if proxies else None

# 推送函数
def push_message(title, content, is_startup=False):
    config = load_config()
    push_config = config.get('push', {})
    
    # 钉钉推送
    if 'dingding' in push_config and push_config['dingding'].get('switch', '') == "ON":
        send_dingding_msg(push_config['dingding'].get('webhook'), push_config['dingding'].get('secret_key'), title,
                          content)

    # 飞书推送
    if 'feishu' in push_config and push_config['feishu'].get('switch', '') == "ON":
        send_feishu_msg(push_config['feishu'].get('webhook'), title, content)

    # Telegram Bot推送
    if 'tg_bot' in push_config and push_config['tg_bot'].get('switch', '') == "ON":
        send_tg_bot_msg(push_config['tg_bot'].get('token'), push_config['tg_bot'].get('group_id'), title, content)
    
    # Discard推送
    if 'discard' in push_config and push_config['discard'].get('switch', '') == "ON" and push_config['discard'].get('send_normal_msg', '') == "ON":
        send_discard_msg(push_config['discard'].get('webhook'), title, content, is_startup=is_startup)

# 飞书推送
def send_feishu_msg(webhook, title, content):
    feishu(title, content, webhook)

# Telegram Bot推送
def send_tg_bot_msg(token, group_id, title, content):
    tgbot(title, content, token, group_id)

# 钉钉推送
def dingding(text, msg, webhook, secretKey):
    try:
        if not webhook or webhook == "https://oapi.dingtalk.com/robot/send?access_token=你的token":
            print(f"钉钉推送跳过：webhook地址未配置")
            return
            
        if not secretKey or secretKey == "你的Key":
            print(f"钉钉推送跳过：secret_key未配置")
            return
            
        ding = cb.DingtalkChatbot(webhook, secret=secretKey)
        ding.send_text(msg='{}\r\n{}'.format(text, msg), is_at_all=False)
        print(f"钉钉推送成功: {text}")
    except Exception as e:
        print(f"钉钉推送失败: {str(e)}")

# 飞书推送
def feishu(text, msg, webhook):
    try:
        if not webhook or webhook == "飞书的webhook地址":
            print(f"飞书推送跳过：webhook地址未配置")
            return
            
        headers = {
            "Content-Type": "application/json;charset=utf-8"
        }
        data = {
            "msg_type": "text",
            "content": {
                "text": '{}\n{}'.format(text, msg)
            }
        }
        
        # 飞书推送不需要代理
        response = requests.post(webhook, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"飞书推送成功: {text}")
    except Exception as e:
        print(f"飞书推送失败: {str(e)}")

# 钉钉推送
def send_dingding_msg(webhook, secret_key, title, content):
    dingding(title, content, webhook, secret_key)

# Discard推送
def send_discard_msg(webhook, title, content, is_daily_report=False, is_weekly_report=False, html_file=None, markdown_content=None, is_startup=False):
    # 检查是否是占位符
    if not webhook or webhook == "discard的webhook地址":
        print(f"Discard推送跳过：webhook地址未配置")
        return
    
    # 检查webhook地址格式
    if not webhook.startswith('http'):
        print(f"Discard推送失败：webhook地址格式错误，必须以http或https开头")
        return
    
    try:
        headers = {
            "Content-Type": "application/json;charset=utf-8"
        }
        
        # 生成随机颜色（0-0xFFFFFF）
        random_color = random.randint(0, 0xFFFFFF)
        
        if is_startup:
            # 动态获取推送渠道
            config = load_config()
            push_config = config.get('push', {})
            enabled_channels = []
            channel_names = {
                'dingding': '钉钉',
                'feishu': '飞书',
                'tg_bot': 'Telegram Bot',
                'discard': 'Discard'
            }
            
            # 只检查定义在channel_names中的推送渠道，确保只显示真实的推送渠道
            for channel in channel_names:
                channel_config = push_config.get(channel, {})
                if channel_config.get('switch', '') == 'ON':
                    enabled_channels.append(channel_names[channel])
            
            # 动态获取运行模式
            import sys
            run_mode = '单次执行' if '--once' in sys.argv else '循环执行'
            
            # 启动卡片，使用绿色主题
            embed = {
                "title": title,
                "color": 0x57F287,  # 绿色
                "description": f"{content}",
                "fields": [
                    {"name": "启动时间", "value": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), "inline": True},
                    {"name": "服务状态", "value": "✅ 已启动", "inline": True},
                    {"name": "版本信息", "value": get_git_version(), "inline": True},
                    {"name": "监控类型", "value": "DarkWeb论坛数据泄露", "inline": True},
                    {"name": "推送渠道", "value": ", ".join(enabled_channels) if enabled_channels else "无", "inline": True},
                    {"name": "运行模式", "value": run_mode, "inline": True}
                ],
                "footer": {
                    "text": "Power By 东方隐侠安全团队·Anonymous@ 隐侠安全客栈",
                    "icon_url": "https://www.dfyxsec.com/favicon.ico"
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"  # ISO 8601格式
            }
            
            data = {
                "embeds": [embed]
            }
        elif is_weekly_report and html_file:
            # 推送周报，使用Embed卡片
            # 生成GitHub Pages URL
            github_pages_url = f"https://adminlove520.github.io/DarkWeb-Forums-Tracker/{html_file}"
            
            # 构建Embed内容
            embed = {
                "title": title,
                "color": 0x9C27B0,  # 紫色
                "description": f"共收集到 {content.split()[1]} 条数据泄露相关信息\n欢迎提交RSS源：[GitHub Issue](https://github.com/adminlove520/DarkWeb-Forums-Tracker/issues/new/choose)",
                "fields": [
                    {
                        "name": "周报链接",
                        "value": f"[Weekly_Report]({github_pages_url})",
                        "inline": False
                    },
                    {
                        "name": "数据来源",
                        "value": "DarkWeb论坛RSS源",
                        "inline": True
                    },
                    {
                        "name": "报告类型",
                        "value": "数据泄露监控周报",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "Power By 东方隐侠安全团队·Anonymous@ 隐侠安全客栈",
                    "icon_url": "https://www.dfyxsec.com/favicon.ico"
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"  # ISO 8601格式
            }
            
            data = {
                "embeds": [embed]
            }
        elif not is_daily_report:  # 普通消息推送，日报不推送
            # 构建普通消息的Embed内容
            # 解析content，提取标题和链接
            lines = content.split('\n')
            item_title = lines[0].replace('标题: ', '') if len(lines) > 0 else "无标题"
            item_link = lines[1].replace('链接: ', '') if len(lines) > 1 else ""
            push_time = lines[2].replace('推送时间：', '') if len(lines) > 2 else time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            
            embed = {
                "title": title,
                "color": random_color,
                "fields": [
                    {
                        "name": "标题",
                        "value": item_title,
                        "inline": False
                    },
                    {
                        "name": "链接",
                        "value": f"[访问链接]({item_link})",
                        "inline": False
                    },
                    {
                        "name": "推送时间",
                        "value": push_time,
                        "inline": True
                    },
                    {
                        "name": "分类",
                        "value": "数据泄露",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "Power By 东方隐侠安全团队·Anonymous@ 隐侠安全客栈",
                    "icon_url": "https://www.dfyxsec.com/favicon.ico"
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"  # ISO 8601格式
            }
            
            data = {
                "embeds": [embed]
            }
        else:
            # 日报只存储不推送，直接返回
            return
        
        print(f"正在发送Discard Embed推送：{title}")
        print(f"目标地址：{webhook}")
        
        # 获取代理配置
        proxies = get_proxies()
        if proxies:
            print(f"使用代理：{proxies}")
        
        # 设置重试参数，符合Discord API官方最佳实践
        max_retries = 5  # 增加重试次数，提高成功率
        base_delay = 1.0  # 基础延迟时间（秒）
        max_delay = 60.0  # 最大延迟时间，防止无限等待
        
        for attempt in range(max_retries):
            try:
                # 使用较短的超时时间，避免长时间阻塞
                response = requests.post(webhook, json=data, headers=headers, timeout=10, proxies=proxies)
                
                print(f"Discard推送响应状态码：{response.status_code}")
                
                # 检查响应状态
                if response.status_code in [200, 204]:
                    print(f"Discard推送成功: {title}")
                    break
                elif response.status_code == 429:
                    # 处理速率限制，严格遵循Discord API返回的Retry-After头
                    # Retry-After头可能返回秒或毫秒，需要根据实际情况处理
                    retry_after_header = response.headers.get('Retry-After')
                    
                    if retry_after_header:
                        try:
                            retry_after = float(retry_after_header)
                            # 检查Retry-After是否为毫秒（如果值很大，可能是毫秒）
                            if retry_after > 1000:  # 如果大于1000，可能是毫秒
                                retry_after = retry_after / 1000  # 转换为秒
                        except ValueError:
                            retry_after = base_delay * (2 ** attempt) + random.uniform(0, 1)  # 添加随机抖动
                    else:
                        # 使用指数退避 + 随机抖动，避免请求风暴
                        retry_after = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    
                    # 确保重试延迟不超过最大值
                    retry_after = min(retry_after, max_delay)
                    
                    print(f"Discard推送速率限制，将在{retry_after:.2f}秒后重试 (尝试 {attempt+1}/{max_retries})")
                    print(f"响应内容: {response.text}")
                    
                    # 等待后继续重试
                    time.sleep(retry_after)
                    continue
                else:
                    print(f"Discard推送失败: HTTP状态码 - {response.status_code}")
                    print(f"响应内容: {response.text}")
                    
                    # 提供解决方案建议
                    if response.status_code == 401:
                        print("建议：请检查webhook地址是否正确，可能包含无效的token")
                    elif response.status_code == 404:
                        print("建议：webhook地址不存在，请检查webhook地址是否正确")
                    elif response.status_code >= 500:
                        print("建议：Discord服务器错误，请稍后再试")
                    break
            except requests.exceptions.Timeout:
                # 超时异常，使用指数退避 + 随机抖动
                retry_after = base_delay * (2 ** attempt) + random.uniform(0, 1)
                retry_after = min(retry_after, max_delay)
                print(f"Discard推送超时，将在{retry_after:.2f}秒后重试 (尝试 {attempt+1}/{max_retries})")
                time.sleep(retry_after)
            except requests.exceptions.ConnectionError:
                # 连接错误，使用指数退避 + 随机抖动
                retry_after = base_delay * (2 ** attempt) + random.uniform(0, 1)
                retry_after = min(retry_after, max_delay)
                print(f"Discard推送连接错误，将在{retry_after:.2f}秒后重试 (尝试 {attempt+1}/{max_retries})")
                time.sleep(retry_after)
            except requests.exceptions.RequestException as e:
                print(f"Discard推送请求异常：{str(e)}")
                break
        else:
            # 所有重试都失败
            print(f"Discard推送失败：已达到最大重试次数 ({max_retries})")
    except Exception as e:
        print(f"Discard推送失败: 未知错误 - {str(e)}")

# 生成RSS feed
def generate_rss_feed(cursor, feed_type="daily"):
    """
    生成RSS feed
    
    Args:
        cursor: 数据库游标
        feed_type: RSS类型，可选值：daily（日报）、weekly（周报）
        
    Returns:
        str: RSS文件路径
    """
    print(f"开始生成{feed_type} RSS feed...")
    
    # 创建RSS目录
    rss_dir = f'rss'
    os.makedirs(rss_dir, exist_ok=True)
    
    # 获取当前日期和时间
    current_date = time.strftime('%Y-%m-%d', time.localtime())
    current_time_utc = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    # 获取数据范围
    if feed_type == "daily":
        # 日报RSS，获取当天数据
        cursor.execute("SELECT title, link, timestamp FROM items WHERE date(timestamp) = date('now') ORDER BY timestamp DESC")
        data_leaks = cursor.fetchall()
        feed_title = f"数据泄露监控日报 RSS {current_date}"
        feed_description = f"每日数据泄露监控RSS feed，包含{current_date}的最新数据泄露信息"
        feed_link = f"https://adminlove520.github.io/DarkWeb-Forums-Tracker/rss/daily_rss_{current_date}.xml"
        rss_file = f'{rss_dir}/daily_rss_{current_date}.xml'
        latest_rss_file = f'{rss_dir}/latest_daily_rss.xml'
    elif feed_type == "weekly":
        # 周报RSS，获取本周数据（周一到周日）
        # 用Python正确计算本周开始和结束日期
        today = datetime.now()
        # 本周一 (weekday() 返回0=Monday)
        monday = today - timedelta(days=today.weekday())
        # 本周日
        sunday = monday + timedelta(days=6)
        start_date = monday.strftime('%Y-%m-%d')
        end_date = sunday.strftime('%Y-%m-%d')

        cursor.execute("SELECT title, link, timestamp FROM items WHERE date(timestamp) >= ? AND date(timestamp) <= ? ORDER BY timestamp DESC", (start_date, end_date))
        data_leaks = cursor.fetchall()
        feed_title = f"数据泄露监控周报 RSS {start_date} - {end_date}"
        feed_description = f"每周数据泄露监控RSS feed，包含{start_date}到{end_date}的最新数据泄露信息"
        feed_link = f"https://adminlove520.github.io/DarkWeb-Forums-Tracker/rss/weekly_rss_{start_date}_{end_date}.xml"
        rss_file = f'{rss_dir}/weekly_rss_{start_date}_{end_date}.xml'
        latest_rss_file = f'{rss_dir}/latest_weekly_rss.xml'
    else:
        print(f"不支持的RSS类型：{feed_type}")
        return None
    
    # 生成RSS XML内容
    rss_content = f"""<?xml version='1.0' encoding='UTF-8'?>
<rss version='2.0'
    xmlns:atom='http://www.w3.org/2005/Atom'>
    <channel>
        <title>{feed_title}</title>
        <description>{feed_description}</description>
        <link>https://adminlove520.github.io/DarkWeb-Forums-Tracker/</link>
        <atom:link href='{feed_link}' rel='self' type='application/rss+xml' />
        <language>zh-CN</language>
        <lastBuildDate>{current_time_utc}</lastBuildDate>
        <ttl>60</ttl>
        
"""
    
    # 添加RSS条目
    for leak in data_leaks:
        title, link, timestamp = leak
        # 转换时间格式为RSS要求的格式（RFC 822）
        rss_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%a, %d %b %Y %H:%M:%S GMT')

        rss_content += f"""        <item>
            <title>{escape(title)}</title>
            <link>{escape(link)}</link>
            <description>{escape(title)}</description>
            <pubDate>{rss_time}</pubDate>
            <guid isPermaLink='false'>{escape(link)}_{timestamp}</guid>
        </item>
"""
    
    # 结束RSS XML
    rss_content += f"""    </channel>
</rss>"""
    
    # 写入RSS文件
    with open(rss_file, 'w', encoding='utf-8') as f:
        f.write(rss_content)
    
    # 写入最新RSS文件（用于外部订阅）
    with open(latest_rss_file, 'w', encoding='utf-8') as f:
        f.write(rss_content)
    
    print(f"{feed_type} RSS feed已生成：{rss_file}")
    print(f"最新{feed_type} RSS feed已更新：{latest_rss_file}")
    
    return rss_file

# 获取数据统计信息
def get_data_statistics(cursor, report_type="daily"):
    """
    获取数据统计信息
    
    Args:
        cursor: 数据库游标
        report_type: 报告类型，可选值：daily（每日）、weekly（每周）
        
    Returns:
        dict: 统计信息字典
    """
    statistics = {}
    
    if report_type == "daily":
        # 每日统计
        # 获取当天总数量
        cursor.execute("SELECT COUNT(*) FROM items WHERE date(timestamp) = date('now')")
        statistics['total_count'] = cursor.fetchone()[0]
        
        # 按数据源统计数量（使用site_name字段）
        cursor.execute("SELECT site_name, COUNT(*) as count FROM items WHERE date(timestamp) = date('now') GROUP BY site_name ORDER BY count DESC")
        statistics['by_source'] = cursor.fetchall()
        
        # 按小时统计数量
        cursor.execute("SELECT strftime('%H', timestamp) as hour, COUNT(*) as count FROM items WHERE date(timestamp) = date('now') GROUP BY hour ORDER BY hour")
        statistics['by_hour'] = cursor.fetchall()
    elif report_type == "weekly":
        # 每周统计（周一到周日）
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        start_date = monday.strftime('%Y-%m-%d')
        end_date = sunday.strftime('%Y-%m-%d')

        # 获取本周总数量
        cursor.execute("SELECT COUNT(*) FROM items WHERE date(timestamp) >= ? AND date(timestamp) <= ?", (start_date, end_date))
        statistics['total_count'] = cursor.fetchone()[0]

        # 按数据源统计数量
        cursor.execute("SELECT site_name, COUNT(*) as count FROM items WHERE date(timestamp) >= ? AND date(timestamp) <= ? GROUP BY site_name ORDER BY count DESC", (start_date, end_date))
        statistics['by_source'] = cursor.fetchall()

        # 按日期统计数量
        cursor.execute("SELECT date(timestamp) as date, COUNT(*) as count FROM items WHERE date(timestamp) >= ? AND date(timestamp) <= ? GROUP BY date ORDER BY date", (start_date, end_date))
        statistics['by_date'] = cursor.fetchall()
    
    return statistics

# 生成日报

def generate_daily_report(cursor):
    print("开始生成日报...")
    
    # 获取当前日期和时间
    current_date = time.strftime('%Y-%m-%d', time.localtime())
    current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    
    # 创建目录结构
    archive_dir = f'archive/{current_date}'
    os.makedirs(archive_dir, exist_ok=True)
    
    # 从数据库中获取当天的所有数据泄露信息，包含来源站点
    cursor.execute("SELECT title, link, timestamp, site_name FROM items WHERE date(timestamp) = date('now') ORDER BY timestamp DESC")
    data_leaks = cursor.fetchall()
    
    # 获取统计信息
    statistics = get_data_statistics(cursor, report_type="daily")
    
    # 生成markdown内容
    markdown_content = f"# 数据泄露监控日报 {current_date}\n\n"
    markdown_content += f"共收集到 {statistics['total_count']} 条数据泄露相关信息\n"
    markdown_content += f"最后更新时间：{current_time}\n\n"
    
    # 添加统计信息
    markdown_content += "## 今日统计\n\n"
    
    # 按数据源统计
    markdown_content += "### 按数据源统计\n"
    for source, count in statistics['by_source']:
        markdown_content += f"- {source}: {count} 条\n"
    markdown_content += "\n"
    
    # 按小时统计
    markdown_content += "### 按小时统计\n"
    for hour, count in statistics['by_hour']:
        markdown_content += f"- {hour}:00: {count} 条\n"
    markdown_content += "\n"
    
    # 准备数据泄露信息，用于HTML模板
    leak_list = []
    for leak in data_leaks:
        title, link, timestamp, site_name = leak
        markdown_content += f"## [{title}]({link})\n"
        markdown_content += f"发布时间：{timestamp}\n"
        markdown_content += f"来源站点：{site_name}\n\n"
        
        # 暂时不进行实时可用性检查，避免生成报告时卡住
        # is_available = check_site_availability(site_name)
        # 默认为True，后续可以考虑异步或定时检查
        is_available = True
        
        # 添加到数据泄露信息列表
        leak_list.append({
            'title': title,
            'link': link,
            'timestamp': timestamp,
            'site_name': site_name,
            'is_available': is_available
        })
    
    # 添加Power By信息（纯markdown格式，避免HTML标签在Discord中显示为文本）
    markdown_content += f"---\n"
    markdown_content += f"Power By 东方隐侠安全团队·Anonymous@ [隐侠安全客栈](https://www.dfyxsec.com/)\n"
    markdown_content += f"---\n"
    
    # 写入markdown文件
    markdown_file = f'{archive_dir}/Daily_{current_date}.md'
    is_update = os.path.exists(markdown_file)
    with open(markdown_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    if is_update:
        print(f"Markdown日报已更新：{markdown_file}")
    else:
        print(f"Markdown日报已生成：{markdown_file}")
    
    # 生成HTML内容
    try:
        # 读取HTML模板
        with open('template.html', 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # 渲染HTML模板
        template = Template(template_content)
        html_content = template.render(
            date=current_date,
            count=statistics['total_count'],
            update_time=current_time,
            articles=leak_list,
            statistics=statistics
        )
        
        # 写入HTML文件
        html_file = f'{archive_dir}/Daily_{current_date}.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        if is_update:
            print(f"HTML日报已更新：{html_file}")
        else:
            print(f"HTML日报已生成：{html_file}")
        
        # 更新index.html
        update_index_html(current_date, leak_list, len(data_leaks))
        
        # Discard推送日报
        config = load_config()
        push_config = config.get('push', {})
        if 'discard' in push_config and push_config['discard'].get('switch', '') == "ON" and push_config['discard'].get('send_daily_report', '') == "ON":
            send_discard_msg(
                push_config['discard'].get('webhook'),
                f"数据泄露监控日报 {current_date}",
                f"共收集到 {len(data_leaks)} 条数据泄露相关信息",
                is_daily_report=True,
                html_file=html_file,
                markdown_content=markdown_content
            )
        
    except Exception as e:
        print(f"生成HTML日报失败：{str(e)}")
    
    return markdown_file, markdown_content

# 生成周报
# 生成周报
def generate_weekly_report(cursor):
    """
    生成周报
    
    Args:
        cursor: 数据库游标
        
    Returns:
        tuple: (markdown_file, markdown_content) 周报文件路径和内容
    """
    print("开始生成周报...")

    # 获取当前日期和时间
    current_date = time.strftime("%Y-%m-%d", time.localtime())
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    # 正确计算本周的开始和结束日期（周一到周日）
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    start_date = monday.strftime('%Y-%m-%d')
    end_date = sunday.strftime('%Y-%m-%d')
    
    # 创建目录结构
    archive_dir = f'archive/Weekly_{start_date}'
    os.makedirs(archive_dir, exist_ok=True)
    
    # 从数据库中获取本周的所有数据泄露信息，包含来源站点
    cursor.execute("SELECT title, link, timestamp, site_name FROM items WHERE timestamp >= ? AND timestamp <= ? ORDER BY timestamp DESC", (start_date, end_date))
    data_leaks = cursor.fetchall()
    
    # 获取统计信息
    statistics = get_data_statistics(cursor, report_type="weekly")
    
    # 生成markdown内容
    markdown_content = f'# 数据泄露监控周报 {start_date} - {end_date}'

    markdown_content += f'共收集到 {statistics["total_count"]} 条数据泄露相关信息'
    markdown_content += f'最后更新时间：{current_time}'

    
    # 添加统计信息
    markdown_content += "## 本周统计\n\n"
    
    # 按日期统计
    markdown_content += "### 按日期统计\n"
    for date, count in statistics["by_date"]:
        markdown_content += f'- {date}: {count} 条\n'
    markdown_content += "\n"
    
    # 按数据源统计
    markdown_content += "### 按数据源统计\n"
    for source, count in statistics["by_source"]:
        markdown_content += f'- {source}: {count} 条\n'
    markdown_content += "\n"
    
    # 准备数据泄露信息，用于HTML模板
    leak_list = []
    for leak in data_leaks:
        title, link, timestamp, site_name = leak
        markdown_content += f'## [{title}]({link})'
        markdown_content += f'发布时间：{timestamp}'
        markdown_content += f'来源站点：{site_name}'

        
        # 暂时不进行实时可用性检查，避免生成报告时卡住
        # is_available = check_site_availability(site_name)
        # 默认为True，后续可以考虑异步或定时检查
        is_available = True
        
        # 添加到数据泄露信息列表
        leak_list.append({
            'title': title,
            'link': link,
            'timestamp': timestamp,
            'site_name': site_name,
            'is_available': is_available
        })
    
    # 添加Power By信息
    markdown_content += f'---'
    markdown_content += f'Power By 东方隐侠安全团队·Anonymous@ [隐侠安全客栈](https://www.dfyxsec.com/)'
    markdown_content += f'---'
    
    # 写入markdown文件
    markdown_file = f'archive/Weekly_{start_date}_{end_date}.md'
    is_update = os.path.exists(markdown_file)
    with open(markdown_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    if is_update:
        print(f'Markdown周报已更新：{markdown_file}')
    else:
        print(f'Markdown周报已生成：{markdown_file}')
    
    # 生成HTML内容
    try:
        # 读取HTML模板
        with open('template.html', 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # 渲染HTML模板
        template = Template(template_content)
        html_content = template.render(
            date=f'{start_date} - {end_date}',
            count=statistics["total_count"],
            update_time=current_time,
            articles=leak_list,
            statistics=statistics
        )
        
        # 写入HTML文件
        html_file = f'archive/Weekly_{start_date}_{end_date}.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        if is_update:
            print(f'HTML周报已更新：{html_file}')
        else:
            print(f'HTML周报已生成：{html_file}')
        
        # 更新index.html
        update_index_html(current_date, leak_list, statistics["total_count"])
        
        # Discard推送周报
        config = load_config()
        push_config = config.get('push', {})
        if 'discard' in push_config and push_config['discard'].get('switch', '') == "ON" and push_config['discard'].get('send_weekly_report', '') == "ON":
            send_discard_msg(
                push_config['discard'].get('webhook'),
                f'数据泄露监控周报 {start_date} - {end_date}',
                f'共收集到 {statistics["total_count"]} 条数据泄露相关信息',
                is_weekly_report=True,
                html_file=html_file,
                markdown_content=markdown_content
            )
        
    except Exception as e:
        print(f'生成HTML周报失败：{str(e)}')
    
    return markdown_file, markdown_content

def update_index_html(current_date, article_list, count):
    print("更新index.html...")
    
    # 创建index.html模板
    index_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DarkWeb-Forums-Tracker</title>
    <style>
        /* 全局样式 */
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        :root {
            /* 终端风格配色 */
            --bg-primary: #0a0e17;
            --bg-secondary: #121721;
            --bg-tertiary: #1a1f2e;
            --bg-gradient: linear-gradient(135deg, #00ff41, #00e0ff);
            --primary-color: #00ff41;
            --primary-dark: #00d437;
            --secondary-color: #00e0ff;
            --accent-color: #ff007f;
            --success-color: #00ff41;
            --warning-color: #ffff00;
            --danger-color: #ff007f;
            --text-primary: #ffffff;
            --text-secondary: #b0b8c1;
            --text-muted: #6b7280;
            --border-color: #2d3748;
            --border-light: #222936;
            --shadow-sm: 0 1px 2px 0 rgba(0, 255, 65, 0.1);
            --shadow-md: 0 4px 6px -1px rgba(0, 255, 65, 0.15), 0 2px 4px -1px rgba(0, 255, 65, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 255, 65, 0.2), 0 4px 6px -2px rgba(0, 255, 65, 0.1);
            --shadow-xl: 0 20px 25px -5px rgba(0, 255, 65, 0.25), 0 10px 10px -5px rgba(0, 255, 65, 0.15);
            --shadow-2xl: 0 25px 50px -12px rgba(0, 255, 65, 0.3);
            --radius-sm: 4px;
            --radius-md: 6px;
            --radius-lg: 8px;
            --radius-xl: 10px;
            --radius-2xl: 12px;
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        body {
            font-family: 'Courier New', Courier, 'Consolas', 'Monaco', 'Ubuntu Mono', monospace;
            line-height: 1.7;
            color: var(--text-primary);
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: var(--bg-secondary);
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(0, 255, 65, 0.05) 0%, rgba(0, 255, 65, 0.05) 90%),
                radial-gradient(circle at 90% 80%, rgba(0, 224, 255, 0.05) 0%, rgba(0, 224, 255, 0.05) 90%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        main {
            flex: 1;
        }
        
        /* 标题样式 */
        h1 {
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--text-primary);
            margin: 0;
            line-height: 1.2;
        }
        
        /* 头部标题样式 */
        header h1 {
            color: white;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            background: none;
            -webkit-background-clip: none;
            -webkit-text-fill-color: white;
        }
        
        h2 {
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 24px;
        }
        
        /* 头部样式 */
        header {
            background: var(--bg-primary);
            color: var(--primary-color);
            padding: 24px 32px;
            border: 1px solid var(--primary-color);
            box-shadow: 0 0 15px rgba(0, 255, 65, 0.2);
            text-align: center;
            margin-bottom: 32px;
            position: relative;
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(to right, transparent, var(--primary-color), transparent);
            animation: scanline 2s linear infinite;
        }
        
        @keyframes scanline {
            0% {
                transform: translateX(-100%);
            }
            100% {
                transform: translateX(100%);
            }
        }
        
        header > * {
            position: relative;
            z-index: 1;
        }
        
        header h1 {
            color: var(--primary-color);
            text-shadow: 0 0 10px rgba(0, 255, 65, 0.5);
            margin: 0;
            font-size: 2.25rem;
        }
        
        header p {
            margin-top: 16px;
            font-size: 1.1rem;
            color: var(--secondary-color);
            font-weight: 500;
            line-height: 1.5;
        }
        
        /* 终端风格标题装饰 */
        .terminal-header {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
        }
        
        .terminal-header::before,
        .terminal-header::after {
            content: '▬';
            color: var(--primary-color);
            font-size: 1.5rem;
            flex: 1;
            text-align: center;
            letter-spacing: -2px;
        }
        
        /* 报告列表样式 */
        .report-list {
            list-style: none;
            padding: 0;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            box-shadow: 0 0 15px rgba(0, 255, 65, 0.1);
        }
        
        .report-item {
            background-color: var(--bg-primary);
            padding: 12px 20px;
            border-bottom: 1px solid var(--border-light);
            transition: var(--transition);
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: relative;
            overflow: hidden;
            font-family: 'Courier New', monospace;
        }
        
        .report-item:last-child {
            border-bottom: none;
        }
        
        .report-item:hover {
            background-color: var(--bg-secondary);
            border-color: var(--primary-color);
            transform: translateX(4px);
        }
        
        .report-link {
            color: var(--secondary-color);
            text-decoration: none;
            font-size: 1.25rem;
            font-weight: 700;
            transition: var(--transition);
            flex: 1;
            position: relative;
            font-family: 'Courier New', monospace;
        }
        
        .report-link::before {
            content: '📄';
            margin-right: 8px;
            color: var(--primary-color);
        }
        
        .report-link:hover {
            color: var(--primary-color);
            text-decoration: none;
            text-shadow: 0 0 8px rgba(0, 255, 65, 0.4);
        }
        
        .report-info {
            color: var(--text-secondary);
            font-size: 0.875rem;
            margin-top: 4px;
            font-family: 'Courier New', monospace;
        }
        
        .report-count {
            background: var(--bg-primary);
            color: var(--primary-color);
            padding: 8px 16px;
            border: 1px solid var(--primary-color);
            font-size: 0.875rem;
            font-weight: 600;
            margin-left: 20px;
            min-width: 80px;
            text-align: center;
            box-shadow: 0 0 10px rgba(0, 255, 65, 0.1);
            transition: var(--transition);
            font-family: 'Courier New', monospace;
            text-shadow: 0 0 5px rgba(0, 255, 65, 0.5);
        }
        
        .report-item:hover .report-count {
            background: var(--primary-color);
            color: var(--bg-primary);
            box-shadow: 0 0 15px rgba(0, 255, 65, 0.3);
            transform: scale(1.05);
        }
        
        /* 空状态样式 */
        .empty-state {
            text-align: center;
            padding: 80px 20px;
            color: var(--text-muted);
            background-color: var(--bg-primary);
            border: 1px dashed var(--border-color);
            margin-top: 24px;
            font-family: 'Courier New', monospace;
        }
        
        .empty-state h3 {
            font-size: 1.5rem;
            margin-bottom: 12px;
            color: var(--secondary-color);
            font-weight: 600;
        }
        
        .empty-state p {
            font-size: 1rem;
            line-height: 1.6;
        }
        
        /* 页脚样式 */
        footer {
            text-align: center;
            margin-top: 64px;
            padding: 24px;
            color: var(--text-primary);
            font-size: 0.9rem;
            font-family: 'Courier New', monospace;
        }
        
        footer p {
            margin: 0;
            line-height: 1.6;
        }
        
        footer a {
            color: var(--primary-color);
            text-decoration: none;
            transition: color 0.3s ease, text-decoration 0.3s ease;
            font-weight: 500;
        }
        
        footer a:hover {
            color: var(--primary-dark);
            text-decoration: underline;
        }
        
        /* 响应式设计 */
        @media (max-width: 768px) {
            body {
                padding: 16px;
            }
            
            h1 {
                font-size: 2rem;
            }
            
            h2 {
                font-size: 1.5rem;
            }
            
            header {
                padding: 32px 24px;
                margin-bottom: 24px;
            }
            
            header p {
                font-size: 1.1rem;
            }
            
            .report-item {
                padding: 20px;
                margin-bottom: 16px;
                flex-direction: column;
                align-items: flex-start;
                gap: 12px;
            }
            
            .report-link {
                font-size: 1.15rem;
            }
            
            .report-count {
                margin-left: 0;
                padding: 8px 14px;
                min-width: 70px;
                align-self: flex-end;
            }
            
            .report-info {
                font-size: 0.9rem;
            }
            
            .empty-state {
                padding: 64px 20px;
            }
            
            footer {
                margin: 48px -16px 0 -16px;
                padding: 24px 16px;
            }
        }
        
        @media (max-width: 480px) {
            body {
                padding: 12px;
            }
            
            h1 {
                font-size: 1.75rem;
            }
            
            h2 {
                font-size: 1.35rem;
            }
            
            header {
                padding: 28px 20px;
                margin-bottom: 20px;
            }
            
            header p {
                font-size: 1rem;
            }
            
            .report-item {
                padding: 18px;
                margin-bottom: 14px;
                flex-direction: column;
                align-items: flex-start;
                gap: 12px;
            }
            
            .report-link {
                font-size: 1.1rem;
            }
            
            .report-count {
                margin-left: 0;
                padding: 8px 16px;
                min-width: 80px;
                align-self: flex-end;
            }
            
            .report-info {
                font-size: 0.85rem;
            }
            
            .empty-state {
                padding: 48px 16px;
            }
            
            .empty-state h3 {
                font-size: 1.25rem;
            }
            
            footer {
                margin: 40px -12px 0 -12px;
                padding: 20px 12px;
            }
        }
        
        /* 滚动条样式 */
        ::-webkit-scrollbar {
            width: 12px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--bg-tertiary);
            border-radius: 6px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(to bottom, var(--primary-color), var(--secondary-color));
            border-radius: 6px;
            border: 3px solid var(--bg-tertiary);
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.2);
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(to bottom, var(--primary-dark), var(--secondary-color));
        }
        
        /* Firefox滚动条样式 */
        * {
            scrollbar-width: thin;
            scrollbar-color: var(--primary-color) var(--bg-tertiary);
        }
        
        /* 加载动画效果 */
        .report-item {
            animation: fadeInUp 0.5s ease forwards;
            opacity: 0;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .report-item:nth-child(1) { animation-delay: 0.1s; }
        .report-item:nth-child(2) { animation-delay: 0.2s; }
        .report-item:nth-child(3) { animation-delay: 0.3s; }
        .report-item:nth-child(4) { animation-delay: 0.4s; }
        .report-item:nth-child(5) { animation-delay: 0.5s; }
        .report-item:nth-child(6) { animation-delay: 0.6s; }
        .report-item:nth-child(7) { animation-delay: 0.7s; }
        .report-item:nth-child(8) { animation-delay: 0.8s; }
        .report-item:nth-child(9) { animation-delay: 0.9s; }
        .report-item:nth-child(10) { animation-delay: 1s; }
    </style>
</head>
<body>
    <header style="border: 1px solid var(--primary-color); box-shadow: 0 0 20px rgba(0, 255, 65, 0.3); padding: 32px 24px; text-align: center; margin-bottom: 32px; border-radius: 16px; background: var(--bg-primary);">
        <h1 style="color: var(--primary-color); text-shadow: 0 0 20px rgba(0, 255, 65, 0.8); font-size: 2.5rem; margin-bottom: 16px; font-family: 'Courier New', monospace;">DARKWEB论坛数据泄露监控系统</h1>
        <p style="color: var(--secondary-color); font-weight: bold; text-shadow: 0 0 10px rgba(0, 224, 255, 0.5); font-size: 1.25rem; font-family: 'Courier New', monospace;">🌐 DARKWEB FORUMS TRACKER 监控报告</p>
    </header>
    
    <main>
        <div style="text-align: center; margin-bottom: 32px;">
            <h2 style="color: var(--warning-color); text-shadow: 0 0 15px rgba(255, 255, 0, 0.6); font-size: 2rem; text-align: center; margin-bottom: 0; padding: 16px 32px; border: 1px solid var(--warning-color); border-radius: 12px; background: var(--bg-primary); font-family: 'Courier New', monospace; box-shadow: 0 0 15px rgba(255, 255, 0, 0.2); display: inline-block;">威 胁 情 报</h2>
        </div>
        <ul class="report-list" style="list-style: none; padding: 0; margin: 0;">
            {% for report in reports %}
            <li class="report-item" style="background: var(--bg-primary); border: 1px solid var(--primary-color); box-shadow: 0 0 15px rgba(0, 255, 65, 0.2); padding: 20px; margin-bottom: 20px; border-radius: 12px; transition: all 0.3s ease; display: flex; justify-content: space-between; align-items: center; text-align: center;">
                <a href="{{ report.path }}" class="report-link" target="_blank" style="color: var(--secondary-color); text-decoration: none; font-size: 1.25rem; font-weight: bold; text-shadow: 0 0 8px rgba(0, 224, 255, 0.4); transition: all 0.3s ease; font-family: 'Courier New', monospace;">{{ report.date }}</a>
                <div class="report-count" style="background: var(--bg-primary); color: var(--primary-color); padding: 10px 20px; border: 1px solid var(--primary-color); border-radius: 8px; font-size: 0.9rem; font-weight: bold; box-shadow: 0 0 10px rgba(0, 255, 65, 0.2); transition: all 0.3s ease; font-family: 'Courier New', monospace; text-shadow: 0 0 5px rgba(0, 255, 65, 0.5);">
                    {{ report.count }} 条
                </div>
            </li>
            {% endfor %}
        </ul>
        
        {% if not reports %}
        <div class="empty-state" style="text-align: center; padding: 60px 20px; background: var(--bg-primary); border: 1px solid var(--primary-color); border-radius: 12px; box-shadow: 0 0 15px rgba(0, 255, 65, 0.2); margin-top: 20px;">
            <h3 style="color: var(--warning-color); font-size: 1.5rem; margin-bottom: 16px; font-family: 'Courier New', monospace;">暂无报告</h3>
            <p style="color: var(--text-secondary); font-size: 1rem; font-family: 'Courier New', monospace;">报告将根据监控数据自动生成</p>
        </div>
        {% endif %}

        <!-- RSS订阅区块 -->
        <div style="margin-top: 48px;">
            <div style="text-align: center; margin-bottom: 24px;">
                <h2 style="color: var(--accent-color); text-shadow: 0 0 15px rgba(255, 0, 127, 0.6); font-size: 1.75rem; text-align: center; margin-bottom: 0; padding: 16px 32px; border: 1px solid var(--accent-color); border-radius: 12px; background: var(--bg-primary); font-family: 'Courier New', monospace; box-shadow: 0 0 15px rgba(255, 0, 127, 0.2); display: inline-block;">📡 RSS 订阅</h2>
            </div>
            <div style="display: flex; gap: 20px; flex-wrap: wrap; justify-content: center;">
                <a href="/DarkWeb-Forums-Tracker/rss/latest_daily_rss.xml" style="flex: 1; min-width: 280px; max-width: 400px; text-decoration: none;">
                    <div style="background: var(--bg-primary); border: 1px solid var(--accent-color); border-radius: 12px; padding: 20px; text-align: center; transition: all 0.3s ease; box-shadow: 0 0 15px rgba(255, 0, 127, 0.2);">
                        <div style="font-size: 2rem; margin-bottom: 12px;">📅</div>
                        <div style="color: var(--secondary-color); font-size: 1.1rem; font-weight: bold; font-family: 'Courier New', monospace; margin-bottom: 8px;">日报 RSS</div>
                        <div style="color: var(--text-secondary); font-size: 0.9rem; font-family: 'Courier New', monospace;">每日数据泄露监控日报订阅</div>
                        <div style="color: var(--accent-color); font-size: 0.8rem; font-family: 'Courier New', monospace; margin-top: 8px;">点击订阅 · /DarkWeb-Forums-Tracker/rss/latest_daily_rss.xml</div>
                    </div>
                </a>
                <a href="/DarkWeb-Forums-Tracker/rss/latest_weekly_rss.xml" style="flex: 1; min-width: 280px; max-width: 400px; text-decoration: none;">
                    <div style="background: var(--bg-primary); border: 1px solid var(--accent-color); border-radius: 12px; padding: 20px; text-align: center; transition: all 0.3s ease; box-shadow: 0 0 15px rgba(255, 0, 127, 0.2);">
                        <div style="font-size: 2rem; margin-bottom: 12px;">📆</div>
                        <div style="color: var(--secondary-color); font-size: 1.1rem; font-weight: bold; font-family: 'Courier New', monospace; margin-bottom: 8px;">周报 RSS</div>
                        <div style="color: var(--text-secondary); font-size: 0.9rem; font-family: 'Courier New', monospace;">每周数据泄露监控周报订阅</div>
                        <div style="color: var(--accent-color); font-size: 0.8rem; font-family: 'Courier New', monospace; margin-top: 8px;">点击订阅 · /DarkWeb-Forums-Tracker/rss/latest_weekly_rss.xml</div>
                    </div>
                </a>
            </div>
        </div>
    </main>
    
    <footer style="text-align: center; margin-top: 64px; padding: 24px; color: var(--text-primary); font-size: 0.9rem; font-family: 'Courier New', monospace;">
        <p>Power By 东方隐侠安全团队 Anonymous@ <a href="https://www.dfyxsec.com/" target="_blank" style="color: var(--primary-color); text-decoration: none; transition: all 0.3s ease; text-shadow: 0 0 5px rgba(0, 255, 65, 0.5);">隐侠安全客栈</a></p>
    </footer>
</body>
</html>
    """
    
    # 获取所有已生成的日报
    reports = []
    
    # 遍历archive目录下的所有日期目录
    if os.path.exists('archive'):
        for date_dir in sorted(os.listdir('archive'), reverse=True):
            if os.path.isdir(os.path.join('archive', date_dir)):
                # 检查该日期目录下是否存在HTML文件
                html_file = f'archive/{date_dir}/Daily_{date_dir}.html'
                if os.path.exists(html_file):
                    # 尝试获取数据泄露信息数量
                    count = 0
                    md_file = f'archive/{date_dir}/Daily_{date_dir}.md'
                    if os.path.exists(md_file):
                        with open(md_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # 从markdown文件中提取数据泄露信息数量
                            import re
                            match = re.search(r'共收集到 (\d+) 条数据泄露相关信息', content)
                            if match:
                                count = match.group(1)
                    
                    reports.append({
                        'date': date_dir,
                        'path': html_file,
                        'count': count
                    })
    
    # 渲染index.html
    template = Template(index_template)
    html_content = template.render(reports=reports)
    
    # 写入index.html文件
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("index.html已更新")

# Telegram Bot推送
def tgbot(text, msg, token, group_id):
    import telegram
    try:
        if not token or token == "Telegram Bot的token":
            print(f"Telegram推送跳过：token未配置")
            return
            
        if not group_id or group_id == "Telegram Bot的group_id":
            print(f"Telegram推送跳过：group_id未配置")
            return
            
        # 获取代理配置
        proxies = get_proxies()
        
        if proxies:
            # 配置telegram bot使用代理
            request_kwargs = {'proxies': proxies}
            bot = telegram.Bot(token=token, request_kwargs=request_kwargs)
        else:
            bot = telegram.Bot(token=token)
            
        bot.send_message(chat_id=group_id, text=f'{text}\n{msg}')
        print(f"Telegram推送成功: {text}")
    except Exception as e:
        print(f"Telegram推送失败: {str(e)}")

# 主函数

def main():
    banner = '''
    +-------------------------------------------+
                DarkWeb Forums Tracker
    使用说明：
    1. 修改config.yaml中的推送配置以及开关
    2. 修改rss_dataleak.yaml中需要增加删除的数据泄露源
    3. 可自行去除或增加新的推送渠道代码到本脚本中
                      2026.1.1
                Powered By：Anonymous
    +-------------------------------------------+
                     开始监控...
    '''

    print(banner)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='数据泄露监控脚本')
    parser.add_argument('--once', action='store_true', help='只执行一次，适合GitHub Action运行')
    parser.add_argument('--daily-report', action='store_true', help='生成日报模式，只生成日报不推送')
    args = parser.parse_args()
    
    conn = init_database()
    cursor = conn.cursor()
    rss_config = {}

    try:
        with open('rss_dataleak.yaml', 'r', encoding='utf-8') as file:
            rss_config = yaml.load(file, Loader=yaml.FullLoader)
    except Exception as e:
        print(f"加载rss_dataleak.yaml文件出错: {str(e)}")
        conn.close()
        return

    # 加载数据源开关配置
    config = load_config()
    datasources_config = config.get('datasources', {})
    
    # 输出已开启监控的数据源
    enabled_datasources = [source for source, enabled in datasources_config.items() if enabled == 1]
    print(f"\n已开启监控的数据源 ({len(enabled_datasources)} 个):")
    for source in enabled_datasources:
        print(f"  - {source}")
    print()

    # 发送启动通知消息 - 非日报模式才发送
    if not args.daily_report:
        # 检查是否有任何推送服务的开关是开启的
        push_config = config.get('push', {})
        any_push_enabled = False
        
        for service in push_config.values():
            if service.get('switch', 'OFF') == 'ON':
                any_push_enabled = True
                break
        
        if any_push_enabled:
            push_message("DarkWeb-Forums-Tracker已启动!", f"启动时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}", is_startup=True)

    try:
        if args.daily_report:
            # 日报模式，先收集数据，再生成日报
            print("使用日报模式")
            # 先收集所有RSS源的数据
            for website, config in rss_config.items():
                # 检查数据源是否启用
                if datasources_config.get(website, 1) == 0:
                    print(f"跳过禁用的数据源：{website}")
                    continue
                    
                website_name = config.get("website_name")
                rss_url = config.get("rss_url")
                # 日报模式下不发送推送，send_push=False
                check_for_updates(rss_url, website_name, cursor, conn, send_push=False)
            # 收集完数据后生成日报
            generate_daily_report(cursor)
            # 生成日报RSS feed
            generate_rss_feed(cursor, feed_type="daily")
        elif args.once:
            # 单次执行模式，适合GitHub Action
            print("使用单次执行模式")
            for website, rss_item in rss_config.items():
                # 检查数据源是否启用
                if datasources_config.get(website, 1) == 0:
                    print(f"跳过禁用的数据源：{website}")
                    continue
                    
                website_name = rss_item.get("website_name")
                rss_url = rss_item.get("rss_url")
                check_for_updates(rss_url, website_name, cursor, conn)
            
            # 检查是否需要生成日报
            if config.get('daily_report', {}).get('switch', 'ON') == 'ON':
                generate_daily_report(cursor)
                # 生成日报RSS feed
                generate_rss_feed(cursor, feed_type="daily")
            
            # 检查是否需要生成周报（如果是周五，基于北京时间）
            # 获取当前UTC时间，转换为北京时间（UTC+8）
            now_utc = datetime.utcnow()
            now_bj = now_utc + timedelta(hours=8)
            if now_bj.weekday() == 4:  # 4表示周五
                if config.get('weekly_report', {}).get('switch', 'ON') == 'ON':
                    generate_weekly_report(cursor)
                    # 生成周报RSS feed
                    generate_rss_feed(cursor, feed_type="weekly")
        else:
            # 循环执行模式，适合本地运行
            while True:
                try:
                    # 检查是否需要夜间休眠
                    if should_sleep():
                        sleep_hours = 7 - datetime.now().hour
                        print(f"当前时间在0-7点之间，将休眠{sleep_hours}小时")
                        time.sleep(sleep_hours * 3600)
                        continue
                    
                    for website, rss_item in rss_config.items():
                        # 检查数据源是否启用
                        if datasources_config.get(website, 1) == 0:
                            print(f"跳过禁用的数据源：{website}")
                            continue
                            
                        website_name = rss_item.get("website_name")
                        rss_url = rss_item.get("rss_url")
                        check_for_updates(rss_url, website_name, cursor, conn)

                    # 检查是否需要生成日报
                    if config.get('daily_report', {}).get('switch', 'ON') == 'ON':
                        generate_daily_report(cursor)
                        # 生成日报RSS feed
                        generate_rss_feed(cursor, feed_type="daily")
                    
                    # 检查是否需要生成周报（如果是周五，基于北京时间）
                    # 获取当前UTC时间，转换为北京时间（UTC+8）
                    now_utc = datetime.utcnow()
                    now_bj = now_utc + timedelta(hours=8)
                    if now_bj.weekday() == 4:  # 4表示周五
                        if config.get('weekly_report', {}).get('switch', 'ON') == 'ON':
                            generate_weekly_report(cursor)
                            # 生成周报RSS feed
                            generate_rss_feed(cursor, feed_type="weekly")

                    # 每二小时执行一次
                    time.sleep(10800)

                except Exception as e:
                    print("发生异常：", str(e))
                    time.sleep(60)  # 出现异常，等待1分钟继续执行
    except Exception as e:
        print("主程序发生异常：", str(e))
    finally:
        conn.close()
        print("监控程序已结束")

if __name__ == "__main__":
    main()