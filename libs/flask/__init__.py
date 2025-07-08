
class Flask:
    def __init__(self, name):
        self.name = name
        self.routes = {}
        self.config = {}
        
    def route(self, rule, **options):
        def decorator(f):
            self.routes[rule] = f
            return f
        return decorator
        
    def run(self, host="127.0.0.1", port=5000, debug=False):
        print(f"🚀 简化版Flask服务器启动")
        print(f"📱 访问: http://{host}:{port}")
        print("💡 这是一个简化版本，仅用于测试ngrok")
        print("按 Ctrl+C 停止服务")
        
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 服务已停止")

def render_template(template_name, **kwargs):
    return f"模板: {template_name}"

def request():
    pass

def jsonify(data):
    return str(data)

def redirect(url):
    return f"重定向到: {url}"

def url_for(endpoint, **values):
    return f"/{endpoint}"

def flash(message):
    print(f"消息: {message}")
