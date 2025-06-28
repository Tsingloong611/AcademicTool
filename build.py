# -*- coding: utf-8 -*-
# @Time    : 2025/4/8 18:55 # Note: The time comment is static, update if needed
# @FileName: build_nuitka.py # Renamed for clarity
# @Software: PyCharm
import subprocess
import os
import sys
import time
import site

# --- Configuration ---
MAIN_SCRIPT = "main.py"
OUTPUT_DIR = "dist_nuitka" # Changed output dir slightly to avoid conflict if both scripts run

# --- Helper Function to Find Module Paths ---
def find_module_path(module_name: str, subdir: str = "") -> str | None:
    """
    Finds the path to a module or a subdirectory within a module in site-packages.
    """
    candidates = site.getsitepackages() + [site.getusersitepackages()]
    for path in candidates:
        module_base_path = os.path.join(path, module_name)
        if os.path.exists(module_base_path):
            candidate = os.path.join(module_base_path, subdir) if subdir else module_base_path
            if os.path.exists(candidate):
                print(f"✅ Found '{module_name}{'/' + subdir if subdir else ''}' at: {candidate}")
                return candidate
            else:
                 print(f"ℹ️ Checked non-existent subdir: {candidate}")
        # else:
            # print(f"ℹ️ Module base '{module_name}' not found in: {path}") # Can be noisy

    print(f"⚠️ Could not find path for '{module_name}{'/' + subdir if subdir else ''}' in site-packages.")
    return None

# --- Find Dynamic Paths ---
print("🔍 Searching for required package data paths...")
owlready2_pellet_path = find_module_path("owlready2", "pellet")
pyagrum_defaults_path = find_module_path("pyagrum", "defaults.ini")

# --- Error Handling for Missing Paths ---
missing_paths = False
if not owlready2_pellet_path:
    print("❌ Critical: Cannot find the 'owlready2/pellet' directory. Please ensure 'owlready2' is correctly installed.")
    missing_paths = True
# Check if the found path is actually a directory as expected
elif not os.path.isdir(owlready2_pellet_path):
     print(f"❌ Critical: Expected 'owlready2/pellet' to be a directory, but found a file at: {owlready2_pellet_path}")
     missing_paths = True


if not pyagrum_defaults_path:
    print("❌ Critical: Cannot find the 'pyagrum/defaults.ini' file. Please ensure 'pyagrum' is correctly installed.")
    missing_paths = True
# Check if the found path is actually a file as expected
elif not os.path.isfile(pyagrum_defaults_path):
    print(f"❌ Critical: Expected 'pyagrum/defaults.ini' to be a file, but found a directory at: {pyagrum_defaults_path}")
    missing_paths = True
rdflib_plugins_path = "C:/Users/Tsing_loong/AppData/Roaming/Python/Python313/site-packages/rdflib/plugins"

if missing_paths:
    sys.exit("Exiting due to missing required package data paths.")

# --- Nuitka Build Command Construction ---
print("🛠️ Constructing Nuitka build command...")
command = [
    sys.executable, "-m", "nuitka",
    "--standalone",             # Create a self-contained folder
    "--assume-yes-for-downloads", # Automatically download dependencies if needed
    "--remove-output",          # Clean output directory before build
    "--follow-imports",

    # === Plugins ===
    "--enable-plugin=pyside6",  # Enable PySide6 support
    "--include-qt-plugins=all", # Include necessary Qt plugins (sensible default)
    # Add other plugins if needed (e.g., numpy, pandas)
    # "--enable-plugin=numpy",
    # "--enable-plugin=pandas",

    # === Data Files & Directories ===
    # --- Dynamic Paths ---
    # Nuitka syntax: --include-data-dir=<SRC>=<DST_IN_BUILD>
    f"--include-data-dir={owlready2_pellet_path}=owlready2/pellet",
    # Nuitka syntax: --include-data-files=<SRC>=<DST_IN_BUILD>
    f"--include-data-files={pyagrum_defaults_path}=pyagrum/defaults.ini",
    "--enable-plugin=multiprocessing", # Enable multiprocessing support
    f"--include-data-dir={rdflib_plugins_path}=rdflib/plugins",  # 确保路径和目标目录正确
    # --- Static Project Files/Dirs ---
    "--include-data-files=config.json=config.json",
    "--include-data-dir=resources=resources",       # Project resource directory
    "--include-data-dir=translations=translations", # Project translation directory
    "--include-data-dir=data=data",                 # Project data directory

    # === Module Handling ===
    # Include potentially hidden imports if needed (example)
    # "--include-module=some.hidden.dependency",

    # Exclude modules to reduce size (keep existing exclusions)

    # === Build Options ===
    #"--windows-disable-console" if sys.platform == "win32" else "", # Use --macos-disable-console on macOS if needed
    f"--jobs={os.cpu_count()}",  # Use available CPU cores
    "--lto=yes",                # Link Time Optimization (can increase build time)

    # === Output & Logging ===
    "--show-progress",          # Display compilation progress
    "--show-scons",             # Show SCons execution details (can be verbose)
    # "--show-modules",           # Show included modules (can be very verbose)
    f"--output-dir={OUTPUT_DIR}",# Specify the output directory name

    # === Main Script ===
    MAIN_SCRIPT
]

