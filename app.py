#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
小红书搜索工具 - 主启动文件
支持智能搜索、双重访问方式和自动认证
"""

import os
import sys
import subprocess
import time

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

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

def check_dependencies():
    """检查并安装依赖"""
    print("🔍 检查Python依赖...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ 依赖检查完成")
    except subprocess.CalledProcessError:
        print("❌ 依赖安装失败，请手动运行: pip install -r requirements.txt")
        return False
    return True

def check_chrome():
    """检查Chrome浏览器"""
    chrome_paths = [
        'google-chrome',
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
    ]
    
    for path in chrome_paths:
        if os.path.exists(path) or subprocess.run(['which', path], capture_output=True).returncode == 0:
            return True
    
    print("⚠️  警告: 未找到Chrome浏览器，Selenium可能无法正常工作")
    print("   请安装Chrome浏览器: https://www.google.com/chrome/")
    return False

def cleanup_temp_files():
    """清理临时文件"""
    temp_dir = DIRECTORIES['TEMP_DIR']
    if os.path.exists(temp_dir):
        temp_files = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]
        if temp_files:
            print(f"🧹 清理 {len(temp_files)} 个临时文件...")
            for file in temp_files:
                try:
                    os.remove(os.path.join(temp_dir, file))
                except:
                    pass
            print("✅ 临时文件清理完成")

def check_port(port):
    """检查端口是否被占用"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def main():
    """主函数"""
    print("🚀 启动小红书搜索工具...")
    print("=" * 50)
    
    # 创建必要目录
    create_directories()
    
    # 检查配置
    errors = validate_config()
    if errors:
        print("❌ 配置验证失败:")
        for error in errors:
            print(f"   - {error}")
        print("\n请检查配置后重试")
        return
    
    # 检查依赖
    if not check_dependencies():
        return
    
    # 检查Chrome
    check_chrome()
    
    # 清理临时文件
    cleanup_temp_files()
    
    # 检查端口
    port = APP_CONFIG['PORT']
    if check_port(port):
        print(f"⚠️  端口 {port} 已被占用，请关闭占用该端口的程序后重试")
        return
    
    # 显示启动信息
    print(f"📍 项目根目录: {PROJECT_ROOT}")
    print(f"🌐 服务地址: http://localhost:{port}")
    print(f"📊 默认搜索结果数: {SEARCH_CONFIG['DEFAULT_MAX_RESULTS']}")
    print(f"💾 缓存目录: {DIRECTORIES['CACHE_DIR']}")
    print("=" * 50)
    
    # 启动服务器
    try:
        # 添加项目根目录到Python路径
        sys.path.insert(0, PROJECT_ROOT)
        
        # 导入并启动主服务器
        from src.server.main_server import app
        
        print("🎉 服务启动成功!")
        print(f"🔗 访问地址: http://localhost:{port}")
        print("⏹️  按 Ctrl+C 停止服务")
        print("=" * 50)
        
        # 启动Flask应用
        app.run(
            host=APP_CONFIG['HOST'],
            port=APP_CONFIG['PORT'],
            debug=APP_CONFIG['DEBUG']
        )
        
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {str(e)}")
        print("请检查错误信息并重试")

if __name__ == '__main__':
    main() 