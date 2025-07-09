"""
API端点测试
"""
import pytest
import json
from app.models import Document, User


class TestDocumentAPI:
    """文档API测试"""
    
    def test_get_documents_empty(self, client):
        """测试获取空文档列表"""
        response = client.get('/api/v1/documents')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data'] == []
        assert data['meta']['total'] == 0
    
    def test_get_documents_with_data(self, client, test_document):
        """测试获取文档列表"""
        response = client.get('/api/v1/documents')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['data']) == 1
        assert data['data'][0]['title'] == test_document.title
    
    def test_get_document_by_id(self, client, test_document):
        """测试获取单个文档"""
        response = client.get(f'/api/v1/documents/{test_document.id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['id'] == test_document.id
        assert data['data']['view_count'] == 1  # 访问后应该增加
    
    def test_create_document_unauthorized(self, client):
        """测试未授权创建文档"""
        response = client.post('/api/v1/documents', 
            json={'title': 'Test', 'content': 'Test', 'category': 'test'})
        assert response.status_code == 401
    
    def test_create_document_authorized(self, client, auth, test_user):
        """测试授权创建文档"""
        auth.login()
        response = client.post('/api/v1/documents', json={
            'title': 'New Document',
            'content': 'This is a new document',
            'category': 'tutorial'
        })
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['data']['title'] == 'New Document'
        assert data['data']['author']['id'] == test_user.id
    
    def test_update_document(self, client, auth, test_document):
        """测试更新文档"""
        auth.login()
        response = client.put(f'/api/v1/documents/{test_document.id}', json={
            'title': 'Updated Title'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['title'] == 'Updated Title'
    
    def test_delete_document(self, client, auth, test_document):
        """测试删除文档"""
        auth.login()
        response = client.delete(f'/api/v1/documents/{test_document.id}')
        assert response.status_code == 200
        
        # 验证文档已被删除
        response = client.get(f'/api/v1/documents/{test_document.id}')
        assert response.status_code == 404
    
    def test_search_documents(self, client, test_document):
        """测试搜索功能"""
        response = client.get('/api/v1/documents?search=Test')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['data']) > 0
    
    def test_filter_by_category(self, client, test_document):
        """测试按分类筛选"""
        response = client.get('/api/v1/documents?category=tutorial')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert all(doc['category'] == 'tutorial' for doc in data['data'])
    
    def test_pagination(self, client, app):
        """测试分页功能"""
        # 创建多个文档
        with app.app_context():
            user = User.query.first()
            for i in range(25):
                doc = Document(
                    title=f'Document {i}',
                    content=f'Content {i}',
                    category='test',
                    user_id=user.id
                )
                db.session.add(doc)
            db.session.commit()
        
        # 测试第一页
        response = client.get('/api/v1/documents?per_page=10')
        data = json.loads(response.data)
        assert len(data['data']) == 10
        assert data['meta']['pages'] == 3
        assert data['links']['next'] is not None
        assert data['links']['prev'] is None


class TestCommentAPI:
    """评论API测试"""
    
    def test_create_comment(self, client, auth, test_document):
        """测试创建评论"""
        auth.login()
        response = client.post(f'/api/v1/documents/{test_document.id}/comments', 
            json={'content': 'Great article!'})
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['data']['content'] == 'Great article!'
    
    def test_get_document_with_comments(self, client, app, test_document, test_user):
        """测试获取文档及其评论"""
        # 先创建一些评论
        with app.app_context():
            from app.models import Comment
            comment = Comment(
                content='Test comment',
                user_id=test_user.id,
                document_id=test_document.id
            )
            db.session.add(comment)
            db.session.commit()
        
        response = client.get(f'/api/v1/documents/{test_document.id}')
        data = json.loads(response.data)
        assert len(data['comments']) == 1
        assert data['comments'][0]['content'] == 'Test comment'


class TestStatsAPI:
    """统计API测试"""
    
    def test_get_stats(self, client, test_document):
        """测试获取统计信息"""
        response = client.get('/api/v1/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['total_documents'] >= 1
        assert data['data']['total_users'] >= 1