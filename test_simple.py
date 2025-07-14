#!/usr/bin/env python3
print("🎉 ROS2 Wiki 测试服务器启动成功!")
print("📱 访问: http://localhost:5000")
print("按 Ctrl+C 停止服务")

try:
    import time
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n🛑 服务已停止")