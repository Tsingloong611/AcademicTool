# -*- coding: utf-8 -*-
# @Time    : 2025/4/8 18:55
# @FileName: build.py
# @Software: PyCharm
import subprocess
import os
import sys
import time
import site

# 主要配置
MAIN_SCRIPT = "main.py"
OUTPUT_DIR = "dist"

# 自动查找 owlready2 的资源目录

def find_module_path(module_name: str, subdir: str = ""):
    candidates = site.getsitepackages() + [site.getusersitepackages()]
    for path in candidates:
        candidate = os.path.join(path, module_name, subdir)
        if os.path.exists(candidate):
            return candidate
    return None

owlready2_pellet_path = find_module_path("owlready2", "pellet")
pyagrum_defaults_path = find_module_path("pyagrum", "defaults.ini")

if not owlready2_pellet_path:
    print("❌ 找不到 owlready2 的 pellet 目录，请确认已正确安装。")
    sys.exit(1)

if not pyagrum_defaults_path:
    print("❌ 找不到 pyagrum 的 defaults.ini 文件，可能无法正常运行。")
    sys.exit(1)

# PyInstaller打包命令
command = [
    sys.executable, "-m", "PyInstaller",
    "--windowed",

    f"--name=main",

    f"--add-data={owlready2_pellet_path};owlready2/pellet" if sys.platform == "win32" else f"--add-data={owlready2_pellet_path}:owlready2/pellet",
    f"--add-data={pyagrum_defaults_path};pyagrum/defaults.ini" if sys.platform == "win32" else f"--add-data={pyagrum_defaults_path}:pyagrum/defaults.ini",

    "--add-data=config.json;." if sys.platform == "win32" else "--add-data=config.json:.",
    "--add-data=resources;resources" if sys.platform == "win32" else "--add-data=resources:resources",
    "--add-data=translations;translations" if sys.platform == "win32" else "--add-data=translations:translations",
    "--add-data=data;data" if sys.platform == "win32" else "--add-data=data:data",

    f"--distpath={OUTPUT_DIR}",
    MAIN_SCRIPT
]

# 执行打包命令
print("开始使用PyInstaller打包...")
start_time = time.time()

process = subprocess.Popen(
    command,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
)

for line in process.stdout:
    print(line.strip())

return_code = process.wait()

elapsed_time = time.time() - start_time
minutes, seconds = divmod(elapsed_time, 60)

if return_code == 0:
    print(f"打包完成！耗时：{int(minutes)}分{int(seconds)}秒")
    with open(os.path.join(OUTPUT_DIR, "run.bat"), "w", encoding="utf-8") as f:
        f.write(r"""@echo off
cd /d %~dp0
main.exe
pause
""")

    print(f"输出目录: {os.path.abspath(OUTPUT_DIR)}")
else:
    print(f"打包过程中出现错误，返回代码: {return_code}")
