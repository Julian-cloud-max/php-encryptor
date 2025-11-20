#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHP代码解析器
负责解析PHP代码，提取变量、函数、类等信息
"""

import re
import ast
from typing import List, Dict, Set, Optional, Tuple

class PHPParser:
    """PHP代码解析器"""

    def __init__(self):
        # PHP保留关键字和超全局变量
        self.reserved_keywords = {
            'abstract', 'and', 'array', 'as', 'break', 'callable', 'case', 'catch',
            'class', 'clone', 'const', 'continue', 'declare', 'default', 'die', 'do',
            'echo', 'else', 'elseif', 'empty', 'enddeclare', 'endfor', 'endforeach',
            'endif', 'endswitch', 'endwhile', 'eval', 'exit', 'extends', 'final',
            'for', 'foreach', 'function', 'global', 'goto', 'if', 'implements',
            'include', 'include_once', 'instanceof', 'insteadof', 'interface',
            'isset', 'list', 'namespace', 'new', 'or', 'print', 'private',
            'protected', 'public', 'require', 'require_once', 'return', 'static',
            'switch', 'throw', 'trait', 'try', 'unset', 'use', 'var', 'while',
            'xor', 'yield'
        }

        # PHP超全局变量（不应被混淆）
        self.superglobals = {
            '$GLOBALS', '$_SERVER', '$_GET', '$_POST', '$_FILES', '$_COOKIE',
            '$_SESSION', '$_REQUEST', '$_ENV', '$this', '$argc', '$argv'
        }

        # PHP魔术常量
        self.magic_constants = {
            '__LINE__', '__FILE__', '__DIR__', '__FUNCTION__', '__CLASS__',
            '__TRAIT__', '__METHOD__', '__NAMESPACE__'
        }

    def parse(self, code: str) -> Dict:
        """
        解析PHP代码

        Args:
            code: PHP代码字符串

        Returns:
            Dict: 解析结果
        """
        return {
            'original_code': code,
            'variables': self.extract_variables(code),
            'functions': self.extract_functions(code),
            'classes': self.extract_classes(code),
            'strings': self.extract_strings(code),
            'comments': self.extract_comments(code)
        }

    def extract_variables(self, code: str) -> List[str]:
        """
        提取变量名

        Args:
            code: PHP代码

        Returns:
            List[str]: 变量名列表
        """
        variables = []

        # 匹配变量名的正则表达式
        variable_pattern = r'\$([a-zA-Z_\x80-\xff][a-zA-Z0-9_\x80-\xff]*)'

        # 查找所有变量
        matches = re.finditer(variable_pattern, code)

        for match in matches:
            var_name = '$' + match.group(1)

            # 过滤掉不应混淆的变量
            if not self._should_obfuscate_variable(var_name):
                continue

            # 避免重复
            if var_name not in variables:
                variables.append(var_name)

        return variables

    def extract_functions(self, code: str) -> List[Dict]:
        """
        提取函数定义

        Args:
            code: PHP代码

        Returns:
            List[Dict]: 函数信息列表
        """
        functions = []

        # 匹配函数定义
        function_pattern = r'function\s+([a-zA-Z_\x80-\xff][a-zA-Z0-9_\x80-\xff]*)\s*\('

        matches = re.finditer(function_pattern, code)

        for match in matches:
            func_name = match.group(1)

            # 过滤掉魔术方法
            if func_name.startswith('__'):
                continue

            functions.append({
                'name': func_name,
                'position': match.start()
            })

        return functions

    def extract_classes(self, code: str) -> List[Dict]:
        """
        提取类定义

        Args:
            code: PHP代码

        Returns:
            List[Dict]: 类信息列表
        """
        classes = []

        # 匹配类定义
        class_pattern = r'(?:abstract\s+|final\s+)?class\s+([a-zA-Z_\x80-\xff][a-zA-Z0-9_\x80-\xff]*)'

        matches = re.finditer(class_pattern, code)

        for match in matches:
            class_name = match.group(1)

            classes.append({
                'name': class_name,
                'position': match.start()
            })

        return classes

    def extract_strings(self, code: str) -> List[Dict]:
        """
        提取字符串常量

        Args:
            code: PHP代码

        Returns:
            List[Dict]: 字符串信息列表
        """
        strings = []

        # 使用更精确的正则表达式匹配字符串
        # 单引号字符串：支持转义
        single_quote_pattern = r"'((?:[^'\\]|\\.)*)'"
        # 双引号字符串：支持转义和变量插值
        double_quote_pattern = r'"((?:[^"\\]|\\.)*)"'
        # Heredoc字符串
        heredoc_pattern = r'<<<([A-Za-z_][A-Za-z0-9_]*)\n(.*?)\n\1'

        patterns = [
            (single_quote_pattern, 'single'),
            (double_quote_pattern, 'double'),
            (heredoc_pattern, 'heredoc')
        ]

        for pattern, string_type in patterns:
            if string_type == 'heredoc':
                matches = re.finditer(pattern, code, re.DOTALL)
            else:
                matches = re.finditer(pattern, code)

            for match in matches:
                if string_type == 'heredoc':
                    string_content = match.group(2)
                    full_match = match.group(0)
                else:
                    string_content = match.group(1)
                    full_match = match.group(0)

                # 过滤掉太短的字符串（但保留重要内容）
                if len(string_content.strip()) < 1:
                    continue

                # 过滤掉看起来像数字或布尔值的字符串
                if string_content.strip() in ['true', 'false', 'null', '0', '1']:
                    continue

                # 过滤掉看起来像纯SQL查询的字符串
                if self._looks_like_sql(string_content):
                    continue

                # 过滤掉HTML片段（通常不应该混淆）
                if self._looks_like_html(string_content):
                    continue

                strings.append({
                    'content': string_content,
                    'type': string_type,
                    'position': match.start(),
                    'length': len(full_match)
                })

        return strings

    def extract_comments(self, code: str) -> List[Dict]:
        """
        提取注释

        Args:
            code: PHP代码

        Returns:
            List[Dict]: 注释信息列表
        """
        comments = []

        # 匹配单行注释
        single_line_pattern = r'//.*$'
        matches = re.finditer(single_line_pattern, code, re.MULTILINE)

        for match in matches:
            comments.append({
                'type': 'single_line',
                'content': match.group(0),
                'position': match.start(),
                'length': len(match.group(0))
            })

        # 匹配多行注释
        multi_line_pattern = r'/\*(.*?)\*/'
        matches = re.finditer(multi_line_pattern, code, re.DOTALL)

        for match in matches:
            comments.append({
                'type': 'multi_line',
                'content': match.group(0),
                'position': match.start(),
                'length': len(match.group(0))
            })

        return comments

    def _should_obfuscate_variable(self, var_name: str) -> bool:
        """
        判断变量是否应该被混淆

        Args:
            var_name: 变量名

        Returns:
            bool: 是否应该混淆
        """
        # 不混淆超全局变量
        if var_name in self.superglobals:
            return False

        # 不混淆魔术常量
        if var_name in self.magic_constants:
            return False

        # 不混淆保留关键字
        if var_name.lstrip('$') in self.reserved_keywords:
            return False

        # 不混淆单个字符的变量（除了特殊情况）
        if len(var_name) <= 2 and var_name not in ['$i', '$j', '$k', '$v', '$k', '$n']:
            return False

        return True

    def _looks_like_sql(self, content: str) -> bool:
        """
        判断字符串是否看起来像SQL查询

        Args:
            content: 字符串内容

        Returns:
            bool: 是否像SQL
        """
        sql_keywords = {
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'FROM', 'WHERE', 'JOIN',
            'INNER', 'LEFT', 'RIGHT', 'ORDER BY', 'GROUP BY', 'HAVING',
            'CREATE', 'DROP', 'ALTER', 'TABLE', 'INDEX'
        }

        content_upper = content.upper()

        # 检查是否包含SQL关键字
        for keyword in sql_keywords:
            if keyword in content_upper:
                return True

        # 检查是否包含表名模式（通常包含下划线）
        if re.search(r'\b[a-z_]+_[a-z_]+\b', content):
            return True

        return False

    def _looks_like_html(self, content: str) -> bool:
        """
        判断字符串是否看起来像HTML代码

        Args:
            content: 字符串内容

        Returns:
            bool: 是否像HTML
        """
        # 检查HTML标签
        html_patterns = [
            r'<[a-zA-Z][^>]*>',  # HTML开始标签
            r'</[a-zA-Z][^>]*>', # HTML结束标签
            r'<[a-zA-Z][^>]*/>', # HTML自闭合标签
            r'&[a-zA-Z]+;',      # HTML实体
        ]

        for pattern in html_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        # 检查常见HTML属性
        html_attributes = [
            'class=', 'id=', 'href=', 'src=', 'alt=', 'title=',
            'style=', 'onclick=', 'onload=', 'target=', 'rel='
        ]

        content_lower = content.lower()
        for attr in html_attributes:
            if attr in content_lower:
                return True

        return False

    def get_code_statistics(self, code: str) -> Dict:
        """
        获取代码统计信息

        Args:
            code: PHP代码

        Returns:
            Dict: 统计信息
        """
        parsed = self.parse(code)

        return {
            'total_lines': len(code.split('\n')),
            'variable_count': len(parsed['variables']),
            'function_count': len(parsed['functions']),
            'class_count': len(parsed['classes']),
            'string_count': len(parsed['strings']),
            'comment_count': len(parsed['comments']),
            'code_size': len(code),
            'code_size_kb': round(len(code) / 1024, 2)
        }