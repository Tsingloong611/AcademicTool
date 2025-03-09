# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:11 AM
# @FileName: tab_widget.py
# @Software: PyCharm
import json
import os
import shutil

import rdflib
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QSizePolicy, QProgressDialog, QApplication
)
from PySide6.QtCore import Qt, Signal
from owlready2 import get_ontology, destroy_entity

from test6 import convert_owl_to_svg
from utils.bn_svg_update import NetworkVisualizer, ScenarioResilience, bn_svg_update, update_with_evidence
from utils.combinesysml2 import combine_sysml2
from utils.createowlfromoriginjson import ScenarioOntologyGenerator
from utils.json2owl import create_ontology, owl_excel_creator, Scenario_owl_creator, Emergency_owl_creator
from utils.parserowl import parse_owl
from utils.plan import PlanDataCollector, convert_to_evidence, PlanData

from utils.sysml2json import process_file
from views.dialogs.custom_error_dialog import CustomErrorDialog
from views.dialogs.custom_information_dialog import CustomInformationDialog
from views.dialogs.custom_warning_dialog import CustomWarningDialog
from views.tabs.element_setting import ElementSettingTab
from views.tabs.model_generation import ModelGenerationTab
from views.tabs.model_transformation import ModelTransformationTab
from views.tabs.condition_setting import ConditionSettingTab


