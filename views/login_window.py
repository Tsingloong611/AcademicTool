# -*- coding: utf-8 -*-
# @Time    : 12/4/2024 5:37 PM
# @FileName: login_window.py
# @Software: PyCharm
import sys
from PySide6.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout, QLabel, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from database.db_config import update_db_config, get_db_config

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('数据库登录')
        self.setGeometry(300, 300, 300, 200)

        # 设置字体
        font = QFont("Microsoft YaHei", 10)
        self.setFont(font)

        # 创建布局
        layout = QVBoxLayout()

        # 用户名输入
        self.username_label = QLabel('用户名:')
        self.username_edit = QLineEdit()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_edit)

        # 密码输入
        self.password_label = QLabel('密码:')
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_edit)

        # 主机输入
        self.host_label = QLabel('主机:')
        self.host_edit = QLineEdit()
        layout.addWidget(self.host_label)
        layout.addWidget(self.host_edit)

        # 端口输入
        self.port_label = QLabel('端口:')
        self.port_edit = QLineEdit()
        layout.addWidget(self.port_label)
        layout.addWidget(self.port_edit)

        # 数据库名输入
        self.db_label = QLabel('数据库名:')
        self.db_edit = QLineEdit()
        layout.addWidget(self.db_label)
        layout.addWidget(self.db_edit)

        # 登录按钮
        self.login_button = QPushButton('登录')
        self.login_button.clicked.connect(self.login)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def login(self):
        username = self.username_edit.text()
        password = self.password_edit.text()
        host = self.host_edit.text()
        port = self.port_edit.text()
        db_name = self.db_edit.text()

        # 更新数据库配置
        update_db_config({
            'DB_USERNAME': username,
            'DB_PASSWORD': password,
            'DB_HOST': host,
            'DB_PORT': port,
            'DB_NAME': db_name
        })

        # 尝试连接数据库
        try:
            QMessageBox.information(self, '成功', '数据库配置更新成功')
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, '错误', f'数据库连接失败: {str(e)}')

def main():
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()