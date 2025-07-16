#!/usr/bin/env python3
"""
ROS2 Wiki应用datetime修复完整验证测试
全面测试PostgreSQL和SQLite环境下的修复效果
"""

import sys
import os
import time
import traceback
from datetime import datetime
from jinja2 import TemplateSyntaxError

# 导入应用
from app import app, DatabaseCompatibility, get_db_connection, HAS_POSTGRESQL

class DatetimeFixTestSuite:
    """datetime修复测试套件"""
    
    def __init__(self):
        self.test_results = {}
        self.performance_data = {}
        self.start_time = time.time()
        
    def log_test(self, test_name, passed, details=""):
        """记录测试结果"""
        self.test_results[test_name] = {
            'passed': passed,
            'details': details,
            'timestamp': datetime.now()
        }
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} {test_name}: {details}")
        
    def test_database_compatibility_class(self):
        """测试DatabaseCompatibility工具类"""
        print("\n🧪 测试DatabaseCompatibility工具类...")
        
        try:
            # 测试PostgreSQL模式
            use_postgresql = True
            
            # 测试datetime对象
            dt_obj = datetime(2024, 7, 16, 14, 30, 25)
            result1 = DatabaseCompatibility.format_datetime(dt_obj)
            expected1 = "2024-07-16 14:30"
            
            if result1 == expected1:
                self.log_test("PostgreSQL_datetime对象", True, f"输出: {result1}")
            else:
                self.log_test("PostgreSQL_datetime对象", False, f"期望: {expected1}, 实际: {result1}")
                return False
            
            # 测试SQLite模式
            dt_str = "2024-07-16 14:30:25"
            result2 = DatabaseCompatibility.format_datetime(dt_str)
            expected2 = "2024-07-16 14:30"
            
            if result2 == expected2:
                self.log_test("SQLite_字符串格式", True, f"输出: {result2}")
            else:
                self.log_test("SQLite_字符串格式", False, f"期望: {expected2}, 实际: {result2}")
                return False
            
            # 测试None值处理
            result3 = DatabaseCompatibility.format_datetime(None)
            expected3 = "N/A"
            
            if result3 == expected3:
                self.log_test("None值处理", True, f"输出: {result3}")
            else:
                self.log_test("None值处理", False, f"期望: {expected3}, 实际: {result3}")
                return False
            
            # 测试自定义格式
            result4 = DatabaseCompatibility.format_datetime(dt_obj, '%Y/%m/%d %H:%M:%S')
            expected4 = "2024/07/16 14:30:25"
            
            if result4 == expected4:
                self.log_test("自定义格式", True, f"输出: {result4}")
            else:
                self.log_test("自定义格式", False, f"期望: {expected4}, 实际: {result4}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("DatabaseCompatibility工具类", False, f"异常: {e}")
            return False
    
    def test_template_filter(self):
        """测试dt_format模板过滤器"""
        print("\n🧪 测试dt_format模板过滤器...")
        
        with app.app_context():
            try:
                # 检查过滤器注册
                if 'dt_format' not in app.jinja_env.filters:
                    self.log_test("过滤器注册", False, "dt_format过滤器未注册")
                    return False
                
                self.log_test("过滤器注册", True, "dt_format过滤器已注册")
                
                # 测试过滤器功能
                template_str = "{{ dt|dt_format if dt else 'N/A' }}"
                template = app.jinja_env.from_string(template_str)
                
                # 测试datetime对象
                dt_obj = datetime(2024, 7, 16, 14, 30, 25)
                result1 = template.render(dt=dt_obj)
                expected1 = "2024-07-16 14:30"
                
                if result1 == expected1:
                    self.log_test("过滤器_datetime对象", True, f"输出: {result1}")
                else:
                    self.log_test("过滤器_datetime对象", False, f"期望: {expected1}, 实际: {result1}")
                    return False
                
                # 测试字符串格式
                dt_str = "2024-07-16 14:30:25"
                result2 = template.render(dt=dt_str)
                expected2 = "2024-07-16 14:30"
                
                if result2 == expected2:
                    self.log_test("过滤器_字符串格式", True, f"输出: {result2}")
                else:
                    self.log_test("过滤器_字符串格式", False, f"期望: {expected2}, 实际: {result2}")
                    return False
                
                # 测试None值
                result3 = template.render(dt=None)
                expected3 = "N/A"
                
                if result3 == expected3:
                    self.log_test("过滤器_None值", True, f"输出: {result3}")
                else:
                    self.log_test("过滤器_None值", False, f"期望: {expected3}, 实际: {result3}")
                    return False
                
                return True
                
            except Exception as e:
                self.log_test("模板过滤器", False, f"异常: {e}")
                return False
    
    def test_template_syntax(self):
        """测试所有修复的模板语法"""
        print("\n🧪 测试模板语法...")
        
        templates_to_test = [
            'admin_dashboard.html',
            'document.html',
            'search/results.html',
            'admin/dashboard.html'
        ]
        
        with app.app_context():
            all_passed = True
            
            for template_name in templates_to_test:
                try:
                    template = app.jinja_env.get_template(template_name)
                    self.log_test(f"模板语法_{template_name}", True, "语法正确")
                except TemplateSyntaxError as e:
                    self.log_test(f"模板语法_{template_name}", False, f"语法错误: {e}")
                    all_passed = False
                except Exception as e:
                    self.log_test(f"模板语法_{template_name}", False, f"加载异常: {e}")
                    all_passed = False
            
            return all_passed
    
    def test_template_rendering(self):
        """测试模板渲染功能"""
        print("\n🧪 测试模板渲染...")
        
        with app.app_context():
            try:
                # 模拟数据
                mock_data = {
                    'user': {
                        'username': 'test_user',
                        'email': 'test@example.com',
                        'created_at': datetime(2024, 7, 16, 14, 30, 25)
                    },
                    'document': {
                        'title': 'ROS2测试文档',
                        'content': '测试内容',
                        'created_at': datetime(2024, 7, 16, 14, 30, 25),
                        'updated_at': datetime(2024, 7, 16, 15, 45, 10)
                    },
                    'comment': {
                        'content': '测试评论',
                        'created_at': datetime(2024, 7, 16, 16, 20, 30)
                    }
                }
                
                # 测试用户时间显示
                user_template = "{{ user.created_at|dt_format if user.created_at else 'N/A' }}"
                user_tmpl = app.jinja_env.from_string(user_template)
                user_result = user_tmpl.render(**mock_data)
                
                if "2024-07-16 14:30" in user_result:
                    self.log_test("用户时间渲染", True, f"输出: {user_result}")
                else:
                    self.log_test("用户时间渲染", False, f"输出: {user_result}")
                    return False
                
                # 测试文档时间显示
                doc_template = """
                发布时间：{{ document.created_at|dt_format }}
                更新时间：{{ document.updated_at|dt_format }}
                """
                doc_tmpl = app.jinja_env.from_string(doc_template)
                doc_result = doc_tmpl.render(**mock_data)
                
                if "2024-07-16 14:30" in doc_result and "2024-07-16 15:45" in doc_result:
                    self.log_test("文档时间渲染", True, "发布和更新时间正确")
                else:
                    self.log_test("文档时间渲染", False, f"输出: {doc_result}")
                    return False
                
                # 测试评论时间显示
                comment_template = "{{ comment.created_at|dt_format }}"
                comment_tmpl = app.jinja_env.from_string(comment_template)
                comment_result = comment_tmpl.render(**mock_data)
                
                if "2024-07-16 16:20" in comment_result:
                    self.log_test("评论时间渲染", True, f"输出: {comment_result}")
                else:
                    self.log_test("评论时间渲染", False, f"输出: {comment_result}")
                    return False
                
                return True
                
            except Exception as e:
                self.log_test("模板渲染", False, f"异常: {e}")
                return False
    
    def test_performance(self):
        """测试性能影响"""
        print("\n🧪 测试性能影响...")
        
        try:
            # 测试datetime格式化性能
            test_datetime = datetime(2024, 7, 16, 14, 30, 25)
            iterations = 1000
            
            # 测试DatabaseCompatibility.format_datetime性能
            start_time = time.time()
            for _ in range(iterations):
                DatabaseCompatibility.format_datetime(test_datetime)
            db_compat_time = time.time() - start_time
            
            # 测试模板过滤器性能
            with app.app_context():
                template_str = "{{ dt|dt_format }}"
                template = app.jinja_env.from_string(template_str)
                
                start_time = time.time()
                for _ in range(iterations):
                    template.render(dt=test_datetime)
                filter_time = time.time() - start_time
            
            # 记录性能数据
            self.performance_data = {
                'db_compat_time': db_compat_time,
                'filter_time': filter_time,
                'iterations': iterations,
                'avg_db_compat': db_compat_time / iterations * 1000,  # ms
                'avg_filter': filter_time / iterations * 1000  # ms
            }
            
            # 性能阈值检查（每次调用不超过1ms）
            if self.performance_data['avg_db_compat'] < 1.0 and self.performance_data['avg_filter'] < 1.0:
                self.log_test("性能测试", True, 
                    f"DatabaseCompatibility: {self.performance_data['avg_db_compat']:.3f}ms, "
                    f"过滤器: {self.performance_data['avg_filter']:.3f}ms")
                return True
            else:
                self.log_test("性能测试", False, 
                    f"性能超出阈值 - DatabaseCompatibility: {self.performance_data['avg_db_compat']:.3f}ms, "
                    f"过滤器: {self.performance_data['avg_filter']:.3f}ms")
                return False
                
        except Exception as e:
            self.log_test("性能测试", False, f"异常: {e}")
            return False
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n🧪 测试错误处理...")
        
        try:
            # 测试无效输入
            invalid_inputs = [
                12345,  # 数字
                [],     # 列表
                {},     # 字典
                "invalid_date",  # 无效日期字符串
            ]
            
            all_passed = True
            
            for i, invalid_input in enumerate(invalid_inputs):
                try:
                    result = DatabaseCompatibility.format_datetime(invalid_input)
                    # 应该返回字符串表示，不应该抛出异常
                    if isinstance(result, str):
                        self.log_test(f"错误处理_{i+1}", True, f"输入: {type(invalid_input).__name__}, 输出: {result}")
                    else:
                        self.log_test(f"错误处理_{i+1}", False, f"返回类型错误: {type(result)}")
                        all_passed = False
                except Exception as e:
                    self.log_test(f"错误处理_{i+1}", False, f"异常: {e}")
                    all_passed = False
            
            # 测试模板过滤器的错误处理
            with app.app_context():
                template_str = "{{ invalid_input|dt_format }}"
                template = app.jinja_env.from_string(template_str)
                
                for i, invalid_input in enumerate(invalid_inputs):
                    try:
                        result = template.render(invalid_input=invalid_input)
                        if isinstance(result, str) and len(result) > 0:
                            self.log_test(f"过滤器错误处理_{i+1}", True, f"输出: {result}")
                        else:
                            self.log_test(f"过滤器错误处理_{i+1}", False, f"输出为空或无效")
                            all_passed = False
                    except Exception as e:
                        self.log_test(f"过滤器错误处理_{i+1}", False, f"异常: {e}")
                        all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.log_test("错误处理", False, f"异常: {e}")
            return False

    def test_database_environments(self):
        """测试数据库环境兼容性"""
        print("\n🧪 测试数据库环境兼容性...")

        try:
            # 检查当前数据库环境
            current_env = "PostgreSQL" if HAS_POSTGRESQL else "SQLite"
            self.log_test("数据库环境检测", True, f"当前环境: {current_env}")

            # 测试数据库连接
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
                conn.close()

                if result and result[0] == 1:
                    self.log_test("数据库连接", True, f"{current_env}连接正常")
                else:
                    self.log_test("数据库连接", False, "连接测试失败")
                    return False
            except Exception as e:
                self.log_test("数据库连接", False, f"连接异常: {e}")
                return False

            # 测试DatabaseCompatibility在当前环境下的工作
            use_postgresql = HAS_POSTGRESQL

            # 测试boolean条件
            bool_condition = DatabaseCompatibility.get_boolean_condition('is_admin', True, use_postgresql)
            expected_bool = "is_admin = TRUE" if use_postgresql else "is_admin = 1"

            if bool_condition == expected_bool:
                self.log_test("Boolean条件兼容性", True, f"输出: {bool_condition}")
            else:
                self.log_test("Boolean条件兼容性", False, f"期望: {expected_bool}, 实际: {bool_condition}")
                return False

            # 测试占位符
            placeholder = DatabaseCompatibility.get_placeholder(use_postgresql)
            expected_placeholder = "%s" if use_postgresql else "?"

            if placeholder == expected_placeholder:
                self.log_test("占位符兼容性", True, f"输出: {placeholder}")
            else:
                self.log_test("占位符兼容性", False, f"期望: {expected_placeholder}, 实际: {placeholder}")
                return False

            # 测试时间戳函数
            timestamp = DatabaseCompatibility.get_current_timestamp(use_postgresql)
            expected_timestamp = "CURRENT_TIMESTAMP" if use_postgresql else "datetime('now')"

            if timestamp == expected_timestamp:
                self.log_test("时间戳函数兼容性", True, f"输出: {timestamp}")
            else:
                self.log_test("时间戳函数兼容性", False, f"期望: {expected_timestamp}, 实际: {timestamp}")
                return False

            return True

        except Exception as e:
            self.log_test("数据库环境兼容性", False, f"异常: {e}")
            return False

    def test_web_routes(self):
        """测试Web路由功能"""
        print("\n🧪 测试Web路由功能...")

        with app.test_client() as client:
            try:
                # 测试健康检查
                response = client.get('/health')
                if response.status_code == 200:
                    self.log_test("健康检查路由", True, f"状态码: {response.status_code}")
                else:
                    self.log_test("健康检查路由", False, f"状态码: {response.status_code}")
                    return False

                # 测试主页
                response = client.get('/')
                if response.status_code in [200, 302]:  # 可能重定向到登录页
                    self.log_test("主页路由", True, f"状态码: {response.status_code}")
                else:
                    self.log_test("主页路由", False, f"状态码: {response.status_code}")
                    return False

                # 测试文档列表
                response = client.get('/documents')
                if response.status_code in [200, 302]:  # 可能需要登录
                    self.log_test("文档列表路由", True, f"状态码: {response.status_code}")
                else:
                    self.log_test("文档列表路由", False, f"状态码: {response.status_code}")
                    return False

                # 测试搜索功能
                response = client.get('/search?q=ROS')
                if response.status_code == 200:
                    self.log_test("搜索路由", True, f"状态码: {response.status_code}")
                else:
                    self.log_test("搜索路由", False, f"状态码: {response.status_code}")
                    return False

                return True

            except Exception as e:
                self.log_test("Web路由功能", False, f"异常: {e}")
                return False

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("🚀 ROS2 Wiki datetime修复完整验证测试")
        print("=" * 60)

        # 记录测试开始时间
        self.start_time = time.time()

        # 运行所有测试
        tests = [
            self.test_database_compatibility_class,
            self.test_template_filter,
            self.test_template_syntax,
            self.test_template_rendering,
            self.test_performance,
            self.test_error_handling,
            self.test_database_environments,
            self.test_web_routes
        ]

        passed_tests = 0
        total_tests = len(tests)

        for test in tests:
            try:
                if test():
                    passed_tests += 1
            except Exception as e:
                print(f"💥 测试 {test.__name__} 发生异常: {e}")
                traceback.print_exc()

        # 计算总体结果
        total_time = time.time() - self.start_time
        success_rate = (passed_tests / total_tests) * 100

        print(f"\n📊 测试结果汇总:")
        print(f"   通过测试: {passed_tests}/{total_tests}")
        print(f"   成功率: {success_rate:.1f}%")
        print(f"   总耗时: {total_time:.2f}秒")

        if self.performance_data:
            print(f"\n⚡ 性能数据:")
            print(f"   DatabaseCompatibility平均耗时: {self.performance_data['avg_db_compat']:.3f}ms")
            print(f"   模板过滤器平均耗时: {self.performance_data['avg_filter']:.3f}ms")

        return passed_tests == total_tests, self.test_results, self.performance_data

def main():
    """主函数"""
    try:
        # 创建测试套件
        test_suite = DatetimeFixTestSuite()

        # 运行所有测试
        all_passed, test_results, performance_data = test_suite.run_all_tests()

        if all_passed:
            print("\n🎉 所有测试通过！datetime修复验证成功。")
            return True, test_results, performance_data
        else:
            print("\n❌ 部分测试失败，需要进一步检查。")
            return False, test_results, performance_data

    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {e}")
        traceback.print_exc()
        return False, {}, {}

if __name__ == '__main__':
    success, results, perf_data = main()
    sys.exit(0 if success else 1)
