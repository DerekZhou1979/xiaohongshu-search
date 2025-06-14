# 小红书搜索工具 (XiaoHongShu Search)

一个功能强大的小红书笔记搜索和访问工具，支持智能排序、双重访问方式和自动认证。

## ✨ 功能特性

### 🔍 智能搜索
- **关键词搜索**：支持任意关键词搜索小红书笔记
- **智能排序**：按评论数降序 + 收藏数降序自动排列
- **批量提取**：一次性获取多条笔记信息
- **唯一Token**：为每个笔记生成独特的xsec_token

### 🌐 双重访问方式
- **直接访问**：自动设置cookies并使用增强URL访问
- **代理访问**：通过代理服务器访问，解决网络限制问题
- **自动认证**：两种方式都已自动处理登录认证

### 📊 数据展示
- **美观界面**：现代化的卡片式布局
- **详细信息**：显示标题、描述、作者、互动数据
- **实时更新**：支持缓存和实时搜索切换

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Chrome浏览器
- 网络连接

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

3. **启动服务**
```bash
python app.py
```

4. **访问应用**
打开浏览器访问：`http://localhost:8080`

## 📖 使用说明

### 基本搜索
1. 在搜索框输入关键词（如"美食"、"护肤"等）
2. 点击搜索按钮或按回车键
3. 等待搜索结果加载

### 访问笔记
- **绿色按钮（直接访问）**：自动设置cookies后在新窗口打开
- **红色按钮（代理访问）**：通过代理服务器访问

### 排序规则
搜索结果按以下优先级排序：
1. 评论数降序（优先级最高）
2. 收藏数降序（评论数相同时）

## 🛠️ 技术架构

### 后端技术
- **Flask**：Web框架
- **Selenium**：浏览器自动化
- **Requests**：HTTP请求处理

### 前端技术
- **HTML5/CSS3**：现代化界面
- **JavaScript**：交互逻辑
- **响应式设计**：支持多设备访问

### 核心功能
- **xsec_token提取**：批量提取唯一认证令牌
- **反爬虫处理**：智能绕过检测机制
- **缓存系统**：提高搜索效率
- **代理服务**：解决访问限制

## 📁 项目结构

```
xiaohongshu-search/
├── app.py                 # 主启动文件
├── requirements.txt       # 依赖包列表
├── README.md             # 项目说明
├── src/                  # 源代码目录
│   ├── crawler/          # 爬虫模块
│   └── server/           # 服务器模块
├── static/               # 静态资源
│   ├── css/             # 样式文件
│   ├── js/              # JavaScript文件
│   └── images/          # 图片资源
├── config/              # 配置文件
└── cache/               # 缓存目录
```

## ⚙️ 配置说明

### 搜索配置
在 `config/config.py` 中可以调整：
- 搜索结果数量
- 缓存过期时间
- 请求延迟设置
- 热门关键词

## 🔧 API接口

### 搜索接口
```
GET /api/search?keyword=关键词&max_results=数量&use_cache=true/false
```

### 笔记详情
```
GET /api/note/{note_id}
```

### 热门关键词
```
GET /api/hot-keywords
```

### 代理访问
```
GET /proxy/note/{encoded_url}
```

## 🚨 注意事项

1. **合法使用**：仅供学习研究使用，请遵守相关法律法规
2. **频率控制**：避免过于频繁的请求，以免触发反爬虫机制
3. **Cookie管理**：首次使用可能需要手动登录获取Cookie
4. **网络环境**：确保网络连接稳定，部分功能需要访问外网

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- 感谢小红书平台提供的内容
- 感谢开源社区的技术支持
- 感谢所有贡献者的努力

---

⭐ 如果这个项目对您有帮助，请给个Star支持一下！ 