# 文件系统功能指南

## 🎯 功能概述

ROS2 Wiki现在包含完整的文件管理系统，支持文件上传、下载、管理和在文档中引用。该系统专门为Render平台优化，提供可靠的文件存储和管理功能。

## 📋 功能特性

### 1. 文件上传
- **支持格式**：txt, pdf, png, jpg, jpeg, gif, doc, docx, xls, xlsx, ppt, pptx, md, zip, rar
- **文件大小**：最大10MB
- **安全检查**：文件名安全化、类型验证、大小限制
- **去重机制**：基于MD5哈希值的文件去重

### 2. 文件管理
- **个人文件**：每个用户管理自己的文件
- **文件信息**：显示文件名、大小、类型、上传时间
- **操作功能**：下载、删除、查看详情
- **权限控制**：只能操作自己上传的文件

### 3. 文件存储
- **存储位置**：`/tmp/uploads`（适配Render平台）
- **文件命名**：UUID + 原始扩展名
- **数据库记录**：完整的文件元数据
- **安全性**：防止路径遍历攻击

### 4. 文件引用
- **文档附件**：在文档中引用相关文件
- **下载链接**：提供直接下载功能
- **文件预览**：显示文件信息和缩略图

## 🔧 技术实现

### 数据库表结构

#### PostgreSQL版本
```sql
CREATE TABLE files (
    id VARCHAR(36) PRIMARY KEY,
    original_name VARCHAR(255) NOT NULL,
    safe_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    file_hash VARCHAR(32),
    mime_type VARCHAR(100),
    user_id INTEGER REFERENCES users(id),
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### SQLite版本
```sql
CREATE TABLE files (
    id TEXT PRIMARY KEY,
    original_name TEXT NOT NULL,
    safe_filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    file_hash TEXT,
    mime_type TEXT,
    user_id INTEGER,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

### 核心类和方法

#### FileManager类
```python
class FileManager:
    def __init__(self):
        self.upload_folder = '/tmp/uploads'
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_extensions = {...}
    
    def save_file(self, file, user_id):
        """保存文件并返回文件信息"""
    
    def get_file_info(self, file_id):
        """获取文件信息"""
    
    def delete_file(self, file_id, user_id):
        """删除文件"""
    
    def get_user_files(self, user_id, limit=50):
        """获取用户文件列表"""
```

### API路由

| 路由 | 方法 | 功能 | 权限 |
|------|------|------|------|
| `/files` | GET | 文件管理页面 | 登录用户 |
| `/upload` | POST | 上传文件 | 登录用户 |
| `/download/<file_id>` | GET | 下载文件 | 登录用户 |
| `/delete_file/<file_id>` | POST | 删除文件 | 文件所有者 |
| `/file_info/<file_id>` | GET | 获取文件信息 | 登录用户 |

## 🚀 使用方法

### 1. 上传文件
```html
<!-- 在文件管理页面 -->
<form method="POST" action="/upload" enctype="multipart/form-data">
    <input type="file" name="file" accept=".txt,.pdf,.png,.jpg,.jpeg,.gif,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.md,.zip,.rar">
    <button type="submit">上传</button>
</form>
```

### 2. 文件列表
```python
# 获取用户文件
user_files = file_manager.get_user_files(current_user.id)

# 模板中显示
{% for file in files %}
    <div class="file-item">
        <span>{{ file.original_name }}</span>
        <span>{{ file.file_size|format_file_size }}</span>
        <a href="{{ url_for('download_file', file_id=file.id) }}">下载</a>
    </div>
{% endfor %}
```

### 3. 文件下载
```python
@app.route('/download/<file_id>')
@login_required
def download_file(file_id):
    file_info = file_manager.get_file_info(file_id)
    return send_file(
        file_info['file_path'],
        as_attachment=True,
        download_name=file_info['original_name']
    )
```

### 4. 文件删除
```python
@app.route('/delete_file/<file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    success, message = file_manager.delete_file(file_id, current_user.id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('files'))
```

## 🔒 安全特性

### 1. 文件名安全
- 使用`secure_filename()`防止路径遍历
- UUID重命名避免文件名冲突
- 保留原始文件名显示

### 2. 类型验证
- 白名单验证文件扩展名
- MIME类型检查
- 文件大小限制

### 3. 权限控制
- 用户只能操作自己的文件
- 登录验证
- 文件所有者验证

### 4. 路径安全
- 绝对路径存储
- 防止目录遍历攻击
- 安全的文件访问

## 📊 性能优化

### 1. 缓存机制
```python
@cache_result('user_files', ttl=300)  # 5分钟缓存
def get_user_files(user_id):
    # 获取用户文件列表
```

### 2. 数据库优化
- 索引优化：user_id, upload_time
- 分页查询：限制返回结果数量
- 连接复用：减少数据库连接开销

### 3. 文件去重
- MD5哈希值检查
- 避免重复存储相同文件
- 节省存储空间

## 🌐 Render平台适配

### 1. 存储位置
```python
# 使用Render平台临时目录
self.upload_folder = '/tmp/uploads'
```

### 2. 文件生命周期
- **上传后**：立即可用
- **重启后**：文件可能丢失
- **建议**：重要文件需要外部备份

### 3. 资源限制
- **磁盘空间**：临时存储有限
- **内存使用**：控制文件处理内存占用
- **请求超时**：大文件上传需要合理的超时设置

## 📝 使用示例

### 1. 基本文件上传
```python
# 在文档编辑页面添加文件上传
<div class="file-upload-section">
    <h5>添加附件</h5>
    <form method="POST" action="{{ url_for('upload_file') }}" enctype="multipart/form-data">
        <div class="input-group">
            <input type="file" class="form-control" name="file">
            <button class="btn btn-primary" type="submit">上传</button>
        </div>
    </form>
</div>
```

### 2. 文件预览
```html
<!-- 图片文件预览 -->
{% if file.mime_type.startswith('image/') %}
    <img src="{{ url_for('download_file', file_id=file.id) }}" 
         alt="{{ file.original_name }}" 
         class="img-thumbnail" 
         style="max-width: 200px;">
{% endif %}
```

### 3. 文件统计
```python
def get_file_statistics(user_id):
    """获取用户文件统计"""
    files = file_manager.get_user_files(user_id)
    total_size = sum(file['file_size'] for file in files)
    file_types = {}
    
    for file in files:
        ext = file['original_name'].split('.')[-1].lower()
        file_types[ext] = file_types.get(ext, 0) + 1
    
    return {
        'total_files': len(files),
        'total_size': total_size,
        'file_types': file_types
    }
```

## 🔧 维护和监控

### 1. 清理策略
```python
def cleanup_old_files(days=30):
    """清理超过指定天数的文件"""
    cutoff_date = datetime.now() - timedelta(days=days)
    # 查找并删除旧文件
```

### 2. 空间监控
```python
def get_storage_usage():
    """获取存储使用情况"""
    total_size = 0
    file_count = 0
    
    for root, dirs, files in os.walk('/tmp/uploads'):
        for file in files:
            file_path = os.path.join(root, file)
            total_size += os.path.getsize(file_path)
            file_count += 1
    
    return {
        'total_size': total_size,
        'file_count': file_count,
        'formatted_size': format_file_size(total_size)
    }
```

### 3. 健康检查
```python
@app.route('/api/files/health')
def files_health_check():
    """文件系统健康检查"""
    try:
        # 检查上传目录
        upload_dir_exists = os.path.exists('/tmp/uploads')
        
        # 检查磁盘空间
        disk_usage = get_storage_usage()
        
        return jsonify({
            'status': 'healthy',
            'upload_dir': upload_dir_exists,
            'storage': disk_usage
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500
```

## 🎉 总结

文件系统功能为ROS2 Wiki提供了完整的文件管理能力，包括：

- ✅ **完整的文件上传下载功能**
- ✅ **安全的文件存储机制**
- ✅ **用户友好的文件管理界面**
- ✅ **适配Render平台的存储策略**
- ✅ **完善的错误处理和用户反馈**
- ✅ **性能优化和缓存机制**

该系统确保了用户能够安全、便捷地管理各种类型的文件，为知识库的完整性和实用性提供了重要支撑。

---

*文件系统功能完成 - 米醋电子工作室*