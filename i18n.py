# -*- coding: utf-8 -*-
# @Time    : 2025/3/9 11:52
# @FileName: test11.py
# @Software: PyCharm
import os
import sys
import subprocess
import glob
import shutil
import time

# PySide6工具路径
PYSIDE6_DIR = r"E:\PySide6"
LUPDATE = os.path.join(PYSIDE6_DIR, "lupdate")
LRELEASE = os.path.join(PYSIDE6_DIR, "lrelease")

# 你现有的翻译文件路径
TS_FILE = "translations/translations_en_US.ts"
QM_FILE = "translations/translations_en_US.qm"
# 修改临时文件名，使用正确的.ts扩展名
TEMP_TS_FILE = "translations/translations_temp.ts"


def ensure_translations_dir():
    """确保translations目录存在"""
    if not os.path.exists("translations"):
        os.makedirs("translations")
        print("Created translations directory")


def find_all_python_files(directory="."):
    """递归查找所有Python文件"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # 排除一些常见的不需要扫描的目录
        if '.git' in dirs:
            dirs.remove('.git')
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')
        if 'venv' in dirs:
            dirs.remove('venv')

        for file in files:
            if file.endswith(".py"):
                # 使用相对路径
                rel_path = os.path.join(root, file)
                python_files.append(rel_path)

    return python_files


def update_existing_translation_file():
    """更新现有的翻译文件，确保所有新的tr调用都被检测到"""
    # 确保翻译目录存在
    ensure_translations_dir()

    # 处理文件权限
    if os.path.exists(TS_FILE):
        try:
            # 检查文件是否可写
            if not os.access(TS_FILE, os.W_OK):
                print(f"警告: 翻译文件 {TS_FILE} 不可写！尝试更改权限...")
                os.chmod(TS_FILE, 0o666)  # 设置可读写权限

            # 创建备份
            backup_file = f"translations/backup_{int(time.time())}.ts"
            shutil.copy2(TS_FILE, backup_file)
            print(f"已备份现有翻译文件到 {backup_file}")
        except Exception as e:
            print(f"处理文件权限或创建备份时出错: {e}")

    # 获取所有Python文件
    py_files = find_all_python_files()
    if not py_files:
        print("当前目录及子目录中未找到Python文件!")
        return False

    print(f"找到 {len(py_files)} 个Python文件")

    # 确保没有遗留的临时文件
    if os.path.exists(TEMP_TS_FILE):
        try:
            os.remove(TEMP_TS_FILE)
        except Exception as e:
            print(f"无法删除旧的临时文件: {e}")

    # 步骤1: 先创建一个全新的翻译文件以确保捕获所有新字符串
    new_cmd = [LUPDATE] + py_files + ["-ts", TEMP_TS_FILE]
    print(f"运行命令: {' '.join(new_cmd)}")

    try:
        process = subprocess.run(new_cmd, check=True, text=True, capture_output=True)
        if process.stdout:
            print(process.stdout)
        if process.stderr and process.stderr.strip():
            print(f"警告/错误: {process.stderr}")

        if not os.path.exists(TEMP_TS_FILE):
            print(f"错误: 临时翻译文件未创建: {TEMP_TS_FILE}")
            return False

        print(f"成功创建临时翻译文件: {TEMP_TS_FILE}")

        # 步骤2: 如果存在现有翻译文件，使用lconvert合并翻译
        if os.path.exists(TS_FILE):
            # 使用步骤1生成的临时文件直接替换原文件，但保持已翻译内容
            try:
                # 方法1: 使用直接的lupdate合并
                merge_cmd = [LUPDATE, "-noobsolete", TEMP_TS_FILE, TS_FILE, "-ts", TS_FILE]
                print(f"合并翻译文件，命令: {' '.join(merge_cmd)}")

                merge_process = subprocess.run(merge_cmd, check=True, text=True, capture_output=True)
                if merge_process.stdout:
                    print(merge_process.stdout)
                if merge_process.stderr and merge_process.stderr.strip():
                    print(f"合并警告/错误: {merge_process.stderr}")

                print(f"已合并翻译文件: {TS_FILE}")
            except subprocess.CalledProcessError as e:
                print(f"合并翻译文件时出错: {e}")
                print(f"命令输出: {e.stdout}")
                print(f"错误输出: {e.stderr}")

                # 如果合并失败，使用备份方案：保留临时文件供手动处理
                print(f"合并失败！临时文件 {TEMP_TS_FILE} 已保留，需要手动合并翻译。")
                return False

        else:
            # 如果不存在旧文件，直接重命名临时文件
            os.rename(TEMP_TS_FILE, TS_FILE)
            print(f"已创建新的翻译文件: {TS_FILE}")

        # 清理临时文件
        if os.path.exists(TEMP_TS_FILE):
            try:
                os.remove(TEMP_TS_FILE)
                print(f"已删除临时文件: {TEMP_TS_FILE}")
            except Exception as e:
                print(f"无法删除临时文件: {e}")

        return True
    except subprocess.CalledProcessError as e:
        print(f"运行lupdate时出错: {e}")
        print(f"命令输出: {e.stdout}")
        print(f"错误输出: {e.stderr}")
        return False
    except Exception as e:
        print(f"更新翻译文件时出错: {e}")
        return False


def compile_translation_file():
    """编译翻译文件为.qm格式"""
    if not os.path.exists(TS_FILE):
        print(f"翻译源文件不存在: {TS_FILE}")
        return False

    cmd = [LRELEASE, TS_FILE, "-qm", QM_FILE]
    print(f"运行命令: {' '.join(cmd)}")

    try:
        process = subprocess.run(cmd, check=True, text=True, capture_output=True)
        if process.stdout:
            print(process.stdout)
        if process.stderr and process.stderr.strip():
            print(f"警告/错误: {process.stderr}")

        print(f"成功编译翻译文件: {QM_FILE}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"运行lrelease时出错: {e}")
        print(f"命令输出: {e.stdout}")
        print(f"错误输出: {e.stderr}")
        return False


def check_translation_status():
    """检查翻译状态"""
    if not os.path.exists(TS_FILE):
        print(f"翻译文件不存在: {TS_FILE}")
        return

    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(TS_FILE)
        root = tree.getroot()

        total_messages = 0
        translated = 0
        untranslated = 0
        new_additions = []

        for context in root.findall(".//context"):
            context_name = context.find("name").text
            messages = context.findall("message")

            for message in messages:
                total_messages += 1

                source_text = message.find("source").text
                translation = message.find("translation")

                if translation.get("type") == "unfinished" or not translation.text:
                    untranslated += 1
                    new_additions.append((context_name, source_text))
                else:
                    translated += 1

        print(f"\n翻译状态统计:")
        print(f"总字符串数: {total_messages}")
        print(f"已翻译: {translated} ({(translated / total_messages * 100) if total_messages else 0:.1f}%)")
        print(f"未翻译: {untranslated} ({(untranslated / total_messages * 100) if total_messages else 0:.1f}%)")

        if untranslated > 0:
            print("\n新增需要翻译的字符串:")
            for idx, (context, source) in enumerate(new_additions, 1):
                print(f"{idx}. [{context}] \"{source}\"")

    except Exception as e:
        print(f"检查翻译状态时出错: {e}")


def extract_tr_calls():
    """提取所有self.tr调用，方便检查是否被正确识别"""
    py_files = find_all_python_files()
    tr_calls = []

    import re
    pattern = r'self\.tr\([\'"]([^\'"]+)[\'"]\)'

    for py_file in py_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            matches = re.findall(pattern, content)
            if matches:
                for match in matches:
                    tr_calls.append((py_file, match))
        except Exception as e:
            print(f"读取文件 {py_file} 时出错: {e}")

    return tr_calls


def main():
    """主函数"""
    print("PySide6翻译文件更新工具 (增强版)")
    print("===========================")
    print("此脚本将更新现有的翻译文件，并确保捕获所有新增的tr调用")
    print(f"翻译文件: {TS_FILE}")
    print()

    # 提取并显示所有tr调用
    print("正在提取所有self.tr调用...")
    tr_calls = extract_tr_calls()
    print(f"在代码中找到 {len(tr_calls)} 个tr调用")

    # 更新翻译文件
    print("\n正在更新翻译文件...")
    if update_existing_translation_file():
        print("\n正在检查翻译状态...")
        check_translation_status()

        print("\n是否要编译翻译文件为.qm格式? (y/n)")
        choice = input().strip().lower()
        if choice == 'y':
            compile_translation_file()

    print("\n完成!")


if __name__ == "__main__":
    main()