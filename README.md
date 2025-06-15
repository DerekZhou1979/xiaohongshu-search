# 豫园股份-小红书搜索工具

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/DerekZhou1979/xiaohongshu-search.svg)](https://github.com/DerekZhou1979/xiaohongshu-search/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/DerekZhou1979/xiaohongshu-search.svg)](https://github.com/DerekZhou1979/xiaohongshu-search/network)
[![GitHub issues](https://img.shields.io/github/issues/DerekZhou1979/xiaohongshu-search.svg)](https://github.com/DerekZhou1979/xiaohongshu-search/issues)

一个专业的小红书内容搜索工具，支持关键词搜索、笔记数据提取、实时debug信息显示和人工验证处理。

## 🌟 主要特性

### 核心功能
- **智能搜索**: 支持关键词搜索小红书笔记内容
- **多策略提取**: 三种数据提取策略确保高成功率
- **人工验证**: 自动检测验证码，支持人工处理
- **实时监控**: 前台实时显示搜索过程的debug信息
- **数据完整**: 提取标题、描述、作者、互动数据、标签等完整信息

### 技术特色
- **反爬虫处理**: 智能检测和处理各种反爬虫机制
- **Cookie管理**: 自动保存和加载用户登录状态
- **缓存系统**: 智能缓存减少重复请求
- **配置化**: 支持5种运行模式，满足不同使用场景
- **错误恢复**: 完善的错误处理和恢复机制

## 📁 项目结构

```
xiaohongshu-search/
├── app.py                      # 主程序入口，配置选择和服务启动
├── simple_refresh_cookies.py   # Cookie刷新工具
├── start_servers.py           # 多服务启动脚本（包含图片代理）
├── requirements.txt           # Python依赖包
├── MANIFEST.in               # 包管理文件
├── README.md                 # 项目文档
├── 
├── src/                      # 源代码目录
│   ├── crawler/              # 爬虫核心模块
│   │   └── xiaohongshu_crawler.py  # 小红书爬虫主类
│   └── server/               # 服务器模块
│       ├── main_server.py    # 主服务器（API + Web界面）
│       └── image_proxy.py    # 图片代理服务器
├── 
├── static/                   # 前端静态文件
│   ├── index.html           # 主页面
│   ├── css/
│   │   └── style.css        # 样式文件
│   └── js/
│       ├── api.js          # API客户端
│       └── script.js       # 前端交互逻辑
├── 
├── cache/                   # 缓存目录
│   ├── cookies/            # Cookie存储
│   ├── temp/               # 临时文件和调试截图
│   ├── results/            # 搜索结果HTML页面
│   └── logs/               # 日志文件
├── 
├── drivers/                # 浏览器驱动
│   └── chromedriver-mac-arm64/  # Chrome驱动（按平台）
└── 
└── .github/
    └── workflows/
        └── deploy.yml      # GitHub Actions部署配置
```

## 🚀 快速开始

### 环境要求

- **Python**: 3.8+
- **Chrome浏览器**: 用于Selenium自动化
- **操作系统**: macOS, Windows, Linux

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-username/xiaohongshu-search.git
cd xiaohongshu-search
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **下载ChromeDriver**
   - 自动下载或手动下载适合您系统的ChromeDriver
   - 放置在 `drivers/` 目录下

4. **启动服务**
```bash
python app.py
```

### 运行模式选择

程序启动时会显示5种运行模式选择：

1. **标准模式（推荐）**
   - 启用所有提取策略
   - 关闭调试截图
   - 适中的验证严格度

2. **调试模式**
   - 启用所有策略
   - 开启详细截图和debug信息
   - 保存所有调试数据

3. **快速模式**
   - 仅启用策略1（最快）
   - 关闭截图和详细日志
   - 降低验证严格度

4. **兼容模式**
   - 启用所有策略
   - 关闭截图
   - 最低验证严格度

5. **自定义模式**
   - 手动配置各项功能
   - 完全个性化设置

## 🔧 使用方法

### Web界面使用

1. 访问 `http://localhost:8080`
2. 在搜索框输入关键词（如：老庙黄金、海鸥表）
3. 点击搜索或选择豫园品牌快捷搜索
4. 实时查看搜索过程的debug信息
5. 查看搜索结果页面

### 验证码处理

当遇到验证码时：

1. **自动检测**: 程序自动检测验证码页面
2. **浏览器激活**: 自动切换到可见模式并激活浏览器窗口  
3. **人工处理**: 用户手动完成拼图验证
4. **自动继续**: 验证完成后程序自动继续

### 实时Debug信息

搜索过程中可以看到：
- 🔍 搜索开始和关键词
- 🚀 浏览器初始化状态
- 🔗 搜索URL尝试过程
- 🛡️ 反爬虫检测结果
- 📄 页面内容加载状态
- 🔧 三种提取策略执行情况
- ✅ 搜索完成和结果统计

## 📊 三种数据提取策略

### 策略1: 探索链接提取
- 搜索页面中的 `/explore/` 链接
- 提取笔记ID和xsec_token
- 从容器元素中提取详细信息

### 策略2: 数据属性提取  
- 查找带有数据属性的元素
- 从 `data-note-id` 等属性获取ID
- 构造URL并提取信息

### 策略3: JavaScript提取
- 使用JavaScript在浏览器中执行
- 直接获取页面渲染后的数据
- 处理动态加载的内容

## 🎯 提取的数据字段

每个笔记包含以下信息：
- **基础信息**: ID、URL、标题、描述、作者
- **媒体内容**: 封面图片URL
- **互动数据**: 点赞数、评论数、收藏数、浏览数
- **标签信息**: 相关话题标签
- **安全令牌**: xsec_token用于直接访问

## ⚙️ 配置说明

### 缓存配置
- **搜索缓存**: 1小时有效期
- **结果页面**: 自动生成HTML页面
- **调试截图**: 可配置开启/关闭

### 反爬虫配置
- **用户代理**: 模拟真实浏览器
- **请求间隔**: 智能延迟控制
- **Cookie管理**: 自动维护登录状态

### 验证严格度
- **低**: 接受大部分结果
- **中等**: 平衡准确性和数量  
- **高**: 严格验证相关性

## 🔍 API接口

### 搜索接口
```
GET /api/search?keyword={keyword}&max_results={num}&session_id={id}
```

### Debug信息接口
```
GET /api/debug/{session_id}?since={timestamp}
```

### 笔记详情接口
```
GET /api/note/{note_id}
```

### 热门关键词接口
```
GET /api/hot-keywords
```

## 🚨 注意事项

### 使用限制
- 本工具仅供学习研究使用
- 请遵守小红书的使用条款
- 不建议用于商业用途
- 请控制请求频率，避免对服务器造成压力

### 技术限制
- 需要Chrome浏览器支持
- 依赖网络连接稳定性
- 可能遇到验证码需要人工处理
- 搜索结果可能因为反爬虫机制而变化

### 隐私安全
- Cookie数据存储在本地
- 不会上传用户个人信息
- 调试截图仅本地保存
- 可以随时清理缓存数据

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目仅供学习研究使用，请遵守相关法律法规。

## 🆘 常见问题

### Q: 搜索没有结果怎么办？
A: 检查网络连接，尝试更换关键词，或重新启动程序。

### Q: 遇到验证码如何处理？
A: 程序会自动切换到可见模式，手动完成拼图验证即可。

### Q: 如何查看详细的debug信息？
A: 选择调试模式启动，或在搜索时点击"详细信息"按钮。

### Q: 数据提取不完整怎么办？
A: 尝试兼容模式或调整验证严格度设置。

---

**开发团队**: 豫园股份技术部
**更新时间**: 2025年1月  
**版本**: v2.0 