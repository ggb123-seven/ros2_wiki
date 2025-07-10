# ROS2 Wiki Enhanced - Render.com 部署指南

## 🚀 快速部署到Render

### 1. 准备GitHub仓库
- ✅ 代码已推送到：https://github.com/ggb123-seven/ros2_wiki.git
- ✅ 所有必要文件已包含

### 2. Render.com 部署步骤

#### 第一步：创建Web Service
1. 访问 [Render.com](https://render.com)
2. 登录或注册账户
3. 点击 "New +" → "Web Service"

#### 第二步：连接GitHub仓库
1. 选择 "Connect a repository"
2. 连接GitHub账户（如果尚未连接）
3. 找到并选择 `ros2_wiki` 仓库
4. 点击 "Connect"

#### 第三步：配置部署设置
```
Name: ros2-wiki-enhanced
Environment: Python 3
Branch: main
Root Directory: (留空)

Build Command: echo "No build required"
Start Command: python3 enhanced_server.py

Instance Type: Free
```

#### 第四步：环境变量（可选）
```
PORT: (Render会自动设置)
```

#### 第五步：部署
1. 点击 "Create Web Service"
2. 等待部署完成（通常2-3分钟）
3. 部署成功后会获得公网URL

## 📋 部署配置详情

### Build 配置
- **Build Command**: `echo "No build required"`
  - 因为项目无需编译，只使用Python标准库
- **Publish Directory**: 不需要设置

### Runtime 配置  
- **Start Command**: `python3 enhanced_server.py`
  - 直接运行主服务器程序
- **Environment**: Python 3
  - Render会自动检测并使用Python 3.x

### 网络配置
- **端口**: 自动从环境变量 `PORT` 获取
- **HTTPS**: Render自动提供
- **CDN**: 全球分发网络

## 🔧 部署后验证

### 1. 访问测试
- 主页：`https://your-app.onrender.com`
- 管理后台：`https://your-app.onrender.com/admin`
- 系统检查：`https://your-app.onrender.com/api/health`

### 2. 功能验证
- ✅ 用户注册/登录
- ✅ 文档浏览
- ✅ 搜索功能
- ✅ 评论系统
- ✅ 管理后台

### 3. 默认账户
- 管理员：`admin` / `admin123`
- 用户：`ros2_user` / `user123`

## 🚨 注意事项

### 数据库
- SQLite数据库会在首次运行时自动创建
- Render免费版本不支持持久存储，重启会重置数据
- 生产环境建议升级到付费版本或使用外部数据库

### 性能
- 免费版本有使用限制：
  - 自动休眠（15分钟无活动）
  - 750小时/月运行时间
  - 带宽限制

### 日志监控
- Render控制台可查看实时日志
- 支持日志下载和搜索

## 🎯 部署成功标志

部署成功后，你应该看到：

1. **Render控制台显示**：
   ```
   🚀 ROS2 Wiki 增强版启动中...
   📱 本地访问: http://localhost:[PORT]
   ✅ 服务器启动成功，监听端口 [PORT]
   ```

2. **网站正常访问**：
   - 首页加载完整的Bootstrap界面
   - 登录功能正常工作
   - 管理后台可访问

3. **API响应正常**：
   ```bash
   curl https://your-app.onrender.com/api/health
   # 返回JSON格式的系统状态
   ```

## 🔄 更新部署

当你更新代码时：
1. 推送到GitHub：`git push origin main`
2. Render会自动检测并重新部署
3. 无需手动操作

## 🆘 故障排除

### 常见问题
1. **启动失败**：检查日志中的错误信息
2. **数据库错误**：确认SQLite文件权限
3. **端口问题**：确认使用环境变量 `PORT`

### 联系支持
- Render支持文档：https://render.com/docs
- GitHub Issues：提交问题报告

---

✅ **准备就绪！** 您的ROS2 Wiki Enhanced已准备好部署到Render平台！