# 内容管理系统 (CMS) 模块

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import sqlite3
import markdown
import os
from datetime import datetime
from app.security import (
    admin_required, InputValidator, PasswordValidator, 
    FileUploadSecurity, validate_csrf_token
)

cms_bp = Blueprint('cms', __name__, url_prefix='/admin')

class ContentManager:
    """内容管理器"""
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    def get_all_documents(self, page=1, per_page=10, category=None, search=None):
        """获取所有文档列表"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 构建查询条件
            where_conditions = []
            params = []
            
            if category:
                where_conditions.append("category = ?")
                params.append(category)
            
            if search:
                where_conditions.append("(title LIKE ? OR content LIKE ?)")
                params.extend([f"%{search}%", f"%{search}%"])
            
            where_clause = " AND ".join(where_conditions) if where_conditions else ""
            if where_clause:
                where_clause = "WHERE " + where_clause
            
            # 获取总数
            count_sql = f"SELECT COUNT(*) as total FROM documents {where_clause}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total']
            
            # 获取分页数据
            offset = (page - 1) * per_page
            data_sql = f"""
            SELECT id, title, category, created_at, updated_at, author_id
            FROM documents {where_clause}
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
            """
            cursor.execute(data_sql, params + [per_page, offset])
            documents = cursor.fetchall()
            
            conn.close()
            
            return {
                'documents': [dict(doc) for doc in documents],
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
            
        except Exception as e:
            print(f"获取文档列表错误: {e}")
            return {'documents': [], 'total': 0, 'page': 1, 'per_page': per_page, 'total_pages': 0}
    
    def get_document(self, doc_id):
        """获取单个文档详情"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT d.*, u.username as author_name
            FROM documents d
            LEFT JOIN users u ON d.author_id = u.id
            WHERE d.id = ?
            """, [doc_id])
            
            document = cursor.fetchone()
            conn.close()
            
            return dict(document) if document else None
            
        except Exception as e:
            print(f"获取文档详情错误: {e}")
            return None
    
    def create_document(self, title, content, category, author_id):
        """创建新文档"""
        try:
            # 验证输入
            is_valid, error = InputValidator.validate_content_length(title, 200)
            if not is_valid:
                return False, f"标题错误: {error}"
            
            is_valid, error = InputValidator.validate_content_length(content, 50000)
            if not is_valid:
                return False, f"内容错误: {error}"
            
            # 清理和验证内容
            clean_title = InputValidator.sanitize_html(title, allow_tags=False)
            clean_content = InputValidator.sanitize_html(content, allow_tags=True)
            clean_category = InputValidator.sanitize_html(category, allow_tags=False)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO documents (title, content, category, author_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """, [
                clean_title, clean_content, clean_category, author_id,
                datetime.now(), datetime.now()
            ])
            
            doc_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return True, doc_id
            
        except Exception as e:
            print(f"创建文档错误: {e}")
            return False, str(e)
    
    def update_document(self, doc_id, title, content, category):
        """更新文档"""
        try:
            # 验证输入
            is_valid, error = InputValidator.validate_content_length(title, 200)
            if not is_valid:
                return False, f"标题错误: {error}"
            
            is_valid, error = InputValidator.validate_content_length(content, 50000)
            if not is_valid:
                return False, f"内容错误: {error}"
            
            # 清理内容
            clean_title = InputValidator.sanitize_html(title, allow_tags=False)
            clean_content = InputValidator.sanitize_html(content, allow_tags=True)
            clean_category = InputValidator.sanitize_html(category, allow_tags=False)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            UPDATE documents 
            SET title = ?, content = ?, category = ?, updated_at = ?
            WHERE id = ?
            """, [clean_title, clean_content, clean_category, datetime.now(), doc_id])
            
            conn.commit()
            affected_rows = cursor.rowcount
            conn.close()
            
            return affected_rows > 0, "更新成功" if affected_rows > 0 else "文档不存在"
            
        except Exception as e:
            print(f"更新文档错误: {e}")
            return False, str(e)
    
    def delete_document(self, doc_id):
        """删除文档"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 同时删除相关评论
            cursor.execute("DELETE FROM comments WHERE document_id = ?", [doc_id])
            cursor.execute("DELETE FROM documents WHERE id = ?", [doc_id])
            
            conn.commit()
            affected_rows = cursor.rowcount
            conn.close()
            
            return affected_rows > 0, "删除成功" if affected_rows > 0 else "文档不存在"
            
        except Exception as e:
            print(f"删除文档错误: {e}")
            return False, str(e)
    
    def get_categories(self):
        """获取所有分类"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM documents 
            WHERE category IS NOT NULL AND category != ''
            GROUP BY category 
            ORDER BY count DESC, category
            """)
            
            categories = cursor.fetchall()
            conn.close()
            
            return [{'name': cat[0], 'count': cat[1]} for cat in categories]
            
        except Exception as e:
            print(f"获取分类错误: {e}")
            return []
    
    def get_statistics(self):
        """获取内容统计信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 文档统计
            cursor.execute("SELECT COUNT(*) FROM documents")
            total_docs = cursor.fetchone()[0]
            
            # 分类统计
            cursor.execute("SELECT COUNT(DISTINCT category) FROM documents WHERE category IS NOT NULL")
            total_categories = cursor.fetchone()[0]
            
            # 评论统计
            cursor.execute("SELECT COUNT(*) FROM comments")
            total_comments = cursor.fetchone()[0]
            
            # 用户统计
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            # 最近活动
            cursor.execute("""
            SELECT title, updated_at 
            FROM documents 
            ORDER BY updated_at DESC 
            LIMIT 5
            """)
            recent_activities = cursor.fetchall()
            
            conn.close()
            
            return {
                'total_documents': total_docs,
                'total_categories': total_categories,
                'total_comments': total_comments,
                'total_users': total_users,
                'recent_activities': [
                    {'title': act[0], 'updated_at': act[1]} 
                    for act in recent_activities
                ]
            }
            
        except Exception as e:
            print(f"获取统计信息错误: {e}")
            return {}

# 获取内容管理器实例
def get_content_manager():
    """获取内容管理器实例"""
    db_path = os.environ.get('SQLITE_DATABASE_URL', 'sqlite:///ros2_wiki.db')
    if db_path.startswith('sqlite:///'):
        db_path = db_path[10:]
    return ContentManager(db_path)

# 路由定义
@cms_bp.route('/')
@login_required
@admin_required
def dashboard():
    """管理后台首页"""
    cm = get_content_manager()
    stats = cm.get_statistics()
    return render_template('admin/dashboard.html', stats=stats)

@cms_bp.route('/documents')
@login_required
@admin_required
def documents():
    """文档管理页面"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    category = request.args.get('category')
    search = request.args.get('search')
    
    cm = get_content_manager()
    data = cm.get_all_documents(page, per_page, category, search)
    categories = cm.get_categories()
    
    return render_template('admin/documents.html', 
                         documents=data['documents'],
                         pagination=data,
                         categories=categories,
                         current_category=category,
                         current_search=search)

