import pytest
from app import create_app, db
from app.models import User, Document
from config import TestingConfig


@pytest.fixture
def app():
    """创建应用实例用于测试"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """创建CLI测试运行器"""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """创建测试用户"""
    user = User(
        username='testuser',
        email='test@example.com'
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin_user(app):
    """创建管理员用户"""
    admin = User(
        username='admin',
        email='admin@example.com',
        is_admin=True
    )
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    return admin


@pytest.fixture
def test_document(app, test_user):
    """创建测试文档"""
    doc = Document(
        title='Test Document',
        content='# Test Content\n\nThis is a test document.',
        category='tutorial',
        user_id=test_user.id
    )
    db.session.add(doc)
    db.session.commit()
    return doc


class AuthActions:
    """认证辅助类"""
    def __init__(self, client):
        self._client = client
    
    def login(self, username='testuser', password='password123'):
        return self._client.post('/auth/login', data={
            'username': username,
            'password': password
        })
    
    def logout(self):
        return self._client.get('/auth/logout')


@pytest.fixture
def auth(client):
    """认证操作fixture"""
    return AuthActions(client)