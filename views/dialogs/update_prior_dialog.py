# -*- coding: utf-8 -*-
# @Time    : 2/4/2025 11:35 AM
# @FileName: nonroot_table_update_dialog.py
# @Software: PyCharm
import itertools
import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QFileDialog, QMessageBox, QApplication, QWidget, QScrollArea, QGroupBox,
    QFormLayout, QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QStyleFactory
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPalette, QColor
from itertools import product
import pandas as pd
import os
import ast

from utils.get_config import get_cfg
from views.dialogs.custom_error_dialog import CustomErrorDialog
from views.dialogs.custom_information_dialog import CustomInformationDialog
from views.dialogs.custom_warning_dialog import CustomWarningDialog

NONROOT_PARENTS = {
    "AbsorptionCapacity": ["roadPassibility", "roadLoss"],
    "AdaptionCapacity": ["emergencyPeriod", "emergencyType", "casualties"],
    "RecoveryCapacity": ["disposalDuration", "responseDuration",
                         "RescueResource", "FirefightingResource", "TowResource", "AidResource"],
    "ScenarioResilience": ["RecoveryCapacity", "AdaptionCapacity", "AbsorptionCapacity"]
}

STATE_OPTIONS = {
    "roadPassibility": ["Impassable", "Passable"],
    "emergencyType": ["Vehicle_Self_Accident", "Vehicle_to_Fixed_Object_Accident", "Collision_Acident"],
    "roadLoss": ["Not_Loss", "Loss"],
    "casualties": ["No_Casualties", "Casualties"],
    "RescueResource": ["Not_Used", "Used"],
    "FirefightingResource": ["Not_Used", "Used"],
    "TowResource": ["Not_Used", "Used"],
    "AidResource": ["Not_Used", "Used"],
    "emergencyPeriod": ["Early_Morning", "Morning", "Afternoon", "Evening"],
    "responseDuration": ["0-15min", "15-30min", "30-60min", "60min+"],
    "disposalDuration": ["0-15min", "15-30min", "30-60min", "60min+"],
    "RecoveryCapacity": ["Good", "Bad"],
    "AdaptionCapacity": ["Good", "Bad"],
    "AbsorptionCapacity": ["Good", "Bad"],
}

# 原来的模糊选项 + “未评估”
EVAL_OPTIONS = ["未评估", "VL", "L", "M", "H", "VH"]

# EXPERT_EXCEL_PATH = r"D:\PythonProjects\AcademicTool_PySide\data\expert estimation test.xlsx"

QUESTION_TEXT = {}

# 1. AbsorptionCapacity
QUESTION_TEXT[("AbsorptionCapacity", 0)] = {
    (1, 0): "道路可通行且不存在道路设施损失时，请评估道路具有较好吸收扰动的能力的可能性：",
    (1, 1): "道路可通行且存在道路设施损失时，请评估道路具有较好吸收扰动的能力的可能性：",
    (0, 1): "道路不可通行且存在道路设施损失时，请评估道路具有较好吸收扰动的能力的可能性：",
    (0, 0): "道路不可通行且不存在道路设施损失时，请评估道路具有较好吸收扰动的能力的可能性：",
}

# 2. AdaptionCapacity
QUESTION_TEXT[("AdaptionCapacity", 0)] = {
    (0, 0,0): "突发事件发生于当天00:00至06:00，事件类型为车辆自身事故（侧翻、抛锚），没有造成人员伤亡，请评估具有较好适应扰动的能力的可能性：",
    (0, 0, 1): "突发事件发生于当天00:00至06:00，事件类型为车辆自身事故（侧翻、抛锚），发生人员伤亡，请评估具有较好适应扰动的能力的可能性：",
    (0, 1,0): "突发事件发生于当天00:00至06:00，事件类型为车辆对固定物事故（撞到护栏、路墩等），没有造成人员伤亡，请评估具有较好适应扰动的能力的可能性：",
    (0, 1, 1): "突发事件发生于当天00:00至06:00，事件类型为车辆对固定物事故（撞到护栏、路墩等），发生人员伤亡，请评估具有较好适应扰动的能力的可能性：",
    (0, 2,0): "突发事件发生于当天00:00至06:00，事件类型为车辆擦碰事故（指两辆或两辆以上的车辆发生意外碰撞），没有造成人员伤亡，请评估具有较好适应扰动的能力的可能性：",
    (0, 2,1): "突发事件发生于当天00:00至06:00，事件类型为车辆擦碰事故（指两辆或两辆以上的车辆发生意外碰撞），发生人员伤亡，请评估具有较好适应扰动的能力的可能性：",
    (1, 0,0): "突发事件发生于当天06:00至12:00，事件类型为车辆自身事故（侧翻、抛锚），没有造成人员伤亡，请评估具有较好适应扰动的能力的可能性：",
    (1, 0,1): "突发事件发生于当天06:00至12:00，事件类型为车辆自身事故（侧翻、抛锚），发生人员伤亡，请评估具有较好适应扰动的能力的可能性：",
    (1, 1,0): "突发事件发生于当天06:00至12:00，事件类型为车辆对固定物事故（撞到护栏、路墩等），没有造成人员伤亡，请评估具有较好适应扰动的能力的可能性：",
    (1, 1,1): "突发事件发生于当天06:00至12:00，事件类型为车辆对固定物事故（撞到护栏、路墩等），发生人员伤亡，请评估具有较好适应扰动的能力的可能性：",
    (1, 2,0): "突发事件发生于当天06:00至12:00，事件类型为车辆擦碰事故（指两辆或两辆以上的车辆发生意外碰撞），没有造成人员伤亡，请评估具有较好适应扰动的能力的可能性：",
    (1, 2,1): "突发事件发生于当天06:00至12:00，事件类型为车辆擦碰事故（指两辆或两辆以上的车辆发生意外碰撞），发生人员伤亡，请评估具有较好适应扰动的能力的可能性：",
    (2, 0,0): "突发事件发生于当天12:00至18:00，事件类型为车辆自身事故（侧翻、抛锚），没有造成人员伤亡，请评估具有较好适应扰动的能力的可能性：",
    (2, 0,1): "突发事件发生于当天12:00至18:00，事件类型为车辆自身事故（侧翻、抛锚），发生人员伤亡，请评估具有较好适应扰动的能力的可能性：",
    (2, 1,0): "突发事件发生于当天12:00至18:00，事件类型为车辆对固定物事故（撞到护栏、路墩等），没有造成人员伤亡，请评估具有较好适应扰动的能力的可能性：",
    (2, 1,1): "突发事件发生于当天12:00至18:00，事件类型为车辆对固定物事故（撞到护栏、路墩等），发生人员伤亡，请评估具有较好适应扰动的能力的可能性：",
    (2, 2,0): "突发事件发生于当天12:00至18:00，事件类型为车辆擦碰事故（指两辆或两辆以上的车辆发生意外碰撞），没有造成人员伤亡，请评估具有较好适应扰动的能力的可能性：",
    (2, 2,1): "突发事件发生于当天12:00至18:00，事件类型为车辆擦碰事故（指两辆或两辆以上的车辆发生意外碰撞），发生人员伤亡，请评估具有较好适应扰动的能力的可能性：",
    (3, 0,0): "突发事件发生于当天18:00至24:00，事件类型为车辆自身事故（侧翻、抛锚），没有造成人员伤亡，请评估具有较好适应扰动的能力的可能性：",
    (3, 0,1): "突发事件发生于当天18:00至24:00，事件类型为车辆自身事故（侧翻、抛锚），发生人员伤亡，请评估具有较好适应扰动的能力的可能性：",
    (3, 1,0): "突发事件发生于当天18:00至24:00，事件类型为车辆对固定物事故（撞到护栏、路墩等），没有造成人员伤亡，请评估具有较好适应扰动的能力的可能性：",
    (3, 1,1): "突发事件发生于当天18:00至24:00，事件类型为车辆对固定物事故（撞到护栏、路墩等），发生人员伤亡，请评估具有较好适应扰动的能力的可能性：",
    (3, 2,0): "突发事件发生于当天18:00至24:00，事件类型为车辆擦碰事故（指两辆或两辆以上的车辆发生意外碰撞），没有造成人员伤亡，请评估具有较好适应扰动的能力的可能性：",
    (3, 2, 1): "突发事件发生于当天18:00至24:00，事件类型为车辆擦碰事故（指两辆或两辆以上的车辆发生意外碰撞），发生人员伤亡，请评估具有较好适应扰动的能力的可能性："
}

