#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书笔记内容提取器 - 生产版本
基于HTML页面技术分析，实现高效的笔记内容提取
支持批量处理和多种数据源
"""

import json
import re
import os
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from urllib.parse import unquote, urlparse

# 配置日志
logger = logging.getLogger(__name__)

class NoteContentExtractor:
    """小红书笔记内容提取器 - 生产版本"""
    
    def __init__(self, cache_dir: str = "cache/notes"):
        """
        初始化提取器
        
        Args:
            cache_dir: 缓存目录路径
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据字段映射配置
        self._setup_field_mappings()
        
        # 统计信息
        self.stats = {
            'processed': 0,
            'success': 0,
            'failed': 0,
            'start_time': None
        }
    
    def _setup_field_mappings(self):
        """设置字段映射配置"""
        
        # JSON数据字段映射
        self.json_fields_mapping = {
            'title': ['title', 'noteTitle', 'desc'],
            'content': ['content', 'desc', 'description'],
            'note_id': ['noteId', 'id', 'note_id'],
            'user_id': ['userId', 'user_id', 'authorId'],
            'images': ['images', 'imageList', 'pics'],
            'video': ['video', 'videoUrl'],
            'tags': ['tags', 'tagList'],
            'like_count': ['likes', 'likeCount', 'interactInfo'],
            'collect_count': ['collects', 'collectCount'],
            'comment_count': ['comments', 'commentCount'],
        }
        
        # HTML选择器映射
        self.html_selectors = {
            'title': ['.note-content .title', '.title', 'h1', '[class*="title"]'],
            'content': ['.note-content .desc', '.desc', '[class*="desc"]', '[class*="content"]'],
            'author_name': ['.author-wrapper .name', '.author .name', '[class*="author"]'],
            'like_count': ['.like-wrapper .count', '[class*="like"] .count'],
            'collect_count': ['.collect-wrapper .count', '[class*="collect"] .count'],
            'comment_count': ['.comments-container .total', '[class*="comment"] .total'],
        }
        
        # 正则表达式模式
        self.regex_patterns = {
            'note_id': [r'/explore/([a-f0-9]{24})'],
            'user_id': [r'userId["\']?\s*[:=]\s*["\']?([a-f0-9]{24})'],
            'title': [r'<title[^>]*>([^<]+)</title>'],
            'image_urls': [r'src=["\']([^"\']+xhscdn[^"\']*)["\']'],
        }
        
        # Meta标签映射
        self.meta_mappings = {
            'og:title': 'meta_title',
            'og:description': 'meta_description',
            'og:image': 'meta_image',
            'og:url': 'meta_url',
            'description': 'page_description',
            'keywords': 'page_keywords',
        }
    
    def extract_from_html_file(self, html_file_path: str) -> Optional[Dict[str, Any]]:
        """
        从HTML文件提取笔记内容
        
        Args:
            html_file_path: HTML文件路径
            
        Returns:
            提取的笔记数据，失败返回None
        """
        try:
            # 读取HTML文件
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            return self.extract_from_html_content(html_content, html_file_path)
            
        except Exception as e:
            logger.error(f"读取HTML文件失败 {html_file_path}: {e}")
            return None
    
    def extract_from_html_content(self, html_content: str, source_file: str = None) -> Optional[Dict[str, Any]]:
        """
        从HTML内容提取笔记数据
        
        Args:
            html_content: HTML内容
            source_file: 源文件路径（用于日志）
            
        Returns:
            提取的笔记数据
        """
        self.stats['processed'] += 1
        
        try:
            logger.info(f"开始提取笔记内容，HTML大小: {len(html_content)} 字符")
            
            # 按优先级提取数据
            all_data = {}
            
            # 1. 尝试JSON数据提取
            json_data = self._extract_from_json(html_content)
            if json_data:
                all_data.update(json_data)
                logger.info(f"JSON提取成功: {len(json_data)} 个字段")
            
            # 2. HTML结构解析
            html_data = self._extract_from_html_structure(html_content)
            if html_data:
                # 合并数据，已有的不覆盖
                for key, value in html_data.items():
                    if key not in all_data or not all_data[key]:
                        all_data[key] = value
                logger.info(f"HTML解析成功: {len(html_data)} 个字段")
            
            # 3. 正则表达式提取
            regex_data = self._extract_with_regex(html_content)
            if regex_data:
                for key, value in regex_data.items():
                    if key not in all_data or not all_data[key]:
                        all_data[key] = value
                logger.info(f"正则提取成功: {len(regex_data)} 个字段")
            
            # 数据清洗和验证
            cleaned_data = self._clean_and_validate_data(all_data)
            
            # 添加元数据
            cleaned_data['extraction_info'] = {
                'source_file': source_file,
                'extracted_at': datetime.now().isoformat(),
                'extractor_version': '1.0.0',
                'fields_count': len(cleaned_data) - 1,  # 减去extraction_info
            }
            
            self.stats['success'] += 1
            logger.info(f"✅ 笔记内容提取成功，共提取 {len(cleaned_data)-1} 个字段")
            
            return cleaned_data
            
        except Exception as e:
            self.stats['failed'] += 1
            logger.error(f"❌ 笔记内容提取失败: {e}")
            return None
    
    def _extract_from_json(self, html_content: str) -> Dict[str, Any]:
        """从JSON数据提取信息"""
        data = {}
        
        try:
            # 查找window.__INITIAL_STATE__
            pattern = r'window\.__INITIAL_STATE__\s*=\s*({.*?});'
            match = re.search(pattern, html_content, re.DOTALL)
            
            if match:
                json_str = match.group(1)
                try:
                    initial_state = json.loads(json_str)
                    data.update(self._parse_json_structure(initial_state))
                except json.JSONDecodeError:
                    # 尝试修复JSON
                    fixed_data = self._try_fix_json(json_str)
                    if fixed_data:
                        data.update(fixed_data)
            
            # 查找其他可能的JSON数据
            other_patterns = [
                r'window\.__NUXT__\s*=\s*({.*?});',
                r'window\.initialData\s*=\s*({.*?});',
                r'window\.pageData\s*=\s*({.*?});',
            ]
            
            for pattern in other_patterns:
                match = re.search(pattern, html_content, re.DOTALL)
                if match:
                    try:
                        json_data = json.loads(match.group(1))
                        data.update(self._parse_json_structure(json_data))
                    except:
                        continue
                        
        except Exception as e:
            logger.warning(f"JSON数据提取失败: {e}")
        
        return data
    
    def _parse_json_structure(self, json_data: Any) -> Dict[str, Any]:
        """解析JSON数据结构"""
        data = {}
        
        try:
            # 递归搜索关键字段
            def search_fields(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        # 检查是否是目标字段
                        for target_field, possible_keys in self.json_fields_mapping.items():
                            if key in possible_keys and value:
                                data[target_field] = value
                        
                        # 递归搜索
                        if isinstance(value, (dict, list)):
                            search_fields(value, f"{path}.{key}" if path else key)
                            
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        if isinstance(item, dict):
                            search_fields(item, f"{path}[{i}]")
            
            search_fields(json_data)
            
        except Exception as e:
            logger.warning(f"JSON结构解析失败: {e}")
        
        return data
    
    def _try_fix_json(self, json_str: str) -> Optional[Dict[str, Any]]:
        """尝试修复损坏的JSON"""
        fixes = [
            lambda s: re.sub(r'[,;]\s*$', '', s.strip()),
            lambda s: s.replace("'", '"'),
            lambda s: re.sub(r',\s*}', '}', s),
            lambda s: re.sub(r',\s*]', ']', s),
        ]
        
        for fix_func in fixes:
            try:
                fixed_json = fix_func(json_str)
                data = json.loads(fixed_json)
                return self._parse_json_structure(data)
            except:
                continue
        
        return None
    
    def _extract_from_html_structure(self, html_content: str) -> Dict[str, Any]:
        """从HTML结构提取数据"""
        data = {}
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取文本数据
            for field, selectors in self.html_selectors.items():
                for selector in selectors:
                    elements = soup.select(selector)
                    if elements:
                        text = elements[0].get_text(strip=True)
                        if text:
                            data[field] = text
                            break
            
            # 提取图片
            images = self._extract_images(soup)
            if images:
                data['images'] = images
            
            # 提取Meta标签
            meta_data = self._extract_meta_tags(soup)
            data.update(meta_data)
            
            # 提取标签信息
            tags = self._extract_tags(soup)
            if tags:
                data['tags'] = tags
            
        except Exception as e:
            logger.warning(f"HTML结构解析失败: {e}")
        
        return data
    
    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """提取图片URL"""
        images = []
        
        selectors = [
            '.swiper-slide img',
            '.media-container img', 
            'img[src*="xhscdn"]',
            '[style*="background-image"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                # 获取图片URL
                src = element.get('src') or element.get('data-src')
                
                # 从style属性中提取background-image
                if not src and element.get('style'):
                    style = element.get('style')
                    bg_match = re.search(r'background-image:\s*url\(["\']?([^"\'()]+)["\']?\)', style)
                    if bg_match:
                        src = bg_match.group(1)
                
                if src and 'xhscdn' in src and src not in images:
                    images.append(src)
        
        # 去重并过滤头像图片
        filtered_images = []
        for img in images:
            # 过滤掉头像图片（通常包含avatar关键词）
            if 'avatar' not in img.lower() and len(filtered_images) < 20:
                filtered_images.append(img)
        
        return filtered_images
    
    def _extract_meta_tags(self, soup: BeautifulSoup) -> Dict[str, str]:
        """提取Meta标签信息"""
        data = {}
        
        for meta_name, field_name in self.meta_mappings.items():
            selectors = [
                f'meta[property="{meta_name}"]',
                f'meta[name="{meta_name}"]',
            ]
            
            for selector in selectors:
                meta_tag = soup.select_one(selector)
                if meta_tag:
                    content = meta_tag.get('content')
                    if content:
                        data[field_name] = content
                        break
        
        return data
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """提取标签信息"""
        tags = []
        
        tag_selectors = [
            '.tag', '[class*="tag"]', '.topic', '[class*="topic"]'
        ]
        
        for selector in tag_selectors:
            elements = soup.select(selector)
            for element in elements:
                tag_text = element.get_text(strip=True)
                if tag_text and tag_text.startswith('#') and tag_text not in tags:
                    tags.append(tag_text)
        
        return tags[:10]  # 限制标签数量
    
    def _extract_with_regex(self, html_content: str) -> Dict[str, Any]:
        """使用正则表达式提取数据"""
        data = {}
        
        try:
            for field, patterns in self.regex_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, html_content, re.IGNORECASE)
                    if matches:
                        if field in ['image_urls']:
                            # 去重并限制数量
                            unique_matches = list(set(matches))[:15]
                            # 过滤掉明显不是内容图片的URL
                            if field == 'image_urls':
                                filtered = [url for url in unique_matches 
                                          if 'xhscdn' in url and 'avatar' not in url.lower()]
                                if filtered:
                                    data[field] = filtered
                        else:
                            data[field] = matches[0]
                        break
                        
        except Exception as e:
            logger.warning(f"正则表达式提取失败: {e}")
        
        return data
    
    def _clean_and_validate_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗和验证数据"""
        cleaned_data = {}
        
        for key, value in raw_data.items():
            try:
                if key in ['like_count', 'collect_count', 'comment_count']:
                    # 清理数字字段
                    if isinstance(value, str):
                        # 提取数字
                        number_match = re.search(r'(\d+)', value)
                        if number_match:
                            cleaned_data[key] = int(number_match.group(1))
                    elif isinstance(value, (int, float)):
                        cleaned_data[key] = int(value)
                        
                elif key in ['title', 'content', 'author_name']:
                    # 清理文本字段
                    if isinstance(value, str):
                        cleaned_text = value.strip()
                        # 移除HTML标签
                        cleaned_text = re.sub(r'<[^>]+>', '', cleaned_text)
                        # 移除多余的空白字符
                        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
                        if cleaned_text:
                            cleaned_data[key] = cleaned_text
                            
                elif key in ['images', 'tags', 'image_urls']:
                    # 清理列表字段
                    if isinstance(value, list):
                        cleaned_list = [item for item in value if item and str(item).strip()]
                        if cleaned_list:
                            cleaned_data[key] = cleaned_list
                            
                else:
                    # 其他字段直接赋值
                    if value:
                        cleaned_data[key] = value
                        
            except Exception as e:
                logger.warning(f"清洗字段 {key} 失败: {e}")
                continue
        
        return cleaned_data
    
    def save_extracted_data(self, note_data: Dict[str, Any], note_id: str = None) -> str:
        """
        保存提取的数据到JSON文件
        
        Args:
            note_data: 笔记数据
            note_id: 笔记ID（可选）
            
        Returns:
            保存的文件路径
        """
        try:
            # 生成文件名
            if note_id:
                filename = f"{note_id}_extracted.json"
            else:
                # 使用数据哈希作为文件名
                data_hash = hashlib.md5(json.dumps(note_data, sort_keys=True).encode()).hexdigest()
                filename = f"note_{data_hash}_extracted.json"
            
            file_path = self.cache_dir / filename
            
            # 保存数据
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(note_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 数据已保存到: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"❌ 保存数据失败: {e}")
            raise
    
    def batch_extract_from_cache(self, pattern: str = "*.html") -> List[Dict[str, Any]]:
        """
        批量处理缓存目录中的HTML文件
        
        Args:
            pattern: 文件匹配模式
            
        Returns:
            提取结果列表
        """
        self.stats['start_time'] = datetime.now()
        results = []
        
        try:
            html_files = list(self.cache_dir.glob(pattern))
            logger.info(f"找到 {len(html_files)} 个HTML文件待处理")
            
            for html_file in html_files:
                logger.info(f"处理文件: {html_file.name}")
                
                extracted_data = self.extract_from_html_file(str(html_file))
                if extracted_data:
                    # 保存提取的数据
                    note_id = extracted_data.get('note_id')
                    saved_path = self.save_extracted_data(extracted_data, note_id)
                    
                    extracted_data['saved_path'] = saved_path
                    results.append(extracted_data)
                    
                    logger.info(f"✅ 成功处理: {html_file.name}")
                else:
                    logger.warning(f"⚠️ 处理失败: {html_file.name}")
                    
        except Exception as e:
            logger.error(f"❌ 批量处理失败: {e}")
        
        # 输出统计信息
        self._print_stats()
        
        return results
    
    def _print_stats(self):
        """打印统计信息"""
        if self.stats['start_time']:
            duration = datetime.now() - self.stats['start_time']
            logger.info("\n" + "="*50)
            logger.info("📊 处理统计")
            logger.info("="*50)
            logger.info(f"总处理数: {self.stats['processed']}")
            logger.info(f"成功数: {self.stats['success']}")
            logger.info(f"失败数: {self.stats['failed']}")
            logger.info(f"成功率: {self.stats['success']/max(self.stats['processed'], 1)*100:.1f}%")
            logger.info(f"处理时间: {duration.total_seconds():.1f} 秒")
            logger.info("="*50)

def main():
    """主函数 - 用于测试"""
    import sys
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    extractor = NoteContentExtractor()
    
    if len(sys.argv) > 1:
        # 处理指定文件
        html_file = sys.argv[1]
        logger.info(f"处理文件: {html_file}")
        
        extracted_data = extractor.extract_from_html_file(html_file)
        if extracted_data:
            note_id = extracted_data.get('note_id')
            saved_path = extractor.save_extracted_data(extracted_data, note_id)
            print(f"✅ 提取成功，保存到: {saved_path}")
        else:
            print("❌ 提取失败")
    else:
        # 批量处理
        logger.info("开始批量处理缓存目录中的HTML文件")
        results = extractor.batch_extract_from_cache()
        print(f"✅ 批量处理完成，共处理 {len(results)} 个文件")

if __name__ == "__main__":
    main() 