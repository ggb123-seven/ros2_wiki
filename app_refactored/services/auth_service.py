"""
认证服务
米醋电子工作室 - SuperClaude重构
"""

from datetime import datetime
from ..models.database import get_db_connection

class AuthService:
    """认证相关业务逻辑"""
    
    def log_user_action(self, user_id, action, ip_address, details=None):
        """记录用户操作日志"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 确保user_logs表存在
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                ip_address TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        try:
            cursor.execute('''
                INSERT INTO user_logs (user_id, action, ip_address, details)
                VALUES (?, ?, ?, ?)
            ''', (user_id, action, ip_address, details))
            
            conn.commit()
            
        except Exception as e:
            print(f"记录用户日志失败: {e}")
            conn.rollback()
    
    def get_user_login_history(self, user_id, limit=10):
        """获取用户登录历史"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT action, ip_address, timestamp
            FROM user_logs
            WHERE user_id = ? AND action IN ('login', 'logout')
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (user_id, limit))
        
        return cursor.fetchall()
    
    def get_failed_login_attempts(self, ip_address, since_minutes=30):
        """获取指定IP的失败登录尝试次数"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*)
            FROM user_logs
            WHERE ip_address = ? 
            AND action = 'login_failed'
            AND timestamp > datetime('now', '-{} minutes')
        '''.format(since_minutes), (ip_address,))
        
        result = cursor.fetchone()
        return result[0] if result else 0
    
    def is_ip_blocked(self, ip_address, max_attempts=5):
        """检查IP是否被阻止"""
        failed_attempts = self.get_failed_login_attempts(ip_address)
        return failed_attempts >= max_attempts
    
    def log_failed_login(self, username, ip_address):
        """记录失败的登录尝试"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 记录到特殊的失败登录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS failed_logins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        try:
            cursor.execute('''
                INSERT INTO failed_logins (username, ip_address)
                VALUES (?, ?)
            ''', (username, ip_address))
            
            conn.commit()
            
        except Exception as e:
            print(f"记录失败登录失败: {e}")
            conn.rollback()
    
    def cleanup_old_logs(self, days=30):
        """清理旧的日志记录"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 清理用户日志
            cursor.execute('''
                DELETE FROM user_logs
                WHERE timestamp < datetime('now', '-{} days')
            '''.format(days))
            
            # 清理失败登录记录
            cursor.execute('''
                DELETE FROM failed_logins
                WHERE timestamp < datetime('now', '-{} days')
            '''.format(days))
            
            conn.commit()
            print(f"清理了{days}天前的日志记录")
            
        except Exception as e:
            print(f"清理日志失败: {e}")
            conn.rollback()
    
    def get_user_statistics(self):
        """获取用户统计信息"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # 总用户数
        cursor.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = cursor.fetchone()[0]
        
        # 管理员数
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
        stats['admin_users'] = cursor.fetchone()[0]
        
        # 今日注册用户
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE DATE(created_at) = DATE('now')
        ''')
        stats['today_registrations'] = cursor.fetchone()[0]
        
        # 本周活跃用户
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM user_logs
            WHERE timestamp > datetime('now', '-7 days')
            AND action = 'login'
        ''')
        stats['weekly_active_users'] = cursor.fetchone()[0]
        
        return stats