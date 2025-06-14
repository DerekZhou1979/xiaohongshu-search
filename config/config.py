#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
小红书搜索工具 - 全局配置文件
包含所有应用配置参数
"""

import os

# ===========================================
# 基础配置
# ===========================================

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 应用配置
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
    # 默认搜索结果数量
    'DEFAULT_MAX_RESULTS': 30,
    
    # 最大搜索结果数量
    'MAX_RESULTS_LIMIT': 100,
    
    # 缓存配置
    'USE_CACHE': True,
    'CACHE_EXPIRE_TIME': 3600,  # 缓存过期时间（秒）
    
    # 请求延迟配置
    'REQUEST_DELAY': 0.5,  # 请求间隔（秒）
    'PAGE_LOAD_TIMEOUT': 30,  # 页面加载超时（秒）
    
    # 重试配置
    'MAX_RETRIES': 3,
    'RETRY_DELAY': 2,  # 重试间隔（秒）
}

# ===========================================
# 爬虫配置
# ===========================================

CRAWLER_CONFIG = {
    # WebDriver配置
    'USE_SELENIUM': True,
    'HEADLESS': True,
    'WINDOW_SIZE': (1920, 1080),
    
    # Chrome配置
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
    
    # 页面操作配置
    'SCROLL_PAUSE_TIME': 2,  # 滚动停顿时间
    'SCROLL_COUNT': 3,  # 滚动次数
    'ELEMENT_WAIT_TIME': 10,  # 元素等待时间
}

# ===========================================
# 三种提取策略配置
# ===========================================

EXTRACTION_STRATEGIES = {
    # 策略1: CSS选择器配置
    'STRATEGY_1': {
        'NAME': 'CSS选择器方法',
        'ENABLED': True,
        'PRIORITY': 1,
        'SELECTORS': [
            # 新版小红书笔记容器
            "div.note-item",
            "div[data-noteid]",
            "div[class*='note']",
            "div[class*='card']",
            "div[class*='item']",
            
            # 搜索结果容器
            ".search-result-item",
            ".search-card",
            ".feeds-container div",
            ".search-feeds-container div",
            
            # 通用容器
            "section[class*='note']",
            "article",
            "div[data-index]",
            
            # 链接容器
            "a[href*='explore']",
            "a[href*='discovery']",
            "a[class*='note']"
        ],
        'MAX_ELEMENTS_PER_SELECTOR': 5
    },
    
    # 策略2: URL模式匹配配置
    'STRATEGY_2': {
        'NAME': 'URL模式匹配方法',
        'ENABLED': True,
        'PRIORITY': 2,
        'URL_PATTERNS': [
            '/explore/',
            '/discovery/', 
            '/note/',
            '/item/',
            '/detail/'
        ],
        'MAX_LINKS_TO_PROCESS': 10
    },
    
    # 策略3: DOM结构分析配置
    'STRATEGY_3': {
        'NAME': 'DOM结构分析方法',
        'ENABLED': True,
        'PRIORITY': 3,
        'XPATH_QUERIES': [
            "//*[contains(text(), '{keyword}')]",
            "//div[contains(text(), '{keyword}')]",
            "//span[contains(text(), '{keyword}')]",
            "//p[contains(text(), '{keyword}')]",
            "//h1[contains(text(), '{keyword}')]",
            "//h2[contains(text(), '{keyword}')]",
            "//h3[contains(text(), '{keyword}')]"
        ],
        'MAX_ELEMENTS_TO_ANALYZE': 100,
        'PARENT_LEVEL_DEPTH': 5  # 向上查找父元素的深度
    }
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
    'DRIVERS_DIR': os.path.join(PROJECT_ROOT, 'drivers'),
}

# ===========================================
# 文件路径配置
# ===========================================

FILE_PATHS = {
    'CHROMEDRIVER_PATH': os.path.join(DIRECTORIES['DRIVERS_DIR'], 'chromedriver-mac-arm64', 'chromedriver'),
    'COOKIES_FILE': os.path.join(DIRECTORIES['COOKIES_DIR'], 'xiaohongshu_cookies.json'),
    'STARTUP_LOG': os.path.join(DIRECTORIES['LOGS_DIR'], 'startup.log'),
    'CRAWLER_LOG': os.path.join(DIRECTORIES['LOGS_DIR'], 'crawler.log'),
}

# ===========================================
# 日志配置
# ===========================================

LOGGING_CONFIG = {
    'LEVEL': 'INFO',
    'FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'DATE_FORMAT': '%Y-%m-%d %H:%M:%S',
    'MAX_FILE_SIZE': 10 * 1024 * 1024,  # 10MB
    'BACKUP_COUNT': 5,
    'ENCODING': 'utf-8'
}

# ===========================================
# URL配置
# ===========================================

URLS = {
    'XIAOHONGSHU_BASE': 'https://www.xiaohongshu.com',
    'SEARCH_URL_TEMPLATE': 'https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web_search&type=comprehensive',
    'LOGIN_URL': 'https://www.xiaohongshu.com/login',
    'API_BASE': '/api'
}

# ===========================================
# 安全配置
# ===========================================

SECURITY_CONFIG = {
    'RATE_LIMIT': {
        'REQUESTS_PER_MINUTE': 30,
        'REQUESTS_PER_HOUR': 500
    },
    'USER_AGENT_ROTATION': True,
    'IP_ROTATION': False,  # 暂不支持
    'CAPTCHA_HANDLING': False  # 暂不支持
}

# ===========================================
# 模拟数据配置
# ===========================================

MOCK_DATA_CONFIG = {
    'ENABLE_MOCK': False,  # 是否启用模拟数据
    'MOCK_DELAY': 0.1,  # 模拟请求延迟
    'MOCK_SUCCESS_RATE': 0.95,  # 模拟成功率
}

# ===========================================
# 热门关键词配置
# ===========================================

HOT_KEYWORDS = [
    "海鸥手表", "上海手表", "连衣裙", "耳机", "咖啡",
    "包包", "眼影", "防晒霜", "面膜", "香水",
    "手表", "鞋子", "数码产品", "家居用品", "美食"
]

# ===========================================
# 错误处理配置
# ===========================================

ERROR_CONFIG = {
    'SAVE_ERROR_SCREENSHOTS': True,
    'SAVE_ERROR_PAGE_SOURCE': True,
    'AUTO_RECOVERY': True,
    'MAX_RECOVERY_ATTEMPTS': 3
}

# ===========================================
# 性能配置
# ===========================================

PERFORMANCE_CONFIG = {
    'ENABLE_PROFILING': False,
    'MAX_MEMORY_USAGE': 1024,  # MB
    'CLEANUP_INTERVAL': 3600,  # 秒
}

def get_config(section=None):
    """
    获取配置信息
    
    参数:
        section (str): 配置节名称，如果为None则返回所有配置
    
    返回:
        dict: 配置信息
    """
    all_config = {
        'APP': APP_CONFIG,
        'SEARCH': SEARCH_CONFIG,
        'CRAWLER': CRAWLER_CONFIG,
        'EXTRACTION_STRATEGIES': EXTRACTION_STRATEGIES,
        'DIRECTORIES': DIRECTORIES,
        'FILE_PATHS': FILE_PATHS,
        'LOGGING': LOGGING_CONFIG,
        'URLS': URLS,
        'SECURITY': SECURITY_CONFIG,
        'MOCK_DATA': MOCK_DATA_CONFIG,
        'HOT_KEYWORDS': HOT_KEYWORDS,
        'ERROR': ERROR_CONFIG,
        'PERFORMANCE': PERFORMANCE_CONFIG
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
    print(f"日志级别: {LOGGING_CONFIG['LEVEL']}") 