# -*- coding: utf-8 -*-
# @Time    : 2025/3/19 19:34
# @FileName: llm_dialog.py
# @Software: PyCharm
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
                               QTextEdit, QPushButton, QLabel, QCheckBox,
                               QApplication, QFrame, QDialog, QProgressBar)
from PySide6.QtCore import Qt, Slot, QThread, Signal
from PySide6.QtGui import QFont, QTextCursor
import sys
import datetime
import re
import markdown2


from utils.get_config import get_cfg
from utils.llm_client import FallbackManager
from views.dialogs.custom_warning_dialog import CustomWarningDialog


# 创建一个线程类来处理LLM请求，避免UI卡顿
class LLMRequestThread(QThread):
    # 定义信号，用于返回处理结果
    response_received = Signal(str, str)  # 参数：响应文本, 模型名称
    error_occurred = Signal(str)  # 参数：错误信息

    def __init__(self, fallback_manager, model, prompt):
        super().__init__()
        self.fallback_manager = fallback_manager
        self.model = model
        self.prompt = prompt

    def run(self):
        try:
            # 调用API获取响应
            response = self.fallback_manager.get_response_with_fallback(self.model, self.prompt)

            # 检查是否使用了备选模型
            actual_model = self.model
            fallback_prefix = self.tr("[使用备选模型")

            if response and fallback_prefix in response:
                try:
                    # 使用翻译后的前缀创建正则表达式
                    pattern = re.escape(fallback_prefix) + r" ([^\s]+)"
                    match = re.search(pattern, response)
                    if match:
                        actual_model = match.group(1)
                except:
                    pass

            # 发送响应信号
            self.response_received.emit(response, actual_model)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(str(e))


class FlatButton(QPushButton):
    """扁平化按钮"""

    def __init__(self, text, parent=None, primary=False):
        super().__init__(text, parent)
        # if primary:
        #     self.setStyleSheet("""
        #         QPushButton {
        #             background-color: #5468FF;
        #             color: white;
        #             border-radius: 4px;
        #             padding: 8px 20px;
        #             font-weight: 500;
        #             border: none;
        #         }
        #         QPushButton:hover {
        #             background-color: #4454DB;
        #         }
        #         QPushButton:pressed {
        #             background-color: #3342CB;
        #         }
        #         QPushButton:disabled {
        #             background-color: #CDD4FF;
        #             color: #E9EBFF;
        #         }
        #     """)
        # else:
        #     self.setStyleSheet("""
        #         QPushButton {
        #             background-color: #F0F0F0;
        #             color: #303030;
        #             border-radius: 4px;
        #             padding: 8px 20px;
        #             font-weight: 400;
        #             border: none;
        #         }
        #         QPushButton:hover {
        #             background-color: #E5E5E5;
        #         }
        #         QPushButton:pressed {
        #             background-color: #D8D8D8;
        #             color: #404040;
        #         }
        #         QPushButton:disabled {
        #             background-color: #F8F8F8;
        #             color: #CCCCCC;
        #         }
        #     """)


