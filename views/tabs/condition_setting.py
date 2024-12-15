import os
import sys
from functools import partial
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QCheckBox, QHBoxLayout, QVBoxLayout,
    QGroupBox, QPushButton, QSizePolicy, QTableWidget, QTableWidgetItem,
    QDialog, QHeaderView, QStackedLayout, QSpinBox, QComboBox, QLineEdit,
    QListWidget, QTextBrowser, QStyleOptionViewItem, QStyledItemDelegate
)
from PySide6.QtCore import Qt, Signal, QEvent, QObject
from PySide6.QtGui import QFont, QPainter, QPen, QColor, QIcon

from views.dialogs.custom_information_dialog import CustomInformationDialog
from views.dialogs.custom_input_dialog import CustomInputDialog
from views.dialogs.custom_question_dialog import CustomQuestionDialog
from views.dialogs.custom_warning_dialog import CustomWarningDialog


class CenteredItemDelegate(QStyledItemDelegate):
    """自定义委托，使 QComboBox 的下拉项内容居中显示。"""

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignCenter


class NoWheelEventFilter(QObject):
    """事件过滤器，禁用滚轮事件。"""

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            return True  # 事件被过滤，不传递下去
        return super().eventFilter(obj, event)


def create_centered_combobox(enum_values, initial_value):
    """
    创建一个居中对齐的 QComboBox，并禁用滚轮事件。
    """
    combobox = QComboBox()
    combobox.addItem("<空>")
    for item in enum_values:
        combobox.addItem(item)

    if initial_value in enum_values:
        combobox.setCurrentText(initial_value)
    else:
        combobox.setCurrentText("<空>")

    # 使 QComboBox 可编辑，以便设置对齐方式
    combobox.setEditable(True)
    # 设置 lineEdit 为只读，防止用户输入新项
    combobox.lineEdit().setReadOnly(True)
    # 设置文本居中对齐
    combobox.lineEdit().setAlignment(Qt.AlignCenter)

    # 获取 QComboBox 的视图并应用自定义委托以居中显示下拉项
    view = combobox.view()
    delegate = CenteredItemDelegate(view)
    view.setItemDelegate(delegate)

    # 安装事件过滤器以禁用滚轮事件
    no_wheel_filter = NoWheelEventFilter(combobox)
    combobox.installEventFilter(no_wheel_filter)

    return combobox

