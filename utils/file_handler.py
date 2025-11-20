#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件处理工具
负责文件和目录的批量操作
"""

import os
import glob
import shutil
from typing import List, Tuple, Generator
from pathlib import Path

class FileHandler:
    """文件处理器"""

    def __init__(self):
        self.supported_extensions = {'.php', '.phtml', '.php3', '.php4', '.php5', '.php7', '.php8'}

    def find_php_files(self, path: str, recursive: bool = True) -> List[str]:
        """
        查找PHP文件

        Args:
            path: 路径（文件或目录）
            recursive: 是否递归搜索

        Returns:
            List[str]: PHP文件路径列表
        """
        php_files = []

        if os.path.isfile(path):
            # 如果是文件，检查扩展名
            if Path(path).suffix.lower() in self.supported_extensions:
                php_files.append(path)
        elif os.path.isdir(path):
            # 如果是目录，搜索所有PHP文件
            if recursive:
                pattern = os.path.join(path, '**', '*.php*')
                php_files = glob.glob(pattern, recursive=True)
                # 过滤扩展名
                php_files = [
                    f for f in php_files
                    if Path(f).suffix.lower() in self.supported_extensions
                ]
            else:
                # 非递归搜索
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    if os.path.isfile(item_path):
                        if Path(item_path).suffix.lower() in self.supported_extensions:
                            php_files.append(item_path)

        # 排序并返回
        return sorted(php_files)

    def batch_process_files(self, file_list: List[str],
                           output_dir: str,
                           processor_func,
                           **kwargs) -> List[Tuple[str, bool, str]]:
        """
        批量处理文件

        Args:
            file_list: 文件列表
            output_dir: 输出目录
            processor_func: 处理函数
            **kwargs: 处理函数的额外参数

        Returns:
            List[Tuple]: 处理结果列表 (文件路径, 成功标志, 消息)
        """
        results = []

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        for file_path in file_list:
            try:
                # 生成输出文件路径
                relative_path = os.path.relpath(file_path)
                output_path = os.path.join(output_dir, relative_path)

                # 确保输出文件的目录存在
                output_file_dir = os.path.dirname(output_path)
                os.makedirs(output_file_dir, exist_ok=True)

                # 处理文件
                result = processor_func(file_path, output_path, **kwargs)

                if result.get('success', False):
                    results.append((file_path, True, '处理成功'))
                else:
                    results.append((file_path, False, result.get('error', '处理失败')))

            except Exception as e:
                results.append((file_path, False, f'处理异常: {str(e)}'))

        return results

    def get_file_info(self, file_path: str) -> dict:
        """
        获取文件信息

        Args:
            file_path: 文件路径

        Returns:
            dict: 文件信息
        """
        try:
            stat = os.stat(file_path)

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                line_count = len(content.splitlines())
                char_count = len(content)

            return {
                'path': file_path,
                'name': os.path.basename(file_path),
                'size': stat.st_size,
                'size_kb': round(stat.st_size / 1024, 2),
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'lines': line_count,
                'characters': char_count,
                'extension': Path(file_path).suffix.lower(),
                'modified_time': stat.st_mtime,
                'is_php': Path(file_path).suffix.lower() in self.supported_extensions
            }

        except Exception as e:
            return {
                'path': file_path,
                'error': str(e)
            }

    def create_backup(self, file_path: str, backup_suffix: str = None) -> str:
        """
        创建文件备份

        Args:
            file_path: 原文件路径
            backup_suffix: 备份后缀

        Returns:
            str: 备份文件路径
        """
        if backup_suffix is None:
            import datetime
            backup_suffix = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

        backup_path = f"{file_path}.backup_{backup_suffix}"

        try:
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            raise Exception(f"创建备份失败: {str(e)}")

    def safe_remove_file(self, file_path: str) -> bool:
        """
        安全删除文件

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否成功删除
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False

    def validate_file_path(self, file_path: str) -> Tuple[bool, str]:
        """
        验证文件路径

        Args:
            file_path: 文件路径

        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        if not file_path:
            return False, "文件路径不能为空"

        if not os.path.exists(file_path):
            return False, "文件不存在"

        if not os.access(file_path, os.R_OK):
            return False, "文件不可读"

        if os.path.isdir(file_path):
            return False, "路径是目录，不是文件"

        extension = Path(file_path).suffix.lower()
        if extension not in self.supported_extensions:
            return False, f"不支持的文件类型: {extension}"

        return True, ""

    def get_directory_info(self, dir_path: str) -> dict:
        """
        获取目录信息

        Args:
            dir_path: 目录路径

        Returns:
            dict: 目录信息
        """
        try:
            php_files = self.find_php_files(dir_path, recursive=True)

            total_size = 0
            total_lines = 0
            file_count = len(php_files)

            for file_path in php_files:
                file_info = self.get_file_info(file_path)
                total_size += file_info.get('size', 0)
                total_lines += file_info.get('lines', 0)

            return {
                'path': dir_path,
                'name': os.path.basename(dir_path),
                'php_files_count': file_count,
                'total_size': total_size,
                'total_size_kb': round(total_size / 1024, 2),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'total_lines': total_lines,
                'average_file_size': total_size / file_count if file_count > 0 else 0,
                'average_lines': total_lines / file_count if file_count > 0 else 0
            }

        except Exception as e:
            return {
                'path': dir_path,
                'error': str(e)
            }

    def progress_generator(self, file_list: List[str]) -> Generator[Tuple[str, int, int], None, None]:
        """
        进度生成器

        Args:
            file_list: 文件列表

        Yields:
            Tuple: (当前文件, 当前进度, 总进度)
        """
        total = len(file_list)

        for index, file_path in enumerate(file_list):
            progress = (index + 1) / total
            yield (file_path, index + 1, total)