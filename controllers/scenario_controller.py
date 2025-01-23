# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:08 AM
# @FileName: scenario_controller.py
# @Software: PyCharm
import json
import datetime
import os
import re

from PySide6.QtCore import QObject, Slot, Qt, Signal
from PySide6.QtWidgets import QInputDialog, QMessageBox, QDialog
from requests import session, delete
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.sync import update
from sqlalchemy.sql.base import elements

from models.models import Scenario, BehaviorValue, AttributeValue, Category, Entity, Template, BehaviorValueReference, \
    AttributeValueReference, entity_category, Owl, Bayes, OwlClassBehavior, OwlClassAttribute, OwlClass, BayesNodeState, \
    BayesNode, BayesNodeTarget
# 假设您已经在 models/scenario.py 中定义了 Scenario 类，
# 其中字段为 scenario_id, scenario_name, scenario_description, ...
from views.dialogs.custom_error_dialog import CustomErrorDialog
from views.dialogs.custom_information_dialog import CustomInformationDialog
from views.dialogs.custom_warning_dialog import CustomWarningDialog
from views.login_dialog import LoginDialog
from views.scenario_manager import ScenarioDialog
import logging
import json
from sqlalchemy.orm import Session
from typing import Dict, Any, Union, List, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class ScenarioController(QObject):
    # 发出查询结果信号
    send_sql_result = Signal(list)
    def __init__(self, scenario_manager, status_bar, tab_widget, db_manager):
        super().__init__()
        self.scenario_id = 1
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
        self.tab_widget.ElementSettingTab.save_to_database_signal.connect(self.apply_changes_from_json)
        self.tab_widget.generate_model_save_to_database.connect(self.generate_model_save_to_database)
        self.tab_widget.generate_bayes_save_to_database.connect(self.generate_bayes_save_to_database)
        self.tab_widget.ConditionSettingTab.save_plan_to_database_signal.connect(self.apply_changes_from_json)
        # 加载初始数据
        self.load_scenarios()

        # 从数据库管理器获取连接信息并更新状态栏
        connection_info = self.db_manager.get_connection_info()
        username = connection_info.get('username', '未知用户')
        database = connection_info.get('database', '未知数据库')
        self.status_bar.update_user_info(username, database)

    def load_scenarios(self,selected_scenario_id=None):
        """加载并在界面上显示所有情景"""
        scenarios = self.get_all_scenarios()
        self.scenario_manager.populate_scenarios(scenarios,selected_scenario_id)
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
        self.scenario_id = scenario_id
        if scenario:
            self.current_scenario = scenario
            # 从数据库管理器获取连接信息
            connection_info = self.db_manager.get_connection_info()
            username = connection_info.get('username', '未知用户')
            database = connection_info.get('database', '未知数据库')


            owl_record = self.session.query(Owl).filter(Owl.scenario_id == scenario.scenario_id).first()

            if owl_record:
                owl_state = "就绪"
            else:
                owl_state = "未完成"

            bayes_record = self.session.query(Bayes).filter(Bayes.scenario_id == scenario.scenario_id).first()
            if bayes_record:
                bayes_state = "待推演"
            else:
                bayes_state = "待推演"
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

            self.tab_widget.ElementSettingTab.session = self.session

            self.static_data = self.get_scenario_data(self.session, scenario_id)
            # 缩进
            self.static_data = json.dumps(self.static_data, indent=4, ensure_ascii=False)

            print(f"得到了{self.static_data}")
            self.static_data = json.loads(self.static_data)

            self.tab_widget.ElementSettingTab.scenario_data = self.static_data
            if not self.static_data["entities"]:
                print("No entities found for the selected scenario.")
                self.tab_widget.ElementSettingTab.element_data = {}
            else:
                entity_data = {
                    entity["entity_id"]: entity for entity in self.static_data["entities"]
                }
                print(f"读取到entity_data: {entity_data}")
                self.tab_widget.ElementSettingTab.element_data = entity_data



        else:
            self.reset_status_bar()

    from typing import Dict, Any
    from sqlalchemy.orm import Session

    def get_scenario_data(self, session: Session, scenario_id: int) -> Dict[str, Any]:
        """
        根据 scenario_id，获取该场景下所有的实体(Entity)、
        以及与实体相关的属性(AttributeValue) / 行为(BehaviorValue) / 类别(Category) 等信息，
        并组织成一个包含 scenario + entities + attributes + behaviors 等的字典。
        """
        # 1. 查找对应的场景
        scenario = session.query(Scenario).filter_by(scenario_id=scenario_id).one()

        # 2. 组织顶层结构
        scenario_data = {
            "scenario_id": scenario.scenario_id,
            "scenario_name": scenario.scenario_name,
            "scenario_description": scenario.scenario_description,
            "scenario_create_time": str(scenario.scenario_create_time),
            "scenario_update_time": str(scenario.scenario_update_time),
            "emergency_id": scenario.emergency_id,
            "entities": []
        }

        # 3. 遍历该 scenario 下的所有 entity
        for entity in scenario.entities:
            entity_dict = {
                "entity_id": entity.entity_id,
                "entity_name": entity.entity_name,
                "entity_type_id": entity.entity_type_id,
                "entity_parent_id": entity.entity_parent_id,
                "scenario_id": entity.scenario_id,
                "create_time": str(entity.create_time),
                "update_time": str(entity.update_time),
                "categories": [],
                "attributes": [],
                "behaviors": []
            }

            # 4. 收集关联的 category
            for cat in entity.categories:
                entity_dict["categories"].append({
                    "category_id": cat.category_id,
                    "category_name": cat.category_name,
                    "description": cat.description
                })

            # 5. 收集 attribute_value
            for av in entity.attribute_values:
                attr_def = av.attribute_definition
                # 优先使用 attribute_value.attribute_name，如果没有则 fallback 到 attribute_code_name
                final_attr_name = av.attribute_name or attr_def.attribute_code.attribute_code_name

                attribute_item = {
                    "attribute_value_id": av.attribute_value_id,
                    "attribute_definition_id": attr_def.attribute_definition_id,
                    "china_default_name": attr_def.china_default_name,
                    "english_default_name": attr_def.english_default_name,
                    "attribute_code_name": attr_def.attribute_code.attribute_code_name,
                    "attribute_aspect_name": attr_def.attribute_aspect.attribute_aspect_name,
                    "attribute_type_code": attr_def.attribute_type.attribute_type_code,
                    "is_required": bool(attr_def.is_required),
                    "is_multi_valued": bool(attr_def.is_multi_valued),
                    "is_reference": bool(attr_def.is_reference),
                    "reference_target_type_id": attr_def.reference_target_type_id,
                    "default_value": attr_def.default_value,
                    "description": attr_def.description,
                    # 读取存放在 attribute_value 表里的值
                    "attribute_value": av.attribute_value,

                    # 最终的展示名称(可能来自 attribute_name, 或者 attribute_code_name)
                    "attribute_name": final_attr_name,

                    # referenced_entities
                    "referenced_entities": []
                }

                # 如果是引用型属性 (is_reference=True)，从 attribute_value_reference 表查所有引用
                if attr_def.is_reference:
                    for ref in av.references:
                        attribute_item["referenced_entities"].append(ref.referenced_entity_id)

                entity_dict["attributes"].append(attribute_item)

            # 6. 收集 behavior_value
            for bv in entity.behavior_values:
                bh_def = bv.behavior_definition
                # behavior_value.behavior_name 若不为空，就直接用；否则 fallback 到 behavior_code_name
                code_obj = bh_def.behavior_code_ref  # BehaviorCode
                fallback_name = code_obj.behavior_code_name if code_obj else ""

                final_behavior_name = bv.behavior_name or fallback_name

                behavior_item = {
                    "behavior_value_id": bv.behavior_value_id,
                    "behavior_definition_id": bh_def.behavior_definition_id,
                    # 用中文名 english_default_name 也可以存到这里视具体需求
                    "china_default_name": bh_def.china_default_name,
                    "english_default_name": bh_def.english_default_name,
                    # 最终的行为名
                    "behavior_name": final_behavior_name,

                    # behavior_code_name => behavior_code_ref.behavior_code_name
                    "behavior_code_name": code_obj.behavior_code_name if code_obj else "",

                    "object_entity_type_id": bh_def.object_entity_type_id,
                    "is_required": bool(bh_def.is_required),
                    "is_multi_valued": bool(bh_def.is_multi_valued),
                    "description": bh_def.description,
                    "create_time": str(bv.create_time),
                    "update_time": str(bv.update_time),

                    # behavior_value_references
                    "object_entities": []
                }

                # 收集 behavior_value_reference
                for ref in bv.references:
                    behavior_item["object_entities"].append(ref.object_entity_id)

                entity_dict["behaviors"].append(behavior_item)

            scenario_data["entities"].append(entity_dict)

        return scenario_data

    def apply_changes_from_json(self,entity_data_list: List[Dict[str, Any]],delete_mode = True):
        """
        将 JSON 列表中的多个实体（含 attributes/behaviors 等）批量写回数据库。

        - entity_data_list: 形如您贴出的 JSON 数组，每个元素是一个 Entity 的完整信息。
        """
        session = self.session
        if delete_mode == True:
            # -1. 把json中不存在的实体删除

            current_entities = session.query(Entity).filter_by(
                scenario_id=self.current_scenario.scenario_id
            ).all()
            current_entity_ids = {entity.entity_id for entity in current_entities}
            json_ids = {entity["entity_id"] for entity in entity_data_list}

            entities_to_delete = current_entity_ids - json_ids

            if entities_to_delete:
                try:
                    session.query(Entity).filter(
                        Entity.scenario_id == self.current_scenario.scenario_id,
                        Entity.entity_id.in_(entities_to_delete)
                    ).delete(synchronize_session='fetch')
                    session.flush()
                except Exception as e:
                    session.rollback()
                    print(f"删除失败: {str(e)}")
                    raise
        # 0. 用于记录临时负数ID => 数据库生成ID 的映射
        temp_id_map = {}

        # 1. 先插入/更新所有 Entity，拿到它们的真实 ID
        for ent_data in entity_data_list:
            self._process_single_entity(session, ent_data, temp_id_map)
        # 2. 现在可以更新parent关系了
        if hasattr(self, '_pending_parents'):
            for child_id, temp_parent_id in self._pending_parents:
                real_parent_id = temp_id_map[temp_parent_id]
                entity = session.query(Entity).filter_by(entity_id=child_id).one()
                entity.entity_parent_id = real_parent_id
            session.flush()
            # 清理临时数据
            del self._pending_parents

        # 2. 第二轮：处理 “Item”/“Entity” 引用关系（因为可能后面才出现被引用对象）
        for ent_data in entity_data_list:
            self._process_entity_attributes(session, ent_data, temp_id_map)
            self._process_entity_behaviors(session, ent_data, temp_id_map)

        session.commit()
        print("回写完成。")

    def _process_single_entity(self,session: Session, ent_data: Dict[str, Any], temp_id_map: Dict[int, int]) -> int:
        """
        第一阶段：只处理 Entity 本身（含 categories），不处理 attributes/behaviors 的引用。
        返回该实体在数据库中的真实 ID。
        """
        e_id = ent_data["entity_id"]
        # 解析基础字段
        entity_name = ent_data["entity_name"]
        entity_type_id = ent_data["entity_type_id"]
        scenario_id = ent_data["scenario_id"]
        create_time = self._parse_datetime(ent_data.get("create_time"))
        update_time = self._parse_datetime(ent_data.get("update_time"))
        parent_id = ent_data.get("entity_parent_id", None)
        parent_is_temp = parent_id is not None and parent_id < 0
        if parent_is_temp:
            parent_id = None  # 临时设为None

        if e_id < 0:
            # 新建
            entity_obj = Entity(
                entity_name=entity_name,
                entity_type_id=entity_type_id,
                scenario_id=scenario_id,
                entity_parent_id=parent_id,
                create_time=create_time,
                update_time=update_time
            )
            session.add(entity_obj)
            session.flush()  # 让数据库生成新的 entity_id
            real_eid = entity_obj.entity_id
            temp_id_map[e_id] = real_eid
            if parent_is_temp:
                # 可以用一个列表存储待更新的parent关系
                if not hasattr(self, '_pending_parents'):
                    self._pending_parents = []
                self._pending_parents.append((real_eid, ent_data["entity_parent_id"]))
        else:
            # 更新
            entity_obj = session.query(Entity).filter_by(entity_id=e_id).one()
            entity_obj.entity_name = entity_name
            entity_obj.entity_type_id = entity_type_id
            entity_obj.scenario_id = scenario_id
            entity_obj.entity_parent_id = parent_id
            entity_obj.update_time = update_time
            session.flush()
            real_eid = e_id

        # 处理 categories (多对多) -- 仅覆盖或增量看业务需求
        # 先清空再插入(简单方式)
        session.execute(
            entity_category.delete().where(entity_category.c.entity_id == real_eid)
        )
        # ent_data["categories"] 形如: [{"category_id":3, "category_name":"HazardElement", ...}, ...]
        for cat_dict in ent_data.get("categories", []):
            cat_id = cat_dict["category_id"]
            if cat_id < 0:
                # 新建 Category
                cat_obj = Category(
                    category_name=cat_dict["category_name"],
                    description=cat_dict.get("description"),
                    create_time=datetime.datetime.now(),
                    update_time=datetime.datetime.now()
                )
                session.add(cat_obj)
                session.flush()
                cat_id = cat_obj.category_id
            # 建立多对多
            session.execute(
                entity_category.insert().values(entity_id=real_eid, category_id=cat_id)
            )
        session.flush()

        return real_eid

    def _process_entity_attributes(self, session: Session, ent_data: Dict[str, Any], temp_id_map: Dict[int, int]):
        """
        Process Entity Attributes with duplicate reference handling.
        """
        e_id = ent_data["entity_id"]
        if e_id < 0:
            e_id = temp_id_map[e_id]

        for attr_dict in ent_data.get("attributes", []):
            av_id = attr_dict["attribute_value_id"]
            attr_value = attr_dict.get("attribute_value", None)
            attr_type_code = attr_dict.get("attribute_type_code", None)
            create_time = datetime.datetime.now()
            update_time = datetime.datetime.now()

            # 1) upsert attribute_value
            if av_id < 0:
                av_obj = AttributeValue(
                    entity_id=e_id,
                    attribute_definition_id=attr_dict["attribute_definition_id"],
                    attribute_name=attr_dict.get("attribute_name"),
                    attribute_value=None,
                    create_time=create_time,
                    update_time=update_time
                )
                session.add(av_obj)
                session.flush()
                real_av_id = av_obj.attribute_value_id
                temp_id_map[av_id] = real_av_id
            else:
                av_obj = session.query(AttributeValue).filter_by(attribute_value_id=av_id).one()
                av_obj.attribute_name = attr_dict.get("attribute_name")
                av_obj.update_time = update_time
                real_av_id = av_id

            # 2) Handle different attribute types
            if attr_type_code == "Item":
                # Handle Item references - update parent relationships
                referenced_entities = attr_dict.get("referenced_entities", [])
                unique_refs = list(set(referenced_entities))  # Remove duplicates

                for ref_id in unique_refs:
                    if ref_id < 0:
                        ref_id = temp_id_map[ref_id]
                    ref_entity = session.query(Entity).filter_by(entity_id=ref_id).one()
                    ref_entity.entity_parent_id = e_id

                av_obj.attribute_value = None

            elif attr_type_code == "Entity":
                # Handle Entity references
                av_obj.attribute_value = None
                session.query(AttributeValueReference).filter_by(attribute_value_id=real_av_id).delete()

                # Get referenced entities and remove duplicates
                referenced_entities = []
                for ref_id in attr_dict.get("referenced_entities", []):
                    if isinstance(ref_id, dict):
                        ref_id = ref_id["referenced_entity_id"]
                    if ref_id < 0:
                        ref_id = temp_id_map[ref_id]
                    referenced_entities.append(ref_id)

                # Remove duplicates while preserving order
                unique_refs = list(dict.fromkeys(referenced_entities))

                # Add unique references
                for ref_id in unique_refs:
                    avr = AttributeValueReference(
                        attribute_value_id=real_av_id,
                        referenced_entity_id=ref_id
                    )
                    session.add(avr)
            else:
                # Handle regular attributes
                av_obj.attribute_value = attr_value

            try:
                session.flush()
            except IntegrityError as e:
                session.rollback()
                raise ValueError(f"Integrity error processing attribute {attr_dict.get('attribute_name')}: {str(e)}")
    def _process_entity_behaviors(self,session: Session, ent_data: Dict[str, Any], temp_id_map: Dict[int, int]):
        """
        处理 behaviors: 负数 => 新建, 正数 => 更新
        若 behavior => "object_entities", type为 "Entity" => behavior_value_reference
        (代码中可以从 behavior_definition_id 找 object_entity_type_id => entity or item?)
        这里做个示例: object_entity_type_id指向 entity => ref
        """
        e_id = ent_data["entity_id"]
        if e_id < 0:
            e_id = temp_id_map[e_id]

        for bhv_dict in ent_data.get("behaviors", []):
            bv_id = bhv_dict["behavior_value_id"]
            behavior_definition_id = bhv_dict["behavior_definition_id"]
            create_time = self._parse_datetime(bhv_dict.get("create_time", None)) or datetime.datetime.now()
            update_time = self._parse_datetime(bhv_dict.get("update_time", None)) or datetime.datetime.now()

            if bv_id < 0:
                # 新建
                bv_obj = BehaviorValue(
                    behavior_definition_id=behavior_definition_id,
                    behavior_name=bhv_dict.get("behavior_name"),
                    subject_entity_id=e_id,
                    create_time=create_time,
                    update_time=update_time
                )
                session.add(bv_obj)
                session.flush()
                real_bv_id = bv_obj.behavior_value_id
                temp_id_map[bv_id] = real_bv_id
            else:
                # 更新
                bv_obj = session.query(BehaviorValue).filter_by(behavior_value_id=bv_id).one()
                bv_obj.behavior_name = bhv_dict.get("behavior_name")
                bv_obj.update_time = update_time
                real_bv_id = bv_id

            # 清空旧引用
            session.query(BehaviorValueReference).filter_by(behavior_value_id=real_bv_id).delete()

            # 如果是类似 entity 引用，就往 behavior_value_reference 写
            # 这里可以从 behavior_definition(object_entity_type_id) 来判断是否 item/entity
            # 为简单，假设“都按 entity 处理”
            for ref_data in bhv_dict.get("object_entities", []):
                obj_id = ref_data
                # 可能 ref_data 就是个 int；如果是dict,自行拆
                if isinstance(ref_data, dict):
                    obj_id = ref_data["object_entity_id"]

                if obj_id < 0:
                    obj_id = temp_id_map[obj_id]
                bvr = BehaviorValueReference(
                    behavior_value_id=real_bv_id,
                    object_entity_id=obj_id
                )
                session.add(bvr)
            session.flush()

    def _parse_datetime(self,dt_str: Union[str, None]) -> datetime.datetime:
        """
        尝试解析 datetime 字符串，若无则返回 None
        """
        if not dt_str:
            return None
        # 可能日期格式: "2025-01-17 15:14:24"
        # 做一个简单的 parse
        return datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")

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
                self.load_scenarios(new_scenario.scenario_id)
                # 自动加载
                self.handle_scenario_selected(new_scenario.scenario_id,new_scenario.scenario_name,new_scenario.scenario_description)


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
    def handle_delete_requested(self, scenario_id):
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
        self.scenario_manager.list_widget.setCurrentItem(None)

        self.session.execute(text(f"DELETE FROM scenario WHERE scenario_id = {scenario_id}"))
        self.session.commit()
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
                scenario_create_time=datetime.datetime.utcnow(),  # Set to current UTC time
                scenario_update_time=datetime.datetime.utcnow(),  # Optionally set update time
                emergency_id=1  # 根据实际需求调整
            )
            self.session.add(new_scenario)
            self.session.commit()  # 提交以获取 new_scenario 的 ID