class FullHeaderDelegate(QStyledItemDelegate):
    """
    自定义两行多级表头，保持原先多级表头的结构。
    额外需求：
      - row=0 col=1/4 ("推演前/推演后")去掉下边线
      - row=1 col=1..6 ("较好/中等/较差")去掉上边线
    """
    def paint(self, painter, option, index):
        r, c = index.row(), index.column()
        if r < 2:
            painter.save()
            painter.fillRect(option.rect, QColor("#f0f0f0"))

            if r == 0 and c == 0:
                # 斜杠 “韧性/预案”
                # 上边线(2px)，下边线(1px)
                pen_top = QPen(Qt.black, 2)
                painter.setPen(pen_top)
                painter.drawLine(option.rect.topLeft(), option.rect.topRight())

                pen_bottom = QPen(Qt.black, 1)
                painter.setPen(pen_bottom)
                painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())

                # 斜线
                painter.drawLine(option.rect.topLeft(), option.rect.bottomRight())

                # 上下文字
                topRect = option.rect.adjusted(0, 0, 0, -option.rect.height()//2)
                bottomRect = option.rect.adjusted(0, option.rect.height()//2, 0, 0)
                painter.drawText(topRect, Qt.AlignCenter, "韧性")
                painter.drawText(bottomRect, Qt.AlignCenter, "预案")

            elif r == 0 and c == 1:
                # “推演前”，去掉下边线
                pen_top = QPen(Qt.black, 2)
                painter.setPen(pen_top)
                painter.drawLine(option.rect.topLeft(), option.rect.topRight())
                # 不画下边线 => 去掉

                painter.drawText(option.rect, Qt.AlignCenter, "推演前")

            elif r == 0 and c == 4:
                # “推演后”，同理去掉下边线
                pen_top = QPen(Qt.black, 2)
                painter.setPen(pen_top)
                painter.drawLine(option.rect.topLeft(), option.rect.topRight())

                painter.drawText(option.rect, Qt.AlignCenter, "推演后")

            elif r == 0:
                # 其他被合并单元格不画线, 仅填充背景
                painter.fillRect(option.rect, QColor("#f0f0f0"))

            elif r == 1 and c in [1,2,3,4,5,6]:
                # 第二行“较好/中等/较差”，去掉上边线
                # 不画上边线
                pen_bottom = QPen(Qt.black, 1)
                painter.setPen(pen_bottom)
                painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
                text_map = {
                    1:"较好", 2:"中等", 3:"较差",
                    4:"较好", 5:"中等", 6:"较差"
                }
                painter.drawText(option.rect, Qt.AlignCenter, text_map[c])

            painter.restore()
        else:
            # row>=2 => 数据行
            super().paint(painter, option, index)


class CustomTableWidget(QTableWidget):
    def resizeEvent(self, event):
        super().resizeEvent(event)
        content_width = self.horizontalHeader().length()
        if content_width < 550:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        else:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

class ClickableLabel(QLabel):
    clicked = Signal()
    def mousePressEvent(self, event):
        self.clicked.emit()

class CustomCheckBoxWithLabel(QWidget):
    def __init__(self, label_text):
        super().__init__()
        self.init_ui(label_text)

    def init_ui(self, label_text):
        # 横向排布：复选框 + label + 时长
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0,0,0,0)

        self.checkbox = QCheckBox()
        self.checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.label = ClickableLabel(label_text)
        self.label.setStyleSheet("cursor: pointer;color: black;font-weight: normal;")
        self.label.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(0,10000)
        self.duration_spin.setSuffix(" 分钟")
        self.duration_spin.setEnabled(False)
        self.duration_spin.setStyleSheet("background-color: #eee;")

        self.duration_spin.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.checkbox)
        layout.addWidget(self.label)
        layout.addWidget(QLabel("时长:"))
        layout.addWidget(self.duration_spin)

    def set_selected(self, selected):
        font = self.label.font()
        if selected:
            # Bold + 蓝色
            font.setBold(True)
            self.label.setFont(font)
            self.label.setStyleSheet("font-weight: bold; color: #5dade2; cursor: pointer;")

            # 开启 spinbox 并设置白色背景
            self.duration_spin.setEnabled(True)
            self.duration_spin.setStyleSheet("background-color: white;")
        else:
            # 普通 + 黑色
            font.setBold(False)
            self.label.setFont(font)
            self.label.setStyleSheet("font-weight: normal; color: black; cursor: pointer;")

            # 禁用 spinbox 并设置灰色背景
            self.duration_spin.setEnabled(False)
            self.duration_spin.setStyleSheet("background-color: #eee;")

    def get_duration(self):
        return self.duration_spin.value()

# 占位对话框: SingleResourceDialog,DetailsDialog,SaveResultDialog...
# 省略实现细节，只是为了完整

