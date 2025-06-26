# 小红书智能搜索工具

## 项目简介

本项目是一个专业的小红书内容搜索与提取工具，支持关键词搜索、笔记数据提取、智能反爬虫、实时debug信息展示、AI同类笔记生成等功能。适用于数据分析、内容采集、AI内容创作等场景。

---

## 目录结构

```
xiaohongshu-search/
├── app.py                  # 主程序入口，自动清理缓存/临时/截图目录
├── requirements.txt        # Python依赖包
├── README.md               # 项目文档（本文件）
├── src/
│   ├── crawler/            # 爬虫核心模块
│   │   ├── XHS_crawler.py         # 小红书搜索主爬虫
│   │   └── backend_XHS_crawler.py # 后台内容深度爬虫
│   └── server/             # 服务端API与逻辑
│       ├── main_server.py         # 主API服务
│       ├── debug_manager.py       # Debug信息管理
│       └── note_content_extractor.py # HTML内容提取
├── static/
│   ├── index.html          # 前端主页面
│   ├── js/
│   │   ├── api.js          # 前端API客户端
│   │   └── script.js       # 前端主逻辑
│   └── css/style.css       # 样式文件
├── cache/
│   ├── results/            # 搜索结果HTML页面
│   ├── temp/               # 临时文件和调试截图
│   └── cookies/            # Cookie存储
├── drivers/
│   └── chromedriver-mac-arm64/    # ChromeDriver本地化
└── ...
```

---

## 快速开始

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```
2. **准备ChromeDriver**
   - 推荐手动下载与你Chrome浏览器版本匹配的ChromeDriver，放入`drivers/chromedriver-mac-arm64/`目录。
3. **启动服务**
   ```bash
   python app.py
   ```
   - 启动时会自动清理cache/results、cache/temp、debug_screenshots目录下所有文件（保留文件夹）。
4. **访问Web界面**
   - 浏览器打开 http://localhost:8080

---

## 主要功能与架构

- **智能搜索**：支持缓存、HTML提取、实时搜索三种策略，按需配置，自动降级。
- **HTML内容提取**：支持从本地HTML文件高效提取笔记数据，兼容新版页面结构。
- **反爬虫与容错**：模拟人类行为、智能等待、自动重试、验证码处理。
- **实时Debug**：前端可实时查看后端debug信息，便于排查问题。
- **AI同类笔记生成**：基于搜索结果一键生成AI笔记内容。
- **本地化ChromeDriver**：避免每次启动重复下载，提升启动速度。
- **自动清理机制**：每次启动前自动清理缓存/临时/截图目录，保证环境整洁。

---

## 智能搜索与提取说明

- **三大搜索策略**：
  1. **缓存搜索**：优先返回本地缓存结果，速度快。
  2. **HTML提取**：自动从已生成的HTML文件中提取笔记数据。
  3. **实时搜索**：如前两者无结果，自动发起实时爬取。
- **HTML提取修复要点**：
  - 优先在`results`目录查找HTML文件，再降级到`temp`目录。
  - 兼容新版HTML结构，优先解析`data-note-id`属性。
  - 提取标题、描述、作者、互动数据、图片等完整信息。
- **前端主流程**：
  - 搜索后只轮询HTML状态，直到ready/error/超时才跳转或报错。
  - debug信息仅展示，不影响主流程。

---

## 主要类与模块关系

- `XiaoHongShuCrawler`：主爬虫类，负责关键词搜索、页面解析、反爬虫处理。
- `DebugManager`：管理和存储debug信息，支持多会话隔离。
- `UnifiedExtractor`/`note_content_extractor.py`：负责HTML文件内容提取。
- `main_server.py`：API服务主入口，负责路由、参数校验、流程调度。
- 前端`api.js`/`script.js`：负责与后端API通信、状态轮询、页面交互。

---

## 常见问题与维护说明

- **ChromeDriver相关**：
  - 启动报错多为ChromeDriver版本不匹配，请手动下载与你Chrome浏览器版本一致的驱动。
  - 放置于`drivers/chromedriver-mac-arm64/`目录，确保有执行权限。
- **依赖冲突**：
  - urllib3等依赖如有冲突，按`requirements.txt`指定版本安装。
- **缓存/临时文件清理**：
  - 每次启动自动清理，无需手动操作。
- **验证码处理**：
  - 遇到验证码时，程序会自动切换到可见模式，需人工干预。
- **调试与日志**：
  - 可通过前端debug面板实时查看后端日志。

---

## 版本与维护

- **当前状态**：核心功能稳定，支持多策略搜索与内容提取。
- **后续计划**：持续优化提取准确率、反爬虫能力、UI体验。
- **技术栈**：Python 3.8+、Flask、Selenium、BeautifulSoup4、前端原生JS+HTML+CSS。

---

> 本项目仅供学习与研究使用，严禁用于任何商业或违法用途。 