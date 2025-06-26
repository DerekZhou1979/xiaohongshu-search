#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一数据提取器 - 整合所有提取方法的统一接口
"""

import os
import re
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup

# 配置日志
logger = logging.getLogger(__name__)

class UnifiedExtractor:
    """统一数据提取器"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 提取策略配置
        self.strategies = {
            'enhanced': True,
            'precise': True,
            'content': True,
            'hybrid': True
        }
        
        # 统计信息
        self.stats = {
            'processed': 0,
            'success': 0,
            'failed': 0,
            'start_time': None,
            'strategy_stats': {}
        }
    
    def extract_from_html_files(self, pattern: str = "*.html", max_files: int = None) -> List[Dict[str, Any]]:
        """从HTML文件批量提取笔记数据"""
        self.stats['start_time'] = datetime.now()
        results = []
        
        try:
            # 先在results目录中查找HTML文件
            results_dir = self.cache_dir / "results"
            temp_dir = self.cache_dir / "temp"
            
            html_files = []
            
            # 优先从results目录查找
            if results_dir.exists():
                html_files.extend(list(results_dir.glob(pattern)))
                logger.info(f"在results目录找到 {len(html_files)} 个HTML文件")
            
            # 然后从temp目录查找
            if temp_dir.exists():
                temp_files = list(temp_dir.glob(pattern))
                html_files.extend(temp_files)
                logger.info(f"在temp目录找到 {len(temp_files)} 个HTML文件")
            
            if not html_files:
                logger.warning(f"在 {results_dir} 和 {temp_dir} 中都未找到HTML文件")
                return []
            
            if max_files:
                html_files = html_files[:max_files]
            
            logger.info(f"总共找到 {len(html_files)} 个HTML文件待处理")
            
            for html_file in html_files:
                logger.info(f"处理文件: {html_file.name}")
                
                extracted_data = self.extract_from_html_file_hybrid(str(html_file))
                
                if extracted_data and extracted_data.get('notes'):
                    results.extend(extracted_data['notes'])
                    logger.info(f"✅ 成功提取: {len(extracted_data['notes'])} 条笔记")
                else:
                    logger.warning(f"⚠️ 提取失败: {html_file.name}")
                    
        except Exception as e:
            logger.error(f"❌ 批量提取失败: {e}")
        
        self._print_stats()
        return results
    
    def extract_from_html_file_hybrid(self, html_file_path: str) -> Optional[Dict[str, Any]]:
        """使用混合策略从HTML文件提取数据"""
        self.stats['processed'] += 1
        
        try:
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
            logger.info(f"开始混合策略提取: {os.path.basename(html_file_path)}")
            
            all_results = {}
            
            # 策略1: 精准容器提取
            if self.strategies['precise']:
                try:
                    precise_results = self._extract_precise_containers(html_content, html_file_path)
                    if precise_results and precise_results.get('notes'):
                        all_results['precise'] = precise_results
                        logger.info(f"✅ 精准容器策略: {len(precise_results['notes'])} 条")
                except Exception as e:
                    logger.error(f"❌ 精准容器策略失败: {e}")
            
            # 选择最佳结果
            best_result = self._select_best_result(all_results)
            
            if best_result:
                best_result['extraction_info'] = {
                    'source_file': html_file_path,
                    'extracted_at': datetime.now().isoformat(),
                    'extractor_version': '2.0.0',
                    'strategies_used': list(all_results.keys()),
                    'best_strategy': best_result.get('extraction_method', 'unknown')
                }
                
                self.stats['success'] += 1
                return best_result
            else:
                self.stats['failed'] += 1
                return None
                
        except Exception as e:
            logger.error(f"❌ 混合策略提取失败: {e}")
            self.stats['failed'] += 1
            return None
    
    def _extract_precise_containers(self, html_content: str, source_file: str) -> Optional[Dict[str, Any]]:
        """精准容器提取策略"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 方法1: 查找带有data-note-id的note-card
            note_cards = soup.find_all('div', class_='note-card')
            note_containers = []
            
            for card in note_cards:
                note_id = card.get('data-note-id')
                if note_id:
                    note_containers.append({
                        'note_id': note_id,
                        'link_href': f'/explore/{note_id}',
                        'container': card,
                        'link_element': card
                    })
            
            # 方法2: 如果没有找到note-card，则查找传统的explore链接
            if not note_containers:
                explore_links = soup.find_all('a', href=re.compile(r'/explore/'))
                
                for link in explore_links:
                    href = link.get('href', '')
                    note_id_match = re.search(r'/explore/([a-f0-9]{24})', href)
                    
                    if note_id_match:
                        note_id = note_id_match.group(1)
                        
                        # 向上查找包含此链接的容器
                        container = link
                        for _ in range(5):
                            parent = container.parent
                            if parent:
                                container = parent
                                images = container.find_all('img')
                                if images:
                                    break
                        
                        note_containers.append({
                            'note_id': note_id,
                            'link_href': href,
                            'container': container,
                            'link_element': link
                        })
            
            logger.info(f"找到 {len(note_containers)} 个笔记容器")
            
            # 从每个容器提取详细信息
            extracted_notes = []
            
            for i, container_info in enumerate(note_containers):
                note_id = container_info['note_id']
                container = container_info['container']
                
                # 提取图片
                images = container.find_all('img')
                image_urls = []
                
                for img in images:
                    src = img.get('src', '')
                    if 'xhscdn.com' in src:
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = 'https://www.xiaohongshu.com' + src
                        image_urls.append(src)
                
                # 提取标题
                title_element = container.find('h3', class_='note-title') or container.find('.note-title')
                title = title_element.get_text(strip=True) if title_element else self._extract_title_from_container(container_info, "", i)
                
                # 提取描述
                desc_element = container.find('p', class_='note-desc') or container.find('.note-desc')
                description = desc_element.get_text(strip=True) if desc_element else ""
                
                # 提取作者
                author_element = container.find('div', class_='note-author')
                if author_element:
                    author_text = author_element.get_text(strip=True)
                    # 移除@符号，保留作者名称，去除粉丝数等数字后缀
                    author = re.sub(r'^@', '', author_text).strip()
                    # 去除可能的粉丝数（如"1千"、"3万"等）
                    author = re.sub(r'\s*\d+[千万kKwW]*\s*$', '', author).strip()
                    author = author or "未知作者"
                else:
                    author = "未知作者"
                
                # 提取互动数据
                stats = self._extract_stats_from_container(container)
                
                # 提取文本内容
                text_content = container.get_text(separator=' ', strip=True)
                
                # 构建完整链接
                full_link = f"https://www.xiaohongshu.com{container_info['link_href']}"
                
                note_data = {
                    'note_id': note_id,
                    'title': title or '未知标题',
                    'desc': description or title or '暂无描述',
                    'link': full_link,
                    'cover': image_urls[0] if image_urls else '',
                    'cover_image': image_urls[0] if image_urls else '',
                    'images': image_urls,
                    'author': author,
                    'content': description or text_content[:200] + "..." if len(text_content) > 200 else text_content,
                    'likes': stats.get('likes', 0),
                    'comments': stats.get('comments', 0),
                    'collects': stats.get('collects', 0),
                    'like_count': stats.get('likes', 0),
                    'comment_count': stats.get('comments', 0),
                    'collect_count': stats.get('collects', 0),
                    'tags': ['小红书搜索'],
                    'raw_text': text_content,
                    'method': 'precise_containers',
                    'published': '',
                    'avatar': ''
                }
                
                extracted_notes.append(note_data)
            
            return {
                "count": len(extracted_notes),
                "notes": extracted_notes,
                "message": f"精准容器提取到{len(extracted_notes)}条笔记数据",
                "status": "success",
                "extraction_method": "precise_containers"
            }
            
        except Exception as e:
            logger.error(f"精准容器提取失败: {e}")
            return None
    
    def _select_best_result(self, all_results: Dict) -> Optional[Dict[str, Any]]:
        """选择最佳提取结果"""
        if not all_results:
            return None
        
        # 策略优先级：精准容器 > 增强提取 > 内容结构
        priority_order = ['precise', 'enhanced', 'content']
        
        for strategy in priority_order:
            if strategy in all_results:
                result = all_results[strategy]
                notes = result.get('notes', [])
                
                # 验证结果质量
                if self._validate_result_quality(notes):
                    logger.info(f"✅ 选择最佳策略: {strategy} ({len(notes)} 条笔记)")
                    return result
        
        # 如果没有高质量结果，返回数量最多的
        if all_results:
            best_strategy = max(all_results.keys(), key=lambda k: len(all_results[k].get('notes', [])))
            logger.info(f"⚠️ 选择数量最多的策略: {best_strategy}")
            return all_results[best_strategy]
        
        return None
    
    def _validate_result_quality(self, notes: List[Dict]) -> bool:
        """验证结果质量"""
        if not notes:
            return False
        
        # 检查基本字段完整性
        valid_count = 0
        for note in notes:
            if (note.get('note_id') and 
                note.get('title') and 
                note.get('link') and
                len(note.get('note_id', '')) == 24):  # 小红书ID长度
                valid_count += 1
        
        # 至少50%的笔记有效
        quality_rate = valid_count / len(notes)
        return quality_rate >= 0.5
    
    def _extract_title_from_container(self, container_info: Dict, text_content: str, index: int) -> str:
        """从容器提取标题"""
        # 方法1：查找链接文本
        link_text = container_info['link_element'].get_text(strip=True)
        if link_text and len(link_text) > 3:
            return link_text
        
        # 方法2：查找容器中的关键词文本
        text_lines = text_content.split()
        for line in text_lines:
            if any(keyword in line for keyword in ['老庙', '黄金', '珠宝']) and 5 < len(line) < 50:
                return line
        
        # 方法3：使用默认格式
        return f"小红书笔记 #{index+1}"
    
    def _extract_author_from_text(self, text_content: str) -> str:
        """从文本中提取作者信息"""
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
    
    def _extract_stats_from_container(self, container) -> Dict[str, int]:
        """从容器中提取互动统计数据"""
        stats = {'likes': 0, 'comments': 0, 'collects': 0, 'shares': 0}
        
        try:
            # 查找统计数据容器
            stats_container = container.find('div', class_='note-stats')
            if stats_container:
                stat_items = stats_container.find_all('span', class_='stat-item')
                
                for item in stat_items:
                    icon = item.find('i')
                    text = item.get_text(strip=True)
                    
                    # 提取数字
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        count = int(numbers[0])
                        
                        # 根据图标类型判断统计类型
                        if icon:
                            icon_class = icon.get('class', [])
                            if 'fa-heart' in icon_class:
                                stats['likes'] = count
                            elif 'fa-comment' in icon_class:
                                stats['comments'] = count
                            elif 'fa-star' in icon_class:
                                stats['collects'] = count
                            elif 'fa-share' in icon_class:
                                stats['shares'] = count
                
        except Exception as e:
            logger.debug(f"提取统计数据失败: {e}")
        
        return stats
    
    def save_unified_results(self, results: List[Dict[str, Any]], keyword: str = "search") -> str:
        """保存统一格式的结果"""
        try:
            # 构建API响应格式
            api_response = {
                "keyword": keyword,
                "count": len(results),
                "notes": results,
                "message": f"统一提取器成功提取{len(results)}条笔记数据",
                "status": "success",
                "extraction_info": {
                    "extractor_version": "2.0.0",
                    "processed_at": datetime.now().isoformat(),
                    "strategies_used": list(set(note.get('method', 'unknown') for note in results))
                }
            }
            
            # 保存JSON结果
            json_file = self.cache_dir / f"unified_extracted_{keyword}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(api_response, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 统一结果已保存到: {json_file}")
            return str(json_file)
            
        except Exception as e:
            logger.error(f"❌ 保存统一结果失败: {e}")
            raise
    
    def _generate_html_preview(self, results: List[Dict[str, Any]], keyword: str) -> str:
        """生成HTML预览页面"""
        try:
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>统一提取器结果 - {keyword}</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5;
        }}
        .header {{ 
            text-align: center; margin-bottom: 30px; 
            background: linear-gradient(135deg, #667eea, #764ba2); color: white;
            padding: 30px; border-radius: 16px; box-shadow: 0 8px 25px rgba(102,126,234,0.3);
        }}
        .note-card {{ 
            background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); transition: transform 0.2s;
        }}
        .note-card:hover {{ transform: translateY(-2px); }}
        .note-title {{ 
            font-size: 18px; font-weight: 600; color: #333; margin-bottom: 10px;
        }}
        .note-meta {{ 
            display: flex; align-items: center; gap: 15px; margin-bottom: 15px; 
            color: #666; font-size: 14px;
        }}
        .note-images {{ 
            display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap;
        }}
        .note-image {{ 
            width: 100px; height: 100px; object-fit: cover; border-radius: 8px;
        }}
        .note-link {{ 
            color: #667eea; text-decoration: none; font-weight: 500;
        }}
        .method-badge {{ 
            background: #667eea; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 统一提取器结果</h1>
        <h2>关键词：{keyword}</h2>
        <div>共找到 {len(results)} 条笔记 | 提取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>
    
    <div class="notes-container">
"""
            
            for i, note in enumerate(results, 1):
                images_html = ""
                if note.get('images'):
                                         images_html = f"""
                        <div class="note-images">
                            {' '.join([f'<img src="{img}" alt="笔记图片" class="note-image" onerror="this.style.display=' + "'none'" + '">' for img in note['images'][:3]])}
                        </div>
                    """
                
                html_content += f"""
        <div class="note-card">
            <div class="note-title">{note.get('title', '未知标题')}</div>
            <div class="note-meta">
                <span>👤 {note.get('author', '未知作者')}</span>
                <span>❤️ {note.get('like_count', '0')}</span>
                <span>💬 {note.get('comment_count', '0')}</span>
                <span class="method-badge">{note.get('method', 'unknown')}</span>
            </div>
            {images_html}
            <div>
                <a href="{note.get('link', '#')}" target="_blank" class="note-link">🔗 查看完整笔记</a>
            </div>
        </div>
                """
            
            html_content += """
    </div>
</body>
</html>
"""
            
            # 保存HTML文件
            html_file = self.cache_dir / f"unified_preview_{keyword}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"✅ HTML预览已保存到: {html_file}")
            return str(html_file)
            
        except Exception as e:
            logger.error(f"❌ 生成HTML预览失败: {e}")
            return ""

    def _print_stats(self):
        """打印统计信息"""
        if self.stats['start_time']:
            duration = datetime.now() - self.stats['start_time']
            logger.info("\n" + "="*50)
            logger.info("📊 统一提取器处理统计")
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
    
    extractor = UnifiedExtractor()
    
    if len(sys.argv) > 1:
        keyword = sys.argv[1]
    else:
        keyword = "search"
    
    logger.info("🚀 启动统一数据提取器")
    
    # 批量处理HTML文件
    results = extractor.extract_from_html_files()
    
    if results:
        # 保存统一结果
        saved_path = extractor.save_unified_results(results, keyword)
        logger.info(f"✅ 统一提取完成，共处理 {len(results)} 条笔记")
        logger.info(f"📄 结果已保存到: {saved_path}")
    else:
        logger.warning("❌ 未提取到任何数据")

if __name__ == "__main__":
    main() 