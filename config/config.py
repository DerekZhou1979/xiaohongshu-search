#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
小红书搜索工具 - 全局配置文件
"""

import os

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ===========================================
# 应用配置
# ===========================================

APP_CONFIG = {
    'DEBUG': False,
    'HOST': '0.0.0.0',
    'PORT': 8080,
    'SECRET_KEY': 'xiaohongshu_search_2024'
}

# ===========================================
# 搜索配置
# ===========================================

SEARCH_CONFIG = {
    'DEFAULT_MAX_RESULTS': 30,
    'MAX_RESULTS_LIMIT': 100,
    'USE_CACHE': True,
    'CACHE_EXPIRE_TIME': 3600,
    'REQUEST_DELAY': 0.5,
    'PAGE_LOAD_TIMEOUT': 30,
    'MAX_RETRIES': 3,
    'RETRY_DELAY': 2
}

# ===========================================
# 爬虫配置
# ===========================================

CRAWLER_CONFIG = {
    'USE_SELENIUM': True,
    'HEADLESS': True,
    'WINDOW_SIZE': (1920, 1080),
    'CHROME_OPTIONS': [
        '--headless',
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--disable-web-security',
        '--ignore-certificate-errors',
        '--disable-blink-features=AutomationControlled',
        '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ],
    'SCROLL_PAUSE_TIME': 2,
    'SCROLL_COUNT': 3,
    'ELEMENT_WAIT_TIME': 10
}

# ===========================================
# 目录配置
# ===========================================

DIRECTORIES = {
    'CACHE_DIR': os.path.join(PROJECT_ROOT, 'cache'),
    'TEMP_DIR': os.path.join(PROJECT_ROOT, 'cache', 'temp'),
    'LOGS_DIR': os.path.join(PROJECT_ROOT, 'cache', 'logs'),
    'COOKIES_DIR': os.path.join(PROJECT_ROOT, 'cache', 'cookies'),
    'STATIC_DIR': os.path.join(PROJECT_ROOT, 'static'),
    'DRIVERS_DIR': os.path.join(PROJECT_ROOT, 'drivers')
}

# ===========================================
# 文件路径配置
# ===========================================

FILE_PATHS = {
    'CHROMEDRIVER_PATH': os.path.join(DIRECTORIES['DRIVERS_DIR'], 'chromedriver-mac-arm64', 'chromedriver'),
    'COOKIES_FILE': os.path.join(DIRECTORIES['COOKIES_DIR'], 'xiaohongshu_cookies.json')
}

# ===========================================
# URL配置
# ===========================================

URLS = {
    'XIAOHONGSHU_BASE': 'https://www.xiaohongshu.com',
    'SEARCH_URL_TEMPLATE': 'https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web_search&type=comprehensive',
    'LOGIN_URL': 'https://www.xiaohongshu.com/login'
}

# ===========================================
# 热门关键词
# ===========================================

HOT_KEYWORDS = [
    "海鸥手表", "上海手表", "连衣裙", "耳机", "咖啡",
    "包包", "眼影", "防晒霜", "面膜", "香水",
    "手表", "鞋子", "数码产品", "家居用品", "美食"
]

def get_config(section=None):
    """获取配置信息"""
    all_config = {
        'APP': APP_CONFIG,
        'SEARCH': SEARCH_CONFIG,
        'CRAWLER': CRAWLER_CONFIG,
        'DIRECTORIES': DIRECTORIES,
        'FILE_PATHS': FILE_PATHS,
        'URLS': URLS,
        'HOT_KEYWORDS': HOT_KEYWORDS
    }
    
    if section:
        return all_config.get(section.upper(), {})
    return all_config

def create_directories():
    """创建必要的目录"""
    for dir_path in DIRECTORIES.values():
        os.makedirs(dir_path, exist_ok=True)

def validate_config():
    """验证配置的有效性"""
    errors = []
    
    # 检查必要的目录
    for name, path in DIRECTORIES.items():
        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
            except Exception as e:
                errors.append(f"无法创建目录 {name}: {path} - {str(e)}")
    
    # 检查ChromeDriver
    chromedriver_path = FILE_PATHS['CHROMEDRIVER_PATH']
    if not os.path.exists(chromedriver_path):
        errors.append(f"ChromeDriver不存在: {chromedriver_path}")
    
    return errors

if __name__ == '__main__':
    # 配置验证
    errors = validate_config()
    if errors:
        print("配置验证失败:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("配置验证成功")
    
    # 显示主要配置信息
    print(f"\n主要配置信息:")
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"服务地址: {APP_CONFIG['HOST']}:{APP_CONFIG['PORT']}")
    print(f"默认搜索结果数: {SEARCH_CONFIG['DEFAULT_MAX_RESULTS']}")
    print(f"缓存目录: {DIRECTORIES['CACHE_DIR']}") 