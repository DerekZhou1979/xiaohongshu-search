#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
豫园股份-小红书搜索工具主程序
"""

import os
import sys
import argparse
import subprocess
import time

# 添加项目根目录到Python路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# ===========================================
# 应用配置
# ===========================================

APP_CONFIG = {
    'DEBUG': False,
    'HOST': '0.0.0.0',
    'PORT': int(os.environ.get('PORT', 8080)),  # 支持环境变量端口
    'SECRET_KEY': os.environ.get('SECRET_KEY', 'xiaohongshu_search_2024')
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

# ===========================================
# 全局爬虫配置（从config.py整合过来）
# ===========================================

CRAWL_CONFIG = {
    'enable_debug_screenshots': False,
    'enable_strategy_1': True,
    'enable_strategy_2': True,
    'enable_strategy_3': True,
    'validation_strict_level': 'medium',
    'enable_detailed_logs': True,
    'screenshot_interval': 0,
}

def get_crawl_config():
    """获取爬虫配置"""
    import os
    import json
    
    # 从环境变量读取配置
    config_str = os.environ.get('CRAWL_CONFIG')
    if config_str:
        try:
            return json.loads(config_str)
        except:
            pass
    
    return CRAWL_CONFIG

def show_config_menu():
    """显示配置选择菜单"""
    print("🚀 启动小红书搜索工具...")
    print("=" * 50)
    print("📋 请选择运行模式：")
    print("")
    print("1️⃣  标准模式（推荐）")
    print("   - 启用所有策略")
    print("   - 关闭调试截图")
    print("   - 适中的验证严格度")
    print("")
    print("2️⃣  调试模式")
    print("   - 启用所有策略")
    print("   - 开启详细截图")
    print("   - 保存所有调试信息")
    print("")
    print("3️⃣  快速模式")
    print("   - 仅启用策略1（最快）")
    print("   - 关闭截图和详细日志")
    print("   - 降低验证严格度")
    print("")
    print("4️⃣  兼容模式")
    print("   - 启用所有策略")
    print("   - 关闭截图")
    print("   - 最低验证严格度")
    print("")
    print("5️⃣  自定义模式")
    print("   - 手动配置各项功能")
    print("")
    print("=" * 50)
    
    while True:
        try:
            choice = input("请输入选择（1-5）: ").strip()
            if choice in ['1', '2', '3', '4', '5']:
                return int(choice)
            else:
                print("❌ 请输入有效的数字（1-5）")
        except KeyboardInterrupt:
            print("\n👋 用户取消，退出程序")
            sys.exit(0)
        except Exception:
            print("❌ 输入无效，请重试")

def get_config_by_mode(mode):
    """根据模式返回配置"""
    configs = {
        1: {  # 标准模式
            'name': '标准模式',
            'enable_debug_screenshots': False,
            'enable_strategy_1': True,
            'enable_strategy_2': True, 
            'enable_strategy_3': True,
            'validation_strict_level': 'medium',
            'enable_detailed_logs': True,
            'screenshot_interval': 0,  # 不截图
        },
        2: {  # 调试模式
            'name': '调试模式',
            'enable_debug_screenshots': True,
            'enable_strategy_1': True,
            'enable_strategy_2': True,
            'enable_strategy_3': True,
            'validation_strict_level': 'medium',
            'enable_detailed_logs': True,
            'screenshot_interval': 1,  # 每1秒截图
        },
        3: {  # 快速模式
            'name': '快速模式',
            'enable_debug_screenshots': False,
            'enable_strategy_1': True,
            'enable_strategy_2': False,
            'enable_strategy_3': False,
            'validation_strict_level': 'low',
            'enable_detailed_logs': False,
            'screenshot_interval': 0,
        },
        4: {  # 兼容模式
            'name': '兼容模式',
            'enable_debug_screenshots': False,
            'enable_strategy_1': True,
            'enable_strategy_2': True,
            'enable_strategy_3': True,
            'validation_strict_level': 'low',
            'enable_detailed_logs': True,
            'screenshot_interval': 0,
        },
        5: {  # 自定义模式
            'name': '自定义模式',
            'enable_debug_screenshots': None,  # 需要用户选择
            'enable_strategy_1': None,
            'enable_strategy_2': None,
            'enable_strategy_3': None,
            'validation_strict_level': None,
            'enable_detailed_logs': None,
            'screenshot_interval': None,
        }
    }
    return configs.get(mode, configs[1])

def get_custom_config():
    """获取自定义配置"""
    config = {
        'name': '自定义模式',
        'enable_debug_screenshots': False,
        'enable_strategy_1': True,
        'enable_strategy_2': True,
        'enable_strategy_3': True,
        'validation_strict_level': 'medium',
        'enable_detailed_logs': True,
        'screenshot_interval': 0,
    }
    
    print("\n🔧 自定义配置：")
    
    # 策略选择
    print("\n📋 提取策略选择：")
    config['enable_strategy_1'] = input("启用策略1（探索链接提取）？[Y/n]: ").lower() != 'n'
    config['enable_strategy_2'] = input("启用策略2（数据属性提取）？[Y/n]: ").lower() != 'n' 
    config['enable_strategy_3'] = input("启用策略3（JavaScript提取）？[Y/n]: ").lower() != 'n'
    
    # 验证严格度
    print("\n🔍 验证严格度选择：")
    print("1. 低（接受大部分结果）")
    print("2. 中等（平衡准确性和数量）")
    print("3. 高（严格验证）")
    strict_choice = input("选择严格度 [1-3，默认2]: ").strip()
    strict_map = {'1': 'low', '2': 'medium', '3': 'high'}
    config['validation_strict_level'] = strict_map.get(strict_choice, 'medium')
    
    # 调试功能
    print("\n🔧 调试功能：")
    config['enable_debug_screenshots'] = input("启用调试截图？[y/N]: ").lower() == 'y'
    if config['enable_debug_screenshots']:
        interval = input("截图间隔（秒，默认5）: ").strip()
        config['screenshot_interval'] = int(interval) if interval.isdigit() else 5
    
    config['enable_detailed_logs'] = input("启用详细日志？[Y/n]: ").lower() != 'n'
    
    return config

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
            return len(temp_files)
    return 0

def check_port(port):
    """检查端口是否被占用"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def main():
    """主函数"""
    try:
        # 显示配置菜单
        mode = show_config_menu()
        config = get_config_by_mode(mode)
        
        if mode == 5:  # 自定义模式
            config = get_custom_config()
        
        print(f"\n✅ 已选择：{config['name']}")
        print("=" * 50)
        
        # 环境设置
        import json
        os.environ['CRAWL_CONFIG'] = json.dumps(config)  # 将配置传递给爬虫
        
        print("🔍 检查Python依赖...")
        check_dependencies()
        print("✅ 依赖检查完成")
        
        print("🧹 清理临时文件...")
        cleanup_count = cleanup_temp_files()
        print(f"✅ 临时文件清理完成 - 清理 {cleanup_count} 个文件")
        
        print("📁 创建目录...")
        create_directories()
        print("✅ 目录创建完成")
        
        # 显示启动信息
        print(f"📍 项目根目录: {PROJECT_ROOT}")
        print(f"🌐 服务地址: http://localhost:{APP_CONFIG['PORT']}")
        print(f"📊 配置模式: {config['name']}")
        print(f"💾 缓存目录: {os.path.join(PROJECT_ROOT, 'cache')}")
        print("=" * 50)
        
        # 启动服务器
        os.environ["FLASK_APP"] = "src.server.main_server"
        subprocess.run([
            sys.executable, "-m", "flask", "run", 
            "--host=0.0.0.0", f"--port={APP_CONFIG['PORT']}"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 用户中断，正在退出...")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 