@cms_bp.route('/documents/new')
@login_required
@admin_required
def new_document():
    """新建文档页面"""
    cm = get_content_manager()
    categories = cm.get_categories()
    return render_template('admin/edit_document.html', 
                         document=None, 
                         categories=categories)

@cms_bp.route('/documents/<int:doc_id>/edit')
@login_required
@admin_required
def edit_document(doc_id):
    """编辑文档页面"""
    cm = get_content_manager()
    document = cm.get_document(doc_id)
    categories = cm.get_categories()
    
    if not document:
        flash('文档不存在', 'error')
        return redirect(url_for('cms.documents'))
    
    return render_template('admin/edit_document.html', 
                         document=document, 
                         categories=categories)

@cms_bp.route('/documents/save', methods=['POST'])
@login_required
@admin_required
@validate_csrf_token
def save_document():
    """保存文档"""
    doc_id = request.form.get('doc_id')
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    category = request.form.get('category', '').strip()
    
    if not title or not content:
        flash('标题和内容不能为空', 'error')
        return redirect(request.referrer or url_for('cms.documents'))
    
    cm = get_content_manager()
    
    if doc_id:  # 更新现有文档
        success, message = cm.update_document(doc_id, title, content, category)
    else:  # 创建新文档
        success, message = cm.create_document(title, content, category, current_user.id)
    
    if success:
        flash('文档保存成功', 'success')
        return redirect(url_for('cms.documents'))
    else:
        flash(f'保存失败: {message}', 'error')
        return redirect(request.referrer or url_for('cms.documents'))

@cms_bp.route('/documents/<int:doc_id>/delete', methods=['POST'])
@login_required
@admin_required
@validate_csrf_token
def delete_document(doc_id):
    """删除文档"""
    cm = get_content_manager()
    success, message = cm.delete_document(doc_id)
    
    if success:
        flash('文档删除成功', 'success')
    else:
        flash(f'删除失败: {message}', 'error')
    
    return redirect(url_for('cms.documents'))

@cms_bp.route('/preview', methods=['POST'])
@login_required
@admin_required
def preview_markdown():
    """Markdown预览"""
    content = request.json.get('content', '')
    
    # 清理和转换Markdown
    clean_content = InputValidator.sanitize_html(content, allow_tags=True)
    html_content = markdown.markdown(
        clean_content,
        extensions=['codehilite', 'fenced_code', 'tables', 'toc']
    )
    
    return jsonify({'html': html_content})

@cms_bp.route('/upload', methods=['POST'])
@login_required
@admin_required
def upload_file():
    """文件上传"""
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    # 验证文件
    if not FileUploadSecurity.allowed_file(file.filename):
        return jsonify({'error': '不支持的文件类型'}), 400
    
    if not FileUploadSecurity.validate_file_size(len(file.read())):
        return jsonify({'error': '文件太大'}), 400
    
    file.seek(0)  # 重置文件指针
    
    # 安全处理文件名
    filename = FileUploadSecurity.sanitize_filename(file.filename)
    
    # 保存文件
    upload_folder = os.path.join('static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    
    # 返回文件URL
    file_url = url_for('static', filename=f'uploads/{filename}')
    return jsonify({'url': file_url, 'filename': filename})