#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHP文件加密工具
主程序入口
"""

import sys
import os
import argparse
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from gui.main_window import MainWindow

def check_dependencies():
    """检查依赖包"""
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        return True
    except ImportError:
        print("❌ 缺少依赖包，请运行：pip install -r requirements.txt")
        return False

def main():
    """主函数"""
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)

    # 创建Qt应用
    app = QApplication(sys.argv)
    app.setApplicationName("PHP文件加密工具")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("East Technologies")

    # 设置应用样式
    app.setStyle('Fusion')

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 运行应用
    sys.exit(app.exec())

if __name__ == '__main__':
    main()