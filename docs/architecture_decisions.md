# ROS2 Wiki 架构决策记录 (ADR)

## ADR-001: 数据库选择

### 状态
待决策

### 背景
当前使用SQLite作为数据库，需要评估是否满足未来需求。

### 决策因素

| 因素 | SQLite | PostgreSQL | MySQL |
|------|---------|------------|--------|
| 并发性能 | 差（写锁） | 优秀 | 良好 |
| 部署复杂度 | 简单（文件） | 中等 | 中等 |
| 全文搜索 | 需要扩展 | 原生支持 | 需要扩展 |
| JSON支持 | 基础 | 优秀 | 良好 |
| 备份恢复 | 文件复制 | 专业工具 | 专业工具 |
| 成本 | 免费 | 免费 | 免费 |

### 推荐方案
1. **开发阶段**：继续使用SQLite
2. **生产环境**：迁移到PostgreSQL
3. **实施步骤**：
   - 使用SQLAlchemy ORM保证数据库无关性
   - 编写数据迁移脚本
   - 使用Docker简化PostgreSQL部署

## ADR-002: 前后端架构

### 状态
待决策

### 背景
当前使用服务端渲染，需要评估是否采用前后端分离。

### 选项分析

#### 选项1：保持现状（服务端渲染）
**优点**：
- SEO友好
- 开发简单
- 部署方便

**缺点**：
- 用户体验受限
- 难以支持移动端
- 无法实现复杂交互

#### 选项2：渐进式改造
**方案**：
- 保留服务端渲染作为基础
- 为关键功能添加API端点
- 使用Vue/React增强交互体验

**实施计划**：
1. 添加RESTful API（/api/v1/）
2. 文档编辑器改用前端框架
3. 实现实时预览功能
4. 逐步迁移其他功能

#### 选项3：完全前后端分离
**优点**：
- 最佳用户体验
- 支持多端（Web/Mobile/Desktop）
- 便于团队协作开发

**缺点**：
- SEO需要额外处理（SSR/SSG）
- 部署复杂度增加
- 开发成本高

### 推荐方案
采用**选项2：渐进式改造**，原因：
1. 风险可控，不影响现有功能
2. 可以根据实际需求调整进度
3. 保留SEO优势的同时提升体验

## ADR-003: 测试策略

### 状态
立即执行

### 背景
项目目前没有任何测试，存在重大质量风险。

### 测试金字塔

```
        E2E测试 (10%)
       /           \
    集成测试 (30%)
   /               \
单元测试 (60%)
```

### 实施计划

#### 第一阶段：基础设施
1. 安装pytest和相关工具
2. 配置测试环境
3. 编写第一个测试

#### 第二阶段：核心功能测试
1. 用户认证测试
2. 文档CRUD测试
3. 权限控制测试

#### 第三阶段：自动化
1. CI/CD集成
2. 代码覆盖率报告
3. 自动化测试运行

### 示例测试代码
```python
# tests/test_auth.py
def test_user_registration(client):
    """测试用户注册功能"""
    response = client.post('/auth/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'Test123!@#'
    })
    assert response.status_code == 302
    assert User.query.filter_by(username='testuser').first() is not None

def test_login_with_valid_credentials(client, test_user):
    """测试有效凭证登录"""
    response = client.post('/auth/login', data={
        'username': test_user.username,
        'password': 'password123'
    })
    assert response.status_code == 302
    assert current_user.is_authenticated
```

## ADR-004: API设计原则

### RESTful API规范

```yaml
# API版本化
/api/v1/

# 资源命名（复数）
/api/v1/documents
/api/v1/users
/api/v1/comments

# HTTP方法语义
GET    /documents     # 列表
GET    /documents/1   # 详情
POST   /documents     # 创建
PUT    /documents/1   # 更新
DELETE /documents/1   # 删除

# 查询参数
/api/v1/documents?category=tutorial&page=1&per_page=20

# 响应格式
{
  "data": {...},
  "meta": {
    "page": 1,
    "total": 100
  },
  "links": {
    "self": "/api/v1/documents?page=1",
    "next": "/api/v1/documents?page=2"
  }
}
```