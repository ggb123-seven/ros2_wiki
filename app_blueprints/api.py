"""
RESTful API Blueprint
"""
from flask import Blueprint, jsonify, request, abort
from flask_login import login_required, current_user
from app.models import Document, Comment, User, db
from app.utils.decorators import admin_required
from datetime import datetime
import markdown

bp = Blueprint('api', __name__, url_prefix='/api/v1')


def serialize_document(doc):
    """序列化文档对象"""
    return {
        'id': doc.id,
        'title': doc.title,
        'content': doc.content,
        'content_html': markdown.markdown(doc.content),
        'category': doc.category,
        'author': {
            'id': doc.author.id,
            'username': doc.author.username
        },
        'created_at': doc.created_at.isoformat(),
        'updated_at': doc.updated_at.isoformat(),
        'view_count': doc.view_count,
        'comment_count': doc.comments.count(),
        'url': f'/documents/{doc.id}'
    }


def serialize_comment(comment):
    """序列化评论对象"""
    return {
        'id': comment.id,
        'content': comment.content,
        'author': {
            'id': comment.author.id,
            'username': comment.author.username
        },
        'created_at': comment.created_at.isoformat(),
        'updated_at': comment.updated_at.isoformat()
    }


# 文档API端点
@bp.route('/documents', methods=['GET'])
def get_documents():
    """获取文档列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category = request.args.get('category')
    search = request.args.get('search')
    
    query = Document.query
    
    # 筛选条件
    if category:
        query = query.filter_by(category=category)
    
    # 搜索功能（使用数据库适配器）
    if search:
        from app.database import get_database_adapter, DatabaseManager
        adapter = get_database_adapter(current_app)
        manager = DatabaseManager(adapter)
        # 这里需要改进为使用适配器的搜索
        query = query.filter(
            db.or_(
                Document.title.contains(search),
                Document.content.contains(search)
            )
        )
    
    # 分页
    pagination = query.order_by(Document.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'data': [serialize_document(doc) for doc in pagination.items],
        'meta': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages
        },
        'links': {
            'self': request.url,
            'next': f'/api/v1/documents?page={page+1}' if pagination.has_next else None,
            'prev': f'/api/v1/documents?page={page-1}' if pagination.has_prev else None
        }
    })


@bp.route('/documents/<int:id>', methods=['GET'])
def get_document(id):
    """获取单个文档"""
    doc = Document.query.get_or_404(id)
    
    # 增加浏览次数
    doc.view_count += 1
    db.session.commit()
    
    return jsonify({
        'data': serialize_document(doc),
        'comments': [serialize_comment(c) for c in doc.comments.order_by(Comment.created_at.desc()).all()]
    })


@bp.route('/documents', methods=['POST'])
@login_required
def create_document():
    """创建文档"""
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['title', 'content', 'category']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # 创建文档
    doc = Document(
        title=data['title'],
        content=data['content'],
        category=data['category'],
        user_id=current_user.id
    )
    
    db.session.add(doc)
    db.session.commit()
    
    return jsonify({
        'data': serialize_document(doc),
        'message': 'Document created successfully'
    }), 201


@bp.route('/documents/<int:id>', methods=['PUT'])
@login_required
def update_document(id):
    """更新文档"""
    doc = Document.query.get_or_404(id)
    
    # 检查权限
    if doc.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    data = request.get_json()
    
    # 更新字段
    if 'title' in data:
        doc.title = data['title']
    if 'content' in data:
        doc.content = data['content']
    if 'category' in data:
        doc.category = data['category']
    
    doc.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'data': serialize_document(doc),
        'message': 'Document updated successfully'
    })


@bp.route('/documents/<int:id>', methods=['DELETE'])
@login_required
def delete_document(id):
    """删除文档"""
    doc = Document.query.get_or_404(id)
    
    # 检查权限
    if doc.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    db.session.delete(doc)
    db.session.commit()
    
    return jsonify({
        'message': 'Document deleted successfully'
    })


# 评论API端点
@bp.route('/documents/<int:doc_id>/comments', methods=['POST'])
@login_required
def create_comment(doc_id):
    """创建评论"""
    doc = Document.query.get_or_404(doc_id)
    data = request.get_json()
    
    if 'content' not in data:
        return jsonify({'error': 'Missing required field: content'}), 400
    
    comment = Comment(
        content=data['content'],
        user_id=current_user.id,
        document_id=doc_id
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({
        'data': serialize_comment(comment),
        'message': 'Comment created successfully'
    }), 201


# 统计API端点
@bp.route('/stats', methods=['GET'])
def get_stats():
    """获取站点统计信息"""
    from app.database import get_database_adapter, DatabaseManager
    adapter = get_database_adapter(current_app)
    manager = DatabaseManager(adapter)
    
    stats = {
        'total_documents': Document.query.count(),
        'total_users': User.query.count(),
        'total_comments': Comment.query.count(),
        'categories': manager.get_document_stats()
    }
    
    return jsonify({'data': stats})


# 错误处理
@bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404


@bp.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Access forbidden'}), 403


@bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500