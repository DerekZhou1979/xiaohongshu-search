# 🚀 小红书搜索工具部署指南

## 📋 部署选项

### 1️⃣ 本地部署

#### 环境要求
- Python 3.9+
- Chrome浏览器
- ChromeDriver

#### 快速启动
```bash
# 克隆仓库
git clone https://github.com/DerekZhou1979/xiaohongshu-search.git
cd xiaohongshu-search

# 安装依赖
pip install -r requirements.txt

# 启动服务
python3 app.py
```

### 2️⃣ Docker部署

#### 使用预构建镜像
```bash
# 拉取镜像
docker pull derekzhou1979/xiaohongshu-search:latest

# 运行容器
docker run -d \
  --name xiaohongshu-search \
  -p 8080:8080 \
  -v $(pwd)/cache:/app/cache \
  derekzhou1979/xiaohongshu-search:latest
```

#### 从源码构建
```bash
# 构建镜像
docker build -t xiaohongshu-search .

# 运行容器
docker run -d \
  --name xiaohongshu-search \
  -p 8080:8080 \
  -v $(pwd)/cache:/app/cache \
  xiaohongshu-search
```

### 3️⃣ Docker Compose部署

创建 `docker-compose.yml` 文件：
```yaml
version: '3.8'
services:
  xiaohongshu-search:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./cache:/app/cache
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
```

启动服务：
```bash
docker-compose up -d
```

### 4️⃣ 云平台部署

#### Railway部署
1. Fork项目到你的GitHub账户
2. 在Railway连接你的GitHub仓库
3. 设置环境变量（如需要）
4. 自动部署完成

#### Heroku部署
1. 创建Heroku应用：
```bash
heroku create your-app-name
```

2. 设置构建包：
```bash
heroku buildpacks:set https://github.com/heroku/heroku-buildpack-google-chrome
heroku buildpacks:add https://github.com/heroku/heroku-buildpack-chromedriver
heroku buildpacks:add heroku/python
```

3. 部署：
```bash
git push heroku main
```

#### DigitalOcean App Platform
1. 连接GitHub仓库
2. 选择Docker部署
3. 设置环境变量
4. 部署完成

## 🔧 配置说明

### 环境变量
```bash
# 服务端口（默认：8080）
PORT=8080

# Flask密钥
SECRET_KEY=your-secret-key

# ChromeDriver路径（可选，会自动下载）
CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# 运行模式（1-5）
RUN_MODE=1
```

### 数据持久化
确保挂载以下目录：
- `/app/cache` - 缓存和日志
- `/app/cache/cookies` - 登录状态
- `/app/cache/results` - 搜索结果

## 🔐 安全配置

### 生产环境建议
1. 设置强密码的SECRET_KEY
2. 使用HTTPS
3. 配置防火墙规则
4. 定期更新依赖
5. 监控日志和性能

### 访问控制
如需要访问控制，可以使用Nginx反向代理：
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🚨 故障排除

### 常见问题

1. **ChromeDriver版本不匹配**
   ```bash
   # 手动安装匹配版本的ChromeDriver
   ```

2. **端口被占用**
   ```bash
   # 检查端口使用
   lsof -i :8080
   
   # 杀死占用进程
   kill -9 <PID>
   ```

3. **内存不足**
   ```bash
   # 增加swap空间或升级服务器配置
   ```

### 日志查看
```bash
# Docker容器日志
docker logs xiaohongshu-search

# 本地部署日志
tail -f cache/logs/backend_crawler.log
```

## 📊 监控与维护

### 健康检查
```bash
# 检查服务状态
curl http://localhost:8080/api/health

# 检查容器状态
docker ps | grep xiaohongshu-search
```

### 性能监控
- CPU使用率
- 内存使用率
- 网络连接数
- 响应时间

### 定期维护
1. 清理缓存文件
2. 更新依赖包
3. 备份重要数据
4. 检查日志错误

## 🔄 自动部署

项目已配置GitHub Actions，每次推送到main分支时自动：
1. 运行测试
2. 构建Docker镜像
3. 部署到云平台
4. 更新文档

## 📞 支持

如遇到问题，请：
1. 查看故障排除部分
2. 检查GitHub Issues
3. 提交新的Issue
4. 联系维护者

---

🌟 **快速部署命令**
```bash
# 一键Docker部署
curl -sSL https://raw.githubusercontent.com/DerekZhou1979/xiaohongshu-search/main/scripts/quick-deploy.sh | bash
``` 