# 3. RecoveryCapacity
# 定义响应与处置时长的描述文本：
response_time_text = ["响应时长在15分钟以内", "响应时长在15-30分钟", "响应时长在30-60分钟", "响应时长在60分钟以上"]
disposal_time_text = ["处置时长在15分钟以内", "处置时长在15-30分钟", "处置时长在30-60分钟", "处置时长在60分钟以上"]
# casualties: 0 -> 无人员伤亡，1 -> 有人员伤亡
casualties_text = ["且无人员伤亡", "且有人员伤亡"]

# 定义各应急资源对应的中文名称
resource_names = {
    "RescueResource": "救助资源",
    "FirefightingResource": "消防资源",
    "TowResource": "牵引资源",
    "AidResource": "抢修资源"
}

# 构造一个函数，根据 4 个应急资源的取值（0 或 1）生成资源部分的描述
def resources_used(rr, ff, tw, aid):
    used = []
    if rr == 1:
        used.append(resource_names["RescueResource"])
    if ff == 1:
        used.append(resource_names["FirefightingResource"])
    if tw == 1:
        used.append(resource_names["TowResource"])
    if aid == 1:
        used.append(resource_names["AidResource"])
    if not used:
        return "未使用任何应急资源"
    elif len(used) == 1:
        return f"仅使用{used[0]}"
    else:
        return "使用" + "和".join(used)

# 对 RecoveryCapacity 生成问题文本
QUESTION_TEXT[("RecoveryCapacity", 0)] = {}
resource_combinations = sorted(list(itertools.product(range(2), repeat=4)), key=lambda x: sum(x))

for rr, ff, tw, aid in resource_combinations:
    for r in range(4):  # responseDuration: 0~3
        for d in range(4):  # disposalDuration: 0~3
            key = (d, r, rr, ff, tw, aid)
            resource_phrase = resources_used(rr, ff, tw, aid)
            question = (
                f"在应急响应过程中{resource_phrase}，"
                f"{response_time_text[r]}，"
                f"{disposal_time_text[d]}，"
                "请评估道路具有较好从扰动中恢复的能力的可能性："
            )
            QUESTION_TEXT[("RecoveryCapacity", 0)][key] = question
# data = []
# for key, q in QUESTION_TEXT[("RecoveryCapacity", 0)].items():
#     d, r, rr, ff, tw, aid = key
#     data.append({
#          "处置时长": disposal_time_text[d],
#          "响应时长": response_time_text[r],
#          "救助资源": rr,
#          "消防资源": ff,
#          "牵引资源": tw,
#          "抢修资源": aid,
#          "问题": q
#     })
#
# # 转换为 DataFrame 并保存到 Excel 文件中
# df = pd.DataFrame(data)
# df.to_excel("RecoveryCapacity_questions.xlsx", index=False)
# print("问题文本已保存到 RecoveryCapacity_questions.xlsx 文件中。")

QUESTION_TEXT[(("ScenarioResilience", 0))] = {
    (0, 0, 0): "在突发事件发生前城市道路系统能够自动吸收潜在的扰动并维持正常运行，在突发事件发生时城市道路系统能够在很少或完全不涉及外部快速恢复操作的情况下快速恢复损失的性能，在实施应急预案后城市道路系统能够快速恢复至正常运行状态，请评估道路具有较好韧性的可能性：",
    (0, 0, 1): "在突发事件发生前城市道路系统能够自动吸收潜在的扰动并维持正常运行，在突发事件发生时城市道路系统能够在很少或完全不涉及外部恢复操作的情况下难以快速恢复损失的性能，在实施应急预案后城市道路系统能够快速恢复至正常运行状态，请评估道路具有较好韧性的可能性：",
    (0, 1, 0): "在突发事件发生前城市道路系统能够自动吸收潜在的扰动并维持正常运行，在突发事件发生时城市道路系统能够在很少或完全不涉及外部快速恢复操作的情况下快速恢复损失的性能，在实施应急预案后城市道路系统难以快速恢复至正常运行状态，请评估道路具有较好韧性的可能性：",
    (0, 1, 1): "在突发事件发生前城市道路系统能够自动吸收潜在的扰动并维持正常运行，在突发事件发生时城市道路系统能够在很少或完全不涉及外部恢复操作的情况下难以快速恢复损失的性能，在实施应急预案后城市道路系统难以快速恢复至正常运行状态，请评估道路具有较好韧性的可能性：",
    (1, 0, 0): "在突发事件发生前城市道路系统难以自动吸收潜在的扰动并维持正常运行，在突发事件发生时城市道路系统能够在很少或完全不涉及外部快速恢复操作的情况下快速恢复损失的性能，在实施应急预案后城市道路系统能够快速恢复至正常运行状态，请评估道路具有较好韧性的可能性：",
    (1, 0, 1): "在突发事件发生前城市道路系统难以自动吸收潜在的扰动并维持正常运行，在突发事件发生时城市道路系统能够在很少或完全不涉及外部恢复操作的情况下难以快速恢复损失的性能，在实施应急预案后城市道路系统能够快速恢复至正常运行状态，请评估道路具有较好韧性的可能性：",
    (1, 1, 0): "在突发事件发生前城市道路系统难以自动吸收潜在的扰动并维持正常运行，在突发事件发生时城市道路系统能够在很少或完全不涉及外部快速恢复操作的情况下快速恢复损失的性能，在实施应急预案后城市道路系统难以快速恢复至正常运行状态，请评估道路具有较好韧性的可能性：",
    (1, 1, 1): "在突发事件发生前城市道路系统难以自动吸收潜在的扰动并维持正常运行，在突发事件发生时城市道路系统能够在很少或完全不涉及外部恢复操作的情况下难以快速恢复损失的性能，在实施应急预案后城市道路系统难以快速恢复至正常运行状态，请评估道路具有较好韧性的可能性："
}


AGE_OPTIONS = ["请选择您的年龄","A.30岁及以下", "B.31-40岁", "C.41-50岁", "D.50岁以上"]
EDU_OPTIONS = ["请选择您的教育水平","A.大专及以下", "B.本科", "C.硕士", "D.博士及以上"]
WORK_OPTIONS = ["请选择您的工作年限","A.5年及以下", "B.6-10年", "C.11-19年", "D.20年及以上"]
JOB_OPTIONS = ["请选择您的工作职位","A.工人", "B.技术员", "C.工程师", "D.副教授", "E.教授"]

AGE_MAPPING = {
    "A.30岁及以下": 1,
    "B.31-40岁": 2,
    "C.41-50岁": 3,
    "D.50岁以上": 4
}

