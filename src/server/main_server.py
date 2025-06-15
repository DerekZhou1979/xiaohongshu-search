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

# Debug信息存储
debug_info_store = {}

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

def create_login_required_page(decoded_url):
    """创建需要登录的页面"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>需要登录</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, sans-serif; 
                text-align: center; 
                padding: 50px; 
                background: #f8f9fa;
            }
            .container { 
                max-width: 600px; 
                margin: 0 auto; 
                background: white; 
                padding: 40px; 
                border-radius: 10px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .warning { color: #ff9800; font-size: 18px; margin-bottom: 20px; }
            .info { color: #666; margin-bottom: 20px; line-height: 1.6; }
            .url-info { 
                background: #f5f5f5; 
                padding: 15px; 
                border-radius: 5px; 
                margin: 20px 0; 
                word-break: break-all; 
                font-family: monospace;
                font-size: 12px;
            }
            .back-btn {
                display: inline-block;
                background: #ff6b6b;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                text-decoration: none;
                margin-top: 20px;
            }
            .back-btn:hover { background: #ff5252; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="warning">🔐 该笔记需要登录才能访问</div>
            <div class="info">
                xsec_token和xsec_source参数已添加，但该笔记仍需要有效的登录状态。<br>
                这可能是因为：<br>
                • 笔记设置为私密或仅好友可见<br>
                • 需要更新的登录凭证<br>
                • 笔记已被删除或限制访问
            </div>
            <div class="url-info">访问URL: ''' + decoded_url + '''</div>
            <a href="javascript:history.back()" class="back-btn">← 返回搜索结果</a>
        </div>
    </body>
    </html>
    ''', 200, {'Content-Type': 'text/html; charset=utf-8'}

def fix_proxy_content(content, original_url):
    """修复代理内容中的链接和资源引用"""
    try:
        import re
        from urllib.parse import urljoin, urlparse
        
        # 获取基础URL
        parsed_url = urlparse(original_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # 修复相对链接
        content = re.sub(r'href="(/[^"]*)"', rf'href="{base_url}\1"', content)
        content = re.sub(r"href='(/[^']*)'", rf"href='{base_url}\1'", content)
        
        # 修复相对资源链接（CSS, JS, 图片等）
        content = re.sub(r'src="(/[^"]*)"', rf'src="{base_url}\1"', content)
        content = re.sub(r"src='(/[^']*)'", rf"src='{base_url}\1'", content)
        
        # 修复CSS中的相对链接
        content = re.sub(r'url\((/[^)]*)\)', rf'url({base_url}\1)', content)
        content = re.sub(r'url\("(/[^"]*)"\)', rf'url("{base_url}\1")', content)
        content = re.sub(r"url\('(/[^']*)'\)", rf"url('{base_url}\1')", content)
        
        # 添加代理提示样式和安全策略
        if '<head>' in content:
            style_injection = '''
            <meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">
            <meta http-equiv="X-Content-Type-Options" content="nosniff">
            <style>
                .proxy-notice { 
                    background: linear-gradient(45deg, #ff6b6b, #ff8e8e);
                    color: white; 
                    padding: 12px; 
                    text-align: center; 
                    position: fixed; 
                    top: 0; 
                    left: 0; 
                    right: 0; 
                    z-index: 9999;
                    font-size: 14px;
                    font-weight: 500;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                }
                body { padding-top: 50px !important; }
                .proxy-notice a {
                    color: white;
                    text-decoration: underline;
                    margin-left: 10px;
                }
            </style>
            '''
            content = content.replace('<head>', f'<head>{style_injection}')
        
        # 添加代理提示
        if '<body>' in content:
            proxy_notice = '''
            <div class="proxy-notice">
                🔗 通过豫园股份代理服务访问 - 已自动处理登录认证
                <a href="javascript:history.back()">← 返回搜索结果</a>
            </div>
            '''
            content = content.replace('<body>', f'<body>{proxy_notice}')
        
        # 修复可能的协议问题
        content = content.replace('http://www.xiaohongshu.com', 'https://www.xiaohongshu.com')
        
        return content
        
    except Exception as e:
        logger.error(f"修复代理内容失败: {str(e)}")
        return content

def store_debug_info(session_id, message, level="INFO"):
    """
    存储debug信息
    
    Args:
        session_id: 会话ID
        message: debug消息
        level: 日志级别
    """
    if session_id not in debug_info_store:
        debug_info_store[session_id] = []
    
    debug_info_store[session_id].append({
        'timestamp': time.time(),
        'level': level,
        'message': message,
        'time_str': time.strftime('%H:%M:%S', time.localtime())
    })
    
    # 限制每个会话最多存储100条debug信息
    if len(debug_info_store[session_id]) > 100:
        debug_info_store[session_id] = debug_info_store[session_id][-100:]

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
        store_debug_info(session_id, f"🔍 开始搜索关键词: {keyword}", "INFO")
        store_debug_info(session_id, f"📊 最大结果数: {max_results}, 使用缓存: {use_cache}", "INFO")
        
        # 设置爬虫的debug回调
        def debug_callback(message, level="INFO"):
            store_debug_info(session_id, message, level)
        
        # 如果爬虫支持debug回调，设置它
        if hasattr(crawler, 'set_debug_callback'):
            crawler.set_debug_callback(debug_callback)
        
        # 执行搜索
        store_debug_info(session_id, "🚀 正在执行搜索...", "INFO")
        search_results = crawler.search(keyword, max_results=max_results, use_cache=use_cache)
        
        # 规范化搜索结果格式
        if isinstance(search_results, dict) and 'data' in search_results:
            notes = search_results['data']
        else:
            notes = search_results if isinstance(search_results, list) else []
        
        store_debug_info(session_id, f"✅ 搜索完成，找到 {len(notes)} 条笔记", "INFO")
        
        # 生成HTML页面URL
        html_hash = hashlib.md5(keyword.encode()).hexdigest()
        html_url = f"/results/search_{html_hash}.html"           # 文件形式
        html_api_url = f"/api/result-html/{html_hash}"           # API形式（推荐）
        
        store_debug_info(session_id, f"📄 生成HTML页面: {html_api_url}", "INFO")
        
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
        store_debug_info(session_id, f"❌ 搜索失败: {str(e)}", "ERROR")
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
    
    if session_id not in debug_info_store:
        return jsonify({"debug_info": []})
    
    debug_info = debug_info_store[session_id]
    
    # 如果指定了since参数，只返回该时间戳之后的信息
    if since > 0:
        debug_info = [info for info in debug_info if info['timestamp'] > since]
    
    return jsonify({
        "session_id": session_id,
        "debug_info": debug_info,
        "last_timestamp": debug_info[-1]['timestamp'] if debug_info else 0
    })

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

# ==================== 代理路由 ====================

@app.route('/proxy/note/<path:note_url>')
def proxy_note(note_url):
    """
    代理小红书笔记链接，使用cookies进行认证
    
    Args:
        note_url: 小红书笔记URL（已编码）
    """
    try:
        import urllib.parse
        import requests
        
        # 解码URL
        decoded_url = urllib.parse.unquote(note_url)
        
        # 确保URL是小红书的链接
        if not decoded_url.startswith('https://www.xiaohongshu.com/'):
            return jsonify({"error": "无效的链接"}), 400
        
        # 加载cookies
        cookies_dict = {}
        if os.path.exists(COOKIES_FILE):
            try:
                with open(COOKIES_FILE, 'r', encoding='utf-8') as f:
                    cookies_list = json.load(f)
                for cookie in cookies_list:
                    cookies_dict[cookie['name']] = cookie['value']
            except Exception as e:
                logger.warning(f"加载cookies失败: {str(e)}")
        
        # 设置请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.xiaohongshu.com/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # 记录访问日志
        logger.info(f"代理访问URL: {decoded_url}")
        
        # 发起请求，禁用SSL验证以避免证书问题
        response = requests.get(decoded_url, cookies=cookies_dict, headers=headers, timeout=15, verify=False)
        
        # 记录响应状态
        logger.info(f"代理响应状态: {response.status_code}")
        
        if response.status_code == 200:
            # 验证是否成功访问（检查是否需要登录）
            content_preview = response.text[:1000].lower()
            if '登录' in content_preview or 'login' in content_preview or '验证' in content_preview:
                logger.warning(f"可能需要登录认证: {decoded_url}")
                return create_login_required_page(decoded_url)
            
            logger.info(f"成功访问笔记: {decoded_url}")
            
            # 处理响应内容
            content = response.text
            
            # 修复内容中的各种链接和资源引用
            content = fix_proxy_content(content, decoded_url)
            
            # 设置正确的响应头
            response_headers = {
                'Content-Type': 'text/html; charset=utf-8',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'X-Frame-Options': 'SAMEORIGIN',
                'X-Content-Type-Options': 'nosniff',
                'Referrer-Policy': 'strict-origin-when-cross-origin',
                'Content-Security-Policy': "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: https: wss:; img-src 'self' data: blob: https: http:; media-src 'self' data: blob: https: http:; connect-src 'self' https: wss:; font-src 'self' data: https:; style-src 'self' 'unsafe-inline' https:; script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; upgrade-insecure-requests;"
            }
            
            return content, 200, response_headers
        else:
            logger.warning(f"代理请求失败: {response.status_code}")
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>访问失败</title>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; text-align: center; padding: 50px; }
                    .error { color: #ff6b6b; font-size: 18px; margin-bottom: 20px; }
                    .retry { color: #666; }
                </style>
            </head>
            <body>
                <div class="error">⚠️ 无法访问该笔记</div>
                <div class="retry">可能是网络问题或笔记已被删除</div>
                <div style="margin-top: 20px;">
                    <a href="javascript:history.back()" style="color: #ff6b6b; text-decoration: none;">← 返回搜索结果</a>
                </div>
            </body>
            </html>
            ''', 200, {'Content-Type': 'text/html; charset=utf-8'}
            
    except Exception as e:
        logger.error(f"代理笔记链接失败: {str(e)}")
        return jsonify({"error": f"代理失败: {str(e)}"}), 500

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