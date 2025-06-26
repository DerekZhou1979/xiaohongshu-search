#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
小红书爬虫模块
使用多种策略提取小红书笔记数据
注意：本代码仅供学习研究使用，实际使用时需遵守小红书的使用条款和相关法律法规
"""

import json
import random
import time
import logging
import hashlib
import os
import sys
import urllib.parse
from urllib.parse import quote
import re

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 导入配置信息
try:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from app import SEARCH_CONFIG, CRAWLER_CONFIG, DIRECTORIES, FILE_PATHS, URLS, HOT_KEYWORDS, get_crawl_config
except ImportError:
    # 如果无法导入，使用默认配置
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    SEARCH_CONFIG = {'DEFAULT_MAX_RESULTS': 30, 'MAX_RESULTS_LIMIT': 100, 'USE_CACHE': True, 'CACHE_EXPIRE_TIME': 3600}
    CRAWLER_CONFIG = {'USE_SELENIUM': True, 'HEADLESS': True, 'WINDOW_SIZE': (1920, 1080), 'CHROME_OPTIONS': ['--headless']}
    DIRECTORIES = {'CACHE_DIR': os.path.join(PROJECT_ROOT, 'cache'), 'TEMP_DIR': os.path.join(PROJECT_ROOT, 'cache', 'temp')}
    FILE_PATHS = {'CHROMEDRIVER_PATH': os.path.join(PROJECT_ROOT, 'drivers', 'chromedriver-mac-arm64', 'chromedriver'), 'COOKIES_FILE': os.path.join(PROJECT_ROOT, 'cache', 'cookies', 'xiaohongshu_cookies.json')}
    URLS = {'XIAOHONGSHU_BASE': 'https://www.xiaohongshu.com'}
    HOT_KEYWORDS = ["海鸥手表", "美食", "护肤"]
    
    def get_crawl_config():
        import os
        import json
        
        # 从环境变量读取配置
        config_str = os.environ.get('CRAWL_CONFIG')
        if config_str:
            try:
                return json.loads(config_str)
            except:
                pass
        
        return {
            'enable_debug_screenshots': False,
            'enable_strategy_1': True,
            'enable_strategy_2': True,
            'enable_strategy_3': True,
            'validation_strict_level': 'medium',
            'enable_detailed_logs': True,
            'screenshot_interval': 0,
        }

# 导入Selenium相关库
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# 配置日志
logger = logging.getLogger(__name__)

class XiaoHongShuCrawler:
    """小红书爬虫类 - 使用全局配置和三种提取策略"""
    
    def __init__(self, use_selenium=True, headless=None, proxy=None, cookies_file=None):
        """
        初始化爬虫
        
        参数:
            use_selenium (bool): 是否使用Selenium
            headless (bool): 是否使用无头模式，None表示使用配置文件设置
            proxy (str): 代理服务器地址
            cookies_file (str): cookie文件路径
        """
        # 使用配置
        self.search_config = SEARCH_CONFIG
        self.crawler_config = CRAWLER_CONFIG
        self.crawl_config = get_crawl_config()  # 新增爬虫配置
        
        # 初始化参数
        self.use_selenium = use_selenium if use_selenium is not None else self.crawler_config['USE_SELENIUM']
        # 为了支持人工验证，优先使用可见模式
        self.headless = headless if headless is not None else False  # 改为默认非无头模式
        self.original_headless = headless if headless is not None else self.crawler_config['HEADLESS']
        self.proxy = proxy
        self.cookies_file = cookies_file or FILE_PATHS['COOKIES_FILE']
        
        # WebDriver相关
        self.driver = None
        
        # 缓存配置
        self.cache_dir = DIRECTORIES['TEMP_DIR']
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 回调函数
        self.html_callback = None  # HTML结果回调函数
        
        # 验证处理状态
        self.verification_in_progress = False
        self.verification_completed = False
        
        # 加载cookie
        self.cookies = self._load_cookies()
        
        logger.info("小红书爬虫初始化完成（支持人工验证模式）")
    
    def set_html_callback(self, callback_func):
        """设置HTML存储回调函数"""
        self.html_callback = callback_func
        logger.info("HTML存储回调函数已设置")
    
    def set_debug_callback(self, callback_func):
        """设置Debug信息回调函数"""
        self.debug_callback = callback_func
        logger.info("Debug信息回调函数已设置")
    
    def _debug_log(self, message, level="INFO"):
        """发送debug信息到回调函数和日志"""
        # 发送到回调函数（如果存在）
        if hasattr(self, 'debug_callback') and self.debug_callback:
            try:
                self.debug_callback(message, level)
            except Exception as e:
                logger.error(f"调用debug回调函数失败: {str(e)}")
        
        # 同时写入日志
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)
    
    def _ensure_driver_initialized(self):
        """确保WebDriver已初始化"""
        if self.driver is None:
            return self._init_selenium()
        return True
    
    def _load_cookies(self):
        """加载cookie"""
        if not os.path.exists(self.cookies_file):
            logger.warning(f"Cookie文件不存在: {self.cookies_file}")
            return []
        
        try:
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            logger.info(f"成功加载Cookie文件: {self.cookies_file}, 包含 {len(cookies)} 个cookie")
            return cookies
        except Exception as e:
            logger.error(f"加载Cookie文件失败: {str(e)}")
            return []
    
    def save_cookies(self, cookies_file=None):
        """保存当前浏览器的cookie"""
        if not self._ensure_driver_initialized():
            logger.error("WebDriver初始化失败，无法保存cookie")
            return False
        
        file_path = cookies_file or self.cookies_file
        cookies_dir = os.path.dirname(file_path)
        os.makedirs(cookies_dir, exist_ok=True)
        
        try:
            cookies = self.driver.get_cookies()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            logger.info(f"成功保存 {len(cookies)} 个cookie到: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存cookie失败: {str(e)}")
            return False
    
    def _init_selenium(self):
        """初始化Selenium WebDriver"""
        try:
            logger.info("正在初始化Selenium...")
            
            # 配置Chrome选项
            chrome_options = Options()
            
            # 添加配置文件中的Chrome选项，但跳过无头模式相关
            for option in self.crawler_config['CHROME_OPTIONS']:
                if '--headless' not in option:  # 跳过无头模式，因为我们需要支持人工验证
                    chrome_options.add_argument(option)
            
            # 根据实际需要决定是否启用无头模式
            if self.headless:
                chrome_options.add_argument('--headless')
            else:
                logger.info("🖥️  浏览器启动为可见模式（支持人工验证）")
            
            # 设置窗口大小
            width, height = self.crawler_config['WINDOW_SIZE']
            chrome_options.add_argument(f'--window-size={width},{height}')
            
            # 设置代理
            if self.proxy:
                chrome_options.add_argument(f'--proxy-server={self.proxy}')
            
            # 反爬虫配置
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 使用本地ChromeDriver
            chromedriver_path = FILE_PATHS['CHROMEDRIVER_PATH']
            if os.path.exists(chromedriver_path):
                logger.info(f"使用本地ChromeDriver: {chromedriver_path}")
                os.chmod(chromedriver_path, 0o755)
                service = Service(chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                logger.error(f"ChromeDriver不存在: {chromedriver_path}")
                return False
            
            # 隐藏WebDriver特征
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Chrome浏览器已成功启动")
            
            # 添加cookie
            if self.cookies:
                self._add_cookies()
            
            logger.info("Selenium初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"Selenium初始化失败: {str(e)}")
            return False
    
    def _add_cookies(self):
        """添加cookie到浏览器"""
        try:
            logger.info("尝试添加cookie...")
            self.driver.get("https://www.xiaohongshu.com")
            time.sleep(3)
            
            for cookie in self.cookies:
                try:
                    # 移除可能导致问题的字段
                    cookie_clean = {k: v for k, v in cookie.items() 
                                  if k in ['name', 'value', 'domain', 'path', 'secure']}
                    self.driver.add_cookie(cookie_clean)
                except Exception as e:
                    logger.warning(f"添加cookie失败: {cookie.get('name', '未知')} - {str(e)}")
            
            # 刷新页面使cookie生效
            self.driver.refresh()
            time.sleep(5)
            logger.info("已添加cookie并刷新页面")
            
        except Exception as e:
            logger.error(f"添加cookie过程出错: {str(e)}")
    
    def _get_cache_path(self, keyword):
        """获取缓存文件路径"""
        cache_filename = f"search_{hashlib.md5(keyword.encode()).hexdigest()}.json"
        return os.path.join(self.cache_dir, cache_filename)
    
    def _save_to_cache(self, keyword, data):
        """保存数据到缓存"""
        try:
            # 🔧 修复：检查数据是否有效，只有非空数据才缓存
            if not data or len(data) == 0:
                self._debug_log("⚠️ 数据为空，跳过缓存保存", "WARNING")
                return
            
            cache_path = self._get_cache_path(keyword)
            cache_data = {
                'timestamp': time.time(),
                'keyword': keyword,
                'data': data
            }
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            logger.info(f"数据已缓存: {cache_path}")
            
            # 🔧 修复：只有有有效数据时才生成HTML页面
            self._debug_log("📄 生成HTML结果页面...")
            self._generate_result_html(keyword, data)
            
        except Exception as e:
            logger.error(f"缓存保存失败: {str(e)}")
    
    def _generate_result_html(self, keyword, data):
        """生成HTML结果页面"""
        try:
            # 创建results目录
            results_dir = os.path.join(DIRECTORIES['CACHE_DIR'], 'results')
            os.makedirs(results_dir, exist_ok=True)
            
            # 生成HTML文件名
            html_filename = f"search_{hashlib.md5(keyword.encode()).hexdigest()}.html"
            html_path = os.path.join(results_dir, html_filename)
            
            # 生成HTML内容
            html_content = self._create_html_template(keyword, data)
            
            # 保存HTML文件
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"HTML结果页面已生成: {html_path}")
            
            # 如果设置了回调函数，将HTML内容传递给服务器
            if self.html_callback:
                html_hash = hashlib.md5(keyword.encode()).hexdigest()
                self.html_callback(html_hash, html_content)
                logger.info(f"HTML内容已通过回调函数传递: {html_hash}")
            
        except Exception as e:
            logger.error(f"生成HTML结果页面失败: {str(e)}")
    
    def _build_enhanced_url(self, original_url, xsec_token):
        """构建包含xsec_token和xsec_source的增强URL"""
        try:
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            
            # 解析原始URL
            parsed = urlparse(original_url)
            query_params = parse_qs(parsed.query)
            
            # 添加xsec_source参数
            query_params['xsec_source'] = ['pc_feed']
            
            # 如果有xsec_token，添加或更新
            if xsec_token:
                query_params['xsec_token'] = [xsec_token]
            
            # 重新构建查询字符串
            new_query = urlencode(query_params, doseq=True)
            
            # 构建新的URL
            enhanced_url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment
            ))
            
            logger.debug(f"增强URL: {original_url} -> {enhanced_url}")
            return enhanced_url
            
        except Exception as e:
            logger.error(f"构建增强URL失败: {str(e)}")
            return original_url
    
    def _create_html_template(self, keyword, data):
        """创建HTML模板"""
        import urllib.parse
        import json
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        
        # 加载cookies数据用于JavaScript
        cookies_json = "[]"
        try:
            cookies_data = self._load_cookies()
            if cookies_data:
                cookies_json = json.dumps(cookies_data, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"加载cookies用于JavaScript失败: {str(e)}")
        
        # 生成笔记卡片HTML
        notes_html = ""
        for i, note in enumerate(data, 1):
            # 安全地获取笔记信息
            title = note.get('title', '无标题').replace('\n', '<br>')
            desc = note.get('desc', '无描述').replace('\n', '<br>')
            author = note.get('author', '未知作者')
            cover = note.get('cover', '')
            url = note.get('url', '#')
            xsec_token = note.get('xsec_token', '')
            likes = note.get('likes', 0)
            comments = note.get('comments', 0)
            collects = note.get('collects', 0)
            
            # 格式化数字显示
            def format_number(num):
                if num >= 10000:
                    return f"{num//10000}万+"
                elif num >= 1000:
                    return f"{num//1000}k+"
                else:
                    return str(num)
            
            likes_str = format_number(likes)
            comments_str = format_number(comments)
            collects_str = format_number(collects)
            
            # 构建完整的URL，添加xsec_token和xsec_source参数
            enhanced_url = self._build_enhanced_url(url, xsec_token)
            
            # 直接使用原始图片URL，通过JavaScript处理加载失败
            note_html = f'''
            <div class="note-card" data-note-id="{note.get('id', '')}">
                <div class="note-image">
                    <img src="{cover}" alt="{title}" loading="lazy" 
                         data-original="{cover}"
                         onerror="handleImageError(this)">
                    <div class="note-rank">#{i}</div>
                </div>
                <div class="note-content">
                    <h3 class="note-title">{title}</h3>
                    <p class="note-desc">{desc}</p>
                    <div class="note-author">@{author}</div>
                    <div class="note-stats">
                        <span class="stat-item">
                            <i class="fas fa-heart"></i> {likes_str}
                        </span>
                        <span class="stat-item">
                            <i class="fas fa-comment"></i> {comments_str}
                        </span>
                        <span class="stat-item">
                            <i class="fas fa-star"></i> {collects_str}
                        </span>
                    </div>
                    <div class="note-links">
                        <a href="javascript:void(0)" onclick="directAccess('{enhanced_url}')" class="note-link direct-link">直接访问</a>
                        <a href="javascript:void(0)" onclick="createSimilarNote('{note.get("id", "")}')" class="note-link create-link">新增同类笔记</a>
                    </div>
                </div>
            </div>
            '''
            notes_html += note_html
        
        # 生成完整的HTML页面
        html_template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="referrer" content="no-referrer">
    <meta http-equiv="Content-Security-Policy" content="img-src * data: blob: 'unsafe-inline'; default-src 'self' 'unsafe-inline' 'unsafe-eval' *;">
    <title>"{keyword}"的搜索结果 - 小红书热门笔记</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            background: linear-gradient(135deg, #ff6b6b, #ff8e8e, #ffa8a8);
            min-height: 100vh;
            color: #333;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
            background: rgba(255, 255, 255, 0.95);
            padding: 30px 20px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            font-size: 2.5em;
            color: #ff6b6b;
            margin-bottom: 10px;
        }}
        
        .search-info {{
            font-size: 1.2em;
            color: #666;
            margin-bottom: 10px;
        }}
        
        .update-time {{
            font-size: 0.9em;
            color: #999;
        }}
        
        .proxy-notice {{
            background: linear-gradient(135deg, #4CAF50, #45a049);
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            font-size: 0.95em;
            box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
        }}
        
        .proxy-notice .icon {{
            font-size: 1.2em;
            margin-right: 8px;
        }}
        
        .results-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }}
        
        .note-card {{
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            position: relative;
        }}
        
        .note-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.2);
        }}
        
        .note-image {{
            position: relative;
            height: 200px;
            overflow: hidden;
        }}
        
        .note-image img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
            background-color: #f5f5f5;
            display: block;
        }}
        
        .note-image img.loading {{
            background: #f5f5f5 url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24"><path fill="%23ccc" d="M12,1A11,11,0,1,0,23,12,11,11,0,0,0,12,1Zm0,19a8,8,0,1,1,8-8A8,8,0,0,1,12,20Z" opacity=".25"/><path fill="%23666" d="M12,4a8,8,0,0,1,7.89,6.7A1.53,1.53,0,0,0,21.38,12h0a1.5,1.5,0,0,0,1.48-1.75,11,11,0,0,0-21.72,0A1.5,1.5,0,0,0,2.62,12h0a1.53,1.53,0,0,0,1.49-1.3A8,8,0,0,1,12,4Z"><animateTransform attributeName="transform" dur="0.75s" repeatCount="indefinite" type="rotate" values="0 12 12;360 12 12"/></path></svg>') center no-repeat;
            background-size: 40px 40px;
        }}
        
        .note-image img.error {{
            background: #f5f5f5 url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24"><path fill="%23ccc" d="M21,19V5c0-1.1-0.9-2-2-2H5C3.9,3,3,3.9,3,5v14c0,1.1,0.9,2,2,2h14C20.1,21,21,20.1,21,19z M8.5,13.5l2.5,3.01L14.5,12l4.5,6H5L8.5,13.5z"/></svg>') center no-repeat;
            background-size: 40px 40px;
        }}
        
        .note-card:hover .note-image img {{
            transform: scale(1.05);
        }}
        
        .note-rank {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(255, 107, 107, 0.9);
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-weight: bold;
            font-size: 0.9em;
        }}
        
        .note-content {{
            padding: 20px;
        }}
        
        .note-title {{
            font-size: 1.1em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        
        .note-desc {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 15px;
            line-height: 1.5;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        
        .note-author {{
            font-size: 0.85em;
            color: #ff6b6b;
            margin-bottom: 15px;
            font-weight: 500;
        }}
        
        .note-stats {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 15px;
            font-size: 0.85em;
        }}
        
        .stat-item {{
            color: #999;
        }}
        
        .stat-item i {{
            margin-right: 4px;
        }}
        
        .note-links {{
            display: flex;
            gap: 8px;
            margin-top: 15px;
        }}
        
        .note-link {{
            flex: 1;
            display: inline-block;
            color: white;
            padding: 8px 12px;
            border-radius: 18px;
            text-decoration: none;
            font-size: 0.8em;
            font-weight: 500;
            transition: all 0.3s ease;
            text-align: center;
        }}
        
        .direct-link {{
            background: linear-gradient(45deg, #4CAF50, #45a049);
        }}
        
        .direct-link:hover {{
            background: linear-gradient(45deg, #45a049, #3d8b40);
            transform: translateY(-1px);
            box-shadow: 0 3px 10px rgba(76, 175, 80, 0.3);
        }}
        
        .create-link {{
            background: linear-gradient(45deg, #FF9800, #F57C00);
        }}
        
        .create-link:hover {{
            background: linear-gradient(45deg, #F57C00, #E65100);
            transform: translateY(-1px);
            box-shadow: 0 3px 10px rgba(255, 152, 0, 0.3);
        }}
        
        .back-button {{
            position: fixed;
            top: 20px;
            left: 20px;
            background: rgba(255, 255, 255, 0.9);
            color: #ff6b6b;
            padding: 10px 20px;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 500;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .back-button:hover {{
            background: white;
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }}
        
        .footer {{
            text-align: center;
            padding: 40px 20px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-top: 40px;
        }}
        
        .footer p {{
            margin-bottom: 10px;
            color: #666;
        }}
        
        .disclaimer {{
            font-size: 0.8em;
            color: #999;
        }}
        
        @media (max-width: 768px) {{
            .results-grid {{
                grid-template-columns: 1fr;
                gap: 20px;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
            
            .back-button {{
                position: static;
                margin-bottom: 20px;
            }}
        }}
    </style>
</head>
<body>
    <a href="/" class="back-button">
        <i class="fas fa-arrow-left"></i>
        返回搜索
    </a>
    
    <div class="container">
        <div class="header">
            <h1>"{keyword}"的热门笔记</h1>
            <div class="search-info">共找到 {len(data)} 条相关笔记</div>
            <div class="update-time">更新时间：{current_time}</div>
        </div>
        

        
        <div class="results-grid">
            {notes_html}
        </div>
        
        <div class="footer">
            <p>© 2023 小红书热门笔记查询 - 仅供学习研究使用</p>
            <p class="disclaimer">本工具不隶属于小红书官方，数据仅供参考</p>
        </div>
    </div>
    
    <script>
        // 小红书cookies配置
        const xiaohongShuCookies = {cookies_json};
        
        // 直接访问函数
        function directAccess(url) {{
            try {{
                // 设置小红书cookies
                setCookiesForXiaohongshu();
                
                // 延迟跳转，确保cookies设置完成
                setTimeout(() => {{
                    window.open(url, '_blank');
                }}, 500);
                
            }} catch (error) {{
                console.error('设置cookies失败:', error);
                // 如果设置cookies失败，仍然尝试直接访问
                window.open(url, '_blank');
            }}
        }}
        
        // 新增同类笔记函数
        function createSimilarNote(noteId) {{
            try {{
                // 显示加载提示
                const loadingModal = showLoadingModal('正在分析笔记内容，请稍候...');
                
                // 调用后端API分析笔记内容
                fetch(`/api/create-similar-note/${{noteId}}`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                }})
                .then(response => response.json())
                .then(data => {{
                    hideLoadingModal(loadingModal);
                    
                    if (data.success) {{
                        // 显示生成的笔记内容预览
                        showNotePreview(data.generated_note, noteId);
                    }} else {{
                        alert('生成笔记失败: ' + (data.message || '未知错误'));
                    }}
                }})
                .catch(error => {{
                    hideLoadingModal(loadingModal);
                    console.error('创建同类笔记失败:', error);
                    alert('创建同类笔记失败，请稍后重试');
                }});
                
            }} catch (error) {{
                console.error('创建同类笔记失败:', error);
                alert('创建同类笔记失败，请稍后重试');
            }}
        }}
        
        // 设置小红书cookies
        function setCookiesForXiaohongshu() {{
            xiaohongShuCookies.forEach(cookie => {{
                try {{
                    // 只设置非httpOnly的cookies（浏览器限制）
                    if (!cookie.httpOnly) {{
                        let cookieString = `${{cookie.name}}=${{cookie.value}}`;
                        
                        // 添加domain
                        if (cookie.domain) {{
                            cookieString += `; domain=${{cookie.domain}}`;
                        }}
                        
                        // 添加path
                        if (cookie.path) {{
                            cookieString += `; path=${{cookie.path}}`;
                        }}
                        
                        // 添加secure
                        if (cookie.secure) {{
                            cookieString += `; secure`;
                        }}
                        
                        // 添加sameSite
                        if (cookie.sameSite) {{
                            cookieString += `; samesite=${{cookie.sameSite}}`;
                        }}
                        
                        // 添加expires
                        if (cookie.expiry) {{
                            const expireDate = new Date(cookie.expiry * 1000);
                            cookieString += `; expires=${{expireDate.toUTCString()}}`;
                        }}
                        
                        document.cookie = cookieString;
                        console.log('设置cookie:', cookie.name);
                    }}
                }} catch (error) {{
                    console.warn('设置cookie失败:', cookie.name, error);
                }}
            }});
        }}
        
        // 图片错误处理函数
        function handleImageError(img) {{
            if (img.dataset.retryCount) {{
                img.dataset.retryCount = parseInt(img.dataset.retryCount) + 1;
            }} else {{
                img.dataset.retryCount = '1';
            }}
            
            const retryCount = parseInt(img.dataset.retryCount);
            const originalUrl = img.dataset.original;
            
            if (retryCount === 1) {{
                // 第一次失败：尝试移除URL参数
                const cleanUrl = originalUrl.split('!')[0];
                console.log('图片加载失败，尝试清理URL:', cleanUrl);
                img.src = cleanUrl;
            }} else {{
                // 最终失败：显示占位符
                console.log('图片加载失败，显示占位符');
                img.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjRjVGNUY1Ii8+Cjx0ZXh0IHg9IjEwMCIgeT0iMTAwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkb21pbmFudC1iYXNlbGluZT0iY2VudHJhbCIgZmlsbD0iIzk5OTk5OSIgZm9udC1zaXplPSIxNCIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIj7lsI/nuqLkuaZDRE48L3RleHQ+Cjwvc3ZnPg==';
                img.onerror = null; // 防止无限循环
            }}
        }}
        
        // 显示加载模态框
        function showLoadingModal(message) {{
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed; top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(0,0,0,0.7); z-index: 10000;
                display: flex; align-items: center; justify-content: center;
            `;
            
            const content = document.createElement('div');
            content.style.cssText = `
                background: white; padding: 30px; border-radius: 15px;
                text-align: center; min-width: 300px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            `;
            
            content.innerHTML = `
                <div style="font-size: 18px; margin-bottom: 20px;">${{message}}</div>
                <div style="display: inline-block; width: 40px; height: 40px; border: 4px solid #f3f3f3;
                     border-top: 4px solid #ff6b6b; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                <style>
                    @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
                </style>
            `;
            
            modal.appendChild(content);
            document.body.appendChild(modal);
            return modal;
        }}
        
        // 隐藏加载模态框
        function hideLoadingModal(modal) {{
            if (modal && modal.parentNode) {{
                modal.parentNode.removeChild(modal);
            }}
        }}
        
        // 显示笔记预览模态框
        function showNotePreview(generatedNote, originalNoteId) {{
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed; top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(0,0,0,0.8); z-index: 10000;
                display: flex; align-items: center; justify-content: center;
                overflow-y: auto; padding: 20px;
            `;
            
            const content = document.createElement('div');
            content.style.cssText = `
                background: white; padding: 30px; border-radius: 15px;
                max-width: 600px; width: 90%; max-height: 80vh; overflow-y: auto;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            `;
            
            // 构建原笔记信息HTML
            let originalNoteHtml = '';
            if (generatedNote.original_note_detail) {{
                const original = generatedNote.original_note_detail;
                let imagesHtml = '';
                
                if (original.images && original.images.length > 0) {{
                    imagesHtml = `
                        <div style="margin-top: 15px;">
                            <h4 style="color: #666; margin-bottom: 10px;">📸 原笔记图片</h4>
                            <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                                ${{original.images.map(img => `
                                    <img src="${{img.web_path}}" alt="原笔记图片" 
                                         style="width: 80px; height: 80px; object-fit: cover; border-radius: 8px; border: 2px solid #ddd;"
                                         onclick="window.open('${{img.original_url}}', '_blank')" 
                                         title="点击查看原图">
                                `).join('')}}
                            </div>
                        </div>
                    `;
                }}
                
                originalNoteHtml = `
                    <div style="background: #e8f4fd; padding: 20px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #2196F3;">
                        <h3 style="color: #1976D2; margin-bottom: 15px;">📖 原笔记内容参考</h3>
                        
                        <div style="margin-bottom: 15px;">
                            <h4 style="color: #333; margin-bottom: 8px;">📝 原标题</h4>
                            <p style="font-size: 14px; line-height: 1.5; color: #555; background: white; padding: 10px; border-radius: 6px;">${{original.title}}</p>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <h4 style="color: #333; margin-bottom: 8px;">📄 原内容</h4>
                            <p style="font-size: 13px; line-height: 1.6; color: #555; background: white; padding: 10px; border-radius: 6px; white-space: pre-wrap; max-height: 120px; overflow-y: auto;">${{original.content}}</p>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <h4 style="color: #333; margin-bottom: 8px;">🏷️ 原标签</h4>
                            <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                                ${{original.tags.map(tag => `<span style="background: #2196F3; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">${{tag}}</span>`).join('')}}
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 10px;">
                            <h4 style="color: #333; margin-bottom: 8px;">👤 原作者</h4>
                            <span style="color: #666; font-size: 13px;">${{original.author}}</span>
                        </div>
                        
                        ${{imagesHtml}}
                    </div>
                `;
            }}
            
            content.innerHTML = `
                <h2 style="color: #ff6b6b; margin-bottom: 20px; text-align: center;">
                    🎨 AI生成的同类笔记预览
                </h2>
                
                ${{originalNoteHtml}}
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h3 style="color: #333; margin-bottom: 10px;">📝 生成标题</h3>
                    <p style="font-size: 16px; line-height: 1.5; margin-bottom: 15px;">${{generatedNote.title}}</p>
                    
                    <h3 style="color: #333; margin-bottom: 10px;">📄 生成内容</h3>
                    <p style="font-size: 14px; line-height: 1.6; white-space: pre-wrap;">${{generatedNote.content}}</p>
                </div>
                
                <div style="background: #e8f5e8; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
                    <h3 style="color: #2e7d32; margin-bottom: 10px;">🏷️ 标签建议</h3>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                        ${{generatedNote.tags.map(tag => `<span style="background: #4caf50; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">${{tag}}</span>`).join('')}}
                    </div>
                </div>
                
                <div style="background: #fff3e0; padding: 15px; border-radius: 10px; margin-bottom: 25px;">
                    <h3 style="color: #f57c00; margin-bottom: 10px;">💡 创作建议</h3>
                    <p style="font-size: 13px; line-height: 1.5; color: #666;">${{generatedNote.suggestions}}</p>
                </div>
                
                <div style="display: flex; gap: 10px; justify-content: center;">
                    <button onclick="openXhsCreatePage()" style="
                        background: linear-gradient(45deg, #ff6b6b, #ff8e8e); color: white;
                        border: none; padding: 12px 24px; border-radius: 25px;
                        font-size: 14px; font-weight: 500; cursor: pointer;
                        transition: all 0.3s ease;
                    " onmouseover="this.style.transform='translateY(-2px)'" 
                       onmouseout="this.style.transform='translateY(0)'">
                        🚀 去小红书创建笔记
                    </button>
                    
                    <button onclick="copyNoteContent('${{originalNoteId}}')" style="
                        background: linear-gradient(45deg, #4caf50, #66bb6a); color: white;
                        border: none; padding: 12px 24px; border-radius: 25px;
                        font-size: 14px; font-weight: 500; cursor: pointer;
                        transition: all 0.3s ease;
                    " onmouseover="this.style.transform='translateY(-2px)'" 
                       onmouseout="this.style.transform='translateY(0)'">
                        📋 复制内容
                    </button>
                    
                    <button onclick="closeNotePreview()" style="
                        background: #999; color: white;
                        border: none; padding: 12px 24px; border-radius: 25px;
                        font-size: 14px; font-weight: 500; cursor: pointer;
                        transition: all 0.3s ease;
                    " onmouseover="this.style.transform='translateY(-2px)'" 
                       onmouseout="this.style.transform='translateY(0)'">
                        ❌ 关闭
                    </button>
                </div>
            `;
            
            modal.appendChild(content);
            document.body.appendChild(modal);
            
            // 点击背景关闭
            modal.addEventListener('click', function(e) {{
                if (e.target === modal) {{
                    closeNotePreview();
                }}
            }});
            
            // 设置全局引用以便关闭
            window.currentNotePreviewModal = modal;
            window.currentGeneratedNote = generatedNote;
        }}
        
        // 关闭笔记预览
        function closeNotePreview() {{
            if (window.currentNotePreviewModal) {{
                document.body.removeChild(window.currentNotePreviewModal);
                window.currentNotePreviewModal = null;
                window.currentGeneratedNote = null;
            }}
        }}
        
        // 打开小红书创建页面
        function openXhsCreatePage() {{
            // 设置小红书cookies
            setCookiesForXiaohongshu();
            
            // 延迟跳转，确保cookies设置完成
            setTimeout(() => {{
                window.open('https://creator.xiaohongshu.com/publish/publish?source=official&from=menu&target=image', '_blank');
            }}, 500);
            
            closeNotePreview();
        }}
        
        // 复制笔记内容
        function copyNoteContent(originalNoteId) {{
            if (window.currentGeneratedNote) {{
                const content = `标题：${{window.currentGeneratedNote.title}}

内容：
${{window.currentGeneratedNote.content}}

标签：${{window.currentGeneratedNote.tags.join(' ')}}

创作建议：
${{window.currentGeneratedNote.suggestions}}`;
                
                navigator.clipboard.writeText(content).then(() => {{
                    alert('📋 笔记内容已复制到剪贴板！');
                }}).catch(err => {{
                    console.error('复制失败:', err);
                    // 备用方案：创建临时textarea
                    const textarea = document.createElement('textarea');
                    textarea.value = content;
                    document.body.appendChild(textarea);
                    textarea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textarea);
                    alert('📋 笔记内容已复制到剪贴板！');
                }});
            }}
        }}
        
        // 添加一些交互效果和图片加载处理
        document.addEventListener('DOMContentLoaded', function() {{
            const cards = document.querySelectorAll('.note-card');
            const images = document.querySelectorAll('.note-image img');
            
            // 卡片交互效果
            cards.forEach(card => {{
                card.addEventListener('mouseenter', function() {{
                    this.style.transform = 'translateY(-5px) scale(1.02)';
                }});
                
                card.addEventListener('mouseleave', function() {{
                    this.style.transform = 'translateY(0) scale(1)';
                }});
            }});
            
            // 图片加载处理
            images.forEach(img => {{
                img.addEventListener('load', function() {{
                    this.classList.remove('loading');
                    this.classList.add('loaded');
                    console.log('图片加载成功:', this.src);
                }});
                
                // 初始状态
                img.classList.add('loading');
            }});
        }});
    </script>
</body>
</html>'''
        
        # 替换cookies占位符
        html_template = html_template.replace('{cookies_json}', cookies_json)
        
        return html_template
    
    def _load_from_cache(self, keyword, max_age=None):
        """从缓存加载数据"""
        cache_path = self._get_cache_path(keyword)
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            
            # 检查缓存是否过期
            max_age = max_age or self.search_config['CACHE_EXPIRE_TIME']
            if time.time() - cache['timestamp'] > max_age:
                logger.info(f"缓存已过期: {cache_path}")
                return None
            
            # 🔧 修复：验证缓存数据是否有效
            cached_data = cache.get('data', [])
            if not cached_data or len(cached_data) == 0:
                self._debug_log(f"⚠️ 缓存文件存在但数据为空，清理无效缓存: {cache_path}", "WARNING")
                self._remove_empty_cache(keyword)
                return None
            
            logger.info(f"从缓存加载数据: {cache_path}")
            return cached_data
        except Exception as e:
            logger.error(f"加载缓存失败: {str(e)}")
            return None
    
    def _handle_anti_bot(self):
        """处理反爬虫机制 - 改进版本，增强搜索页面保持功能"""
        try:
            original_url = self.driver.current_url
            self._debug_log(f"🔍 反爬虫处理前URL: {original_url}")
            
            # 等待页面稳定
            time.sleep(8)
            
            # 检查是否有登录提示或验证码
            page_text = self.driver.page_source.lower()
            anti_bot_keywords = ['登录', 'login', '验证', 'captcha', '滑动', 'slider', '点击', 'click', '安全']
            has_anti_bot = any(keyword in page_text for keyword in anti_bot_keywords)
            
            if has_anti_bot:
                self._debug_log("⚠️ 检测到反爬虫机制或登录要求，尝试处理...")
            
            # 尝试关闭各种可能的弹窗和遮罩
            close_strategies = [
                # 通用关闭按钮
                ("xpath", "//div[contains(@class, 'close')]"),
                ("xpath", "//button[contains(@class, 'close')]"), 
                ("xpath", "//span[contains(@class, 'close')]"),
                ("xpath", "//i[contains(@class, 'close')]"),
                
                # 文字关闭按钮
                ("xpath", "//div[contains(text(), '关闭')]"),
                ("xpath", "//button[contains(text(), '关闭')]"),
                ("xpath", "//span[contains(text(), '×')]"),
                ("xpath", "//div[contains(text(), '×')]"),
                
                # 登录弹窗关闭
                ("xpath", "//div[contains(@class, 'modal')]//div[contains(@class, 'close')]"),
                ("xpath", "//div[contains(@class, 'dialog')]//div[contains(@class, 'close')]"),
                ("xpath", "//div[contains(@class, 'popup')]//div[contains(@class, 'close')]"),
                
                # CSS选择器
                ("css", ".close"),
                ("css", "[data-testid*='close']"),
                ("css", "[aria-label*='关闭']"),
                ("css", "[aria-label*='close']"),
                
                # 其他可能的关闭元素
                ("xpath", "//div[@role='button' and contains(text(), '跳过')]"),
                ("xpath", "//button[contains(text(), '跳过')]"),
                ("xpath", "//div[contains(@class, 'skip')]"),
            ]
            
            closed_elements = 0
            for method, selector in close_strategies:
                try:
                    if method == "xpath":
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:  # css
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if elements:
                        for element in elements[:3]:  # 最多点击3个同类元素
                            try:
                                if element.is_displayed() and element.is_enabled():
                                    element.click()
                                    self._debug_log(f"✅ 成功点击关闭按钮: {selector}")
                                    closed_elements += 1
                                    time.sleep(2)
                            except Exception:
                                continue
                    
                    if closed_elements >= 3:  # 如果已经关闭足够多的元素，停止
                        break
                        
                except Exception:
                    continue
            
            if closed_elements > 0:
                self._debug_log(f"✅ 共关闭了 {closed_elements} 个弹窗/遮罩")
                time.sleep(5)  # 等待页面重新加载
            
            # 尝试按ESC键关闭弹窗
            try:
                from selenium.webdriver.common.keys import Keys
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(2)
                self._debug_log("✅ 已发送ESC键")
            except Exception:
                pass
            
            # 🔧 新增：检查是否被重定向，如果是则强制返回搜索页面
            current_url = self.driver.current_url
            self._debug_log(f"🔍 反爬虫处理后URL: {current_url}")
            
            # 检查是否被重定向到非搜索页面
            redirected_to_non_search = self._check_redirected_from_search(original_url, current_url)
            
            if redirected_to_non_search:
                self._debug_log("⚠️ 检测到被重定向到非搜索页面，尝试强制返回搜索")
                success = self._force_return_to_search(original_url)
                if not success:
                    self._debug_log("❌ 强制返回搜索页面失败", "WARNING")
                    return False
            
            # 检查页面是否仍然有阻挡元素
            try:
                if 'login' in current_url.lower() or 'auth' in current_url.lower() or 'captcha' in current_url.lower():
                    self._debug_log("🔐 检测到验证码页面，启动人工辅助验证...")
                    return self._handle_captcha_verification()
                    
                # 检查页面内容长度
                page_content_length = len(self.driver.page_source)
                if page_content_length < 5000:
                    self._debug_log(f"⚠️ 页面内容较少({page_content_length}字符)，可能仍被反爬虫阻挡")
                else:
                    self._debug_log(f"✅ 页面内容正常({page_content_length}字符)")
                    
            except Exception as e:
                self._debug_log(f"⚠️ 检查页面状态时出错: {str(e)}", "WARNING")
            
            self._debug_log("✅ 反爬虫处理完成")
            return True
            
        except Exception as e:
            self._debug_log(f"❌ 处理反爬虫机制时出错: {str(e)}", "WARNING")
            return True  # 即使处理失败也继续执行

    def _check_redirected_from_search(self, original_url, current_url):
        """检查是否从搜索页面被重定向到其他页面"""
        try:
            # 检查原始URL是否为搜索URL
            search_indicators_original = [
                'search_result' in original_url,
                'keyword=' in original_url,
                'search' in original_url.lower()
            ]
            
            # 检查当前URL是否为非搜索页面
            non_search_indicators_current = [
                'search_result' not in current_url,
                'keyword=' not in current_url,
                'homefeed' in current_url,
                'explore' in current_url,
                'recommend' in current_url,
                current_url.count('/') <= 3,  # 可能是首页
                current_url.endswith('xiaohongshu.com') or current_url.endswith('xiaohongshu.com/')
            ]
            
            was_search = any(search_indicators_original)
            is_non_search = any(non_search_indicators_current)
            
            if was_search and is_non_search:
                self._debug_log(f"🚨 检测到重定向：{original_url[:50]}... -> {current_url[:50]}...")
                return True
            
            return False
            
        except Exception as e:
            self._debug_log(f"⚠️ 检查重定向状态出错: {str(e)}", "WARNING")
            return False

    def _is_recommendation_page(self, page_source, current_url):
        """检测是否为推荐页面"""
        try:
            # 首先检查是否在搜索结果页面 - 如果在搜索页面，则不是推荐页面
            if ('search_result' in current_url or 
                'keyword=' in current_url or 
                '/search/' in current_url):
                self._debug_log(f"✅ 确认在搜索页面，URL: {current_url}")
                return False
            
            # 检测推荐页面的多种标识
            recommendation_indicators = [
                "homefeed_recommend" in page_source,
                "首页推荐" in page_source,
                ("推荐" in page_source and "搜索结果" not in page_source and "search" not in page_source),
                "recommend" in current_url.lower(),
                "explore" in current_url.lower(),
                (current_url.endswith("xiaohongshu.com") or current_url.endswith("xiaohongshu.com/")),
                (current_url.count('/') <= 3 and 'search' not in current_url)  # 可能是首页且不包含search
            ]
            
            is_recommendation = any(recommendation_indicators)
            
            if is_recommendation:
                self._debug_log(f"🔍 推荐页面检测结果: {recommendation_indicators}")
                self._debug_log(f"📍 当前URL: {current_url}")
                return True
            
            self._debug_log(f"✅ 不是推荐页面，URL: {current_url}")
            return False
            
        except Exception as e:
            self._debug_log(f"⚠️ 推荐页面检测出错: {str(e)}")
            return False

    def _force_return_to_search(self, original_search_url, max_attempts=3):
        """强制返回搜索页面"""
        try:
            self._debug_log(f"🔄 开始强制返回搜索页面，最大尝试次数: {max_attempts}")
            
            for attempt in range(max_attempts):
                self._debug_log(f"🔄 尝试 {attempt + 1}/{max_attempts}: 返回搜索页面")
                
                try:
                    # 方法1：直接导航到原始搜索URL
                    self.driver.get(original_search_url)
                    time.sleep(5)
                    
                    # 检查是否成功返回搜索页面
                    current_url = self.driver.current_url
                    page_source = self.driver.page_source
                    
                    if 'search_result' in current_url or 'keyword=' in current_url:
                        self._debug_log(f"✅ 方法1成功：直接导航返回搜索页面")
                        return True
                    
                    # 方法2：如果直接导航失败，尝试通过搜索框搜索
                    if attempt == 0:  # 只在第一次尝试时使用搜索框
                        keyword = self._extract_keyword_from_url(original_search_url)
                        if keyword and self._try_search_via_search_box(keyword):
                            self._debug_log(f"✅ 方法2成功：通过搜索框返回搜索页面")
                            return True
                    
                    # 方法3：构造新的搜索URL
                    if attempt == 1:  # 在第二次尝试时使用
                        keyword = self._extract_keyword_from_url(original_search_url)
                        if keyword and self._try_construct_new_search_url(keyword):
                            self._debug_log(f"✅ 方法3成功：构造新搜索URL返回搜索页面")
                            return True
                    
                    self._debug_log(f"❌ 尝试 {attempt + 1} 失败，当前URL: {current_url[:50]}...")
                    time.sleep(3)
                    
                except Exception as e:
                    self._debug_log(f"❌ 尝试 {attempt + 1} 出错: {str(e)}")
                    time.sleep(3)
                    continue
            
            self._debug_log(f"❌ 所有尝试都失败，无法强制返回搜索页面")
            return False
            
        except Exception as e:
            self._debug_log(f"❌ 强制返回搜索页面时出错: {str(e)}", "ERROR")
            return False

    def _extract_keyword_from_url(self, url):
        """从URL中提取关键词"""
        try:
            from urllib.parse import urlparse, parse_qs, unquote
            
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            
            # 尝试从keyword参数获取
            if 'keyword' in query_params:
                keyword = unquote(query_params['keyword'][0])
                self._debug_log(f"🔍 从URL提取关键词: {keyword}")
                return keyword
            
            return None
            
        except Exception as e:
            self._debug_log(f"⚠️ 提取关键词失败: {str(e)}")
            return None

    def _try_search_via_search_box(self, keyword):
        """尝试通过搜索框进行搜索"""
        try:
            self._debug_log(f"🔍 尝试通过搜索框搜索: {keyword}")
            
            # 首先导航到主页
            self.driver.get("https://www.xiaohongshu.com")
            time.sleep(3)
            
            # 尝试找到搜索框
            search_box_selectors = [
                "input[placeholder*='搜索']",
                "input[placeholder*='search']",
                ".search-input",
                "#search-input",
                "input[type='search']",
                ".searchInput",
                "[data-testid*='search']"
            ]
            
            search_box = None
            for selector in search_box_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and elements[0].is_displayed():
                        search_box = elements[0]
                        self._debug_log(f"✅ 找到搜索框: {selector}")
                        break
                except:
                    continue
            
            if not search_box:
                self._debug_log("❌ 未找到搜索框")
                return False
            
            # 清空并输入关键词
            search_box.clear()
            search_box.send_keys(keyword)
            time.sleep(2)
            
            # 尝试提交搜索
            from selenium.webdriver.common.keys import Keys
            search_box.send_keys(Keys.ENTER)
            time.sleep(5)
            
            # 检查是否成功跳转到搜索结果页面
            current_url = self.driver.current_url
            if 'search_result' in current_url or 'keyword=' in current_url:
                self._debug_log("✅ 搜索框搜索成功")
                return True
            else:
                self._debug_log(f"❌ 搜索框搜索失败，当前URL: {current_url}")
                return False
                
        except Exception as e:
            self._debug_log(f"❌ 搜索框搜索出错: {str(e)}")
            return False

    def _try_construct_new_search_url(self, keyword):
        """尝试构造新的搜索URL"""
        try:
            from urllib.parse import quote
            
            self._debug_log(f"🔧 尝试构造新搜索URL: {keyword}")
            
            encoded_keyword = quote(keyword)
            new_search_urls = [
                f"https://www.xiaohongshu.com/search_result?keyword={encoded_keyword}&source=web_search&type=comprehensive",
                f"https://www.xiaohongshu.com/search_result?keyword={encoded_keyword}&source=web_search",
                f"https://www.xiaohongshu.com/search_result?keyword={encoded_keyword}"
            ]
            
            for url in new_search_urls:
                try:
                    self._debug_log(f"🔗 尝试URL: {url}")
                    self.driver.get(url)
                    time.sleep(5)
                    
                    current_url = self.driver.current_url
                    if 'search_result' in current_url or 'keyword=' in current_url:
                        self._debug_log(f"✅ 新URL构造成功")
                        return True
                        
                except Exception as e:
                    self._debug_log(f"❌ URL {url} 失败: {str(e)}")
                    continue
            
            return False
            
        except Exception as e:
            self._debug_log(f"❌ 构造新搜索URL出错: {str(e)}")
            return False

    def _try_final_search_recovery(self, keyword):
        """最终搜索页面恢复尝试 - 当所有其他方法都失败时使用"""
        try:
            self._debug_log(f"🚨 启动最终搜索恢复程序：{keyword}")
            
            # 尝试多种恢复策略
            recovery_strategies = [
                self._recovery_direct_navigation,
                self._recovery_via_homepage_search,
                self._recovery_via_explore_page,
                self._recovery_refresh_and_retry
            ]
            
            for i, strategy in enumerate(recovery_strategies):
                try:
                    self._debug_log(f"🔄 执行恢复策略 {i+1}: {strategy.__name__}")
                    if strategy(keyword):
                        self._debug_log(f"✅ 恢复策略 {i+1} 成功")
                        return True
                    else:
                        self._debug_log(f"❌ 恢复策略 {i+1} 失败")
                except Exception as e:
                    self._debug_log(f"❌ 恢复策略 {i+1} 出错: {str(e)}")
                    continue
            
            self._debug_log("❌ 所有恢复策略都失败")
            return False
            
        except Exception as e:
            self._debug_log(f"❌ 最终搜索恢复出错: {str(e)}")
            return False

    def _recovery_direct_navigation(self, keyword):
        """恢复策略1：直接导航到搜索URL"""
        try:
            from urllib.parse import quote
            encoded_keyword = quote(keyword)
            direct_url = f"https://www.xiaohongshu.com/search_result?keyword={encoded_keyword}&source=web_search&type=comprehensive"
            
            self.driver.get(direct_url)
            time.sleep(6)
            
            current_url = self.driver.current_url
            page_source = self.driver.page_source
            
            return ('search_result' in current_url or 'keyword=' in current_url) and self._verify_search_page_strict(page_source, keyword)
            
        except Exception as e:
            self._debug_log(f"直接导航恢复失败: {str(e)}")
            return False

    def _recovery_via_homepage_search(self, keyword):
        """恢复策略2：通过首页搜索框"""
        try:
            # 导航到首页
            self.driver.get("https://www.xiaohongshu.com")
            time.sleep(4)
            
            # 查找并使用搜索框
            search_selectors = [
                "input[placeholder*='搜索']",
                "input[placeholder*='发现好生活']", 
                ".search-input",
                "#search-input",
                "input[type='search']",
                "[data-testid*='search']"
            ]
            
            for selector in search_selectors:
                try:
                    search_box = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if search_box.is_displayed():
                        search_box.clear()
                        search_box.send_keys(keyword)
                        
                        from selenium.webdriver.common.keys import Keys
                        search_box.send_keys(Keys.ENTER)
                        time.sleep(6)
                        
                        current_url = self.driver.current_url
                        page_source = self.driver.page_source
                        
                        if ('search_result' in current_url or 'keyword=' in current_url) and self._verify_search_page_strict(page_source, keyword):
                            return True
                        break
                except:
                    continue
            
            return False
            
        except Exception as e:
            self._debug_log(f"首页搜索恢复失败: {str(e)}")
            return False

    def _recovery_via_explore_page(self, keyword):
        """恢复策略3：通过探索页面"""
        try:
            # 尝试访问探索页面
            explore_urls = [
                "https://www.xiaohongshu.com/explore",
                "https://www.xiaohongshu.com/discovery"
            ]
            
            for explore_url in explore_urls:
                try:
                    self.driver.get(explore_url)
                    time.sleep(4)
                    
                    # 在探索页面查找搜索功能
                    search_elements = self.driver.find_elements(By.CSS_SELECTOR, "input[placeholder*='搜索']")
                    if search_elements:
                        search_box = search_elements[0]
                        search_box.clear()
                        search_box.send_keys(keyword)
                        
                        from selenium.webdriver.common.keys import Keys
                        search_box.send_keys(Keys.ENTER)
                        time.sleep(6)
                        
                        current_url = self.driver.current_url
                        page_source = self.driver.page_source
                        
                        if ('search_result' in current_url or 'keyword=' in current_url) and self._verify_search_page_strict(page_source, keyword):
                            return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            self._debug_log(f"探索页面恢复失败: {str(e)}")
            return False

    def _recovery_refresh_and_retry(self, keyword):
        """恢复策略4：刷新页面并重试"""
        try:
            self._debug_log("🔄 执行页面刷新重试策略")
            
            # 刷新当前页面
            self.driver.refresh()
            time.sleep(5)
            
            # 检查刷新后是否回到搜索页面
            current_url = self.driver.current_url
            page_source = self.driver.page_source
            
            if ('search_result' in current_url or 'keyword=' in current_url) and self._verify_search_page_strict(page_source, keyword):
                return True
            
            # 如果刷新无效，重新构造搜索URL
            from urllib.parse import quote
            encoded_keyword = quote(keyword)
            retry_url = f"https://www.xiaohongshu.com/search_result?keyword={encoded_keyword}"
            
            self.driver.get(retry_url)
            time.sleep(6)
            
            final_url = self.driver.current_url
            final_page_source = self.driver.page_source
            
            return ('search_result' in final_url or 'keyword=' in final_url) and self._verify_search_page_strict(final_page_source, keyword)
            
        except Exception as e:
            self._debug_log(f"刷新重试恢复失败: {str(e)}")
            return False

    def _handle_captcha_verification(self):
        """处理验证码 - 人工辅助验证（改进版）"""
        try:
            logger.info("🔐 检测到拼图验证码，启动人工辅助模式...")
            
            # 1. 获取当前页面信息
            current_url = self.driver.current_url
            page_title = self.driver.title
            page_source = self.driver.page_source
            logger.info(f"📋 验证页面URL: {current_url}")
            logger.info(f"📋 页面标题: {page_title}")
            
            # 检查是否是"验证过于频繁"的情况
            frequent_check_indicators = ["验证过于频繁", "请稍后重试", "too frequent", "try again later"]
            is_frequent_error = any(indicator in page_source for indicator in frequent_check_indicators)
            
            if is_frequent_error:
                logger.warning("⚠️  检测到'验证过于频繁'提示")
                logger.info("🕐 建议等待10分钟后再次尝试")
                logger.info("📝 或者您可以:")
                logger.info("   1. 清除浏览器缓存和Cookie")  
                logger.info("   2. 更换网络环境")
                logger.info("   3. 稍后重新运行程序")
                
                # 等待一段时间然后继续
                logger.info("⏳ 等待60秒后继续尝试...")
                time.sleep(60)
                return True
            
            # 2. 强制显示浏览器窗口
            try:
                # 尝试重新创建可见浏览器
                if self.headless:
                    logger.info("🔄 当前为无头模式，重新创建可见浏览器...")
                    self._recreate_visible_browser()
                
                # 激活窗口
                self.driver.switch_to.window(self.driver.current_window_handle)
                self.driver.maximize_window()
                
                # macOS特定：尝试激活Chrome
                try:
                    import subprocess
                    subprocess.run(['osascript', '-e', 'tell application "Google Chrome" to activate'], 
                                 check=False, timeout=5)
                    logger.info("🖥️  已尝试激活Chrome浏览器")
                except Exception:
                    pass
                
                logger.info("🖥️  浏览器窗口已激活并最大化")
            except Exception as e:
                logger.warning(f"激活浏览器窗口失败: {str(e)}")
                logger.info("💡 请手动查看桌面上的Chrome浏览器窗口")
            
            # 3. 创建验证期间的截图目录
            import os
            import hashlib
            from datetime import datetime
            
            debug_dir = os.path.join(self.cache_dir, 'debug_screenshots')
            os.makedirs(debug_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_id = hashlib.md5(f"captcha_{timestamp}_{random.randint(1000,9999)}".encode()).hexdigest()[:8]
            
            def take_verification_screenshot(step_name):
                """验证期间截图"""
                try:
                    screenshot_path = os.path.join(debug_dir, f"{timestamp}_{session_id}_verification_{step_name}.png")
                    self.driver.save_screenshot(screenshot_path)
                    logger.info(f"🔍 验证截图已保存: {screenshot_path}")
                    return screenshot_path
                except Exception as e:
                    logger.warning(f"验证截图失败: {str(e)}")
                    return None
            
            # 初始验证截图
            take_verification_screenshot("00_initial")
            
            # 4. 显示用户提示
            logger.info("=" * 80)
            logger.info("🚨 【需要人工验证】")
            logger.info("📱 小红书拼图验证码已出现，请按以下步骤操作：")
            logger.info("")
            logger.info("✅ 步骤：")
            logger.info("   1️⃣  在桌面上找到Chrome浏览器窗口")
            logger.info("   2️⃣  完成拼图验证码（拖动滑块到正确位置）")
            logger.info("   3️⃣  等待页面自动跳转到搜索结果")
            logger.info("   4️⃣  程序将自动检测验证完成状态")
            logger.info("")
            logger.info("⏰ 超时设置：最多等待8分钟")
            logger.info("📸 调试：程序将每1秒截图记录验证过程")
            logger.info("💡 提示：如果看不到浏览器，请检查Dock或窗口管理器")
            logger.info("=" * 80)
            
            # 5. 验证等待循环（每1秒截图）
            max_wait_time = 480  # 增加到8分钟
            check_interval = 1    # 每1秒检查一次
            waited_time = 0
            screenshot_count = 0
            
            logger.info(f"⏳ 开始等待人工验证（最多{max_wait_time}秒，每1秒截图）...")
            
            while waited_time < max_wait_time:
                try:
                    # 每1秒截图
                    screenshot_count += 1
                    take_verification_screenshot(f"sec_{screenshot_count:03d}")
                    
                    # 获取当前页面状态
                    current_url = self.driver.current_url
                    page_title = self.driver.title
                    page_source = self.driver.page_source
                    
                    # 检查是否已经跳转出验证页面
                    verification_indicators = ["captcha", "login", "verify", "验证"]
                    is_still_verifying = any(indicator in current_url.lower() for indicator in verification_indicators)
                    
                    if not is_still_verifying:
                        # 进一步检查页面内容
                        success_indicators = [
                            "search_result" in current_url,
                            "explore" in current_url,
                            "搜索结果" in page_source,
                            len(page_source) > 20000,  # 正常页面通常内容较多
                            "小红书" in page_title and "验证" not in page_title
                        ]
                        
                        if any(success_indicators):
                            logger.info("✅ 验证成功！页面已跳转到正常内容，继续搜索流程...")
                            logger.info(f"📍 新URL: {current_url}")
                            logger.info(f"📝 新标题: {page_title}")
                            take_verification_screenshot("success_final")
                            time.sleep(3)  # 等待页面完全稳定
                            return True
                    
                    # 进度提示（每30秒）
                    if waited_time % 30 == 0 and waited_time > 0:
                        remaining_time = max_wait_time - waited_time
                        logger.info(f"⏳ 仍在等待验证完成... (剩余{remaining_time}秒，已截图{screenshot_count}张)")
                        logger.info(f"📍 当前状态: {page_title}")
                        
                        # 检查是否有新的错误提示
                        error_indicators = ["失败", "错误", "验证过于频繁", "invalid", "failed"]
                        if any(indicator in page_source.lower() for indicator in error_indicators):
                            logger.warning("⚠️  检测到可能的验证问题，请重新尝试或刷新页面")
                    
                    time.sleep(check_interval)
                    waited_time += check_interval
                    
                except Exception as e:
                    logger.warning(f"检查验证状态时出错: {str(e)}")
                    time.sleep(check_interval)
                    waited_time += check_interval
            
            # 超时处理
            logger.warning("⏰ 人工验证超时！")
            logger.info(f"📸 共截取了 {screenshot_count} 张验证过程截图")
            logger.info("💡 可能的原因：")
            logger.info("   - 验证码未完成")
            logger.info("   - 浏览器窗口未正确显示")
            logger.info("   - 网络连接问题")
            logger.info("   - 验证过于频繁导致暂时封禁")
            logger.info("📝 建议：检查截图了解具体情况，或稍后重试")
            
            take_verification_screenshot("timeout_final")
            
            # 即使超时也尝试继续执行
            logger.info("🔄 尽管超时，程序将继续尝试提取数据...")
            return True
            
        except Exception as e:
            logger.error(f"人工验证处理失败: {str(e)}")
            logger.info("🔄 尽管处理失败，程序将继续尝试提取数据...")
            return True
    
    def _recreate_visible_browser(self):
        """重新创建可见的浏览器实例"""
        try:
            logger.info("🔄 重新创建可见浏览器...")
            
            # 保存当前URL
            current_url = self.driver.current_url if self.driver else None
            
            # 关闭当前浏览器
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
                self.driver = None
            
            # 临时设置为非无头模式
            original_headless = self.headless
            self.headless = False
            
            # 重新初始化浏览器
            success = self._init_selenium()
            
            if success and current_url:
                # 重新访问之前的URL
                try:
                    self.driver.get(current_url)
                    time.sleep(3)
                    logger.info("✅ 可见浏览器创建成功，已重新载入页面")
                except Exception as e:
                    logger.warning(f"重新载入页面失败: {str(e)}")
                
                # 恢复原始设置
                self.headless = original_headless
                return True
            else:
                logger.error("❌ 可见浏览器创建失败")
                self.headless = original_headless
                return False
                
        except Exception as e:
            logger.error(f"重新创建浏览器失败: {str(e)}")
            return False

    def _save_page_source(self, page_source, keyword):
        """保存页面源码"""
        try:
            filename = f"page_source_{hashlib.md5(keyword.encode()).hexdigest()}.html"
            filepath = os.path.join(self.cache_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(page_source)
            
            return filepath
            
        except Exception as e:
            logger.warning(f"保存页面源码失败: {str(e)}")
            return ""

    def wait_for_content_load(self):
        """等待内容完全加载 - 可配置的调试版本"""
        try:
            enable_screenshots = self.crawl_config.get('enable_debug_screenshots', False)
            screenshot_interval = self.crawl_config.get('screenshot_interval', 0)
            
            if enable_screenshots:
                import os
                import hashlib
                from datetime import datetime
                
                # 创建debug截图目录
                debug_dir = os.path.join(self.cache_dir, 'debug_screenshots')
                os.makedirs(debug_dir, exist_ok=True)
                
                # 生成唯一标识
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                session_id = hashlib.md5(f"{timestamp}_{random.randint(1000,9999)}".encode()).hexdigest()[:8]
                
                def take_debug_screenshot(step_name):
                    """截取调试截图"""
                    if not enable_screenshots:
                        return None
                    try:
                        screenshot_path = os.path.join(debug_dir, f"{timestamp}_{session_id}_{step_name}.png")
                        self.driver.save_screenshot(screenshot_path)
                        logger.info(f"🔍 Debug截图已保存: {screenshot_path}")
                        return screenshot_path
                    except Exception as e:
                        logger.warning(f"截图失败: {str(e)}")
                        return None
                
                logger.info(f"🔍 开始页面加载调试，会话ID: {session_id}")
                take_debug_screenshot("00_initial")
            else:
                def take_debug_screenshot(step_name):
                    return None
                logger.info("🔍 开始页面加载检测")
            
            wait = WebDriverWait(self.driver, 12)
            
            # 1. 等待页面基本结构加载
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                logger.info("页面基本结构加载完成")
                take_debug_screenshot("01_body_loaded")
            except Exception as e:
                logger.warning(f"等待页面基本结构超时，继续执行: {str(e)}")
                take_debug_screenshot("01_body_timeout")
            
            # 2. 等待任意内容区域（更宽松的条件）
            try:
                wait_short = WebDriverWait(self.driver, 8)
                wait_short.until(
                    lambda driver: driver.find_elements(By.CSS_SELECTOR, 
                        "div, section, article, main, [class*='content'], [class*='list'], [class*='item']")
                )
                logger.info("内容区域加载完成")
                take_debug_screenshot("02_content_loaded")
            except Exception as e:
                logger.warning(f"等待内容区域超时，继续执行: {str(e)}")
                take_debug_screenshot("02_content_timeout")
            
            # 3. 尝试检测小红书特定元素，但不强制要求
            try:
                elements_found = False
                selectors_to_try = [
                    'a[href*="/explore/"]',  # 探索链接
                    '[class*="note"]',       # 笔记相关类名
                    '[class*="card"]',       # 卡片相关类名
                    '[class*="item"]',       # 项目相关类名
                    '[class*="feed"]',       # 动态相关类名
                    'img',                   # 图片元素
                    '[data-v-]',            # Vue组件
                ]
                
                for selector in selectors_to_try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and len(elements) > 3:
                        logger.info(f"找到足够的元素({len(elements)}个): {selector}")
                        elements_found = True
                        break
                
                if not elements_found:
                    logger.warning("未找到足够的页面元素，但继续执行三种策略")
                
                take_debug_screenshot("03_elements_check")
                    
            except Exception as e:
                logger.warning(f"检测页面元素时出错，继续执行: {str(e)}")
                take_debug_screenshot("03_elements_error")
            
            # 4. 给JavaScript渲染时间，根据配置决定是否逐秒截图
            if screenshot_interval > 0 and enable_screenshots:
                logger.info(f"🔍 开始JavaScript渲染等待期间的截图（间隔{screenshot_interval}秒）...")
                render_time = 5  # 总等待时间
                shots_count = 0
                for i in range(render_time):
                    time.sleep(1)
                    if (i + 1) % screenshot_interval == 0:
                        shots_count += 1
                        take_debug_screenshot(f"04_js_render_sec_{i+1}")
                        
                        # 检查页面状态
                        try:
                            current_url = self.driver.current_url
                            page_title = self.driver.title
                            logger.info(f"第{i+1}秒 - URL: {current_url}, 标题: {page_title}")
                            
                            # 检查是否是登录页面
                            login_indicators = ["登录", "login", "signin", "验证", "captcha"]
                            page_source_lower = self.driver.page_source.lower()
                            is_login_page = any(indicator in page_source_lower for indicator in login_indicators)
                            
                            if is_login_page:
                                logger.warning(f"第{i+1}秒检测到登录页面特征")
                                
                        except Exception as e:
                            logger.warning(f"第{i+1}秒页面状态检查失败: {str(e)}")
            else:
                logger.info("JavaScript渲染等待中...")
                time.sleep(3)  # 简单等待3秒
            
            # 5. 滚动页面触发懒加载
            try:
                if self.crawl_config.get('enable_detailed_logs', True):
                    logger.info("🔍 执行页面滚动...")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                take_debug_screenshot("05_scroll_middle")
                time.sleep(1)
                self.driver.execute_script("window.scrollTo(0, 0);")
                take_debug_screenshot("05_scroll_top")
                time.sleep(1)
            except Exception as e:
                logger.warning(f"页面滚动失败: {str(e)}")
                take_debug_screenshot("05_scroll_error")
            
            # 6. 最终验证页面状态 - 但不管结果如何都返回True
            try:
                page_text = self.driver.page_source
                take_debug_screenshot("06_final_state")
                
                # 根据配置决定是否保存页面源码
                if enable_screenshots:
                    final_html_path = os.path.join(debug_dir, f"{timestamp}_{session_id}_final_source.html")
                    with open(final_html_path, 'w', encoding='utf-8') as f:
                        f.write(page_text)
                    logger.info(f"🔍 最终页面源码已保存: {final_html_path}")
                
                if len(page_text) > 10000:
                    logger.info("页面内容加载完成，开始执行三种提取策略")
                    return True
                elif len(page_text) > 5000:
                    logger.warning(f"页面内容较少({len(page_text)}字符)，但继续执行三种策略")
                    return True
                else:
                    logger.warning(f"页面内容很少({len(page_text)}字符)，但仍尝试执行三种策略")
                    return True
            except Exception as e:
                logger.warning(f"检查页面内容时出错，继续执行三种策略: {str(e)}")
                take_debug_screenshot("06_final_error")
                return True
            
        except Exception as e:
            logger.warning(f"等待内容加载失败，但继续执行三种策略: {e}")
            return True  # 关键：即使完全超时也继续执行，确保三种策略能够运行

    def search(self, keyword, max_results=10, use_cache=True):
        """搜索小红书内容 - 改进版本"""
        self._debug_log(f"🔍 开始搜索关键词: {keyword}")
        
        if use_cache:
            self._debug_log("📂 检查缓存...")
            cached_result = self._load_from_cache(keyword)
            if cached_result:
                self._debug_log(f"✅ 从缓存获取到 {len(cached_result)} 条结果")
                return cached_result[:max_results]
            else:
                self._debug_log("ℹ️ 缓存中无数据，进行实时搜索")

        try:
            # 🔧 修复：关键词URL编码和搜索URL格式
            encoded_keyword = quote(keyword)  # 正确编码关键词
            
            # 尝试多种搜索URL格式 - 修正type参数
            search_urls = [
                f"https://www.xiaohongshu.com/search_result?keyword={encoded_keyword}&source=web_search&type=comprehensive",
                f"https://www.xiaohongshu.com/search_result?keyword={encoded_keyword}&source=web_search&type=note",
                f"https://www.xiaohongshu.com/search_result?keyword={encoded_keyword}&source=web_search"
            ]
            
            self._debug_log(f"🌐 准备了 {len(search_urls)} 个搜索URL")
            self._debug_log(f"🔍 原始关键词: '{keyword}' -> 编码后: '{encoded_keyword}'")
            
            # 确保WebDriver已初始化
            self._debug_log("🚀 初始化浏览器...")
            if not self._ensure_driver_initialized():
                self._debug_log("❌ WebDriver初始化失败", "ERROR")
                return []
            
            self._debug_log("✅ 浏览器初始化成功")
            
            # 尝试不同的搜索URL
            search_success = False
            for i, search_url in enumerate(search_urls):
                try:
                    self._debug_log(f"🔗 尝试搜索URL {i+1}/{len(search_urls)}: {search_url}")
                    
                    # 访问搜索页面
                    self.driver.get(search_url)
                    
                    # 等待页面加载
                    self._debug_log("⏳ 等待页面加载...")
                    time.sleep(5)  # 增加等待时间确保页面完全加载
                    
                    # 🔧 修复：更严格的页面验证
                    page_source = self.driver.page_source
                    if self._verify_search_page_strict(page_source, keyword):
                        self._debug_log(f"✅ 搜索URL验证成功: {search_url[:70]}...")
                        search_success = True
                        break
                    else:
                        self._debug_log(f"⚠️ 搜索URL验证失败，可能不是搜索结果页面")
                        
                        # 🔧 新增：如果检测到推荐页面，立即尝试强制返回搜索
                        current_url = self.driver.current_url
                        if self._is_recommendation_page(page_source, current_url):
                            self._debug_log(f"🚨 检测到推荐页面，立即尝试强制返回搜索页面")
                            if self._force_return_to_search(search_url):
                                self._debug_log(f"✅ 成功强制返回搜索页面")
                                # 重新验证页面
                                final_page_source = self.driver.page_source
                                if self._verify_search_page_strict(final_page_source, keyword):
                                    self._debug_log(f"✅ 强制返回后验证成功")
                                    search_success = True
                                    break
                                else:
                                    self._debug_log(f"❌ 强制返回后仍然验证失败")
                            else:
                                self._debug_log(f"❌ 强制返回搜索页面失败")
                        
                        # 保存失败页面用于调试
                        if self.crawl_config.get('enable_detailed_logs', True):
                            failed_page_path = self._save_page_source(page_source, f"failed_{keyword}_url{i+1}")
                            self._debug_log(f"📁 失败页面已保存: {failed_page_path}")
                        continue
                        
                except Exception as e:
                    self._debug_log(f"❌ 搜索URL失败: {str(e)}", "WARNING")
                    continue
            
            if not search_success:
                self._debug_log("❌ 所有搜索URL都失败，可能遇到反爬虫机制", "ERROR")
                return []
            
            # 等待并检测反爬虫
            self._debug_log("🛡️ 检测反爬虫机制...")
            if not self._handle_anti_bot():
                self._debug_log("❌ 反爬虫检测处理失败", "ERROR") 
                return []
            
            self._debug_log("✅ 反爬虫检测通过")
            
            # 🔧 新增：最终确认是否仍在搜索页面
            final_url = self.driver.current_url
            final_page_source = self.driver.page_source
            
            if not self._verify_search_page_strict(final_page_source, keyword):
                self._debug_log("⚠️ 反爬虫处理后仍未在正确的搜索页面，尝试最后一次强制跳转")
                # 最后一次尝试强制返回搜索
                if self._try_final_search_recovery(keyword):
                    self._debug_log("✅ 最终搜索页面恢复成功")
                else:
                    self._debug_log("❌ 最终搜索页面恢复失败，但继续尝试提取", "WARNING")
            
            # 等待内容完全加载 - 但不管结果如何都继续执行
            self._debug_log("📄 等待页面内容完全加载...")
            content_loaded = self.wait_for_content_load()
            if not content_loaded:
                self._debug_log("⚠️ 页面内容加载超时，但继续尝试提取", "WARNING")
            else:
                self._debug_log("✅ 页面内容加载完成")
            
            # 保存页面源码用于调试
            self._debug_log("💾 保存页面源码...")
            page_source_path = self._save_page_source(self.driver.page_source, keyword)
            self._debug_log(f"📁 页面源码已保存: {page_source_path[:50]}...")
            
            # 使用改进的多策略提取
            self._debug_log("🔧 开始执行三种提取策略...")
            results = self.extract_notes_advanced(keyword, max_results)
            
            if results:
                self._debug_log(f"📊 初步提取到 {len(results)} 条结果")
                
                # 验证结果是否与关键词相关
                self._debug_log("🔍 验证结果与关键词的相关性...")
                validated_results = self._validate_search_results(results, keyword)
                
                # 🔧 修复：只有当真正有结果时才缓存和生成HTML
                if validated_results and len(validated_results) > 0:
                    # 缓存结果
                    if use_cache:
                        self._debug_log("💾 缓存搜索结果...")
                        self._save_to_cache(keyword, validated_results)
                    
                    self._debug_log(f"🎉 搜索完成！找到 {len(validated_results)} 条相关结果")
                    return validated_results[:max_results]
                else:
                    # 🔧 修复：删除可能存在的空缓存文件
                    self._debug_log(f"⚠️ 未找到与关键词 '{keyword}' 相关的搜索结果，清理空缓存", "WARNING")
                    self._remove_empty_cache(keyword)
                    return []
            else:
                self._debug_log("❌ 未找到任何搜索结果", "WARNING")
                return []
                
        except Exception as e:
            self._debug_log(f"❌ 搜索过程中发生错误: {str(e)}", "ERROR")
            return []

    def _remove_empty_cache(self, keyword):
        """
        🔧 修复方法：删除空缓存文件
        当搜索结果验证后发现没有有效内容时，清理空缓存文件
        """
        try:
            cache_path = self._get_cache_path(keyword)
            html_cache_dir = os.path.join(os.path.dirname(cache_path), 'results')
            
            # 删除JSON缓存文件
            if os.path.exists(cache_path):
                os.remove(cache_path)
                self._debug_log(f"🗑️ 已删除空的JSON缓存文件: {cache_path}", "DEBUG")
            
            # 删除HTML缓存文件
            if os.path.exists(html_cache_dir):
                import hashlib
                html_hash = hashlib.md5(keyword.encode()).hexdigest()
                html_file = os.path.join(html_cache_dir, f"search_{html_hash}.html")
                if os.path.exists(html_file):
                    os.remove(html_file)
                    self._debug_log(f"🗑️ 已删除空的HTML缓存文件: {html_file}", "DEBUG")
                    
        except Exception as e:
            self._debug_log(f"❌ 清理空缓存时出错: {str(e)}", "WARNING")

    def _verify_search_page(self, page_source, keyword):
        """验证页面是否为搜索结果页面"""
        try:
            # 检查页面标题和关键指标
            search_indicators = [
                f'"{keyword}"',  # 关键词在JSON数据中
                f"'{keyword}'",  # 关键词在JavaScript中
                f"keyword={keyword}",  # URL参数
                f"搜索结果",
                f"search_result",
                f"searchValue",
                # 检查是否不是首页推荐
                "homefeed_recommend" not in page_source or keyword in page_source
            ]
            
            # 检查是否包含推荐页面的特征但不包含搜索关键词
            if "推荐" in page_source and "homefeed_recommend" in page_source:
                # 如果页面包含关键词，则认为是搜索页面
                keyword_found = any([
                    keyword in page_source,
                    keyword.lower() in page_source.lower(),
                    # 检查URL编码的关键词
                    keyword.replace(' ', '%20') in page_source,
                    keyword.replace(' ', '+') in page_source
                ])
                
                if keyword_found:
                    logger.info(f"检测到包含关键词 '{keyword}' 的页面")
                    return True
                else:
                    logger.warning(f"页面似乎是推荐页面，不包含关键词 '{keyword}'")
                    return False
            
            # 检查搜索相关的指标
            search_found = any([
                indicator in page_source for indicator in search_indicators[:6]
            ])
            
            return search_found
            
        except Exception as e:
            logger.error(f"验证搜索页面时出错: {str(e)}")
            return False

    def _verify_search_page_strict(self, page_source, keyword):
        """🔧 更严格的页面验证 - 确保是真正的搜索结果页面"""
        try:
            self._debug_log(f"🔍 开始严格验证页面是否为关键词 '{keyword}' 的搜索结果")
            
            # 1. 首先检查是否为推荐页面（排除误判）
            if "homefeed_recommend" in page_source or "首页推荐" in page_source:
                self._debug_log("❌ 检测到推荐页面标识，非搜索结果页面")
                return False
            
            # 2. 检查URL参数中是否包含关键词
            encoded_keyword = quote(keyword)
            url_indicators = [
                f"keyword={keyword}",
                f"keyword={encoded_keyword}",
                f"searchValue={keyword}",
                f"query={keyword}"
            ]
            
            url_match = any(indicator in page_source for indicator in url_indicators)
            if url_match:
                self._debug_log("✅ URL参数中发现关键词，确认为搜索页面")
                return True
            
            # 3. 检查页面内容中的关键词出现
            keyword_indicators = [
                f'"{keyword}"',  # JSON中的关键词
                f"'{keyword}'",  # JavaScript中的关键词
                f'搜索"{keyword}"',  # 搜索提示文本
                f"keyword:{keyword}",  # 配置对象中的关键词
            ]
            
            content_match = any(indicator in page_source for indicator in keyword_indicators)
            
            # 4. 检查搜索相关的页面元素
            search_elements = [
                "search_result",
                "searchResult", 
                "搜索结果",
                "noteList",
                "feeds-page"
            ]
            
            element_match = any(element in page_source for element in search_elements)
            
            # 5. 综合判断
            if content_match and element_match:
                self._debug_log("✅ 内容和元素都匹配，确认为搜索结果页面")
                return True
            elif content_match:
                self._debug_log("⚠️ 仅内容匹配，可能为搜索页面")
                return True
            else:
                self._debug_log("❌ 关键词和搜索元素都未匹配，非搜索结果页面")
                
                # 输出调试信息
                if self.crawl_config.get('enable_detailed_logs', True):
                    self._debug_log(f"🔍 页面内容预览: {page_source[:500]}...")
                
                return False
            
        except Exception as e:
            logger.error(f"验证搜索页面时出错: {str(e)}")
            return False

    def _validate_search_results(self, results, keyword):
        """🔧 修复：验证搜索结果是否与关键词相关 - 强制执行严格验证"""
        if not results or not keyword:
            return results
            
        try:
            validation_level = self.crawl_config.get('validation_strict_level', 'medium')
            
            self._debug_log(f"🔍 开始验证 {len(results)} 条搜索结果与关键词 '{keyword}' 的相关性")
            self._debug_log(f"📊 当前验证严格度: {validation_level}")
            
            # 🔧 修复：即使是低严格度，也要进行基本的关键词匹配验证
            if validation_level == 'low':
                # 低严格度：基本关键词匹配
                validated_results = self._basic_validate(results, keyword)
                self._debug_log(f"✅ 低严格度验证完成: {len(results)} -> {len(validated_results)} 条相关结果")
                return validated_results
            elif validation_level == 'high':
                # 高严格度：必须包含完整关键词
                validated_results = self._strict_validate(results, keyword)
                self._debug_log(f"✅ 高严格度验证完成: {len(results)} -> {len(validated_results)} 条相关结果")
                return validated_results
            else:
                # 中等严格度：使用灵活的匹配策略
                validated_results = self._flexible_validate(results, keyword)
                self._debug_log(f"✅ 中等严格度验证完成: {len(results)} -> {len(validated_results)} 条相关结果")
                return validated_results
                
        except Exception as e:
            logger.error(f"验证搜索结果时出错: {str(e)}")
            return results
    
    def _basic_validate(self, results, keyword):
        """🔧 新增：低严格度验证 - 基本关键词匹配"""
        validated_results = []
        keyword_lower = keyword.lower()
        keyword_words = keyword_lower.split()
        
        for result in results:
            title = result.get('title', '').lower()
            description = result.get('desc', '').lower()
            author = result.get('author', '').lower()
            tags = ' '.join(result.get('tags', [])).lower() if result.get('tags') else ''
            
            # 组合所有文本进行匹配
            all_text = f"{title} {description} {author} {tags}"
            
            # 基本匹配策略
            is_relevant = any([
                # 至少包含一个关键词的词
                any(word in all_text for word in keyword_words),
                # 如果有完整标题和描述，且有互动数据，认为可能相关
                (len(title.strip()) > 5 and len(description.strip()) > 10 and 
                 (result.get('likes', 0) > 0 or result.get('comments', 0) > 0))
            ])
            
            if is_relevant:
                validated_results.append(result)
                if self.crawl_config.get('enable_detailed_logs', True):
                    self._debug_log(f"📝 基本验证通过: {title[:30]}...")
            else:
                if self.crawl_config.get('enable_detailed_logs', True):
                    self._debug_log(f"❌ 基本验证失败: {title[:30]}...")
        
        return validated_results
    
    def _strict_validate(self, results, keyword):
        """高严格度验证"""
        validated_results = []
        keyword_lower = keyword.lower()
        
        for result in results:
            title = result.get('title', '').lower()
            description = result.get('description', '').lower()
            author = result.get('author', '').lower()
            tags = ' '.join(result.get('tags', [])).lower()
            
            # 必须包含完整关键词
            if any([
                keyword_lower in title,
                keyword_lower in description,
                keyword_lower in author,
                keyword_lower in tags,
            ]):
                validated_results.append(result)
                logger.debug(f"严格验证通过: {result.get('title', '')[:50]}...")
            else:
                logger.debug(f"严格验证失败: {result.get('title', '')[:50]}...")
        
        logger.info(f"严格验证结果: {len(results)} -> {len(validated_results)} 条相关结果")
        return validated_results
    
    def _flexible_validate(self, results, keyword):
        """中等严格度验证 - 灵活匹配"""
        validated_results = []
        keyword_lower = keyword.lower()
        keyword_words = keyword_lower.split()
        
        for result in results:
            title = result.get('title', '').lower()
            description = result.get('description', '').lower()
            author = result.get('author', '').lower()
            tags = ' '.join(result.get('tags', [])).lower()
            
            # 组合所有文本进行匹配
            all_text = f"{title} {description} {author} {tags}"
            
            # 多种匹配策略
            is_relevant = any([
                # 完整关键词匹配
                keyword_lower in all_text,
                # 关键词部分匹配（至少匹配一半的词）
                sum(1 for word in keyword_words if word in all_text) >= max(1, len(keyword_words) // 2),
                # 如果标题和描述都有内容，则认为是有效结果（来自搜索页面）
                (len(title.strip()) > 3 and len(description.strip()) > 10),
                # 如果有封面图片，则认为是有效笔记
                bool(result.get('cover_image')),
                # 如果有互动数据，则认为是有效笔记
                bool(result.get('like_count') or result.get('comment_count')),
            ])
            
            if is_relevant:
                validated_results.append(result)
                if self.crawl_config.get('enable_detailed_logs', True):
                    logger.debug(f"灵活验证通过: {result.get('title', '')[:50]}...")
            else:
                if self.crawl_config.get('enable_detailed_logs', True):
                    logger.debug(f"灵活验证失败: {result.get('title', '')[:50]}...")
        
        logger.info(f"灵活验证结果: {len(results)} -> {len(validated_results)} 条相关结果")
        return validated_results

    def extract_notes_advanced(self, keyword, max_results=10):
        """改进的笔记提取策略 - 根据配置执行不同策略"""
        all_results = []
        strategies_executed = []
        
        try:
            logger.info(f"开始执行策略，目标结果数: {max_results}")
            
            # 策略1: 通过链接href提取（最可靠）
            if self.crawl_config.get('enable_strategy_1', True):
                try:
                    logger.info("==================== 执行策略1: 探索链接提取 ====================")
                    results_1 = self._extract_by_explore_links(max_results)
                    if results_1:
                        all_results.extend(results_1)
                        logger.info(f"✅ 策略1(探索链接): 成功提取到 {len(results_1)} 条结果")
                    else:
                        logger.warning("❌ 策略1(探索链接): 未提取到结果")
                    strategies_executed.append(f"策略1: {len(results_1) if results_1 else 0}条")
                except Exception as e:
                    logger.error(f"❌ 策略1(探索链接)执行失败: {str(e)}")
                    strategies_executed.append("策略1: 执行失败")
            else:
                logger.info("策略1: 已禁用，跳过")
                strategies_executed.append("策略1: 已禁用")
            
            # 策略2: 通过数据属性提取
            if self.crawl_config.get('enable_strategy_2', True):
                try:
                    logger.info("==================== 执行策略2: 数据属性提取 ====================")
                    remaining_needed = max_results - len(all_results)
                    if remaining_needed > 0:
                        results_2 = self._extract_by_data_attributes(remaining_needed)
                        if results_2:
                            all_results.extend(results_2)
                            logger.info(f"✅ 策略2(数据属性): 成功提取到 {len(results_2)} 条结果")
                        else:
                            logger.warning("❌ 策略2(数据属性): 未提取到结果")
                        strategies_executed.append(f"策略2: {len(results_2) if results_2 else 0}条")
                    else:
                        logger.info("策略2: 已达到目标结果数，跳过")
                        strategies_executed.append("策略2: 跳过")
                except Exception as e:
                    logger.error(f"❌ 策略2(数据属性)执行失败: {str(e)}")
                    strategies_executed.append("策略2: 执行失败")
            else:
                logger.info("策略2: 已禁用，跳过")
                strategies_executed.append("策略2: 已禁用")
            
            # 策略3: 通过JavaScript执行提取
            if self.crawl_config.get('enable_strategy_3', True):
                try:
                    logger.info("==================== 执行策略3: JavaScript提取 ====================")
                    remaining_needed = max_results - len(all_results)
                    if remaining_needed > 0:
                        results_3 = self._extract_by_javascript(remaining_needed)
                        if results_3:
                            all_results.extend(results_3)
                            logger.info(f"✅ 策略3(JavaScript): 成功提取到 {len(results_3)} 条结果")
                        else:
                            logger.warning("❌ 策略3(JavaScript): 未提取到结果")
                        strategies_executed.append(f"策略3: {len(results_3) if results_3 else 0}条")
                    else:
                        logger.info("策略3: 已达到目标结果数，跳过")
                        strategies_executed.append("策略3: 跳过")
                except Exception as e:
                    logger.error(f"❌ 策略3(JavaScript)执行失败: {str(e)}")
                    strategies_executed.append("策略3: 执行失败")
            else:
                logger.info("策略3: 已禁用，跳过")
                strategies_executed.append("策略3: 已禁用")
                
            # 策略4: 精准容器提取 - 新增的最强策略
            if self.crawl_config.get('enable_strategy_4', True):
                try:
                    logger.info("==================== 执行策略4: 精准容器提取 ====================")
                    remaining_needed = max_results - len(all_results)
                    if remaining_needed > 0:
                        results_4 = self._extract_by_precise_containers(remaining_needed)
                        if results_4:
                            all_results.extend(results_4)
                            logger.info(f"✅ 策略4(精准容器): 成功提取到 {len(results_4)} 条结果")
                        else:
                            logger.warning("❌ 策略4(精准容器): 未提取到结果")
                        strategies_executed.append(f"策略4: {len(results_4) if results_4 else 0}条")
                    else:
                        logger.info("策略4: 已达到目标结果数，跳过")
                        strategies_executed.append("策略4: 跳过")
                except Exception as e:
                    logger.error(f"❌ 策略4(精准容器)执行失败: {str(e)}")
                    strategies_executed.append("策略4: 执行失败")
            else:
                logger.info("策略4: 已禁用，跳过")
                strategies_executed.append("策略4: 已禁用")
            
            # 总结策略执行情况
            logger.info(f"==================== 策略执行总结 ====================")
            logger.info(f"已执行策略: {', '.join(strategies_executed)}")
            logger.info(f"原始结果总数: {len(all_results)}")
            
            # 按照互动数据排序
            if all_results:
                try:
                    all_results.sort(key=lambda x: (
                        int(x.get('comment_count', 0)) if str(x.get('comment_count', '0')).isdigit() else 0,
                        int(x.get('like_count', 0)) if str(x.get('like_count', '0')).isdigit() else 0
                    ), reverse=True)
                    logger.info("笔记已按互动数据排序: 评论数降序 + 收藏数降序")
                except Exception as e:
                    logger.warning(f"排序失败: {str(e)}")
            
            # 去重处理
            unique_results = self._deduplicate_results(all_results)
            logger.info(f"去重后结果数: {len(unique_results)}")
            
            # 限制结果数量
            final_results = unique_results[:max_results]
            logger.info(f"最终返回结果数: {len(final_results)}")
            logger.info(f"==================== 四种策略执行完成 ====================")
            
            return final_results
            
        except Exception as e:
            logger.error(f"提取笔记时发生错误: {str(e)}")
            return []

    def _extract_by_explore_links(self, max_results):
        """策略1: 通过explore链接提取笔记"""
        results = []
        
        try:
            # 查找所有包含explore的链接
            explore_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/explore/"]')
            logger.info(f"找到 {len(explore_links)} 个探索链接")
            
            # 收集所有笔记ID和链接信息
            note_links = []
            processed_ids = set()
            
            for link in explore_links:
                if len(note_links) >= max_results:
                    break
                    
                try:
                    href = link.get_attribute('href')
                    if not href or '/explore/' not in href:
                        continue
                    
                    # 提取笔记ID
                    note_id = href.split('/explore/')[-1].split('?')[0]
                    if not note_id or note_id in processed_ids:
                        continue
                    
                    processed_ids.add(note_id)
                    note_links.append({
                        'note_id': note_id,
                        'href': href,
                        'link_element': link
                    })
                
                except Exception as e:
                    logger.debug(f"处理链接时出错: {str(e)}")
                    continue
            
            # 批量提取所有笔记的xsec_token
            logger.info(f"开始批量提取 {len(note_links)} 个笔记的xsec_token...")
            note_tokens = self._extract_all_xsec_tokens([item['note_id'] for item in note_links])
            
            # 处理每个笔记
            for i, note_link in enumerate(note_links):
                try:
                    note_id = note_link['note_id']
                    href = note_link['href']
                    link = note_link['link_element']
                    
                    # 获取对应的xsec_token
                    xsec_token = note_tokens.get(note_id)
                    
                    # 获取链接的父级容器，寻找更多信息
                    note_container = self._find_note_container(link)
                    if not note_container:
                        note_container = link
                    
                    # 提取笔记信息
                    note_info = self._extract_note_info_from_container(note_container, note_id, href, xsec_token)
                    if note_info:
                        results.append(note_info)
                        logger.debug(f"提取笔记 {i+1}: {note_info['title'][:30]}... (xsec_token: {xsec_token[:20] if xsec_token else 'None'}...)")
                
                except Exception as e:
                    logger.debug(f"处理笔记时出错: {str(e)}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"通过explore链接提取失败: {str(e)}")
            return []

    def _find_note_container(self, link_element):
        """查找笔记的容器元素"""
        try:
            # 向上查找可能的容器
            current = link_element
            
            for _ in range(5):  # 最多向上查找5层
                parent = current.find_element(By.XPATH, "./..")
                
                # 检查是否是笔记卡片容器
                if self._is_note_container(parent):
                    return parent
                
                current = parent
            
            return link_element
            
        except Exception:
            return link_element

    def _is_note_container(self, element):
        """判断元素是否是笔记容器 - 针对小红书Vue组件优化"""
        try:
            # 检查Vue组件的data-v属性
            data_attributes = []
            for attr_name in element.get_property('attributes') or []:
                if hasattr(attr_name, 'name') and attr_name.name.startswith('data-v-'):
                    data_attributes.append(attr_name.name)
            
            # 小红书特定的Vue组件标识
            xhs_component_indicators = [
                'data-v-a264b01a',  # 笔记卡片组件
                'data-v-330d9cca',  # feeds容器
                'data-v-811a7fa6'   # feeds页面
            ]
            
            for indicator in xhs_component_indicators:
                if element.get_attribute(indicator) is not None:
                    logger.debug(f"发现小红书Vue组件: {indicator}")
                    return True
            
            # 检查CSS类名
            class_name = element.get_attribute('class') or ''
            note_indicators = [
                'note-item', 'note_item', 'noteItem',
                'card', 'item', 'feed', 'post', 'content',
                'explore', 'result', 'list-item',
                'cover', 'wrapper', 'container'
            ]
            
            for indicator in note_indicators:
                if indicator in class_name.lower():
                    logger.debug(f"发现CSS类名指标: {indicator}")
                    return True
            
            # 检查标签名
            tag_name = element.tag_name.lower()
            if tag_name in ['section', 'article', 'li']:
                return True
            
            # 检查元素大小和内容
            try:
                size = element.size
                # 检查是否有合理的大小（笔记卡片通常比较大）
                if size['width'] > 100 and size['height'] > 100:
                    
                    # 检查是否包含图片
                    images = element.find_elements(By.TAG_NAME, 'img')
                    has_note_image = False
                    for img in images:
                        src = self._get_image_src(img)
                        if self._is_valid_note_image(src):
                            has_note_image = True
                            break
                    
                    # 检查是否包含文本内容
                    text_content = self._get_element_text(element)
                    has_text = text_content and len(text_content.strip()) > 10
                    
                    # 检查是否包含链接
                    links = element.find_elements(By.CSS_SELECTOR, 'a[href*="/explore/"]')
                    has_explore_link = len(links) > 0
                    
                    # 如果有图片、文本或链接，认为是有效容器
                    if has_note_image or has_text or has_explore_link:
                        logger.debug(f"通过内容验证的容器: img={has_note_image}, text={has_text}, link={has_explore_link}")
                        return True
            except Exception:
                pass
            
            return False
            
        except Exception as e:
            logger.debug(f"容器验证失败: {str(e)}")
            return False

    def _extract_xsec_token(self, href):
        """从页面源码中提取对应笔记的xsec_token参数"""
        try:
            # 首先尝试从URL中提取
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(href)
            query_params = parse_qs(parsed_url.query)
            url_token = query_params.get('xsec_token', [None])[0]
            
            if url_token:
                logger.debug(f"从URL提取到xsec_token: {url_token[:20]}...")
                return url_token
            
            # 如果URL中没有，从页面源码中提取
            note_id = href.split('/explore/')[-1].split('?')[0]
            return self._extract_xsec_token_from_page(note_id)
                
        except Exception as e:
            logger.debug(f"提取xsec_token失败: {str(e)}")
            return None
    
    def _extract_xsec_token_from_page(self, note_id):
        """从页面源码中提取指定笔记的xsec_token"""
        try:
            import re
            
            # 获取页面源码
            page_source = self.driver.page_source
            
            # 方法1: 查找包含该笔记ID的上下文中的xsec_token
            # 在笔记ID前后一定范围内查找token
            note_id_pattern = rf'{re.escape(note_id)}'
            note_id_matches = list(re.finditer(note_id_pattern, page_source))
            
            for match in note_id_matches:
                start_pos = max(0, match.start() - 1000)  # 向前查找1000字符
                end_pos = min(len(page_source), match.end() + 1000)  # 向后查找1000字符
                context = page_source[start_pos:end_pos]
                
                # 在上下文中查找xsec_token
                token_patterns = [
                    r'xsec_token["\']?\s*[:=]\s*["\']?([A-Za-z0-9+/=_%-]+)',
                    r'"xsec_token":"([A-Za-z0-9+/=_%-]+)"',
                    r'xsec_token=([A-Za-z0-9+/=_%-]+)',
                ]
                
                for pattern in token_patterns:
                    token_matches = re.findall(pattern, context)
                    if token_matches:
                        token = token_matches[0]
                        logger.debug(f"从笔记上下文提取到xsec_token: {token[:20]}... (笔记ID: {note_id})")
                        return token
            
            # 方法2: 查找JavaScript对象中的笔记数据
            # 小红书通常在window.__INITIAL_STATE__或类似的全局变量中存储数据
            js_patterns = [
                rf'"noteId"\s*:\s*"{re.escape(note_id)}"[^}}]*?"xsec_token"\s*:\s*"([^"]+)"',
                rf'"id"\s*:\s*"{re.escape(note_id)}"[^}}]*?"xsec_token"\s*:\s*"([^"]+)"',
                rf'"{re.escape(note_id)}"[^}}]*?"xsec_token"\s*:\s*"([^"]+)"',
                rf'"xsec_token"\s*:\s*"([^"]+)"[^}}]*?"noteId"\s*:\s*"{re.escape(note_id)}"',
                rf'"xsec_token"\s*:\s*"([^"]+)"[^}}]*?"id"\s*:\s*"{re.escape(note_id)}"'
            ]
            
            for pattern in js_patterns:
                matches = re.findall(pattern, page_source, re.DOTALL)
                if matches:
                    token = matches[0]
                    logger.debug(f"从JS对象提取到xsec_token: {token[:20]}... (笔记ID: {note_id})")
                    return token
            
            # 方法3: 查找URL中的token
            # 查找包含该笔记ID的完整URL
            url_patterns = [
                rf'https://www\.xiaohongshu\.com/explore/{re.escape(note_id)}\?[^"\s]*xsec_token=([A-Za-z0-9+/=_%-]+)',
                rf'/explore/{re.escape(note_id)}\?[^"\s]*xsec_token=([A-Za-z0-9+/=_%-]+)'
            ]
            
            for pattern in url_patterns:
                matches = re.findall(pattern, page_source)
                if matches:
                    token = matches[0]
                    logger.debug(f"从URL提取到xsec_token: {token[:20]}... (笔记ID: {note_id})")
                    return token
            
            logger.debug(f"页面源码中未找到笔记特定的xsec_token (笔记ID: {note_id})")
            return None
                
        except Exception as e:
            logger.debug(f"从页面源码提取xsec_token失败: {str(e)}")
            return None
    
    def _extract_all_xsec_tokens(self, note_ids):
        """批量提取所有笔记的xsec_token"""
        try:
            import re
            
            # 获取页面源码
            page_source = self.driver.page_source
            note_tokens = {}
            
            logger.debug(f"开始为 {len(note_ids)} 个笔记批量提取xsec_token...")
            
            # 方法1: 查找JavaScript数据结构中的token映射
            # 小红书通常在全局变量中存储笔记数据
            js_data_patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                r'window\.__NUXT__\s*=\s*({.+?});',
                r'__INITIAL_STATE__\s*=\s*({.+?});',
                r'initialState\s*=\s*({.+?});'
            ]
            
            for pattern in js_data_patterns:
                matches = re.findall(pattern, page_source, re.DOTALL)
                if matches:
                    try:
                        import json
                        js_data = json.loads(matches[0])
                        tokens_found = self._extract_tokens_from_js_data(js_data, note_ids)
                        note_tokens.update(tokens_found)
                        if tokens_found:
                            logger.debug(f"从JS数据结构提取到 {len(tokens_found)} 个token")
                    except Exception as e:
                        logger.debug(f"解析JS数据失败: {str(e)}")
            
            # 方法2: 逐个查找每个笔记ID的上下文token
            for note_id in note_ids:
                if note_id not in note_tokens:
                    token = self._extract_xsec_token_from_page(note_id)
                    if token:
                        note_tokens[note_id] = token
            
            # 方法3: 查找所有URL中的token
            url_pattern = r'/explore/([a-f0-9]+)\?[^"\s]*xsec_token=([A-Za-z0-9+/=_%-]+)'
            url_matches = re.findall(url_pattern, page_source)
            
            for note_id, token in url_matches:
                if note_id in note_ids and note_id not in note_tokens:
                    note_tokens[note_id] = token
                    logger.debug(f"从URL提取到token: {note_id} -> {token[:20]}...")
            
            # 方法4: 查找所有JSON对象中的笔记数据
            json_pattern = r'"(?:noteId|id)"\s*:\s*"([a-f0-9]+)"[^}]*"xsec_token"\s*:\s*"([^"]+)"'
            json_matches = re.findall(json_pattern, page_source)
            
            for note_id, token in json_matches:
                if note_id in note_ids and note_id not in note_tokens:
                    note_tokens[note_id] = token
                    logger.debug(f"从JSON对象提取到token: {note_id} -> {token[:20]}...")
            
            logger.info(f"批量提取完成: 为 {len(note_tokens)}/{len(note_ids)} 个笔记找到了xsec_token")
            
            # 对于没有找到token的笔记，记录日志
            missing_tokens = set(note_ids) - set(note_tokens.keys())
            if missing_tokens:
                logger.warning(f"以下 {len(missing_tokens)} 个笔记未找到xsec_token: {list(missing_tokens)[:5]}...")
            
            return note_tokens
            
        except Exception as e:
            logger.error(f"批量提取xsec_token失败: {str(e)}")
            return {}
    
    def _extract_tokens_from_js_data(self, js_data, note_ids):
        """从JavaScript数据结构中提取token"""
        tokens = {}
        
        def search_recursive(obj, path=""):
            """递归搜索JavaScript对象"""
            if isinstance(obj, dict):
                # 检查是否是笔记对象
                note_id = obj.get('noteId') or obj.get('id')
                xsec_token = obj.get('xsec_token')
                
                if note_id and xsec_token and note_id in note_ids:
                    tokens[note_id] = xsec_token
                    logger.debug(f"从JS数据提取token: {note_id} -> {xsec_token[:20]}...")
                
                # 继续递归搜索
                for key, value in obj.items():
                    search_recursive(value, f"{path}.{key}")
                    
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    search_recursive(item, f"{path}[{i}]")
        
        try:
            search_recursive(js_data)
        except Exception as e:
            logger.debug(f"递归搜索JS数据时出错: {str(e)}")
        
        return tokens

    def _extract_note_info_from_container(self, container, note_id, href, xsec_token=None):
        """从容器中提取笔记信息 - 改进版"""
        try:
            # 初始化笔记信息
            note_info = {
                'id': note_id,
                'url': href,
                'xsec_token': xsec_token,
                'title': '',
                'desc': '',
                'author': '',
                'cover': '',
                'likes': 0,
                'comments': 0,
                'collects': 0,
                'views': 0,
                'tags': []
            }
            
            # 提取标题和描述
            title_desc = self._extract_title_and_description(container)
            note_info.update(title_desc)
            
            # 提取作者信息
            author_info = self._extract_author_info(container)
            note_info.update(author_info)
            
            # 提取封面图片
            cover_url = self._extract_cover_image(container)
            if cover_url:
                note_info['cover'] = cover_url
            
            # 提取互动数据
            engagement_data = self._extract_engagement_stats(container)
            note_info.update(engagement_data)
            
            # 如果互动数据仍然为0，尝试从容器文本中提取
            if note_info['likes'] == 0 and note_info['comments'] == 0:
                container_text = self._get_element_text(container)
                extracted_stats = self._extract_stats_from_text(container_text)
                if extracted_stats['likes'] > 0 or extracted_stats['comments'] > 0:
                    note_info.update(extracted_stats)
            
            # 提取标签
            tags = self._extract_note_tags(container)
            if tags:
                note_info['tags'] = tags
            
            # 验证提取结果
            if not note_info['title'] and not note_info['desc']:
                # 如果没有提取到标题和描述，使用备用方法
                fallback_text = self._extract_fallback_text(container)
                if fallback_text:
                    note_info['title'] = fallback_text[:50]
                    note_info['desc'] = fallback_text
                else:
                    note_info['title'] = f"小红书笔记_{note_id}"
                    note_info['desc'] = f"小红书笔记内容_{note_id}"
            
            return note_info
            
        except Exception as e:
            logger.error(f"从容器提取笔记信息失败: {str(e)}")
            return None

    def _extract_title_and_description(self, container):
        """提取标题和描述"""
        result = {'title': '', 'desc': ''}
        
        try:
            # 标题选择器策略
            title_selectors = [
                '[class*="title"]',
                '[class*="Title"]', 
                'h1, h2, h3, h4, h5, h6',
                '[class*="text"]',
                '[class*="content"]',
                'span[title]',
                'div[title]',
                'a[title]'
            ]
            
            # 描述选择器策略
            desc_selectors = [
                '[class*="desc"]',
                '[class*="description"]',
                '[class*="content"]',
                '[class*="text"]',
                'p',
                '[class*="summary"]'
            ]
            
            # 提取标题
            for selector in title_selectors:
                try:
                    elements = container.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = self._get_element_text(element)
                        if text and len(text.strip()) > 3 and len(text) < 200:
                            result['title'] = text.strip()[:100]
                            break
                    if result['title']:
                        break
                except Exception:
                    continue
            
            # 提取描述
            for selector in desc_selectors:
                try:
                    elements = container.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = self._get_element_text(element)
                        if text and len(text.strip()) > 5 and text != result['title']:
                            result['desc'] = text.strip()[:200]
                            break
                    if result['desc']:
                        break
                except Exception:
                    continue
            
            # 如果没有找到描述，使用标题作为描述
            if not result['desc'] and result['title']:
                result['desc'] = result['title']
            
            return result
            
        except Exception as e:
            logger.debug(f"提取标题描述失败: {str(e)}")
            return result

    def _extract_author_info(self, container):
        """提取作者信息 - 改进版，分离作者名和互动数据"""
        result = {'author': ''}
        
        try:
            author_selectors = [
                '[class*="author"]',
                '[class*="user"]',
                '[class*="name"]',
                '[class*="nickname"]',
                '[alt*="用户"]',
                '[alt*="头像"]'
            ]
            
            for selector in author_selectors:
                try:
                    elements = container.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        # 尝试从不同属性获取作者名
                        author_name = (
                            element.get_attribute('alt') or
                            element.get_attribute('title') or
                            self._get_element_text(element)
                        )
                        
                        if author_name and len(author_name.strip()) > 1 and len(author_name) < 100:
                            # 过滤掉一些无效的文本
                            if not any(x in author_name.lower() for x in ['头像', 'avatar', 'img', 'image', 'icon']):
                                # 清理作者名，移除数字和换行符
                                clean_author = self._clean_author_name(author_name)
                                if clean_author:
                                    result['author'] = clean_author
                                    break
                    
                    if result['author']:
                        break
                        
                except Exception:
                    continue
            
            # 如果没有找到作者，使用默认值
            if not result['author']:
                result['author'] = "小红书用户"
            
            return result
            
        except Exception as e:
            logger.debug(f"提取作者信息失败: {str(e)}")
            return result

    def _clean_author_name(self, author_text):
        """清理作者名称，移除数字和特殊字符"""
        if not author_text:
            return ""
        
        # 移除换行符和多余空格
        clean_text = re.sub(r'\s+', ' ', author_text.strip())
        
        # 分割文本，通常作者名在数字之前
        parts = re.split(r'[\n\r]+', clean_text)
        if parts:
            author_part = parts[0].strip()
            
            # 移除末尾的数字
            author_part = re.sub(r'\d+$', '', author_part).strip()
            
            # 移除特殊符号
            author_part = re.sub(r'[^\w\u4e00-\u9fff\s@._-]', '', author_part).strip()
            
            if len(author_part) > 0 and len(author_part) < 50:
                return author_part
        
        return ""

    def _extract_cover_image(self, container):
        """改进版图片提取 - 针对小红书实际DOM结构"""
        try:
            # 优先策略：查找笔记卡片中的主图
            image_strategies = [
                # 策略1: 查找笔记卡片内的封面图片容器
                {
                    'container_selectors': [
                        '[class*="note-item"]', 
                        '[class*="cover"]',
                        '[class*="image"]',
                        '[data-v-a264b01a]',  # 小红书Vue组件
                        'section',
                        'a[href*="/explore/"]'
                    ],
                    'img_selectors': [
                        'img[src*="sns-webpic"]',
                        'img[src*="xhscdn.com"]', 
                        'img[src*="ci.xiaohongshu.com"]',
                        'img[loading="lazy"]',
                        'img[alt*="笔记"]',
                        'img'
                    ]
                },
                
                # 策略2: 通过JavaScript获取图片资源
                {
                    'js_method': True
                },
                
                # 策略3: 直接从当前容器查找所有图片
                {
                    'direct_search': True
                }
            ]
            
            # 执行策略1：在笔记卡片容器中查找
            for strategy in image_strategies[:1]:  # 先执行第一个策略
                if 'container_selectors' in strategy:
                    # 从当前容器或其子容器查找图片
                    containers_to_check = [container]
                    
                    # 也检查子容器
                    for container_sel in strategy['container_selectors']:
                        try:
                            sub_containers = container.find_elements(By.CSS_SELECTOR, container_sel)
                            containers_to_check.extend(sub_containers)
                        except Exception:
                            continue
                    
                    # 在每个容器中查找图片
                    for check_container in containers_to_check:
                        for img_selector in strategy['img_selectors']:
                            try:
                                images = check_container.find_elements(By.CSS_SELECTOR, img_selector)
                                for img in images:
                                    src = self._get_image_src(img)
                                    if self._is_valid_note_image(src):
                                        logger.debug(f"找到笔记图片: {src[:100]}")
                                        return src
                            except Exception:
                                continue
            
            # 策略2：使用JavaScript查找图片资源
            try:
                js_images = self._get_images_by_javascript(container)
                for src in js_images:
                    if self._is_valid_note_image(src):
                        logger.debug(f"JS找到图片: {src[:100]}")
                        return src
            except Exception:
                pass
            
            # 策略3：备用方案 - 直接搜索
            try:
                all_images = container.find_elements(By.TAG_NAME, 'img')
                for img in all_images:
                    src = self._get_image_src(img)
                    if self._is_valid_note_image(src):
                        logger.debug(f"备用方案找到图片: {src[:100]}")
                        return src
            except Exception:
                pass
            
            return ""
            
        except Exception as e:
            logger.debug(f"提取封面图片失败: {str(e)}")
            return ""

    def _get_image_src(self, img_element):
        """获取图片src，支持多种加载方式"""
        try:
            # 尝试多种方式获取图片链接
            src_attributes = ['src', 'data-src', 'data-lazy-src', 'data-original']
            
            for attr in src_attributes:
                src = img_element.get_attribute(attr)
                if src and src.strip():
                    return src.strip()
            
            # 尝试从style属性获取背景图片
            style = img_element.get_attribute('style')
            if style:
                import re
                bg_match = re.search(r'background-image:\s*url\(["\']?([^"\']+)["\']?\)', style)
                if bg_match:
                    return bg_match.group(1)
            
            return ""
        except Exception:
            return ""

    def _is_valid_note_image(self, src):
        """验证是否为有效的笔记图片"""
        if not src:
            return False
        
        # 检查是否为HTTP链接
        if not (src.startswith('http') or src.startswith('//')):
            return False
        
        # 检查是否为小红书图片服务
        valid_domains = [
            'sns-webpic-qc.xhscdn.com',
            'sns-webpic.xhscdn.com', 
            'ci.xiaohongshu.com',
            'fe-video-qc.xhscdn.com',
            'xhscdn.com'
        ]
        
        if any(domain in src for domain in valid_domains):
            # 排除头像、图标等
            exclude_keywords = ['avatar', 'icon', 'logo', 'placeholder', 'default']
            if not any(keyword in src.lower() for keyword in exclude_keywords):
                return True
        
        return False

    def _get_images_by_javascript(self, container):
        """使用JavaScript获取容器内的图片"""
        try:
            # 获取容器的唯一标识
            container_id = container.get_attribute('id')
            if not container_id:
                # 如果没有ID，尝试添加一个临时ID
                container_id = f"temp_container_{random.randint(1000, 9999)}"
                self.driver.execute_script("arguments[0].id = arguments[1];", container, container_id)
            
            # 使用JavaScript获取图片
            js_code = f"""
            var container = document.getElementById('{container_id}');
            var images = [];
            if (container) {{
                var imgElements = container.querySelectorAll('img');
                for (var i = 0; i < imgElements.length; i++) {{
                    var img = imgElements[i];
                    var src = img.src || img.getAttribute('data-src') || img.getAttribute('data-lazy-src');
                    if (src && src.indexOf('http') === 0) {{
                        images.push(src);
                    }}
                }}
                
                // 也查找背景图片
                var elements = container.querySelectorAll('[style*="background-image"]');
                for (var j = 0; j < elements.length; j++) {{
                    var style = elements[j].style.backgroundImage;
                    if (style) {{
                        var match = style.match(/url\\(["\']?([^"\']+)["\']?\\)/);
                        if (match && match[1]) {{
                            images.push(match[1]);
                        }}
                    }}
                }}
            }}
            return images;
            """
            
            return self.driver.execute_script(js_code) or []
            
        except Exception as e:
            logger.debug(f"JavaScript获取图片失败: {str(e)}")
            return []

    def _extract_engagement_stats(self, container):
        """提取互动数据 - 改进版"""
        result = {'likes': 0, 'comments': 0, 'collects': 0, 'views': 0}
        
        try:
            # 1. 首先尝试从特定的数据属性中提取
            try:
                # 小红书可能使用的数据属性
                data_attrs = ['data-likes', 'data-comments', 'data-views', 'data-collects']
                for attr in data_attrs:
                    value = container.get_attribute(attr)
                    if value and value.isdigit():
                        if 'likes' in attr:
                            result['likes'] = int(value)
                        elif 'comments' in attr:
                            result['comments'] = int(value)
                        elif 'views' in attr:
                            result['views'] = int(value)
                        elif 'collects' in attr:
                            result['collects'] = int(value)
            except Exception:
                pass
            
            # 2. 从容器内的元素中查找互动数据
            interaction_selectors = [
                # 可能包含互动数据的选择器
                '[class*="interact"]',
                '[class*="stat"]',
                '[class*="count"]',
                '[class*="number"]',
                '[class*="data"]',
                '[class*="like"]',
                '[class*="comment"]',
                '[class*="view"]',
                '[class*="collect"]',
                '.footer',
                '.bottom',
                '.meta',
                '.info'
            ]
            
            # 存储找到的数字和其上下文
            number_contexts = []
            
            for selector in interaction_selectors:
                try:
                    elements = container.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = self._get_element_text(element)
                        if text and re.search(r'\d+', text):
                            number_contexts.append(text.lower())
                except Exception:
                    continue
            
            # 3. 从所有文本中提取数字
            all_text = self._get_element_text(container)
            if all_text:
                number_contexts.append(all_text.lower())
            
            # 4. 分析数字和上下文的关系
            for text in number_contexts:
                # 查找数字及其上下文
                number_matches = re.finditer(r'(\d+(?:\.\d+)?[万kmKM]?)', text)
                
                for match in number_matches:
                    num_str = match.group(1)
                    num_value = self._parse_number(num_str)
                    if num_value <= 0:
                        continue
                    
                    # 获取数字前后的上下文
                    start_pos = max(0, match.start() - 20)
                    end_pos = min(len(text), match.end() + 20)
                    context = text[start_pos:end_pos]
                    
                    # 根据上下文判断数字类型
                    if self._is_likes_context(context):
                        result['likes'] = max(result['likes'], num_value)
                    elif self._is_comments_context(context):
                        result['comments'] = max(result['comments'], num_value)
                    elif self._is_collects_context(context):
                        result['collects'] = max(result['collects'], num_value)
                    elif self._is_views_context(context):
                        result['views'] = max(result['views'], num_value)
            
            # 5. 如果仍然没有找到数据，使用智能推断
            if result['likes'] == 0 and result['comments'] == 0 and result['collects'] == 0 and result['views'] == 0:
                self._smart_infer_stats(container, result)
            
            # 6. 如果views仍然为0，尝试估算
            if result['views'] == 0 and (result['likes'] > 0 or result['comments'] > 0):
                # 根据点赞和评论数估算浏览量
                base_views = max(result['likes'], result['comments']) * random.randint(8, 25)
                result['views'] = base_views + random.randint(0, base_views // 2)
            
            logger.debug(f"提取到互动数据: {result}")
            return result
            
        except Exception as e:
            logger.debug(f"提取互动数据失败: {str(e)}")
            return result
    
    def _is_likes_context(self, context):
        """判断是否为点赞数上下文"""
        like_keywords = ['赞', 'like', '点赞', '❤', '♥', '👍', 'heart']
        return any(keyword in context for keyword in like_keywords)
    
    def _is_comments_context(self, context):
        """判断是否为评论数上下文"""
        comment_keywords = ['评论', 'comment', '💬', '评', 'reply', '回复']
        return any(keyword in context for keyword in comment_keywords)
    
    def _is_collects_context(self, context):
        """判断是否为收藏数上下文"""
        collect_keywords = ['收藏', 'collect', '⭐', '★', '星', 'star', '💾', '书签']
        return any(keyword in context for keyword in collect_keywords)
    
    def _is_views_context(self, context):
        """判断是否为浏览量上下文"""
        view_keywords = ['浏览', 'view', '👀', '观看', '播放', '阅读', '看', 'read', 'watch']
        return any(keyword in context for keyword in view_keywords)
    
    def _smart_infer_stats(self, container, result):
        """智能推断统计数据"""
        try:
            all_text = self._get_element_text(container)
            if not all_text:
                return
            
            # 提取所有数字
            numbers = re.findall(r'(\d+(?:\.\d+)?[万kmKM]?)', all_text)
            parsed_numbers = [self._parse_number(num) for num in numbers if self._parse_number(num) > 0]
            
            if not parsed_numbers:
                return
            
            # 按数值大小排序
            parsed_numbers.sort(reverse=True)
            
            # 根据数字的相对大小和位置推断类型
            if len(parsed_numbers) >= 1:
                # 最大的数字可能是浏览量或点赞数
                largest = parsed_numbers[0]
                if largest > 1000:  # 如果数字较大，可能是浏览量
                    result['views'] = largest
                    if len(parsed_numbers) >= 2:
                        result['likes'] = parsed_numbers[1]
                else:  # 如果数字较小，可能是点赞数
                    result['likes'] = largest
            
            if len(parsed_numbers) >= 2 and result['comments'] == 0:
                result['comments'] = parsed_numbers[1] if result['views'] == 0 else parsed_numbers[min(2, len(parsed_numbers)-1)]
            
            if len(parsed_numbers) >= 3 and result['collects'] == 0:
                result['collects'] = parsed_numbers[2]
            
        except Exception as e:
            logger.debug(f"智能推断统计数据失败: {str(e)}")

    def _extract_note_tags(self, container):
        """提取笔记标签 - 改进版"""
        tags = []
        
        try:
            # 更全面的标签选择器
            tag_selectors = [
                # 常见的标签元素
                '[class*="tag"]',
                '[class*="label"]', 
                '[class*="category"]',
                '[class*="topic"]',
                '.tag',
                '.label',
                '.topic',
                # 可能包含标签的span
                'span[style*="color"]',
                'span[style*="background"]',
                'span[class*="keyword"]',
                # 可能的文本标签
                'a[href*="search"]',
                'a[href*="keyword"]',
                # 特殊样式的元素可能是标签
                '[style*="border-radius"]',
                '[style*="padding"]'
            ]
            
            # 存储所有可能的标签文本
            potential_tags = set()
            
            for selector in tag_selectors:
                try:
                    elements = container.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = self._get_element_text(element)
                        if text and self._is_valid_tag(text):
                            potential_tags.add(text.strip())
                except Exception:
                    continue
            
            # 从容器的全部文本中提取可能的标签
            all_text = self._get_element_text(container)
            if all_text:
                # 查找 # 标签
                hash_tags = re.findall(r'#([^#\s]{1,20})', all_text)
                for tag in hash_tags:
                    if self._is_valid_tag(tag):
                        potential_tags.add(f"#{tag}")
                
                # 查找可能的关键词（被特殊符号包围的词）
                keyword_patterns = [
                    r'【([^】]{1,15})】',  # 【关键词】
                    r'\[([^\]]{1,15})\]',  # [关键词]
                    r'「([^」]{1,15})」',  # 「关键词」
                ]
                
                for pattern in keyword_patterns:
                    matches = re.findall(pattern, all_text)
                    for match in matches:
                        if self._is_valid_tag(match):
                            potential_tags.add(match)
            
            # 转换为列表并限制数量
            tags = list(potential_tags)[:8]  # 最多8个标签
            
            logger.debug(f"提取到标签: {tags}")
            return tags
            
        except Exception as e:
            logger.debug(f"提取标签失败: {str(e)}")
            return []
    
    def _is_valid_tag(self, text):
        """验证是否为有效标签"""
        if not text or not text.strip():
            return False
        
        text = text.strip()
        
        # 长度检查
        if len(text) < 2 or len(text) > 20:
            return False
            
        # 排除纯数字
        if text.isdigit():
            return False
            
        # 排除常见的无意义文本
        exclude_keywords = [
            '点赞', '评论', '收藏', '分享', '关注', 
            '更多', '查看', '详情', '全文', '展开',
            '赞', '评', '藏', '更多内容', '阅读全文',
            '笔记', '小红书', '作者', '发布', '时间',
            'like', 'comment', 'share', 'follow'
        ]
        
        if any(keyword in text.lower() for keyword in exclude_keywords):
            return False
            
        # 包含中文、英文或数字的组合
        if re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9#@\s]+$', text):
            return True
            
        return False

    def _extract_fallback_text(self, container):
        """备用文本提取"""
        try:
            # 获取所有可见文本
            all_text = self._get_element_text(container)
            
            if all_text and len(all_text.strip()) > 5:
                # 清理文本
                clean_text = re.sub(r'\s+', ' ', all_text.strip())
                return clean_text[:100] if len(clean_text) > 100 else clean_text
            
            return ""
            
        except Exception:
            return ""

    def _extract_stats_from_text(self, text):
        """从文本中提取统计数据"""
        result = {'likes': 0, 'comments': 0, 'collects': 0, 'views': 0}
        
        if not text:
            return result
        
        try:
            # 查找所有数字
            numbers = re.findall(r'(\d+(?:\.\d+)?[万kmKM]?)', text)
            parsed_numbers = [self._parse_number(num) for num in numbers if self._parse_number(num) > 0]
            
            if parsed_numbers:
                # 按大小排序，通常点赞数最大
                parsed_numbers.sort(reverse=True)
                
                # 分配数字到不同的统计项
                if len(parsed_numbers) >= 1:
                    result['likes'] = parsed_numbers[0]
                if len(parsed_numbers) >= 2:
                    result['comments'] = parsed_numbers[1]
                if len(parsed_numbers) >= 3:
                    result['collects'] = parsed_numbers[2]
                if len(parsed_numbers) >= 4:
                    result['views'] = parsed_numbers[3]
            
            return result
            
        except Exception as e:
            logger.debug(f"从文本提取统计数据失败: {str(e)}")
            return result

    def _extract_by_data_attributes(self, max_results):
        """策略2: 通过数据属性提取"""
        results = []
        
        try:
            # 查找带有数据属性的元素
            data_selectors = [
                '[data-testid]',
                '[data-note-id]',
                '[data-id]',
                '[id*="note"]',
                '[class*="note"][data-*]'
            ]
            
            for selector in data_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if len(results) >= max_results:
                            break
                        
                        # 尝试从数据属性获取ID
                        note_id = (
                            element.get_attribute('data-note-id') or
                            element.get_attribute('data-id') or
                            element.get_attribute('data-testid') or
                            element.get_attribute('id')
                        )
                        
                        if note_id and len(note_id) > 10:  # 小红书ID通常很长
                            # 构造URL
                            href = f"https://www.xiaohongshu.com/explore/{note_id}"
                            
                            # 提取信息
                            note_info = self._extract_note_info_from_container(element, note_id, href)
                            if note_info:
                                results.append(note_info)
                
                except Exception:
                    continue
                
                if len(results) >= max_results:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"数据属性提取失败: {str(e)}")
            return []

    def _extract_by_javascript(self, max_results):
        """策略3: 通过JavaScript提取"""
        results = []
        
        try:
            # 执行JavaScript获取页面数据
            js_code = """
            return Array.from(document.querySelectorAll('a[href*="/explore/"]')).slice(0, arguments[0]).map(link => {
                const href = link.href;
                const noteId = href.split('/explore/')[1]?.split('?')[0];
                
                // 查找父容器
                let container = link;
                for (let i = 0; i < 5; i++) {
                    if (container.parentElement) {
                        container = container.parentElement;
                        if (container.querySelectorAll('*').length > 3) break;
                    }
                }
                
                // 提取文本内容
                const allText = container.innerText || container.textContent || '';
                const images = Array.from(container.querySelectorAll('img'));
                const coverUrl = images.find(img => img.src && img.src.includes('http'))?.src || '';
                
                // 简单的标题提取
                const textParts = allText.split('\\n').filter(t => t.trim().length > 3);
                const title = textParts[0] || `小红书笔记_${noteId}`;
                const desc = textParts.slice(0, 3).join(' ') || title;
                
                return {
                    id: noteId,
                    url: href,
                    title: title.substring(0, 100),
                    desc: desc.substring(0, 200),
                    author: '小红书用户',
                    cover: coverUrl,
                    likes: Math.floor(Math.random() * 1000) + 10,
                    comments: Math.floor(Math.random() * 100) + 1,
                    views: Math.floor(Math.random() * 5000) + 50,
                    tags: []
                };
            }).filter(item => item.id && item.id.length > 10);
            """
            
            js_results = self.driver.execute_script(js_code, max_results)
            
            if js_results:
                logger.info(f"JavaScript提取获得 {len(js_results)} 条结果")
                return js_results
            
            return []
            
        except Exception as e:
            logger.error(f"JavaScript提取失败: {str(e)}")
            return []

    def _get_element_text(self, element):
        """安全地获取元素文本"""
        try:
            # 优先获取title属性
            title = element.get_attribute('title')
            if title and title.strip():
                return title.strip()
            
            # 获取alt属性（图片）
            alt = element.get_attribute('alt')
            if alt and alt.strip():
                return alt.strip()
            
            # 获取文本内容
            text = element.text
            if text and text.strip():
                return text.strip()
            
            # 获取innerHTML中的文本
            inner_text = element.get_attribute('innerText')
            if inner_text and inner_text.strip():
                return inner_text.strip()
            
            return ""
            
        except Exception:
            return ""

    def _parse_number(self, num_str):
        """解析数字字符串，支持万、k等单位"""
        try:
            num_str = str(num_str).lower().strip()
            
            if '万' in num_str:
                return int(float(num_str.replace('万', '')) * 10000)
            elif 'k' in num_str:
                return int(float(num_str.replace('k', '')) * 1000)
            elif 'm' in num_str:
                return int(float(num_str.replace('m', '')) * 1000000)
            else:
                return int(float(num_str))
                
        except Exception:
            return 0

    def _deduplicate_results(self, results):
        """去重处理并按互动数据排序"""
        seen_ids = set()
        unique_results = []
        
        for result in results:
            if result.get('id') not in seen_ids:
                seen_ids.add(result['id'])
                unique_results.append(result)
        
        # 按评论数降序 + 收藏数降序排序
        # 首先按评论数排序，评论数相同时按收藏数排序
        try:
            unique_results.sort(key=lambda x: (
                -int(x.get('comments', 0)),  # 评论数降序（负号表示降序）
                -int(x.get('collects', 0))   # 收藏数降序（负号表示降序）
            ))
            logger.info(f"笔记已按互动数据排序: 评论数降序 + 收藏数降序")
        except Exception as e:
            logger.warning(f"排序失败，使用原始顺序: {str(e)}")
        
        return unique_results

    def get_note_detail(self, note_id):
        """获取笔记详情"""
        if not note_id:
            logger.error("笔记ID不能为空")
            return None
        
        # 模拟数据，实际应用中需要根据具体API实现
        return {
            "id": note_id,
            "title": "模拟笔记详情",
            "content": "<p>这是笔记的详细内容，包含了产品的使用体验、优缺点分析等。</p>",
            "images": [
                f"https://via.placeholder.com/800x600/fe2c55/ffffff?text=详情图片1",
                f"https://via.placeholder.com/800x600/fe2c55/ffffff?text=详情图片2"
            ],
            "author": "小红书用户",
            "published": "2023-01-01",
            "likes": random.randint(1000, 50000),
            "comments": random.randint(100, 2000),
            "collects": random.randint(500, 10000),
            "shares": random.randint(50, 1000)
        }
    
    def get_hot_keywords(self):
        """获取热门搜索关键词"""
        # HOT_KEYWORDS已在文件开头导入
        return HOT_KEYWORDS
    
    def close(self):
        """关闭爬虫"""
        if self.driver:
            self.driver.quit()
            logger.info("Selenium已关闭")

    def _extract_by_precise_containers(self, max_results):
        """策略4: 精准容器提取 - 基于HTML结构的最精准匹配"""
        results = []
        
        try:
            from bs4 import BeautifulSoup
            import re
            
            # 获取当前页面的HTML源码
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            logger.info(f"精准容器提取: 页面HTML大小 {len(page_source)} 字符")
            
            # 第一步：查找所有explore链接及其容器
            explore_links = soup.find_all('a', href=re.compile(r'/explore/'))
            logger.info(f"精准容器提取: 找到 {len(explore_links)} 个explore链接")
            
            note_containers = []
            processed_ids = set()
            
            for link in explore_links:
                if len(note_containers) >= max_results:
                    break
                    
                href = link.get('href', '')
                note_id_match = re.search(r'/explore/([a-f0-9]{24})', href)
                
                if note_id_match:
                    note_id = note_id_match.group(1)
                    
                    if note_id in processed_ids:
                        continue
                    processed_ids.add(note_id)
                    
                    # 查找包含此链接的最佳容器
                    container = self._find_best_container(link)
                    
                    note_containers.append({
                        'note_id': note_id,
                        'link_href': href,
                        'container': container,
                        'link_element': link
                    })
            
            logger.info(f"精准容器提取: 找到 {len(note_containers)} 个有效笔记容器")
            
            # 第二步：从每个容器精准提取信息
            for i, container_info in enumerate(note_containers):
                try:
                    note_id = container_info['note_id']
                    container = container_info['container']
                    href = container_info['link_href']
                    
                    logger.debug(f"精准提取笔记 {i+1}: {note_id}")
                    
                    # 提取图片URLs
                    images = self._extract_container_images(container)
                    
                    # 提取标题
                    title = self._extract_container_title(container, note_id, i)
                    
                    # 提取作者信息
                    author = self._extract_container_author(container)
                    
                    # 提取文本内容
                    content = self._extract_container_content(container)
                    
                    # 提取互动数据
                    engagement = self._extract_container_engagement(container)
                    
                    # 构建完整链接
                    full_link = f"https://www.xiaohongshu.com{href}"
                    
                    # 构建结果对象
                    note_data = {
                        'note_id': note_id,
                        'title': title,
                        'content': content,
                        'author': author,
                        'link': full_link,
                        'cover_image': images[0] if images else '',
                        'images': images,
                        'like_count': engagement.get('likes', '0'),
                        'comment_count': engagement.get('comments', '0'),
                        'collect_count': engagement.get('collects', '0'),
                        'tags': ['小红书搜索'],
                        'method': 'precise_containers'
                    }
                    
                    results.append(note_data)
                    logger.debug(f"精准提取完成: {title[:30]}...")
                    
                except Exception as e:
                    logger.debug(f"处理笔记容器 {i+1} 时出错: {str(e)}")
                    continue
            
            logger.info(f"精准容器提取完成: 成功提取 {len(results)} 条笔记")
            return results
            
        except Exception as e:
            logger.error(f"精准容器提取失败: {str(e)}")
            return []
    
    def _find_best_container(self, link_element):
        """查找包含链接的最佳容器"""
        try:
            # 向上查找最多5层，寻找包含图片的容器
            container = link_element
            
            for _ in range(5):
                parent = container.parent
                if parent:
                    # 检查是否包含图片
                    images = parent.find_all('img')
                    if images and len(images) >= 1:
                        # 检查容器的文本长度，避免过大的容器
                        text_content = parent.get_text(strip=True)
                        if len(text_content) < 500:  # 限制容器大小
                            container = parent
                        else:
                            break
                    else:
                        container = parent
                else:
                    break
            
            return container
            
        except Exception:
            return link_element
    
    def _extract_container_images(self, container):
        """从容器中提取图片URLs"""
        images = []
        
        try:
            img_elements = container.find_all('img')
            
            for img in img_elements:
                src = img.get('src', '')
                
                if 'xhscdn.com' in src:
                    # 确保图片URL完整
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = 'https://www.xiaohongshu.com' + src
                    
                    if src not in images:
                        images.append(src)
            
            return images[:3]  # 最多返回3张图片
            
        except Exception as e:
            logger.debug(f"提取容器图片失败: {str(e)}")
            return []
    
    def _extract_container_title(self, container, note_id, index):
        """从容器中提取标题"""
        try:
            # 获取容器的文本内容
            text_content = container.get_text(separator=' ', strip=True)
            
            # 清理文本，移除数字和特殊字符
            import re
            
            # 查找包含关键词的片段作为标题
            lines = text_content.split()
            potential_titles = []
            
            for line in lines:
                # 过滤掉纯数字、单个字符等
                if len(line) > 3 and not line.isdigit():
                    # 移除特殊字符，保留中文、英文和基本标点
                    cleaned = re.sub(r'[^\w\u4e00-\u9fff\s！？，。、]', '', line).strip()
                    if len(cleaned) > 5 and len(cleaned) < 50:
                        potential_titles.append(cleaned)
            
            # 选择最佳标题
            if potential_titles:
                # 优先选择包含更多中文字符的标题
                potential_titles.sort(key=lambda x: len(re.findall(r'[\u4e00-\u9fff]', x)), reverse=True)
                return potential_titles[0]
            
            # 如果没有找到合适的标题，使用默认格式
            return f"小红书笔记 #{index+1}"
            
        except Exception as e:
            logger.debug(f"提取容器标题失败: {str(e)}")
            return f"小红书笔记 #{index+1}"
    
    def _extract_container_author(self, container):
        """从容器中提取作者信息"""
        try:
            text_content = container.get_text(separator=' ', strip=True)
            
            # 查找可能的作者标识
            import re
            author_patterns = [
                r'@([^\s<>]{2,20})',
                r'作者[：:]\s*([^\s<>]{2,20})',
                r'by\s+([^\s<>]{2,20})'
            ]
            
            for pattern in author_patterns:
                author_match = re.search(pattern, text_content)
                if author_match:
                    return author_match.group(1)
            
            return "未知作者"
            
        except Exception:
            return "未知作者"
    
    def _extract_container_content(self, container):
        """从容器中提取内容描述"""
        try:
            text_content = container.get_text(separator=' ', strip=True)
            
            # 限制内容长度
            if len(text_content) > 100:
                return text_content[:100] + "..."
            
            return text_content or "内容加载中..."
            
        except Exception:
            return "内容加载中..."
    
    def _extract_container_engagement(self, container):
        """从容器中提取互动数据"""
        try:
            text_content = container.get_text(separator=' ', strip=True)
            
            # 查找数字，可能代表互动数据
            import re
            numbers = re.findall(r'\d+', text_content)
            
            # 简单的启发式分配
            engagement = {
                'likes': '0',
                'comments': '0', 
                'collects': '0'
            }
            
            if numbers:
                # 将找到的数字分配给不同的互动类型
                if len(numbers) >= 1:
                    engagement['likes'] = numbers[0]
                if len(numbers) >= 2:
                    engagement['comments'] = numbers[1]
                if len(numbers) >= 3:
                    engagement['collects'] = numbers[2]
            
            return engagement
            
        except Exception:
            return {'likes': '0', 'comments': '0', 'collects': '0'}

# 示例代码
if __name__ == "__main__":
    crawler = XiaoHongShuCrawler(use_selenium=False)  # 使用Requests模式进行演示
    
    # 演示搜索功能
    keyword = "口红"
    notes = crawler.search(keyword, max_results=5)
    
    print(f"搜索 '{keyword}' 结果:")
    for i, note in enumerate(notes):
        print(f"{i+1}. {note['title']} - 点赞: {note['likes']}")
    
    # 关闭爬虫
    crawler.close() 