EDU_MAPPING = {
    "A.大专及以下": 1,
    "B.本科": 2,
    "C.硕士": 3,
    "D.博士及以上": 4
}

WORK_MAPPING = {
    "A.5年及以下": 1,
    "B.6-10年": 2,
    "C.11-19年": 3,
    "D.20年及以上": 4
}

JOB_MAPPING = {
    "A.工人": 1,
    "B.技术员": 2,
    "C.工程师": 3,
    "D.副教授": 4,
    "E.教授": 5,
}


class AddExpertDialog(QDialog):
    """
    演示一个“新增专家”对话框：
      1) 上半部分收集专家个人信息(年龄/教育/工龄/职位)。
      2) 下半部分显示问卷问题(多级字典里所有条目)，并让用户给出评分。
      3) 点击“保存”时，分开获取:
         - personal_info (dict)
         - expert_rating => 多级字典 { (node, state): {cond_tuple: rating } }
      4) 你可在这里将它们分开写入 Excel，或存数据库等。
    """

    def __init__(self, info_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("新增专家问卷"))
        self.resize(1200, 700)
        self.info_dir = info_dir  # 可能用于保存/读取Excel的路径
        self.parent = parent

        main_layout = QVBoxLayout(self)

        #####################################################
        # 1) 专家个人信息区域 (使用 QFormLayout)
        #####################################################
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.combo_node = QComboBox()
        # 从 QUESTION_TEXT 的 key 中提取唯一节点（注意 QUESTION_TEXT 的 key 为 (node, state)）
        nodes = sorted({node for (node, state) in QUESTION_TEXT.keys()})
        self.combo_node.addItems(nodes)
        # 增加默认值
        self.combo_node.insertItem(0, self.tr("请选择节点"))
        self.combo_node.setCurrentIndex(0)
        self.flag = True
        self.combo_node.currentTextChanged.connect(self.on_node_changed)
        form_layout.addRow(self.tr("请选择节点："), self.combo_node)

        self.combo_age = QComboBox()
        self.combo_age.addItems(AGE_OPTIONS)
        form_layout.addRow(self.tr("您的年龄："), self.combo_age)

        self.combo_edu = QComboBox()
        self.combo_edu.addItems(EDU_OPTIONS)
        form_layout.addRow(self.tr("您的教育水平："), self.combo_edu)

        self.combo_workyear = QComboBox()
        self.combo_workyear.addItems(WORK_OPTIONS)
        form_layout.addRow(self.tr("您的工作年限："), self.combo_workyear)

        self.combo_job = QComboBox()
        self.combo_job.addItems(JOB_OPTIONS)
        form_layout.addRow(self.tr("您的工作职位："), self.combo_job)

        main_layout.addLayout(form_layout)


        # 分割线/标题
        sep_label = QLabel(self.tr("请为下列问题进行打分："))
        sep_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        main_layout.addWidget(sep_label)

        #####################################################
        # 2) 问卷表格区域
        #####################################################
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Condition", "Question", "Rating"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        # 隐藏Condition列
        self.table.setColumnHidden(0, True)
        self.apply_table_style(self.table)
        main_layout.addWidget(self.table)
        self.node_answers = {}
        # 当前显示的节点（初始取下拉框默认值）
        self.current_node = self.combo_node.currentText()
        # 加载当前节点的问题并填充表格
        self.load_current_node_questions()

        #####################################################
        # 3) 底部按钮
        #####################################################
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton(self.tr("取消"))
        btn_cancel.setFixedWidth(110)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton(self.tr("保存"))
        btn_save.setFixedWidth(110)
        btn_save.clicked.connect(self.on_save_clicked)
        btn_layout.addWidget(btn_save)

        main_layout.addLayout(btn_layout)

    def apply_table_style(self, table: QTableWidget):
        table.setStyleSheet("""
            QTableWidget {
                border: none;
                font-size: 14px;
                border-bottom: 1px solid black;
                background-color: white;
                alternate-background-color: #e9e7e3;
            }
            QHeaderView::section {
                border-top: 1px solid black;
                border-bottom: 1px solid black;
                background-color: #f0f0f0;
                font-weight: bold;
                padding: 4px;
                color: #333333;
                text-align: center;
            }
            QTableWidget::item {
                border: none;
                padding: 5px;
                text-align: center;
            }
            QTableWidget::item:selected {
                background-color: #cce5ff;
                color: black;
                border: none;
            }
            QTableWidget:focus {
                outline: none;
            }
        """)
        self.force_refresh_table_headers(table)

    def force_refresh_table_headers(self, table: QTableWidget):
        table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                border-top: 1px solid black;
                border-bottom: 1px solid black;
                background-color: #f0f0f0;
                font-weight: bold;
                padding: 4px;
                color: #333333;
                text-align: center;
            }
        """)
        table.horizontalHeader().repaint()

    def load_current_node_questions(self):
        """
        根据当前选中的节点，从 QUESTION_TEXT 中加载对应的问题。
        注意：这里默认 state 为 0。
        """
        node = self.current_node
        key = (node, 0)
        if key in QUESTION_TEXT:
            cond_map = QUESTION_TEXT[key]
            # 将问题转为列表，每一项为 (cond_tuple, question_text)
            self.current_questions = list(cond_map.items())
        else:
            self.current_questions = []
        self.populate_table()

    def populate_table(self):
        """
        根据 self.current_questions 填充表格。
        如果当前节点已保存了答案，则使用保存的评分；否则，默认显示“未评估”。
        """
        self.table.setRowCount(len(self.current_questions))
        # 尝试从 self.node_answers 中加载当前节点的答案
        saved_answers = self.node_answers.get(self.current_node, {})
        for row_idx, (cond_tuple, q_text) in enumerate(self.current_questions):
            # Column 0: Condition（将条件元组转换为列表字符串显示）
            item_cond = QTableWidgetItem(str(list(cond_tuple)))
            item_cond.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row_idx, 0, item_cond)
            # Column 1: Question
            item_q = QTableWidgetItem(q_text)
            item_q.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row_idx, 1, item_q)
            # 鼠标悬停显示完整文本
            item_q.setToolTip(q_text)
            # Column 2: Rating 下拉框
            combo = QComboBox()
            combo.addItems(EVAL_OPTIONS)
            # 如果当前节点已有答案，则按条件显示，否则设为“未评估”
            rating = saved_answers.get(cond_tuple, self.tr("未评估"))
            if rating in EVAL_OPTIONS:
                combo.setCurrentText(rating)
            else:
                combo.setCurrentText(self.tr("未评估"))
            self.table.setCellWidget(row_idx, 2, combo)


    def on_node_changed(self, new_node):
        """
        当节点下拉框改变时，先保存当前节点的问卷答案，再加载新节点的问题。
        """
        if self.flag:
            # 第一次加载时，不需要保存，禁用请选择节点
            self.combo_node.removeItem(0)
            self.current_node = new_node
            self.load_current_node_questions()
            self.flag = False
            return
        # 保存当前节点的答案
        self.save_current_node_answers()
        # 更新当前节点，并加载对应问题
        self.current_node = new_node
        self.load_current_node_questions()

    def save_current_node_answers(self):
        """
        从当前表格中读取数据，保存到 self.node_answers[self.current_node] 中。
        """
        node = self.current_node
        answers = {}
        for row in range(self.table.rowCount()):
            # 第一列为 Condition（字符串形式的列表），解析为 tuple
            cond_str = self.table.item(row, 0).text()
            try:
                cond_list = ast.literal_eval(cond_str)
                cond_tuple = tuple(cond_list)
            except Exception:
                cond_tuple = cond_str
            # 第三列为 Rating，通过下拉框获取
            combo = self.table.cellWidget(row, 2)
            rating = combo.currentText() if combo else self.tr("未评估")
            answers[cond_tuple] = rating
        self.node_answers[node] = answers

    def on_save_clicked(self):
        """
        点击“保存”时，将个人信息和问卷评分分开收集，做后续处理。
        """
        self.save_current_node_answers()

        # 校验各节点数据
        for node, answers in self.node_answers.items():
            ratings = list(answers.values())
            if not ratings:
                continue
            has_unevaluated = any(r == self.tr("未评估") or r.strip() == "" for r in ratings)
            has_evaluated = any(r != self.tr("未评估") and r.strip() != "" for r in ratings)
            if has_unevaluated and has_evaluated:
                CustomWarningDialog(
                    self.tr("警告"), self.tr("节点 {0} 下的问卷问题存在部分未评估与部分已评估，请修正后再保存！").format(node)
                ).exec_()
                return  # 校验失败，不允许保存
        # 获取用户选择的值
        selected_age = self.combo_age.currentText()
        selected_edu = self.combo_edu.currentText()
        selected_workyear = self.combo_workyear.currentText()
        selected_job = self.combo_job.currentText()

        # 检查是否有未选择的个人信息
        if (selected_age == AGE_OPTIONS[0] or
                selected_edu == EDU_OPTIONS[0] or
                selected_workyear == WORK_OPTIONS[0] or
                selected_job == JOB_OPTIONS[0]):
            CustomWarningDialog(self.tr("警告"), self.tr("请完整填写所有个人信息！")).exec_()
            return  # 阻止保存操作

        #####################################################
        # A) 收集个人信息
        #####################################################
        personal_info = {
            "Age": AGE_MAPPING.get(self.combo_age.currentText(), 0),
            "Education": EDU_MAPPING.get(self.combo_edu.currentText(), 0),
            "WorkYear": WORK_MAPPING.get(self.combo_workyear.currentText(), 0),
            "JobPosition": JOB_MAPPING.get(self.combo_job.currentText(), 0),
        }



        #####################################################
        # B) 收集表格里的评分 => expert_rating 多级字典
        #####################################################
        expert_rating = {}
        for node, answers in self.node_answers.items():
            # 如果全部都是“未评估”，则跳过该节点
            if all(r == self.tr("未评估") or r.strip() == "" for r in answers.values()):
                continue
            # 默认 state 为 0
            expert_rating[(node, 0)] = answers

        if not expert_rating:
            CustomWarningDialog(self.tr("警告"), self.tr("请至少为一个节点的问卷问题提供完整评分！")).exec_()
            return
        # 这里只演示打印
        print("\n===== 个人信息 =====")
        print(personal_info)

        print("\n===== 问卷评分 =====")
        print(expert_rating)

        #   1) expert_rating -> 写到 ExpertRating sheet
        expert_estimation_path = os.path.join(self.info_dir, "expert_estimation_data.xlsx")
        df_rating = pd.DataFrame(expert_rating)


        #   2) personal_info -> 写到 ExpertInfo sheet
        expert_info_path = os.path.join(self.info_dir, "expert_info_data.xlsx")

        try:
            with open(expert_info_path, "rb") as f:
                pass  # 仅用于检查文件是否可以访问
        except PermissionError:
            CustomWarningDialog(self.tr("错误"), self.tr("无法访问 expertInfo.xlsx，请关闭 Excel 后重试！")).exec_()
            return

        if os.path.exists(expert_info_path):
            df_info = pd.read_excel(expert_info_path, engine="openpyxl")  # 使用 openpyxl 兼容 Excel
        else:
            df_info = pd.DataFrame(columns=["Expert no.", "Job_title", "Educational_level", "Job_experience", "Age"])

        max_expert_no = df_info["Expert no."].max() if not df_info.empty else 0
        new_expert_no = max_expert_no + 1  # 新增专家编号

        new_expert_data = pd.DataFrame([{
            "Expert no.": new_expert_no,
            "Job_title": personal_info["JobPosition"],
            "Educational_level": personal_info["Education"],
            "Job_experience": personal_info["WorkYear"],
            "Age": personal_info["Age"]
        }])

        df_info = pd.concat([df_info, new_expert_data], ignore_index=True)

        temp_path = expert_info_path + ".tmp.xlsx"
        df_info.to_excel(temp_path, index=False, engine="openpyxl")

        os.replace(temp_path, expert_info_path)

        if os.path.exists(expert_info_path):
            df_info = pd.read_excel(expert_info_path, engine="openpyxl")
            max_expert_no = df_info["Expert no."].max() if not df_info.empty else 1
        else:
            max_expert_no = 1  # 如果 expertInfo.xlsx 不存在，则假设第一位专家

        new_expert_col = f"E{max_expert_no}"  # 新专家列，比如 "E8"

        if os.path.exists(expert_estimation_path):
            df_estimation = pd.read_excel(expert_estimation_path, engine="openpyxl")
        else:
            df_estimation = pd.DataFrame(columns=["Node", "Condition", "State"])

        if new_expert_col not in df_estimation.columns:
            df_estimation[new_expert_col] = ""

        for (node, state), cond_map in expert_rating.items():
            for cond_tuple, rating in cond_map.items():
                condition_str = str(list(cond_tuple))  # 转换为字符串 "[x, y]"

                # 找到 DataFrame 里对应的行
                mask = (df_estimation["Node"] == node) & (df_estimation["Condition"] == condition_str) & (
                            df_estimation["State"] == state)

                # 如果匹配到行，则写入评分，否则跳过
                if mask.any():
                    if rating != self.tr("未评估"):  # 如果不是 "未评估"，才写入
                        df_estimation.loc[mask, new_expert_col] = rating

        df_estimation.to_excel(expert_estimation_path, index=False, engine="openpyxl")

        self.parent.updated = True


        CustomInformationDialog(self.tr("成功"), self.tr("已成功获取个人信息与问卷评分。")).exec_()

        self.accept()  # 关闭对话框


class NonRootTableUpdateDialog(QDialog):
    def __init__(self, info_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("更新非根节点先验数据"))
        self.resize(850, 700)

        self.info_dir = info_dir
        self.expert_excel_path = os.path.join(self.info_dir, "expert_estimation_data.xlsx")
        self.parent = parent

        # 1) 从Excel中探测已有专家数量，以及加载已有数据
        self.num_experts = self.load_expert_count()
        self.existing_expert_data = self.load_existing_expert_data()

        # 2) 在内存中维护一个大字典，存放“所有节点”的问卷结果
        #    结构: { (nodeName, stateInt): { tuple_condition: [expertVal,...], ... }, ... }
        self.all_node_data = {}

        # 根据已有 Excel 数据，先把它解析到 all_node_data
        self.init_all_node_data()

        self.init_ui()
        self.current_node = None
        self.current_state = None
        self.prev_node = 'AbsorptionCapacity'
        self.prev_state = 0


    def load_expert_count(self):
        try:
            if os.path.exists(self.expert_excel_path):
                df = pd.read_excel(self.expert_excel_path)
                num_experts = df.shape[1] - 3
                return num_experts if num_experts > 0 else 7
        except Exception as e:
            print("加载专家Excel失败：", e)
        return 7

    def load_existing_expert_data(self):
        """
        返回 { (node, conditionStr, stateInt): [expertVals], ... }
        其中 conditionStr 形如 '[0, 1]'，expertVals 是字符串列表
        """
        existing_data = {}
        if not os.path.exists(self.expert_excel_path):
            return existing_data

        try:
            df = pd.read_excel(self.expert_excel_path)
            for index, row in df.iterrows():
                node = str(row["Node"]).strip()
                condition_raw = row["Condition"]
                try:
                    cond_list = ast.literal_eval(str(condition_raw))
                except Exception as e:
                    cond_list = condition_raw

                if isinstance(cond_list, list):
                    parents = NONROOT_PARENTS.get(node, [])
                    if len(parents) == len(cond_list):
                        numeric_cond = []
                        for p, val in zip(parents, cond_list):
                            val_str = str(val).strip()
                            try:
                                numeric_val = int(val_str)
                            except:
                                # 如果不是数字，尝试到 STATE_OPTIONS 里找
                                options = STATE_OPTIONS.get(p, [])
                                found = False
                                for idx, opt in enumerate(options):
                                    if str(opt).strip() == val_str:
                                        numeric_val = idx
                                        found = True
                                        break
                                if not found:
                                    numeric_val = -1
                            numeric_cond.append(numeric_val)
                        condition = str(numeric_cond)
                    else:
                        condition = str(cond_list)
                else:
                    condition = str(condition_raw).strip()

                try:
                    state = int(row["State"])
                except Exception:
                    state = row["State"]

                # 读取专家列
                expert_vals = []
                for col in df.columns[3:]:
                    val = str(row[col]).strip()
                    if val.lower() in ("nan", "none"):
                        val = ""
                    expert_vals.append(val)

                key = (node, condition, state)
                existing_data[key] = expert_vals
        except Exception as e:
            print("加载已有专家数据失败：", e)

        print(f"已加载的专家数据：\n{existing_data}")
        return existing_data

    def init_all_node_data(self):
        """
        把 self.existing_expert_data 的内容解析进 self.all_node_data
        结构: { (node, state): { tuple_condition: [expertVal, ...], ... }, ... }
        """
        for (node, cond_str, state_int), expert_vals in self.existing_expert_data.items():
            # cond_str 形如 '[0, 1]'
            try:
                cond_tuple = tuple(ast.literal_eval(cond_str))  # (0,1)
            except:
                cond_tuple = cond_str

            ns_key = (node, state_int)
            if ns_key not in self.all_node_data:
                self.all_node_data[ns_key] = {}
            self.all_node_data[ns_key][cond_tuple] = expert_vals
        print(f"初始化的 all_node_data：\n{self.all_node_data}")

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        header = QLabel(self.tr("更新非根节点先验数据（问卷填写）"))
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("SimSun", 16, QFont.Bold))
        main_layout.addWidget(header)

        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel(self.tr("非根节点：")))
        self.combo_nonroot = QComboBox()
        self.combo_nonroot.addItems(list(NONROOT_PARENTS.keys()))
        # 当节点变化时，需要先保存当前表格，再生成新表格
        self.combo_nonroot.currentTextChanged.connect(self.on_nonroot_changed)
        select_layout.addWidget(self.combo_nonroot)

        select_layout.addSpacing(20)

        #select_layout.addWidget(QLabel("目标状态："))
        self.combo_state = QComboBox()
        self.combo_state.addItems(["Good", "Bad"])
        # 同理 state 改变时，也先保存当前表格，再更新
        self.combo_state.currentTextChanged.connect(self.on_state_changed)
        #select_layout.addWidget(self.combo_state)
        select_layout.addStretch()
        main_layout.addLayout(select_layout)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(1 + self.num_experts)
        header_labels = [self.tr("条件")] + [self.tr("专家{0}").format(i + 1) for i in range(self.num_experts)]
        self.table.setHorizontalHeaderLabels(header_labels)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        for i in range(1, self.num_experts+1):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        main_layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton(self.tr("取消"))
        btn_cancel.setFixedWidth(110)
        btn_ok = QPushButton(self.tr("确定"))
        btn_ok.setFixedWidth(110)
        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self.on_ok_clicked)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        main_layout.addLayout(btn_layout)

        # 初次显示表格
        self.generate_table()

    # =========== 关键：在切换节点/状态前后，先保存当前表格，再生成新表格 ===========

    def on_nonroot_changed(self):
        """当非根节点选择发生变化时，先保存当前表格数据，再重新生成表格。"""
        # 切换之前的节点名字

        self.retrieve_table_data()
        self.generate_table()
        self.prev_node = self.current_node
        self.prev_state = self.current_state

    def on_state_changed(self):
        """当目标状态选择发生变化时，先保存当前表格数据，再重新生成表格。"""

        self.retrieve_table_data()
        self.generate_table()
        self.prev_node = self.current_node
        self.prev_state = self.current_state

    # =========== 从表格读取 / 向表格写入 ===========

    def retrieve_table_data(self,current_mode=False):
        """
        从当前表格中读取数据，保存到 self.all_node_data[(当前node, 当前state)] 中
        """
        self.current_node = self.combo_nonroot.currentText()
        self.current_state = 0 if self.combo_state.currentText() == "Good" else 1
        if self.table.rowCount() == 0:
            return

        if current_mode:
            node = self.current_node
            state = self.current_state
        else:
            node = self.prev_node
            state = self.prev_state
        ns_key = (node, state)
        # print(f"保存表格数据：{ns_key}, {self.current_node}, {self.current_state}, {self.prev_node}, {self.prev_state}")
        if ns_key not in self.all_node_data:
            self.all_node_data[ns_key] = {}

        for row in range(self.table.rowCount()):
            condition_item = self.table.item(row, 0)
            if not condition_item:
                continue

            # condition_item.text() 形如: "xxx\n[0,1]"
            text = condition_item.text().splitlines()[-1]
            try:
                cond_tuple = tuple(ast.literal_eval(text))
            except:
                cond_tuple = text

            # 读取所有专家的下拉框
            expert_vals = []
            for col in range(1, 1 + self.num_experts):
                widget = self.table.cellWidget(row, col)
                val = widget.currentText().strip() if widget else self.tr("未评估")
                expert_vals.append(val)

            self.all_node_data[ns_key][cond_tuple] = expert_vals
            # print(f"保存数据：{ns_key} / {cond_tuple} => {expert_vals}")

    def generate_table(self):
        """
        根据当前combo的node & state，从 all_node_data 中加载数据到表格。
        如果没有，默认“未评估”。
        """
        current_node = self.combo_nonroot.currentText()
        current_state = 0 if self.combo_state.currentText() == "Good" else 1
        ns_key = (current_node, current_state)
        # print(f"生成表格：{ns_key}")

        parents = NONROOT_PARENTS.get(current_node, [])
        if not parents:
            self.table.setRowCount(0)
            return

        parent_options = [STATE_OPTIONS.get(p, []) for p in parents]
        combinations = list(product(*parent_options))
        # print(f"当前节点的所有条件组合：{combinations}")
        self.table.setRowCount(len(combinations))

        # 拿到已经暂存的数据，如果没有就给个空dict
        node_data_dict = self.all_node_data.get(ns_key, {})
        # print(f"当前节点的已有数据：{node_data_dict}")

        for row, comb in enumerate(combinations):
            # numeric_comb = [0,1,...]
            numeric_comb = [STATE_OPTIONS[p].index(val) for p, val in zip(parents, comb)]
            condition_str = str(numeric_comb)
            cond_desc = " & ".join([f"{p}={v}" for p, v in zip(parents, comb)])
            item = QTableWidgetItem(f"{cond_desc}\n{condition_str}")
            item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 0, item)
            # 设置鼠标悬停提示
            item.setToolTip(cond_desc)

            # 在 all_node_data 里查找对应的专家值
            cond_tuple = tuple(numeric_comb)
            expert_vals = node_data_dict.get(cond_tuple, None)

            for col in range(1, 1 + self.num_experts):
                combo = QComboBox()
                combo.addItems(EVAL_OPTIONS)
                if expert_vals and (col - 1) < len(expert_vals):
                    val = expert_vals[col - 1]
                    if val in EVAL_OPTIONS:
                        combo.setCurrentText(val)
                    else:
                        combo.setCurrentText(self.tr("未评估"))
                else:
                    combo.setCurrentText(self.tr("未评估"))

                self.table.setCellWidget(row, col, combo)

        self.apply_table_style(self.table)

    def apply_table_style(self, table: QTableWidget):
        table.setStyleSheet("""
            QTableWidget {
                border: none;
                font-size: 14px;
                border-bottom: 1px solid black;
                background-color: white;
                alternate-background-color: #e9e7e3;
            }
            QHeaderView::section {
                border-top: 1px solid black;
                border-bottom: 1px solid black;
                background-color: #f0f0f0;
                font-weight: bold;
                padding: 4px;
                color: #333333;
                text-align: center;
            }
            QTableWidget::item {
                border: none;
                padding: 5px;
                text-align: center;
            }
            QTableWidget::item:selected {
                background-color: #cce5ff;
                color: black;
                border: none;
            }
            QTableWidget:focus {
                outline: none;
            }
        """)
        self.force_refresh_table_headers(table)

    def force_refresh_table_headers(self, table: QTableWidget):
        table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                border-top: 1px solid black;
                border-bottom: 1px solid black;
                background-color: #f0f0f0;
                font-weight: bold;
                padding: 4px;
                color: #333333;
                text-align: center;
            }
        """)
        table.horizontalHeader().repaint()

    # =========== 最终点击“确定” => 把当前表格也存起来，然后一次性校验 & 保存 ===========

    def on_ok_clicked(self):
        # 先保存当前表格的内容到内存
        self.retrieve_table_data(current_mode=True)

        # 执行整体校验 + 保存
        success = self.validate_and_save_all_data()
        if success:
            if self.parent:
                self.parent.updated = True
            self.accept()

    def validate_and_save_all_data(self):
        """
        对 self.all_node_data 中所有非根节点数据进行校验，然后统一保存到 Excel。

        校验规则：
          1) 对于每个 (node, state) 下的所有条件组合，按专家列检查：
               - 如果某一专家列在所有条件组合中既存在“未评估”（或空字符串）又存在具体评估值，
                 则提示错误，不允许保存。
          2) 对于整行都是“未评估”的条件组合，则跳过不保存。
          3) 其余情况，将所有数据行合并后保存。
        """
        rows_to_save = []
        # 遍历所有非根节点的数据
        for (node, state_int), cond_map in self.all_node_data.items():
            if not cond_map:
                continue

            # 先按专家列进行校验（当前节点下所有条件组合的数据均参与校验）
            # 这里每一行 expert_vals 为长度为 num_experts 的列表
            data_rows = list(cond_map.values())
            for expert_index in range(self.num_experts):
                # 收集当前专家列在所有条件组合中的评分
                col_vals = [row[expert_index] for row in data_rows if len(row) > expert_index]
                if not col_vals:
                    continue  # 若该列没有数据则跳过
                has_unevaluated = any(val == self.tr("未评估") or val.strip() == "" for val in col_vals)
                has_evaluated = any(val != self.tr("未评估") and val.strip() != "" for val in col_vals)
                if has_unevaluated and has_evaluated:
                    CustomWarningDialog(
                        self.tr("警告"),
                        self.tr("节点 {0} / 中，第 {1} 位专家存在部分已评估与部分未评估的混合，请修正后再保存。").format(
                            node, expert_index + 1)
                    ).exec_()
                    return False

            # 对于当前节点的每一行数据，若整行都是“未评估”，则跳过，否则构造保存用的数据行
            for cond_tuple, expert_vals in cond_map.items():
                if all(val == self.tr("未评估") or val.strip() == "" for val in expert_vals):
                    continue  # 整行都未评估，则不保存
                row_dict = {
                    "Node": node,
                    "Condition": str(list(cond_tuple)),  # 例如 "[0, 1]"
                    "State": state_int
                }
                for i, val in enumerate(expert_vals):
                    if val == self.tr("未评估"):
                        val = ""
                    row_dict[f"E{i + 1}"] = val
                rows_to_save.append(row_dict)

        # 若校验全部通过，则将所有节点的数据一次性保存到 Excel
        try:
            if os.path.exists(self.expert_excel_path):
                df_old = pd.read_excel(self.expert_excel_path, engine="openpyxl")
            else:
                cols = ["Node", "Condition", "State"] + [f"E{i + 1}" for i in range(self.num_experts)]
                df_old = pd.DataFrame(columns=cols)
            df_final = pd.DataFrame(rows_to_save, columns=df_old.columns)
            print(f"最终保存的数据：\n{df_final}")
            df_final.to_excel(self.expert_excel_path, index=False, engine="openpyxl")
            CustomInformationDialog(self.tr("成功"), self.tr("所有非根节点问卷数据已校验并保存到 Excel。")).exec_()
            return True
        except Exception as e:
            CustomErrorDialog(self.tr("错误"), self.tr("保存Excel文件时发生错误：{0}").format(str(e))).exec_()
            return False


