#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHP文件加密引擎
负责PHP文件的加密处理
"""

import os
import re
import secrets
import base64
from typing import Dict, List, Tuple
from datetime import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import hmac
from core.key_manager import KeyManager
from utils.php_parser import PHPParser
from utils.obfuscator import PHPObfuscator

class PHPEncryptor:
    """PHP文件加密器"""

    def __init__(self, master_key: bytes, salt: bytes):
        """
        初始化加密器

        Args:
            master_key: 主密钥
            salt: 盐值
        """
        self.master_key = master_key
        self.salt = salt
        self.backend = default_backend()
        self.key_manager = KeyManager()
        self.parser = PHPParser()
        self.obfuscator = PHPObfuscator()

    def encrypt_file(self, input_path: str, output_path: str,
                    obfuscate_vars: bool = True,
                    obfuscate_functions: bool = False,
                    obfuscate_classes: bool = False) -> Dict:
        """
        加密PHP文件

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            obfuscate_vars: 是否混淆变量
            obfuscate_functions: 是否混淆函数
            obfuscate_classes: 是否混淆类

        Returns:
            Dict: 加密结果信息
        """
        try:
            # 读取原始PHP代码
            with open(input_path, 'r', encoding='utf-8') as f:
                original_code = f.read()

            # 解析PHP代码
            parsed_code = self.parser.parse(original_code)

            # 混淆处理
            if obfuscate_vars or obfuscate_functions or obfuscate_classes:
                obfuscated_code = self.obfuscator.obfuscate(
                    parsed_code,
                    obfuscate_vars=obfuscate_vars,
                    obfuscate_functions=obfuscate_functions,
                    obfuscate_classes=obfuscate_classes
                )
            else:
                obfuscated_code = original_code

            # 生成文件专属密钥
            file_key = self.key_manager.generate_file_key(
                self.master_key, input_path
            )

            # 准备原始数据（移除压缩）
            raw_data = obfuscated_code.encode('utf-8')

            # 分块加密
            encrypted_chunks = self._encrypt_chunks(raw_data, file_key)

            # 生成完整性校验
            integrity_hash = self._generate_integrity_hash(
                encrypted_chunks, file_key
            )

            # 生成自解密PHP文件
            decryptor_code = self._generate_decryptor(
                encrypted_chunks, file_key, self.salt, integrity_hash
            )

            # 写入加密文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(decryptor_code)

            # 返回加密结果
            result = {
                'success': True,
                'input_path': input_path,
                'output_path': output_path,
                'original_size': len(original_code),
                'encrypted_size': len(decryptor_code),
                'chunks_count': len(encrypted_chunks),
                'file_key': base64.b64encode(file_key).decode()
            }

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'input_path': input_path
            }

    def _encrypt_chunks(self, data: bytes, key: bytes,
                       chunk_size: int = 8192) -> List[Dict]:
        """
        分块加密数据

        Args:
            data: 要加密的数据
            key: 加密密钥
            chunk_size: 块大小

        Returns:
            List[Dict]: 加密块列表
        """
        encrypted_chunks = []

        # 生成随机IV
        iv = secrets.token_bytes(12)

        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]

            # 为每个块生成随机nonce
            nonce = secrets.token_bytes(12)

            # AES-256-GCM加密
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(nonce),
                backend=self.backend
            )
            encryptor = cipher.encryptor()

            # 加密块
            encrypted_chunk = encryptor.update(chunk) + encryptor.finalize()

            # 存储加密块信息
            chunk_data = {
                'iv': base64.b64encode(iv).decode(),
                'nonce': base64.b64encode(nonce).decode(),
                'data': base64.b64encode(encrypted_chunk).decode(),
                'tag': base64.b64encode(encryptor.tag).decode(),
                'index': i // chunk_size
            }

            encrypted_chunks.append(chunk_data)

        return encrypted_chunks

    def _generate_integrity_hash(self, encrypted_chunks: List[Dict],
                               key: bytes) -> str:
        """
        生成完整性校验哈希

        Args:
            encrypted_chunks: 加密块列表
            key: 密钥

        Returns:
            str: HMAC签名
        """
        # 构建要签名的数据
        chunks_data = ''.join([
            chunk['nonce'] + chunk['data'] + chunk['tag']
            for chunk in encrypted_chunks
        ])

        # 生成HMAC签名
        from cryptography.hazmat.primitives.hmac import HMAC
        h = HMAC(key, hashes.SHA256(), backend=self.backend)
        h.update(chunks_data.encode())
        return base64.b64encode(h.finalize()).decode()

    def _generate_decryptor(self, encrypted_chunks: List[Dict],
                          file_key: bytes, salt: bytes,
                          integrity_hash: str) -> str:
        """
        生成自解密PHP代码

        Args:
            encrypted_chunks: 加密块列表
            file_key: 文件密钥
            salt: 盐值
            integrity_hash: 完整性哈希

        Returns:
            str: 自解密PHP代码
        """
        # 将加密块转换为JSON字符串
        import json
        chunks_json = base64.b64encode(
            json.dumps(encrypted_chunks).encode()
        ).decode()

        # 将密钥转换为Base64
        file_key_b64 = base64.b64encode(file_key).decode()
        salt_b64 = base64.b64encode(salt).decode()

        # 生成解密器模板（无注释版本）
        decryptor_template = f'''<?php
class PHPDecryptor {{
    private $fileKey = '{file_key_b64}';
    private $salt = '{salt_b64}';
    private $integrityHash = '{integrity_hash}';
    private $chunks = '{chunks_json}';

    public function __construct() {{
        if (!$this->validateEnvironment()) {{
            die('Security check failed');
        }}

        $this->execute();
    }}

    private function validateEnvironment() {{
        if (version_compare(PHP_VERSION, '7.4.0', '<')) {{
            return false;
        }}

        if (!extension_loaded('openssl')) {{
            return false;
        }}

        return true;
    }}

    private function decryptChunks() {{
        try {{
            $fileKey = base64_decode($this->fileKey);
            $chunks = json_decode(base64_decode($this->chunks), true);

            $decryptedData = '';

            foreach ($chunks as $chunk) {{
                $iv = base64_decode($chunk['iv']);
                $nonce = base64_decode($chunk['nonce']);
                $data = base64_decode($chunk['data']);
                $tag = base64_decode($chunk['tag']);

                $cipher = openssl_decrypt(
                    $data,
                    'aes-256-gcm',
                    $fileKey,
                    OPENSSL_RAW_DATA,
                    $nonce,
                    $tag,
                    ''
                );

                if ($cipher === false) {{
                    throw new Exception('Decryption failed');
                }}

                $decryptedData .= $cipher;
            }}

            if (!$this->verifyIntegrity($decryptedData)) {{
                throw new Exception('Integrity check failed');
            }}

            return $decryptedData;

        }} catch (Exception $e) {{
            die('Decryption error: ' . $e->getMessage());
        }}
    }}

    private function verifyIntegrity($data) {{
        $fileKey = base64_decode($this->fileKey);
        $chunks = json_decode(base64_decode($this->chunks), true);

        $chunksData = '';
        foreach ($chunks as $chunk) {{
            $chunksData .= $chunk['nonce'] . $chunk['data'] . $chunk['tag'];
        }}

        $computedHash = hash_hmac('sha256', $chunksData, $fileKey, true);
        $expectedHash = base64_decode($this->integrityHash);

        return hash_equals($computedHash, $expectedHash);
    }}

    private function execute() {{
        $code = $this->decryptChunks();

        // 创建一个临时的全局变量容器
        $global_vars = array();

        // 在方法作用域内执行代码，但捕获所有定义的变量
        $capture_vars = function($code) use (&$global_vars) {{
            // 在这个闭包中执行原始代码
            eval('?>' . $code);

            // 捕获所有当前作用域的变量（除了内置变量）
            $defined_vars = get_defined_vars();
            $exclude_keys = ['code', 'global_vars', 'capture_vars', 'this'];

            foreach ($defined_vars as $name => $value) {{
                if (!in_array($name, $exclude_keys) && $name !== 'GLOBALS' && strpos($name, '_') !== 0) {{
                    $global_vars[$name] = $value;
                }}
            }}
        }};

        // 执行代码并捕获变量
        $capture_vars($code);

        // 将捕获的变量注入到全局作用域
        foreach ($global_vars as $name => $value) {{
            $GLOBALS[$name] = $value;
        }}

  
        unset($code, $global_vars, $capture_vars);
    }}
}}

new PHPDecryptor();
?>
'''

        return decryptor_template