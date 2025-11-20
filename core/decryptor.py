#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHP文件解密引擎
负责PHP文件的解密处理
"""

import os
import re
import base64
import json
from typing import Dict
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import hmac
from core.key_manager import KeyManager

class PHPDecryptor:
    """PHP文件解密器"""

    def __init__(self, master_key: bytes, salt: bytes):
        """
        初始化解密器

        Args:
            master_key: 主密钥
            salt: 盐值
        """
        self.master_key = master_key
        self.salt = salt
        self.backend = default_backend()
        self.key_manager = KeyManager()

    def decrypt_file(self, input_path: str, output_path: str,
                    original_file_path: str = None) -> Dict:
        """
        解密PHP文件

        Args:
            input_path: 加密文件路径
            output_path: 输出文件路径
            original_file_path: 原始文件路径（用于生成文件密钥）

        Returns:
            Dict: 解密结果信息
        """
        try:
            # 读取加密文件
            with open(input_path, 'r', encoding='utf-8') as f:
                encrypted_code = f.read()

            # 提取加密信息
            decrypt_info = self._extract_decrypt_info(encrypted_code)

            # 如果没有提供原始文件路径，尝试从加密文件中提取
            if not original_file_path:
                original_file_path = input_path.replace('.encrypted.php', '.php')

            # 生成文件专属密钥
            file_key = self.key_manager.generate_file_key(
                self.master_key, original_file_path
            )

            # 解密数据
            decrypted_code = self._decrypt_data(
                decrypt_info, file_key
            )

            # 写入解密文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(decrypted_code)

            # 返回解密结果
            result = {
                'success': True,
                'input_path': input_path,
                'output_path': output_path,
                'original_file_path': original_file_path,
                'decrypted_size': len(decrypted_code),
                'chunks_count': len(decrypt_info['chunks'])
            }

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'input_path': input_path
            }

    def _extract_decrypt_info(self, encrypted_code: str) -> Dict:
        """
        从加密代码中提取解密信息

        Args:
            encrypted_code: 加密的PHP代码

        Returns:
            Dict: 解密信息
        """
        decrypt_info = {
            'file_key': None,
            'salt': None,
            'integrity_hash': None,
            'chunks': None
        }

        # 提取文件密钥
        key_match = re.search(r'private \$fileKey = \'([^\']+)\';', encrypted_code)
        if key_match:
            decrypt_info['file_key'] = key_match.group(1)

        # 提取盐值
        salt_match = re.search(r'private \$salt = \'([^\']+)\';', encrypted_code)
        if salt_match:
            decrypt_info['salt'] = salt_match.group(1)

        # 提取完整性哈希
        hash_match = re.search(r'private \$integrityHash = \'([^\']+)\';', encrypted_code)
        if hash_match:
            decrypt_info['integrity_hash'] = hash_match.group(1)

        # 提取加密块
        chunks_match = re.search(r'private \$chunks = \'([^\']+)\';', encrypted_code)
        if chunks_match:
            decrypt_info['chunks'] = chunks_match.group(1)

        return decrypt_info

    def _decrypt_data(self, decrypt_info: Dict, file_key: bytes) -> str:
        """
        解密数据

        Args:
            decrypt_info: 解密信息
            file_key: 文件密钥

        Returns:
            str: 解密后的PHP代码
        """
        try:
            # 解码加密块
            chunks_data = base64.b64decode(decrypt_info['chunks'])
            chunks = json.loads(chunks_data)

            # 解密每个块
            decrypted_data = b''

            for chunk in chunks:
                nonce = base64.b64decode(chunk['nonce'])
                data = base64.b64decode(chunk['data'])
                tag = base64.b64decode(chunk['tag'])

                # AES-256-GCM解密
                cipher = Cipher(
                    algorithms.AES(file_key),
                    modes.GCM(nonce, tag),
                    backend=self.backend
                )
                decryptor = cipher.decryptor()

                decrypted_chunk = decryptor.update(data) + decryptor.finalize()
                decrypted_data += decrypted_chunk

            # 验证完整性
            if not self._verify_integrity(decrypted_data, decrypt_info, file_key):
                raise Exception("Integrity verification failed")

            # 直接返回解密数据（移除压缩）
            return decrypted_data.decode('utf-8')

        except Exception as e:
            raise Exception(f"Decryption failed: {str(e)}")

    def _verify_integrity(self, data: bytes, decrypt_info: Dict, file_key: bytes) -> bool:
        """
        验证数据完整性

        Args:
            data: 解密后的数据
            decrypt_info: 解密信息
            file_key: 文件密钥

        Returns:
            bool: 完整性验证结果
        """
        try:
            # 解码加密块
            chunks_data = base64.b64decode(decrypt_info['chunks'])
            chunks = json.loads(chunks_data)

            # 构建签名数据
            chunks_data_str = ''.join([
                chunk['nonce'] + chunk['data'] + chunk['tag']
                for chunk in chunks
            ])

            # 计算HMAC
            from cryptography.hazmat.primitives.hmac import HMAC
            h = HMAC(file_key, hashes.SHA256(), backend=self.backend)
            h.update(chunks_data_str.encode())
            computed_hash = h.finalize()

            # 比较哈希值
            expected_hash = base64.b64decode(decrypt_info['integrity_hash'])

            # 使用安全的比较函数
            return hmac.compare_digest(computed_hash, expected_hash)

        except Exception:
            return False

    def validate_file(self, file_path: str) -> bool:
        """
        验证文件是否为有效的加密文件

        Args:
            file_path: 文件路径

        Returns:
            bool: 验证结果
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查是否包含解密器标识
            if 'class PHPDecryptor' not in content:
                return False

            # 检查必要的字段
            required_fields = [
                'private $fileKey',
                'private $salt',
                'private $integrityHash',
                'private $chunks'
            ]

            for field in required_fields:
                if field not in content:
                    return False

            return True

        except Exception:
            return False