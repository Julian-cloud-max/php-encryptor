#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHP代码混淆器
负责变量名和字符串的混淆处理
"""

import re
import random
import string
from typing import Dict, List, Set
from .php_parser import PHPParser

class PHPObfuscator:
    """PHP代码混淆器"""

    def __init__(self):
        self.parser = PHPParser()
        self.variable_map = {}
        self.function_map = {}
        self.class_map = {}

    def obfuscate(self, parsed_code: Dict,
                  obfuscate_vars: bool = True,
                  obfuscate_functions: bool = False,
                  obfuscate_classes: bool = False) -> str:
        """
        混淆PHP代码

        Args:
            parsed_code: 解析后的代码信息
            obfuscate_vars: 是否混淆变量
            obfuscate_functions: 是否混淆函数
            obfuscate_classes: 是否混淆类

        Returns:
            str: 混淆后的代码
        """
        code = parsed_code['original_code']

        # 混淆变量名
        if obfuscate_vars:
            code = self._obfuscate_variables(code, parsed_code['variables'])

        # 混淆函数名
        if obfuscate_functions:
            code = self._obfuscate_functions(code, parsed_code['functions'])

        # 混淆类名
        if obfuscate_classes:
            code = self._obfuscate_classes(code, parsed_code['classes'])

        # 添加反调试代码
       # code = self._add_anti_debug_code(code)

        return code

    
    def _obfuscate_variables(self, code: str, variables: List[str]) -> str:
        """
        混淆变量名

        Args:
            code: PHP代码
            variables: 变量名列表

        Returns:
            str: 混淆后的代码
        """
        # 为每个变量生成混淆名
        for var in variables:
            if var not in self.variable_map:
                self.variable_map[var] = self._generate_obfuscated_name('var')

        # 替换变量名（要小心处理字符串中的内容）
        result = code
        for original, obfuscated in self.variable_map.items():
            # 只替换PHP代码中的变量，避免替换字符串中的
            pattern = r'(?<![\'"$])\b' + re.escape(original) + r'\b'
            result = re.sub(pattern, obfuscated, result)

        return result

    def _obfuscate_functions(self, code: str, functions: List[Dict]) -> str:
        """
        混淆函数名

        Args:
            code: PHP代码
            functions: 函数信息列表

        Returns:
            str: 混淆后的代码
        """
        # 为每个函数生成混淆名
        for func_info in functions:
            func_name = func_info['name']
            if func_name not in self.function_map:
                self.function_map[func_name] = self._generate_obfuscated_name('func')

        # 替换函数定义和调用
        result = code
        for original, obfuscated in self.function_map.items():
            # 替换函数定义
            result = re.sub(
                r'\bfunction\s+' + re.escape(original) + r'\s*\(',
                f'function {obfuscated}(',
                result
            )

            # 替换函数调用
            result = re.sub(
                r'\b' + re.escape(original) + r'\s*\(',
                f'{obfuscated}(',
                result
            )

        return result

    def _obfuscate_classes(self, code: str, classes: List[Dict]) -> str:
        """
        混淆类名

        Args:
            code: PHP代码
            classes: 类信息列表

        Returns:
            str: 混淆后的代码
        """
        # 为每个类生成混淆名
        for class_info in classes:
            class_name = class_info['name']
            if class_name not in self.class_map:
                self.class_map[class_name] = self._generate_obfuscated_name('class')

        # 替换类定义和使用
        result = code
        for original, obfuscated in self.class_map.items():
            # 替换类定义
            result = re.sub(
                r'\bclass\s+' + re.escape(original) + r'\b',
                f'class {obfuscated}',
                result
            )

            # 替换类实例化
            result = re.sub(
                r'\bnew\s+' + re.escape(original) + r'\b',
                f'new {obfuscated}',
                result
            )

            # 替换静态调用
            result = re.sub(
                r'\b' + re.escape(original) + r'::',
                f'{obfuscated}::',
                result
            )

        return result

    
    def _generate_obfuscated_name(self, prefix: str) -> str:
        """
        生成混淆名称

        Args:
            prefix: 名称前缀

        Returns:
            str: 混淆后的名称
        """
        if prefix == 'var':
            # 变量名使用$ + 字符数字混合
            chars = string.ascii_letters + string.digits
            length = random.randint(8, 12)
            name = '$' + ''.join(random.choice(chars) for _ in range(length))
        else:
            # 函数名和类名使用字母组合
            chars = string.ascii_letters
            length = random.randint(10, 15)
            name = ''.join(random.choice(chars) for _ in range(length))

        return name

    def _add_anti_debug_code(self, code: str) -> str:
        """
        添加反调试代码

        Args:
            code: PHP代码

        Returns:
            str: 添加反调试代码后的代码
        """
        anti_debug_code = '''
// 反调试检测
if(function_exists('xdebug_break') || ini_get('display_errors') || defined('DEBUG_BACKTRACE_IGNORE_ARGS')) {
    die('Debug environment detected');
}

// 检测可疑的调试器扩展
$debug_extensions = ['xdebug', 'xhprof', 'blackfire'];
foreach($debug_extensions as $ext) {
    if(extension_loaded($ext)) {
        die('Debug extension detected');
    }
}

// 时间检查，防止断点调试
$start_time = microtime(true);
function checkExecutionTime($threshold = 0.001) {
    global $start_time;
    $elapsed = microtime(true) - $start_time;
    if ($elapsed < $threshold) {
        die('Execution time too short - possible debugger bypass');
    }
    if ($elapsed > 10.0) {
        die('Execution time too long - possible debugging');
    }
}

'''

        return anti_debug_code + code

    def get_obfuscation_statistics(self) -> Dict:
        """
        获取混淆统计信息

        Returns:
            Dict: 混淆统计信息
        """
        return {
            'obfuscated_variables': len(self.variable_map),
            'obfuscated_functions': len(self.function_map),
            'obfuscated_classes': len(self.class_map),
            'variable_map': self.variable_map.copy(),
            'function_map': self.function_map.copy(),
            'class_map': self.class_map.copy()
        }