# ===================== 主选择界面 =====================
class MainUpdateDialog(QDialog):
    def __init__(self, info_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("类型选择"))
        # 使用最小尺寸
        self.resize(100, 50)
        self.updated = False
        layout = QVBoxLayout(self)
        # header = QLabel("请选择更新先验数据的类型：")
        # header.setAlignment(Qt.AlignCenter)
        # # 使用宋体
        # font = QFont("SimSun", 14, QFont.Bold)
        # layout.addWidget(header)
        btn_root = QPushButton(self.tr("更新根节点"))
        btn_nonroot = QPushButton(self.tr("更新非根节点"))
        # 固定宽度为110
        btn_root.setFixedWidth(110)
        btn_nonroot.setFixedWidth(110)
        btn_root.clicked.connect(self.open_root_dialog)
        btn_nonroot.clicked.connect(self.open_nonroot_dialog)
        layout.addWidget(btn_root)
        layout.addWidget(btn_nonroot)
        layout.addStretch()
        self.info_dir = info_dir
        if get_cfg()['i18n']['language'] == 'en_US':
            self.resize(220, 50)
            btn_root.setFixedWidth(210)
            btn_nonroot.setFixedWidth(210)

    def open_root_dialog(self):

        dialog = RootUpdateDialog(self.info_dir, self)
        dialog.exec()

    def open_nonroot_dialog(self):
        dialog = NonRootActionDialog(self.info_dir, self)
        dialog.exec()


