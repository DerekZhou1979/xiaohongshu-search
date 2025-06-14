# GitHub 发布指南

## 📋 发布步骤

### 1. 创建GitHub仓库

1. **登录GitHub**
   - 访问 [GitHub.com](https://github.com)
   - 登录您的账户

2. **创建新仓库**
   - 点击右上角的 "+" 按钮
   - 选择 "New repository"
   - 仓库名称：`xiaohongshu-search`
   - 描述：`一个功能强大的小红书笔记搜索和访问工具，支持智能排序、双重访问方式和自动认证`
   - 设置为 Public（公开）
   - **不要**勾选 "Add a README file"（我们已经有了）
   - **不要**勾选 "Add .gitignore"（我们已经有了）
   - **不要**选择 License（我们已经有了）
   - 点击 "Create repository"

### 2. 连接本地仓库到GitHub

在项目目录中执行以下命令：

```bash
# 添加远程仓库（替换 YOUR_USERNAME 为您的GitHub用户名）
git remote add origin https://github.com/DerekZhou1979/xiaohongshu-search.git

# 推送代码到GitHub
git branch -M main
git push -u origin main
```

### 3. 完善仓库设置

1. **添加仓库描述**
   - 在仓库页面点击 "Edit" 按钮
   - 添加描述：`🔍 小红书搜索工具 - 支持智能排序、双重访问、自动认证`
   - 添加标签：`python`, `flask`, `selenium`, `xiaohongshu`, `web-scraping`, `search-tool`
   - 添加网站：`http://localhost:8080`（如果有在线演示地址可以替换）

2. **设置仓库主题**
   - 在 Settings → General 中设置
   - 确保仓库是 Public
   - 启用 Issues 和 Wiki（如果需要）

### 4. 创建Release版本

1. **创建第一个Release**
   - 在仓库页面点击 "Releases"
   - 点击 "Create a new release"
   - Tag version: `v1.0.0`
   - Release title: `小红书搜索工具 v1.0.0 - 首个正式版本`
   - 描述：
   ```markdown
   ## 🎉 首个正式版本发布！
   
   ### ✨ 主要功能
   - 🔍 智能搜索：支持关键词搜索小红书笔记
   - 📊 智能排序：按评论数降序 + 收藏数降序排列
   - 🌐 双重访问：直接访问和代理访问两种方式
   - 🔐 自动认证：自动处理cookies和xsec_token
   - 🚀 批量提取：一次性获取多条笔记的唯一token
   - 🎨 美观界面：现代化卡片式布局
   - ⚡ 缓存系统：提高搜索效率
   
   ### 🛠️ 技术特性
   - 后端：Flask + Selenium + Requests
   - 前端：HTML5 + CSS3 + JavaScript
   - 核心：xsec_token提取 + 反爬虫处理
   
   ### 📦 安装使用
   ```bash
   git clone https://github.com/YOUR_USERNAME/xiaohongshu-search.git
   cd xiaohongshu-search
   pip install -r requirements.txt
   python app.py
   ```
   
   ### 🚨 注意事项
   - 仅供学习研究使用
   - 请遵守相关法律法规
   - 避免过于频繁的请求
   ```
   - 点击 "Publish release"

## 🔧 后续维护

### 更新代码
```bash
# 添加修改的文件
git add .

# 提交更改
git commit -m "描述您的更改"

# 推送到GitHub
git push origin main
```

### 创建新版本
```bash
# 创建新的标签
git tag v1.1.0

# 推送标签
git push origin v1.1.0
```

然后在GitHub上创建对应的Release。

## 📊 仓库优化建议

### 1. 添加徽章（Badges）
在README.md顶部添加：
```markdown
![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![GitHub stars](https://img.shields.io/github/stars/YOUR_USERNAME/xiaohongshu-search.svg)
![GitHub forks](https://img.shields.io/github/forks/YOUR_USERNAME/xiaohongshu-search.svg)
```

### 2. 添加截图
在static/images/目录下添加应用截图，然后在README中展示：
```markdown
## 📸 应用截图

![搜索界面](static/images/screenshot-search.png)
![结果展示](static/images/screenshot-results.png)
```

### 3. 设置GitHub Pages（可选）
如果要展示静态演示页面：
- Settings → Pages
- Source: Deploy from a branch
- Branch: main
- Folder: /docs 或 / (root)

## 🎯 推广建议

1. **社交媒体分享**
   - 在技术社区分享项目
   - 写技术博客介绍项目

2. **开源社区**
   - 提交到 awesome-python 等列表
   - 参与相关技术讨论

3. **持续改进**
   - 收集用户反馈
   - 定期更新功能
   - 修复bug和优化性能

---

🎉 **恭喜！您的项目现在已经准备好发布到GitHub了！** 