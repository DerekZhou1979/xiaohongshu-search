"""
小红书笔记内容生成器
负责分析原笔记内容并使用大模型生成新的同类笔记内容
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import re
import random
import requests
import hashlib
from urllib.parse import urlparse, urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NoteContentGenerator:
    """笔记内容生成器"""
    
    def __init__(self):
        """初始化生成器"""
        # 使用项目根目录下的cache目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.cache_dir = os.path.join(project_root, "cache")
        self.debug_dir = os.path.join(self.cache_dir, "note_generation_debug")
        self.notes_dir = os.path.join(self.cache_dir, "notes")
        
        # 确保目录存在
        os.makedirs(self.debug_dir, exist_ok=True)
        os.makedirs(self.notes_dir, exist_ok=True)
        
        # 初始化大模型设置（这里使用模拟，实际可以接入OpenAI, Claude等）
        self.ai_enabled = False  # 默认关闭，可以通过环境变量开启
        
        # Cookie文件路径
        self.cookies_file = os.path.join('cache', 'cookies', 'xiaohongshu_cookies.json')
        
        logger.info("笔记内容生成器初始化完成")
    
    def generate_similar_note(self, original_note: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据原笔记生成同类笔记内容
        
        Args:
            original_note: 原笔记信息，包含title, content, tags等
            
        Returns:
            Dict: 生成的笔记内容，包含title, content, tags, suggestions等
        """
        try:
            logger.info(f"开始生成同类笔记，原笔记ID: {original_note.get('note_id')}")
            
            # 创建debug会话
            session_id = self._create_debug_session(original_note)
            
            # 获取原笔记的完整内容（通过代理访问）
            note_detail = self._fetch_note_detail(original_note.get('note_id'), session_id)
            self._save_debug_info(session_id, "note_detail", note_detail)
            
            # 分析原笔记内容
            analysis_result = self._analyze_original_note(note_detail if note_detail.get('success') else original_note)
            self._save_debug_info(session_id, "analysis", analysis_result)
            
            # 生成新笔记内容
            source_note = note_detail if note_detail.get('success') else original_note
            if self.ai_enabled:
                generated_note = self._generate_with_ai(source_note, analysis_result)
            else:
                generated_note = self._generate_with_templates(source_note, analysis_result)
            
            self._save_debug_info(session_id, "generated_note", generated_note)
            
            # 添加生成时间和会话ID
            generated_note['generated_at'] = datetime.now().isoformat()
            generated_note['debug_session_id'] = session_id
            
            # 添加原笔记详细信息
            if note_detail and note_detail.get('success'):
                generated_note['original_note_detail'] = {
                    'title': note_detail.get('title', ''),
                    'content': note_detail.get('content', ''),
                    'tags': note_detail.get('tags', []),
                    'images': note_detail.get('images', []),
                    'author': note_detail.get('author', ''),
                    'note_id': original_note.get('note_id', ''),
                    'source_file': note_detail.get('source_file', ''),
                    'images_dir': note_detail.get('images_dir', '')
                }
            
            logger.info(f"笔记生成完成，会话ID: {session_id}")
            return generated_note
            
        except Exception as e:
            logger.error(f"生成同类笔记失败: {str(e)}")
            raise
    
    def _create_debug_session(self, original_note: Dict[str, Any]) -> str:
        """创建debug会话"""
        session_id = f"note_gen_{int(time.time())}_{random.randint(1000, 9999)}"
        
        session_info = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "original_note_id": original_note.get('note_id', 'unknown'),
            "original_note_title": original_note.get('title', '未知标题'),
            "status": "started"
        }
        
        session_file = os.path.join(self.debug_dir, f"{session_id}_session.json")
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_info, f, ensure_ascii=False, indent=2)
        
        return session_id
    
    def _save_debug_info(self, session_id: str, step: str, data: Any):
        """保存debug信息"""
        try:
            debug_file = os.path.join(self.debug_dir, f"{session_id}_{step}.json")
            debug_data = {
                "session_id": session_id,
                "step": step,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            
            with open(debug_file, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存debug信息失败: {str(e)}")
    
    def _analyze_original_note(self, original_note: Dict[str, Any]) -> Dict[str, Any]:
        """分析原笔记内容"""
        title = original_note.get('title', '')
        content = original_note.get('content', '')
        tags = original_note.get('tags', [])
        
        analysis = {
            "content_type": self._detect_content_type(title, content),
            "tone": self._detect_tone(title, content), 
            "topics": self._extract_topics(title, content),
            "keywords": self._extract_keywords(title, content),
            "structure": self._analyze_structure(content),
            "engagement_elements": self._find_engagement_elements(title, content),
            "original_tags": tags
        }
        
        return analysis
    
    def _detect_content_type(self, title: str, content: str) -> str:
        """检测内容类型"""
        text = (title + " " + content).lower()
        
        if any(word in text for word in ['教程', '攻略', '步骤', '方法', '如何', '怎么']):
            return "教程攻略"
        elif any(word in text for word in ['分享', '推荐', '种草', '好物', '值得']):
            return "分享推荐"
        elif any(word in text for word in ['穿搭', '搭配', '服装', '衣服', '时尚']):
            return "穿搭时尚"
        elif any(word in text for word in ['美食', '吃', '餐厅', '菜谱', '料理']):
            return "美食"
        elif any(word in text for word in ['旅行', '旅游', '景点', '打卡', '出行']):
            return "旅行"
        elif any(word in text for word in ['护肤', '化妆', '美妆', '保养', '护理']):
            return "美妆护肤"
        elif any(word in text for word in ['生活', '日常', 'vlog', '记录']):
            return "生活日常"
        else:
            return "综合分享"
    
    def _detect_tone(self, title: str, content: str) -> str:
        """检测语调风格"""
        text = (title + " " + content).lower()
        
        if any(word in text for word in ['！', '!', '哇', '太好了', '超级', '巨']):
            return "活泼兴奋"
        elif any(word in text for word in ['温柔', '轻松', '舒适', '静谧']):
            return "温柔治愈"
        elif any(word in text for word in ['专业', '建议', '推荐', '分析']):
            return "专业理性"
        elif any(word in text for word in ['可爱', '萌', '小仙女', '宝贝']):
            return "可爱甜美"
        else:
            return "自然亲和"
    
    def _extract_topics(self, title: str, content: str) -> List[str]:
        """提取主题关键词"""
        text = title + " " + content
        
        # 简单的主题提取逻辑
        topics = []
        
        # 常见主题关键词
        topic_keywords = {
            "美食": ["美食", "吃", "餐厅", "菜谱", "料理", "小食", "甜品"],
            "穿搭": ["穿搭", "服装", "衣服", "搭配", "时尚", "风格"],
            "护肤": ["护肤", "保养", "肌肤", "面膜", "精华", "乳液"],
            "化妆": ["化妆", "彩妆", "口红", "眼影", "粉底", "美妆"],
            "旅行": ["旅行", "旅游", "景点", "打卡", "出行", "度假"],
            "生活": ["生活", "日常", "家居", "收纳", "整理"],
            "学习": ["学习", "读书", "知识", "技能", "提升"],
            "健身": ["健身", "运动", "锻炼", "瑜伽", "减肥"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text for keyword in keywords):
                topics.append(topic)
        
        return topics[:3]  # 最多返回3个主题
    
    def _extract_keywords(self, title: str, content: str) -> List[str]:
        """提取关键词"""
        text = title + " " + content
        
        # 简单的关键词提取（实际项目中可以使用更sophisticated的NLP技术）
        keywords = []
        
        # 使用正则表达式提取可能的关键词
        # 这里简化处理，提取一些常见的名词性短语
        try:
            import jieba
            # 分词
            words = jieba.lcut(text)
            
            # 过滤词汇
            filtered_words = [
                word for word in words 
                if len(word) >= 2 and word not in ['的', '是', '在', '有', '和', '与', '了', '着', '过']
            ]
            
            # 统计词频（简化版）
            word_freq = {}
            for word in filtered_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # 按频率排序，取前8个
            keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:8]
            keywords = [word[0] for word in keywords]
            
        except:
            # 如果jieba不可用，使用简单的方法
            keywords = re.findall(r'[\u4e00-\u9fff]{2,4}', text)[:8]
        
        return keywords
    
    def _fetch_note_detail(self, note_id: str, session_id: str) -> Dict[str, Any]:
        """
        通过代理方式获取笔记详细内容
        
        Args:
            note_id: 笔记ID
            session_id: 会话ID
            
        Returns:
            Dict: 包含笔记详细信息的字典
        """
        try:
            logger.info(f"开始获取笔记详情: {note_id}")
            
            # 构建笔记URL
            note_url = f"https://www.xiaohongshu.com/explore/{note_id}"
            
            # 创建浏览器实例
            driver = self._create_browser_instance()
            if not driver:
                return {"success": False, "error": "无法创建浏览器实例"}
            
            try:
                # 加载cookies
                self._load_cookies_to_browser(driver)
                
                # 访问笔记页面
                logger.info(f"访问笔记页面: {note_url}")
                driver.get(note_url)
                
                # 等待页面加载
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # 等待内容加载
                time.sleep(3)
                
                # 获取页面源码
                page_source = driver.page_source
                
                # 保存页面源码
                source_file = self._save_page_source(note_id, page_source, session_id)
                
                # 解析页面内容
                note_detail = self._parse_note_content(page_source, note_id, session_id)
                note_detail['source_file'] = source_file
                note_detail['success'] = True
                
                logger.info(f"笔记详情获取成功: {note_id}")
                return note_detail
                
            finally:
                driver.quit()
                
        except Exception as e:
            logger.error(f"获取笔记详情失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _create_browser_instance(self):
        """创建浏览器实例"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # 尝试不同的ChromeDriver路径
            driver_paths = [
                'drivers/chromedriver-mac-arm64/chromedriver',
                'drivers/chromedriver',
                '/usr/local/bin/chromedriver',
                '/opt/homebrew/bin/chromedriver'
            ]
            
            for driver_path in driver_paths:
                if os.path.exists(driver_path):
                    from selenium.webdriver.chrome.service import Service
                    service = Service(driver_path)
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    return driver
            
            # 如果没有找到指定路径，尝试系统PATH中的chromedriver
            driver = webdriver.Chrome(options=chrome_options)
            return driver
            
        except Exception as e:
            logger.error(f"创建浏览器实例失败: {str(e)}")
            return None
    
    def _load_cookies_to_browser(self, driver):
        """加载cookies到浏览器"""
        try:
            if os.path.exists(self.cookies_file):
                # 先访问主页以设置域名
                driver.get("https://www.xiaohongshu.com")
                time.sleep(1)
                
                with open(self.cookies_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                
                for cookie in cookies:
                    try:
                        driver.add_cookie(cookie)
                    except Exception as e:
                        logger.debug(f"添加cookie失败: {str(e)}")
                        continue
                
                logger.info("Cookies加载完成")
            else:
                logger.warning("Cookies文件不存在")
                
        except Exception as e:
            logger.error(f"加载cookies失败: {str(e)}")
    
    def _save_page_source(self, note_id: str, page_source: str, session_id: str) -> str:
        """保存页面源码"""
        try:
            filename = f"{note_id}_{session_id}_source.html"
            file_path = os.path.join(self.notes_dir, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(page_source)
            
            logger.info(f"页面源码已保存: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"保存页面源码失败: {str(e)}")
            return ""
    
    def _parse_note_content(self, page_source: str, note_id: str, session_id: str) -> Dict[str, Any]:
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
            
            # 下载并保存图片
            images = self._download_note_images(soup, note_id, session_id)
            
            return {
                'title': title,
                'content': content,
                'tags': tags,
                'author': author,
                'images': images,
                'images_dir': os.path.join(self.notes_dir, f"{note_id}_{session_id}_images")
            }
            
        except Exception as e:
            logger.error(f"解析笔记内容失败: {str(e)}")
            return {
                'title': '',
                'content': '',
                'tags': [],
                'author': '',
                'images': []
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
                    logger.info(f"提取到标题: {title[:50]}...")
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
                    logger.info(f"提取到内容: {len(content)} 字符")
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
            hashtags = re.findall(hashtag_pattern, text_content)
            for tag in hashtags:
                if tag not in tags:
                    tags.append(tag)
            
            logger.info(f"提取到标签: {tags}")
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
                    logger.info(f"提取到作者: {author}")
                    return author
            
            return "未知作者"
            
        except Exception as e:
            logger.error(f"提取作者失败: {str(e)}")
            return "作者提取失败"
    
    def _download_note_images(self, soup: BeautifulSoup, note_id: str, session_id: str) -> List[Dict[str, str]]:
        """下载笔记图片"""
        try:
            images = []
            images_dir = os.path.join(self.notes_dir, f"{note_id}_{session_id}_images")
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
                image_info = self._download_single_image(src, images_dir, f"{note_id}_{i}")
                if image_info:
                    images.append(image_info)
            
            logger.info(f"下载了 {len(images)} 张图片")
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
            web_path = f"/cache/notes/{os.path.basename(save_dir)}/{filename}"
            
            return {
                'original_url': url,
                'local_path': file_path,
                'web_path': web_path,
                'filename': filename
            }
            
        except Exception as e:
            logger.error(f"下载图片失败 {url}: {str(e)}")
            return None
    
    def _analyze_structure(self, content: str) -> Dict[str, Any]:
        """分析内容结构"""
        lines = content.split('\n')
        
        structure = {
            "line_count": len(lines),
            "has_list": '•' in content or '·' in content or any(line.strip().startswith(('1.', '2.', '3.')) for line in lines),
            "has_emoji": bool(re.search(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', content)),
            "paragraph_count": len([line for line in lines if line.strip()]),
            "avg_line_length": sum(len(line) for line in lines) / max(len(lines), 1)
        }
        
        return structure
    
    def _find_engagement_elements(self, title: str, content: str) -> List[str]:
        """找出吸引人的元素"""
        text = title + " " + content
        elements = []
        
        # 检测各种吸引人的元素
        if '?' in text or '？' in text:
            elements.append("互动问句")
        
        if any(word in text for word in ['分享', '推荐', '必买', '必看']):
            elements.append("推荐语气")
            
        if any(word in text for word in ['超级', '巨', '特别', '非常']):
            elements.append("强调词汇")
            
        if re.search(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', text):
            elements.append("表情符号")
            
        if any(word in text for word in ['攻略', '秘籍', '技巧', '妙招']):
            elements.append("实用价值")
        
        return elements
    
    def _generate_with_templates(self, original_note: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """使用模板生成新笔记内容（当AI不可用时的备选方案）"""
        
        content_type = analysis['content_type']
        tone = analysis['tone']
        topics = analysis['topics']
        keywords = analysis['keywords']
        
        # 根据内容类型选择模板
        templates = self._get_templates_by_type(content_type)
        selected_template = random.choice(templates)
        
        # 生成标题
        title = self._generate_title_from_template(selected_template, topics, keywords, tone)
        
        # 生成内容
        content = self._generate_content_from_template(selected_template, original_note, analysis)
        
        # 生成标签
        tags = self._generate_tags(topics, keywords, analysis['original_tags'])
        
        # 生成创作建议
        suggestions = self._generate_suggestions(content_type, tone, analysis)
        
        return {
            "title": title,
            "content": content,
            "tags": tags,
            "suggestions": suggestions,
            "generation_method": "template_based",
            "content_type": content_type,
            "tone": tone
        }
    
    def _generate_with_ai(self, original_note: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """使用大模型生成新笔记内容（需要配置AI API）"""
        # 这里是AI生成的接口，需要根据实际使用的大模型进行实现
        # 比如OpenAI GPT, Claude, 或者本地模型等
        
        # 暂时返回模板生成的结果
        logger.info("AI生成功能暂未配置，使用模板生成")
        return self._generate_with_templates(original_note, analysis)
    
    def _get_templates_by_type(self, content_type: str) -> List[Dict[str, Any]]:
        """根据内容类型获取模板"""
        
        templates = {
            "教程攻略": [
                {
                    "title_patterns": [
                        "{topic}新手必看！{keyword}详细教程来啦📚",
                        "超实用{topic}攻略！{keyword}这样做就对了✨",
                        "{keyword}完整教程分享，{topic}小白也能学会🎯"
                    ],
                    "content_structure": "intro_problem_solution_tips_conclusion"
                }
            ],
            "分享推荐": [
                {
                    "title_patterns": [
                        "真的好用！{keyword}分享给大家💕",
                        "又发现了{topic}好物！{keyword}强烈推荐✨",
                        "忍不住要推荐的{keyword}，{topic}爱好者必入🛒"
                    ],
                    "content_structure": "discovery_features_experience_recommendation"
                }
            ]
        }
        
        return templates.get(content_type, [
            {
                "title_patterns": [
                    "分享一个{keyword}，关于{topic}的小心得💡",
                    "{keyword}体验分享！{topic}真的不错👍",
                    "今天来聊聊{topic}，{keyword}心得分享✨"
                ],
                "content_structure": "general_sharing"
            }
        ])
    
    def _generate_title_from_template(self, template: Dict[str, Any], topics: List[str], keywords: List[str], tone: str) -> str:
        """从模板生成标题"""
        
        title_patterns = template['title_patterns']
        selected_pattern = random.choice(title_patterns)
        
        # 选择合适的topic和keyword
        topic = topics[0] if topics else "生活"
        keyword = keywords[0] if keywords else "分享"
        
        # 根据季节添加额外信息
        season = self._get_current_season()
        
        # 替换占位符
        title = selected_pattern.format(
            topic=topic,
            keyword=keyword,  
            season=season
        )
        
        return title
    
    def _generate_content_from_template(self, template: Dict[str, Any], original_note: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """从模板生成内容"""
        
        keywords = analysis['keywords']
        topics = analysis['topics']
        
        topic = topics[0] if topics else "这个方法"
        keyword = keywords[0] if keywords else "技巧"
        
        content = f"""今天来分享一个关于{topic}的实用{keyword}！

🤔 遇到的问题：
很多朋友都在问关于{topic}的问题，特别是{keyword}方面的困惑。

💡 解决方案：
经过我的实践总结，发现了一个特别好用的方法：

1️⃣ 首先，要了解{keyword}的基本原理
2️⃣ 然后，准备必要的工具和材料  
3️⃣ 按照步骤一步步操作
4️⃣ 注意关键细节，避免常见错误

✨ 实用小贴士：
• 建议初学者从简单的开始
• 多练习几次就能熟练掌握
• 有问题随时交流讨论

希望这个分享对大家有帮助！有什么问题欢迎评论区讨论～

#实用教程 #{topic} #{keyword}"""
        
        return content
    
    def _generate_tags(self, topics: List[str], keywords: List[str], original_tags: List[str]) -> List[str]:
        """生成标签"""
        
        tags = []
        
        # 添加主题相关标签
        for topic in topics[:2]:  # 最多2个主题标签
            tags.append(topic)
        
        # 添加关键词标签
        for keyword in keywords[:3]:  # 最多3个关键词标签
            if keyword not in tags:
                tags.append(keyword)
        
        # 添加一些通用标签
        general_tags = ["生活分享", "实用推荐", "日常记录", "心得体会", "经验分享"]
        tags.append(random.choice(general_tags))
        
        # 去重并限制数量
        unique_tags = list(dict.fromkeys(tags))[:8]  # 最多8个标签
        
        return unique_tags
    
    def _generate_suggestions(self, content_type: str, tone: str, analysis: Dict[str, Any]) -> str:
        """生成创作建议"""
        
        suggestions = []
        
        # 根据内容类型给建议
        if content_type == "教程攻略":
            suggestions.append("可以添加步骤图片或视频，让教程更直观")
            suggestions.append("记得在开头说明难度等级和所需时间")
        elif content_type == "分享推荐":
            suggestions.append("可以添加产品细节图片，增加可信度")
            suggestions.append("分享购买链接或渠道信息会更实用")
        
        # 通用建议
        suggestions.extend([
            "适当添加表情符号和换行，让版面更清晰",
            "在评论区多与读者互动，提高笔记热度"
        ])
        
        return " | ".join(suggestions[:4])  # 最多4条建议
    
    def _get_current_season(self) -> str:
        """获取当前季节"""
        month = datetime.now().month
        
        if month in [12, 1, 2]:
            return "冬季"
        elif month in [3, 4, 5]:
            return "春季"
        elif month in [6, 7, 8]:
            return "夏季"
        else:
            return "秋季"
    
    def get_debug_info(self, session_id: str) -> Dict[str, Any]:
        """获取debug信息"""
        debug_info = {}
        
        try:
            # 读取会话信息
            session_file = os.path.join(self.debug_dir, f"{session_id}_session.json")
            if os.path.exists(session_file):
                with open(session_file, 'r', encoding='utf-8') as f:
                    debug_info['session'] = json.load(f)
            
            # 读取分析结果
            analysis_file = os.path.join(self.debug_dir, f"{session_id}_analysis.json")
            if os.path.exists(analysis_file):
                with open(analysis_file, 'r', encoding='utf-8') as f:
                    debug_info['analysis'] = json.load(f)
            
            # 读取生成结果
            generated_file = os.path.join(self.debug_dir, f"{session_id}_generated_note.json")
            if os.path.exists(generated_file):
                with open(generated_file, 'r', encoding='utf-8') as f:
                    debug_info['generated_note'] = json.load(f)
                    
        except Exception as e:
            logger.error(f"获取debug信息失败: {str(e)}")
        
        return debug_info
    
    def cleanup_old_debug_files(self, days: int = 7):
        """清理旧的debug文件"""
        try:
            current_time = time.time()
            cutoff_time = current_time - (days * 24 * 60 * 60)
            
            for filename in os.listdir(self.debug_dir):
                file_path = os.path.join(self.debug_dir, filename)
                if os.path.getmtime(file_path) < cutoff_time:
                    os.remove(file_path)
                    logger.info(f"删除旧debug文件: {filename}")
                    
        except Exception as e:
            logger.error(f"清理debug文件失败: {str(e)}") 