#!/usr/bin/env python3
"""
云端启动脚本 - 确保管理员账户存在
"""

import os
import sys

# 设置环境变量以跳过密码验证
os.environ['SKIP_PASSWORD_VALIDATION'] = 'true'
os.environ['MIN_PASSWORD_LENGTH'] = '6'

# 导入并运行管理员创建脚本
try:
    from emergency_admin_create import create_admin_account
    print("[START] 云端启动：创建管理员账户...")
    create_admin_account()
except Exception as e:
    print(f"[WARNING] 管理员创建失败: {e}")

# 继续正常启动
print("[OK] 启动脚本完成")
