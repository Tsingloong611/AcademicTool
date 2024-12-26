# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:08 AM
# @FileName: scenario_controller.py
# @Software: PyCharm
import json

from PySide6.QtCore import QObject, Slot, Qt
from PySide6.QtWidgets import QInputDialog, QMessageBox, QDialog
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.sync import update
from sqlalchemy.sql.base import elements

# 假设您已经在 models/scenario.py 中定义了 Scenario 类，
# 其中字段为 scenario_id, scenario_name, scenario_description, ...
from models.models import Scenario, ElementBase, Element, Attribute, AttributeBase, BehaviorObject, BehaviorBaseObject, \
    Behavior, BehaviorBase, AttributeAssociation, AttributeBaseAssociation

from views.dialogs.custom_error_dialog import CustomErrorDialog
from views.dialogs.custom_information_dialog import CustomInformationDialog
from views.dialogs.custom_warning_dialog import CustomWarningDialog
from views.login_dialog import LoginDialog
from views.scenario_manager import ScenarioDialog


class ScenarioController(QObject):
    def __init__(self, scenario_manager, status_bar, tab_widget, db_manager):
        super().__init__()
        self.scenario_manager = scenario_manager
        self.status_bar = status_bar
        self.tab_widget = tab_widget
        self.db_manager = db_manager  # 使用传入的 DatabaseManager 实例
        self.current_scenario = None
        self.session = self.db_manager.get_session()

        # 连接信号
        self.scenario_manager.scenario_selected.connect(self.handle_scenario_selected)
        self.scenario_manager.add_requested.connect(self.handle_add_requested)
        self.scenario_manager.edit_requested.connect(self.handle_edit_requested)
        self.scenario_manager.delete_requested.connect(self.handle_delete_requested)

        # 加载初始数据
        self.load_scenarios()

        # 从数据库管理器获取连接信息并更新状态栏
        connection_info = self.db_manager.get_connection_info()
        username = connection_info.get('username', '未知用户')
        database = connection_info.get('database', '未知数据库')
        self.status_bar.update_user_info(username, database)

    def load_scenarios(self):
        """加载并在界面上显示所有情景"""
        scenarios = self.get_all_scenarios()
        self.scenario_manager.populate_scenarios(scenarios)
        # 初始时保持标签页锁定和占位页面显示
        if scenarios:
            self.tab_widget.show_placeholder(True)
        else:
            self.tab_widget.show_placeholder(True, "请添加情景")

    def get_all_scenarios(self):
        try:
            # 这里注意：Scenario 主键改为 scenario_id
            scenarios = self.session.query(Scenario).all()
            return scenarios
        except SQLAlchemyError as e:
            print(f"Error fetching scenarios: {e}")
            QMessageBox.critical(None, "错误", f"获取情景列表失败: {e}")
            return []

    @Slot(int, str, str)
    def handle_scenario_selected(self, scenario_id, scenario_name, scenario_description):
        """当用户在列表中选择了一个情景时触发"""
        scenario = self.get_scenario_by_id(scenario_id)
        if scenario:
            self.current_scenario = scenario
            # 从数据库管理器获取连接信息
            connection_info = self.db_manager.get_connection_info()
            username = connection_info.get('username', '未知用户')
            database = connection_info.get('database', '未知数据库')

            # 如果 Scenario 中还有 owl_status, bayes_status, updated_at 之类字段，
            # 也要相应做修改与获取；以下仅作示例
            owl_state = getattr(scenario, 'owl_status', "未知")
            bayes_state = getattr(scenario, 'bayes_status', "未知")
            update_time = getattr(scenario, 'scenario_update_time', None)
            if update_time is not None:
                update_time = update_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                update_time = "无"

            self.status_bar.update_status(
                username=username,
                database=database,
                scenario_name=scenario.scenario_name,  # 新字段名
                owl_status=owl_state,
                bayes_status=bayes_state,
                scenario_description=scenario.scenario_description,  # 新字段名
                update_time=update_time
            )

            # 解锁标签页并显示功能区
            self.tab_widget.show_placeholder(False)

            self.static_data = self.build_static_data(scenario_id)


            self.tab_widget.ElementSettingTab.static_data = self.static_data
            self.tab_widget.ElementSettingTab.category_data = {category: json.loads(json.dumps(data)) for category, data in self.static_data.items()}
            self.tab_widget.ElementSettingTab.category_to_attributes = {
            category: list(data.get("attributes", {}).keys())
            for category, data in self.static_data.items()
        }
            self.tab_widget.ElementSettingTab.attribute_editors= {category: {} for category in self.tab_widget.ElementSettingTab.categories}
        else:
            self.reset_status_bar()


    def build_static_data(self, scenario_id):
        """
        根据题中提到的三条查询逻辑，构造 static_data 字典
        """
        # 第 1 步：获取 “父节点不为空 且 父节点不等于 关联实体” 的所有 Element
        # 相当于：
        # SELECT * FROM element
        #  WHERE scenario_id=20
        #    AND element_parent_id IS NOT NULL
        #    AND element_parent_id <> (SELECT element_id FROM element WHERE scenario_id=20 AND element_name='关联实体')

        # 先拿 '关联实体' 的 element_id
        ent = self.session.query(Element.element_id).filter(
            Element.scenario_id == scenario_id,
            Element.element_name == '关联实体'
        ).scalar()  # 返回单个值 or None

        # 再拿符合条件的 Element
        elements = self.session.query(Element).filter(
            Element.scenario_id == scenario_id,
            Element.element_parent_id.isnot(None),
            Element.element_parent_id != ent
        ).all()

        # 用于构造 static_data
        static_data = {}

        # 第 2 & 第 3 步：对每个要素，分别查询 Attribute、Behavior
        for elem in elements:
            elem_name = elem.element_name

            # 查属性: SELECT * FROM attribute WHERE element_id = elem.element_id
            attrs = self.session.query(Attribute).filter(Attribute.element_id == elem.element_id).all()

            # 查行为: SELECT * FROM behavior WHERE element_id = elem.element_id
            behs = self.session.query(Behavior).filter(Behavior.element_id == elem.element_id).all()

            # 组装属性字典
            attr_dict = {}
            for a in attrs:
                attr_dict[a.attribute_name] = a.attribute_value  # or whatever fields

            # 组装行为列表
            beh_list = []
            for b in behs:
                # 根据你实际表字段来赋值, 这里举例:
                beh_list.append({
                    "name": b.behavior_name,
                    # 如果你还有 subject/object 字段，就加上:
                    # "subject": b.behavior_subject,
                    # "object": b.behavior_object
                })

            static_data[elem_name] = {
                "attributes": attr_dict,
                "behavior": beh_list
            }

        print(f"static_data:{static_data}")

        return static_data

    def reset_status_bar(self):
        """重置状态栏的内容"""
        connection_info = self.db_manager.get_connection_info()
        username = connection_info.get('username', '未知用户')
        database = connection_info.get('database', '未知数据库')
        self.status_bar.update_status(
            username,
            database,
            scenario_name="等待情景加载",
            owl_status="等待情景加载",
            bayes_status="等待情景加载",
            scenario_description="等待情景加载",
            update_time = "等待情景加载"
        )
        self.tab_widget.show_placeholder()

    @Slot()
    def handle_add_requested(self):
        """用户点击“添加情景”按钮时执行"""
        dialog = ScenarioDialog(self.scenario_manager)
        if dialog.exec() == QDialog.Accepted:
            name, description = dialog.get_data()
            if not name:
                CustomWarningDialog("添加失败", "情景名称不能为空。").exec()
                return
            new_scenario = self.add_scenario(name, description)
            if new_scenario:
                self.load_scenarios()

    @Slot()
    def handle_edit_requested(self):
        """用户点击“编辑情景”按钮时执行"""
        current_item = self.scenario_manager.list_widget.currentItem()
        if not current_item:
            CustomWarningDialog("警告", "请选择要修改的情景。").exec()
            return
        scenario_id = current_item.data(Qt.UserRole)
        scenario = self.get_scenario_by_id(scenario_id)
        if not scenario:
            CustomWarningDialog("警告", "未找到选中的情景。").exec()
            return

        dialog = ScenarioDialog(self.scenario_manager, scenario=scenario)
        if dialog.exec() == QDialog.Accepted:
            name, description = dialog.get_data()
            if not name:
                CustomWarningDialog("修改失败", "情景名称不能为空。").exec()
                return
            updated = self.update_scenario(scenario_id, name, description)
            if updated:
                self.load_scenarios()
                if self.current_scenario and self.current_scenario.scenario_id == scenario_id:
                    # 也可以更新状态栏 (如果有需要)
                    pass

    @Slot()
    def handle_delete_requested(self):
        """用户点击“删除情景”按钮时执行"""
        current_item = self.scenario_manager.list_widget.currentItem()
        if not current_item:
            CustomWarningDialog("警告", "请选择要删除的情景。").exec()
            return
        scenario_id = current_item.data(Qt.UserRole)
        scenario = self.get_scenario_by_id(scenario_id)
        if not scenario:
            CustomWarningDialog("警告", "未找到选中的情景。").exec()
            return

        success = self.delete_scenario(scenario_id)
        if success:
            self.load_scenarios()
            if self.current_scenario and self.current_scenario.scenario_id == scenario_id:
                self.current_scenario = None
                self.reset_status_bar()

    def add_scenario(self, scenario_name, scenario_description=''):
        """在数据库中插入新情景"""
        try:
            # 创建新的 Scenario 实例
            new_scenario = Scenario(
                scenario_name=scenario_name,
                scenario_description=scenario_description,
                emergency_id=1  # 根据实际需求调整
            )
            self.session.add(new_scenario)
            self.session.commit()  # 提交以获取 new_scenario 的 ID

            self.replicate_all_for_scenario(new_scenario.scenario_id)


            # 提交所有新的 Element 实例
            self.session.commit()
            self.session.refresh(new_scenario)
            return new_scenario
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error adding scenario: {e}")
            CustomErrorDialog("错误", f"新增情景失败: {e}").exec()
            return None

    def replicate_all_for_scenario(self, scenario_id):
        """
        将 element_base / attribute_base / attribute_base_association / behavior_base / behavior_base_object
        等数据复制到 element / attribute / attribute_association / behavior / behavior_object
        以在指定 scenario 中创建完整要素、属性及行为模型。
        """

        ########################
        # 1. 复制 element_base -> element
        ########################
        element_base_list = self.session.query(ElementBase).all()
        element_base_to_element = {}  # 用于记录映射：element_base_id -> element_id

        # 假设 element_base_list 中，父节点的记录在子节点之前
        for eb in element_base_list:
            # 根据 eb.element_base_parent_id 找到新父节点
            parent_id = None
            if eb.element_base_parent_id is not None:
                # 到映射字典查父节点新ID
                # 注意：如果父节点还没处理过，就会拿不到，须保证顺序或做二次处理
                parent_id = element_base_to_element.get(eb.element_base_parent_id)

            new_elem = Element(
                element_name=eb.element_base_name,
                element_type_id=eb.element_base_type_id,
                scenario_id=scenario_id,
                element_parent_id=parent_id  # 这里赋给新 Element 的父节点
            )
            self.session.add(new_elem)
            self.session.commit()  # 提交后获得 new_elem.element_id

            # 记录映射关系
            element_base_to_element[eb.element_base_id] = new_elem.element_id

        self.session.commit()

        ########################
        # 2. 复制 attribute_base -> attribute
        ########################
        # 对每个 element_base, 查找其下所有 attribute_base, 复制到 attribute
        attribute_base_to_attribute = {}

        for eb in element_base_list:
            # 找到对应的 element_id
            if eb.element_base_id not in element_base_to_element:
                continue
            new_element_id = element_base_to_element[eb.element_base_id]

            # 查找该 base 下的所有 attribute_base
            attr_bases = self.session.query(AttributeBase).filter_by(element_base_id=eb.element_base_id).all()
            for ab in attr_bases:
                new_attr = Attribute(
                    attribute_name=ab.attribute_base_name,
                    attribute_type_id=ab.attribute_base_type_id,
                    is_required=ab.is_required,
                    is_multi_valued=ab.is_multi_valued,
                    enum_value_id=ab.enum_value_id,
                    attribute_value=ab.attribute_base_value or "",
                    element_id=new_element_id
                )
                self.session.add(new_attr)
                self.session.commit()
                # 记录映射
                attribute_base_to_attribute[ab.attribute_base_id] = new_attr.attribute_id

        self.session.commit()

        ########################
        # 3. 复制 attribute_base_association -> attribute_association
        ########################
        # attribute_base_association 是 (attribute_base_id, associated_element_base_id) 复合主键
        # 复制成 (attribute_id, associated_element_id)
        assoc_bases = self.session.query(AttributeBaseAssociation).all()
        for assoc in assoc_bases:
            # 1) 找到对应的新 attribute_id
            attr_base_id = assoc.attribute_base_id
            if attr_base_id not in attribute_base_to_attribute:
                continue
            new_attr_id = attribute_base_to_attribute[attr_base_id]

            # 2) 找到对应的新 element_id
            assoc_elem_base_id = assoc.associated_element_base_id
            if assoc_elem_base_id not in element_base_to_element:
                continue
            new_assoc_elem_id = element_base_to_element[assoc_elem_base_id]

            # 插入到 attribute_association
            new_assoc = AttributeAssociation(
                attribute_id=new_attr_id,
                associated_element_id=new_assoc_elem_id
            )
            self.session.add(new_assoc)
            # 不需要立即commit，最后统一提交

        self.session.commit()

        ########################
        # 4. 复制 behavior_base -> behavior
        ########################
        # behavior_base: (behavior_base_id, behavior_base_name, object_type_id, is_multi_valued, element_base_id ...)
        behavior_base_list = self.session.query(BehaviorBase).all()
        behavior_base_to_behavior = {}

        for bb in behavior_base_list:
            # 找到对应的 element
            if bb.element_base_id not in element_base_to_element:
                continue
            new_elem_id = element_base_to_element[bb.element_base_id]

            new_behavior = Behavior(
                behavior_name=bb.behavior_base_name,
                object_type_id=bb.object_type_id,
                is_multi_valued=bb.is_multi_valued,
                element_id=new_elem_id,
                # 如果有 is_required 字段或者其他字段，也可在这里赋值
                is_required = bb.is_required,
            )
            self.session.add(new_behavior)
            self.session.commit()

            behavior_base_to_behavior[bb.behavior_base_id] = new_behavior.behavior_id

        self.session.commit()

        ########################
        # 5. 复制 behavior_base_object -> behavior_object
        ########################
        # behavior_base_object: (behavior_base_id, object_element_base_id) 复合主键
        # => behavior_object: (behavior_id, object_element_id)
        bbo_list = self.session.query(BehaviorBaseObject).all()
        for bbo in bbo_list:
            # 找到 behavior_id
            if bbo.behavior_base_id not in behavior_base_to_behavior:
                continue
            new_behavior_id = behavior_base_to_behavior[bbo.behavior_base_id]

            # 找到新 object_element_id
            if bbo.object_element_base_id not in element_base_to_element:
                continue
            new_object_elem_id = element_base_to_element[bbo.object_element_base_id]

            # 插入
            new_bobj = BehaviorObject(
                behavior_id=new_behavior_id,
                object_element_id=new_object_elem_id
            )
            self.session.add(new_bobj)
            # 不需要马上 commit

        self.session.commit()

        print("=== 复制完成：element/attribute/behavior及中间关联表都已生成 ===")

    def update_scenario(self, scenario_id, scenario_name=None, scenario_description=None):
        """更新情景信息"""
        try:
            scenario = self.session.query(Scenario).filter(Scenario.scenario_id == scenario_id).first()
            if not scenario:
                return None
            if scenario_name:
                scenario.scenario_name = scenario_name
            if scenario_description:
                scenario.scenario_description = scenario_description
            self.session.commit()
            self.session.refresh(scenario)
            return scenario
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error updating scenario: {e}")
            CustomErrorDialog("错误", f"修改情景失败: {e}").exec()
            return None

    def delete_scenario(self, scenario_id):
        """删除指定情景"""
        try:
            scenario = self.session.query(Scenario).filter(Scenario.scenario_id == scenario_id).first()
            if not scenario:
                return False
            self.session.delete(scenario)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error deleting scenario: {e}")
            CustomErrorDialog("错误", f"删除情景失败: {e}").exec()
            return False

    def get_scenario_by_id(self, scenario_id):
        """根据ID获取情景"""
        try:
            scenario = self.session.query(Scenario).filter(Scenario.scenario_id == scenario_id).first()
            return scenario
        except SQLAlchemyError as e:
            print(f"Error fetching scenario by id: {e}")
            return None

    # 废弃方法
    # @Slot()
    # def open_database_login_dialog(self):
    #     """打开数据库登录对话框"""
    #     dialog = LoginDialog(self.session, self.scenario_manager)
    #     dialog.login_success.connect(self.handle_database_connected)
    #     if dialog.exec() == QDialog.Accepted:
    #         CustomInformationDialog("成功", "已成功连接到数据库。").exec()
    #         self.load_scenarios()
    #     else:
    #         CustomInformationDialog("错误", "无法连接到数据库。").exec()
    #
    # @Slot()
    # def handle_database_connected(self):
    #     """数据库登录成功后刷新情景列表"""
    #     CustomInformationDialog("成功", "已成功连接到数据库。").exec()
    #     self.load_scenarios()

    def get_element_by_scenario_id(self,scenario_id):
        pass

    def __del__(self):
        if self.session:
            self.session.close()
            print("Session closed.")
