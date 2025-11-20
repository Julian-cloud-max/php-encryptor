#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解密对话框
处理文件解密过程
"""

import os
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QMessageBox, QFileDialog
)
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QFont
from core.key_manager import KeyManager
from core.decryptor import PHPDecryptor

class DecryptThread(QThread):
    """解密工作线程"""
    progress_updated = pyqtSignal(int, int, str)  # 当前进度, 总数, 当前文件
    file_completed = pyqtSignal(str, bool, str)   # 文件路径, 成功标志, 消息
    decryption_finished = pyqtSignal(bool, int)   # 是否成功, 成功数量
    log_message = pyqtSignal(str)                 # 日志消息

    def __init__(self, files, key_file, output_dir):
        super().__init__()
        self.files = files
        self.key_file = key_file
        self.output_dir = output_dir
        self.should_stop = False

    def run(self):
        """运行解密任务"""
        success_count = 0
        total_files = len(self.files)

        try:
            # 加载密钥
            key_manager = KeyManager()
            key_info = key_manager.load_key_info(self.key_file)
            master_key = key_manager.load_key_info(self.key_file).get('master_key', '')
            salt = key_manager.load_key_info(self.key_file).get('salt', '')

            if not master_key or not salt:
                raise Exception("无效的密钥文件")

            # 解码密钥和盐值
            import base64
            master_key = base64.b64decode(master_key)
            salt = base64.b64decode(salt)

            self.log_message.emit(f"🔑 密钥加载完成: {os.path.basename(self.key_file)}")

            # 创建解密器
            decryptor = PHPDecryptor(master_key, salt)

            # 解密每个文件
            for i, file_path in enumerate(self.files):
                if self.should_stop:
                    break

                self.progress_updated.emit(i + 1, total_files, os.path.basename(file_path))

                # 验证文件
                if not decryptor.validate_file(file_path):
                    self.file_completed.emit(file_path, False, "不是有效的加密文件")
                    continue

                # 生成输出文件路径（避免覆盖原文件）
                file_name = os.path.basename(file_path)
                if file_name.endswith('.encrypted.php'):
                    # 生成带时间戳的文件名，避免覆盖原文件
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    original_name = file_name[:-14]  # 移除 .encrypted.php 后缀
                    file_name = f"{original_name}.decrypted_{timestamp}.php"
                else:
                    file_name = file_name + '.decrypted.php'

                output_path = os.path.join(self.output_dir, file_name)

                # 确保输出目录存在
                os.makedirs(self.output_dir, exist_ok=True)

                # 解密文件
                result = decryptor.decrypt_file(file_path, output_path)

                if result.get('success', False):
                    success_count += 1
                    self.file_completed.emit(file_path, True, f"解密成功")
                else:
                    self.file_completed.emit(file_path, False, f"解密失败: {result.get('error', '未知错误')}")

            self.decryption_finished.emit(not self.should_stop, success_count)

        except Exception as e:
            self.log_message.emit(f"❌ 解密过程出错: {str(e)}")
            self.decryption_finished.emit(False, success_count)

    def stop(self):
        """停止解密"""
        self.should_stop = True

class DecryptDialog(QDialog):
    """解密对话框"""

    def __init__(self, files, key_file, parent=None):
        super().__init__(parent)
        self.files = files
        self.key_file = key_file
        self.setParent(parent)
        self.setModal(True)
        self.setWindowTitle("解密文件")
        self.setFixedSize(600, 500)

        self.decrypt_thread = None

        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel(f"🔓 正在解密 {len(self.files)} 个加密文件")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)

        # 密钥文件信息
        key_info_layout = QHBoxLayout()
        key_info_layout.addWidget(QLabel("密钥文件:"))
        key_label = QLabel(os.path.basename(self.key_file))
        key_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        key_info_layout.addWidget(key_label)
        key_info_layout.addStretch()
        layout.addLayout(key_info_layout)

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

        self.start_btn = QPushButton("开始解密")
        self.start_btn.clicked.connect(self.start_decryption)
        button_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_decryption)
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

    def start_decryption(self):
        """开始解密"""
        if self.output_label.text() == "未选择":
            QMessageBox.warning(self, "警告", "请先选择输出目录")
            return

        # 验证密钥文件
        if not os.path.exists(self.key_file):
            QMessageBox.error(self, "错误", "密钥文件不存在")
            return

        try:
            # 尝试加载密钥文件以验证格式
            key_manager = KeyManager()
            key_info = key_manager.load_key_info(self.key_file)

            required_fields = ['master_key', 'salt', 'created_at']
            for field in required_fields:
                if field not in key_info:
                    raise Exception(f"密钥文件格式错误，缺少字段: {field}")

        except Exception as e:
            QMessageBox.error(self, "错误", f"密钥文件无效: {str(e)}")
            return

        # 创建并启动解密线程
        self.decrypt_thread = DecryptThread(
            self.files,
            self.key_file,
            self.output_label.text()
        )

        # 连接信号
        self.decrypt_thread.progress_updated.connect(self.update_progress)
        self.decrypt_thread.file_completed.connect(self.on_file_completed)
        self.decrypt_thread.decryption_finished.connect(self.on_decryption_finished)
        self.decrypt_thread.log_message.connect(self.add_log_message)

        # 更新UI状态
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.browse_btn.setEnabled(False)

        # 启动线程
        self.decrypt_thread.start()

    def stop_decryption(self):
        """停止解密"""
        if self.decrypt_thread:
            self.decrypt_thread.stop()
            self.add_log_message("⏹️ 正在停止解密...")

    def update_progress(self, current, total, current_file):
        """更新进度"""
        self.progress_bar.setValue(current)
        self.current_file_label.setText(f"正在处理: {current_file} ({current}/{total})")

    def on_file_completed(self, file_path, success, message):
        """文件完成处理"""
        file_name = os.path.basename(file_path)
        status = "✅" if success else "❌"
        self.results_text.append(f"{status} {file_name}: {message}")

    def on_decryption_finished(self, success, success_count):
        """解密完成处理"""
        self.progress_bar.setValue(len(self.files))

        if success:
            self.add_log_message(f"🎉 解密完成! 成功处理 {success_count}/{len(self.files)} 个文件")
            QMessageBox.information(
                self,
                "解密完成",
                f"成功解密 {success_count}/{len(self.files)} 个文件"
            )
            self.accept()  # 关闭对话框并返回 QDialog.Accepted
        else:
            self.add_log_message("⚠️ 解密被中断或失败")
            QMessageBox.warning(
                self,
                "解密中断",
                f"解密被中断，成功处理 {success_count}/{len(self.files)} 个文件"
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
        if self.decrypt_thread and self.decrypt_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "确认",
                "解密正在进行中，确定要关闭吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.decrypt_thread.stop()
                self.decrypt_thread.wait(3000)  # 等待3秒
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()