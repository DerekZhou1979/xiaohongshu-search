# 豫园股份-小红书搜索工具

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![Selenium](https://img.shields.io/badge/Selenium-4.15+-orange.svg)](https://selenium.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/DerekZhou1979/xiaohongshu-search.svg)](https://github.com/DerekZhou1979/xiaohongshu-search/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/DerekZhou1979/xiaohongshu-search.svg)](https://github.com/DerekZhou1979/xiaohongshu-search/network)
[![GitHub issues](https://img.shields.io/github/issues/DerekZhou1979/xiaohongshu-search.svg)](https://github.com/DerekZhou1979/xiaohongshu-search/issues)

一个专业的小红书内容搜索工具，支持关键词搜索、笔记数据提取、实时debug信息显示、人工验证处理和智能反爬虫技术。

## 🌟 主要特性

### 核心功能
- **智能搜索**: 支持关键词搜索小红书笔记内容
- **多策略提取**: 三种数据提取策略确保高成功率
- **🆕 后台笔记内容提取**: 自动深度挖掘笔记详细内容和图片
- **🆕 人为行为模拟**: 智能模拟人类浏览行为，大幅降低被检测风险
- **人工验证**: 自动检测验证码，支持人工处理
- **实时监控**: 前台实时显示搜索过程的debug信息
- **数据完整**: 提取标题、描述、作者、互动数据、标签、图片等完整信息
- **AI笔记生成**: 基于搜索结果生成同类笔记内容，支持一键跳转小红书创作页面

### 🛡️ 高级反反爬虫技术
- **浏览器指纹隐蔽**: 完全隐藏Selenium自动化特征
- **人类行为模拟**: 随机鼠标移动、页面滚动、停留时间
- **智能等待策略**: 时段感知的动态等待时间
- **错误检测与重试**: 自动识别"你访问的笔记不见了"并智能重试
- **分批处理**: 避免连续高频访问，降低封锁风险
- **Cookie管理**: 自动保存和加载用户登录状态

### 技术特色
- **缓存系统**: 智能缓存减少重复请求
- **配置化**: 支持5种运行模式，满足不同使用场景
- **错误恢复**: 完善的错误处理和恢复机制
- **实时调试**: 页面源码保存，便于问题诊断

## 📁 项目结构

```
xiaohongshu-search/
├── app.py                      # 主程序入口，配置选择和服务启动
├── simple_refresh_cookies.py   # Cookie刷新工具
├── start_servers.py           # 服务启动脚本（简化版）
├── requirements.txt           # Python依赖包
├── requirements_note_generation.txt  # 🆕 笔记生成功能专用依赖
├── MANIFEST.in               # 包管理文件
├── README.md                 # 项目文档
├── 
├── src/                      # 源代码目录
│   ├── crawler/              # 爬虫核心模块
│   │   ├── XHS_crawler.py    # 小红书搜索爬虫主类
│   │   └── backend_XHS_crawler.py  # 🆕 后台笔记内容深度爬虫（反反爬技术）
│   └── server/               # 服务器模块
│       ├── main_server.py    # 主服务器（API + Web界面）
│       ├── debug_manager.py  # Debug信息管理器
│       └── note_generator.py # 笔记内容生成器
├── 
├── static/                   # 前端静态文件
│   ├── index.html           # 主页面
│   ├── css/
│   │   └── style.css        # 样式文件
│   └── js/
│       ├── api.js          # API客户端
│       └── script.js       # 前端交互逻辑
├── 
├── cache/                   # 🆕 统一缓存目录
│   ├── cookies/            # Cookie存储
│   ├── temp/               # 临时文件和调试截图
│   ├── results/            # 搜索结果HTML页面
│   ├── logs/               # 日志文件
│   ├── notes/              # 🆕 后台提取的笔记内容和图片
│   └── note_generation_debug/  # 🆕 笔记生成调试信息
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
- **内存**: 建议8GB+（用于浏览器自动化）

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-username/xiaohongshu-search.git
cd xiaohongshu-search
```

2. **安装依赖**
```bash
# 安装基础依赖
pip install -r requirements.txt

# 安装笔记生成功能依赖（可选）
pip install -r requirements_note_generation.txt
```

3. **下载ChromeDriver**
   - 自动下载或手动下载适合您系统的ChromeDriver
   - 放置在 `drivers/` 目录下

4. **启动服务**
```bash
python app.py
# 或使用简化启动脚本
python start_servers.py
```

### 运行模式选择

程序启动时会显示5种运行模式选择：

1. **标准模式（推荐）**
   - 启用所有提取策略
   - 关闭调试截图
   - 适中的验证严格度
   - ✅ **启用后台笔记内容提取**

2. **调试模式**
   - 启用所有策略
   - 开启详细截图和debug信息
   - 保存所有调试数据
   - ✅ **启用后台笔记内容提取**

3. **快速模式**
   - 仅启用策略1（最快）
   - 关闭截图和详细日志
   - 降低验证严格度
   - ❌ **关闭后台笔记内容提取**（提升性能）

4. **兼容模式**
   - 启用所有策略
   - 关闭截图
   - 最低验证严格度
   - ✅ **启用后台笔记内容提取**

5. **自定义模式**
   - 手动配置各项功能
   - 完全个性化设置
   - 🔧 **可选择后台笔记内容提取**

## 🔧 使用方法

### Web界面使用

1. 访问 `http://localhost:8080`
2. 在搜索框输入关键词（如：老庙黄金、海鸥表）
3. 点击搜索或选择豫园品牌快捷搜索
4. 实时查看搜索过程的debug信息
5. 查看搜索结果页面
6. **🆕 后台自动提取**: 程序会在后台自动深度提取每个笔记的详细内容

### 🆕 后台笔记内容提取功能

当启用后台提取功能时，程序会自动：

1. **智能访问**: 使用人为行为模式逐个访问笔记页面
2. **深度提取**: 获取完整的笔记内容、图片、作者信息
3. **文件保存**: 
   - 笔记内容 → `cache/notes/batch_{session_id}_results.json`
   - 页面源码 → `cache/notes/{note_id}_{session_id}_source.html`
   - 图片文件 → `cache/notes/{note_id}_images/`
4. **实时监控**: 在Web界面查看提取进度

### 验证码处理

当遇到验证码时：

1. **自动检测**: 程序自动检测验证码页面
2. **浏览器激活**: 自动切换到可见模式并激活浏览器窗口  
3. **人工处理**: 用户手动完成拼图验证
4. **自动继续**: 验证完成后程序自动继续

### 🛡️ 反反爬虫策略处理

遇到"你访问的笔记不见了"时，程序会自动：

1. **错误检测**: 识别反爬虫页面特征
2. **智能重试**: 使用新的浏览器实例重试（最多3次）
3. **延长等待**: 重试前等待10-20秒
4. **行为模拟**: 每次重试都模拟不同的人类行为
5. **长休息**: 每5个笔记后休息30-60秒

### 实时Debug信息

搜索过程中可以看到：
- 🔍 搜索开始和关键词
- 🚀 浏览器初始化状态
- 🔗 搜索URL尝试过程
- 🛡️ 反爬虫检测结果
- 📄 页面内容加载状态
- 🔧 三种提取策略执行情况
- 🤖 **后台提取任务启动状态**
- 🎭 **人为行为模拟过程**
- ⏱️ **智能等待策略执行**
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

### 基础搜索数据
每个笔记包含以下信息：
- **基础信息**: ID、URL、标题、描述、作者
- **媒体内容**: 封面图片URL
- **互动数据**: 点赞数、评论数、收藏数、浏览数
- **标签信息**: 相关话题标签
- **安全令牌**: xsec_token用于直接访问

### 🆕 后台深度提取数据
后台提取功能额外获取：
- **完整标题**: 页面完整标题
- **详细描述**: 笔记完整正文内容
- **作者详情**: 作者昵称和个人信息
- **统计数据**: 详细的互动统计
- **图片集合**: 所有笔记图片的高清版本
- **页面源码**: 原始HTML源码（用于调试）

## 🛡️ 反反爬虫技术详解

### 浏览器指纹隐蔽
```python
# 禁用webdriver检测
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

# 隐藏navigator.webdriver标识
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
```

### 人类行为模拟
- **随机鼠标移动**: 1-3次随机坐标移动
- **自然页面滚动**: 1-3次随机高度滚动
- **动态停留时间**: 5-15秒随机停留
- **随机用户代理**: 从真实浏览器UA池中随机选择

### 智能等待策略
```python
# 基础等待时间：3-8秒
base_wait = random.uniform(3, 8)

# 时段感知调整
if 23 <= hour <= 6:     # 夜间延长50%
    base_wait *= 1.5
elif 12 <= hour <= 14:  # 午休延长20%
    base_wait *= 1.2
```

### 错误检测与重试
- **检测关键词**: "你访问的笔记不见了"、"页面不存在"、"网络异常"
- **重试机制**: 最多3次，每次使用全新浏览器实例
- **重试间隔**: 10-20秒随机延长等待
- **批量休息**: 每5个笔记后强制休息30-60秒

## ⚙️ 配置说明

### 缓存配置
- **搜索缓存**: 1小时有效期
- **结果页面**: 自动生成HTML页面
- **调试截图**: 可配置开启/关闭
- **🆕 笔记内容**: 保存在`cache/notes/`目录

### 反爬虫配置
- **人为行为模拟**: 可在自定义模式中开启/关闭
- **等待时间范围**: 3-8秒基础，时段自动调整
- **重试次数**: 默认3次，可配置
- **批量处理**: 每5个笔记休息，可调整

### 验证严格度
- **低**: 接受大部分结果
- **中等**: 平衡准确性和数量  
- **高**: 严格验证相关性

## 🔍 API接口

### 基础接口
```bash
# 搜索接口
GET /api/search?keyword={keyword}&max_results={num}&session_id={id}

# Debug信息接口
GET /api/debug/{session_id}?since={timestamp}

# 笔记详情接口
GET /api/note/{note_id}

# 热门关键词接口
GET /api/hot-keywords
```

### 🆕 笔记生成相关接口
```bash
# 创建同类笔记
POST /api/create-similar-note/{note_id}

# 笔记生成Debug信息
GET /api/note-generation-debug/{session_id}
```

### 🆕 后台提取相关接口
```bash
# 后台提取状态
GET /api/backend-status/{session_id}

# 提取结果查看
GET /cache/notes/batch_{session_id}_results.json
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
- **🆕 后台提取较慢**: 为了避免被检测，提取速度会比较慢

### 隐私安全
- Cookie数据存储在本地
- 不会上传用户个人信息
- 调试截图仅本地保存
- 可以随时清理缓存数据
- **🆕 页面源码**: 仅本地保存，不会外传

### 🛡️ 反爬虫最佳实践
1. **避免高频使用**: 建议每次搜索间隔至少5分钟
2. **选择合适时段**: 避免在深夜或工作时间高频使用
3. **控制搜索数量**: 单次搜索建议不超过50个结果
4. **定期更新Cookie**: 使用`simple_refresh_cookies.py`更新登录状态
5. **监控日志信息**: 及时发现和处理异常情况

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

### 开发建议
- 添加新的反爬虫策略时，请在`backend_XHS_crawler.py`中实现
- 增强人为行为模拟功能，可以参考`simulate_human_behavior`方法
- 优化等待策略，可以修改`smart_wait_between_requests`方法

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

### 🆕 Q: 后台提取总是失败，显示"你访问的笔记不见了"怎么办？
A: 
1. **选择兼容模式**: 使用最强的反反爬虫设置
2. **等待更长时间**: 在搜索间隔增加更多等待时间
3. **更新Cookie**: 使用`simple_refresh_cookies.py`刷新登录状态
4. **分批次处理**: 减少单次搜索的结果数量
5. **检查IP**: 如果频繁失败，可能需要更换网络环境

### 🆕 Q: 如何关闭后台笔记内容提取功能？
A: 在启动时选择"快速模式"或"自定义模式"中关闭该功能。

### 🆕 Q: 后台提取的文件保存在哪里？
A: 所有文件保存在`cache/notes/`目录下：
- 提取结果：`batch_{session_id}_results.json`
- 页面源码：`{note_id}_{session_id}_source.html`
- 图片文件：`{note_id}_images/`目录

### 🆕 Q: 人为行为模拟包括哪些动作？
A: 包括随机鼠标移动、页面滚动、动态停留时间、随机窗口大小、时段感知等待等。

---

**开发团队**: 豫园股份技术部  
**最新更新**: 2025年1月 - 反反爬虫技术大幅升级  
**版本**: v3.0 - 智能人为行为模拟版 