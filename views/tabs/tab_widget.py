# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:11 AM
# @FileName: tab_widget.py
# @Software: PyCharm
import os

import rdflib
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot
from owlready2 import get_ontology, destroy_entity

from test6 import convert_owl_to_svg
from utils.combinesysml2 import combine_sysml2
from utils.json2owl import create_ontology, owl_excel_creator, Scenario_owl_creator, Emergency_owl_creator
from utils.parserowl import parse_owl

from utils.sysml2json import process_file
from views.tabs.element_setting import ElementSettingTab
from views.tabs.model_generation import ModelGenerationTab
from views.tabs.model_transformation import ModelTransformationTab
from views.tabs.condition_setting import ConditionSettingTab


class CustomTabWidget(QWidget):
    tab_changed = Signal(int)
    generate_model_save_to_database = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.init_ui()
        self.ElementSettingTab.generate_model_show.connect(self.generate_model)
        self.ModelGenerationTab.generate_request.connect(self.generate_bayes)
        self.ModelTransformationTab.set_inference_request.connect(self.set_inference_conditions)



    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.tab_buttons_widget = QWidget()
        self.tab_buttons_widget.setObjectName("TabButtonsWidget")
        self.tab_buttons_layout = QHBoxLayout(self.tab_buttons_widget)
        self.tab_buttons_layout.setSpacing(0)
        self.tab_buttons_layout.setContentsMargins(0, 0, 0, 0)


        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("ContentStack")
        self.content_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.ElementSettingTab = ElementSettingTab()
        self.ModelGenerationTab = ModelGenerationTab()
        self.ModelTransformationTab = ModelTransformationTab()
        self.ConditionSettingTab = ConditionSettingTab()

        self.tabs = []
        self.add_tab(self.tr("情景要素设定"), self.ElementSettingTab)
        self.add_tab(self.tr("情景模型生成"), self.ModelGenerationTab)
        self.add_tab(self.tr("推演模型转换"), self.ModelTransformationTab)
        self.add_tab(self.tr("推演条件设定"), self.ConditionSettingTab)



        self.placeholder = QWidget()
        placeholder_layout = QVBoxLayout(self.placeholder)
        placeholder_layout.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet("""
    border-radius: 10px; /* 圆角边框 */
    """)

        self.placeholder_label = QLabel("")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setObjectName("PlaceholderLabel")

        placeholder_layout.addWidget(self.placeholder_label)

        self.content_stack.addWidget(self.placeholder)
        self.content_stack.setCurrentWidget(self.placeholder)

        main_layout.addWidget(self.tab_buttons_widget)
        main_layout.addWidget(self.content_stack)

        self.tab_buttons_widget.setVisible(False)

    def set_border(self):
        """设置边框样式"""
        self.content_stack.setStyleSheet("""QStackedWidget {
    border: 2px solid dark; /* 边框颜色 */
    border-radius: 10px; /* 圆角边框 */
}""")

    def add_tab(self, tab_name, content_widget):
        button = QPushButton(self.tr(tab_name))
        button.setObjectName(f"{tab_name}Button")
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setCheckable(True)
        button.clicked.connect(lambda checked, idx=len(self.tabs)+1: self.switch_tab(idx))
        # 设置固定高度以保持一致性
        button.setFixedHeight(32)
        # 样式根据 tab_name 判断，但这些判断字符串并非直接展示给用户，仅用于条件判断，不添加 tr()
        if tab_name in [self.tr("情景模型生成")]:
            button.setStyleSheet("""
                border: 2px solid dark; /* 边框颜色 */
                border-radius: 10px; /* 圆角边框 */
                background-color: transparent; /* 背景透明 */
                color: #333333; /* 文字颜色 */
                font-size: 18px; /* 文字大小 */
                font-weight: bold; /* 文字加粗 */
                    padding: 5px;
                border-top-left-radius: 0px; /* 左上角直角 */
                border-top-right-radius: 0px; /* 右上角直角 */
                border-bottom: none; /* 下方没有边框 */
                border-bottom-left-radius: 0; /* 左下角直角 */
                border-bottom-right-radius: 0; /* 右下角直角 */
            }

            QPushButton:checked {
                background-color: #5dade2; /* 选中时的背景颜色 */
                color: white; /* 选中时的文字颜色 */
                border: 2px solid dark; /* 选中时边框颜色 */
                border-bottom: none; /* 下方没有边框 */
            }

            QPushButton:hover {
                background-color: #B0E2FF; /* 鼠标悬停时的背景颜色 */
                border: 2px solid dark; /* 鼠标悬停时边框颜色 */
                border-bottom: none; /* 下方没有边框 */
            }

            QPushButton:pressed {
                background-color: #5dade2; /* 鼠标按下时的背景颜色 */
                border: 2px solid dark;
                border-bottom: none; /* 下方没有边框 */}
            """)
        elif tab_name in [self.tr("推演模型转换")]:
            button.setStyleSheet("""
                            border: 2px solid dark; /* 边框颜色 */
                            border-radius: 10px; /* 圆角边框 */
                            background-color: transparent; /* 背景透明 */
                            color: #333333; /* 文字颜色 */
                            font-size: 18px; /* 文字大小 */
                            font-weight: bold; /* 文字加粗 */
                            border-top-left-radius: 0px; /* 左上角直角 */
                                padding: 5px;
                            border-top-right-radius: 0px; /* 右上角直角 */
                            border-bottom: none; /* 下方没有边框 */
                            border-left: none; /* 左侧没有边框 */
                            border-bottom-left-radius: 0; /* 左下角直角 */
                            border-bottom-right-radius: 0; /* 右下角直角 */
                        }

            QPushButton:checked {
                background-color: #5dade2; /* 选中时的背景颜色 */
                color: white; /* 选中时的文字颜色 */
                border: 2px solid dark; /* 选中时边框颜色 */
                border-bottom: none; /* 下方没有边框 */
                border-left: none; /* 左侧没有边框 */
            }

            QPushButton:hover {
                background-color: #B0E2FF; /* 鼠标悬停时的背景颜色 */
                border: 2px solid dark; /* 鼠标悬停时边框颜色 */
                border-bottom: none; /* 下方没有边框 */
                border-left: none; /* 左侧没有边框 */
            }

            QPushButton:pressed {
                background-color: #5dade2; /* 鼠标按下时的背景颜色 */
                border: 2px solid dark;
                border-bottom: none; /* 下方没有边框 */
                border-left: none; /* 左侧没有边框 */}
                        """)
        elif tab_name in [self.tr("情景要素设定")]:
            button.setStyleSheet("""
                border: 2px solid dark; /* 边框颜色 */
                border-radius: 10px; /* 圆角边框 */
                background-color: transparent; /* 背景透明 */
                color: #333333; /* 文字颜色 */
                font-size: 18px; /* 文字大小 */
                font-weight: bold; /* 文字加粗 */
                    padding: 5px;
                border-top-right-radius: 0px; /* 右上角直角 */
                border-right: none; /* 右侧没有边框 */
                border-bottom: none; /* 下方没有边框 */
                border-bottom-left-radius: 0; /* 左下角直角 */
                border-bottom-right-radius: 0; /* 右下角直角 */
            }

            QPushButton:checked {
                background-color: #5dade2; /* 选中时的背景颜色 */
                color: white; /* 选中时的文字颜色 */
                border: 2px solid dark; /* 选中时边框颜色 */
                border-bottom: none; /* 下方没有边框 */
                border-right: none; /* 右侧没有边框 */
            }

            QPushButton:hover {
                background-color: #B0E2FF; /* 鼠标悬停时的背景颜色 */
                border: 2px solid dark; /* 鼠标悬停时边框颜色 */
                border-bottom: none; /* 下方没有边框 */
                border-right: none; /* 右侧没有边框 */
            }

            QPushButton:pressed {
                background-color: #5dade2; /* 鼠标按下时的背景颜色 */
                border: 2px solid dark;
                border-bottom: none; /* 下方没有边框 */
                border-right: none; /* 右侧没有边框 */}
            """)
        elif tab_name in [self.tr("推演条件设定")]:
            button.setStyleSheet("""
                border: 2px solid dark; /* 边框颜色 */
                border-radius: 10px; /* 圆角边框 */
                background-color: transparent; /* 背景透明 */
                color: #333333; /* 文字颜色 */
                font-size: 18px; /* 文字大小 */
                font-weight: bold; /* 文字加粗 */
                    padding: 5px;
                border-top-left-radius: 0px; /* 右上角直角 */
                border-left: none; /* 右侧没有边框 */
                border-bottom: none; /* 下方没有边框 */
                border-bottom-left-radius: 0; /* 左下角直角 */
                border-bottom-right-radius: 0; /* 右下角直角 */
            }

            QPushButton:checked {
                background-color: #5dade2; /* 选中时的背景颜色 */
                color: white; /* 选中时的文字颜色 */
                border: 2px solid dark; /* 选中时边框颜色 */
                border-bottom: none; /* 下方没有边框 */
                border-left: none; /* 左侧没有边框 */
            }

            QPushButton:hover {
                background-color: #B0E2FF; /* 鼠标悬停时的背景颜色 */
                border: 2px solid dark; /* 鼠标悬停时边框颜色 */
                border-bottom: none; /* 下方没有边框 */
                border-left: none; /* 左侧没有边框 */
            }

            QPushButton:pressed {
                background-color: #5dade2; /* 鼠标按下时的背景颜色 */
                border: 2px solid dark;
                border-bottom: none; /* 下方没有边框 */
                border-left: none; /* 左侧没有边框 */}
            """)

        self.tab_buttons_layout.addWidget(button)
        self.tabs.append(button)
        self.content_stack.addWidget(content_widget)

    def switch_tab(self, index):
        self.content_stack.setCurrentIndex(index - 1)
        self.tab_changed.emit(index - 1)

        for i, button in enumerate(self.tabs):
            button.setChecked(i + 1 == index)

        self.content_stack.setStyleSheet("""QStackedWidget {
    border: 2px solid dark; /* 边框颜色 */
    border-top: none; /* 上方没有边框 */
    border-bottom-left-radius: 10px; /* 左下角圆角 */
    border-bottom-right-radius: 10px; /* 右下角圆角 */
    background-color:#E8E8E8; /* 淡灰色 */
}
""")

    def show_placeholder(self, show=True, message=None):
        if message is None:
            message = self.tr("请选择或新建情景")
        if show:
            self.content_stack.setCurrentWidget(self.placeholder)
            self.placeholder_label.setText(self.tr(message))
            for button in self.tabs:
                button.setChecked(False)
            self.tab_buttons_widget.setVisible(False)
            self.content_stack.setStyleSheet("""QStackedWidget {
                border: 2px solid dark; /* 边框颜色 */
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom-left-radius: 10px; /* 左下角圆角 */
                border-bottom-right-radius: 10px; /* 右下角圆角 */
                background-color:#E8E8E8; /* 淡灰色 */
            }
            """)
        else:
            self.tab_buttons_widget.setVisible(True)
            self.reset_all_inputs()
            for button in self.tabs:
                self.lock_tabs(self.tabs.index(button) + 1)
            if self.tabs:
                self.unlock_tabs(1)
                self.switch_tab(1)

    def reset_all_inputs(self):
        self.ElementSettingTab.reset_inputs()
        self.ModelGenerationTab.reset_inputs()
        self.ModelTransformationTab.reset_inputs()
        self.ConditionSettingTab.reset_inputs()

    def lock_tabs(self, index):
        # 根据索引锁定标签
        for i, button in enumerate(self.tabs):
            if i + 1 == index:
                button.setDisabled(True)

    def unlock_tabs(self, index):
        # 根据索引解锁标签
        for i, button in enumerate(self.tabs):
            if i + 1 == index:
                button.setEnabled(True)

    def generate_model(self):
        self.unlock_tabs(2)
        self.switch_tab(2)
        scenario_id = self.ElementSettingTab.scenario_data['scenario_id']
        input_dir = os.path.join(os.path.dirname(__file__), f'../../data/sysml2/{scenario_id}')
        output_dir = os.path.join(os.path.dirname(__file__), f'../../data/sysml2/{scenario_id}/combined')

        config_path = os.path.join(os.path.dirname(__file__), '../../config.json')
        combine_sysml2(input_dir, output_dir, config_path)

        input_dir = output_dir
        output_dir = os.path.join(os.path.dirname(__file__), f'../../data/sysml2/{scenario_id}/result')
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 遍历输入目录中的所有 .txt 文件
        for file_name in os.listdir(input_dir):
            if file_name.endswith('.txt'):
                input_path = os.path.join(input_dir, file_name)
                process_file(input_path, output_dir)

        print("\n所有文件处理完成。")

        input_dir = output_dir
        output_dir = os.path.join(os.path.dirname(__file__), f'../../data/sysml2/{scenario_id}/owl')
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 获取所有JSON文件
        json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]

        # 创建ScenarioElement本体文件
        scenario_element_owl = os.path.join(output_dir, "ScenarioElement.owl")
        for input_file in json_files:
            input_path = os.path.join(input_dir, input_file)
            create_ontology(input_path, scenario_element_owl)

        # 加载ScenarioElement.owl文件并进行后续操作
        onto = get_ontology(scenario_element_owl).load()
        # 删除Action和Resource类及其子类
        with onto:
            if 'Action' in onto.classes():
                destroy_entity(onto.Action)
                print("已删除类 Action 及其子类")
            if 'Resource' in onto.classes():
                destroy_entity(onto.Resource)
                print("已删除类 Resource 及其子类")

        # 保存修改后的ScenarioElement.owl文件
        onto.save(file=scenario_element_owl, format="rdfxml")
        print(f"修改后的ScenarioElement.owl文件已保存到: {scenario_element_owl}")

        # 创建对应的Excel文件
        owl_excel_creator(scenario_element_owl, os.path.join(output_dir, "ScenarioElement_Prop.xlsx"))

        # 创建Scenario本体
        scenario_output_path = os.path.join(output_dir, "Scenario.owl")
        Scenario_owl_creator(scenario_output_path)
        owl_excel_creator(scenario_output_path, os.path.join(output_dir, "Scenario_Prop.xlsx"))

        # 创建Emergency本体
        emergency_output_path = os.path.join(output_dir, "Emergency.owl")
        Emergency_owl_creator(emergency_output_path)
        owl_excel_creator(emergency_output_path, os.path.join(output_dir, "Emergency_Prop.xlsx"))

        # 合并OWL文件
        input_owl_files = [
            scenario_element_owl,
            scenario_output_path,
            emergency_output_path
        ]
        combined_output_path = os.path.join(output_dir, "Merge.owl")
        combined_graph = rdflib.Graph()

            # 读取三个OWL文件并将它们的数据合并到一个图中
        combined_graph.parse(scenario_element_owl, format="xml")  # 假设OWL文件是RDF/XML格式
        combined_graph.parse(scenario_output_path, format="xml")
        combined_graph.parse(emergency_output_path, format="xml")

            # 将合并后的图写入输出文件
        combined_graph.serialize(destination=combined_output_path, format="xml")
        print(f"OWL files merged successfully into {combined_output_path}")

           # 创建owl图片
        input_owl_files = input_owl_files + [combined_output_path]
        convert_owl_to_svg(input_owl_files, output_dir)

        # 解析模型
        for input_owl in input_owl_files:
            parse_owl(input_owl)

        # 上传到数据库
        self.generate_model_save_to_database.emit()



    def generate_bayes(self):
        self.unlock_tabs(3)
        self.switch_tab(3)

    def set_inference_conditions(self):
        self.unlock_tabs(4)
        self.switch_tab(4)

if __name__ == '__main__':
    input_dir = os.path.join(os.path.dirname(__file__), '../../data/sysml2')
    output_dir = os.path.join(os.path.dirname(__file__), '../../data/sysml2/combined')

    config_path = os.path.join(os.path.dirname(__file__), '../../config.json')
    # 打印绝对路径，合并..后的格式
    print(os.path.abspath(input_dir))
    print(os.path.abspath(output_dir))
    print(os.path.abspath(config_path))