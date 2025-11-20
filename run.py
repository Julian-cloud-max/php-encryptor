#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHP文件加密工具启动脚本
简化用户启动流程
"""

import sys
import os
import subprocess

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 错误：需要Python 3.8或更高版本")
        print(f"   当前版本：{sys.version}")
        return False
    return True

def install_dependencies():
    """安装依赖包"""
    print("📦 正在检查依赖包...")

    try:
        import PyQt6
        import cryptography
        print("✅ 依赖包已安装")
        return True
    except ImportError:
        print("⚠️  缺少依赖包，正在安装...")

        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ])
            print("✅ 依赖包安装完成")
            return True
        except subprocess.CalledProcessError:
            print("❌ 依赖包安装失败，请手动运行：pip install -r requirements.txt")
            return False

def main():
    """主函数"""
    print("🔐 PHP文件加密工具启动中...")
    print("=" * 40)

    # 检查Python版本
    if not check_python_version():
        input("按回车键退出...")
        return

    # 安装依赖
    if not install_dependencies():
        input("按回车键退出...")
        return

    # 启动主程序
    print("🚀 启动主程序...")
    try:
        from gui.main_window import MainWindow
        from PyQt6.QtWidgets import QApplication

        app = QApplication(sys.argv)
        app.setApplicationName("PHP文件加密工具")
        app.setApplicationVersion("1.0.0")

        window = MainWindow()
        window.show()

        print("✅ 程序启动成功！")
        print("=" * 40)

        sys.exit(app.exec())

    except ImportError as e:
        print(f"❌ 导入错误：{e}")
        print("请确保已正确安装所有依赖包")
        input("按回车键退出...")
    except Exception as e:
        print(f"❌ 启动失败：{e}")
        input("按回车键退出...")

if __name__ == '__main__':
    main()