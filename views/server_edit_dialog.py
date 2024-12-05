# -*- coding: utf-8 -*-
# @Time    : 12/5/2024 11:23 AM
# @FileName: server_edit_dialog.py
# @Software: PyCharm
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QMessageBox, QFormLayout, QCheckBox
)
from PySide6.QtCore import Qt

class ServerEditDialog(QDialog):
    def __init__(self, parent=None, server: dict = None):
        super().__init__(parent)
        self.setWindowTitle("编辑服务器" if server else "新增服务器")
        self.server = server
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("服务器名称")
        form_layout.addRow("名称：", self.name_edit)

        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("例如：localhost")
        form_layout.addRow("主机名：", self.host_edit)

        self.port_edit = QLineEdit()
        self.port_edit.setPlaceholderText("默认：3306")
        self.port_edit.setText("3306")
        form_layout.addRow("端口：", self.port_edit)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("例如：root")
        form_layout.addRow("用户名：", self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("请输入密码")
        form_layout.addRow("密码：", self.password_edit)

        self.database_edit = QLineEdit()
        self.database_edit.setPlaceholderText("例如：emergency_scenarios")
        form_layout.addRow("数据库名：", self.database_edit)

        layout.addLayout(form_layout)

        # 显示密码复选框
        self.show_password_checkbox = QCheckBox("显示密码")
        self.show_password_checkbox.stateChanged.connect(self.toggle_password_visibility)
        layout.addWidget(self.show_password_checkbox)

        # 按钮区域
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存")
        self.cancel_button = QPushButton("取消")
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # 连接信号与槽
        self.save_button.clicked.connect(self.save)
        self.cancel_button.clicked.connect(self.reject)

        # 如果是编辑模式，填充已有数据
        if self.server:
            self.name_edit.setText(self.server.get('name', ''))
            self.host_edit.setText(self.server.get('host', ''))
            self.port_edit.setText(str(self.server.get('port', '3306')))
            self.username_edit.setText(self.server.get('username', ''))
            self.password_edit.setText(self.server.get('password', ''))
            self.database_edit.setText(self.server.get('database', ''))

    def toggle_password_visibility(self, state):
        if state == Qt.Checked:
            self.password_edit.setEchoMode(QLineEdit.Normal)
        else:
            self.password_edit.setEchoMode(QLineEdit.Password)

    def save(self):
        name = self.name_edit.text().strip()
        host = self.host_edit.text().strip()
        port = self.port_edit.text().strip()
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        database = self.database_edit.text().strip()

        if not name or not host or not port or not username or not database:
            QMessageBox.warning(self, "警告", "请填写所有必填字段。")
            return

        try:
            port = int(port)
        except ValueError:
            QMessageBox.warning(self, "警告", "端口号必须是数字。")
            return

        self.server_data = {
            'name': name,
            'host': host,
            'port': port,
            'username': username,
            'password': password,
            'database': database
        }
        self.accept()

    def get_server_data(self) -> dict:
        return self.server_data