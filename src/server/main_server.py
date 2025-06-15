#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
小红书搜索服务器模块
提供Web API和静态文件服务，支持搜索、结果展示等功能

主要功能：
1. Web API服务 - 搜索、笔记详情、热门关键词
2. 静态文件服务 - HTML、CSS、JS、图片
3. HTML结果页面服务 - 文件形式和API形式
4. 用户登录支持
"""

import sys
import os
import logging
import time
import hashlib
import traceback
import json
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
from flask_cors import CORS
from src.crawler.xiaohongshu_crawler import XiaoHongShuCrawler
from src.server.debug_manager import debug_manager

# ==================== 配置和初始化 ====================

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__, static_folder='../../static')
CORS(app)  # 允许跨域请求

# ==================== 全局变量 ====================

# Cookie文件路径
COOKIES_FILE = os.path.join('cache', 'cookies', 'xiaohongshu_cookies.json')

# 全局爬虫实例（延迟初始化）
crawler = None

# HTML结果内存缓存（避免文件路径问题）
html_results_cache = {}

# ==================== 工具函数 ====================

def store_html_result(html_hash, html_content):
    """
    存储HTML结果到内存缓存
    
    Args:
        html_hash: HTML内容的MD5哈希值
        html_content: HTML内容
    """
    global html_results_cache
    html_results_cache[html_hash] = html_content
    logger.info(f"HTML内容已存储到内存缓存: {html_hash}")

def init_crawler():
    """
    延迟初始化爬虫实例
    只在第一次使用时初始化，避免启动时的性能开销
    
    Returns:
        bool: 初始化是否成功
    """
    global crawler
    if crawler is None:
        try:
            logger.info("正在初始化小红书爬虫...")
            crawler = XiaoHongShuCrawler(
                use_selenium=True, 
                headless=True, 
                cookies_file=COOKIES_FILE
            )
            # 设置HTML存储回调函数
            crawler.set_html_callback(store_html_result)
            logger.info("小红书爬虫初始化成功")
            return True
        except Exception as e:
            logger.error(f"小红书爬虫初始化失败: {str(e)}")
            logger.error(traceback.format_exc())
            crawler = None
            return False
    return True

def get_project_root():
    """获取项目根目录路径"""
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))





# ==================== 静态文件路由 ====================

@app.route('/')
def index():
    """主页 - 返回搜索界面"""
    return send_from_directory('../../static', 'index.html')

@app.route('/css/<path:path>')
def serve_css(path):
    """提供CSS文件服务"""
    return send_from_directory('../../static/css', path)

@app.route('/js/<path:path>')
def serve_js(path):
    """提供JavaScript文件服务"""
    return send_from_directory('../../static/js', path)

@app.route('/img/<path:path>')
def serve_img(path):
    """提供图片文件服务"""
    return send_from_directory('../../static/images', path)

# ==================== 用户登录路由 ====================

@app.route('/login')
def login():
    """
    用户登录页面
    打开浏览器让用户手动登录小红书，获取cookie
    """
    try:
        # 创建专门用于登录的爬虫实例（非无头模式）
        login_crawler = XiaoHongShuCrawler(use_selenium=True, headless=False)
        success = login_crawler.login()
        login_crawler.close()
        
        if success:
            # 登录成功后重置主爬虫实例，以使用新的cookie
            global crawler
            crawler = None
            return redirect(url_for('index'))
        else:
            return jsonify({"error": "登录失败，请重试"}), 500
    except Exception as e:
        logger.error(f"登录过程出错: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"登录过程出错: {str(e)}"}), 500

# ==================== API路由 ====================

@app.route('/api/search')
def search():
    """
    搜索API
    根据关键词搜索小红书笔记
    
    参数:
        keyword: 搜索关键词（必需）
        max_results: 最大结果数量（可选，默认21）
        use_cache: 是否使用缓存（可选，默认true）
        session_id: 会话ID（可选，用于debug信息）
    
    返回:
        JSON格式的搜索结果，包含笔记列表和HTML页面URL
    """
    # 初始化爬虫
    if not init_crawler():
        return jsonify({"error": "爬虫初始化失败，请检查网络连接和Chrome浏览器"}), 500
        
    # 获取参数
    keyword = request.args.get('keyword', '').strip()
    session_id = request.args.get('session_id', f"search_{int(time.time())}")
    
    if not keyword:
        return jsonify({"error": "缺少关键词参数"}), 400
    
    try:
        # 解析参数
        max_results = int(request.args.get('max_results', 21))
        use_cache = request.args.get('use_cache', 'true').lower() == 'true'
        
        # 记录开始搜索
        debug_manager.store_debug_info(session_id, f"🔍 开始搜索关键词: {keyword}", "INFO")
        debug_manager.store_debug_info(session_id, f"📊 最大结果数: {max_results}, 使用缓存: {use_cache}", "INFO")
        
        # 设置爬虫的debug回调
        debug_callback = debug_manager.create_debug_callback(session_id)
        
        # 如果爬虫支持debug回调，设置它
        if hasattr(crawler, 'set_debug_callback'):
            crawler.set_debug_callback(debug_callback)
        
        # 执行搜索
        debug_manager.store_debug_info(session_id, "🚀 正在执行搜索...", "INFO")
        search_results = crawler.search(keyword, max_results=max_results, use_cache=use_cache)
        
        # 规范化搜索结果格式
        if isinstance(search_results, dict) and 'data' in search_results:
            notes = search_results['data']
        else:
            notes = search_results if isinstance(search_results, list) else []
        
        debug_manager.store_debug_info(session_id, f"✅ 搜索完成，找到 {len(notes)} 条笔记", "INFO")
        
        # 生成HTML页面URL
        html_hash = hashlib.md5(keyword.encode()).hexdigest()
        html_url = f"/results/search_{html_hash}.html"           # 文件形式
        html_api_url = f"/api/result-html/{html_hash}"           # API形式（推荐）
        
        debug_manager.store_debug_info(session_id, f"📄 生成HTML页面: {html_api_url}", "INFO")
        
        return jsonify({
            "keyword": keyword,
            "session_id": session_id,
            "timestamp": int(time.time()),
            "count": len(notes),
            "notes": notes,
            "html_url": html_url,
            "html_api_url": html_api_url
        })
    except Exception as e:
        logger.error(f"搜索出错: {str(e)}")
        logger.error(traceback.format_exc())
        debug_manager.store_debug_info(session_id, f"❌ 搜索失败: {str(e)}", "ERROR")
        return jsonify({"error": "搜索失败", "message": str(e), "session_id": session_id}), 500

@app.route('/api/note/<note_id>')
def get_note(note_id):
    """
    获取笔记详情API
    
    参数:
        note_id: 笔记ID
    
    返回:
        JSON格式的笔记详情
    """
    if not init_crawler():
        return jsonify({"error": "爬虫初始化失败"}), 500
        
    if not note_id:
        return jsonify({"error": "缺少笔记ID参数"}), 400
    
    try:
        note = crawler.get_note_detail(note_id)
        
        if note:
            return jsonify({"note": note})
        else:
            return jsonify({"error": "未找到该笔记"}), 404
    except Exception as e:
        logger.error(f"获取笔记详情出错: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": "获取笔记详情失败", "message": str(e)}), 500

@app.route('/api/hot-keywords')
def hot_keywords():
    """
    获取热门关键词API
    
    返回:
        JSON格式的热门关键词列表
    """
    if not init_crawler():
        return jsonify({"error": "爬虫初始化失败"}), 500
        
    try:
        keywords = crawler.get_hot_keywords()
        return jsonify({"keywords": keywords})
    except Exception as e:
        logger.error(f"获取热门关键词出错: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": "获取热门关键词失败", "message": str(e)}), 500

@app.route('/api/debug/<session_id>')
def get_debug_info(session_id):
    """
    获取debug信息API
    
    参数:
        session_id: 会话ID
        since: 获取指定时间戳之后的信息（可选）
    
    返回:
        JSON格式的debug信息列表
    """
    since = request.args.get('since', type=float, default=0)
    return jsonify(debug_manager.get_debug_info(session_id, since))

# ==================== HTML结果页面路由 ====================

@app.route('/results/<path:filename>')
def serve_results(filename):
    """
    提供HTML结果页面服务（文件形式）
    从文件系统提供预生成的HTML结果页面
    """
    results_dir = os.path.join(get_project_root(), 'cache', 'results')
    logger.debug(f"文件服务目录: {results_dir}")
    return send_from_directory(results_dir, filename)

@app.route('/api/result-html/<html_hash>')
def get_result_html(html_hash):
    """
    直接返回HTML结果页面内容（API形式，推荐）
    优先从内存缓存返回，避免文件路径问题
    
    参数:
        html_hash: HTML内容的MD5哈希值
    
    返回:
        HTML页面内容
    """
    global html_results_cache
    
    # 优先从内存缓存获取
    if html_hash in html_results_cache:
        html_content = html_results_cache[html_hash]
        logger.info(f"从内存缓存返回HTML内容: {html_hash}")
        return html_content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    
    # 回退：尝试从文件读取
    try:
        html_filename = f"search_{html_hash}.html"
        results_dir = os.path.join(get_project_root(), 'cache', 'results')
        html_path = os.path.join(results_dir, html_filename)
        
        if os.path.exists(html_path):
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            # 存储到内存缓存中
            html_results_cache[html_hash] = html_content
            logger.info(f"从文件读取并缓存HTML内容: {html_path}")
            return html_content, 200, {'Content-Type': 'text/html; charset=utf-8'}
        else:
            logger.warning(f"HTML文件不存在: {html_path}")
            return jsonify({"error": "HTML结果页面不存在"}), 404
    except Exception as e:
        logger.error(f"读取HTML文件失败: {str(e)}")
        return jsonify({"error": "无法读取HTML文件"}), 500



# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(e):
    """处理404错误"""
    return jsonify({"error": "资源不存在"}), 404

@app.errorhandler(500)
def server_error(e):
    """处理500错误"""
    return jsonify({"error": "服务器内部错误"}), 500

# ==================== 清理函数 ====================

def cleanup():
    """应用退出时的清理工作"""
    global crawler
    if crawler:
        crawler.close()
        crawler = None

# ==================== 主程序入口 ====================

if __name__ == '__main__':
    import atexit
    
    try:
        # 创建必要的目录
        project_root = get_project_root()
        essential_dirs = [
            'cache/cookies',
            'cache/temp', 
            'cache/logs',
            'cache/results',
            'static/images'
        ]
        for dir_path in essential_dirs:
            full_path = os.path.join(project_root, dir_path)
            os.makedirs(full_path, exist_ok=True)
        
        # 注册清理函数
        atexit.register(cleanup)
        
        logger.info("小红书搜索服务启动中...")
        logger.info("访问地址: http://localhost:8080")
        logger.info("如需登录，请访问: http://localhost:8080/login")
        
        # 启动服务
        app.run(debug=False, host='0.0.0.0', port=8080)
    except KeyboardInterrupt:
        logger.info("服务已停止")
        cleanup()
    except Exception as e:
        logger.error(f"服务启动失败: {str(e)}")
        logger.error(traceback.format_exc())
        cleanup() 