class UploadExpertDialog(QDialog):
    """
    文件上传对话框：
      1. 提供上传文件按钮，用于选择待上传的 Excel 文件（xlsx/xls）。
      2. 显示已选择的文件名称。
      3. 包含“确定”与“取消”按钮（“确定”后的具体上传逻辑暂留空）。
    """
    def __init__(self, info_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("上传专家意见"))
        self.resize(400, 200)
        self.info_dir = info_dir
        self.parent = parent
        self.selected_file = None  # 用于存储选中的文件路径

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # 文件上传区域：上传按钮 + 文件名称显示区域
        file_layout = QHBoxLayout()
        self.btn_select_file = QPushButton(self.tr("选择文件"))
        self.btn_select_file.setFixedWidth(110)
        self.btn_select_file.clicked.connect(self.select_file)
        file_layout.addWidget(self.btn_select_file)

        self.file_label = QLabel(self.tr("未选择文件"))
        file_layout.addWidget(self.file_label)
        file_layout.addStretch()
        main_layout.addLayout(file_layout)

        # 底部按钮区域：确定和取消按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton(self.tr("取消"))
        self.btn_cancel.setFixedWidth(110)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_ok = QPushButton(self.tr("确定"))
        self.btn_ok.setFixedWidth(110)
        self.btn_ok.clicked.connect(self.on_ok)
        btn_layout.addWidget(self.btn_ok)

        main_layout.addLayout(btn_layout)

    def select_file(self):
        """
        点击“选择文件”按钮后，弹出文件对话框选择 Excel 文件，
        选定后在标签中显示文件名称，并保存文件路径。
        """
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Excel Files (*.xlsx *.xls)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.selected_file = selected_files[0]
                self.file_label.setText(os.path.basename(self.selected_file))
                self.file_label.setStyleSheet("color: #27ae60;")

    def on_ok(self):
        """
        点击“确定”后，解析上传的 XLSX 文件，
        对专家个人信息和问卷评分进行校验：
          - 个人信息：年龄、教育水平、工作年限答案必须为 A/B/C/D，
            工作职位答案必须为 A/B/C/D/E（不区分大小写）。
          - 问卷评分：每个题目的评分必须为 VL/L/M/H/VH（不区分大小写）。
        校验通过后，将解析结果打印出来。
        """
        if not self.selected_file:
            CustomWarningDialog(self.tr("警告"), self.tr("请先选择文件！")).exec_()
            return

        try:
            # 读取整个 Excel 文件（不设定表头，便于后续手动分区）
            df = pd.read_excel(self.selected_file, header=None, engine="openpyxl")

            # 查找第一列中包含“节点”的行作为问卷数据的标题行
            header_indices = df.index[
                df.iloc[:, 0].astype(str).str.strip().str.contains(self.tr("节点"), na=False)
            ].tolist()
            if not header_indices:
                raise ValueError(self.tr("未能在上传文件中找到问卷数据标题行 '节点'"))
            header_row = header_indices[0]

            # -------------------------------
            # 1. 解析并校验专家个人信息（前 4 行）
            expert_info_df = df.iloc[:header_row, :].copy()
            # 假设每一行第三列（索引2）为专家填写的答案
            raw_age = str(expert_info_df.iloc[0, 2]).strip()
            raw_edu = str(expert_info_df.iloc[1, 2]).strip()
            raw_work = str(expert_info_df.iloc[2, 2]).strip()
            raw_job = str(expert_info_df.iloc[3, 2]).strip()

            # 自动转大写
            ans_age = raw_age.upper()
            ans_edu = raw_edu.upper()
            ans_work = raw_work.upper()
            ans_job = raw_job.upper()

            # 校验答案是否合法
            valid_ADE = {"A", "B", "C", "D"}
            valid_job = {"A", "B", "C", "D", "E"}
            if ans_age not in valid_ADE:
                CustomWarningDialog(self.tr("警告"), self.tr("个人信息：年龄答案不合法，必须是 A、B、C 或 D！")).exec_()
                return
            if ans_edu not in valid_ADE:
                CustomWarningDialog(self.tr("警告"), self.tr("个人信息：教育水平答案不合法，必须是 A、B、C 或 D！")).exec_()
                return
            if ans_work not in valid_ADE:
                CustomWarningDialog(self.tr("警告"), self.tr("个人信息：工作年限答案不合法，必须是 A、B、C 或 D！")).exec_()
                return
            if ans_job not in valid_job:
                CustomWarningDialog(self.tr("警告"), self.tr("个人信息：工作职位答案不合法，必须是 A、B、C、D 或 E！")).exec_()
                return

            # 根据答案构造个人信息（此处使用自定义映射：A->1, B->2, C->3, D->4；工作职位 A-E映射为1-5）
            personal_info = {
                "Age": {"A": 1, "B": 2, "C": 3, "D": 4}[ans_age],
                "Education": {"A": 1, "B": 2, "C": 3, "D": 4}[ans_edu],
                "WorkYear": {"A": 1, "B": 2, "C": 3, "D": 4}[ans_work],
                "JobPosition": {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}[ans_job]
            }

            print("===== 个人信息 =====")
            print(personal_info)

            # -------------------------------
            # 2. 解析并校验问卷数据部分（标题行及之后）
            df_questionnaire = pd.read_excel(self.selected_file, header=header_row, engine="openpyxl")
            # 判断评分列：如果存在"评分"列则使用，否则使用第三列
            if "评分" in df_questionnaire.columns:
                rating_col = self.tr("评分")
            else:
                rating_col = df_questionnaire.columns[2]

            expert_rating = {}
            current_node = None
            reverse_map = {}  # 当前节点下的反向映射：归一化问句 -> 条件元组

            # 有效评分集合（注意自动转大写）
            valid_ratings = {"VL", "L", "M", "H", "VH"}

            # 遍历问卷数据
            for idx, row in df_questionnaire.iterrows():
                # 如果“节点”列有值，则更新当前节点
                node_val = str(row["节点"]).strip() if pd.notnull(row["节点"]) else ""
                if node_val:
                    current_node = node_val
                    expert_rating[(current_node, 0)] = {}
                    # 构造当前节点的反向映射（使用预定义的 QUESTION_TEXT）
                    reverse_map = {}
                    if (current_node, 0) in QUESTION_TEXT:
                        for cond, q_text in QUESTION_TEXT[(current_node, 0)].items():
                            norm_q = q_text.replace(" ", "").replace("\n", "")
                            reverse_map[norm_q] = cond
                    else:
                        reverse_map = {}

                # 解析题目文本和评分
                question_text = str(row["问题"]).strip()
                raw_rating = str(row[rating_col]).strip()
                if not raw_rating:
                    CustomWarningDialog(self.tr("警告"), self.tr("问卷题目 '{0}' 缺失评分，请补充完整！").format(question_text)).exec_()
                    return
                rating = raw_rating.upper()
                if rating not in valid_ratings:
                    CustomWarningDialog(self.tr("警告"),
                                        self.tr("问卷题目 '{0}' 的评分不合法（{1}），必须是 VL, L, M, H 或 VH！").format(question_text,raw_rating)).exec_()
                    return

                # 归一化题目文本进行匹配
                norm_question = question_text.replace(" ", "").replace("\n", "")
                matched = False
                for norm_q, cond_tuple in reverse_map.items():
                    if norm_question in norm_q or norm_q in norm_question:
                        expert_rating[(current_node, 0)][cond_tuple] = rating
                        matched = True
                        break
                if not matched:
                    print(self.tr("警告：无法匹配题目文本: {0} 在节点 {1}").format(question_text, current_node))

            print("===== 问卷评分 =====")
            print(expert_rating)

            #   1) expert_rating -> 写到 ExpertRating sheet
            expert_estimation_path = os.path.join(self.info_dir, "expert_estimation_data.xlsx")
            df_rating = pd.DataFrame(expert_rating)

            #   2) personal_info -> 写到 ExpertInfo sheet
            expert_info_path = os.path.join(self.info_dir, "expert_info_data.xlsx")

            try:
                with open(expert_info_path, "rb") as f:
                    pass  # 仅用于检查文件是否可以访问
            except PermissionError:
                CustomWarningDialog(self.tr("错误"), self.tr("无法访问 expertInfo.xlsx，请关闭 Excel 后重试！")).exec_()
                return

            if os.path.exists(expert_info_path):
                df_info = pd.read_excel(expert_info_path, engine="openpyxl")  # 使用 openpyxl 兼容 Excel
            else:
                df_info = pd.DataFrame(
                    columns=["Expert no.", "Job_title", "Educational_level", "Job_experience", "Age"])

            max_expert_no = df_info["Expert no."].max() if not df_info.empty else 0
            new_expert_no = max_expert_no + 1  # 新增专家编号

            new_expert_data = pd.DataFrame([{
                "Expert no.": new_expert_no,
                "Job_title": personal_info["JobPosition"],
                "Educational_level": personal_info["Education"],
                "Job_experience": personal_info["WorkYear"],
                "Age": personal_info["Age"]
            }])

            df_info = pd.concat([df_info, new_expert_data], ignore_index=True)

            temp_path = expert_info_path + ".tmp.xlsx"
            df_info.to_excel(temp_path, index=False, engine="openpyxl")

            os.replace(temp_path, expert_info_path)

            if os.path.exists(expert_info_path):
                df_info = pd.read_excel(expert_info_path, engine="openpyxl")
                max_expert_no = df_info["Expert no."].max() if not df_info.empty else 1
            else:
                max_expert_no = 1  # 如果 expertInfo.xlsx 不存在，则假设第一位专家

            new_expert_col = f"E{max_expert_no}"  # 新专家列，比如 "E8"

            if os.path.exists(expert_estimation_path):
                df_estimation = pd.read_excel(expert_estimation_path, engine="openpyxl")
            else:
                df_estimation = pd.DataFrame(columns=["Node", "Condition", "State"])

            if new_expert_col not in df_estimation.columns:
                df_estimation[new_expert_col] = ""

            for (node, state), cond_map in expert_rating.items():
                for cond_tuple, rating in cond_map.items():
                    condition_str = str(list(cond_tuple))  # 转换为字符串 "[x, y]"

                    # 找到 DataFrame 里对应的行
                    mask = (df_estimation["Node"] == node) & (df_estimation["Condition"] == condition_str) & (
                            df_estimation["State"] == state)

                    # 如果匹配到行，则写入评分，否则跳过
                    if mask.any():
                        if rating != self.tr("未评估"):  # 如果不是 "未评估"，才写入
                            df_estimation.loc[mask, new_expert_col] = rating

            df_estimation.to_excel(expert_estimation_path, index=False, engine="openpyxl")

            self.parent.updated = True

            CustomInformationDialog(self.tr("成功"), self.tr("已成功获取个人信息与问卷评分。")).exec_()

            self.accept()
        except Exception as e:
            CustomErrorDialog(self.tr("错误"), self.tr("处理上传文件时发生错误：{0}").format(str(e))).exec_()
            return


