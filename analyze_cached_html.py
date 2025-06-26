#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import urllib.parse
from bs4 import BeautifulSoup

def extract_notes_from_html(html_file_path):
    """分析HTML文件并提取笔记数据"""
    print(f"正在分析文件: {html_file_path}")
    
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        print(f"HTML文件大小: {len(html_content)} 字符")
        
        # 分析数据
        results = []
        
        # 方法1: 查找explore链接
        print("\n==================== 方法1: 分析explore链接 ====================")
        explore_links = soup.find_all('a', href=re.compile(r'/explore/'))
        print(f"找到 {len(explore_links)} 个explore链接")
        
        for i, link in enumerate(explore_links[:10]):  # 只分析前10个
            href = link.get('href', '')
            if '/explore/' in href:
                note_id = href.split('/explore/')[-1].split('?')[0]
                title_element = link.find(class_=re.compile(r'title|text'))
                title = title_element.get_text(strip=True) if title_element else "未找到标题"
                
                print(f"  {i+1}. 笔记ID: {note_id}")
                print(f"     标题: {title}")
                print(f"     链接: {href}")
                
                results.append({
                    'note_id': note_id,
                    'title': title,
                    'link': href,
                    'method': 'explore_link'
                })
        
        # 方法2: 查找图片和标题
        print("\n==================== 方法2: 分析图片和标题 ====================")
        images = soup.find_all('img', src=re.compile(r'xhscdn\.com'))
        print(f"找到 {len(images)} 个小红书CDN图片")
        
        image_notes = {}
        for img in images:
            src = img.get('src', '')
            if 'notes_pre_post' in src:
                # 尝试找到父级容器
                parent = img.parent
                for _ in range(5):  # 向上查找5层
                    if parent:
                        text = parent.get_text(strip=True)
                        if text and len(text) > 10:
                            # 可能是笔记标题
                            image_notes[src] = text[:100]
                            break
                        parent = parent.parent
        
        print(f"从图片找到 {len(image_notes)} 个可能的笔记")
        for i, (src, title) in enumerate(list(image_notes.items())[:5]):
            print(f"  {i+1}. 标题: {title}")
            print(f"     图片: {src[:80]}...")
        
        # 方法3: 查找热搜或推荐内容
        print("\n==================== 方法3: 分析文本内容 ====================")
        text_content = soup.get_text()
        
        # 查找"老庙黄金"相关文本
        keyword_matches = re.findall(r'老庙黄金[^。！？\n]{0,30}', text_content)
        print(f"找到 {len(keyword_matches)} 处关键词匹配:")
        for i, match in enumerate(keyword_matches[:10]):
            print(f"  {i+1}. {match}")
        
        # 方法4: 查找JSON数据
        print("\n==================== 方法4: 分析JSON数据 ====================")
        json_pattern = re.compile(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', re.DOTALL)
        json_match = json_pattern.search(html_content)
        
        if json_match:
            try:
                json_data = json.loads(json_match.group(1))
                print("找到初始状态JSON数据")
                
                # 递归查找notes相关数据
                def find_notes_in_json(obj, path=""):
                    notes_data = []
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            current_path = f"{path}.{key}" if path else key
                            if 'note' in key.lower() and isinstance(value, (list, dict)):
                                notes_data.append((current_path, value))
                            notes_data.extend(find_notes_in_json(value, current_path))
                    elif isinstance(obj, list):
                        for i, item in enumerate(obj):
                            notes_data.extend(find_notes_in_json(item, f"{path}[{i}]"))
                    return notes_data
                
                notes_data = find_notes_in_json(json_data)
                print(f"在JSON中找到 {len(notes_data)} 个notes相关数据结构:")
                
                for path, data in notes_data[:5]:
                    print(f"  路径: {path}")
                    if isinstance(data, list):
                        print(f"  类型: 数组，长度: {len(data)}")
                    elif isinstance(data, dict):
                        print(f"  类型: 对象，键数: {len(data.keys())}")
                        if len(data) < 20:  # 只显示小对象的键
                            print(f"  键: {list(data.keys())}")
                    print()
                    
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
        else:
            print("未找到初始状态JSON数据")
        
        # 方法5: 查找具体的笔记元素
        print("\n==================== 方法5: 查找笔记元素 ====================")
        
        # 查找包含data-v属性的元素（Vue组件）
        vue_elements = soup.find_all(attrs={'data-v': True})
        print(f"找到 {len(vue_elements)} 个Vue组件元素")
        
        # 查找可能的笔记卡片
        note_cards = []
        for element in vue_elements:
            text = element.get_text(strip=True)
            if text and ('老庙' in text or len(text) > 20):
                # 检查是否包含图片
                images = element.find_all('img')
                links = element.find_all('a')
                
                if images or links:
                    note_cards.append({
                        'text': text[:100],
                        'images': len(images),
                        'links': len(links),
                        'tag': element.name,
                        'attrs': dict(element.attrs)
                    })
        
        print(f"找到 {len(note_cards)} 个可能的笔记卡片:")
        for i, card in enumerate(note_cards[:5]):
            print(f"  {i+1}. 文本: {card['text']}")
            print(f"     标签: {card['tag']}, 图片: {card['images']}, 链接: {card['links']}")
            print(f"     属性: {list(card['attrs'].keys())}")
            print()
        
        print(f"\n==================== 分析完成 ====================")
        print(f"总共提取到 {len(results)} 个确认的笔记")
        print(f"发现 {len(image_notes)} 个图片相关笔记")
        print(f"发现 {len(note_cards)} 个可能的笔记卡片")
        print(f"关键词匹配 {len(keyword_matches)} 处")
        
        return results
        
    except Exception as e:
        print(f"分析文件时出错: {e}")
        return []

def main():
    """主函数"""
    cache_dir = "cache/temp"
    
    if not os.path.exists(cache_dir):
        print(f"缓存目录不存在: {cache_dir}")
        return
    
    # 查找HTML文件
    html_files = [f for f in os.listdir(cache_dir) if f.endswith('.html')]
    
    if not html_files:
        print("未找到HTML文件")
        return
    
    print(f"找到 {len(html_files)} 个HTML文件:")
    for i, filename in enumerate(html_files):
        print(f"  {i+1}. {filename}")
    
    # 分析最新的HTML文件
    latest_file = max(html_files, key=lambda x: os.path.getmtime(os.path.join(cache_dir, x)))
    file_path = os.path.join(cache_dir, latest_file)
    
    print(f"\n正在分析最新文件: {latest_file}")
    results = extract_notes_from_html(file_path)
    
    if results:
        print(f"\n成功提取到的笔记:")
        for i, result in enumerate(results):
            print(f"{i+1}. {result['title']} (ID: {result['note_id']})")

if __name__ == "__main__":
    main() 