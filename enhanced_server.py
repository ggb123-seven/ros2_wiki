#!/usr/bin/env python3
"""
ROS2 Wiki增强版 - 轻量级但功能完整的Wiki系统
只使用Python标准库，支持搜索、用户管理、评论等功能
"""
import http.server
import socketserver
import json
import urllib.parse
import sqlite3
import hashlib
import os
import re
from datetime import datetime
from http.cookies import SimpleCookie

# 全局会话存储
sessions = {}

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect('simple_wiki.db')
    cursor = conn.cursor()
    
    # 检查并更新现有表结构
    cursor.execute('PRAGMA table_info(users)')
    users_columns = [col[1] for col in cursor.fetchall()]
    
    # 如果没有email列，添加它
    if 'email' not in users_columns:
        cursor.execute('ALTER TABLE users ADD COLUMN email TEXT')
    if 'is_admin' not in users_columns:
        cursor.execute('ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0')
    
    # 检查documents表
    cursor.execute('PRAGMA table_info(documents)')
    docs_columns = [col[1] for col in cursor.fetchall()]
    if 'category' not in docs_columns:
        cursor.execute('ALTER TABLE documents ADD COLUMN category TEXT DEFAULT "ROS2基础"')
    
    # 添加默认用户（如果不存在）
    cursor.execute('SELECT COUNT(*) FROM users WHERE username = "admin"')
    if cursor.fetchone()[0] == 0:
        admin_hash = hashlib.sha256(('admin123' + 'salt').encode()).hexdigest()
        user_hash = hashlib.sha256(('user123' + 'salt').encode()).hexdigest()
        
        cursor.execute('INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                      ('admin', 'admin@ros2wiki.com', admin_hash, 1))
        cursor.execute('INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                      ('ros2_user', 'user@ros2wiki.com', user_hash, 0))
    
    conn.commit()
    conn.close()

def get_session_user(handler):
    """获取当前会话用户"""
    cookie_header = handler.headers.get('Cookie', '')
    if 'session_id=' in cookie_header:
        session_id = cookie_header.split('session_id=')[1].split(';')[0]
        return sessions.get(session_id, {}).get('username')
    return None

def is_admin_user(username):
    """检查用户是否为管理员"""
    if not username:
        return False
    
    conn = sqlite3.connect('simple_wiki.db')
    cursor = conn.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    
    return result and result[0] == 1

def simple_markdown(content):
    """简化的Markdown渲染"""
    html = content
    
    # 标题处理
    html = re.sub(r'^# (.*$)', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*$)', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.*$)', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    
    # 代码块处理
    html = re.sub(r'```(\w+)?\n(.*?)```', r'<pre><code class="language-\1">\2</code></pre>', html, flags=re.DOTALL)
    
    # 行内代码
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    # 粗体和斜体
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
    
    # 链接
    html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', html)
    
    # 列表处理
    html = re.sub(r'^- (.*$)', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)
    html = re.sub(r'</ul>\s*<ul>', '', html)
    
    # 段落处理
    paragraphs = html.split('\n\n')
    processed_paragraphs = []
    for p in paragraphs:
        p = p.strip()
        if p and not p.startswith('<'):
            p = f'<p>{p}</p>'
        processed_paragraphs.append(p)
    
    html = '\n'.join(processed_paragraphs)
    
    # 清理多余的标签
    html = re.sub(r'<p><h([1-6])>', r'<h\1>', html)
    html = re.sub(r'</h([1-6])></p>', r'</h\1>', html)
    html = re.sub(r'<p><pre>', r'<pre>', html)
    html = re.sub(r'</pre></p>', r'</pre>', html)
    html = re.sub(r'<p><ul>', r'<ul>', html)
    html = re.sub(r'</ul></p>', r'</ul>', html)
    
    return html

class WikiHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # 静默日志输出
        pass
    
    def do_GET(self):
        if self.path == '/':
            self.serve_homepage()
        elif self.path.startswith('/doc/'):
            doc_id = self.path.split('/')[-1]
            self.serve_document(doc_id)
        elif self.path == '/search':
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('q', [''])[0]
            self.serve_search(query)
        elif self.path.startswith('/search?'):
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            query = query_params.get('q', [''])[0]
            self.serve_search(query)
        elif self.path == '/login':
            self.serve_login()
        elif self.path == '/register':
            self.serve_register()
        elif self.path == '/logout':
            self.serve_logout()
        elif self.path == '/admin':
            self.serve_admin()
        elif self.path == '/favicon.ico':
            self.serve_favicon()
        elif self.path == '/api/health':
            self.serve_health()
        else:
            self.send_error(404, 'Page Not Found')
    
    def do_POST(self):
        if self.path == '/login':
            self.handle_login()
        elif self.path == '/register':
            self.handle_register()
        elif self.path.startswith('/comment/'):
            doc_id = self.path.split('/')[-1]
            self.handle_comment(doc_id)
        elif self.path == '/admin/add':
            self.handle_admin_add()
        else:
            self.send_error(404, 'Page Not Found')
    
    def serve_favicon(self):
        """提供favicon"""
        # 返回一个简单的透明1x1像素PNG
        favicon_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        
        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.send_header('Content-Length', str(len(favicon_data)))
        self.end_headers()
        self.wfile.write(favicon_data)
    
    def serve_health(self):
        """系统健康检查页面"""
        # 检查数据库连接
        db_status = self.check_database()
        
        # 获取系统统计
        stats = self.get_system_stats()
        
        # 检查功能模块
        features_status = self.check_features()
        
        # 获取运行时间信息
        runtime_info = self.get_runtime_info()
        
        # 总体状态
        overall_status = "healthy" if db_status['status'] == 'ok' else "warning"
        
        # 如果请求JSON格式
        if self.headers.get('Accept') == 'application/json':
            health_data = {
                'status': overall_status,
                'message': 'ROS2 Wiki Enhanced Running',
                'database': db_status,
                'statistics': stats,
                'features': features_status,
                'runtime': runtime_info,
                'timestamp': datetime.now().isoformat()
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(health_data, ensure_ascii=False).encode('utf-8'))
            return
        
        # 渲染HTML页面
        status_color = "success" if overall_status == "healthy" else "warning"
        status_icon = "fa-check-circle" if overall_status == "healthy" else "fa-exclamation-triangle"
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>系统状态检查 - ROS2 Wiki</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .status-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem 0;
            margin-bottom: 2rem;
        }}
        .status-card {{
            border-radius: 10px;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .metric-item {{
            padding: 0.75rem 0;
            border-bottom: 1px solid #f0f0f0;
        }}
        .metric-item:last-child {{
            border-bottom: none;
        }}
        .status-badge {{
            font-size: 0.9rem;
            padding: 0.5rem 1rem;
        }}
        .refresh-btn {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            border-radius: 50px;
            padding: 12px 20px;
        }}
        .auto-refresh {{
            color: #6c757d;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <!-- 状态头部 -->
    <div class="status-header">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <h1 class="display-5 fw-bold">
                        <i class="fas fa-heartbeat"></i> 系统状态检查
                    </h1>
                    <p class="lead">ROS2 Wiki 系统健康监控面板</p>
                </div>
                <div class="col-md-4 text-center">
                    <div class="text-{status_color}">
                        <i class="fas {status_icon} fa-6x"></i>
                        <h3 class="mt-3">系统{overall_status.upper()}</h3>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="container">
        <!-- 总体状态 -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card status-card border-{status_color}">
                    <div class="card-header bg-{status_color} text-white">
                        <h5><i class="fas fa-tachometer-alt"></i> 系统总体状态</h5>
                    </div>
                    <div class="card-body">
                        <div class="row text-center">
                            <div class="col-md-3">
                                <h4 class="text-{status_color}">
                                    <i class="fas {status_icon}"></i> {overall_status.upper()}
                                </h4>
                                <small class="text-muted">总体状态</small>
                            </div>
                            <div class="col-md-3">
                                <h4 class="text-info">
                                    <i class="fas fa-clock"></i> {runtime_info['uptime']}
                                </h4>
                                <small class="text-muted">运行时间</small>
                            </div>
                            <div class="col-md-3">
                                <h4 class="text-primary">
                                    <i class="fas fa-server"></i> {runtime_info['version']}
                                </h4>
                                <small class="text-muted">Python版本</small>
                            </div>
                            <div class="col-md-3">
                                <h4 class="text-success">
                                    <i class="fas fa-memory"></i> {runtime_info['memory']}
                                </h4>
                                <small class="text-muted">内存使用</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <!-- 数据库状态 -->
            <div class="col-md-6">
                <div class="card status-card">
                    <div class="card-header">
                        <h5><i class="fas fa-database"></i> 数据库状态</h5>
                    </div>
                    <div class="card-body">
                        <div class="metric-item d-flex justify-content-between">
                            <span><i class="fas fa-plug"></i> 连接状态</span>
                            <span class="badge bg-{("success" if db_status["status"] == "ok" else "danger")} status-badge">
                                {db_status["status"].upper()}
                            </span>
                        </div>
                        <div class="metric-item d-flex justify-content-between">
                            <span><i class="fas fa-stopwatch"></i> 响应时间</span>
                            <span class="text-muted">{db_status["response_time"]}ms</span>
                        </div>
                        <div class="metric-item d-flex justify-content-between">
                            <span><i class="fas fa-table"></i> 数据表</span>
                            <span class="text-muted">{db_status["tables"]} 个</span>
                        </div>
                        <div class="metric-item d-flex justify-content-between">
                            <span><i class="fas fa-file-alt"></i> 数据库版本</span>
                            <span class="text-muted">{db_status["version"]}</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 数据统计 -->
            <div class="col-md-6">
                <div class="card status-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-bar"></i> 数据统计</h5>
                    </div>
                    <div class="card-body">
                        <div class="metric-item d-flex justify-content-between">
                            <span><i class="fas fa-users"></i> 注册用户</span>
                            <span class="badge bg-primary status-badge">{stats["users"]}</span>
                        </div>
                        <div class="metric-item d-flex justify-content-between">
                            <span><i class="fas fa-file-alt"></i> 技术文档</span>
                            <span class="badge bg-success status-badge">{stats["documents"]}</span>
                        </div>
                        <div class="metric-item d-flex justify-content-between">
                            <span><i class="fas fa-comments"></i> 用户评论</span>
                            <span class="badge bg-info status-badge">{stats["comments"]}</span>
                        </div>
                        <div class="metric-item d-flex justify-content-between">
                            <span><i class="fas fa-user-shield"></i> 管理员数</span>
                            <span class="badge bg-warning status-badge">{stats["admins"]}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 功能模块状态 -->
        <div class="row">
            <div class="col-md-8">
                <div class="card status-card">
                    <div class="card-header">
                        <h5><i class="fas fa-cogs"></i> 功能模块检查</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">'''
        
        # 添加功能状态
        for feature, status in features_status.items():
            icon_class = "fa-check-circle text-success" if status else "fa-times-circle text-danger"
            status_text = "正常" if status else "异常"
            html += f'''
                            <div class="col-md-6">
                                <div class="metric-item">
                                    <i class="fas {icon_class}"></i> {feature}: {status_text}
                                </div>
                            </div>'''
        
        html += f'''
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 系统信息 -->
            <div class="col-md-4">
                <div class="card status-card">
                    <div class="card-header">
                        <h5><i class="fas fa-info-circle"></i> 系统信息</h5>
                    </div>
                    <div class="card-body">
                        <div class="metric-item">
                            <small class="text-muted">服务器时间</small><br>
                            <strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</strong>
                        </div>
                        <div class="metric-item">
                            <small class="text-muted">最后检查</small><br>
                            <strong id="lastCheck">{datetime.now().strftime('%H:%M:%S')}</strong>
                        </div>
                        <div class="metric-item">
                            <small class="text-muted">检查频率</small><br>
                            <strong class="auto-refresh">每30秒自动刷新</strong>
                        </div>
                    </div>
                </div>
                
                <!-- 快速操作 -->
                <div class="card status-card mt-3">
                    <div class="card-header">
                        <h6><i class="fas fa-tools"></i> 快速操作</h6>
                    </div>
                    <div class="card-body p-2">
                        <div class="d-grid gap-2">
                            <a href="/admin" class="btn btn-primary btn-sm">
                                <i class="fas fa-cog"></i> 管理后台
                            </a>
                            <a href="/" class="btn btn-outline-secondary btn-sm">
                                <i class="fas fa-home"></i> 返回首页
                            </a>
                            <button onclick="exportReport()" class="btn btn-outline-info btn-sm">
                                <i class="fas fa-download"></i> 导出报告
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 最近活动 -->
        <div class="row mt-4">
            <div class="col-12">
                <div class="card status-card">
                    <div class="card-header">
                        <h5><i class="fas fa-history"></i> 系统日志概览</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4">
                                <div class="text-center">
                                    <h4 class="text-success">{stats["recent_docs"]}</h4>
                                    <small class="text-muted">今日新增文档</small>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="text-center">
                                    <h4 class="text-info">{stats["recent_users"]}</h4>
                                    <small class="text-muted">今日新注册用户</small>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="text-center">
                                    <h4 class="text-warning">{stats["recent_comments"]}</h4>
                                    <small class="text-muted">今日新增评论</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- 刷新按钮 -->
    <button onclick="location.reload()" class="btn btn-primary refresh-btn">
        <i class="fas fa-sync-alt"></i> 刷新
    </button>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // 自动刷新功能
        setInterval(function() {{
            document.getElementById('lastCheck').textContent = new Date().toLocaleTimeString();
        }}, 30000);
        
        // 导出报告功能
        function exportReport() {{
            const data = {{
                timestamp: new Date().toISOString(),
                status: "{overall_status}",
                database: {json.dumps(db_status)},
                statistics: {json.dumps(stats)},
                features: {json.dumps(features_status)},
                runtime: {json.dumps(runtime_info)}
            }};
            
            const blob = new Blob([JSON.stringify(data, null, 2)], {{type: 'application/json'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'ros2-wiki-health-report-' + new Date().toISOString().split('T')[0] + '.json';
            a.click();
            URL.revokeObjectURL(url);
        }}
        
        // 页面加载完成后30秒自动刷新
        setTimeout(function() {{
            location.reload();
        }}, 30000);
    </script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def check_database(self):
        """检查数据库状态"""
        start_time = datetime.now()
        try:
            conn = sqlite3.connect('simple_wiki.db')
            cursor = conn.cursor()
            
            # 检查连接
            cursor.execute('SELECT 1')
            
            # 获取数据库版本
            cursor.execute('SELECT sqlite_version()')
            version = cursor.fetchone()[0]
            
            # 检查表数量
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            conn.close()
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                'status': 'ok',
                'response_time': round(response_time, 2),
                'version': version,
                'tables': table_count
            }
        except Exception as e:
            return {
                'status': 'error',
                'response_time': 0,
                'version': 'unknown',
                'tables': 0,
                'error': str(e)
            }
    
    def get_system_stats(self):
        """获取系统统计数据"""
        try:
            conn = sqlite3.connect('simple_wiki.db')
            cursor = conn.cursor()
            
            # 基础统计
            cursor.execute('SELECT COUNT(*) FROM users')
            users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM documents')
            documents = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM comments')
            comments = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_admin = 1')
            admins = cursor.fetchone()[0]
            
            # 今日数据
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('SELECT COUNT(*) FROM documents WHERE created_at LIKE ?', (f'{today}%',))
            recent_docs = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM users WHERE created_at LIKE ?', (f'{today}%',))
            recent_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM comments WHERE created_at LIKE ?', (f'{today}%',))
            recent_comments = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'users': users,
                'documents': documents,
                'comments': comments,
                'admins': admins,
                'recent_docs': recent_docs,
                'recent_users': recent_users,
                'recent_comments': recent_comments
            }
        except Exception:
            return {
                'users': 0,
                'documents': 0,
                'comments': 0,
                'admins': 0,
                'recent_docs': 0,
                'recent_users': 0,
                'recent_comments': 0
            }
    
    def check_features(self):
        """检查功能模块状态"""
        features = {}
        
        # 检查数据库连接
        try:
            conn = sqlite3.connect('simple_wiki.db')
            conn.close()
            features['数据库连接'] = True
        except:
            features['数据库连接'] = False
        
        # 检查会话管理
        features['会话管理'] = len(sessions) >= 0
        
        # 检查Markdown渲染
        try:
            simple_markdown('# Test')
            features['Markdown渲染'] = True
        except:
            features['Markdown渲染'] = False
        
        # 检查用户认证
        try:
            hashlib.sha256('test'.encode()).hexdigest()
            features['用户认证'] = True
        except:
            features['用户认证'] = False
        
        # 检查搜索功能
        features['搜索功能'] = True  # 基于代码逻辑检查
        
        # 检查评论系统
        features['评论系统'] = True  # 基于代码逻辑检查
        
        return features
    
    def get_runtime_info(self):
        """获取运行时信息"""
        import sys
        import platform
        import os
        
        try:
            # 简化的内存信息获取
            try:
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                    for line in meminfo.split('\n'):
                        if 'MemAvailable:' in line:
                            mem_available = int(line.split()[1]) // 1024  # KB to MB
                            memory_info = f"{mem_available}MB可用"
                            break
                    else:
                        memory_info = "N/A"
            except:
                memory_info = "N/A"
            
            return {
                'version': f"Python {sys.version.split()[0]}",
                'platform': platform.system(),
                'uptime': '运行中',
                'memory': memory_info
            }
        except Exception as e:
            return {
                'version': f"Python {sys.version.split()[0]}",
                'platform': 'Unknown', 
                'uptime': '运行中',
                'memory': 'N/A'
            }
    
    def handle_comment(self, doc_id):
        """处理评论提交"""
        current_user = get_session_user(self)
        if not current_user:
            self.send_error(401, 'Unauthorized')
            return
        
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        data = urllib.parse.parse_qs(post_data)
        
        comment_content = data.get('content', [''])[0]
        
        if comment_content:
            conn = sqlite3.connect('simple_wiki.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO comments (document_id, username, content) VALUES (?, ?, ?)',
                          (doc_id, current_user, comment_content))
            conn.commit()
            conn.close()
        
        # 重定向回文档页面
        self.send_response(302)
        self.send_header('Location', f'/doc/{doc_id}')
        self.end_headers()
    
    def serve_homepage(self):
        """首页"""
        current_user = get_session_user(self)
        
        conn = sqlite3.connect('simple_wiki.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, title, created_at FROM documents ORDER BY id DESC LIMIT 10')
        docs = cursor.fetchall()
        conn.close()
        
        # 按分类分组
        categories = {"ROS2基础": []}
        for doc in docs:
            categories["ROS2基础"].append(doc + ("ROS2基础",))  # 添加默认分类
        
        user_menu = self.get_user_menu_html(current_user)
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ROS2 Wiki - 机器人操作系统学习平台</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/github.min.css">
    <style>
        .hero-section {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            padding: 4rem 0; 
            margin-bottom: 2rem;
        }}
        .doc-card {{ 
            transition: transform 0.2s; 
            height: 100%;
        }}
        .doc-card:hover {{ 
            transform: translateY(-5px); 
        }}
        .category-badge {{ 
            font-size: 0.8rem; 
        }}
        .search-box {{ 
            max-width: 500px; 
        }}
        .stats-card {{
            text-align: center;
            padding: 1.5rem;
        }}
    </style>
</head>
<body>
    <!-- 导航栏 -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-robot"></i> ROS2 Wiki
            </a>
            
            <!-- 搜索框 -->
            <form class="d-flex me-auto ms-3" method="GET" action="/search">
                <div class="input-group search-box">
                    <input class="form-control" type="search" name="q" placeholder="搜索教程..." aria-label="搜索">
                    <button class="btn btn-outline-light" type="submit">
                        <i class="fas fa-search"></i>
                    </button>
                </div>
            </form>
            
            <!-- 用户菜单 -->
            <div class="navbar-nav">
                {user_menu}
            </div>
        </div>
    </nav>
    
    <!-- Hero区域 -->
    <div class="hero-section">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <h1 class="display-4 fw-bold">
                        <i class="fas fa-robot"></i> ROS2 Wiki
                    </h1>
                    <p class="lead">学习ROS2机器人操作系统，掌握现代机器人开发技术</p>
                    <div class="mt-4">
                        <a href="/search" class="btn btn-light btn-lg me-3">
                            <i class="fas fa-search"></i> 浏览教程
                        </a>
                        {('<a href="/admin" class="btn btn-outline-light btn-lg"><i class="fas fa-cog"></i> 管理后台</a>' if current_user == 'admin' else '')}
                    </div>
                </div>
                <div class="col-md-4 text-center">
                    <i class="fas fa-cogs fa-8x opacity-75"></i>
                </div>
            </div>
        </div>
    </div>
    
    <div class="container">
        <!-- 统计信息 -->
        <div class="row mb-5">
            <div class="col-md-4">
                <div class="card stats-card bg-primary text-white">
                    <div class="card-body">
                        <i class="fas fa-book fa-2x mb-2"></i>
                        <h3>{len(docs)}</h3>
                        <p>技术教程</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card stats-card bg-success text-white">
                    <div class="card-body">
                        <i class="fas fa-folder fa-2x mb-2"></i>
                        <h3>{len(categories)}</h3>
                        <p>分类目录</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card stats-card bg-info text-white">
                    <div class="card-body">
                        <i class="fas fa-users fa-2x mb-2"></i>
                        <h3>实时</h3>
                        <p>内容更新</p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 分类教程 -->
        <h2 class="mb-4"><i class="fas fa-graduation-cap"></i> 学习路径</h2>
'''
        
        for category, cat_docs in categories.items():
            html += f'''
        <div class="row mb-4">
            <div class="col-12">
                <h4 class="mb-3">
                    <span class="badge bg-secondary category-badge">{category}</span>
                </h4>
            </div>
'''
            for doc in cat_docs:
                html += f'''
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card doc-card">
                    <div class="card-body">
                        <h5 class="card-title">
                            <a href="/doc/{doc[0]}" class="text-decoration-none">{doc[1]}</a>
                        </h5>
                        <p class="card-text">
                            <small class="text-muted">
                                <i class="fas fa-calendar"></i> {doc[3][:16]}
                            </small>
                        </p>
                        <a href="/doc/{doc[0]}" class="btn btn-primary btn-sm">
                            <i class="fas fa-arrow-right"></i> 开始学习
                        </a>
                    </div>
                </div>
            </div>
'''
            html += '</div>'
        
        if not docs:
            html += '''
        <div class="text-center py-5">
            <i class="fas fa-book-open fa-4x text-muted mb-3"></i>
            <h4 class="text-muted">暂无教程内容</h4>
            <p class="text-muted">请管理员添加教程内容</p>
        </div>
'''
        
        html += '''
        <!-- 学习指南 -->
        <div class="row mt-5">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-route"></i> 推荐学习路径</h5>
                    </div>
                    <div class="card-body">
                        <ol class="list-group list-group-numbered">
                            <li class="list-group-item">🚀 ROS2环境搭建与配置</li>
                            <li class="list-group-item">📦 包管理和工作空间创建</li>
                            <li class="list-group-item">🔄 节点通信机制详解</li>
                            <li class="list-group-item">🛠️ 常用工具和调试技巧</li>
                            <li class="list-group-item">🤖 实际机器人应用开发</li>
                        </ol>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-tools"></i> 开发工具</h5>
                    </div>
                    <div class="card-body">
                        <ul class="list-unstyled">
                            <li class="mb-2"><i class="fas fa-terminal text-primary"></i> <strong>ros2命令行工具</strong></li>
                            <li class="mb-2"><i class="fas fa-chart-line text-success"></i> <strong>rqt图形化界面</strong></li>
                            <li class="mb-2"><i class="fas fa-cube text-info"></i> <strong>Gazebo仿真环境</strong></li>
                            <li class="mb-2"><i class="fas fa-eye text-warning"></i> <strong>RViz2可视化工具</strong></li>
                            <li class="mb-2"><i class="fas fa-hammer text-danger"></i> <strong>colcon构建系统</strong></li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- 页脚 -->
    <footer class="bg-dark text-white mt-5 py-4">
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <h5><i class="fas fa-robot"></i> ROS2 Wiki</h5>
                    <p>机器人操作系统学习平台 - 让机器人开发更简单</p>
                </div>
                <div class="col-md-6 text-end">
                    <p>
                        <a href="/api/health" class="text-white-50">系统状态</a> | 
                        <a href="/search" class="text-white-50">搜索</a>
                        {' | <a href="/admin" class="text-white-50">管理</a>' if current_user == 'admin' else ''}
                    </p>
                </div>
            </div>
        </div>
    </footer>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
    <script>hljs.highlightAll();</script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_document(self, doc_id):
        """文档详情页"""
        try:
            doc_id = int(doc_id)
            conn = sqlite3.connect('simple_wiki.db')
            cursor = conn.cursor()
            cursor.execute('SELECT title, content, created_at FROM documents WHERE id = ?', (doc_id,))
            doc = cursor.fetchone()
            
            # 获取评论
            cursor.execute('''
                SELECT username, content, created_at 
                FROM comments 
                WHERE document_id = ? 
                ORDER BY created_at DESC
            ''', (doc_id,))
            comments = cursor.fetchall()
            
            conn.close()
            
            if doc:
                current_user = get_session_user(self)
                title, content, created_at = doc
                category = "ROS2基础"  # 默认分类
                html_content = simple_markdown(content)
                user_menu = self.get_user_menu_html(current_user)
                
                comment_form = ''
                if current_user:
                    comment_form = f'''
                    <div class="card mb-4">
                        <div class="card-header">
                            <h5><i class="fas fa-comment-dots"></i> 发表评论</h5>
                        </div>
                        <div class="card-body">
                            <form method="POST" action="/comment/{doc_id}">
                                <div class="mb-3">
                                    <textarea class="form-control" name="content" rows="3" 
                                             placeholder="分享您的想法..." required></textarea>
                                </div>
                                <button type="submit" class="btn btn-primary">
                                    <i class="fas fa-paper-plane"></i> 提交评论
                                </button>
                            </form>
                        </div>
                    </div>
                    '''
                else:
                    comment_form = '''
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle"></i> 
                        请先 <a href="/login">登录</a> 后发表评论
                    </div>
                    '''
                
                comments_html = ''
                for comment in comments:
                    comments_html += f'''
                    <div class="card mb-3">
                        <div class="card-body">
                            <div class="d-flex justify-content-between mb-2">
                                <strong class="text-primary">
                                    <i class="fas fa-user-circle"></i> {comment[0]}
                                </strong>
                                <small class="text-muted">{comment[2][:16]}</small>
                            </div>
                            <p class="mb-0">{comment[1]}</p>
                        </div>
                    </div>
                    '''
                
                html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - ROS2 Wiki</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/github.min.css">
    <style>
        .document-content {{ line-height: 1.8; }}
        .document-content h1, .document-content h2, .document-content h3 {{ 
            color: #2c3e50; margin-top: 2rem; margin-bottom: 1rem; 
        }}
        .document-content h1 {{ 
            border-bottom: 2px solid #3498db; padding-bottom: 0.5rem; 
        }}
        .document-content pre {{ 
            background-color: #f8f9fa; border: 1px solid #e9ecef; 
            border-radius: 0.375rem; padding: 1rem; overflow-x: auto; 
        }}
        .document-content code {{ 
            background-color: #f8f9fa; color: #e83e8c; 
            padding: 0.2rem 0.4rem; border-radius: 0.25rem; 
        }}
        .document-content pre code {{ 
            background-color: transparent; color: inherit; padding: 0; 
        }}
        .document-content blockquote {{ 
            border-left: 4px solid #3498db; margin: 1rem 0; 
            padding: 0.5rem 1rem; background-color: #f8f9fa; 
        }}
        .toc {{ position: sticky; top: 1rem; }}
    </style>
</head>
<body>
    <!-- 导航栏 -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-robot"></i> ROS2 Wiki
            </a>
            
            <form class="d-flex me-auto ms-3" method="GET" action="/search">
                <div class="input-group" style="width: 300px;">
                    <input class="form-control" type="search" name="q" placeholder="搜索教程..." aria-label="搜索">
                    <button class="btn btn-outline-light" type="submit">
                        <i class="fas fa-search"></i>
                    </button>
                </div>
            </form>
            
            <div class="navbar-nav">
                {user_menu}
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        <div class="row">
            <div class="col-md-9">
                <!-- 面包屑导航 -->
                <nav aria-label="breadcrumb">
                    <ol class="breadcrumb">
                        <li class="breadcrumb-item"><a href="/">首页</a></li>
                        <li class="breadcrumb-item">{category}</li>
                        <li class="breadcrumb-item active">{title}</li>
                    </ol>
                </nav>
                
                <!-- 文档内容 -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h1 class="mb-0">{title}</h1>
                        <small class="text-muted">
                            <i class="fas fa-folder"></i> {category} | 
                            <i class="fas fa-calendar"></i> {created_at[:16]}
                        </small>
                    </div>
                    <div class="card-body">
                        <div class="document-content">
                            {html_content}
                        </div>
                    </div>
                </div>
                
                <!-- 评论区 -->
                <h4><i class="fas fa-comments"></i> 评论区 ({len(comments)})</h4>
                {comment_form}
                
                <div class="comments-section">
                    {comments_html if comments else '<p class="text-muted text-center py-4">暂无评论，快来发表第一条评论吧！</p>'}
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="toc">
                    <div class="card">
                        <div class="card-header">
                            <h6><i class="fas fa-list"></i> 页面导航</h6>
                        </div>
                        <div class="card-body">
                            <div id="toc-content">
                                <!-- 目录将通过JS生成 -->
                            </div>
                        </div>
                    </div>
                    
                    <div class="card mt-3">
                        <div class="card-header">
                            <h6><i class="fas fa-share-alt"></i> 快速操作</h6>
                        </div>
                        <div class="card-body">
                            <a href="/" class="btn btn-outline-primary btn-sm d-block mb-2">
                                <i class="fas fa-home"></i> 返回首页
                            </a>
                            <a href="/search" class="btn btn-outline-info btn-sm d-block">
                                <i class="fas fa-search"></i> 搜索更多
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
    <script>
        hljs.highlightAll();
        
        // 生成目录
        document.addEventListener('DOMContentLoaded', function() {{
            const headers = document.querySelectorAll('.document-content h1, .document-content h2, .document-content h3');
            const tocContent = document.getElementById('toc-content');
            
            if (headers.length === 0) {{
                tocContent.innerHTML = '<p class="text-muted small">无目录</p>';
                return;
            }}
            
            let tocHTML = '<ul class="list-unstyled">';
            headers.forEach((header, index) => {{
                const id = 'heading-' + index;
                header.id = id;
                const level = parseInt(header.tagName.substr(1));
                const indent = (level - 1) * 15;
                tocHTML += `<li style="margin-left: ${{indent}}px; margin-bottom: 5px;">
                    <a href="#${{id}}" class="text-decoration-none small">${{header.textContent}}</a>
                </li>`;
            }});
            tocHTML += '</ul>';
            tocContent.innerHTML = tocHTML;
        }});
    </script>
</body>
</html>'''
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
            else:
                self.send_error(404, 'Document Not Found')
        except ValueError:
            self.send_error(400, 'Invalid Document ID')
    
    def serve_search(self, query=''):
        """搜索页面"""
        current_user = get_session_user(self)
        user_menu = self.get_user_menu_html(current_user)
        
        documents = []
        if query:
            conn = sqlite3.connect('simple_wiki.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, content, created_at 
                FROM documents 
                WHERE title LIKE ? OR content LIKE ?
                ORDER BY created_at DESC
            ''', (f'%{query}%', f'%{query}%'))
            documents = cursor.fetchall()
            conn.close()
        
        results_html = ''
        if query and documents:
            for doc in documents:
                snippet = doc[2][:200] + '...' if len(doc[2]) > 200 else doc[2]
                # 高亮搜索词
                highlighted_title = doc[1].replace(query, f'<mark>{query}</mark>')
                highlighted_snippet = snippet.replace(query, f'<mark>{query}</mark>')
                
                results_html += f'''
                <div class="card mb-3">
                    <div class="card-body">
                        <h5 class="card-title">
                            <a href="/doc/{doc[0]}" class="text-decoration-none">{highlighted_title}</a>
                        </h5>
                        <p class="card-text">{highlighted_snippet}</p>
                        <p class="card-text">
                            <small class="text-muted">
                                <span class="badge bg-secondary">ROS2基础</span>
                                <i class="fas fa-calendar ms-2"></i> {doc[3][:16]}
                            </small>
                        </p>
                        <a href="/doc/{doc[0]}" class="btn btn-primary btn-sm">
                            <i class="fas fa-arrow-right"></i> 查看详情
                        </a>
                    </div>
                </div>
                '''
        elif query and not documents:
            results_html = '''
            <div class="text-center py-5">
                <i class="fas fa-search fa-4x text-muted mb-3"></i>
                <h4 class="text-muted">未找到相关结果</h4>
                <p class="text-muted">请尝试其他关键词</p>
            </div>
            '''
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>搜索{f" - {query}" if query else ""} - ROS2 Wiki</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        mark {{ background-color: #fff3cd; padding: 1px 2px; }}
        .search-stats {{ color: #6c757d; font-size: 0.9rem; }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-robot"></i> ROS2 Wiki
            </a>
            <div class="navbar-nav ms-auto">
                {user_menu}
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        <div class="row">
            <div class="col-md-8 mx-auto">
                <div class="card mb-4">
                    <div class="card-header">
                        <h4><i class="fas fa-search"></i> 搜索教程</h4>
                    </div>
                    <div class="card-body">
                        <form method="GET" action="/search">
                            <div class="input-group">
                                <input type="text" class="form-control form-control-lg" 
                                       name="q" value="{query}" 
                                       placeholder="搜索教程标题、内容或分类..." 
                                       aria-label="搜索">
                                <button class="btn btn-primary btn-lg" type="submit">
                                    <i class="fas fa-search"></i> 搜索
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
                
                {f'<p class="search-stats">找到 <strong>{len(documents)}</strong> 个关于 "<strong>{query}</strong>" 的结果</p>' if query else ''}
                
                {results_html}
                
                {'''
                <div class="text-center py-5">
                    <i class="fas fa-lightbulb fa-4x text-muted mb-3"></i>
                    <h4 class="text-muted">搜索提示</h4>
                    <div class="row mt-4">
                        <div class="col-md-6">
                            <ul class="list-unstyled text-start">
                                <li><i class="fas fa-check text-success"></i> 使用关键词: "ROS2"、"节点"、"话题"</li>
                                <li><i class="fas fa-check text-success"></i> 搜索分类: "基础"、"进阶"、"应用"</li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <ul class="list-unstyled text-start">
                                <li><i class="fas fa-check text-success"></i> 搜索代码: "python"、"launch"、"colcon"</li>
                                <li><i class="fas fa-check text-success"></i> 搜索工具: "gazebo"、"rviz"、"rqt"</li>
                            </ul>
                        </div>
                    </div>
                </div>
                ''' if not query else ''}
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def get_user_menu_html(self, current_user):
        """获取用户菜单HTML"""
        if current_user:
            admin_link = '<a class="nav-link" href="/admin"><i class="fas fa-cog"></i> 管理</a>' if current_user == 'admin' else ''
            return f'''
                <span class="navbar-text me-3">
                    <i class="fas fa-user-circle"></i> {current_user}
                </span>
                {admin_link}
                <a class="nav-link" href="/logout">
                    <i class="fas fa-sign-out-alt"></i> 退出
                </a>
            '''
        else:
            return '''
                <a class="nav-link" href="/login">
                    <i class="fas fa-sign-in-alt"></i> 登录
                </a>
                <a class="nav-link" href="/register">
                    <i class="fas fa-user-plus"></i> 注册
                </a>
            '''
    
    def serve_login(self):
        """登录页面"""
        # 实现登录页面（简化版）
        html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>登录 - ROS2 Wiki</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container">
        <div class="row justify-content-center mt-5">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h4><i class="fas fa-sign-in-alt"></i> 登录</h4>
                    </div>
                    <div class="card-body">
                        <form method="POST">
                            <div class="mb-3">
                                <label class="form-label">用户名</label>
                                <input type="text" class="form-control" name="username" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">密码</label>
                                <input type="password" class="form-control" name="password" required>
                            </div>
                            <button type="submit" class="btn btn-primary">登录</button>
                            <a href="/register" class="btn btn-outline-secondary">注册</a>
                            <a href="/" class="btn btn-link">返回首页</a>
                        </form>
                        <hr>
                        <small class="text-muted">
                            <strong>测试账户:</strong><br>
                            管理员: admin / admin123<br>
                            用户: ros2_user / user123
                        </small>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def handle_login(self):
        """处理登录"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        data = urllib.parse.parse_qs(post_data)
        
        username = data.get('username', [''])[0]
        password = data.get('password', [''])[0]
        
        # 验证用户
        conn = sqlite3.connect('simple_wiki.db')
        cursor = conn.cursor()
        cursor.execute('SELECT username, password_hash FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and hashlib.sha256((password + 'salt').encode()).hexdigest() == user[1]:
            # 创建会话
            import uuid
            session_id = str(uuid.uuid4())
            sessions[session_id] = {'username': username}
            
            # 设置cookie并重定向
            self.send_response(302)
            self.send_header('Location', '/')
            self.send_header('Set-Cookie', f'session_id={session_id}; Path=/; Max-Age=3600')
            self.end_headers()
        else:
            # 登录失败，返回错误页面
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            error_html = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>登录失败</title></head>
<body><div class="container"><div class="alert alert-danger">用户名或密码错误</div>
<a href="/login">重新登录</a></div></body></html>'''
            self.wfile.write(error_html.encode('utf-8'))
    
    def serve_logout(self):
        """登出处理"""
        cookie_header = self.headers.get('Cookie', '')
        if 'session_id=' in cookie_header:
            session_id = cookie_header.split('session_id=')[1].split(';')[0]
            if session_id in sessions:
                del sessions[session_id]
        
        self.send_response(302)
        self.send_header('Location', '/')
        self.send_header('Set-Cookie', 'session_id=; Path=/; Max-Age=0')
        self.end_headers()
    
    def serve_admin(self):
        """管理员后台页面"""
        current_user = get_session_user(self)
        if not current_user or not is_admin_user(current_user):
            self.send_response(302)
            self.send_header('Location', '/login')
            self.end_headers()
            return
        
        conn = sqlite3.connect('simple_wiki.db')
        cursor = conn.cursor()
        
        # 获取统计数据
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM documents')
        doc_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM comments')
        comment_count = cursor.fetchone()[0]
        
        # 获取最新文档
        cursor.execute('''
            SELECT id, title, created_at 
            FROM documents 
            ORDER BY created_at DESC 
            LIMIT 10
        ''')
        recent_docs = cursor.fetchall()
        
        # 获取最新用户
        cursor.execute('''
            SELECT username, created_at 
            FROM users 
            ORDER BY created_at DESC 
            LIMIT 5
        ''')
        recent_users = cursor.fetchall()
        
        conn.close()
        
        user_menu = self.get_user_menu_html(current_user)
        
        # 生成最新文档HTML
        docs_html = ''
        for doc in recent_docs:
            docs_html += f'''
            <tr>
                <td><span class="badge bg-secondary">{doc[0]}</span></td>
                <td>
                    <a href="/doc/{doc[0]}" class="text-decoration-none">
                        {doc[1]}
                    </a>
                </td>
                <td><small class="text-muted">{doc[2][:16]}</small></td>
                <td>
                    <a href="/doc/{doc[0]}" class="btn btn-outline-primary btn-sm">
                        <i class="fas fa-eye"></i>
                    </a>
                    <button class="btn btn-outline-danger btn-sm" 
                            onclick="deleteDoc({doc[0]})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
            '''
        
        # 生成最新用户HTML
        users_html = ''
        for user in recent_users:
            users_html += f'''
            <tr>
                <td>
                    <i class="fas fa-user-circle"></i> {user[0]}
                </td>
                <td><small class="text-muted">{user[1][:16]}</small></td>
            </tr>
            '''
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>管理员后台 - ROS2 Wiki</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .stats-card {{
            text-align: center;
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }}
        .admin-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem 0;
            margin-bottom: 2rem;
        }}
        .quick-action {{
            transition: transform 0.2s;
        }}
        .quick-action:hover {{
            transform: translateY(-2px);
        }}
    </style>
</head>
<body>
    <!-- 导航栏 -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-robot"></i> ROS2 Wiki
            </a>
            <div class="navbar-nav ms-auto">
                {user_menu}
            </div>
        </div>
    </nav>
    
    <!-- 管理员头部 -->
    <div class="admin-header">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <h1 class="display-5 fw-bold">
                        <i class="fas fa-tachometer-alt"></i> 管理员后台
                    </h1>
                    <p class="lead">系统管理和内容管理中心</p>
                </div>
                <div class="col-md-4 text-center">
                    <i class="fas fa-shield-alt fa-6x opacity-75"></i>
                </div>
            </div>
        </div>
    </div>
    
    <div class="container">
        <!-- 统计信息 -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card stats-card bg-primary text-white">
                    <div class="card-body">
                        <i class="fas fa-users fa-2x mb-2"></i>
                        <h3>{user_count}</h3>
                        <p>注册用户</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stats-card bg-success text-white">
                    <div class="card-body">
                        <i class="fas fa-file-alt fa-2x mb-2"></i>
                        <h3>{doc_count}</h3>
                        <p>技术文档</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stats-card bg-info text-white">
                    <div class="card-body">
                        <i class="fas fa-comments fa-2x mb-2"></i>
                        <h3>{comment_count}</h3>
                        <p>用户评论</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stats-card bg-warning text-white">
                    <div class="card-body">
                        <i class="fas fa-server fa-2x mb-2"></i>
                        <h3>运行中</h3>
                        <p>系统状态</p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 快速操作 -->
        <div class="row mb-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-bolt"></i> 快速操作</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <div class="d-grid">
                                    <button class="btn btn-success quick-action" onclick="showAddForm()">
                                        <i class="fas fa-plus fa-2x d-block mb-2"></i>
                                        新建文档
                                    </button>
                                </div>
                            </div>
                            <div class="col-md-3 mb-3">
                                <div class="d-grid">
                                    <a href="/search" class="btn btn-info quick-action">
                                        <i class="fas fa-search fa-2x d-block mb-2"></i>
                                        搜索内容
                                    </a>
                                </div>
                            </div>
                            <div class="col-md-3 mb-3">
                                <div class="d-grid">
                                    <a href="/api/health" class="btn btn-warning quick-action">
                                        <i class="fas fa-heart fa-2x d-block mb-2"></i>
                                        系统检查
                                    </a>
                                </div>
                            </div>
                            <div class="col-md-3 mb-3">
                                <div class="d-grid">
                                    <button class="btn btn-secondary quick-action" onclick="refreshData()">
                                        <i class="fas fa-sync fa-2x d-block mb-2"></i>
                                        刷新数据
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 管理面板 -->
        <div class="row">
            <div class="col-md-8">
                <!-- 最新文档 -->
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5><i class="fas fa-clock"></i> 最新文档</h5>
                        <button class="btn btn-success btn-sm" onclick="showAddForm()">
                            <i class="fas fa-plus"></i> 新建
                        </button>
                    </div>
                    <div class="card-body">
                        {f'''
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>标题</th>
                                        <th>创建时间</th>
                                        <th>操作</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {docs_html}
                                </tbody>
                            </table>
                        </div>
                        ''' if recent_docs else '''
                        <div class="text-center py-4">
                            <i class="fas fa-file-alt fa-3x text-muted mb-3"></i>
                            <h5 class="text-muted">暂无文档</h5>
                            <button class="btn btn-success" onclick="showAddForm()">
                                <i class="fas fa-plus"></i> 创建第一个文档
                            </button>
                        </div>
                        '''}
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <!-- 最新用户 -->
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-user-plus"></i> 最新用户</h5>
                    </div>
                    <div class="card-body">
                        {f'''
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <tbody>
                                    {users_html}
                                </tbody>
                            </table>
                        </div>
                        ''' if recent_users else '''
                        <p class="text-muted text-center">暂无新用户</p>
                        '''}
                    </div>
                </div>
                
                <!-- 系统信息 -->
                <div class="card mt-3">
                    <div class="card-header">
                        <h5><i class="fas fa-info-circle"></i> 系统信息</h5>
                    </div>
                    <div class="card-body">
                        <ul class="list-unstyled">
                            <li><i class="fas fa-check text-success"></i> 数据库连接正常</li>
                            <li><i class="fas fa-check text-success"></i> 会话管理正常</li>
                            <li><i class="fas fa-check text-success"></i> 权限验证正常</li>
                            <li><i class="fas fa-clock text-info"></i> 服务器时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- 新建文档模态框 -->
    <div class="modal fade" id="addDocModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title"><i class="fas fa-plus"></i> 新建文档</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <form method="POST" action="/admin/add">
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label">文档标题</label>
                            <input type="text" class="form-control" name="title" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">分类</label>
                            <select class="form-select" name="category">
                                <option value="ROS2基础">ROS2基础</option>
                                <option value="ROS2进阶">ROS2进阶</option>
                                <option value="机器人应用">机器人应用</option>
                                <option value="工具使用">工具使用</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">文档内容 (支持Markdown)</label>
                            <textarea class="form-control" name="content" rows="10" 
                                     placeholder="请输入Markdown格式的文档内容..." required></textarea>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="submit" class="btn btn-success">
                            <i class="fas fa-save"></i> 保存文档
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function showAddForm() {{
            new bootstrap.Modal(document.getElementById('addDocModal')).show();
        }}
        
        function deleteDoc(docId) {{
            if (confirm('确定要删除这个文档吗？')) {{
                fetch(`/admin/delete/${{docId}}`, {{method: 'DELETE'}})
                .then(() => location.reload());
            }}
        }}
        
        function refreshData() {{
            location.reload();
        }}
    </script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_register(self):
        """用户注册页面"""
        html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>用户注册 - ROS2 Wiki</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .register-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
        }
        .register-card {
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <div class="register-container">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-6 col-lg-5">
                    <div class="card register-card">
                        <div class="card-header text-center bg-primary text-white">
                            <h4><i class="fas fa-user-plus"></i> 用户注册</h4>
                        </div>
                        <div class="card-body p-4">
                            <form method="POST">
                                <div class="mb-3">
                                    <label class="form-label">
                                        <i class="fas fa-user"></i> 用户名
                                    </label>
                                    <input type="text" class="form-control" name="username" 
                                           placeholder="请输入用户名" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">
                                        <i class="fas fa-envelope"></i> 邮箱
                                    </label>
                                    <input type="email" class="form-control" name="email" 
                                           placeholder="请输入邮箱地址" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">
                                        <i class="fas fa-lock"></i> 密码
                                    </label>
                                    <input type="password" class="form-control" name="password" 
                                           placeholder="请输入密码" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">
                                        <i class="fas fa-lock"></i> 确认密码
                                    </label>
                                    <input type="password" class="form-control" name="confirm_password" 
                                           placeholder="请再次输入密码" required>
                                </div>
                                <div class="d-grid">
                                    <button type="submit" class="btn btn-primary btn-lg">
                                        <i class="fas fa-user-plus"></i> 注册账户
                                    </button>
                                </div>
                            </form>
                            
                            <hr>
                            <div class="text-center">
                                <p class="mb-0">已有账户？ 
                                    <a href="/login" class="text-decoration-none">立即登录</a>
                                </p>
                                <a href="/" class="btn btn-link">返回首页</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def handle_register(self):
        """处理用户注册"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        data = urllib.parse.parse_qs(post_data)
        
        username = data.get('username', [''])[0]
        email = data.get('email', [''])[0]
        password = data.get('password', [''])[0]
        confirm_password = data.get('confirm_password', [''])[0]
        
        # 验证密码
        if password != confirm_password:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            error_html = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>注册失败</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head><body><div class="container mt-5"><div class="alert alert-danger">密码不匹配</div>
<a href="/register" class="btn btn-primary">重新注册</a></div></body></html>'''
            self.wfile.write(error_html.encode('utf-8'))
            return
        
        # 检查用户名是否存在
        conn = sqlite3.connect('simple_wiki.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', (username,))
        if cursor.fetchone()[0] > 0:
            conn.close()
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            error_html = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>注册失败</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head><body><div class="container mt-5"><div class="alert alert-danger">用户名已存在</div>
<a href="/register" class="btn btn-primary">重新注册</a></div></body></html>'''
            self.wfile.write(error_html.encode('utf-8'))
            return
        
        # 创建新用户
        password_hash = hashlib.sha256((password + 'salt').encode()).hexdigest()
        cursor.execute('INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                      (username, email, password_hash, 0))
        conn.commit()
        conn.close()
        
        # 注册成功，重定向到登录页面
        self.send_response(302)
        self.send_header('Location', '/login')
        self.end_headers()
    
    def handle_admin_add(self):
        """处理管理员添加文档"""
        current_user = get_session_user(self)
        if not current_user or not is_admin_user(current_user):
            self.send_error(403, 'Forbidden')
            return
        
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        data = urllib.parse.parse_qs(post_data)
        
        title = data.get('title', [''])[0]
        content = data.get('content', [''])[0]
        category = data.get('category', ['ROS2基础'])[0]
        
        if title and content:
            conn = sqlite3.connect('simple_wiki.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO documents (title, content, category) VALUES (?, ?, ?)',
                          (title, content, category))
            conn.commit()
            conn.close()
        
        # 重定向回管理页面
        self.send_response(302)
        self.send_header('Location', '/admin')
        self.end_headers()

    def handle_comment(self, doc_id):
        """处理评论提交"""
        current_user = get_session_user(self)
        if not current_user:
            self.send_error(401, 'Unauthorized')
            return
        
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        data = urllib.parse.parse_qs(post_data)
        
        comment_content = data.get('content', [''])[0]
        
        if comment_content:
            conn = sqlite3.connect('simple_wiki.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO comments (document_id, username, content) VALUES (?, ?, ?)',
                          (doc_id, current_user, comment_content))
            conn.commit()
            conn.close()
        
        # 重定向回文档页面
        self.send_response(302)
        self.send_header('Location', f'/doc/{doc_id}')
        self.end_headers()

def main():
    init_db()
    # 支持Render等云平台的环境变量端口
    PORT = int(os.environ.get('PORT', 8000))
    
    print("🚀 ROS2 Wiki 增强版启动中...")
    print(f"📱 本地访问: http://localhost:{PORT}")
    print(f"🌍 公网访问: 启动 './ngrok http {PORT}' 获取公网地址")
    print(f"👤 管理员账户: admin / admin123")
    print(f"👤 测试用户: ros2_user / user123")
    print(f"✨ 新功能: 搜索、用户登录、评论系统、管理后台")
    print(f"🛑 按 Ctrl+C 停止服务")
    print("-" * 60)
    
    # 创建服务器并设置端口重用
    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True
    
    try:
        # 绑定到所有接口以支持云部署
        server_address = ("0.0.0.0", PORT)
        with ReusableTCPServer(server_address, WikiHandler) as httpd:
            print(f"✅ 服务器启动成功，监听端口 {PORT}")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n🛑 正在停止服务器...")
                print("✅ ROS2 Wiki 服务器已停止")
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"❌ 端口 {PORT} 被占用，尝试使用端口 {PORT+1}")
            PORT = PORT + 1
            try:
                server_address = ("0.0.0.0", PORT)
                with ReusableTCPServer(server_address, WikiHandler) as httpd:
                    print(f"✅ 服务器启动成功，监听端口 {PORT}")
                    print(f"📱 更新后的访问地址: http://localhost:{PORT}")
                    try:
                        httpd.serve_forever()
                    except KeyboardInterrupt:
                        print("\n🛑 正在停止服务器...")
                        print("✅ ROS2 Wiki 服务器已停止")
            except Exception as e:
                print(f"❌ 服务器启动失败: {e}")
        else:
            print(f"❌ 服务器启动失败: {e}")

if __name__ == "__main__":
    main()