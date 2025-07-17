# Claude Code 监视系统使用指南

## 🎯 功能概述

Claude Code监视系统帮助您实时监控项目状态、文件变更和应用运行情况。

### ✨ 主要功能

1. **📁 文件监视** - 实时监控项目文件变更
2. **🌐 Web仪表板** - 可视化状态监控界面  
3. **📊 状态检查** - 应用健康状态检测
4. **📝 日志记录** - 详细的操作日志

## 🚀 快速开始

### 方法1: 一键启动 (推荐)
```bash
python start_claude_monitor.py
```

### 方法2: 分别启动
```bash
# 启动文件监视器
python claude_monitor.py

# 启动Web仪表板 (新终端)
python claude_dashboard.py
```

## 📋 使用说明

### 1. 文件监视器 (`claude_monitor.py`)

**功能**:
- 监控 `.py`, `.js`, `.html`, `.css`, `.md`, `.yaml`, `.json`, `.txt` 文件
- 检测文件新增、修改、删除
- 记录详细的变更日志
- 生成状态报告

**输出文件**:
- `claude_monitor.log` - 详细日志
- `claude_status.json` - 状态数据

### 2. Web仪表板 (`claude_dashboard.py`)

**访问地址**: http://localhost:8080

**功能**:
- 实时系统状态显示
- 文件变更历史
- 日志查看器
- 自动刷新 (3秒间隔)

**界面说明**:
- 🟢 绿色图标 = 正常状态
- 🔴 红色图标 = 异常状态
- 📊 实时数据更新
- 📱 响应式设计

### 3. 状态检查

**检查项目**:
- ✅ `wsgi.py` - WSGI入口文件
- ✅ `app.py` - 主应用文件
- ✅ `requirements.txt` - 依赖文件
- ✅ `render.yaml` - Render配置

## 🔧 配置选项

### 监视间隔调整
```python
# 在 claude_monitor.py 中修改
monitor.start_monitoring(interval=3)  # 3秒检查一次
```

### 监视文件类型
```python
# 在 claude_monitor.py 中修改
important_files = [
    "*.py", "*.js", "*.html", "*.css", "*.md", 
    "*.yaml", "*.yml", "*.json", "*.txt"
]
```

### 仪表板端口
```python
# 在 claude_dashboard.py 中修改
app.run(host='0.0.0.0', port=8080, debug=True)
```

## 📊 监视数据

### 日志格式
```
2025-07-14T17:30:45 [CHANGE] 检测到文件变更
  详情: {
    "modified": ["wsgi.py"],
    "added": [],
    "deleted": []
  }
```

### 状态数据
```json
{
  "timestamp": "2025-07-14T17:30:45",
  "files_monitored": 25,
  "wsgi_exists": true,
  "app_exists": true,
  "requirements_exists": true,
  "render_config_exists": true,
  "wsgi_imports_app": true
}
```

## 🛠️ 故障排除

### 常见问题

1. **监视器无法启动**
   ```bash
   # 检查Python版本
   python --version
   
   # 检查文件权限
   ls -la claude_monitor.py
   ```

2. **Web仪表板无法访问**
   ```bash
   # 检查端口占用
   netstat -an | grep 8080
   
   # 尝试其他端口
   python claude_dashboard.py  # 修改端口后运行
   ```

3. **文件变更未检测到**
   - 检查文件是否在监视范围内
   - 确认文件扩展名是否支持
   - 查看日志文件确认监视状态

### 调试模式

启用详细日志:
```python
# 在脚本中添加
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 高级用法

### 1. 集成到CI/CD
```yaml
# GitHub Actions 示例
- name: 启动监视器
  run: python claude_monitor.py &
  
- name: 运行测试
  run: pytest
  
- name: 检查状态
  run: python -c "import json; print(json.load(open('claude_status.json')))"
```

### 2. 自定义监视规则
```python
# 添加自定义检查
def custom_check(self):
    # 检查特定条件
    if condition:
        self.log_event("CUSTOM", "自定义检查通过")
```

### 3. 远程监控
```python
# 修改仪表板绑定地址
app.run(host='0.0.0.0', port=8080)  # 允许外部访问
```

## 🔒 安全注意事项

1. **本地使用** - 仅在开发环境使用
2. **端口安全** - 不要在生产环境暴露监控端口
3. **日志清理** - 定期清理日志文件避免占用过多空间
4. **权限控制** - 确保监控脚本有适当的文件访问权限

## 📞 支持

如有问题或建议，请检查:
1. 📋 日志文件 `claude_monitor.log`
2. 📊 状态文件 `claude_status.json`
3. 🌐 Web仪表板 http://localhost:8080

---

**版本**: 1.0.0  
**更新时间**: 2025-07-14  
**兼容性**: Python 3.7+