class NonRootActionDialog(QDialog):
    def __init__(self, info_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("非根节点操作选择"))
        self.resize(100, 70)
        self.info_dir = info_dir
        self.parent = parent

        layout = QVBoxLayout(self)

        # 两个按钮
        btn_modify = QPushButton(self.tr("修改专家意见"))
        btn_add = QPushButton(self.tr("增加专家意见"))
        btn_upload = QPushButton(self.tr("上传专家意见"))
        # 固定宽度为110
        btn_modify.setFixedWidth(110)
        btn_add.setFixedWidth(110)
        btn_upload.setFixedWidth(110)
        if get_cfg()['i18n']['language'] == 'en_US':
            self.resize(280, 70)
            btn_modify.setFixedWidth(270)
            btn_add.setFixedWidth(270)
            btn_upload.setFixedWidth(270)

        btn_modify.clicked.connect(self.open_modify_dialog)
        btn_add.clicked.connect(self.open_add_dialog)
        btn_upload.clicked.connect(self.open_upload_dialog)

        layout.addWidget(btn_modify)
        layout.addWidget(btn_add)
        layout.addWidget(btn_upload)
        layout.addStretch()

    def open_modify_dialog(self):
        """
        修改专家意见 => 打开现有的 NonRootTableUpdateDialog
        """
        dialog = NonRootTableUpdateDialog(self.info_dir, self.parent)
        dialog.exec()
        # 可以在这里根据需要判断是否需要关闭当前对话框
        # self.accept()

    def open_add_dialog(self):
        """
        增加专家意见 => 这里演示一个示例对话框，用于添加一个新专家列
        """
        dialog = AddExpertDialog(self.info_dir, self.parent)
        dialog.exec()
        # 同理可在此处做后续逻辑
        # self.accept()
        
    def open_upload_dialog(self):
        """
        上传专家意见 => 这里演示一个示例对话框，用于上传一个新专家列
        """
        dialog = UploadExpertDialog(self.info_dir, self.parent)
        dialog.exec()
        # 同理可在此处做后续逻辑
        # self.accept()


