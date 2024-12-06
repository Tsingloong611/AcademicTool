# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:09 AM
# @FileName: main.py
# @Software: PyCharm

import sys

from PySide6.QtGui import QFont, Qt
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog
from views.main_window import MainWindow
from views.login_dialog import LoginDialog
from database.db_config import DatabaseManager

def main():
    app = QApplication(sys.argv)
    QApplication.setStyle("Fusion")

    # 设置全局字体
    app.setAttribute(Qt.AA_EnableHighDpiScaling)  # 启用高 DPI 支持
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)  # 使图标适配高 DPI

    # 初始化数据库管理器
    db_manager = DatabaseManager()

    # 创建登录对话框
    login_dialog = LoginDialog(db_manager)
    if login_dialog.exec() == QDialog.Accepted:
        # 登录成功，创建并显示主窗口

        window = MainWindow(db_manager)
        window.show()
        sys.exit(app.exec())
    else:
        # 登录失败或用户取消，退出应用程序
        sys.exit()

if __name__ == '__main__':
    main()