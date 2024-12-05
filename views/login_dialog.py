# -*- coding: utf-8 -*-
# @Time    : 12/5/2024 10:44 AM
# @FileName: login_dialog.py
# @Software: PyCharm
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QMessageBox, QLineEdit, QHBoxLayout, QPushButton, QCheckBox, QDialog, QVBoxLayout, \
    QFormLayout, QListWidget, QLabel, QInputDialog, QListWidgetItem

from controllers.server_manager import ServerManager



# views/login_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QListWidgetItem, QLabel,
    QMessageBox, QLineEdit, QFormLayout
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QIcon, QAction
from controllers.server_manager import ServerManager
import os

class LoginDialog(QDialog):
    login_success = Signal()

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("连接数据库")
        self.db_manager = db_manager
        self.server_manager = ServerManager()  # 使用默认路径
        self.init_ui()
        self.apply_styles()


    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # 服务器列表区域
        server_list_layout = QVBoxLayout()
        self.server_list = QListWidget()
        self.populate_server_list()

        server_list_layout.addWidget(QLabel("已保存的服务器："))
        server_list_layout.addWidget(self.server_list)

        # 服务器管理按钮
        server_button_layout = QHBoxLayout()
        self.add_server_button = QPushButton("新增")
        self.edit_server_button = QPushButton("编辑")
        self.delete_server_button = QPushButton("删除")
        server_button_layout.addWidget(self.add_server_button)
        server_button_layout.addWidget(self.edit_server_button)
        server_button_layout.addWidget(self.delete_server_button)
        server_list_layout.addLayout(server_button_layout)

        # 连接按钮
        self.connect_button = QPushButton("连接到选中的服务器")
        self.connect_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff; /* 白色背景 */
                color: #000000; /* 黑色文字 */
                border: 1px solid #bdc3c7; /* 浅灰色边框 */
                padding: 8px 16px; /* 内边距 */
                border-radius: 5px; /* 圆角 */
            }
            QPushButton:hover {
                background-color: #f0f4f7; /* 浅灰色悬停效果 */
            }
            QPushButton:pressed {
                background-color: #e0e0e0; /* 按下时更深的灰色 */
            }
        """)
        server_list_layout.addWidget(self.connect_button)

        # 直接连接按钮
        self.direct_connect_button = QPushButton("直接连接")
        self.direct_connect_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff; /* 白色背景 */
                color: #000000; /* 黑色文字 */
                border: 1px solid #bdc3c7; /* 浅灰色边框 */
                padding: 8px 16px; /* 内边距 */
                border-radius: 5px; /* 圆角 */
            }
            QPushButton:hover {
                background-color: #f0f4f7; /* 浅灰色悬停效果 */
            }
            QPushButton:pressed {
                background-color: #e0e0e0; /* 按下时更深的灰色 */
            }
        """)
        server_list_layout.addWidget(self.direct_connect_button)

        main_layout.addLayout(server_list_layout)

        # 连接信号与槽
        self.add_server_button.clicked.connect(self.add_server)
        self.edit_server_button.clicked.connect(self.edit_server)
        self.delete_server_button.clicked.connect(self.delete_server)
        self.connect_button.clicked.connect(self.connect_selected_server)
        self.direct_connect_button.clicked.connect(self.open_manual_connect_dialog)
        self.server_list.itemDoubleClicked.connect(self.connect_selected_server)
        self.add_server_button.setFocus()  # 设置焦点到“新增”按钮

    def apply_styles(self):
        # 加载QSS文件
        styles_dir = os.path.join(os.path.dirname(__file__), "..", "resources", "styles")
        qss_file = os.path.join(styles_dir, "login_dialog.qss")
        if os.path.exists(qss_file):
            with open(qss_file, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        else:
            print(f"QSS文件不存在: {qss_file}")

    def populate_server_list(self):
        self.server_list.clear()
        for server in self.server_manager.get_all_servers():
            item = QListWidgetItem(server['name'])
            item.setData(Qt.UserRole, server['id'])
            self.server_list.addItem(item)
        # 不选择任何项
        self.server_list.setCurrentItem(None)

    def add_server(self):
        dialog = ServerEditDialog(self)
        if dialog.exec() == QDialog.Accepted:
            server_data = dialog.get_server_data()
            self.server_manager.add_server(server_data)
            self.populate_server_list()

    def edit_server(self):
        selected_item = self.server_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "警告", "请先选择要编辑的服务器。")
            return
        server_id = selected_item.data(Qt.UserRole)
        server = self.server_manager.get_server(server_id)
        dialog = ServerEditDialog(self, server=server)
        if dialog.exec() == QDialog.Accepted:
            updated_data = dialog.get_server_data()
            self.server_manager.update_server(server_id, updated_data)
            self.populate_server_list()

    def delete_server(self):
        selected_item = self.server_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "警告", "请先选择要删除的服务器。")
            return
        server_id = selected_item.data(Qt.UserRole)
        server = self.server_manager.get_server(server_id)
        confirm = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除服务器 '{selected_item.text()}' 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            success = self.server_manager.delete_server(server_id)
            if success:
                self.populate_server_list()
            else:
                QMessageBox.critical(self, "错误", "删除服务器失败。")

    def connect_selected_server(self):
        selected_item = self.server_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "警告", "请先选择一个服务器。")
            return
        server_id = selected_item.data(Qt.UserRole)
        server = self.server_manager.get_server(server_id)
        if not server:
            QMessageBox.critical(self, "错误", "未找到选中的服务器。")
            return

        if server.get('save_password') and 'password' in server and server['password']:
            password = server['password']
        else:
            # 如果未保存密码，弹出输入密码的对话框
            dialog = PasswordInputDialog(server['name'], self)
            if dialog.exec() == QDialog.Accepted:
                password = dialog.get_password()
            else:
                QMessageBox.warning(self, "警告", "未输入密码，无法连接。")
                return

            # 询问是否保存密码
            save_password = False
            dialog = SavePasswordDialog(self)
            if dialog.exec() == QDialog.Accepted:
                save_password = dialog.get_save_password()
            else:
                save_password = False

            # 更新服务器数据
            updated_data = {
                'save_password': save_password,
                'password': password if save_password else ''
            }
            self.server_manager.update_server(server_id, updated_data)

        success, message = self.db_manager.connect(
            server['username'],
            password,
            server['host'],
            server['port'],
            server['database']
        )
        if success:
            QMessageBox.information(self, "成功", message)
            self.login_success.emit()
            self.accept()
        else:
            QMessageBox.critical(self, "连接失败", f"无法连接到数据库：{message}")

    def open_manual_connect_dialog(self):
        dialog = ManualConnectDialog(self.db_manager, self)
        if dialog.exec() == QDialog.Accepted:
            QMessageBox.information(self, "成功", "已成功连接到数据库。")
            self.login_success.emit()
            self.accept()
        else:
            QMessageBox.warning(self, "连接取消", "直接连接已取消。")


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
        form_layout.addRow("端口：", self.port_edit)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("例如：root")
        form_layout.addRow("用户名：", self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("请输入密码")
        form_layout.addRow("密码：", self.password_edit)

        self.database_edit = QLineEdit()
        self.database_edit.setPlaceholderText("例如：test")
        form_layout.addRow("数据库名：", self.database_edit)

        self.save_password_checkbox = QCheckBox("")
        form_layout.addRow("保存密码：", self.save_password_checkbox)

        layout.addLayout(form_layout)

        # 添加眼睛图标按钮用于显示/隐藏密码
        self.toggle_password_action = QAction(self)
        eye_open_icon_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'icons', 'eye.png')
        eye_closed_icon_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'icons', 'eye_off.png')

        # 确保图标文件存在
        if os.path.exists(eye_open_icon_path) and os.path.exists(eye_closed_icon_path):
            eye_open_icon = QIcon(eye_open_icon_path)
            eye_closed_icon = QIcon(eye_closed_icon_path)
        else:
            # 使用默认图标或文本代替
            eye_open_icon = QIcon()
            eye_closed_icon = QIcon()

        self.password_visible = False
        self.toggle_password_action.setIcon(eye_closed_icon)
        self.password_edit.addAction(self.toggle_password_action, QLineEdit.TrailingPosition)
        self.toggle_password_action.triggered.connect(lambda: self.toggle_password_visibility(eye_open_icon, eye_closed_icon))

        # 按钮区域
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存")
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff; /* 白色背景 */
                color: #000000; /* 黑色文字 */
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                transition: background-color 0.3s ease, transform 0.1s ease;
            }
            QPushButton:hover {
                background-color: #f0f4f7; /* 浅灰色悬停效果 */
            }
            QPushButton:pressed {
                background-color: #e0e0e0; /* 按下时更深的灰色 */
            }
        """)
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
            self.database_edit.setText(self.server.get('database', ''))
            if self.server.get('save_password') and 'password' in self.server and self.server['password']:
                self.save_password_checkbox.setChecked(True)
                self.password_edit.setText(self.server['password'])

    def toggle_password_visibility(self, eye_open_icon, eye_closed_icon):
        if self.password_visible:
            self.password_edit.setEchoMode(QLineEdit.Password)
            self.toggle_password_action.setIcon(eye_closed_icon)
            self.password_visible = False
        else:
            self.password_edit.setEchoMode(QLineEdit.Normal)
            self.toggle_password_action.setIcon(eye_open_icon)
            self.password_visible = True

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
            'database': database,
            'save_password': self.save_password_checkbox.isChecked(),
            'password': password if self.save_password_checkbox.isChecked() else ''
        }
        self.accept()

    def get_server_data(self) -> dict:
        return self.server_data


class ManualConnectDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("直接连接数据库")
        self.db_manager = db_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("例如：localhost")
        form_layout.addRow("主机名：", self.host_edit)

        self.port_edit = QLineEdit()
        self.port_edit.setPlaceholderText("默认：3306")
        form_layout.addRow("端口：", self.port_edit)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("例如：root")
        form_layout.addRow("用户名：", self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("请输入密码")
        form_layout.addRow("密码：", self.password_edit)

        self.database_edit = QLineEdit()
        self.database_edit.setPlaceholderText("例如：text")
        form_layout.addRow("数据库名：", self.database_edit)

        layout.addLayout(form_layout)

        # 添加眼睛图标按钮用于显示/隐藏密码
        self.toggle_password_action = QAction(self)
        eye_open_icon_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'icons', 'eye.png')
        eye_closed_icon_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'icons', 'eye_off.png')

        # 确保图标文件存在
        if os.path.exists(eye_open_icon_path) and os.path.exists(eye_closed_icon_path):
            eye_open_icon = QIcon(eye_open_icon_path)
            eye_closed_icon = QIcon(eye_closed_icon_path)
        else:
            # 使用默认图标或文本代替
            eye_open_icon = QIcon()
            eye_closed_icon = QIcon()

        self.password_visible = False
        self.toggle_password_action.setIcon(eye_closed_icon)
        self.password_edit.addAction(self.toggle_password_action, QLineEdit.TrailingPosition)
        self.toggle_password_action.triggered.connect(lambda: self.toggle_password_visibility(eye_open_icon, eye_closed_icon))

        # 按钮区域
        button_layout = QHBoxLayout()
        self.connect_button = QPushButton("连接")
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff; /* 白色背景 */
                color: #000000; /* 黑色文字 */
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                transition: background-color 0.3s ease, transform 0.1s ease;
            }
            QPushButton:hover {
                background-color: #f0f4f7; /* 浅灰色悬停效果 */
            }
            QPushButton:pressed {
                background-color: #e0e0e0; /* 按下时更深的灰色 */
            }
        """)
        button_layout.addStretch()
        button_layout.addWidget(self.connect_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # 连接信号与槽
        self.connect_button.clicked.connect(self.attempt_login)
        self.cancel_button.clicked.connect(self.reject)

    def toggle_password_visibility(self, eye_open_icon, eye_closed_icon):
        if self.password_visible:
            self.password_edit.setEchoMode(QLineEdit.Password)
            self.toggle_password_action.setIcon(eye_closed_icon)
            self.password_visible = False
        else:
            self.password_edit.setEchoMode(QLineEdit.Normal)
            self.toggle_password_action.setIcon(eye_open_icon)
            self.password_visible = True

    def attempt_login(self):
        host = self.host_edit.text().strip()
        port = self.port_edit.text().strip()
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        database = self.database_edit.text().strip()

        if not host or not port or not username or not database:
            QMessageBox.warning(self, "警告", "请填写所有必填字段。")
            return

        try:
            port = int(port)
        except ValueError:
            QMessageBox.warning(self, "警告", "端口号必须是数字。")
            return

        success, message = self.db_manager.connect(username, password, host, port, database)
        if success:
            QMessageBox.information(self, "成功", message)
            self.accept()
        else:
            QMessageBox.critical(self, "连接失败", f"无法连接到数据库：{message}")

class PasswordInputDialog(QDialog):
    def __init__(self, server_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("输入密码")
        self.server_name = server_name
        self.password = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 提示标签
        label = QLabel(f"请输入服务器 '{self.server_name}' 的密码：")
        layout.addWidget(label)

        # 密码输入框
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("请输入密码")
        layout.addWidget(self.password_edit)

        # 按钮布局
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("确定")
        self.cancel_button = QPushButton("取消")

        # 自定义按钮样式
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff; /* 白色背景 */
                color: #000000; /* 黑色文字 */
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                transition: background-color 0.3s ease, transform 0.1s ease;
            }
            QPushButton:hover {
                background-color: #f0f4f7; /* 浅灰色悬停效果 */
            }
            QPushButton:pressed {
                background-color: #e0e0e0; /* 按下时更深的灰色 */
            }
        """)

        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # 信号与槽
        self.ok_button.clicked.connect(self.accept_password)
        self.cancel_button.clicked.connect(self.reject)

    def accept_password(self):
        password = self.password_edit.text().strip()
        if not password:
            QMessageBox.warning(self, "警告", "密码不能为空！")
            return
        self.password = password
        self.accept()

    def get_password(self):
        return self.password

class SavePasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("保存密码")
        self.save_password = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 提示文字
        label = QLabel("是否保存密码以便下次自动连接？")
        layout.addWidget(label)

        # 按钮布局
        button_layout = QHBoxLayout()
        self.yes_button = QPushButton("是")
        self.no_button = QPushButton("否")

        # 设置按钮样式
        self.no_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff; /* 白色背景 */
                color: #000000; /* 黑色文字 */
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                transition: background-color 0.3s ease, transform 0.1s ease;
            }
            QPushButton:hover {
                background-color: #f0f4f7; /* 浅灰色悬停效果 */
            }
            QPushButton:pressed {
                background-color: #e0e0e0; /* 按下时更深的灰色 */
            }
        """)

        # 添加按钮到布局
        button_layout.addWidget(self.yes_button)
        button_layout.addWidget(self.no_button)
        layout.addLayout(button_layout)

        # 连接信号与槽
        self.yes_button.clicked.connect(self.accept_yes)
        self.no_button.clicked.connect(self.reject)

    def accept_yes(self):
        self.save_password = True
        self.accept()

    def get_save_password(self):
        return self.save_password