# ===================== 根节点更新界面（简化示例） =====================
class RootUpdateDialog(QDialog):
    def __init__(self, info_dir,parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("更新根节点先验"))
        self.resize(500, 300)
        self.info_dir = info_dir
        self.parent = parent
        layout = QVBoxLayout(self)
        instruction = QLabel(self.tr("请选择包含根节点先验数据的事故数据Excel文件："))
        layout.addWidget(instruction)
        self.btn_select_file = QPushButton(self.tr("选择文件"))
        self.btn_select_file.setFixedWidth(110)
        self.btn_select_file.clicked.connect(self.select_file)
        layout.addWidget(self.btn_select_file)
        self.file_label = QLabel(self.tr("未选择文件"))
        layout.addWidget(self.file_label)
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton(self.tr("确定"))
        self.btn_ok.setFixedWidth(110)
        self.btn_cancel = QPushButton(self.tr("取消"))
        self.btn_cancel.setFixedWidth(110)
        self.btn_ok.clicked.connect(self.on_ok)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)
        layout.addLayout(btn_layout)

    def select_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Excel Files (*.xlsx *.xls)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.selected_file = selected_files[0]
                self.file_label.setText(os.path.basename(self.selected_file))
                self.file_label.setStyleSheet("color: #27ae60;")

    def on_ok(self):
        if not hasattr(self, "selected_file") or not self.selected_file:

            CustomWarningDialog(self.tr("警告"), self.tr("请先选择事故数据文件！")).exec_()
            return
        # 把info_dir/prior prob test.xlsx替换掉
        try:
            # 读取Excel文件
            df = pd.read_excel(self.selected_file)
            # 保存到新的文件
            new_file = os.path.join(self.info_dir, "root_prior_data.xlsx")
            df.to_excel(new_file, index=False)

            CustomInformationDialog(self.tr("成功"), self.tr("根节点先验数据已更新并保存到 Excel。")).exec_()
        except Exception as e:
            CustomErrorDialog(self.tr("错误"), self.tr("保存Excel文件时发生错误：{0}").format(str(e))).exec_()
        self.parent.updated = True
        self.accept()


# ===================== 主程序入口 =====================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(245, 246, 250))
    palette.setColor(QPalette.WindowText, QColor(44, 62, 80))
    app.setPalette(palette)
    info_dir = r"D:\PythonProjects\AcademicTool_PySide\data"
    main_dialog = MainUpdateDialog(info_dir)
    main_dialog.exec()  # 进入主对话框

    # 在对话框关闭后，根据 updated 标记执行动作
    if main_dialog.updated:
        print("先验更新处理完毕")
        # 在这里添加其他你需要执行的操作
    else:
        print("没有更新先验数据")
    sys.exit(app.exec())
