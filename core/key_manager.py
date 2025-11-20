#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
密钥管理模块
负责生成、存储和管理加密密钥
"""

import os
import json
import secrets
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64

class KeyManager:
    """密钥管理器"""

    def __init__(self):
        self.backend = default_backend()

    def generate_master_key(self, password: str = None) -> bytes:
        """
        生成主密钥

        Args:
            password: 可选密码，如果提供则派生密钥，否则生成随机密钥

        Returns:
            bytes: 32字节的主密钥
        """
        if password:
            # 基于密码派生密钥
            salt = secrets.token_bytes(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=self.backend
            )
            key = kdf.derive(password.encode())
            return key, salt
        else:
            # 生成随机密钥
            return secrets.token_bytes(32)

    def generate_file_key(self, master_key: bytes, file_path: str) -> bytes:
        """
        基于主密钥和文件路径生成文件专属密钥

        Args:
            master_key: 主密钥
            file_path: 文件路径

        Returns:
            bytes: 文件专属密钥
        """
        # 使用主密钥和文件路径的哈希值派生文件密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=os.path.basename(file_path).encode(),
            iterations=1000,
            backend=self.backend
        )
        return kdf.derive(master_key)

    def save_key_info(self, key_data: dict, output_dir: str) -> str:
        """
        保存密钥信息

        Args:
            key_data: 密钥数据字典
            output_dir: 输出目录

        Returns:
            str: 密钥文件路径
        """
        # 生成密钥文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        key_file = os.path.join(output_dir, f"php_encryptor_keys_{timestamp}.json")

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 保存密钥信息
        with open(key_file, 'w', encoding='utf-8') as f:
            json.dump(key_data, f, indent=2, ensure_ascii=False)

        return key_file

    def load_key_info(self, key_file: str) -> dict:
        """
        加载密钥信息

        Args:
            key_file: 密钥文件路径

        Returns:
            dict: 密钥数据字典
        """
        with open(key_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def generate_key_package(self, output_dir: str) -> dict:
        """
        生成完整的密钥包

        Args:
            output_dir: 输出目录

        Returns:
            dict: 密钥包数据
        """
        # 生成主密钥
        master_key = self.generate_master_key()

        # 生成随机盐值
        salt = secrets.token_bytes(16)

        # 生成时间戳
        timestamp = datetime.now().isoformat()

        # 构建密钥包
        key_package = {
            'master_key': base64.b64encode(master_key).decode(),
            'salt': base64.b64encode(salt).decode(),
            'created_at': timestamp,
            'algorithm': 'AES-256-GCM',
            'key_derivation': 'PBKDF2-SHA256',
            'iterations': 100000
        }

        # 保存密钥包
        key_file = self.save_key_info(key_package, output_dir)

        return {
            'master_key': master_key,
            'salt': salt,
            'key_file': key_file,
            'package_data': key_package
        }