class CustomTabWidget(QWidget):
    tab_changed = Signal(int)
    generate_model_save_to_database = Signal()
    generate_bayes_save_to_database = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.analyzer = None
        self.init_ui()
        self.ElementSettingTab.generate_model_show.connect(self.generate_model)
        self.ModelGenerationTab.generate_request.connect(self.generate_bayes)
        self.ModelTransformationTab.set_inference_request.connect(self.set_inference_conditions)
        self.ModelTransformationTab.update_bayes_network.connect(self.generate_bayes)



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
        try:
            from PySide6.QtWidgets import QProgressDialog, QMessageBox
            from PySide6.QtCore import Qt, QTimer
            from PySide6.QtWidgets import QApplication
            import time

            # 创建进度条对话框
            progress = QProgressDialog(self.tr("准备开始..."), None, 0, 8, self)
            progress.setWindowTitle(self.tr("生成模型"))
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)  # 立即显示进度条
            progress.setMinimumWidth(300)
            progress.setCancelButton(None)  # 不显示取消按钮
            progress.setAutoClose(True)
            progress.show()

            def update_progress(step, text):
                progress.setValue(step)
                progress.setLabelText(text)
                QApplication.processEvents()  # 强制刷新界面
                time.sleep(0.1)  # 添加小延迟让进度条可见

            # 第1步：初始化
            update_progress(0, self.tr("正在初始化..."))


            scenario_id = self.ElementSettingTab.scenario_data['scenario_id']
            input_dir = os.path.join(os.path.dirname(__file__), f'../../data/sysml2/{scenario_id}')
            output_dir = os.path.join(os.path.dirname(__file__), f'../../data/sysml2/{scenario_id}/combined')

            # 第2步：合并SysML2文件
            update_progress(1, self.tr("正在合并SysML2文件..."))

            try:
                config_path = os.path.join(os.path.dirname(__file__), '../../config.json')
                combine_sysml2(input_dir, output_dir, config_path)
            except Exception as e:
                raise Exception(self.tr('合并SysML2文件失败: {e}').format(e=str(e)))

            # 第3步：处理文件
            update_progress(2, self.tr("正在处理文件..."))

            input_dir = output_dir
            output_dir = os.path.join(os.path.dirname(__file__), f'../../data/sysml2/{scenario_id}/result')
            os.makedirs(output_dir, exist_ok=True)

            try:
                for file_name in os.listdir(input_dir):
                    if file_name.endswith('.txt'):
                        input_path = os.path.join(input_dir, file_name)
                        process_file(input_path, output_dir)
            except Exception as e:
                raise Exception(self.tr('处理文件失败: {e}'.format(e=str(e))))

            # 第4步：生成ScenarioElement本体
            update_progress(3, self.tr("正在生成ScenarioElement本体..."))

            try:
                input_dir = output_dir
                output_dir = os.path.join(os.path.dirname(__file__), f'../../data/sysml2/{scenario_id}/owl')
                os.makedirs(output_dir, exist_ok=True)

                for f in os.listdir(output_dir):
                    if f.endswith('.owl'):
                        os.remove(os.path.join(output_dir, f))

                json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
                scenario_element_owl = os.path.join(output_dir, "ScenarioElement.owl")

                # for input_file in json_files:
                #     input_path = os.path.join(input_dir, input_file)
                #     create_ontology(input_path, scenario_element_owl)
                generator = ScenarioOntologyGenerator()
                element_list = list(self.ElementSettingTab.element_data.items())
                converted_data = [item[1] for item in element_list]  # 直接提取值部分
                json_data = converted_data
                # print(f"23123{json_data}")
                generator.generate(converted_data, scenario_element_owl)

                onto = get_ontology(scenario_element_owl).load()
                with onto:
                    if 'Action' in onto.classes():
                        destroy_entity(onto.Action)
                    if 'Resource' in onto.classes():
                        destroy_entity(onto.Resource)
                onto.save(file=scenario_element_owl, format="rdfxml")

                owl_excel_creator(scenario_element_owl, os.path.join(output_dir, "ScenarioElement_Prop.xlsx"))
            except Exception as e:
                raise Exception(self.tr('生成ScenarioElement本体失败: {e}').format(e=str(e)))

            # 第5步：创建其他本体文件
            update_progress(4, self.tr("正在创建其他本体文件..."))

            try:
                scenario_output_path = os.path.join(output_dir, "Scenario.owl")
                Scenario_owl_creator(scenario_output_path)
                owl_excel_creator(scenario_output_path, os.path.join(output_dir, "Scenario_Prop.xlsx"))

                emergency_output_path = os.path.join(output_dir, "Emergency.owl")
                Emergency_owl_creator(emergency_output_path)
                owl_excel_creator(emergency_output_path, os.path.join(output_dir, "Emergency_Prop.xlsx"))
            except Exception as e:
                raise Exception(self.tr('创建Scenario和Emergency本体失败: {e}').format(e=str(e)))

            # 第6步：合并OWL文件
            update_progress(5, self.tr("正在合并OWL文件..."))

            try:
                input_owl_files = [
                    scenario_element_owl,
                    scenario_output_path,
                    emergency_output_path
                ]
                combined_output_path = os.path.join(output_dir, "Merge.owl")
                combined_graph = rdflib.Graph()

                for owl_file in input_owl_files:
                    combined_graph.parse(owl_file, format="xml")

                combined_graph.serialize(destination=combined_output_path, format="xml")
            except Exception as e:
                raise Exception(self.tr('合并OWL文件失败: {e}').format(e=str(e)))

            # 第7步：创建OWL图片和解析模型
            update_progress(6, self.tr("正在创建OWL图片和解析模型..."))

            try:
                input_owl_files = input_owl_files + [combined_output_path]
                convert_owl_to_svg(input_owl_files, output_dir)

                for input_owl in input_owl_files:
                    element_list = list(self.ElementSettingTab.element_data.items())
                    converted_data = [item[1] for item in element_list]  # 直接提取值部分
                    json_data = converted_data
                    parse_owl(input_owl, json_data)
            except Exception as e:
                raise Exception(self.tr('创建OWL图片或解析模型失败: {e}').format(e=str(e)))

            # 第8步：保存到数据库
            update_progress(7, self.tr("正在保存到数据库..."))

            try:
                self.generate_model_save_to_database.emit()

            except Exception as e:
                raise Exception(self.tr('保存到数据库失败: {e}').format(e=str(e)))

            # 完成
            update_progress(8, self.tr("完成"))
            time.sleep(0.5)  # 让用户看到100%的进度
            progress.close()
            self.unlock_tabs(2)
            self.switch_tab(2)
            CustomInformationDialog(" ", self.tr("已成功生成情景级孪生模型。"), parent=self).exec()

        except Exception as e:
            if 'progress' in locals():
                progress.close()
            QMessageBox.critical(None, "错误", self.tr('模型生成失败:{e}').format(e=str(e)))
            print(f"Error: {str(e)}")

    def generate_bayes(self):
        try:
            import time

            # 创建进度条对话框
            progress = QProgressDialog(self.tr("准备开始..."), None, 0, 8, self)
            progress.setWindowTitle(self.tr("生成贝叶斯网络"))
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setMinimumWidth(300)
            progress.setCancelButton(None)
            progress.setAutoClose(True)
            progress.show()

            def update_progress(step, text):
                progress.setValue(step)
                progress.setLabelText(text)
                QApplication.processEvents()
                time.sleep(0.1)

            # 步骤1：初始化
            update_progress(0, self.tr("正在初始化..."))

            scenario_id = self.ElementSettingTab.scenario_data['scenario_id']

            # 步骤2：加载OWL文件
            update_progress(1, self.tr("正在加载OWL文件..."))
            try:
                input_owl = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                         f'../../data/sysml2/{scenario_id}/owl/Scenario.owl'))
                analyzer = ScenarioResilience(input_owl)
            except Exception as e:
                raise Exception(self.tr('加载OWL文件失败: {e}').format(e=str(e)))

            # 步骤3：提取数据属性
            update_progress(2, self.tr("正在提取数据属性..."))
            try:
                analyzer.extract_data_properties()
            except Exception as e:
                raise Exception(self.tr('提取数据属性失败: {e}').format(e=str(e)))

            # 步骤4：创建贝叶斯网络结构
            update_progress(3, self.tr("正在创建贝叶斯网络结构..."))
            try:
                analyzer.create_bayesian_network()
            except Exception as e:
                raise Exception(self.tr('创建贝叶斯网络结构失败: {e}').format(e=str(e)))

            # 步骤5：设置先验概率
            update_progress(4, self.tr("正在设置先验概率..."))
            # try:
            #     # 当前脚本所在的目录
            #     current_dir = os.path.dirname(__file__)
            #
            #     # 源文件所在目录
            #     source_dir = os.path.abspath(os.path.join(current_dir, '../../data/required_information'))
            #
            #     # 指定的目标文件夹
            #     destination_dir = os.path.abspath(os.path.join(current_dir, f'../../data/bn/{scenario_id}/required_information'))
            #     self.ModelTransformationTab.info_dir = destination_dir
            #
            #     # 如果目标文件夹不存在，则创建它
            #     if not os.path.exists(destination_dir):
            #         os.makedirs(destination_dir)
            #
            #
            #     # 文件列表
            #     files = [
            #         'prior prob test.xlsx',
            #         'expertInfo.xlsx',
            #         'expert estimation test.xlsx'
            #     ]
            #
            #     # 循环复制每个文件
            #     # 如果已经存在，跳过复制
            #     for file_name in files:
            #
            #         src_path = os.path.join(source_dir, file_name)
            #         dst_path = os.path.join(destination_dir, file_name)
            #
            #         # 复制文件，保留元数据（使用 copy2）；
            #         # 如果不需要保留元数据，可以使用 shutil.copy
            #
            #         # 如果已经存在，跳过复制
            #         if os.path.exists(dst_path):
            #             continue
            #         shutil.copy2(src_path, dst_path)
            #
            #     print("文件复制成功！")
            #
            # except Exception as e:
            #     raise Exception(f"复制文件失败: {str(e)}")
            try:
                prior_prob_test_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                                    f'../../data/required_information/root_prior_data.xlsx'))
                expert_info_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                                f'../../data/required_information/expert_info_data.xlsx'))
                expert_estimation_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                                      f'../../data/required_information/expert_estimation_data.xlsx'))

                analyzer.set_prior_probabilities(prior_prob_test_path)
                self.ModelTransformationTab.info_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                                f'../../data/required_information'))
            except Exception as e:
                raise Exception(self.tr('设置先验概率失败: {e}').format(e=str(e)))

            # 步骤6：处理专家评估
            update_progress(5, self.tr("正在处理专家评估..."))
            try:
                expert_df = analyzer.process_expert_evaluation(
                    expert_info_path=expert_info_path,
                    expert_estimation_path=expert_estimation_path
                )
                analyzer.set_conditional_probabilities(expert_df)
            except Exception as e:
                raise Exception(self.tr('处理专家评估失败: {e}').format(e=str(e)))

            # 步骤7：执行推理和保存网络
            update_progress(6, self.tr("正在执行推理和保存网络..."))
            try:
                analyzer.make_inference()

                output_dir = os.path.join(os.path.dirname(__file__), f'../../data/bn/{scenario_id}')
                structure_path, params_path = analyzer.save_network(output_dir)
            except Exception as e:
                raise Exception(self.tr('执行推理或保存网络失败: {e}').format(e=str(e)))

            # 步骤8：可视化网络
            update_progress(7, self.tr("正在可视化网络..."))
            try:
                visualizer = NetworkVisualizer()
                ie = visualizer.visualize_network(
                    bn=analyzer.bn,
                    output_dir=output_dir,
                    state_mapping=analyzer.state_mapping
                )

                node_data_path = os.path.join(output_dir, "node_data.json")

                # 创建会话和收集器实例
                collector = PlanDataCollector(self.ElementSettingTab.session, scenario_id=scenario_id)

                # 收集数据
                plan_data = collector.collect_all_data(plan_name=None)

                # 转换为贝叶斯网络证据
                evidence = convert_to_evidence(plan_data)
                # 查看有没有设置resource
                related_usage = collector.get_related_resource()
                print(f"324234243{related_usage}")
                if not related_usage:
                    evidence.pop('responseDuration', None)
                    evidence.pop('disposalDuration', None)
                    # evidence.pop('AidResource', None)
                    # evidence.pop('TowResource', None)
                    # evidence.pop('FirefightingResource', None)
                    # evidence.pop('RescueResource', None)
                    evidence['AidResource']= 0
                    evidence['TowResource'] = 0
                    evidence['FirefightingResource'] = 0
                    evidence['RescueResource'] = 0
                update_with_evidence(analyzer, evidence,output_dir)

                self.ModelTransformationTab.set_node_data(json.load(open(node_data_path, 'r')))
                self.ModelTransformationTab.set_bayesian_network_image(
                    os.path.join(output_dir, "combined_visualization.svg"))
                self.generate_bayes_save_to_database.emit()
            except Exception as e:
                raise Exception(self.tr('可视化网络失败: {e}').format(e=str(e)))

            # 完成
            update_progress(8, self.tr("完成"))
            time.sleep(0.5)  # 让用户看到100%的进度
            progress.close()
            self.unlock_tabs(3)
            self.switch_tab(3)
            self.analyzer = analyzer
            CustomInformationDialog(" ", self.tr("已成功生成推演模型。"), parent=self).exec()

        except Exception as e:
            if 'progress' in locals():
                progress.close()
            CustomErrorDialog(self.tr("错误"), self.tr('生成推演模型失败:{e}').format(e=str(e)), parent=self).exec()
            print(f"Error: {str(e)}")


    def set_inference_conditions(self):
        self.ConditionSettingTab.session = self.ElementSettingTab.session
        self.ConditionSettingTab.scenario_id = self.ElementSettingTab.scenario_data['scenario_id']
        self.ConditionSettingTab.analyzer = self.analyzer
        self.ConditionSettingTab.new_plan_generator = PlanData(self.ConditionSettingTab.session,self.ConditionSettingTab.scenario_id,self.ConditionSettingTab.neg_id_gen)
        self.ConditionSettingTab.change_path =os.path.abspath(os.path.join(os.path.dirname(__file__), f"../../data/bn/{self.ElementSettingTab.scenario_data['scenario_id']}/posterior_probabilities.json"))
        self.ConditionSettingTab.load_saved_plans()
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