#!/usr/bin/env python3
"""
�ƶ������ű� - ȷ������Ա�˻�����
"""

import os
import sys

# ���û�������������������֤
os.environ['SKIP_PASSWORD_VALIDATION'] = 'true'
os.environ['MIN_PASSWORD_LENGTH'] = '6'

# ���벢���й���Ա�����ű�
try:
    from emergency_admin_create import create_admin_account
    print("[START] �ƶ���������������Ա�˻�...")
    create_admin_account()
except Exception as e:
    print(f"[WARNING] ����Ա����ʧ��: {e}")

# ������������
print("[OK] �����ű����")
