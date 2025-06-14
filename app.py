#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
小红书搜索工具 - 整合启动文件
确保所有依赖服务在localhost访问前完成初始化，使用本地ChromeDriver
"""

import sys
import os
import logging
import time
import threading
import shutil
from flask import Flask

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(__file__))

# 导入全局配置
from config.config import (
    APP_CONFIG, SEARCH_CONFIG, CRAWLER_CONFIG, 
    DIRECTORIES, FILE_PATHS, LOGGING_CONFIG,
    create_directories, validate_config
)

# 创建必要的目录
create_directories()

# 配置日志 - 使用全局配置
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['LEVEL']), 
    format=LOGGING_CONFIG['FORMAT'],
    handlers=[
        logging.FileHandler(FILE_PATHS['STARTUP_LOG'], encoding=LOGGING_CONFIG['ENCODING']),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def cleanup_cache():
    """清理缓存目录中的过期文件，保留cookies目录和最新的日志文件"""
    logger.info("正在清理缓存过期文件...")
    
    try:
        cache_dir = DIRECTORIES['CACHE_DIR']
        
        if not os.path.exists(cache_dir):
            logger.info("缓存目录不存在，无需清理")
            return True
        
        # 保护的目录列表（不删除）
        protected_dirs = ['cookies']
        
        # 统计清理的文件和目录数量
        cleaned_files = 0
        cleaned_dirs = 0
        
        # 遍历cache目录中的所有项目
        for item in os.listdir(cache_dir):
            item_path = os.path.join(cache_dir, item)
            
            # 跳过受保护的目录
            if item in protected_dirs:
                logger.info(f"保留受保护的目录: {item}")
                continue
            
            # 特殊处理logs目录：只保留最新的日志文件
            if item == 'logs' and os.path.isdir(item_path):
                cleaned_log_files = _cleanup_logs_directory(item_path)
                cleaned_files += cleaned_log_files
                logger.info(f"logs目录清理完成，删除了 {cleaned_log_files} 个旧日志文件")
                continue
            
            try:
                if os.path.isfile(item_path):
                    # 删除文件
                    os.remove(item_path)
                    cleaned_files += 1
                    logger.debug(f"删除文件: {item}")
                elif os.path.isdir(item_path):
                    # 删除目录及其内容
                    shutil.rmtree(item_path)
                    cleaned_dirs += 1
                    logger.debug(f"删除目录: {item}")
                    
            except Exception as e:
                logger.warning(f"删除 {item} 时出错: {str(e)}")
                continue
        
        logger.info(f"✓ 缓存清理完成: 删除了 {cleaned_files} 个文件, {cleaned_dirs} 个目录")
        
        # 重新创建必要的目录
        essential_dirs = ['temp', 'logs', 'results']
        for dir_name in essential_dirs:
            dir_path = os.path.join(cache_dir, dir_name)
            os.makedirs(dir_path, exist_ok=True)
        
        logger.info("✓ 重新创建必要的缓存目录")
        return True
        
    except Exception as e:
        logger.error(f"清理缓存时出错: {str(e)}")
        return False

def _cleanup_logs_directory(logs_dir):
    """清理logs目录，只保留最新的日志文件"""
    try:
        if not os.path.exists(logs_dir):
            return 0
        
        # 获取所有日志文件
        log_files = []
        for filename in os.listdir(logs_dir):
            file_path = os.path.join(logs_dir, filename)
            if os.path.isfile(file_path) and filename.endswith('.log'):
                # 获取文件的修改时间
                mtime = os.path.getmtime(file_path)
                log_files.append((file_path, mtime, filename))
        
        # 如果没有日志文件，返回
        if not log_files:
            return 0
        
        # 按修改时间排序，最新的在前
        log_files.sort(key=lambda x: x[1], reverse=True)
        
        # 保留最新的日志文件，删除其他的
        cleaned_count = 0
        for i, (file_path, mtime, filename) in enumerate(log_files):
            if i == 0:
                # 保留最新的日志文件
                logger.info(f"保留最新日志文件: {filename}")
            else:
                # 删除旧的日志文件
                try:
                    os.remove(file_path)
                    cleaned_count += 1
                    logger.debug(f"删除旧日志文件: {filename}")
                except Exception as e:
                    logger.warning(f"删除日志文件 {filename} 时出错: {str(e)}")
        
        return cleaned_count
        
    except Exception as e:
        logger.warning(f"清理logs目录时出错: {str(e)}")
        return 0

def check_dependencies():
    """检查和安装所有依赖"""
    logger.info("正在检查系统依赖...")
    
    try:
        # 检查基础Python包
        import selenium
        import flask
        import flask_cors
        import requests
        import bs4
        logger.info("✓ 基础Python包检查完成")
    except ImportError as e:
        logger.error(f"缺少必要的Python包: {e}")
        logger.info("正在安装缺失的依赖...")
        os.system("python3 -m pip install -r requirements.txt")
        return False
    
    # 检查Chrome和chromedriver
    try:
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if not os.path.exists(chrome_path):
            logger.warning("未找到Chrome浏览器，请确保已安装Google Chrome")
        else:
            logger.info("✓ Chrome浏览器检查完成")
    except Exception as e:
        logger.error(f"Chrome检查失败: {e}")
        return False
    
    return True

def initialize_webdriver():
    """初始化WebDriver - 使用全局配置"""
    logger.info("正在初始化WebDriver...")
    
    try:
        from selenium.webdriver.chrome.service import Service
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        # 配置Chrome选项 - 使用全局配置
        chrome_options = Options()
        for option in CRAWLER_CONFIG['CHROME_OPTIONS']:
            chrome_options.add_argument(option)
        
        # 使用本地chromedriver
        local_driver_path = FILE_PATHS['CHROMEDRIVER_PATH']
        
        if os.path.exists(local_driver_path):
            logger.info(f"找到本地chromedriver: {local_driver_path}")
            
            # 设置文件权限
            os.chmod(local_driver_path, 0o755)
            
            # 验证本地chromedriver
            service = Service(local_driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.get("data:text/html,<html><body><h1>WebDriver Validation</h1></body></html>")
            driver.quit()
            
            logger.info("✓ 本地chromedriver验证成功")
            return True
        else:
            logger.error("本地chromedriver不存在")
            logger.info("请确保drivers/chromedriver-mac-arm64/chromedriver文件存在")
            return False
                
    except Exception as e:
        logger.error(f"WebDriver初始化失败: {e}")
        return False

def initialize_crawler():
    """预初始化爬虫组件"""
    logger.info("正在预初始化爬虫组件...")
    
    try:
        from src.crawler.xiaohongshu_crawler import XiaoHongShuCrawler
        
        # 创建配置目录 - 使用全局配置
        for dir_path in DIRECTORIES.values():
            os.makedirs(dir_path, exist_ok=True)
        
        logger.info("✓ 爬虫组件预初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"爬虫组件预初始化失败: {e}")
        return False

def start_flask_app():
    """启动Flask应用"""
    logger.info("正在启动Flask应用...")
    
    try:
        from src.server.main_server import app
        
        # 创建静态文件目录
        os.makedirs(os.path.join(DIRECTORIES['STATIC_DIR'], 'css'), exist_ok=True)
        os.makedirs(os.path.join(DIRECTORIES['STATIC_DIR'], 'js'), exist_ok=True)
        os.makedirs(os.path.join(DIRECTORIES['STATIC_DIR'], 'images'), exist_ok=True)
        
        logger.info("所有服务初始化完成！")
        logger.info("=" * 50)
        logger.info("小红书搜索服务已就绪")
        logger.info(f"访问地址: http://{APP_CONFIG['HOST']}:{APP_CONFIG['PORT']}")
        logger.info(f"如需登录，请访问: http://{APP_CONFIG['HOST']}:{APP_CONFIG['PORT']}/login")
        logger.info(f"默认搜索结果数量: {SEARCH_CONFIG['DEFAULT_MAX_RESULTS']} 篇笔记")
        logger.info("=" * 50)
        
        # 启动Flask应用 - 使用全局配置
        app.run(debug=APP_CONFIG['DEBUG'], host=APP_CONFIG['HOST'], port=APP_CONFIG['PORT'])
        
    except Exception as e:
        logger.error(f"Flask应用启动失败: {e}")
        raise

def main():
    """主启动函数"""
    start_time = time.time()
    logger.info("开始启动小红书搜索服务...")
    
    try:
        # 步骤0: 验证配置
        config_errors = validate_config()
        if config_errors:
            logger.warning("配置验证发现问题:")
            for error in config_errors:
                logger.warning(f"  - {error}")
        else:
            logger.info("✓ 配置验证通过")
        
        # 步骤1: 清理缓存过期文件
        if not cleanup_cache():
            logger.warning("缓存清理失败，但继续启动...")
        
        # 步骤2: 检查依赖
        if not check_dependencies():
            logger.error("依赖检查失败，请手动安装所需依赖")
            return False
        
        # 步骤3: 初始化WebDriver（使用本地chromedriver）
        if not initialize_webdriver():
            logger.error("WebDriver初始化失败，请检查本地chromedriver")
            return False
        
        # 步骤4: 预初始化爬虫组件
        if not initialize_crawler():
            logger.error("爬虫组件预初始化失败")
            return False
        
        # 步骤5: 启动Flask应用
        elapsed_time = time.time() - start_time
        logger.info(f"所有初始化步骤完成，用时: {elapsed_time:.2f}秒")
        
        start_flask_app()
        
    except KeyboardInterrupt:
        logger.info("服务已停止")
    except Exception as e:
        logger.error(f"启动失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 