# Filter out empty strings from command list (e.g., from conditional options)
command = [arg for arg in command if arg]
import os
import sys
import site


# 或者使用您的特定路径
site_packages_path = "C:/Users/Tsing_loong/AppData/Roaming/Python/Python313/site-packages"

# 您需要包含的包列表
packages = [
    "altgraph", "asttokens", "certifi", "charset_normalizer", "colorama",
    "contourpy", "cycler", "decorator", "et_xmlfile", "executing",
    "fonttools", "graphviz", "greenlet", "idna", "ipydex",
    "ipython", "ipython_pygments_lexers", "jedi", "kiwisolver", "markdown2",
    "matplotlib", "matplotlib_inline", "mysql", "mysql_connector_python", "mysqlclient",
    "networkx", "nuitka", "numpy", "nxv", "openpyxl",
    "ordered_set", "owlready2", "packaging", "pandas", "parso",
    "pefile", "pexpect", "pickleshare", "pillow", "prompt_toolkit",
    "ptyprocess", "pure_eval", "pyAgrum", "pydot", "pygments",
    "pyinstaller", "pyinstaller_hooks_contrib", "pymysql", "pyparsing", "PySide6",
    "PySide6_Addons", "PySide6_Essentials", "python_dateutil", "python_decouple", "pytz",
    "pywin32_ctypes", "pyyaml", "rdflib", "requests", "scipy",
    "semantictools", "setuptools", "shiboken6", "six", "sqlalchemy",
    "stack_data", "traitlets", "typing_extensions", "tzdata", "urllib3",
    "wcwidth", "zstandard"
]
for package in packages:
    package_path = os.path.join(site_packages_path, package)
    # 检查包是否存在(文件夹形式)
    if os.path.isdir(package_path):
        command.append(f'--include-data-dir={package_path}={package}')
# --- Execute Build Command ---
print("-" * 60)
print(f"🚀 Starting Nuitka build for '{MAIN_SCRIPT}'...")
print(f"Output directory: {os.path.abspath(OUTPUT_DIR)}")
# Print the command for debugging (optional)
# print("Executing command:")
# print(" ".join(command))
print("-" * 60)

start_time = time.time()

# Run Nuitka using subprocess, capturing output
process = subprocess.Popen(
    command,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT, # Redirect stderr to stdout
    text=True,                # Decode output as text
    encoding='utf-8',         # Specify encoding (important for cross-platform)
    errors='replace',         # Replace undecodable characters
    bufsize=1,                # Line buffered output
)

# Print Nuitka output line by line
while True:
    line = process.stdout.readline()
    if not line:
        break
    print(line.strip())

# Wait for the process to complete and get the return code
return_code = process.wait()

# --- Post-Build ---
elapsed_time = time.time() - start_time
minutes, seconds = divmod(elapsed_time, 60)

print("-" * 60)
if return_code == 0:
    print(f"✅ Nuitka build completed successfully!")
    print(f"⏱️ Total time taken: {int(minutes)} minutes {int(seconds)} seconds")

    # Create a batch file for easy execution on Windows
    if sys.platform == "win32":
        run_script_path = os.path.join(OUTPUT_DIR, "run.bat")
        # Nuitka standalone places the exe inside a <main_script_name>.dist folder
        exe_folder = f"{os.path.splitext(MAIN_SCRIPT)[0]}.dist"
        exe_path = os.path.join(exe_folder, f"{os.path.splitext(MAIN_SCRIPT)[0]}.exe")

        try:
            with open(run_script_path, "w", encoding="utf-8") as f:
                f.write(f"""@echo off
echo Changing directory to executable location...
cd /d "%~dp0\\{exe_folder}"
echo Launching {os.path.basename(exe_path)}...
start "" "{os.path.basename(exe_path)}"

rem Optional: Add error logging check if your app creates one
rem if exist error.log (
rem     echo Found error.log, opening...
rem     notepad error.log
rem ) else (
rem     echo No error.log found.
rem )

echo Script finished. Press any key to close this window.
pause > nul
""")
            print(f"📄 Created helper script: {run_script_path}")
        except Exception as e:
            print(f"⚠️ Could not create run.bat: {e}")

    # Add similar script generation for Linux/macOS if desired (.sh)

    print(f"📦 Output located at: {os.path.abspath(OUTPUT_DIR)}")
else:
    print(f"❌ Nuitka build failed with error code: {return_code}")
    print("👉 Please check the output above for specific error messages from Nuitka.")
print("-" * 60)