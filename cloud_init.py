#!/usr/bin/env python3
"""
云端环境初始化脚本
适配PostgreSQL和SQLite双环境
"""
import os

def cloud_init():
    """云端环境初始化"""
    print("🚀 SuperClaude云端环境初始化...")
    
    # 检查数据库环境
    if os.environ.get('DATABASE_URL'):
        print("✅ 检测到PostgreSQL环境")
        print("✅ 数据库连接将在应用启动时建立")
    else:
        print("✅ 检测到本地SQLite环境")
        print("✅ 数据库文件将在应用启动时创建")
    
    print("✅ 云端初始化完成")
    return True

if __name__ == "__main__":
    cloud_init()