#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
小红书后台静默爬虫
用于批量提取搜索结果中所有笔记的详细内容
"""

import os
import sys
import json
import time
import logging
import threading
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import urljoin

# 添加项目根目录到Python路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

# 导入必要的模块
import requests
from bs4 import BeautifulSoup

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('cache/logs/backend_crawler.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class BackendXHSCrawler:
    """后台小红书笔记内容爬虫 - 增强反反爬功能"""
    
    def __init__(self):
        """初始化爬虫"""
        # 使用项目根目录下的cache目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.cache_dir = os.path.join(project_root, "cache")
        self.notes_dir = os.path.join(self.cache_dir, "notes")
        self.cookies_file = os.path.join('cache', 'cookies', 'xiaohongshu_cookies.json')
        
        # 确保目录存在
        os.makedirs(self.notes_dir, exist_ok=True)
        os.makedirs('cache/logs', exist_ok=True)
        
        # 爬虫配置
        self.max_workers = 2  # 并发线程数（降低以避免被封）
        self.request_delay = 3  # 请求间隔（秒）
        self.timeout = 30  # 请求超时时间
        self.retry_count = 2  # 重试次数
        
        # 反爬虫配置
        self.human_behavior_config = {
            'min_wait_between_requests': 3,    # 最小等待时间（秒）
            'max_wait_between_requests': 8,    # 最大等待时间（秒）
            'scroll_pause_time': 2,            # 滚动停留时间
            'random_mouse_move': True,         # 随机鼠标移动
            'page_stay_time': (5, 15),        # 页面停留时间范围
            'retry_on_error': True,            # 遇到错误时重试
            'max_retries': 3,                  # 最大重试次数
        }
        
        # 统计信息
        self.stats = {
            'total_notes': 0,
            'success_count': 0,
            'failed_count': 0,
            'start_time': None,
            'end_time': None
        }
        
        self.driver = None
        logger.info("🚀 后台小红书爬虫初始化完成 - 增强反反爬功能")
    
    def start_batch_crawl(self, notes_data: List[Dict[str, Any]], session_id: str = None) -> Dict[str, Any]:
        """启动批量爬取任务"""
        if not session_id:
            session_id = f"batch_{int(time.time())}"
        
        self.stats['start_time'] = datetime.now()
        self.stats['total_notes'] = len(notes_data)
        
        logger.info(f"🎯 开始批量爬取任务")
        logger.info(f"📊 会话ID: {session_id}")
        logger.info(f"📝 待爬取笔记数量: {len(notes_data)}")
        logger.info(f"🔧 并发线程数: {self.max_workers}")
        logger.info(f"⏱️ 请求间隔: {self.request_delay}秒")
        
        # 创建会话目录
        session_dir = os.path.join(self.notes_dir, f"batch_{session_id}")
        os.makedirs(session_dir, exist_ok=True)
        
        # 保存任务信息
        task_info = {
            'session_id': session_id,
            'start_time': self.stats['start_time'].isoformat(),
            'total_notes': len(notes_data),
            'notes_list': notes_data
        }
        
        task_file = os.path.join(session_dir, 'task_info.json')
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task_info, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📁 任务信息已保存: {task_file}")
        
        # 使用线程池进行并发爬取
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_note = {
                executor.submit(self._crawl_single_note, note_data, session_id, i+1): note_data 
                for i, note_data in enumerate(notes_data)
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_note):
                note_data = future_to_note[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result['success']:
                        self.stats['success_count'] += 1
                        note_id_display = note_data.get('note_id') or note_data.get('id', 'N/A')
                        logger.info(f"✅ [{self.stats['success_count']}/{len(notes_data)}] 笔记爬取成功: {note_id_display}")
                    else:
                        self.stats['failed_count'] += 1
                        note_id_display = note_data.get('note_id') or note_data.get('id', 'N/A')
                        logger.error(f"❌ [{self.stats['failed_count']}/{len(notes_data)}] 笔记爬取失败: {note_id_display} - {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    self.stats['failed_count'] += 1
                    note_id_display = note_data.get('note_id') or note_data.get('id', 'N/A')
                    logger.error(f"❌ 笔记爬取异常: {note_id_display} - {str(e)}")
                    results.append({
                        'note_id': note_data.get('note_id') or note_data.get('id'),
                        'success': False,
                        'error': str(e)
                    })
                
                # 添加延迟避免请求过快
                time.sleep(self.request_delay)
        
        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        # 保存结果统计
        final_stats = {
            **self.stats,
            'start_time': self.stats['start_time'].isoformat(),
            'end_time': self.stats['end_time'].isoformat(),
            'duration_seconds': duration,
            'success_rate': self.stats['success_count'] / len(notes_data) * 100 if notes_data else 0,
            'results': results
        }
        
        stats_file = os.path.join(session_dir, 'crawl_stats.json')
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(final_stats, f, ensure_ascii=False, indent=2)
        
        # 输出最终统计
        logger.info("🎉 批量爬取任务完成!")
        logger.info(f"📊 总计: {len(notes_data)} 篇笔记")
        logger.info(f"✅ 成功: {self.stats['success_count']} 篇")
        logger.info(f"❌ 失败: {self.stats['failed_count']} 篇")
        logger.info(f"📈 成功率: {final_stats['success_rate']:.1f}%")
        logger.info(f"⏱️ 总耗时: {duration:.1f} 秒")
        logger.info(f"📁 结果保存在: {session_dir}")
        
        return final_stats
    
    def _crawl_single_note(self, note_data: Dict[str, Any], session_id: str, index: int) -> Dict[str, Any]:
        """爬取单个笔记的详细内容"""
        # 支持多种ID字段名格式
        note_id = note_data.get('note_id') or note_data.get('id')
        note_url = note_data.get('url') or note_data.get('link')
        
        if not note_id:
            logger.error(f"❌ [{index}] 笔记数据缺少ID字段，数据结构: {list(note_data.keys())}")
            return {'note_id': None, 'success': False, 'error': '缺少笔记ID'}
        
        logger.info(f"🔍 [{index}] 开始爬取笔记: {note_id}")
        
        # 重试机制
        for attempt in range(self.retry_count):
            try:
                if attempt > 0:
                    logger.info(f"🔄 [{index}] 第 {attempt + 1} 次重试: {note_id}")
                    time.sleep(attempt * 2)  # 递增延迟
                
                # 创建浏览器实例
                driver = self._create_browser_instance()
                if not driver:
                    raise Exception("无法创建浏览器实例")
                
                try:
                    # 加载cookies
                    self._load_cookies()
                    
                    # 构建笔记URL（添加必要的xsec参数）
                    xsec_token = note_data.get('xsec_token', '')
                    
                    if note_url and note_url.startswith('http'):
                        # 如果已有完整URL，检查是否包含xsec参数
                        if 'xsec_token' not in note_url and xsec_token:
                            separator = '&' if '?' in note_url else '?'
                            target_url = f"{note_url}{separator}xsec_source=pc_feed&xsec_token={xsec_token}"
                        else:
                            target_url = note_url
                    else:
                        # 构建完整URL并添加xsec参数
                        base_url = f"https://www.xiaohongshu.com/explore/{note_id}"
                        if xsec_token:
                            target_url = f"{base_url}?xsec_source=pc_feed&xsec_token={xsec_token}"
                        else:
                            target_url = base_url
                            logger.warning(f"⚠️ [{index}] 笔记 {note_id} 缺少xsec_token，可能影响访问成功率")
                    
                    logger.debug(f"🌐 [{index}] 访问URL: {target_url}")
                    
                    # 访问笔记页面
                    driver.get(target_url)
                    
                    # 等待页面加载
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    
                    # 等待内容加载
                    time.sleep(3)
                    
                    # 获取页面源码
                    page_source = driver.page_source
                    
                    # 保存页面源码
                    source_file = self._save_page_source(note_id, page_source, session_id, index)
                    
                    # 解析页面内容
                    note_detail = self._parse_note_content(page_source, note_id, session_id, index)
                    
                    # 下载图片
                    images = self._download_note_images_from_source(page_source, note_id, session_id, index)
                    note_detail['images'] = images
                    
                    # 保存笔记详情
                    detail_file = self._save_note_detail(note_detail, note_id, session_id, index)
                    
                    logger.info(f"✅ [{index}] 笔记爬取完成: {note_id}")
                    logger.info(f"📄 [{index}] 标题: {note_detail.get('title', 'N/A')[:50]}...")
                    logger.info(f"📝 [{index}] 内容长度: {len(note_detail.get('content', ''))} 字符")
                    logger.info(f"🏷️ [{index}] 标签数量: {len(note_detail.get('tags', []))}")
                    logger.info(f"🖼️ [{index}] 图片数量: {len(images)}")
                    
                    return {
                        'note_id': note_id,
                        'success': True,
                        'source_file': source_file,
                        'detail_file': detail_file,
                        'images_count': len(images),
                        'title': note_detail.get('title', ''),
                        'content_length': len(note_detail.get('content', '')),
                        'tags_count': len(note_detail.get('tags', []))
                    }
                    
                finally:
                    driver.quit()
                    
            except Exception as e:
                logger.error(f"❌ [{index}] 爬取失败 (尝试 {attempt + 1}/{self.retry_count}): {note_id} - {str(e)}")
                if attempt == self.retry_count - 1:  # 最后一次尝试
                    return {
                        'note_id': note_id,
                        'success': False,
                        'error': str(e),
                        'attempts': attempt + 1
                    }
        
        return {'note_id': note_id, 'success': False, 'error': '所有重试均失败'}
    
    def _create_browser_instance(self):
        """创建浏览器实例"""
        try:
            from selenium.webdriver.chrome.service import Service
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 无头模式
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # 智能选择ChromeDriver
            service = None
            
            # 1. 尝试使用本地ChromeDriver
            driver_paths = [
                'drivers/chromedriver-mac-arm64/chromedriver',
                'drivers/chromedriver',
                '/usr/local/bin/chromedriver',
                '/opt/homebrew/bin/chromedriver'
            ]
            
            for driver_path in driver_paths:
                if os.path.exists(driver_path):
                    try:
                        service = Service(executable_path=driver_path)
                        driver = webdriver.Chrome(service=service, options=chrome_options)
                        logger.debug(f"使用本地ChromeDriver: {driver_path}")
                        return driver
                    except Exception as e:
                        logger.debug(f"使用路径 {driver_path} 创建驱动失败: {str(e)}")
                        continue
            
            # 2. 使用webdriver-manager自动下载（优先级提高）
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                # 使用中国镜像源加速下载
                os.environ['WDM_LOCAL'] = '1'  # 本地存储
                driver_path = ChromeDriverManager().install()
                service = Service(driver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.debug(f"使用webdriver-manager下载的ChromeDriver: {driver_path}")
                return driver
            except Exception as e:
                logger.debug(f"webdriver-manager下载失败: {str(e)}")
            
            # 3. 最后尝试系统PATH中的chromedriver
            try:
                driver = webdriver.Chrome(options=chrome_options)
                logger.debug("使用系统PATH中的chromedriver")
                return driver
            except Exception as e:
                logger.debug(f"使用系统PATH中的chromedriver失败: {str(e)}")
            
            return None
            
        except Exception as e:
            logger.error(f"创建浏览器实例失败: {str(e)}")
            return None
    
    def _load_cookies(self):
        """加载cookies"""
        try:
            if os.path.exists(self.cookies_file):
                with open(self.cookies_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                
                # 先访问小红书主页
                self.driver.get("https://www.xiaohongshu.com")
                time.sleep(2)
                
                # 添加cookies
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        logger.debug(f"添加cookie失败: {e}")
                
                logger.debug("✅ cookies加载完成")
            else:
                logger.warning("⚠️ cookies文件不存在")
        except Exception as e:
            logger.error(f"❌ 加载cookies失败: {str(e)}")
    
    def _save_page_source(self, note_id: str, page_source: str, session_id: str, index: int) -> str:
        """保存页面源码"""
        try:
            filename = f"{index:03d}_{note_id}_source.html"
            session_dir = os.path.join(self.notes_dir, f"batch_{session_id}")
            file_path = os.path.join(session_dir, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(page_source)
            
            logger.debug(f"页面源码已保存: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"保存页面源码失败: {str(e)}")
            return ""
    
    def _parse_note_content(self, page_source: str, note_id: str, session_id: str, index: int) -> Dict[str, Any]:
        """解析笔记内容"""
        try:
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # 提取标题
            title = self._extract_title(soup)
            
            # 提取内容
            content = self._extract_content(soup)
            
            # 提取标签
            tags = self._extract_tags(soup)
            
            # 提取作者信息
            author = self._extract_author(soup)
            
            return {
                'note_id': note_id,
                'title': title,
                'content': content,
                'tags': tags,
                'author': author,
                'crawl_time': datetime.now().isoformat(),
                'session_id': session_id,
                'index': index
            }
            
        except Exception as e:
            logger.error(f"解析笔记内容失败: {str(e)}")
            return {
                'note_id': note_id,
                'title': '解析失败',
                'content': '解析失败',
                'tags': [],
                'author': '未知',
                'error': str(e)
            }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取标题"""
        try:
            # 尝试多种选择器
            title_selectors = [
                'h1.title',
                '.note-title',
                '[data-testid="note-title"]',
                'h1',
                '.content-title',
                'title'
            ]
            
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element and element.get_text(strip=True):
                    title = element.get_text(strip=True)
                    return title
            
            # 从页面title标签提取
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)
                # 清理标题
                title = title.replace(' - 小红书', '').replace(' | 小红书', '').strip()
                if title:
                    return title
            
            return "未找到标题"
            
        except Exception as e:
            logger.error(f"提取标题失败: {str(e)}")
            return "标题提取失败"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取内容"""
        try:
            # 尝试多种选择器
            content_selectors = [
                '.note-content',
                '.content-text',
                '[data-testid="note-content"]',
                '.desc',
                '.note-desc',
                '.content-desc'
            ]
            
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element and element.get_text(strip=True):
                    content = element.get_text(strip=True)
                    return content
            
            # 尝试从script标签中提取JSON数据
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'window.__INITIAL_STATE__' in script.string:
                    try:
                        # 提取JSON数据
                        json_start = script.string.find('{')
                        json_end = script.string.rfind('}') + 1
                        if json_start != -1 and json_end != -1:
                            json_str = script.string[json_start:json_end]
                            data = json.loads(json_str)
                            
                            # 在JSON中查找内容
                            content = self._extract_content_from_json(data)
                            if content:
                                return content
                    except:
                        continue
            
            return "未找到内容"
            
        except Exception as e:
            logger.error(f"提取内容失败: {str(e)}")
            return "内容提取失败"
    
    def _extract_content_from_json(self, data: dict) -> str:
        """从JSON数据中提取内容"""
        try:
            def search_content(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key in ['desc', 'content', 'text', 'title'] and isinstance(value, str) and len(value) > 10:
                            return value
                        result = search_content(value, f"{path}.{key}")
                        if result:
                            return result
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        result = search_content(item, f"{path}[{i}]")
                        if result:
                            return result
                return None
            
            return search_content(data) or ""
            
        except Exception as e:
            logger.error(f"从JSON提取内容失败: {str(e)}")
            return ""
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """提取标签"""
        try:
            tags = []
            
            # 尝试多种选择器
            tag_selectors = [
                '.tag',
                '.hashtag',
                '.topic',
                '[data-testid="tag"]',
                '.note-tag',
                '.topic-tag'
            ]
            
            for selector in tag_selectors:
                elements = soup.select(selector)
                for element in elements:
                    tag_text = element.get_text(strip=True)
                    if tag_text and tag_text not in tags:
                        # 清理标签文本
                        tag_text = tag_text.replace('#', '').strip()
                        if tag_text:
                            tags.append(tag_text)
            
            # 从文本中提取#标签
            text_content = soup.get_text()
            hashtag_pattern = r'#([^#\s]+)'
            import re
            hashtags = re.findall(hashtag_pattern, text_content)
            for tag in hashtags:
                if tag not in tags:
                    tags.append(tag)
            
            return tags[:10]  # 最多返回10个标签
            
        except Exception as e:
            logger.error(f"提取标签失败: {str(e)}")
            return []
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """提取作者信息"""
        try:
            # 尝试多种选择器
            author_selectors = [
                '.author-name',
                '.user-name',
                '[data-testid="author"]',
                '.note-author',
                '.username'
            ]
            
            for selector in author_selectors:
                element = soup.select_one(selector)
                if element and element.get_text(strip=True):
                    author = element.get_text(strip=True)
                    return author
            
            return "未知作者"
            
        except Exception as e:
            logger.error(f"提取作者失败: {str(e)}")
            return "作者提取失败"
    
    def _download_note_images_from_source(self, page_source: str, note_id: str, session_id: str, index: int) -> List[Dict[str, str]]:
        """从页面源码下载笔记图片"""
        try:
            soup = BeautifulSoup(page_source, 'html.parser')
            images = []
            
            # 创建图片目录
            session_dir = os.path.join(self.notes_dir, f"batch_{session_id}")
            images_dir = os.path.join(session_dir, f"{index:03d}_{note_id}_images")
            os.makedirs(images_dir, exist_ok=True)
            
            # 查找图片元素
            img_elements = soup.find_all('img')
            
            for i, img in enumerate(img_elements):
                src = img.get('src') or img.get('data-src') or img.get('data-original')
                if not src:
                    continue
                
                # 过滤掉小图标和无关图片
                if any(keyword in src.lower() for keyword in ['icon', 'avatar', 'logo', 'button']):
                    continue
                
                # 确保是完整URL
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = 'https://www.xiaohongshu.com' + src
                
                # 下载图片
                image_info = self._download_single_image(src, images_dir, f"{index:03d}_{note_id}_{i}")
                if image_info:
                    images.append(image_info)
            
            logger.debug(f"下载了 {len(images)} 张图片")
            return images
            
        except Exception as e:
            logger.error(f"下载图片失败: {str(e)}")
            return []
    
    def _download_single_image(self, url: str, save_dir: str, filename_prefix: str) -> Optional[Dict[str, str]]:
        """下载单张图片"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.xiaohongshu.com/'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 确定文件扩展名
            content_type = response.headers.get('content-type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'png' in content_type:
                ext = '.png'
            elif 'webp' in content_type:
                ext = '.webp'
            else:
                ext = '.jpg'  # 默认
            
            filename = f"{filename_prefix}{ext}"
            file_path = os.path.join(save_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # 生成Web访问路径
            relative_path = os.path.relpath(file_path, self.temp_dir)
            web_path = f"/temp/{relative_path.replace(os.sep, '/')}"
            
            return {
                'original_url': url,
                'local_path': file_path,
                'web_path': web_path,
                'filename': filename
            }
            
        except Exception as e:
            logger.debug(f"下载图片失败 {url}: {str(e)}")
            return None
    
    def _save_note_detail(self, note_detail: Dict[str, Any], note_id: str, session_id: str, index: int) -> str:
        """保存笔记详情"""
        try:
            filename = f"{index:03d}_{note_id}_detail.json"
            session_dir = os.path.join(self.notes_dir, f"batch_{session_id}")
            file_path = os.path.join(session_dir, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(note_detail, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"笔记详情已保存: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"保存笔记详情失败: {str(e)}")
            return ""

    def create_stealth_driver(self):
        """创建隐蔽性浏览器驱动"""
        try:
            chrome_options = Options()
            
            # 基础反检测配置
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 模拟真实浏览器环境
            user_agents = [
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            chrome_options.add_argument(f'--user-agent={random.choice(user_agents)}')
            
            # 其他隐蔽性设置
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            
            # 窗口大小随机化
            window_sizes = ['1366,768', '1920,1080', '1440,900', '1280,720']
            chrome_options.add_argument(f'--window-size={random.choice(window_sizes)}')
            
            # 创建驱动
            driver = webdriver.Chrome(options=chrome_options)
            
            # 执行反检测脚本
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['zh-CN', 'zh', 'en']
                    });
                    window.chrome = {
                        runtime: {}
                    };
                '''
            })
            
            logger.info("✅ 创建隐蔽性浏览器驱动成功")
            return driver
            
        except Exception as e:
            logger.error(f"❌ 创建浏览器驱动失败: {str(e)}")
            raise
    
    def simulate_human_behavior(self, driver):
        """模拟人类浏览行为"""
        try:
            # 随机鼠标移动
            if self.human_behavior_config['random_mouse_move']:
                action = ActionChains(driver)
                # 获取页面尺寸
                page_width = driver.execute_script("return window.innerWidth")
                page_height = driver.execute_script("return window.innerHeight")
                
                # 随机移动鼠标
                for _ in range(random.randint(1, 3)):
                    x = random.randint(100, page_width - 100)
                    y = random.randint(100, page_height - 100)
                    action.move_by_offset(x, y).perform()
                    time.sleep(random.uniform(0.5, 1.5))
            
            # 随机滚动
            scroll_times = random.randint(1, 3)
            for _ in range(scroll_times):
                scroll_height = random.randint(200, 800)
                driver.execute_script(f"window.scrollBy(0, {scroll_height});")
                time.sleep(random.uniform(1, 2))
            
            # 页面停留时间
            stay_time = random.uniform(*self.human_behavior_config['page_stay_time'])
            logger.debug(f"🎭 模拟人类行为: 页面停留 {stay_time:.1f} 秒")
            time.sleep(stay_time)
            
        except Exception as e:
            logger.warning(f"⚠️ 模拟人类行为时出现异常: {str(e)}")
    
    def smart_wait_between_requests(self):
        """智能等待策略"""
        base_wait = random.uniform(
            self.human_behavior_config['min_wait_between_requests'],
            self.human_behavior_config['max_wait_between_requests']
        )
        
        # 根据时间段调整等待时间（夜间延长等待）
        current_hour = datetime.now().hour
        if 23 <= current_hour or current_hour <= 6:  # 夜间
            base_wait *= 1.5
        elif 12 <= current_hour <= 14:  # 午休时间
            base_wait *= 1.2
        
        logger.debug(f"⏱️ 智能等待: {base_wait:.1f} 秒")
        time.sleep(base_wait)
    
    def extract_note_content_with_retry(self, note_url, session_id, retries=0):
        """带重试机制的笔记内容提取"""
        max_retries = self.human_behavior_config['max_retries']
        
        if retries >= max_retries:
            logger.error(f"❌ 达到最大重试次数 ({max_retries})，放弃提取: {note_url}")
            return None
        
        try:
            if retries > 0:
                logger.info(f"🔄 第 {retries + 1} 次尝试提取笔记: {note_url}")
                # 重试前等待更长时间
                extended_wait = random.uniform(10, 20)
                logger.info(f"⏳ 重试前等待 {extended_wait:.1f} 秒...")
                time.sleep(extended_wait)
            
            # 创建新的驱动（每次重试使用新的浏览器实例）
            if self.driver:
                self.driver.quit()
            
            self.driver = self.create_stealth_driver()
            
            # 加载cookies
            self._load_cookies()
            
            # 智能等待
            self.smart_wait_between_requests()
            
            logger.info(f"🌐 正在访问笔记页面: {note_url}")
            
            # 访问页面
            self.driver.get(note_url)
            
            # 模拟人类浏览行为
            self.simulate_human_behavior(self.driver)
            
            # 检查是否遇到"你访问的笔记不见了"
            page_source = self.driver.page_source
            error_indicators = [
                "你访问的笔记不见了",
                "页面不存在",
                "内容已删除",
                "access denied",
                "网络异常"
            ]
            
            for error in error_indicators:
                if error in page_source:
                    logger.warning(f"⚠️ 检测到错误页面: {error}")
                    if self.human_behavior_config['retry_on_error']:
                        return self.extract_note_content_with_retry(note_url, session_id, retries + 1)
                    else:
                        return None
            
            # 等待页面加载完成
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 提取内容
            content = self._extract_note_details()
            
            # 保存页面源码用于调试
            self._save_page_source(note_url, session_id)
            
            logger.info(f"✅ 成功提取笔记内容")
            return content
            
        except TimeoutException:
            logger.warning(f"⏰ 页面加载超时: {note_url}")
            if self.human_behavior_config['retry_on_error']:
                return self.extract_note_content_with_retry(note_url, session_id, retries + 1)
            return None
            
        except Exception as e:
            logger.error(f"❌ 提取笔记内容时出错: {str(e)}")
            if self.human_behavior_config['retry_on_error'] and "你访问的笔记不见了" not in str(e):
                return self.extract_note_content_with_retry(note_url, session_id, retries + 1)
            return None
    
    def batch_extract_notes(self, note_links, session_id):
        """批量提取笔记内容 - 采用人为行为模式"""
        if not note_links:
            logger.warning("⚠️ 没有提供笔记链接")
            return []
        
        results = []
        total_notes = len(note_links)
        
        logger.info(f"📋 开始批量提取 {total_notes} 个笔记内容（人为行为模式）")
        
        for i, note_url in enumerate(note_links, 1):
            try:
                logger.info(f"📖 正在处理第 {i}/{total_notes} 个笔记")
                
                # 提取笔记内容（带重试机制）
                content = self.extract_note_content_with_retry(note_url, session_id)
                
                if content:
                    results.append({
                        'url': note_url,
                        'content': content,
                        'extracted_at': datetime.now().isoformat()
                    })
                    logger.info(f"✅ 第 {i} 个笔记提取成功")
                else:
                    logger.warning(f"❌ 第 {i} 个笔记提取失败")
                
                # 每处理几个笔记后进行更长时间的休息
                if i % 5 == 0 and i < total_notes:
                    long_break = random.uniform(30, 60)
                    logger.info(f"😴 处理了 {i} 个笔记，休息 {long_break:.1f} 秒...")
                    time.sleep(long_break)
                
            except KeyboardInterrupt:
                logger.info("🛑 用户中断批量提取")
                break
            except Exception as e:
                logger.error(f"❌ 处理第 {i} 个笔记时出错: {str(e)}")
                continue
        
        # 清理资源
        if self.driver:
            self.driver.quit()
            self.driver = None
        
        logger.info(f"🎉 批量提取完成，成功提取 {len(results)}/{total_notes} 个笔记")
        
        # 保存结果
        self._save_batch_results(results, session_id)
        
        return results

    def _extract_note_details(self):
        """提取笔记详细信息"""
        try:
            content = {}
            
            # 提取标题
            try:
                title_element = self.driver.find_element(By.CSS_SELECTOR, ".note-detail-wrapper .title")
                content['title'] = title_element.text.strip()
            except:
                content['title'] = ""
            
            # 提取正文内容
            try:
                desc_element = self.driver.find_element(By.CSS_SELECTOR, ".note-detail-wrapper .desc")
                content['description'] = desc_element.text.strip()
            except:
                content['description'] = ""
            
            # 提取作者信息
            try:
                author_element = self.driver.find_element(By.CSS_SELECTOR, ".author-wrapper .author-name")
                content['author'] = author_element.text.strip()
            except:
                content['author'] = ""
            
            # 提取点赞数、收藏数等
            try:
                stats_elements = self.driver.find_elements(By.CSS_SELECTOR, ".note-detail-wrapper .count")
                content['stats'] = [elem.text.strip() for elem in stats_elements]
            except:
                content['stats'] = []
            
            # 提取图片链接
            try:
                img_elements = self.driver.find_elements(By.CSS_SELECTOR, ".note-detail-wrapper img")
                content['images'] = [img.get_attribute('src') for img in img_elements if img.get_attribute('src')]
            except:
                content['images'] = []
            
            return content
            
        except Exception as e:
            logger.error(f"❌ 提取笔记详情失败: {str(e)}")
            return {}
    
    def _save_page_source(self, note_url, session_id):
        """保存页面源码用于调试"""
        try:
            # 从URL中提取note_id
            note_id = note_url.split('/')[-1] if '/' in note_url else 'unknown'
            
            # 创建文件名
            filename = f"{note_id}_{session_id}_source.html"
            filepath = os.path.join(self.notes_dir, filename)
            
            # 保存页面源码
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            logger.debug(f"📁 页面源码已保存: {filepath}")
            
        except Exception as e:
            logger.warning(f"⚠️ 保存页面源码失败: {str(e)}")
    
    def _save_batch_results(self, results, session_id):
        """保存批量提取结果"""
        try:
            filename = f"batch_{session_id}_results.json"
            filepath = os.path.join(self.notes_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 批量提取结果已保存: {filepath}")
            
        except Exception as e:
            logger.error(f"❌ 保存批量结果失败: {str(e)}")

def start_backend_crawl(notes_data: List[Dict[str, Any]], session_id: str = None) -> Dict[str, Any]:
    """
    启动后台爬取任务的入口函数 - 使用人为行为模式
    
    Args:
        notes_data: 笔记数据列表
        session_id: 会话ID
        
    Returns:
        Dict: 爬取结果统计
    """
    try:
        logger.info(f"🚀 启动后台爬虫任务（人为行为模式），共 {len(notes_data)} 个笔记")
        
        # 创建爬虫实例
        crawler = BackendXHSCrawler()
        
        # 提取笔记链接并添加必要的xsec参数
        note_links = []
        for note in notes_data:
            note_url = None
            xsec_token = note.get('xsec_token', '')
            note_id = note.get('note_id') or note.get('id', '')
            
            # 获取基础URL
            if 'link' in note and note['link']:
                note_url = note['link']
            elif 'url' in note and note['url']:
                note_url = note['url']
            elif 'note_url' in note and note['note_url']:
                note_url = note['note_url']
            elif note_id:
                # 如果没有URL但有note_id，构建基础URL
                note_url = f"https://www.xiaohongshu.com/explore/{note_id}"
            
            if note_url:
                # 添加xsec参数（如果还没有的话）
                if 'xsec_token' not in note_url and xsec_token:
                    separator = '&' if '?' in note_url else '?'
                    note_url = f"{note_url}{separator}xsec_source=pc_feed&xsec_token={xsec_token}"
                    logger.debug(f"🔗 为笔记 {note_id} 添加xsec参数")
                elif not xsec_token:
                    logger.warning(f"⚠️ 笔记 {note_id} 缺少xsec_token，可能影响访问成功率")
                
                note_links.append(note_url)
        
        if not note_links:
            logger.warning("⚠️ 没有找到有效的笔记链接")
            return {
                'success': False,
                'error': '没有有效的笔记链接',
                'total_crawled': 0,
                'success_count': 0,
                'failed_count': 0
            }
        
        # 使用新的人为行为模式进行批量提取
        results = crawler.batch_extract_notes(note_links, session_id)
        
        success_count = len([r for r in results if r.get('content')])
        failed_count = len(note_links) - success_count
        
        return {
            'success': True,
            'total_crawled': len(note_links),
            'success_count': success_count,
            'failed_count': failed_count,
            'results': results,
            'session_id': session_id
        }
        
    except Exception as e:
        logger.error(f"❌ 后台爬虫任务失败: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'total_crawled': 0,
            'success_count': 0,
            'failed_count': 0
        }

if __name__ == '__main__':
    # 测试用例
    test_notes = [
        {
            'note_id': '65a1b2c3d4e5f6789abcdef0', 
            'url': 'https://www.xiaohongshu.com/explore/65a1b2c3d4e5f6789abcdef0',
            'xsec_token': 'XYZ123456789ABC'
        },
        {
            'note_id': '65a1b2c3d4e5f6789abcdef1', 
            'url': 'https://www.xiaohongshu.com/explore/65a1b2c3d4e5f6789abcdef1',
            'xsec_token': 'ABC987654321XYZ'
        },
    ]
    
    result = start_backend_crawl(test_notes, "test_session")
    print(json.dumps(result, ensure_ascii=False, indent=2)) 