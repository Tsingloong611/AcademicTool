# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:08 AM
# @FileName: scenario_controller.py
# @Software: PyCharm

from PySide6.QtCore import QObject, Slot, Qt
from PySide6.QtWidgets import QInputDialog, QMessageBox, QDialog
from sqlalchemy.exc import SQLAlchemyError
from models.scenario import Scenario
from database.db_config import SessionLocal

from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QInputDialog, QMessageBox
from sqlalchemy.exc import SQLAlchemyError
from models.scenario import Scenario
from database.db_config import SessionLocal
from views.scenario_manager import ScenarioDialog


class ScenarioController(QObject):
    def __init__(self, scenario_manager, status_bar, tab_widget):
        super().__init__()
        self.scenario_manager = scenario_manager
        self.status_bar = status_bar
        self.tab_widget = tab_widget
        self.db = SessionLocal()
        self.current_scenario = None

        # 连接信号
        self.scenario_manager.scenario_selected.connect(self.handle_scenario_selected)
        self.scenario_manager.add_requested.connect(self.handle_add_requested)
        self.scenario_manager.edit_requested.connect(self.handle_edit_requested)
        self.scenario_manager.delete_requested.connect(self.handle_delete_requested)

        # 加载初始数据
        self.load_scenarios()

    def load_scenarios(self):
        scenarios = self.get_all_scenarios()
        self.scenario_manager.populate_scenarios(scenarios)
        # 初始时保持标签页锁定和占位页面显示
        if(scenarios):
            self.tab_widget.show_placeholder(True)
        else:
            self.tab_widget.show_placeholder(False)

    def get_all_scenarios(self):
        try:
            scenarios = self.db.query(Scenario).all()
            return scenarios
        except SQLAlchemyError as e:
            print(f"Error fetching scenarios: {e}")
            QMessageBox.critical(None, "错误", f"获取情景列表失败: {e}")
            return []

    @Slot(int, str, str)
    def handle_scenario_selected(self, scenario_id, scenario_name, scenario_description):
        scenario = self.get_scenario_by_id(scenario_id)
        if scenario:
            self.current_scenario = scenario
            # 更新状态栏中的所有信息项
            self.status_bar.user_label.setText("当前用户: 用户名")  # 示例，实际应从用户管理模块获取
            self.status_bar.database_label.setText("当前数据库: 数据库名称")  # 示例，实际应从数据库管理模块获取
            self.status_bar.current_scenario_label.setText(f"当前情景: {scenario.name}")
            self.status_bar.owl_status_label.setText("OWL 文件状态: 正常")  # 示例
            self.status_bar.bayes_status_label.setText("贝叶斯网络状态: 正常")  # 示例
            self.status_bar.scenario_update_time_label.setText("最后更新时间: 2024-12-03 10:00:00")  # 示例

            # 解锁标签页并显示功能区
            self.tab_widget.show_tabs()
            # TODO: 更新右侧标签页内容
        else:
            # 如果情景不存在，重置状态栏和标签页
            self.status_bar.user_label.setText("当前用户: 无")
            self.status_bar.database_label.setText("当前数据库: 无")
            self.status_bar.current_scenario_label.setText("当前情景: 无")
            self.status_bar.owl_status_label.setText("OWL 文件状态: 无")
            self.status_bar.bayes_status_label.setText("贝叶斯网络状态: 无")
            self.status_bar.scenario_update_time_label.setText("最后更新时间: 无")
            self.tab_widget.show_placeholder()

    @Slot()
    def handle_add_requested(self):
        dialog = ScenarioDialog(self.scenario_manager)  # 将父窗口更改为 scenario_manager
        if dialog.exec() == QDialog.Accepted:
            name, description = dialog.get_data()
            if not name:
                QMessageBox.warning(None, "添加失败", "情景名称不能为空。")
                return
            new_scenario = self.add_scenario(name, description)
            if new_scenario:
                self.load_scenarios()

    @Slot()
    def handle_edit_requested(self):
        current_item = self.scenario_manager.list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(None, "警告", "请选择要修改的情景。")
            return
        scenario_id = current_item.data(Qt.UserRole)
        scenario = self.get_scenario_by_id(scenario_id)
        if not scenario:
            QMessageBox.warning(None, "警告", "未找到选中的情景。")
            return
        dialog = ScenarioDialog(self.scenario_manager, scenario=scenario)  # 将父窗口更改为 scenario_manager
        if dialog.exec() == QDialog.Accepted:
            name, description = dialog.get_data()
            if not name:
                QMessageBox.warning(None, "修改失败", "情景名称不能为空。")
                return
            updated = self.update_scenario(scenario_id, name, description)
            if updated:
                self.load_scenarios()
                if self.current_scenario and self.current_scenario.id == scenario_id:
                    # 更新状态栏中的所有信息项
                    self.status_bar.current_scenario_label.setText(f"当前情景: {updated.name}")
                    self.status_bar.owl_status_label.setText("OWL 文件状态: 正常")
                    self.status_bar.bayes_status_label.setText("贝叶斯网络状态: 正常")
                    self.status_bar.last_update_label.setText("最后更新时间: 2024-12-03 10:00:00")

    @Slot()
    def handle_delete_requested(self):
        current_item = self.scenario_manager.list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(None, "警告", "请选择要删除的情景。")
            return
        scenario_id = current_item.data(Qt.UserRole)
        scenario = self.get_scenario_by_id(scenario_id)
        if not scenario:
            QMessageBox.warning(None, "警告", "未找到选中的情景。")
            return
        reply = QMessageBox.question(
            None, '删除情景',
            f'是否删除情景 "{scenario.name}"？',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success = self.delete_scenario(scenario_id)
            if success:
                self.load_scenarios()
                if self.current_scenario and self.current_scenario.id == scenario_id:
                    self.current_scenario = None
                    # 更新状态栏中的所有信息项
                    self.status_bar.user_label.setText("当前用户: 无")
                    self.status_bar.database_label.setText("当前数据库: 无")
                    self.status_bar.current_scenario_label.setText("当前情景: 无")
                    self.status_bar.owl_status_label.setText("OWL 文件状态: 无")
                    self.status_bar.bayes_status_label.setText("贝叶斯网络状态: 无")
                    self.status_bar.last_update_label.setText("最后更新时间: 无")
                    self.tab_widget.show_placeholder()

    def add_scenario(self, name, description=''):
        try:
            new_scenario = Scenario(name=name, description=description)
            self.db.add(new_scenario)
            self.db.commit()
            self.db.refresh(new_scenario)
            return new_scenario
        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"Error adding scenario: {e}")
            QMessageBox.critical(None, "错误", f"新增情景失败: {e}")
            return None

    def update_scenario(self, scenario_id, name=None, description=None, status=None):
        try:
            scenario = self.db.query(Scenario).filter(Scenario.id == scenario_id).first()
            if not scenario:
                return None
            if name:
                scenario.name = name
            if description:
                scenario.description = description
            if status:
                scenario.status = status
            self.db.commit()
            self.db.refresh(scenario)
            return scenario
        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"Error updating scenario: {e}")
            QMessageBox.critical(None, "错误", f"修改情景失败: {e}")
            return None

    def delete_scenario(self, scenario_id):
        try:
            scenario = self.db.query(Scenario).filter(Scenario.id == scenario_id).first()
            if not scenario:
                return False
            self.db.delete(scenario)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"Error deleting scenario: {e}")
            QMessageBox.critical(None, "错误", f"删除情景失败: {e}")
            return False

    def get_scenario_by_id(self, scenario_id):
        try:
            scenario = self.db.query(Scenario).filter(Scenario.id == scenario_id).first()
            return scenario
        except SQLAlchemyError as e:
            print(f"Error fetching scenario by id: {e}")
            return None

    def __del__(self):
        self.db.close()