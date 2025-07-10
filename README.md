# ROS2 Wiki Enhanced - 现代化机器人学习平台

一个功能完整、现代化的ROS2技术教育网站，采用轻量级架构，支持用户管理、文档系统、评论互动和管理后台等全套功能。

## ✨ 主要特色

### 🚀 核心功能
- ✅ **现代化UI设计** - Bootstrap 5 + 渐变背景 + FontAwesome图标
- ✅ **用户认证系统** - 注册/登录/会话管理/权限控制
- ✅ **文档管理系统** - Markdown渲染/语法高亮/分类管理
- ✅ **搜索功能** - 全文搜索/关键词高亮/结果统计
- ✅ **评论系统** - 用户互动/实时评论/评论管理
- ✅ **管理后台** - 数据统计/用户管理/文档管理/系统监控

### 🛠️ 技术特点
- **零依赖设计** - 仅使用Python标准库，无需安装额外包
- **轻量级架构** - 单文件部署，SQLite数据库
- **响应式设计** - 支持桌面、平板、手机访问
- **云平台友好** - 支持Render、Heroku等云部署
- **安全可靠** - 密码加密、会话管理、权限验证

### 📊 系统监控
- **健康检查API** - 系统状态实时监控
- **性能指标** - 数据库响应时间、内存使用
- **功能模块检查** - 自动检测所有核心功能
- **导出报告** - 一键导出系统状态报告

## 🚀 快速开始

### 本地运行

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd ros2_wiki

# 2. 运行服务器（无需安装依赖）
python3 enhanced_server.py

# 3. 访问应用
# 本地: http://localhost:8000
# 管理后台: http://localhost:8000/admin
```

### 云平台部署 (Render)

1. Fork此仓库到你的GitHub账户
2. 在[Render.com](https://render.com)创建新的Web Service
3. 连接你的GitHub仓库
4. 设置部署配置：
   - **Build Command**: `echo "No build required"`
   - **Start Command**: `python3 enhanced_server.py`
   - **Environment**: Python 3

## 📱 默认账户

| 角色 | 用户名 | 密码 | 权限 |
|------|---------|-------|------|
| 管理员 | `admin` | `admin123` | 完整管理权限 |
| 普通用户 | `ros2_user` | `user123` | 查看和评论 |

## 🏗️ 项目结构

```
ros2_wiki/
├── enhanced_server.py      # 主服务器程序（增强版）
├── simple_server.py        # 简化版服务器
├── start.py                # 生产环境启动脚本
├── requirements.txt        # 依赖声明（空文件，仅标准库）
├── .gitignore             # Git忽略配置
├── README.md              # 项目文档
├── templates/             # HTML模板（Flask风格）
│   ├── base.html         # 基础模板
│   ├── admin/            # 管理后台模板
│   └── ...               # 其他页面模板
└── simple_wiki.db        # SQLite数据库（运行时生成）
```

## 🔧 技术架构

### 后端技术栈
- **Python 3** - 核心语言
- **http.server** - 内置HTTP服务器
- **SQLite** - 轻量级数据库
- **hashlib** - 密码加密
- **datetime** - 时间处理
- **json/urllib** - 数据处理

### 前端技术栈
- **Bootstrap 5** - 响应式UI框架
- **FontAwesome 6** - 图标库
- **Highlight.js** - 代码语法高亮
- **Vanilla JavaScript** - 原生JS交互

### 数据库设计
```sql
-- 用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    email TEXT,
    password_hash TEXT,
    is_admin BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 文档表
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    title TEXT,
    content TEXT,
    category TEXT DEFAULT "ROS2基础",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 评论表
CREATE TABLE comments (
    id INTEGER PRIMARY KEY,
    document_id INTEGER,
    username TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 📡 API接口

### 健康检查API
```bash
# HTML格式（可视化面板）
GET http://localhost:8000/api/health

# JSON格式（API调用）
curl -H "Accept: application/json" http://localhost:8000/api/health
```

**JSON响应示例**:
```json
{
  "status": "healthy",
  "database": {
    "status": "ok",
    "response_time": 0.29,
    "version": "3.45.1",
    "tables": 4
  },
  "statistics": {
    "users": 2,
    "documents": 2,
    "comments": 1,
    "admins": 1
  },
  "features": {
    "数据库连接": true,
    "会话管理": true,
    "Markdown渲染": true,
    "用户认证": true,
    "搜索功能": true,
    "评论系统": true
  },
  "runtime": {
    "version": "Python 3.12.3",
    "platform": "Linux",
    "memory": "6705MB可用"
  }
}
```

## 🎯 功能详解

### 用户认证系统
- **安全注册** - 用户名唯一性检查、密码确认验证
- **会话管理** - Cookie-based会话、自动过期
- **权限控制** - 管理员权限、功能访问控制

### 文档管理系统
- **Markdown支持** - 完整Markdown语法渲染
- **代码高亮** - 支持多种编程语言语法高亮
- **分类管理** - 文档分类展示和管理
- **目录生成** - 自动生成文档目录导航

### 搜索功能
- **全文搜索** - 标题和内容全文搜索
- **关键词高亮** - 搜索结果关键词高亮显示
- **统计信息** - 搜索结果数量和相关度

### 管理后台
- **仪表板** - 系统概览、数据统计、快速操作
- **用户管理** - 用户列表、权限管理、活动监控
- **内容管理** - 文档CRUD、分类管理、批量操作
- **系统监控** - 实时状态、性能指标、健康检查

## 🌐 部署选项

### 1. Render.com (推荐)
- 免费tier支持
- 自动HTTPS
- 全球CDN
- 零配置部署

### 2. Heroku
- 支持免费dyno
- Git部署
- 插件生态

### 3. Railway
- 现代化平台
- GitHub集成
- 实时日志

### 4. 自托管
- VPS/云服务器
- Docker容器
- 反向代理

## 🔒 安全特性

- **密码加密** - SHA256+盐值加密存储
- **会话安全** - 随机UUID会话ID
- **权限验证** - 基于角色的访问控制
- **输入验证** - 防止SQL注入和XSS攻击
- **HTTPS支持** - 云平台自动启用

## 📈 性能优化

- **轻量级设计** - 零外部依赖
- **高效数据库** - SQLite优化查询
- **缓存策略** - 静态资源缓存
- **压缩传输** - Gzip压缩支持

## 🚀 扩展功能

计划中的功能增强：

1. **内容编辑器**
   - 在线Markdown编辑器
   - 实时预览
   - 图片上传支持

2. **用户体验**
   - 主题切换（深色/浅色）
   - 多语言支持
   - 无障碍访问优化

3. **数据分析**
   - 用户行为分析
   - 内容热度统计
   - 访问量监控

4. **API扩展**
   - RESTful API
   - 第三方集成
   - Webhook支持

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork项目
2. 创建功能分支
3. 提交代码变更
4. 创建Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

🤖 **ROS2 Wiki Enhanced** - 让机器人学习更简单、更现代！