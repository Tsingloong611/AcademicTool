# -*- coding: utf-8 -*-
# @Time    : 2025/3/9 11:52
# @FileName: test11.py
# @Software: PyCharm
import os
import sys
import subprocess
import glob

# PySide6工具路径
PYSIDE6_DIR = r"E:\PySide6"
LUPDATE = os.path.join(PYSIDE6_DIR, "lupdate")
LRELEASE = os.path.join(PYSIDE6_DIR, "lrelease")

# 你现有的翻译文件路径
TS_FILE = "translations/translations_en_US.ts"
QM_FILE = "translations/translations_en_US.qm"


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
    """直接更新现有的翻译文件，保留已翻译的内容"""
    # 确保翻译文件存在
    if not os.path.exists(TS_FILE):
        print(f"现有翻译文件不存在: {TS_FILE}")
        print("请确保已将旧的翻译文件复制到正确位置")
        return False

    # 获取所有Python文件
    py_files = find_all_python_files()
    if not py_files:
        print("当前目录及子目录中未找到Python文件!")
        return False

    print(f"找到 {len(py_files)} 个Python文件")

    # 使用lupdate直接更新现有文件
    # lupdate会保留已翻译的部分，并添加新的未翻译字符串
    cmd = [LUPDATE, "-noobsolete"] + py_files + ["-ts", TS_FILE]
    print(f"运行命令: {' '.join(cmd)}")

    try:
        process = subprocess.run(cmd, check=True, text=True, capture_output=True)
        if process.stdout:
            print(process.stdout)
        if process.stderr:
            print(f"警告/错误: {process.stderr}")

        print(f"成功更新翻译文件: {TS_FILE}")
        print("已保留所有已翻译的内容，并添加了新的可翻译字符串")
        return True
    except subprocess.CalledProcessError as e:
        print(f"运行lupdate时出错: {e}")
        print(f"命令输出: {e.stdout}")
        print(f"错误输出: {e.stderr}")
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
        if process.stderr:
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

    # 使用lupdate的-noobsolete选项更新一次，以确保状态是最新的
    py_files = find_all_python_files()
    subprocess.run([LUPDATE, "-noobsolete"] + py_files + ["-ts", TS_FILE],
                   check=False, capture_output=True)

    # 使用简单的XML解析来检查翻译状态
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(TS_FILE)
        root = tree.getroot()

        total_messages = 0
        translated = 0
        untranslated = 0

        for context in root.findall(".//context"):
            context_name = context.find("name").text
            messages = context.findall("message")

            for message in messages:
                total_messages += 1

                source_text = message.find("source").text
                translation = message.find("translation")

                if translation.get("type") == "unfinished" or not translation.text:
                    untranslated += 1
                    print(f"未翻译: [{context_name}] \"{source_text}\"")
                else:
                    translated += 1

        print(f"\n翻译状态统计:")
        print(f"总字符串数: {total_messages}")
        print(f"已翻译: {translated} ({(translated / total_messages * 100) if total_messages else 0:.1f}%)")
        print(f"未翻译: {untranslated} ({(untranslated / total_messages * 100) if total_messages else 0:.1f}%)")

    except Exception as e:
        print(f"检查翻译状态时出错: {e}")


def main():
    """主函数"""
    # 确保翻译目录存在
    ensure_translations_dir()

    print("PySide6翻译文件更新工具")
    print("=====================")
    print("此脚本将更新现有的翻译文件，同时保留已翻译内容")
    print(f"翻译文件: {TS_FILE}")
    print()

    # 更新翻译文件
    print("正在更新翻译文件...")
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