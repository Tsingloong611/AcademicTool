# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:08 AM
# @FileName: scenario_controller.py
# @Software: PyCharm
import json

from PySide6.QtCore import QObject, Slot, Qt, Signal
from PySide6.QtWidgets import QInputDialog, QMessageBox, QDialog
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.sync import update
from sqlalchemy.sql.base import elements

# 假设您已经在 models/scenario.py 中定义了 Scenario 类，
# 其中字段为 scenario_id, scenario_name, scenario_description, ...
from models.models import Scenario, ElementBase, Element, Attribute, AttributeBase, BehaviorObject, BehaviorBaseObject, \
    Behavior, BehaviorBase, AttributeAssociation, AttributeBaseAssociation, ElementType, EnumValue, AttributeType

from views.dialogs.custom_error_dialog import CustomErrorDialog
from views.dialogs.custom_information_dialog import CustomInformationDialog
from views.dialogs.custom_warning_dialog import CustomWarningDialog
from views.login_dialog import LoginDialog
from views.scenario_manager import ScenarioDialog


class ScenarioController(QObject):
    # 发出查询结果信号
    send_sql_result = Signal(list)
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

        self.tab_widget.ElementSettingTab.request_sql_query.connect(self.execute_sql_query)
        self.send_sql_result.connect(self.tab_widget.ElementSettingTab.receive_sql_result)
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

        else:
            self.reset_status_bar()


    def build_static_data(self, scenario_id):
        """
        根据给定的 scenario_id，从数据库加载所有相关元素及其属性和行为，
        构建 static_data 字典，符合指定的简化 JSON 结构。

        Args:
            scenario_id (int): 情景的唯一标识符。

        Returns:
            dict: 包含情景要素、属性和行为的嵌套字典。
        """
        # 初始化 static_data
        static_data = {
            "scenario": {
                "scenario_id": scenario_id,
                "scenario_name": "",
                "scenario_description": "",
                "create_time": "",
                "update_time": "",
                "emergency_id": None,
                "elements": []
            }
        }

        try:
            # 预先加载所有 AttributeTypes 和 EnumValues，缓存以减少查询次数
            attribute_types = {at.attribute_type_id: at for at in self.session.query(AttributeType).all()}
            enum_values = {ev.enum_value_id: ev.value for ev in self.session.query(EnumValue).all()}


            # 获取符合条件的 Elements
            elements = self.session.query(Element).filter(
                Element.scenario_id == scenario_id,
            ).all()

            element_ids = [elem.element_id for elem in elements]

            # 获取所有相关的 Attributes
            attributes = self.session.query(Attribute).filter(
                Attribute.element_id.in_(element_ids)
            ).all()

            # 获取所有相关的 AttributeAssociations
            attribute_associations = self.session.query(AttributeAssociation).filter(
                AttributeAssociation.attribute_id.in_([attr.attribute_id for attr in attributes])
            ).all()

            # 构建属性关联字典
            attr_assoc_dict = {}
            for assoc in attribute_associations:
                if assoc.attribute_id not in attr_assoc_dict:
                    attr_assoc_dict[assoc.attribute_id] = []
                attr_assoc_dict[assoc.attribute_id].append(assoc.associated_element_id)

            # 获取所有相关的 Behaviors
            behaviors = self.session.query(Behavior).filter(
                Behavior.element_id.in_(element_ids)
            ).all()

            # 获取所有相关的 BehaviorObjects
            behavior_objects = self.session.query(BehaviorObject).filter(
                BehaviorObject.behavior_id.in_([beh.behavior_id for beh in behaviors])
            ).all()

            # 构建行为关联字典
            beh_assoc_dict = {}
            for assoc in behavior_objects:
                if assoc.behavior_id not in beh_assoc_dict:
                    beh_assoc_dict[assoc.behavior_id] = []
                beh_assoc_dict[assoc.behavior_id].append(assoc.object_element_id)

            # 将 Attributes 按 element_id 分组
            attributes_by_element = {}
            for attr in attributes:
                if attr.element_id not in attributes_by_element:
                    attributes_by_element[attr.element_id] = []
                attributes_by_element[attr.element_id].append(attr)

            # 将 Behaviors 按 element_id 分组
            behaviors_by_element = {}
            for beh in behaviors:
                if beh.element_id not in behaviors_by_element:
                    behaviors_by_element[beh.element_id] = []
                behaviors_by_element[beh.element_id].append(beh)

            for elem in elements:
                # 获取元素类型
                elem_type = self.session.query(ElementType).filter(
                    ElementType.element_type_id == elem.element_type_id
                ).one_or_none()
                elem_type_code = elem_type.code if elem_type else "unknown"

                elem_dict = {
                    "element_id": elem.element_id,
                    "element_name": elem.element_name,
                    "element_type_id": elem.element_type_id,
                    "element_parent_id": elem.element_parent_id,
                    "attributes": [],
                    "behaviors": []
                }

                # 处理属性
                elem_attributes = attributes_by_element.get(elem.element_id, [])
                for attr in elem_attributes:
                    attr_type = attribute_types.get(attr.attribute_type_id)
                    if not attr_type:
                        continue  # 或者处理未知类型


                    attr_value = attr.attribute_value

                    # 根据属性类型处理关联
                    if attr_type.code not in ['string', 'int', 'boolean', 'enum']:
                        # 需要从 attribute_association 获取关联的 element_id
                        associated_ids = attr_assoc_dict.get(attr.attribute_id, [])
                        if attr.is_multi_valued:
                            attr_value = associated_ids  # 多个关联ID
                        else:
                            attr_value = associated_ids[0] if associated_ids else None  # 单个关联ID
                            attr_value = list(attr_value)

                    # 构建属性字典
                    attr_entry = {
                        "attribute_id": attr.attribute_id,
                        "attribute_name": attr.attribute_name,
                        "attribute_type_id": attr.attribute_type_id,
                        "is_required": bool(attr.is_required),
                        "is_multi_valued": bool(attr.is_multi_valued),
                        "enum_value_id": attr.enum_value_id,
                        "attribute_value": attr_value
                    }

                    elem_dict["attributes"].append(attr_entry)

                # 处理行为
                elem_behaviors = behaviors_by_element.get(elem.element_id, [])
                for beh in elem_behaviors:
                    # 获取行为类型
                    beh_type = self.session.query(ElementType).filter(
                        ElementType.element_type_id == beh.object_type_id
                    ).one_or_none()

                    beh_type_code = beh_type.code if beh_type else "unknown"

                    # 根据行为类型处理关联
                    associated_ids = beh_assoc_dict.get(beh.behavior_id, [])
                    if beh.is_multi_valued:
                        related_objects = associated_ids
                    else:
                        related_objects = [associated_ids[0]] if associated_ids else []

                    beh_entry = {
                        "behavior_id": beh.behavior_id,
                        "behavior_name": beh.behavior_name,
                        "is_required": bool(beh.is_required),
                        "object_type_id": beh.object_type_id,
                        "is_multi_valued": bool(beh.is_multi_valued),
                        "related_objects": related_objects
                    }

                    elem_dict["behaviors"].append(beh_entry)

                static_data["scenario"]["elements"].append(elem_dict)

        except AttributeError as e:
            # 记录错误日志
            print(f"AttributeError: {e}")
        except Exception as e:
            # 记录其他错误日志
            print(f"Error: {e}")

        try:
            # 获取情景的其他信息（名称、描述、时间等）
            scenario = self.session.query(Scenario).filter(
                Scenario.scenario_id == scenario_id
            ).one_or_none()

            if scenario:
                static_data["scenario"]["scenario_name"] = scenario.scenario_name
                static_data["scenario"]["scenario_description"] = scenario.scenario_description
                static_data["scenario"][
                    "create_time"] = scenario.scenario_create_time.isoformat() if scenario.scenario_create_time else None
                static_data["scenario"][
                    "update_time"] = scenario.scenario_update_time.isoformat() if scenario.scenario_update_time else None
                static_data["scenario"]["emergency_id"] = scenario.emergency_id

        except Exception as e:
            print(f"Error while fetching scenario details: {e}")

        print(f"static_data: {json.dumps(static_data, ensure_ascii=False, indent=2)}")
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

    def execute_sql_query(self, sql_query):
        print("执行查询")
        # 执行 SQL 查询
        result = self.get_result_by_sql(sql_query)
        # 发出查询结果信号
        self.send_sql_result.emit(result)

    def get_result_by_sql(self, sql_query):
        try:
            # 执行查询
            result = self.session.execute(text(sql_query)).fetchall()
            print(f"查询结果: {result}")
            return result
        except Exception as e:
            print(f"执行 SQL 查询时出错: {e}")
            return []

    def __del__(self):
        if self.session:
            self.session.close()
            print("Session closed.")
