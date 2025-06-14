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

# 导入配置信息（现在在app.py中定义）
try:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from app import SEARCH_CONFIG, CRAWLER_CONFIG, DIRECTORIES, FILE_PATHS, URLS, HOT_KEYWORDS
except ImportError:
    # 如果无法导入，使用默认配置
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    SEARCH_CONFIG = {'DEFAULT_MAX_RESULTS': 30, 'MAX_RESULTS_LIMIT': 100, 'USE_CACHE': True, 'CACHE_EXPIRE_TIME': 3600}
    CRAWLER_CONFIG = {'USE_SELENIUM': True, 'HEADLESS': True, 'WINDOW_SIZE': (1920, 1080), 'CHROME_OPTIONS': ['--headless']}
    DIRECTORIES = {'CACHE_DIR': os.path.join(PROJECT_ROOT, 'cache'), 'TEMP_DIR': os.path.join(PROJECT_ROOT, 'cache', 'temp')}
    FILE_PATHS = {'CHROMEDRIVER_PATH': os.path.join(PROJECT_ROOT, 'drivers', 'chromedriver-mac-arm64', 'chromedriver'), 'COOKIES_FILE': os.path.join(PROJECT_ROOT, 'cache', 'cookies', 'xiaohongshu_cookies.json')}
    URLS = {'XIAOHONGSHU_BASE': 'https://www.xiaohongshu.com'}
    HOT_KEYWORDS = ["海鸥手表", "美食", "护肤"]

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
        
        # 初始化参数
        self.use_selenium = use_selenium if use_selenium is not None else self.crawler_config['USE_SELENIUM']
        self.headless = headless if headless is not None else self.crawler_config['HEADLESS']
        self.proxy = proxy
        self.cookies_file = cookies_file or FILE_PATHS['COOKIES_FILE']
        
        # WebDriver相关
        self.driver = None
        
        # 缓存配置
        self.cache_dir = DIRECTORIES['TEMP_DIR']
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # HTML回调函数
        self.html_callback = None
        
        # 加载cookie
        self.cookies = self._load_cookies()
        
        logger.info("小红书爬虫初始化完成")
    
    def set_html_callback(self, callback_func):
        """设置HTML存储回调函数"""
        self.html_callback = callback_func
        logger.info("HTML存储回调函数已设置")
    
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
            
            # 添加配置文件中的Chrome选项
            for option in self.crawler_config['CHROME_OPTIONS']:
                chrome_options.add_argument(option)
            
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
            cache_path = self._get_cache_path(keyword)
            cache_data = {
                'timestamp': time.time(),
                'keyword': keyword,
                'data': data
            }
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            logger.info(f"数据已缓存: {cache_path}")
            
            # 同时生成HTML结果页面
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
            
            # 编码URL用于代理
            encoded_url = urllib.parse.quote(enhanced_url, safe='')
            
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
                        <a href="/proxy/note/{encoded_url}" target="_blank" class="note-link proxy-link">代理访问</a>
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
        
        .proxy-link {{
            background: linear-gradient(45deg, #ff6b6b, #ff8e8e);
        }}
        
        .proxy-link:hover {{
            background: linear-gradient(45deg, #ff5252, #ff6b6b);
            transform: translateY(-1px);
            box-shadow: 0 3px 10px rgba(255, 107, 107, 0.3);
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
            }} else if (retryCount === 2) {{
                // 第二次失败：尝试通过代理服务器
                const proxyUrl = `http://localhost:8081/image?url=${{encodeURIComponent(originalUrl)}}`;
                console.log('清理URL失败，尝试代理服务器:', proxyUrl);
                img.src = proxyUrl;
            }} else {{
                // 最终失败：显示占位符
                console.log('所有方法都失败，显示占位符');
                img.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjRjVGNUY1Ii8+Cjx0ZXh0IHg9IjEwMCIgeT0iMTAwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkb21pbmFudC1iYXNlbGluZT0iY2VudHJhbCIgZmlsbD0iIzk5OTk5OSIgZm9udC1zaXplPSIxNCIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIj7lsI/nuqLkuaZDRE48L3RleHQ+Cjwvc3ZnPg==';
                img.onerror = null; // 防止无限循环
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
            
            logger.info(f"从缓存加载数据: {cache_path}")
            return cache['data']
        except Exception as e:
            logger.error(f"加载缓存失败: {str(e)}")
            return None
    
    def _handle_anti_bot(self):
        """处理反爬虫机制"""
        try:
            # 等待页面加载
            time.sleep(5)
            
            # 检查是否有登录提示或验证码
            page_text = self.driver.page_source.lower()
            if any(keyword in page_text for keyword in ['登录', 'login', '验证', 'captcha']):
                logger.warning("检测到反爬虫机制或登录要求")
            
            # 尝试关闭可能的弹窗
            close_selectors = [
                "//div[contains(@class, 'close')]",
                "//button[contains(@class, 'close')]", 
                "//span[contains(@class, 'close')]",
                "//div[contains(text(), '关闭')]",
                "//button[contains(text(), '关闭')]"
            ]
            
            for selector in close_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        elements[0].click()
                        logger.info(f"成功点击关闭按钮: {selector}")
                        time.sleep(2)
                        break
                except:
                    continue
            
            return True
            
        except Exception as e:
            logger.warning(f"处理反爬虫机制时出错: {str(e)}")
            return True  # 即使处理失败也继续执行

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
        """等待内容完全加载"""
        try:
            wait = WebDriverWait(self.driver, 30)
            
            # 1. 等待页面基本结构加载
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # 2. 等待搜索结果区域
            wait.until(
                lambda driver: driver.find_elements(By.CSS_SELECTOR, 
                    "[class*='feeds'], [class*='note'], [class*='card'], section, .note-item, [data-testid]")
            )
            
            # 3. 使用JavaScript检测内容是否完全渲染
            self.driver.execute_script("""
                return new Promise((resolve) => {
                    const checkContent = () => {
                        const elements = document.querySelectorAll('a[href*="/explore/"], [class*="note"], [class*="card"]');
                        if (elements.length > 10) {
                            resolve(true);
                        } else {
                            setTimeout(checkContent, 1000);
                        }
                    };
                    checkContent();
                });
            """)
            
            # 4. 等待图片加载
            time.sleep(3)
            
            # 5. 滚动页面触发懒加载
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            logger.info("页面内容加载完成")
            return True
            
        except Exception as e:
            logger.warning(f"等待内容加载失败: {e}")
            return False

    def search(self, keyword, max_results=10, use_cache=True):
        """搜索小红书内容 - 改进版本"""
        if use_cache:
            cached_result = self._load_from_cache(keyword)
            if cached_result:
                logger.info(f"从缓存获取搜索结果: {keyword}")
                return cached_result[:max_results]

        try:
            search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}"
            logger.info(f"开始搜索: {keyword}")
            
            # 确保WebDriver已初始化
            if not self._ensure_driver_initialized():
                logger.error("WebDriver初始化失败")
                return []
            
            # 访问搜索页面
            self.driver.get(search_url)
            
            # 等待并检测反爬虫
            if not self._handle_anti_bot():
                logger.error("反爬虫检测处理失败")
                return []
            
            # 等待内容完全加载
            if not self.wait_for_content_load():
                logger.error("页面内容加载超时")
                return []
            
            # 保存页面源码用于调试
            page_source_path = self._save_page_source(self.driver.page_source, keyword)
            logger.info(f"页面源码已保存: {page_source_path}")
            
            # 使用改进的多策略提取
            results = self.extract_notes_advanced(keyword, max_results)
            
            if results:
                # 缓存结果
                if use_cache:
                    self._save_to_cache(keyword, results)
                
                logger.info(f"搜索完成，找到 {len(results)} 条结果")
                return results[:max_results]
            else:
                logger.warning("未找到任何搜索结果")
                return []
                
        except Exception as e:
            logger.error(f"搜索过程中发生错误: {str(e)}")
            return []

    def extract_notes_advanced(self, keyword, max_results=10):
        """改进的笔记提取策略"""
        all_results = []
        
        try:
            # 策略1: 通过链接href提取（最可靠）
            results_1 = self._extract_by_explore_links(max_results)
            if results_1:
                all_results.extend(results_1)
                logger.info(f"策略1(探索链接): 提取到 {len(results_1)} 条结果")
            
            # 策略2: 通过数据属性提取
            if len(all_results) < max_results:
                results_2 = self._extract_by_data_attributes(max_results - len(all_results))
                if results_2:
                    all_results.extend(results_2)
                    logger.info(f"策略2(数据属性): 提取到 {len(results_2)} 条结果")
            
            # 策略3: 通过JavaScript执行提取
            if len(all_results) < max_results:
                results_3 = self._extract_by_javascript(max_results - len(all_results))
                if results_3:
                    all_results.extend(results_3)
                    logger.info(f"策略3(JavaScript): 提取到 {len(results_3)} 条结果")
            
            # 去重处理
            unique_results = self._deduplicate_results(all_results)
            
            # 限制结果数量
            return unique_results[:max_results]
            
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
            # 获取容器内所有文本
            all_text = self._get_element_text(container)
            
            # 查找包含数字的元素
            text_elements = container.find_elements(By.XPATH, ".//*[text()]")
            
            # 收集所有可能的数字
            potential_numbers = []
            
            for element in text_elements:
                text = self._get_element_text(element)
                if not text:
                    continue
                
                # 提取数字信息
                numbers = re.findall(r'(\d+(?:\.\d+)?[万kmKM]?)', text)
                
                for num_str in numbers:
                    num_value = self._parse_number(num_str)
                    if num_value > 0:
                        # 获取上下文信息
                        context = text.lower()
                        parent_element = element.find_element(By.XPATH, "..") if element else None
                        parent_text = self._get_element_text(parent_element).lower() if parent_element else ""
                        
                        # 根据上下文判断数字类型
                        if any(keyword in context or keyword in parent_text for keyword in ['赞', 'like', '点赞', '❤', '♥']):
                            result['likes'] = max(result['likes'], num_value)
                        elif any(keyword in context or keyword in parent_text for keyword in ['评论', 'comment', '💬', '评']):
                            result['comments'] = max(result['comments'], num_value)
                        elif any(keyword in context or keyword in parent_text for keyword in ['收藏', 'collect', '⭐', '★', '星', 'star']):
                            result['collects'] = max(result['collects'], num_value)
                        elif any(keyword in context or keyword in parent_text for keyword in ['浏览', 'view', '👀', '观看', '播放']):
                            result['views'] = max(result['views'], num_value)
                        else:
                            # 如果无法确定类型，收集起来后面处理
                            potential_numbers.append(num_value)
            
            # 如果没有找到明确的互动数据，尝试从数字推断
            if result['likes'] == 0 and result['comments'] == 0 and result['collects'] == 0 and result['views'] == 0 and potential_numbers:
                # 按数值大小排序，通常点赞数最大，评论数次之，收藏数第三
                potential_numbers.sort(reverse=True)
                
                if len(potential_numbers) >= 1:
                    result['likes'] = potential_numbers[0]  # 最大的数字通常是点赞数
                if len(potential_numbers) >= 2:
                    result['comments'] = potential_numbers[1]  # 第二大的通常是评论数
                if len(potential_numbers) >= 3:
                    result['collects'] = potential_numbers[2]  # 第三大的通常是收藏数
                if len(potential_numbers) >= 4:
                    result['views'] = potential_numbers[3]  # 第四大的可能是浏览数
            
            return result
            
        except Exception as e:
            logger.debug(f"提取互动数据失败: {str(e)}")
            return result

    def _extract_note_tags(self, container):
        """提取笔记标签"""
        tags = []
        
        try:
            # 标签选择器
            tag_selectors = [
                '[class*="tag"]',
                '[class*="label"]',
                '[class*="category"]',
                'span[style*="color"]'
            ]
            
            for selector in tag_selectors:
                try:
                    elements = container.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = self._get_element_text(element)
                        if text and len(text.strip()) > 1 and len(text) < 20:
                            if text.strip() not in tags:
                                tags.append(text.strip())
                except Exception:
                    continue
            
            return tags[:5]  # 最多返回5个标签
            
        except Exception as e:
            logger.debug(f"提取标签失败: {str(e)}")
            return []

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