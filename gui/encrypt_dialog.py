#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加密对话框
处理文件加密过程
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QFileDialog, QMessageBox
)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from core.key_manager import KeyManager
from core.encryptor import PHPEncryptor

class EncryptThread(QThread):
    """加密工作线程"""
    progress_updated = pyqtSignal(int, int, str)  # 当前进度, 总数, 当前文件
    file_completed = pyqtSignal(str, bool, str)   # 文件路径, 成功标志, 消息
    encryption_finished = pyqtSignal(bool, int)   # 是否成功, 成功数量
    log_message = pyqtSignal(str)                 # 日志消息

    def __init__(self, files, output_dir, options):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.options = options
        self.should_stop = False

    def run(self):
        """运行加密任务"""
        success_count = 0
        total_files = len(self.files)

        try:
            # 生成密钥
            key_manager = KeyManager()
            key_package = key_manager.generate_key_package(self.output_dir)
            master_key = key_package['master_key']
            salt = key_package['salt']

            self.log_message.emit(f"🔑 生成密钥完成: {os.path.basename(key_package['key_file'])}")

            # 创建加密器
            encryptor = PHPEncryptor(master_key, salt)

            # 加密每个文件
            for i, file_path in enumerate(self.files):
                if self.should_stop:
                    break

                self.progress_updated.emit(i + 1, total_files, os.path.basename(file_path))

                # 生成输出文件路径
                file_name = os.path.basename(file_path)
                if file_name.endswith('.php'):
                    output_name = file_name.replace('.php', '.encrypted.php')
                else:
                    output_name = file_name + '.encrypted.php'
                output_path = os.path.join(self.output_dir, output_name)

                # 确保输出目录存在
                os.makedirs(self.output_dir, exist_ok=True)

                # 加密文件
                result = encryptor.encrypt_file(
                    file_path,
                    output_path,
                    obfuscate_vars=self.options.get('obfuscate_vars', True)
                )

                if result.get('success', False):
                    success_count += 1
                    self.file_completed.emit(file_path, True, f"加密成功 (压缩率: {result.get('compression_ratio', 0):.2%})")
                else:
                    self.file_completed.emit(file_path, False, f"加密失败: {result.get('error', '未知错误')}")

            self.encryption_finished.emit(not self.should_stop, success_count)

        except Exception as e:
            self.log_message.emit(f"❌ 加密过程出错: {str(e)}")
            self.encryption_finished.emit(False, success_count)

    def stop(self):
        """停止加密"""
        self.should_stop = True

class EncryptDialog(QDialog):
    """加密对话框"""

    def __init__(self, files, parent=None):
        super().__init__(parent)
        self.files = files
        self.setParent(parent)
        self.setModal(True)
        self.setWindowTitle("加密文件")
        self.setFixedSize(600, 500)

        self.encrypt_thread = None

        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel(f"🔒 正在加密 {len(self.files)} 个PHP文件")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)

        # 输出目录选择
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出目录:"))

        self.output_label = QLabel("未选择")
        output_layout.addWidget(self.output_label)

        self.browse_btn = QPushButton("浏览")
        self.browse_btn.clicked.connect(self.browse_output_directory)
        output_layout.addWidget(self.browse_btn)

        layout.addLayout(output_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, len(self.files))
        layout.addWidget(self.progress_bar)

        # 当前文件
        self.current_file_label = QLabel("准备开始...")
        layout.addWidget(self.current_file_label)

        # 结果列表
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(200)
        layout.addWidget(self.results_text)

        # 按钮
        button_layout = QHBoxLayout()

        self.start_btn = QPushButton("开始加密")
        self.start_btn.clicked.connect(self.start_encryption)
        button_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_encryption)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)

        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def browse_output_directory(self):
        """浏览输出目录"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        if directory:
            self.output_label.setText(directory)

    def start_encryption(self):
        """开始加密"""
        if self.output_label.text() == "未选择":
            QMessageBox.warning(self, "警告", "请先选择输出目录")
            return

        # 获取加密选项
        options = {
            'obfuscate_vars': self.parent().obfuscate_vars_cb.isChecked(),
            'obfuscate_functions': self.parent().obfuscate_functions_cb.isChecked(),
            'strength': self.parent().strength_spin.value()
        }

        # 创建并启动加密线程
        self.encrypt_thread = EncryptThread(
            self.files,
            self.output_label.text(),
            options
        )

        # 连接信号
        self.encrypt_thread.progress_updated.connect(self.update_progress)
        self.encrypt_thread.file_completed.connect(self.on_file_completed)
        self.encrypt_thread.encryption_finished.connect(self.on_encryption_finished)
        self.encrypt_thread.log_message.connect(self.add_log_message)

        # 更新UI状态
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.browse_btn.setEnabled(False)

        # 启动线程
        self.encrypt_thread.start()

    def stop_encryption(self):
        """停止加密"""
        if self.encrypt_thread:
            self.encrypt_thread.stop()
            self.add_log_message("⏹️ 正在停止加密...")

    def update_progress(self, current, total, current_file):
        """更新进度"""
        self.progress_bar.setValue(current)
        self.current_file_label.setText(f"正在处理: {current_file} ({current}/{total})")

    def on_file_completed(self, file_path, success, message):
        """文件完成处理"""
        file_name = os.path.basename(file_path)
        status = "✅" if success else "❌"
        self.results_text.append(f"{status} {file_name}: {message}")

    def on_encryption_finished(self, success, success_count):
        """加密完成处理"""
        self.progress_bar.setValue(len(self.files))

        if success:
            self.add_log_message(f"🎉 加密完成! 成功处理 {success_count}/{len(self.files)} 个文件")
            QMessageBox.information(
                self,
                "加密完成",
                f"成功加密 {success_count}/{len(self.files)} 个文件"
            )
            self.accept()  # 关闭对话框并返回 QDialog.Accepted
        else:
            self.add_log_message("⚠️ 加密被中断或失败")
            QMessageBox.warning(
                self,
                "加密中断",
                f"加密被中断，成功处理 {success_count}/{len(self.files)} 个文件"
            )

        # 恢复UI状态
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.browse_btn.setEnabled(True)

    def add_log_message(self, message):
        """添加日志消息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.results_text.append(f"[{timestamp}] {message}")

    def closeEvent(self, event):
        """关闭事件"""
        if self.encrypt_thread and self.encrypt_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "确认",
                "加密正在进行中，确定要关闭吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.encrypt_thread.stop()
                self.encrypt_thread.wait(3000)  # 等待3秒
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()