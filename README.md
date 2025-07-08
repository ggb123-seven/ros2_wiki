# ROS2 Wiki - 技术教育网站

一个简单而功能完整的ROS2技术教育网站，支持用户注册、文档管理、评论互动等功能。

## 功能特点

- ✅ 用户注册登录系统
- ✅ ROS2教程文档展示
- ✅ Markdown文档渲染
- ✅ 代码语法高亮
- ✅ 评论系统
- ✅ 响应式设计
- ✅ 文档API接口

## 技术栈

- **后端**: Python Flask + SQLite
- **前端**: HTML/CSS/JavaScript + Bootstrap
- **认证**: Flask-Login
- **文档**: Markdown + Pygments
- **代码高亮**: highlight.js

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
cd /home/sevenseven/ros2_wiki

# 安装依赖
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
# 初始化示例数据
python init_sample_data.py
```

### 3. 运行应用

```bash
# 启动开发服务器
python app.py
```

访问 http://localhost:5000 即可使用。

## 默认账户

- **管理员**: admin / admin123
- **用户**: ros2_learner / user123

## 项目结构

```
ros2_wiki/
├── app.py                 # 主应用文件
├── requirements.txt       # 依赖包
├── init_sample_data.py   # 示例数据初始化
├── ros2_wiki.db          # SQLite数据库（运行后生成）
├── static/
│   ├── css/
│   │   └── style.css     # 自定义样式
│   └── js/               # JavaScript文件
└── templates/
    ├── base.html         # 基础模板
    ├── index.html        # 首页
    ├── login.html        # 登录页
    ├── register.html     # 注册页
    └── document.html     # 文档详情页
```

## API接口

### 文档渲染API

```
GET /api/documents/{id}/render-html
```

返回指定文档的HTML渲染结果。

**响应示例**:
```json
{
  "id": 1,
  "title": "ROS2快速入门指南",
  "html_content": "<h1>ROS2快速入门指南</h1>...",
  "category": "ROS2基础",
  "created_at": "2023-12-07 10:00:00"
}
```

## 功能说明

### 用户系统
- 用户注册（用户名、邮箱、密码）
- 用户登录/退出
- 登录状态管理

### 文档系统
- 教程列表展示
- 分类管理
- Markdown内容渲染
- 代码语法高亮
- 自动生成目录

### 评论系统
- 用户可对教程发表评论
- 评论列表展示
- 需要登录才能评论

### 响应式设计
- 支持桌面和移动设备
- Bootstrap响应式布局
- 友好的用户体验

## 扩展功能

后续可以添加的功能：

1. **内容管理系统**
   - 管理员可在线编辑教程
   - 文档版本管理
   - 富文本编辑器

2. **搜索功能**
   - 全文搜索
   - 标签系统
   - 分类筛选

3. **用户增强**
   - 用户个人资料
   - 用户权限管理
   - 评论回复功能

4. **部署优化**
   - Docker部署
   - 生产环境配置
   - 数据库迁移

## 贡献

欢迎提交Issue和Pull Request来改进项目！

## 许可证

MIT License