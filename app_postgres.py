from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import markdown
import os
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__)

# 配置
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///ros2_wiki.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化扩展
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 数据库模型
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    documents = db.relationship('Document', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')

class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    view_count = db.Column(db.Integer, default=0)
    
    # 关系
    comments = db.relationship('Comment', backref='document', lazy='dynamic', cascade='all, delete-orphan')

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('需要管理员权限', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# 路由
@app.route('/')
def index():
    category = request.args.get('category')
    query = Document.query
    if category:
        query = query.filter_by(category=category)
    documents = query.order_by(Document.created_at.desc()).all()
    
    # 获取所有分类
    categories = db.session.query(Document.category).distinct().all()
    categories = [c[0] for c in categories]
    
    return render_template('index.html', documents=documents, categories=categories, current_category=category)

@app.route('/document/<int:doc_id>')
def view_document(doc_id):
    document = Document.query.get_or_404(doc_id)
    document.view_count += 1
    db.session.commit()
    
    # 转换Markdown为HTML
    content_html = markdown.markdown(document.content, extensions=['extra', 'codehilite'])
    comments = Comment.query.filter_by(document_id=doc_id).order_by(Comment.created_at.desc()).all()
    
    return render_template('document.html', document=document, content_html=content_html, comments=comments)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 检查用户是否存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'error')
            return redirect(url_for('register'))
        
        # 创建新用户
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功！请登录', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/add_comment/<int:doc_id>', methods=['POST'])
@login_required
def add_comment(doc_id):
    content = request.form.get('content')
    if content:
        comment = Comment(
            content=content,
            user_id=current_user.id,
            document_id=doc_id
        )
        db.session.add(comment)
        db.session.commit()
        flash('评论添加成功', 'success')
    
    return redirect(url_for('view_document', doc_id=doc_id))

# 管理员路由
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_documents = Document.query.count()
    total_comments = Comment.query.count()
    recent_documents = Document.query.order_by(Document.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_documents=total_documents,
                         total_comments=total_comments,
                         recent_documents=recent_documents)

@app.route('/admin/upload', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_upload():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')
        
        document = Document(
            title=title,
            content=content,
            category=category,
            user_id=current_user.id
        )
        db.session.add(document)
        db.session.commit()
        
        flash('文档上传成功', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/upload.html')

@app.route('/admin/edit/<int:doc_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit(doc_id):
    document = Document.query.get_or_404(doc_id)
    
    if request.method == 'POST':
        document.title = request.form.get('title')
        document.content = request.form.get('content')
        document.category = request.form.get('category')
        document.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('文档更新成功', 'success')
        return redirect(url_for('view_document', doc_id=doc_id))
    
    return render_template('admin/edit.html', document=document)

@app.route('/admin/delete/<int:doc_id>')
@login_required
@admin_required
def admin_delete(doc_id):
    document = Document.query.get_or_404(doc_id)
    db.session.delete(document)
    db.session.commit()
    
    flash('文档删除成功', 'success')
    return redirect(url_for('admin_dashboard'))

def init_db():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        
        # 创建默认管理员账号（如果不存在）
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@ros2wiki.local',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("默认管理员账号创建成功: admin / admin123")

# 注册API蓝图
try:
    from app.api import bp as api_bp
    app.register_blueprint(api_bp)
except ImportError:
    pass  # API模块可选

if __name__ == '__main__':
    print(f"使用数据库: {app.config['SQLALCHEMY_DATABASE_URI']}")
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)