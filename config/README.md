# 配置说明

本目录包含小红书搜索工具的全局配置文件。

## 配置文件

### config.py - 主配置文件

包含所有应用配置参数：

#### 1. 应用配置 (APP_CONFIG)
- `DEBUG`: 调试模式开关
- `HOST`: 服务器监听地址
- `PORT`: 服务器端口
- `SECRET_KEY`: 应用密钥

#### 2. 搜索配置 (SEARCH_CONFIG)
- `DEFAULT_MAX_RESULTS`: 默认搜索结果数量 (30篇)
- `MAX_RESULTS_LIMIT`: 最大搜索结果数量
- `USE_CACHE`: 是否启用缓存
- `CACHE_EXPIRE_TIME`: 缓存过期时间（秒）
- `REQUEST_DELAY`: 请求间隔
- `PAGE_LOAD_TIMEOUT`: 页面加载超时
- `MAX_RETRIES`: 最大重试次数
- `RETRY_DELAY`: 重试间隔

#### 3. 爬虫配置 (CRAWLER_CONFIG)
- `USE_SELENIUM`: 是否使用Selenium
- `HEADLESS`: 是否使用无头模式
- `WINDOW_SIZE`: 浏览器窗口大小
- `CHROME_OPTIONS`: Chrome浏览器选项列表
- `SCROLL_PAUSE_TIME`: 滚动停顿时间
- `SCROLL_COUNT`: 滚动次数
- `ELEMENT_WAIT_TIME`: 元素等待时间

#### 4. 目录配置 (DIRECTORIES)
- `CACHE_DIR`: 缓存目录
- `TEMP_DIR`: 临时文件目录
- `LOGS_DIR`: 日志目录
- `COOKIES_DIR`: Cookie存储目录
- `STATIC_DIR`: 静态文件目录
- `DRIVERS_DIR`: WebDriver目录

#### 5. 文件路径配置 (FILE_PATHS)
- `CHROMEDRIVER_PATH`: ChromeDriver可执行文件路径
- `COOKIES_FILE`: Cookie文件路径

#### 6. URL配置 (URLS)
- `XIAOHONGSHU_BASE`: 小红书基础URL
- `SEARCH_URL_TEMPLATE`: 搜索URL模板
- `LOGIN_URL`: 登录页面URL

#### 7. 热门关键词 (HOT_KEYWORDS)
预设的热门搜索关键词列表

## 使用方法

### 1. 在代码中导入配置

```python
from config.config import (
    SEARCH_CONFIG, CRAWLER_CONFIG, 
    DIRECTORIES, FILE_PATHS, URLS,
    get_config
)

# 获取特定配置
search_config = get_config('SEARCH')
crawler_config = get_config('CRAWLER')

# 获取所有配置
all_config = get_config()
```

### 2. 修改配置

直接编辑 `config.py` 文件中的对应配置项。

### 3. 验证配置

```bash
python3 config/config.py
```

### 4. 创建目录

```python
from config.config import create_directories
create_directories()
```

## 常见问题

### Q: 如何修改默认搜索结果数量？
A: 修改 `SEARCH_CONFIG['DEFAULT_MAX_RESULTS']` 的值。

### Q: 如何修改Chrome浏览器选项？
A: 在 `CRAWLER_CONFIG['CHROME_OPTIONS']` 列表中添加或修改选项。

### Q: 配置验证失败怎么办？
A: 检查错误提示，确保必要的目录存在且ChromeDriver路径正确。

## 注意事项

1. 修改配置后需要重启应用
2. ChromeDriver路径必须正确且可执行
3. 确保有足够的磁盘空间用于缓存和日志 