class SingleResourceDialog(QDialog):
    def __init__(self, resource=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("资源信息")
        self.resource = resource
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout(self)
        self.resource_label = QLabel("资源:")
        # self.resource_input = QComboBox()
        # self.resource_input.addItems(["人员", "物资", "车辆"])
        # 使用自定义居中对齐的 QComboBox
        self.resource_input = create_centered_combobox(["人员", "物资", "车辆"], "人员")
        layout.addWidget(self.resource_label)
        layout.addWidget(self.resource_input)

        self.type_label = QLabel("类型:")
        # self.type_input = QComboBox()
        # self.type_input.addItems(["类型A", "类型B", "类型C"])
        # 使用自定义居中对齐的 QComboBox
        self.type_input = create_centered_combobox(["类型A", "类型B", "类型C"], "类型A")
        layout.addWidget(self.type_label)
        layout.addWidget(self.type_input)

        self.quantity_label = QLabel("数量:")
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setAlignment(Qt.AlignCenter)
        self.quantity_spin.setRange(1,1000)
        layout.addWidget(self.quantity_label)
        layout.addWidget(self.quantity_spin)

        self.location_label = QLabel("位置:")
        self.location_input = QLineEdit()
        layout.addWidget(self.location_label)
        layout.addWidget(self.location_input)

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.cancel_btn = QPushButton("取消")
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        if self.resource:
            self.resource_input.setCurrentText(self.resource["资源"])
            self.type_input.setCurrentText(self.resource["类型"])
            self.quantity_spin.setValue(self.resource["数量"])
            self.location_input.setText(self.resource["位置"])

        for i in range(btn_layout.count()):
            btn_layout.itemAt(i).widget().setFixedWidth(50)

        self.setStyleSheet("""
                        QLineEdit, QComboBox {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #0078d7; /* 蓝色边框 */
            }
        """
)

    def get_resource(self):
        return {
            "资源":self.resource_input.currentText(),
            "类型":self.type_input.currentText(),
            "数量":self.quantity_spin.value(),
            "位置":self.location_input.text().strip() if self.location_input.text().strip() else "未知"
        }

class DetailsDialog(QDialog):
    def __init__(self, info_html, parent=None):
        super().__init__(parent)
        self.setWindowTitle("详细信息")
        self.setModal(True)
        self.resize(600,400)
        layout = QVBoxLayout(self)
        self.browser = QTextBrowser()
        self.browser.setHtml(info_html)
        layout.addWidget(self.browser)
        close_btn = QPushButton("确定")
        close_btn.clicked.connect(self.accept)
        close_btn.setFixedWidth(50)
        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(close_btn)
        h.addStretch()
        layout.addLayout(h)
        self.setLayout(layout)

class SaveResultDialog(QDialog):
    def __init__(self, saved_categories, info_html, parent=None):
        super().__init__(parent)
        self.setWindowTitle("保存结果")
        self.setModal(True)
        self.resize(300,250)
        main_layout = QVBoxLayout(self)
        lab = QLabel("已保存的应急行为类别:")
        lab.setFont(QFont("SimSun",14,QFont.Bold))
        main_layout.addWidget(lab)

        self.listwidget = QListWidget()
        for sc in saved_categories:
            self.listwidget.addItem(sc["category"])
        main_layout.addWidget(self.listwidget)

        btn_h = QHBoxLayout()
        self.btn_detail = QPushButton("查看详情")
        self.btn_detail.setFixedWidth(85)
        self.btn_detail.clicked.connect(lambda: self.open_detail_dialog(info_html))
        self.btn_ok = QPushButton("确定")
        self.btn_ok.setFixedWidth(50)
        self.btn_ok.clicked.connect(self.accept)
        btn_h.addWidget(self.btn_detail)
        btn_h.addWidget(self.btn_ok)
        main_layout.addLayout(btn_h)
        self.setLayout(main_layout)

    def open_detail_dialog(self, info_html):
        dlg = DetailsDialog(info_html, parent=self)
        dlg.exec()




class ConditionSettingTab(QWidget):
    save_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("应急预案设置")
        # 行为资源
        self.behavior_resources = {b:[] for b in ["救助","牵引","抢修","消防"]}
        self.current_behavior = None
        self.init_ui()

    def init_ui(self):
        self.set_stylesheet()
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(main_layout)

        # =============== 上方布局：应急行为(左) & 应急资源(右) =================
        upper_layout = QHBoxLayout()
        upper_layout.setSpacing(10)

        # 左侧：QVBoxLayout，里面放 (应急行为设置 GroupBox [stretch=10]) + (按钮 [stretch=1])
        left_vbox = QVBoxLayout()
        left_vbox.setSpacing(10)

        behavior_group = QGroupBox("应急行为设置")
        behavior_group_layout = QVBoxLayout()
        behavior_group_layout.setContentsMargins(10,10,10,10)
        # 设置最小宽度
        behavior_group.setMinimumWidth(200)
        # 4 个行为checkbox
        self.behaviors = ["救助","牵引","抢修","消防"]
        self.behavior_settings = {}
        for b in self.behaviors:
            cbox_with_label = CustomCheckBoxWithLabel(b)
            cbox_with_label.checkbox.stateChanged.connect(
                partial(self.handle_checkbox_state_changed, behavior=b)
            )
            cbox_with_label.label.clicked.connect(
                partial(self.handle_label_clicked, behavior=b)
            )
            behavior_group_layout.addWidget(cbox_with_label)
            self.behavior_settings[b] = cbox_with_label

        behavior_group.setLayout(behavior_group_layout)

        # 按钮
        self.execute_btn = QPushButton("保存预案，执行推演")
        self.execute_btn.setEnabled(False)
        self.execute_btn.setToolTip("请配置应急行为")
        self.execute_btn.setMaximumWidth(160)
        self.execute_btn.clicked.connect(self.handle_save)
        self.execute_btn.setStyleSheet("""
            QPushButton {
                color: black;
                background-color: #cce5ff;
                border: 1px solid #0078d7;
                border-radius: 5px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #5dade2;
            }
            QPushButton:disabled {
                background-color: #d3d3d3; color:#888; border:1px solid #aaa;
            }
        """)

        # 比例 10:1
        left_vbox.addWidget(behavior_group, stretch=10)
        left_vbox.addWidget(self.execute_btn, alignment=Qt.AlignCenter, stretch=0)

        # 右侧：应急资源设置
        resource_group = QGroupBox("应急资源设置")
        resource_layout = QVBoxLayout()
        resource_layout.setContentsMargins(10,10,10,10)
        self.resource_stacked_layout = QStackedLayout()

        self.placeholder_widget = QWidget()
        ph_layout = QVBoxLayout()
        ph_label = QLabel("请选择应急行为")
        ph_label.setAlignment(Qt.AlignCenter)
        ph_label.setStyleSheet("""
                color: gray;
                font-size: 20pt;
                border-radius: 10px;
                border: 0px solid #c0c0c0;
                background-color: #ffffff;
            """)
        ph_layout.addWidget(ph_label)
        self.placeholder_widget.setLayout(ph_layout)
        self.resource_stacked_layout.addWidget(self.placeholder_widget)

        self.resource_management_widget = QWidget()
        res_mgmt_layout = QVBoxLayout()
        res_mgmt_layout.setContentsMargins(0,0,0,0)


        label_btn_layout = QHBoxLayout()
        label_btn_layout.setContentsMargins(0,0,0,0)
        self.current_behavior_label = QLabel("请选择应急行为")
        self.current_behavior_label.setAlignment(Qt.AlignCenter)
        self.current_behavior_label.setStyleSheet("font-weight:bold;color:gray;")

        btn_hbox = QHBoxLayout()
        btn_hbox.setContentsMargins(0,0,0,0)
        self.add_resource_btn = QPushButton("添加")
        self.edit_resource_btn = QPushButton("修改")
        self.delete_resource_btn = QPushButton("删除")

        self.add_resource_btn.setIcon(
            QIcon(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "icons", "add.png")))
        self.edit_resource_btn.setIcon(
            QIcon(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "icons", "edit.png")))
        self.delete_resource_btn.setIcon(
            QIcon(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "icons", "delete.png")))

        self.add_resource_btn.setMaximumWidth(100)
        self.edit_resource_btn.setMaximumWidth(100)
        self.delete_resource_btn.setMaximumWidth(100)

        btn_hbox.addWidget(self.add_resource_btn)
        btn_hbox.addWidget(self.edit_resource_btn)
        btn_hbox.addWidget(self.delete_resource_btn)

        label_btn_layout.addWidget(self.current_behavior_label)
        label_btn_layout.addLayout(btn_hbox)

        res_mgmt_layout.addLayout(label_btn_layout)

        self.resource_table = QTableWidget(0,4)
        self.resource_table.setHorizontalHeaderLabels(["资源","类型","数量","位置"])
        self.resource_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.resource_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.resource_table.setSelectionMode(QTableWidget.SingleSelection)
        self.resource_table.verticalHeader().setVisible(False)
        self.resource_table.setAlternatingRowColors(True)
        self.resource_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.resource_table.setShowGrid(False)
        self.resource_table.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.apply_table_style(self.resource_table)

        res_mgmt_layout.addWidget(self.resource_table)
        self.resource_management_widget.setLayout(res_mgmt_layout)
        self.resource_stacked_layout.addWidget(self.resource_management_widget)

        resource_layout.addLayout(self.resource_stacked_layout)
        resource_group.setLayout(resource_layout)

        upper_layout.addLayout(left_vbox, stretch=1)
        upper_layout.addWidget(resource_group, stretch=4)

        main_layout.addLayout(upper_layout, stretch=1)

        # =============== 下方布局：证据更新（左） & 推演结果（右） =================
        lower_layout = QHBoxLayout()
        lower_layout.setSpacing(10)

        evidence_group = QGroupBox("证据更新")
        # 设置最小宽度
        evidence_group.setMinimumWidth(200)
        evidence_layout = QVBoxLayout()
        evidence_layout.setContentsMargins(10,20,10,10)
        self.evidence_table = CustomTableWidget(0,3)
        self.evidence_table.setHorizontalHeaderLabels(["要素节点","状态","概率"])
        self.evidence_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.evidence_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.evidence_table.setSelectionMode(QTableWidget.SingleSelection)
        self.evidence_table.verticalHeader().setVisible(False)
        self.evidence_table.setAlternatingRowColors(True)
        self.evidence_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.evidence_table.setShowGrid(False)
        self.evidence_table.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.apply_table_style(self.evidence_table)

        evidence_layout.addWidget(self.evidence_table)
        evidence_group.setLayout(evidence_layout)

        simulation_group = QGroupBox("推演结果")
        simulation_layout = QVBoxLayout()
        simulation_layout.setContentsMargins(10,20,10,10)
        self.simulation_table = CustomTableWidget(2,7)
        self.simulation_table.setShowGrid(False)
        self.simulation_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.simulation_table.setSelectionMode(QTableWidget.SingleSelection)
        self.simulation_table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.simulation_table.horizontalHeader().setVisible(False)
        self.simulation_table.verticalHeader().setVisible(False)

        # 多级表头：两行
        self.simulation_table.setSpan(0,0,2,1)  # 斜杠"韧性/预案"
        self.simulation_table.setSpan(0,1,1,3)  # "推演前"
        self.simulation_table.setSpan(0,4,1,3)  # "推演后"

        # 自定义表头委托
        header_delegate = FullHeaderDelegate(self.simulation_table)
        for row in range(2):
            for col in range(self.simulation_table.columnCount()):
                self.simulation_table.setItemDelegateForRow(row, header_delegate)

        self.apply_table_style(self.simulation_table)

        self.simulation_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        simulation_layout.addWidget(self.simulation_table)
        simulation_group.setLayout(simulation_layout)

        lower_layout.addWidget(evidence_group, stretch=1)
        lower_layout.addWidget(simulation_group, stretch=4)

        main_layout.addLayout(lower_layout, stretch=1)

        # 连接按钮
        self.add_resource_btn.clicked.connect(self.add_resource)
        self.edit_resource_btn.clicked.connect(self.edit_resource)
        self.delete_resource_btn.clicked.connect(self.delete_resource)

    def handle_label_clicked(self, behavior):
        cbox = self.behavior_settings[behavior].checkbox
        if not cbox.isChecked():
            cbox.setChecked(True)
        else:
            self.switch_behavior(behavior)
            self.update_label_styles(behavior)

    def handle_checkbox_state_changed(self, state, behavior):
        if state == 2:
            self.behavior_settings[behavior].checkbox.setEnabled(False)
            self.switch_behavior(behavior)
            self.update_label_styles(behavior)
            self.update_resource_dependencies(behavior)
            self.check_execute_button()

    def switch_behavior(self, behavior):
        self.current_behavior = behavior
        self.current_behavior_label.setText(f"正在编辑: {behavior}")
        self.current_behavior_label.setStyleSheet("font-weight:bold;color:#5dade2;")
        self.add_resource_btn.setToolTip(f"添加{behavior}的资源")
        self.edit_resource_btn.setToolTip(f"修改{behavior}的资源")
        self.delete_resource_btn.setToolTip(f"删除{behavior}的资源")
        self.resource_stacked_layout.setCurrentWidget(self.resource_management_widget)
        self.load_resources_for_behavior(behavior)

    def update_label_styles(self, selected_behavior):
        for b, cbl in self.behavior_settings.items():
            cbl.set_selected(b == selected_behavior)

    def update_resource_dependencies(self, behavior):
        self.resource_stacked_layout.setCurrentWidget(self.resource_management_widget)
        self.load_resources_for_behavior(behavior)

    def load_resources_for_behavior(self, behavior):
        self.resource_table.setRowCount(0)
        for r in self.behavior_resources[behavior]:
            self.add_resource_to_table(r, behavior)

    def add_resource_to_table(self, resource, behavior):
        rowpos = self.resource_table.rowCount()
        self.resource_table.insertRow(rowpos)
        self.resource_table.setItem(rowpos,0,QTableWidgetItem(resource["资源"]))
        self.resource_table.setItem(rowpos,1,QTableWidgetItem(resource["类型"]))
        self.resource_table.setItem(rowpos,2,QTableWidgetItem(str(resource["数量"])))
        self.resource_table.setItem(rowpos,3,QTableWidgetItem(resource["位置"]))
        for col in range(4):
            self.resource_table.item(rowpos,col).setTextAlignment(Qt.AlignCenter)

    def add_resource(self):
        if not self.current_behavior:
            CustomWarningDialog("提示","请先选择应急行为").exec()
            return
        dlg = SingleResourceDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            r = dlg.get_resource()
            self.behavior_resources[self.current_behavior].append(r)
            self.add_resource_to_table(r, self.current_behavior)
            self.check_execute_button()

    def edit_resource(self):
        sel = self.resource_table.selectedItems()
        if not sel:
            CustomWarningDialog("提示","请选择要修改的资源。").exec()
            return
        row = sel[0].row()
        resource = {
            "资源": self.resource_table.item(row,0).text(),
            "类型": self.resource_table.item(row,1).text(),
            "数量": int(self.resource_table.item(row,2).text()),
            "位置": self.resource_table.item(row,3).text()
        }
        dlg = SingleResourceDialog(resource, parent=self)
        if dlg.exec() == QDialog.Accepted:
            updated = dlg.get_resource()
            try:
                idx = self.behavior_resources[self.current_behavior].index(resource)
                self.behavior_resources[self.current_behavior][idx] = updated
            except ValueError:
                CustomWarningDialog("提示","未找到要修改的资源。").exec()
                return
            self.resource_table.setItem(row,0,QTableWidgetItem(updated["资源"]))
            self.resource_table.setItem(row,1,QTableWidgetItem(updated["类型"]))
            self.resource_table.setItem(row,2,QTableWidgetItem(str(updated["数量"])))
            self.resource_table.setItem(row,3,QTableWidgetItem(updated["位置"]))
            for col in range(4):
                self.resource_table.item(row,col).setTextAlignment(Qt.AlignCenter)
            self.check_execute_button()

    def delete_resource(self):
        sel = self.resource_table.selectedItems()
        if not sel:
            CustomWarningDialog("提示","请选择要删除的资源。").exec()
            return
        row = sel[0].row()
        resource = {
            "资源": self.resource_table.item(row,0).text(),
            "类型": self.resource_table.item(row,1).text(),
            "数量": int(self.resource_table.item(row,2).text()),
            "位置": self.resource_table.item(row,3).text()
        }
        reply = CustomQuestionDialog("确认删除",f"确定要删除应急行为 '{self.current_behavior}' 下的选中资源吗？", parent=self).ask()
        if reply:
            try:
                self.behavior_resources[self.current_behavior].remove(resource)
            except ValueError:
                CustomWarningDialog("提示","未找到要删除的资源。").exec()
                return
            self.resource_table.removeRow(row)
            self.check_execute_button()

    def check_execute_button(self):
        selected_b = [b for b in self.behaviors if self.behavior_settings[b].checkbox.isChecked()]
        all_checked = (len(selected_b)==len(self.behaviors))
        self.execute_btn.setEnabled(all_checked)
        self.execute_btn.setToolTip("请配置应急行为" if not all_checked else "")

    def handle_save(self):
        saved_categories = []
        for b in self.behaviors:
            cbox = self.behavior_settings[b].checkbox
            if cbox.isChecked():
                duration = self.behavior_settings[b].get_duration()
                res_list = self.behavior_resources[b]
                saved_categories.append({
                    "category": b,
                    "attributes": {"时长": f"{duration} 分钟"},
                    "behaviors": res_list
                })
        if not saved_categories:
            CustomInformationDialog("保存结果","没有要保存的应急行为。", parent=self).exec()
            return

        info_html = """
        <html><head><style>
         body{font-family:"Microsoft YaHei";font-size:14px;color:#333}
         h2{text-align:center;color:#0078d7;margin-bottom:20px}
         h3{color:#005a9e;margin-top:30px;margin-bottom:10px}
         table{width:100%;border-collapse:collapse;margin-bottom:20px}
         th,td{border:1px solid #ccc;padding:10px;text-align:center}
         th{background-color:#f0f0f0}
         .no-behavior{color:red;font-style:italic;text-align:center}
        </style></head><body><h2>保存结果详情</h2>
        """
        for item in saved_categories:
            info_html += f"<h3>类别: {item['category']}</h3>"
            info_html += """<b>属性:</b>
            <table><tr><th>属性名称</th><th>属性值</th></tr>"""
            for k,v in item["attributes"].items():
                info_html += f"<tr><td>{k}</td><td>{v}</td></tr>"
            info_html += "</table><b>资源列表:</b>"
            if item["behaviors"]:
                info_html += """<table>
                <tr><th>资源名称</th><th>类型</th><th>数量</th><th>位置</th></tr>"""
                for r in item["behaviors"]:
                    info_html += f"<tr><td>{r['资源']}</td><td>{r['类型']}</td><td>{r['数量']}</td><td>{r['位置']}</td></tr>"
                info_html += "</table>"
            else:
                info_html += "<p class='no-behavior'>无资源</p>"
        info_html += "</body></html>"

        dlg = SaveResultDialog(saved_categories, info_html, parent=self)
        if dlg.exec():
            # 询问预案名
            input_dlg = CustomInputDialog("预案名称设置","请输入预案名字:",parent=self)
            if input_dlg.exec():
                plan_name = input_dlg.get_input().strip()
                if plan_name:
                    self.update_evidence_table()
                    self.update_simulation_table(plan_name)
                    CustomInformationDialog("成功", f"预案 '{plan_name}' 已保存并推演。",parent=self).exec()
                else:
                    CustomWarningDialog("提示","预案名字不能为空。").exec()

    def update_evidence_table(self):
        example_data = [
            {"要素节点":"节点1","状态":"正常","概率":"80%"},
            {"要素节点":"节点2","状态":"异常","概率":"20%"},
        ]
        # 清空表格内容和行数
        self.evidence_table.clearContents()
        self.evidence_table.setRowCount(0)

        for d in example_data:
            rowpos = self.evidence_table.rowCount()
            self.evidence_table.insertRow(rowpos)
            self.evidence_table.setItem(rowpos,0,QTableWidgetItem(d["要素节点"]))
            self.evidence_table.setItem(rowpos,1,QTableWidgetItem(d["状态"]))
            self.evidence_table.setItem(rowpos,2,QTableWidgetItem(d["概率"]))
            for col in range(3):
                self.evidence_table.item(rowpos,col).setTextAlignment(Qt.AlignCenter)

    def update_simulation_table(self, plan_name):
        # 从 row=2 开始插数据
        data = [
            {
                "预案名字": plan_name,
                "推演前-较好":"30%",
                "推演前-中等":"50%",
                "推演前-较差":"20%",
                "推演后-较好":"60%",
                "推演后-中等":"30%",
                "推演后-较差":"10%",
            }
        ]
        for d in data:
            rowpos = self.simulation_table.rowCount()
            self.simulation_table.setRowCount(rowpos+1)
            self.simulation_table.setItem(rowpos,0,QTableWidgetItem(d["预案名字"]))
            self.simulation_table.setItem(rowpos,1,QTableWidgetItem(d["推演前-较好"]))
            self.simulation_table.setItem(rowpos,2,QTableWidgetItem(d["推演前-中等"]))
            self.simulation_table.setItem(rowpos,3,QTableWidgetItem(d["推演前-较差"]))
            self.simulation_table.setItem(rowpos,4,QTableWidgetItem(d["推演后-较好"]))
            self.simulation_table.setItem(rowpos,5,QTableWidgetItem(d["推演后-中等"]))
            self.simulation_table.setItem(rowpos,6,QTableWidgetItem(d["推演后-较差"]))
            for col in range(7):
                self.simulation_table.item(rowpos,col).setTextAlignment(Qt.AlignCenter)

    def set_stylesheet(self):
        self.setStyleSheet("""
        QGroupBox {
            border:1px solid #ccc;
            border-radius:8px;
            margin-top:10px;
            font-weight:bold;
            background-color:#fff;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding:2px 10px;
            font-weight:bold;
            color:#333;
            background-color:#E8E8E8;
            border-radius:10px;
            border-bottom-left-radius:0;
        }
        QLabel{ color:#333; }
        QCheckBox{ color:#333; }

        /* ----------------------【改动 2】：在下面的选择器中加入 QSpinBox ---------------------- */
        QLineEdit, QComboBox, QSpinBox {
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 5px;
            background-color: white; /* 这里可根据需要自定义 */
        }
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
            border: 2px solid #0078d7; /* 蓝色边框 */
        }
        /* ------------------------------------------------------------------- */

        QScrollBar:vertical, QScrollBar:horizontal {
            border:none; background:#f1f1f1; width:8px; height:8px; margin:0;
        }
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
            background:#c1c1c1; min-width:20px; min-height:20px; border-radius:4px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            height:0;width:0;subcontrol-origin:margin;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background:none;
        }
        """)

    def apply_table_style(self, table: QTableWidget):
        table.setStyleSheet("""
            QTableWidget {
                border:none;
                font-size:14px;
                border-bottom:1px solid black;
            }
            QHeaderView::section {
                border-top:1px solid black;
                border-bottom:1px solid black;
                background-color:#f0f0f0;
                font-weight:bold;
                padding:4px;
                color:#333;
                text-align:center;
            }
            QTableWidget::item {
                border:none;
                padding:5px;
                text-align:center;
            }
            QTableWidget::item:selected {
                background-color:#cce5ff; color:black; border:none;
            }
            QTableWidget:focus {
                outline:none;
            }
        """)
        table.setAlternatingRowColors(True)

    def reset_inputs(self):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConditionSettingTab()
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())