#            self.replicate_all_for_scenario(new_scenario.scenario_id) TO DO 暂时废除

            # 提交所有新的 Element 实例
            self.session.commit()
            self.session.refresh(new_scenario)
            return new_scenario
            # 查找新添加的情景并选中

        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error adding scenario: {e}")
            CustomErrorDialog("错误", f"新增情景失败: {e}").exec()
            return None


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


    def replicate_all_for_scenario(self, scenario_id: int):
        """
        1) 根据 scenario_id 获取该场景。
        2) 遍历数据库中所有(或特定) Template，为每个 Template 在该场景下新建一个 Entity。
        3) 为该新 Entity:
           - 附加模板所指定的 category
           - 不管 is_required 与否，对 template.attribute_definitions 中的每个属性都建一条 AttributeValue
           - 同理，对 template.behavior_definitions 中的每个行为都建一条 BehaviorValue
        4) 最后 commit。
        """

        # 0. 找到目标场景
        scenario_obj = self.session.query(Scenario).get(scenario_id)
        if not scenario_obj:
            raise ValueError(f"Scenario(id={scenario_id}) not found.")

        # 1. 获取要复制的所有模板 (可根据业务需求，添加 filter)
        all_templates = self.session.query(Template).all()

        # 2. 遍历模板，新建实体
        for tpl in all_templates:
            # 2.1 创建一个 entity 对象
            new_entity = Entity(
                entity_name=f"{tpl.template_name}_复制品",
                entity_type_id=tpl.entity_type_id,
                scenario_id=scenario_obj.scenario_id,
                create_time=datetime.utcnow(),
                update_time=datetime.utcnow()
            )
            self.session.add(new_entity)
            self.session.flush()  # 拿到 new_entity.entity_id

            # 2.2 附加模板的 category 到新实体上
            #     template.category_id -> 找到 Category 后 append
            cat_obj = self.session.query(Category).get(tpl.category_id)
            if cat_obj:
                new_entity.categories.append(cat_obj)

            # 2.3 遍历 template.attribute_definitions，对每条都创建 AttributeValue
            for attr_def in tpl.attribute_definitions:
                av = AttributeValue(
                    entity_id=new_entity.entity_id,
                    attribute_definition_id=attr_def.attribute_definition_id,
                    attribute_value=attr_def.default_value,  # 可以用默认值，也可设为 None
                    create_time=datetime.utcnow(),
                    update_time=datetime.utcnow()
                )
                self.session.add(av)
                # 不一定要 flush()，可留到 commit 一并提交

            # 2.4 遍历 template.behavior_definitions，对每条都创建 BehaviorValue
            for bhv_def in tpl.behavior_definitions:
                bv = BehaviorValue(
                    behavior_definition_id=bhv_def.behavior_definition_id,
                    subject_entity_id=new_entity.entity_id,
                    create_time=datetime.utcnow(),
                    update_time=datetime.utcnow()
                )
                self.session.add(bv)

        # 3. 一次性 commit
        self.session.commit()
        print(f"复制完成: scenario_id={scenario_id} 已新增 {len(all_templates)} 个entity。")

    def populate_owl_database(self, session, scenario_id, owl_dir):
        # 1. Insert OWL files
        owl_files = {
            'Merge.owl': 1,
            'Emergency.owl': 2,
            'ScenarioElement.owl': 3,
            'Scenario.owl': 4
        }

        owl_records = []
        for owl_file, owl_type_id in owl_files.items():
            owl_path = os.path.join(owl_dir, owl_file)
            if os.path.exists(owl_path):
                owl = Owl(
                    owl_type_id=owl_type_id,
                    owl_file_path=owl_path,
                    scenario_id=scenario_id
                )
                session.add(owl)
                session.flush()  # Get the owl_id
                owl_records.append((owl, owl_file))

        # 2. Process corresponding structure files
        for owl, owl_file in owl_records:
            json_file = owl_file.replace('.owl', '_ontology_structure.json')
            json_path = os.path.join(owl_dir, json_file)

            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    structure = json.load(f)
                    self.process_owl_structure(session, structure, owl.owl_id)

    def process_owl_structure(self,session, structure, owl_id):
        # Keep track of class IDs for parent relationships
        class_map = {}

        # First pass: Create all classes
        for class_name, class_data in structure.items():
            owl_class = OwlClass(
                owl_class_name=class_name,
                owl_id=owl_id
            )
            session.add(owl_class)
            session.flush()
            class_map[class_name] = owl_class.owl_class_id

        # Second pass: Set parent relationships
        for class_name, class_data in structure.items():
            if 'parent_class' in class_data and class_data['parent_class'] in class_map:
                owl_class = session.query(OwlClass).filter_by(
                    owl_class_name=class_name,
                    owl_id=owl_id
                ).first()
                if owl_class:
                    owl_class.owl_class_parent = class_map[class_data['parent_class']]

        # Third pass: Add properties
        current_time = datetime.datetime.utcnow()

        for class_name, class_data in structure.items():
            if 'Properties' in class_data:
                owl_class = session.query(OwlClass).filter_by(
                    owl_class_name=class_name,
                    owl_id=owl_id
                ).first()

                if owl_class:
                    for prop in class_data['Properties']:
                        if prop['property_type'].lower() == 'datatypeproperty':
                            # Add attribute
                            attr = OwlClassAttribute(
                                owl_class_attribute_name=prop['property_name'],
                                owl_class_attribute_range=prop['property_range'],
                                owl_class_id=owl_class.owl_class_id,
                                create_time=current_time,
                                update_time=current_time
                            )
                            session.add(attr)

                        elif prop['property_type'].lower() == 'objectproperty':
                            # Add behavior
                            behavior = OwlClassBehavior(
                                owl_class_behavior_name=prop['property_name'],
                                owl_class_behavior_range=prop['property_range'],
                                owl_class_id=owl_class.owl_class_id,
                                create_time=current_time,
                                update_time=current_time
                            )
                            session.add(behavior)

    def generate_model_save_to_database(self):
        session = self.session

        # Delete existing OWL records
        try:
            rows_deleted = session.query(Owl).filter(
                Owl.scenario_id == self.current_scenario.scenario_id
            ).delete()

            if rows_deleted > 0:
                print(f"已删除 {rows_deleted} 条记录")
            else:
                print(f"没有找到符合条件的记录需要删除")

            session.commit()

        except Exception as e:
            session.rollback()
            print(f"删除记录时出错: {e}")
            return

        # Add new records
        owl_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            f'../data/sysml2/{self.current_scenario.scenario_id}/owl'
        ))

        try:
            self.populate_owl_database(session, self.current_scenario.scenario_id, owl_dir)
            session.commit()
            self.status_bar.owl_status_label.setText(self.tr("OWL 文件状态: ") + self.tr("就绪"))
            print("OWL数据库更新成功")
            self.update_gui_with_data()

        except Exception as e:
            session.rollback()
            print(f"插入OWL数据时出错: {e}")
            self.status_bar.owl_status_label.setText(self.tr("OWL 文件状态: ") + self.tr("错误"))

    def fetch_ontology_data(self,session, scenario_id: int) -> Tuple[Dict, Dict, Dict, Dict]:
        """
        从数据库获取数据并组织成所需的字典格式

        Returns:
            Tuple[Dict, Dict, Dict, Dict]: 返回SVG_FILES, CLASS_OPTIONS, ATTRIBUTE_SAMPLE_DATA, BEHAVIOR_SAMPLE_DATA
        """

        # 1. 获取OWL文件信息
        owl_type_to_name = {
            1: "整体",
            2: "突发事件本体",
            3: "情景要素本体",
            4: "情景本体"
        }

        svg_files = {}
        owl_records = session.query(Owl).filter_by(scenario_id=scenario_id).all()

        for owl in owl_records:
            owl_name = owl_type_to_name.get(owl.owl_type_id)
            if owl_name:
                # 获取完整的SVG路径
                svg_path = owl.owl_file_path.replace('.owl', '.svg')
                svg_files[owl_name] = svg_path

        # 2. 获取每个本体的类
        class_options = {name: [] for name in owl_type_to_name.values()}

        for owl in owl_records:
            owl_name = owl_type_to_name.get(owl.owl_type_id)
            if owl_name:
                # 查询该owl_id下的所有类
                classes = session.query(OwlClass).filter_by(owl_id=owl.owl_id).all()
                class_options[owl_name] = [cls.owl_class_name for cls in classes]

        # 3. 获取每个类的属性
        attribute_sample_data = {}

        # 获取所有类
        all_classes = session.query(OwlClass).join(Owl).filter(Owl.scenario_id == scenario_id).all()

        for cls in all_classes:
            # 查询该类的所有属性
            attributes = session.query(OwlClassAttribute).filter_by(owl_class_id=cls.owl_class_id).all()

            if attributes:  # 只添加有属性的类
                attribute_sample_data[cls.owl_class_name] = [
                    (attr.owl_class_attribute_name, attr.owl_class_attribute_range)
                    for attr in attributes
                ]

        # 4. 获取每个类的行为
        behavior_sample_data = {}

        for cls in all_classes:
            # 查询该类的所有行为
            behaviors = session.query(OwlClassBehavior).filter_by(owl_class_id=cls.owl_class_id).all()

            if behaviors:  # 只添加有行为的类
                behavior_sample_data[cls.owl_class_name] = [
                    (behavior.owl_class_behavior_name, behavior.owl_class_behavior_range)
                    for behavior in behaviors
                ]

        return svg_files, class_options, attribute_sample_data, behavior_sample_data

    def update_gui_with_data(self):
        """
        用于在GUI类中调用，更新界面数据
        """
        try:
            svg_files, class_options, attribute_data, behavior_data = self.fetch_ontology_data(
                self.session,
                self.current_scenario.scenario_id
            )

            # 更新类变量
            self.tab_widget.ModelGenerationTab.SVG_FILES = svg_files
            self.tab_widget.ModelGenerationTab.CLASS_OPTIONS = class_options
            self.tab_widget.ModelGenerationTab.ATTRIBUTE_SAMPLE_DATA = attribute_data
            self.tab_widget.ModelGenerationTab.BEHAVIOR_SAMPLE_DATA = behavior_data
            print("数据获取成功")


            return True, "数据获取成功"

        except Exception as e:
            return False, f"数据获取失败: {str(e)}"

    def generate_bayes_save_to_database(self):
        """
        生成贝叶斯网络并保存到数据库
        如果当前场景已存在贝叶斯网络则更新，否则创建新的
        """
        try:
            # 查找当前场景的贝叶斯网络
            existing_bayes = self.session.query(Bayes).filter(
                Bayes.scenario_id == self.current_scenario.scenario_id
            ).first()

            # 获取新的文件路径
            bn_file = os.path.abspath(os.path.join(
                os.path.dirname(__file__),
                f'../data/bn/{self.current_scenario.scenario_id}/bn_structure.bif'
            ))

            if existing_bayes:
                # 更新现有贝叶斯网络的文件路径
                existing_bayes.bayes_file_path = bn_file
                bayes = existing_bayes
            else:
                # 创建新的贝叶斯网络记录
                bayes = Bayes(
                    bayes_file_path=bn_file,
                    scenario_id=self.current_scenario.scenario_id
                )
                self.session.add(bayes)

            self.session.flush()  # 获取bayes_id

            # 读取节点数据
            node_data_file = os.path.join(os.path.dirname(bn_file), 'node_data.json')
            with open(node_data_file, 'r') as f:
                node_data = json.load(f)

            # 处理节点和状态
            node_id_map = {}  # 用于存储节点名称到ID的映射
            current_time = datetime.datetime.utcnow()

            for node_name, states in node_data.items():
                # 查找或创建节点
                existing_node = self.session.query(BayesNode).filter(
                    BayesNode.bayes_id == bayes.bayes_id,
                    BayesNode.bayes_node_name == node_name
                ).first()

                if existing_node:
                    node = existing_node
                else:
                    node = BayesNode(
                        bayes_node_name=node_name,
                        bayes_id=bayes.bayes_id
                    )
                    self.session.add(node)
                    self.session.flush()

                node_id_map[node_name] = node.bayes_node_id

                # 更新节点状态
                for state_name, probability in states:
                    existing_state = self.session.query(BayesNodeState).filter(
                        BayesNodeState.bayes_node_id == node.bayes_node_id,
                        BayesNodeState.bayes_node_state_name == state_name
                    ).first()

                    if existing_state:
                        # 更新现有状态的概率
                        existing_state.bayes_node_state_prior_probability = float(probability)
                        existing_state.update_time = current_time
                    else:
                        # 创建新的状态
                        node_state = BayesNodeState(
                            bayes_node_state_name=state_name,
                            bayes_node_state_prior_probability=float(probability),
                            bayes_node_id=node.bayes_node_id,
                            create_time=current_time,
                            update_time=current_time
                        )
                        self.session.add(node_state)

            # 如果是新建的贝叶斯网络，需要创建节点关系
            if not existing_bayes:
                # 读取bif文件获取节点关系
                with open(bn_file, 'r') as f:
                    bif_content = f.read()

                # 使用正则表达式提取节点关系
                pattern = r'probability\s*\(\s*([^|]+)\s*\|\s*([^)]+)\)'
                relationships = re.findall(pattern, bif_content)

                # 创建节点关系记录
                for target, sources in relationships:
                    target_node = target.strip()
                    source_nodes = [s.strip() for s in sources.split(',')]

                    for source_node in source_nodes:
                        node_target = BayesNodeTarget(
                            source_node_id=node_id_map[source_node],
                            target_node_id=node_id_map[target_node]
                        )
                        self.session.add(node_target)

            self.session.commit()
            print("贝叶斯网络数据已成功保存到数据库")

        except Exception as e:
            self.session.rollback()
            print(f"保存贝叶斯网络数据时出错: {e}")
            raise