class AskLLM(QDialog):
    """
    模仿Claude风格的智能问答界面
    - 简洁的顶部导航
    - 一体化的消息流
    - 柔和的色彩方案
    """

    def __init__(self, parent=None, plan_data=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("AI 智能问答"))
        self.parent = parent
        self.resize(900, 700)

        # 设置应用全局样式
        self.apply_claude_style()
        self.plan_data = plan_data

        # 当前预案内容
        self.contingency_plan = self.plan_data

        self.config = get_cfg()['llm']

        self.fallback_manager = FallbackManager(self.config)

        # 可用模型
        self.models = [item['model_name'] for item in self.config['model_list']]

        # 当前处理请求的线程
        self.request_thread = None

        # 初始化界面
        self.init_ui()

        # 设置默认选中的模型 - 修改为选择第一个模型
        self.set_default_model()

        # 打印启动信息
        print("[系统启动] AI 智能问答系统已初始化")

    def set_default_model(self):
        """设置默认选中的模型"""
        default_model = self.config.get('default_model')

        # 如果找到配置中的默认模型，则使用它
        if default_model in self.models:
            default_index = self.models.index(default_model)
        else:
            # 如果找不到配置的默认模型，或者配置中没有指定，默认选择第一个模型
            default_index = 0
            print(f"[警告] 配置中的默认模型 '{default_model}' 不在可用模型列表中，默认选择第一个模型")

        # 设置下拉框选中的项
        self.model_combo.setCurrentIndex(default_index)
        # 更新状态栏显示
        selected_model = self.models[default_index]
        self.status_label.setText(self.tr("已选择模型: {0}").format(selected_model))
        print(f"[默认模型] 已设置默认模型: {selected_model}")

    def apply_claude_style(self):
        """应用Claude风格的主题样式"""
        self.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                color: #1A1A1A;
                font-family: 'Microsoft YaHei UI', 'Segoe UI';
                font-size: 14px;
            }

            QTextEdit {
                border: 1px solid #E5E5E5;
                border-radius: 4px;
                background-color: white;
                padding: 12px;
                selection-background-color: #EFEFFF;
                line-height: 150%;
            }
            QTextEdit:focus {
                border: 1px solid #5468FF;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #D1D1D1;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #5468FF;
                border: 1px solid #5468FF;
            }
            QLabel {
                color: #4A4A4A;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #F7F7F7;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #E5E5E5;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #D1D1D1;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

    def init_ui(self):
        """初始化界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 顶部导航区域 (简化的顶部栏，类似Claude)
        top_bar = QWidget()
        top_bar.setFixedHeight(56)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 5, 16, 5)

        # 模型选择
        model_layout = QHBoxLayout()
        model_label = QLabel(self.tr("选择智能模型:"))

        self.model_combo = QComboBox()
        self.model_combo.addItems(self.models)
        self.model_combo.currentIndexChanged.connect(self.model_changed)

        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)

        top_layout.addLayout(model_layout)
        top_layout.addStretch()

        # 预案复选框
        contingency_layout = QHBoxLayout()
        if self.plan_data == None:
            contingency_label = QLabel(self.tr("无可用预案信息"))
        else:
            contingency_label = QLabel(self.tr("附带预案信息:"))
        contingency_label.setStyleSheet("font-weight: 400; color: #606060;")

        self.contingency_check = QCheckBox()
        self.contingency_check.setStyleSheet("""
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #D1D1D1;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #5dade2;
                border: 1px solid #5468FF;
            }
        """)
        if self.plan_data == None:
            # 隐藏
            self.contingency_check.setVisible(False)
        self.contingency_check.stateChanged.connect(self.contingency_toggled)

        contingency_layout.addWidget(contingency_label)
        contingency_layout.addWidget(self.contingency_check)

        top_layout.addLayout(contingency_layout)

        main_layout.addWidget(top_bar)
        # 分隔线 - 非常微妙的分隔线
        separator_first = QFrame()
        separator_first.setFrameShape(QFrame.HLine)
        separator_first.setFrameShadow(QFrame.Plain)
        separator_first.setStyleSheet("background-color: #EEEEEE; border: none; height: 1px;")

        main_layout.addWidget(separator_first)

        # 聊天内容区域 - Claude风格的干净界面
        chat_container = QWidget()
        chat_container.setObjectName("chatContainer")
        chat_container.setStyleSheet("#chatContainer { background-color: #FFFFFF; }")
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(16, 16, 16, 16)
        chat_layout.setSpacing(0)

        # 聊天历史显示区
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setPlaceholderText(self.tr("对话内容将显示在这里..."))

        # 设置聊天历史样式
        self.chat_history.setStyleSheet("""
            QTextEdit {
                border: none;
                border-radius: 0px;
                background-color: white;
                padding: 8px;
                font-size: 14px;
                line-height: 1.4;
            }
        """)

        self.chat_history.setFrameShape(QFrame.NoFrame)
        self.chat_history.setAcceptRichText(True)
        self.chat_history.setTextInteractionFlags(Qt.TextBrowserInteraction)

        # 设置文档样式
        document = self.chat_history.document()
        document.setDocumentMargin(8)  # 设置文档外边距

        chat_layout.addWidget(self.chat_history, 1)

        main_layout.addWidget(chat_container, 1)

        separator_second = QFrame()
        separator_second.setFrameShape(QFrame.HLine)
        separator_second.setFrameShadow(QFrame.Plain)
        separator_second.setStyleSheet("background-color: #EEEEEE; border: none; height: 1px;")

        main_layout.addWidget(separator_second)

        # 输入区域 - Claude风格的简洁输入区
        input_container = QWidget()
        input_container.setObjectName("inputContainer")
        input_container.setStyleSheet("#inputContainer { background-color: #FFFFFF; }")
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(16, 16, 16, 16)
        input_layout.setSpacing(8)

        # 输入框和按钮组
        input_row = QHBoxLayout()
        input_row.setSpacing(12)

        # 文本输入 - 更大的输入框
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText(self.tr("在此输入您的问题..."))
        self.input_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E5E5E5;
                border-radius: 8px;
                background-color: white;
                padding: 12px 16px;
                font-size: 14px;
                line-height: 150%;
            }
            QTextEdit:focus {
    border: 1px solid #5dade2; /* 浅蓝色 */
}
        """)
        self.input_text.setMinimumHeight(80)
        self.input_text.setMaximumHeight(120)
        input_row.addWidget(self.input_text, 1)

        # 按钮组 - Claude风格的按钮
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(8)

        self.send_btn = FlatButton(self.tr("发送"), primary=True)
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setShortcut(Qt.Key_Return | Qt.KeyboardModifier.ControlModifier)
        self.send_btn.setFixedWidth(110)
        self.send_btn.setCursor(Qt.PointingHandCursor)

        self.clear_btn = FlatButton(self.tr("清空"))
        self.clear_btn.clicked.connect(self.clear_chat)
        self.clear_btn.setFixedWidth(110)
        self.clear_btn.setCursor(Qt.PointingHandCursor)

        btn_layout.addWidget(self.send_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()

        input_row.addLayout(btn_layout)
        input_layout.addLayout(input_row)

        # 进度显示（隐藏状态）
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(0)  # 设置为0表示不确定进度
        self.progress_bar.setMinimum(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #F5F5F5;
            }
            QProgressBar::chunk {
                background-color: #5dade2;
            }
        """)
        self.progress_bar.hide()  # 初始状态隐藏
        input_layout.addWidget(self.progress_bar)

        # 移除此处的提示文本
        # hint_label = QLabel("提示: 按 Ctrl+Enter 快捷发送")
        # hint_label.setStyleSheet("color: #909090; font-size: 12px;")
        # hint_label.setAlignment(Qt.AlignRight)
        # input_layout.addWidget(hint_label)

        main_layout.addWidget(input_container)

        # 状态栏 - 轻量的状态栏，添加右侧的提示信息
        status_bar = QWidget()
        status_bar.setFixedHeight(30)
        status_bar.setStyleSheet("background-color: #FAFAFA;")
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(16, 0, 16, 0)

        self.status_label = QLabel(self.tr("已选择模型: ") + (self.models[0] if self.models else self.tr("无可用模型")))
        self.status_label.setStyleSheet("color: #909090; font-size: 12px;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        # 添加到状态栏右侧的提示文本
        hint_label = QLabel(self.tr("提示: 按 Ctrl+Enter 快捷发送"))
        hint_label.setStyleSheet("color: #909090; font-size: 12px;")
        status_layout.addWidget(hint_label)

        main_layout.addWidget(status_bar)

    @Slot()
    def model_changed(self, index):
        """模型选择变更"""
        model = self.models[index]
        self.status_label.setText(self.tr("已选择模型: {0}").format(model))
        print(f"[模型选择] 用户选择了模型: {model}")

    @Slot()
    def contingency_toggled(self, state):
        """预案选项切换"""
        is_checked = (state == 2)
        status = "启用" if is_checked else "禁用"
        print(f"[预案状态] 预案信息已{status}")
        if is_checked:
            self.show_plan_info_window()

    def show_plan_info_window(self):
        """显示预案信息的新窗口"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout, QWidget
        from PySide6.QtCore import Qt

        # 创建一个对话框
        plan_dialog = QDialog(self)
        plan_dialog.setWindowTitle(self.tr("预案详情 - ") + next(iter(self.contingency_plan.values()))['plan_name'])
        plan_dialog.resize(700, 500)

        # 设置对话框样式
        plan_dialog.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 1px solid #CCCCCC;
            }
        """)

        # 创建布局
        layout = QVBoxLayout(plan_dialog)

        # 创建文本浏览器来显示HTML内容
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setStyleSheet("""
            QTextBrowser {
        border: 1px solid #5dade2;
    }
        QScrollBar:horizontal {
            border: none;
            background: #f1f1f1;
            height: 8px;
            margin: 0px;
        }
        QScrollBar::handle:horizontal {
            background: #c1c1c1;
            min-width: 20px;
            border-radius: 4px;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
            subcontrol-origin: margin;
        }
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
        }
                QScrollBar:vertical {
            border: none;
            background: #f1f1f1;
            width: 8px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: #c1c1c1;
            min-height: 20px;
            border-radius: 4px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
            subcontrol-origin: margin;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
    """)

        # 将预案数据格式化为HTML
        html_content = self.generate_plan_info_html(self.contingency_plan)

        # 设置HTML文本
        text_browser.setHtml(html_content)

        # 添加到布局
        layout.addWidget(text_browser)

        # 添加确定按钮
        button_layout = QHBoxLayout()
        bottom_widget = QWidget()
        bottom_widget.setFixedHeight(60)
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 10, 0, 10)

        # 确定按钮
        confirm_btn = QPushButton(self.tr("确定"))
        confirm_btn.setFixedWidth(110)
        confirm_btn.clicked.connect(plan_dialog.accept)

        # 添加按钮到底部布局，居中显示
        bottom_layout.addStretch()
        bottom_layout.addWidget(confirm_btn)
        bottom_layout.addStretch()

        # 添加底部控件到主布局
        layout.addWidget(bottom_widget)

        # 显示对话框（模态，需要用户确认后才能继续）
        plan_dialog.setModal(True)
        plan_dialog.show()

    def generate_plan_info_html(self, plan_data):
        """将预案数据格式化为HTML格式，参考预案详情样式"""
        info_html = """
        <html><head><style>
         body{font-family:"Microsoft YaHei";font-size:14px;color:#333;padding:15px;background-color:#fff;border:1px solid #0078d7;border-radius:3px}
         h2{text-align:center;color:#0078d7;margin-bottom:20px}
         h3{color:#0078d7;font-size:18px;margin-top:30px;margin-bottom:15px;font-weight:bold}
         .timestamp{color:#666;font-size:12px;text-align:right;margin-bottom:20px}
         table{width:100%;border-collapse:collapse;margin-bottom:20px;table-layout:fixed}
         th,td{border:1px solid #ccc;padding:10px;text-align:center}
         th{background-color:#f0f0f0;color:#333}
         .no-resource{color:red;font-style:italic;text-align:center}
         .simulation-results{margin-top:20px;margin-bottom:20px}
         .section-title{font-weight:bold;margin-top:15px;color:#0078d7;font-size:16px}
         .plan-content{padding:20px}
        </style></head><body>
        <div class="plan-content">
        """

        if not plan_data:
            info_html += "<h2>无预案数据可显示</h2></body></html>"
            return info_html

        for plan_id, plan in plan_data.items():
            info_html += f"<h2>{plan['plan_name']}</h2>"
            create_time_str = self.tr('创建时间') + ": " + plan.get('timestamp', '')
            info_html += f"<div class='timestamp'>{create_time_str}</div>"

            # 应急行动部分
            for i, action in enumerate(plan.get('emergency_actions', []), 1):
                implementation_status = self.tr('已实施') if action.get('implementation_status') == 'True' else self.tr(
                    '未实施')
                title_str = f"{self.tr('应急行为')} {i}: {action.get('action_type', '')} ({implementation_status})"
                info_html += f"<h3>{title_str}</h3>"

                info_html += f"<p><b>{self.tr('时长')}:</b> {action.get('duration', '')}</p>"

                info_html += f"<div class='section-title'>{self.tr('资源列表')}:</div>"
                if action.get('resources'):
                    info_html += """
                    <table>
                    <tr>
                        <th width="20%">""" + self.tr('资源名称') + """</th>
                        <th width="15%">""" + self.tr('类型') + """</th>
                        <th width="10%">""" + self.tr('数量') + """</th>
                        <th width="55%">""" + self.tr('位置') + """</th>
                    </tr>
                    """
                    for resource in action['resources']:
                        info_html += f"""
                        <tr>
                            <td>{resource.get('resource_type', '')}</td>
                            <td>{resource.get('resource_category', '')}</td>
                            <td>{resource.get('quantity', '')}</td>
                            <td>{resource.get('location', '')}</td>
                        </tr>
                        """
                    info_html += "</table>"
                else:
                    info_html += f"<p class='no-resource'>{self.tr('无资源')}</p>"

            # 推演结果部分
            info_html += f"<h3>{self.tr('推演结果')}</h3>"
            sim_results = plan.get('simulation_results', {})
            if sim_results:
                info_html += """
                <table class="simulation-results">
                <tr>
                    <th width="33%">""" + self.tr('阶段') + """</th>
                    <th width="33%">""" + self.tr('较好结果') + """</th>
                    <th width="34%">""" + self.tr('较差结果') + """</th>
                </tr>
                <tr>
                    <td>""" + self.tr('推演前') + """</td>
                    <td>""" + str(sim_results.get('推演前-较好', '')) + """</td>
                    <td>""" + str(sim_results.get('推演前-较差', '')) + """</td>
                </tr>
                <tr>
                    <td>""" + self.tr('推演后') + """</td>
                    <td>""" + str(sim_results.get('推演后-较好', '')) + """</td>
                    <td>""" + str(sim_results.get('推演后-较差', '')) + """</td>
                </tr>
                </table>
                """
            else:
                info_html += f"<p class='no-resource'>{self.tr('无推演结果')}</p>"

        info_html += "</div></body></html>"
        return info_html

    def add_chat_message(self, sender, timestamp, content, sender_color="#303030"):
        """
        直接添加聊天消息到历史记录，精确控制空行，不添加分隔线

        参数:
        sender: 发送者名称
        timestamp: 时间戳
        content: 消息内容
        sender_color: 发送者名称的颜色
        is_model: 是否是模型消息（决定是否在消息前添加空行）
        """
        # 获取当前文档
        document = self.chat_history.document()

        # 创建光标并移动到文档末尾
        cursor = QTextCursor(document)
        cursor.movePosition(QTextCursor.End)

        # 如果是模型消息且文档不为空，添加一个空行
        if not document.isEmpty():
            cursor.insertBlock()
            cursor.insertBlock()

        # 插入发送者行（不使用div，直接控制文本）
        cursor.insertHtml(f'<span style="font-weight: 400; color: {sender_color};">{sender}</span> ')
        cursor.insertHtml(f'<span style="color: #909090; font-size: 12px;">{timestamp}</span>')

        # 将发送者和内容分开显示
        cursor.insertBlock()

        # 插入内容
        cursor.insertHtml(f'<span style="color: #303030;">{content}</span>')

        # 更新光标位置并滚动到末尾
        self.chat_history.setTextCursor(cursor)
        self.chat_history.ensureCursorVisible()

    def convert_markdown_to_html(self, text):
        """将Markdown文本转换为HTML"""
        # 保留原始样式，只进行基础Markdown转换
        try:
            html = markdown2.markdown(text, extras=["fenced-code-blocks", "tables", "code-friendly"])

            # 仅添加最基本的样式，保持与原有UI风格一致
            styled_html = f"""
            <style>
                code {{
                    background-color: #f6f8fa;
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-family: 'Microsoft YaHei UI', 'Segoe UI', monospace;
                }}
                pre {{
                    background-color: #f6f8fa;
                    padding: 8px;
                    border-radius: 4px;
                    overflow: auto;
                }}
                pre code {{
                    background-color: transparent;
                    padding: 0;
                }}
                table {{
                    border-collapse: collapse;
                    margin: 8px 0;
                }}
                th, td {{
                    border: 1px solid #dfe2e5;
                    padding: 6px 13px;
                }}
                blockquote {{
                    border-left: 3px solid #dfe2e5;
                    padding-left: 12px;
                    color: #6a737d;
                    margin: 8px 0;
                }}
            </style>
            {html}
            """
            return styled_html
        except Exception as e:
            print(f"Markdown转换错误: {str(e)}")
            return text  # 如果转换失败，返回原始文本

    @Slot()
    # 修改append_html_with_precise_spacing方法以更精确地控制空行
    def append_html_with_precise_spacing(self, html_content, add_spacing_before=False):
        """
        使用QTextCursor添加HTML内容，精确控制换行

        参数:
        html_content: 要添加的HTML内容
        add_spacing_before: 是否在内容前添加空行（用于用户消息和模型名之间的空行）
        """
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.End)

        # 如果需要在内容前添加空行（用户消息和模型名之间）
        if add_spacing_before:
            cursor.insertBlock()  # 插入空行

        # 插入HTML内容
        cursor.insertHtml(html_content)
        self.chat_history.setTextCursor(cursor)

        # 确保滚动到最新消息
        self.chat_history.ensureCursorVisible()

    # 修改send_message方法，确保用户消息和模型之间需要有空行
    def send_message(self):
        """发送当前消息到LLM"""
        user_input = self.input_text.toPlainText().strip()
        if not user_input:
            return

        # 禁用发送按钮，防止重复发送
        self.send_btn.setEnabled(False)

        selected_model = self.model_combo.currentText()

        # 打印调试信息
        print(f"\n[用户输入] {user_input}")

        # 添加用户消息到聊天历史
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        # 使用新方法添加用户消息
        self.add_chat_message(
            sender=get_cfg()['database']['username'],
            timestamp=timestamp,
            content=user_input,
            sender_color="#303030"
        )

        # 准备提示词
        # 如果启用了预案，添加预案信息
        if self.contingency_check.isChecked():
            # 格式化预案数据成可读字符串
            formatted_plan_data = self.format_plan_data(self.contingency_plan)

            # 使用配置中的带预案提示词模板
            prompt = self.config['prompt_with_plan_data'].format(
                plan_data=formatted_plan_data,
                user_input=user_input
            )
            print(f"[调试信息] 附带预案的完整提示词: {prompt}")
        else:
            # 使用配置中的无预案提示词模板
            prompt = self.config['prompt_without_plan_data'].format(
                user_input=user_input
            )
            print(f"[调试信息] 不附带预案的提示词: {prompt}")

        # 更新状态和显示进度条
        self.status_label.setText(self.tr("正在处理请求... 使用模型: {0}").format(selected_model))
        self.progress_bar.show()
        QApplication.processEvents()

        # 创建并启动工作线程
        self.request_thread = LLMRequestThread(self.fallback_manager, selected_model, prompt)
        self.request_thread.response_received.connect(self.handle_response)
        self.request_thread.error_occurred.connect(self.handle_error)
        self.request_thread.finished.connect(self.thread_finished)
        self.request_thread.start()

        # 清空输入框
        self.input_text.clear()

    def handle_response(self, response, actual_model):
        """处理从线程收到的响应"""
        if response is None:
            response = self.tr("抱歉，无法获取AI响应。请检查网络连接或稍后再试。")

            error_dialog = CustomWarningDialog(
                self.tr("请求失败"),
                self.tr("无法获取AI响应。您可以尝试以下解决方法:\n\n"
                "1. 检查网络连接是否正常\n"
                "2. 确认API密钥是否有效\n"
                "3. 稍后再试，API服务可能暂时不可用")
            )
            error_dialog.exec()
        # 模型颜色和处理Markdown格式
        model_colors = {}
        for item in self.config['model_list']:
            model_color = item.get('model_color', "#5468FF")
            model_colors[item['model_name']] = model_color

        model_color = model_colors.get(actual_model, "#5468FF")

        # 处理备选模型标记和Markdown转换的代码保持不变
        response_content = response
        prefix = ""

        fallback_prefix_translated = self.tr("[使用备选模型")

        if response and fallback_prefix_translated in response:
            pattern = re.escape(fallback_prefix_translated) + r"[^\]]+\].*?\n\n"

            match = re.search(pattern, response, re.DOTALL)
            if match:
                prefix = match.group(0)
                response_content = response[match.end():]


        # 转换Markdown为HTML
        html_content = self.convert_markdown_to_html(response_content)

        # 完整的回复内容（包括前缀和HTML内容）
        full_content = f"{prefix}{html_content}"

        # 显示响应
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        # 使用新方法添加模型消息
        self.add_chat_message(
            sender=actual_model,
            timestamp=timestamp,
            content=full_content,
            sender_color=model_color
        )

        # 恢复状态
        self.status_label.setText(self.tr("已选择模型: {0}").format(self.model_combo.currentText()))
        self.progress_bar.hide()

    def handle_error(self, error_message):
        """处理线程中的错误"""
        response = f"处理请求时发生错误: {error_message}"

        # 显示错误消息
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        # 使用新方法添加错误消息
        self.add_chat_message(
            sender=self.tr("系统"),
            timestamp=timestamp,
            content=response,
            sender_color="#FF5555"
        )

        # 恢复状态
        self.status_label.setText(self.tr("已选择模型: {0}").format(self.model_combo.currentText()))
        self.progress_bar.hide()

    def thread_finished(self):
        """线程完成时的处理"""
        # 重新启用发送按钮
        self.send_btn.setEnabled(True)
        # 清理资源
        if self.request_thread:
            self.request_thread = None

    def format_plan_data(self, plan_data):
        """将预案数据格式化为易读的字符串"""
        formatted = ""
        for plan_id, plan in plan_data.items():
            formatted += f"预案名称: {plan['plan_name']}\n"
            formatted += "应急行动:\n"

            for i, action in enumerate(plan['emergency_actions'], 1):
                formatted += f"{i}. 类型: {action['action_type']}, 持续时间: {action['duration']}, 已实施: {action['implementation_status']}\n"
                formatted += "   资源:\n"
                for j, resource in enumerate(action['resources'], 1):
                    formatted += f"   {j}. {resource['resource_type']} - {resource['resource_category']}, 数量: {resource['quantity']}, 位置: {resource['location']}\n"

            formatted += "推演结果:\n"
            sim_results = plan['simulation_results']
            formatted += f"- 推演前: 较好 {sim_results['推演前-较好']}, 较差 {sim_results['推演前-较差']}\n"
            formatted += f"- 推演后: 较好 {sim_results['推演后-较好']}, 较差 {sim_results['推演后-较差']}\n"
            formatted += f"创建时间: {plan['timestamp']}\n\n"

        return formatted

    def get_llm_response(self, model, prompt):
        """
        将提示发送到所选LLM并处理响应
        使用FallbackManager处理API调用和故障转移
        注意：此方法现在实际上不会被直接调用，而是由线程处理
        """
        try:
            # 调用API获取响应
            response = self.fallback_manager.get_response_with_fallback(model, prompt)
            return response, model
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"处理请求时发生错误: {str(e)}", "错误"

    @Slot()
    def clear_chat(self):
        """清空聊天历史"""
        self.chat_history.clear()
        print("[操作] 聊天历史已清空")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AskLLM()
    window.show()
    sys.exit(app.exec())