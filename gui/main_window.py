#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主界面窗口
现代化Material Design风格的GUI界面
"""

import os
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QTextEdit, QTabWidget,
    QFrame, QSplitter, QGroupBox, QCheckBox, QSpinBox,
    QFileDialog, QMessageBox, QStatusBar, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor
from gui.encrypt_dialog import EncryptDialog
from gui.decrypt_dialog import DecryptDialog

class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PHP文件加密工具 v1.0")
        self.setGeometry(100, 100, 1200, 800)

        # 设置应用图标
        # self.setWindowIcon(QIcon("assets/icons/app_icon.png"))

        # 初始化UI
        self.init_ui()

        # 加载样式
        self.load_styles()

        # 初始化组件
        self.init_components()

    def init_ui(self):
        """初始化用户界面"""
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 标题区域
        self.create_header_section(main_layout)

        # 主要操作区域
        self.create_main_action_section(main_layout)

        # 文件列表区域
        self.create_file_list_section(main_layout)

        # 进度和日志区域
        self.create_progress_section(main_layout)

        # 创建状态栏
        self.create_status_bar()

    def create_header_section(self, parent_layout):
        """创建标题区域"""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_frame.setMaximumHeight(100)

        header_layout = QHBoxLayout(header_frame)

        # 应用标题
        title_label = QLabel("🔐 PHP文件加密工具")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1976D2; margin: 10px;")

        # 版本信息
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("color: #666; font-size: 12px;")

        # 标题布局
        title_layout = QVBoxLayout()
        title_layout.addWidget(title_label)
        title_layout.addWidget(version_label)
        title_layout.addStretch()

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        parent_layout.addWidget(header_frame)

    def create_main_action_section(self, parent_layout):
        """创建主要操作区域"""
        actions_frame = QFrame()
        actions_frame.setFrameStyle(QFrame.Shape.StyledPanel)

        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setSpacing(30)

        # 加密区域
        encrypt_group = self.create_encrypt_group()
        actions_layout.addWidget(encrypt_group)

        # 解密区域
        decrypt_group = self.create_decrypt_group()
        actions_layout.addWidget(decrypt_group)

        # 配置区域
        config_group = self.create_config_group()
        actions_layout.addWidget(config_group)

        parent_layout.addWidget(actions_frame)

    def create_encrypt_group(self):
        """创建加密操作组"""
        group = QGroupBox("🔒 加密文件")
        group.setMinimumWidth(300)

        layout = QVBoxLayout(group)

        # 添加文件按钮
        self.add_encrypt_btn = QPushButton("📁 添加PHP文件")
        self.add_encrypt_btn.clicked.connect(self.add_files_to_encrypt)

        # 添加文件夹按钮
        self.add_encrypt_dir_btn = QPushButton("📂 添加文件夹")
        self.add_encrypt_dir_btn.clicked.connect(self.add_directory_to_encrypt)

        # 开始加密按钮
        self.start_encrypt_btn = QPushButton("🚀 开始加密")
        self.start_encrypt_btn.clicked.connect(self.start_encryption)
        self.start_encrypt_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        layout.addWidget(self.add_encrypt_btn)
        layout.addWidget(self.add_encrypt_dir_btn)
        layout.addWidget(self.start_encrypt_btn)

        return group

    def create_decrypt_group(self):
        """创建解密操作组"""
        group = QGroupBox("🔓 解密文件")
        group.setMinimumWidth(300)

        layout = QVBoxLayout(group)

        # 添加文件按钮
        self.add_decrypt_btn = QPushButton("📁 添加加密文件")
        self.add_decrypt_btn.clicked.connect(self.add_files_to_decrypt)

        # 选择密钥文件按钮
        self.select_key_btn = QPushButton("🔑 选择密钥文件")
        self.select_key_btn.clicked.connect(self.select_key_file)

        # 开始解密按钮
        self.start_decrypt_btn = QPushButton("🚀 开始解密")
        self.start_decrypt_btn.clicked.connect(self.start_decryption)
        self.start_decrypt_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

        layout.addWidget(self.add_decrypt_btn)
        layout.addWidget(self.select_key_btn)
        layout.addWidget(self.start_decrypt_btn)

        return group

    def create_config_group(self):
        """创建配置组"""
        group = QGroupBox("⚙️ 加密配置")
        group.setMinimumWidth(250)

        layout = QVBoxLayout(group)

        # 混淆选项
        self.obfuscate_vars_cb = QCheckBox("混淆变量名")
        self.obfuscate_vars_cb.setChecked(True)

        
        self.obfuscate_functions_cb = QCheckBox("混淆函数名")
        self.obfuscate_functions_cb.setChecked(False)

        # 加密强度
        strength_layout = QHBoxLayout()
        strength_layout.addWidget(QLabel("加密强度:"))

        self.strength_spin = QSpinBox()
        self.strength_spin.setRange(1, 5)
        self.strength_spin.setValue(3)
        self.strength_spin.setSuffix(" 级")

        strength_layout.addWidget(self.strength_spin)

        layout.addWidget(self.obfuscate_vars_cb)
        layout.addWidget(self.obfuscate_functions_cb)
        layout.addLayout(strength_layout)

        return group

    def create_file_list_section(self, parent_layout):
        """创建文件列表区域"""
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 加密文件列表
        self.encrypt_list = QTextEdit()
        self.encrypt_list.setPlaceholderText("等待添加要加密的PHP文件...")
        self.encrypt_list.setMaximumWidth(400)

        # 解密文件列表
        self.decrypt_list = QTextEdit()
        self.decrypt_list.setPlaceholderText("等待添加要解密的文件...")
        self.decrypt_list.setMaximumWidth(400)

        # 添加到分割器
        splitter.addWidget(self.create_file_list_widget("待加密文件", self.encrypt_list))
        splitter.addWidget(self.create_file_list_widget("待解密文件", self.decrypt_list))

        parent_layout.addWidget(splitter)

    def create_file_list_widget(self, title, text_edit):
        """创建文件列表部件"""
        widget = QFrame()
        layout = QVBoxLayout(widget)

        # 标题
        label = QLabel(title)
        label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        label.setStyleSheet("color: #333; margin: 5px;")

        layout.addWidget(label)
        layout.addWidget(text_edit)

        return widget

    def create_progress_section(self, parent_layout):
        """创建进度和日志区域"""
        progress_frame = QFrame()
        progress_frame.setFrameStyle(QFrame.Shape.StyledPanel)

        progress_layout = QVBoxLayout(progress_frame)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        # 日志区域
        log_label = QLabel("📋 操作日志:")
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setPlaceholderText("操作日志将显示在这里...")

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(log_label)
        progress_layout.addWidget(self.log_text)

        parent_layout.addWidget(progress_frame)

    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # 状态信息
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)

        # 文件计数
        self.file_count_label = QLabel("文件: 0")
        self.status_bar.addPermanentWidget(self.file_count_label)

    def load_styles(self):
        """加载样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }

            QFrame[frameShape="4"] {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin: 5px;
            }

            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #333;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }

            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
                min-height: 20px;
            }

            QPushButton:hover {
                background-color: #e0e0e0;
            }

            QPushButton:pressed {
                background-color: #d0d0d0;
            }

            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }

            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                text-align: center;
                font-weight: bold;
            }

            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)

    def init_components(self):
        """初始化组件"""
        self.encrypt_files = []
        self.decrypt_files = []
        self.key_file = None

        # 设置拖拽支持
        self.setAcceptDrops(True)

    def add_files_to_encrypt(self):
        """添加文件到加密列表"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择PHP文件",
            "",
            "PHP文件 (*.php *.phtml);;所有文件 (*.*)"
        )

        if files:
            self.encrypt_files.extend(files)
            self.update_encrypt_list()
            self.log_message(f"添加了 {len(files)} 个文件到加密列表")

    def add_directory_to_encrypt(self):
        """添加目录到加密列表"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择包含PHP文件的目录"
        )

        if directory:
            # 这里可以递归查找PHP文件
            from ..utils.file_handler import FileHandler
            handler = FileHandler()
            php_files = handler.find_php_files(directory, recursive=True)

            self.encrypt_files.extend(php_files)
            self.update_encrypt_list()
            self.log_message(f"从目录 {directory} 添加了 {len(php_files)} 个PHP文件")

    def add_files_to_decrypt(self):
        """添加文件到解密列表"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择加密的PHP文件",
            "",
            "PHP文件 (*.php *.phtml);;所有文件 (*.*)"
        )

        if files:
            self.decrypt_files.extend(files)
            self.update_decrypt_list()
            self.log_message(f"添加了 {len(files)} 个文件到解密列表")

    def select_key_file(self):
        """选择密钥文件"""
        file, _ = QFileDialog.getOpenFileName(
            self,
            "选择密钥文件",
            "",
            "密钥文件 (*.json);;所有文件 (*.*)"
        )

        if file:
            self.key_file = file
            self.log_message(f"选择密钥文件: {file}")

    def start_encryption(self):
        """开始加密"""
        if not self.encrypt_files:
            QMessageBox.warning(self, "警告", "请先添加要加密的文件")
            return

        # 打开加密对话框
        dialog = EncryptDialog(self.encrypt_files, self)
        if dialog.exec() == 1:  # QDialog.Accepted
            self.log_message("加密完成")
            self.encrypt_files.clear()
            self.update_encrypt_list()

    def start_decryption(self):
        """开始解密"""
        if not self.decrypt_files:
            QMessageBox.warning(self, "警告", "请先添加要解密的文件")
            return

        if not self.key_file:
            QMessageBox.warning(self, "警告", "请先选择密钥文件")
            return

        # 打开解密对话框
        dialog = DecryptDialog(self.decrypt_files, self.key_file, self)
        if dialog.exec() == 1:  # QDialog.Accepted
            self.log_message("解密完成")
            self.decrypt_files.clear()
            self.update_decrypt_list()

    def update_encrypt_list(self):
        """更新加密文件列表"""
        self.encrypt_list.clear()
        for file in self.encrypt_files:
            self.encrypt_list.append(f"📄 {os.path.basename(file)}\n")
        self.update_file_count()

    def update_decrypt_list(self):
        """更新解密文件列表"""
        self.decrypt_list.clear()
        for file in self.decrypt_files:
            self.decrypt_list.append(f"📄 {os.path.basename(file)}\n")
        self.update_file_count()

    def update_file_count(self):
        """更新文件计数"""
        total_files = len(self.encrypt_files) + len(self.decrypt_files)
        self.file_count_label.setText(f"文件: {total_files}")

    def log_message(self, message):
        """添加日志消息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """拖拽放下事件"""
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        php_files = [f for f in files if f.lower().endswith(('.php', '.phtml'))]

        if php_files:
            self.encrypt_files.extend(php_files)
            self.update_encrypt_list()
            self.log_message(f"通过拖拽添加了 {len(php_files)} 个PHP文件")
        else:
            QMessageBox.information(self, "提示", "请拖拽PHP文件")