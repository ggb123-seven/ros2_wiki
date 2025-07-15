#!/usr/bin/env python3
"""
Claude Code 监视器启动脚本
一键启动监视和仪表板
"""

import os
import sys
import time
import subprocess
import threading
from pathlib import Path

def start_monitor():
    """启动文件监视器"""
    print("🔍 启动文件监视器...")
    try:
        subprocess.run([sys.executable, "claude_monitor.py"], check=True)
    except KeyboardInterrupt:
        print("📁 文件监视器已停止")
    except Exception as e:
        print(f"❌ 文件监视器错误: {e}")

def start_dashboard():
    """启动Web仪表板"""
    print("🌐 启动Web仪表板...")
    try:
        subprocess.run([sys.executable, "claude_dashboard.py"], check=True)
    except KeyboardInterrupt:
        print("🌐 Web仪表板已停止")
    except Exception as e:
        print(f"❌ Web仪表板错误: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("🤖 Claude Code 监视系统")
    print("=" * 60)
    
    # 检查必要文件
    required_files = ["claude_monitor.py", "claude_dashboard.py"]
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ 缺少文件: {file}")
            return
    
    print("✅ 所有必要文件已就绪")
    print("\n选择启动模式:")
    print("1. 仅文件监视器")
    print("2. 仅Web仪表板")
    print("3. 同时启动两者 (推荐)")
    print("4. 快速状态检查")
    
    try:
        choice = input("\n请选择 (1-4): ").strip()
        
        if choice == "1":
            start_monitor()
        elif choice == "2":
            start_dashboard()
        elif choice == "3":
            print("\n🚀 同时启动监视器和仪表板...")
            print("📝 提示: 使用 Ctrl+C 停止所有服务")
            
            # 在后台启动监视器
            monitor_thread = threading.Thread(target=start_monitor, daemon=True)
            monitor_thread.start()
            
            # 等待一下让监视器启动
            time.sleep(2)
            
            # 启动仪表板 (前台运行)
            start_dashboard()
            
        elif choice == "4":
            print("\n📊 快速状态检查:")
            
            # 检查项目文件
            important_files = {
                "wsgi.py": "WSGI入口文件",
                "app.py": "主应用文件", 
                "requirements.txt": "依赖文件",
                "render.yaml": "Render配置"
            }
            
            for file, desc in important_files.items():
                if os.path.exists(file):
                    size = os.path.getsize(file)
                    print(f"  ✅ {file} ({desc}) - {size} bytes")
                else:
                    print(f"  ❌ {file} ({desc}) - 不存在")
            
            # 检查最近的日志
            if os.path.exists("claude_monitor.log"):
                print(f"\n📋 监视日志存在")
                with open("claude_monitor.log", "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    print(f"  📝 共 {len(lines)} 条日志记录")
                    if lines:
                        print(f"  🕐 最后记录: {lines[-1].strip()}")
            else:
                print("\n📋 暂无监视日志")
                
        else:
            print("❌ 无效选择")
            
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作")
    except Exception as e:
        print(f"\n❌ 启动错误: {e}")

if __name__ == "__main__":
    main()
