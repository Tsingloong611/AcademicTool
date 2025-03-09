# -*- coding: utf-8 -*-
# @Time    : 1/22/2025 8:02 PM
# @FileName: plan.py
# @Software: PyCharm
import json
import logging
import os
import re
from collections import defaultdict
from datetime import datetime

import pandas as pd
import requests
from PySide6.QtCore import QTimer, QThread, QCoreApplication
from jedi.inference.gradual.typing import Tuple
from semantictools import config_path
from sqlalchemy import select, and_, create_engine, text, bindparam
from sqlalchemy.orm import Session, sessionmaker
from typing import Dict, List, Optional, Any

from models.models import AttributeValue, Entity, AttributeDefinition, AttributeCode, EntityType, Template, Category, \
    PosterioriData, BayesNode, BayesNodeState, AttributeValueReference
from views.dialogs.custom_warning_dialog import CustomWarningDialog


class PlanDataCollector:
    def __init__(self, session: Session, scenario_id: int):
        """
        初始化计划数据收集器

        Args:
            session: SQLAlchemy会话
            scenario_id: 场景ID
        """
        self.session = session
        self.scenario_id = scenario_id

    def get_road_passibility(self) -> List[Any]:
        """获取道路通行性数据"""
        sql = """
        SELECT av.attribute_value_id, av.entity_id, av.attribute_definition_id, 
               av.attribute_name, av.attribute_value 
        FROM attribute_value av
        JOIN entity e ON av.entity_id = e.entity_id
        JOIN attribute_definition ad ON av.attribute_definition_id = ad.attribute_definition_id
        JOIN attribute_code ac ON ad.attribute_code_id = ac.attribute_code_id
        WHERE e.scenario_id = :scenario_id
        AND (ac.attribute_code_name = 'ClosureCondition'
        OR(ac.attribute_code_name = 'RoadClosureStatus' AND e.entity_parent_id IS NOT NULL))
        """
        return self.session.execute(text(sql), {"scenario_id": self.scenario_id}).all()

    def get_road_damage(self) -> List[Any]:
        """获取道路损毁数据"""
        sql = """
        SELECT av.attribute_value_id, av.entity_id, av.attribute_definition_id, 
               av.attribute_name, av.attribute_value 
        FROM attribute_value av
        JOIN entity e ON av.entity_id = e.entity_id
        JOIN attribute_definition ad ON av.attribute_definition_id = ad.attribute_definition_id
        JOIN attribute_code ac ON ad.attribute_code_id = ac.attribute_code_id
        WHERE e.scenario_id = :scenario_id
        AND (
            ac.attribute_code_name = 'RoadDamageCondition' 
            OR 
            (ac.attribute_code_name = 'FacilityDamageStatus' AND e.entity_parent_id IS NOT NULL)
        )
        """
        return self.session.execute(text(sql), {"scenario_id": self.scenario_id}).all()

    def get_road_position(self) -> Tuple:
        # 查询满足条件的第一个实体
        first_entity = self.session.query(Entity) \
            .join(EntityType, Entity.entity_type_id == EntityType.entity_type_id) \
            .filter(
            Entity.scenario_id == self.scenario_id,
            EntityType.entity_type_code == 'Road'
        ) \
            .order_by(Entity.entity_id) \
            .first()

        if first_entity is None:
            # 如果没有满足条件的实体，返回空元组
            return tuple()

        # 查询第一个实体的属性值
        results = self.session.query(AttributeValue.attribute_value) \
            .join(AttributeDefinition,
                  AttributeValue.attribute_definition_id == AttributeDefinition.attribute_definition_id) \
            .join(AttributeCode, AttributeDefinition.attribute_code_id == AttributeCode.attribute_code_id) \
            .filter(
            AttributeValue.entity_id == first_entity.entity_id,
            AttributeCode.attribute_code_name.in_(['RoadName','SegmentStartStakeNumber', 'SegmentEndStakeNumber'])
        ).all()

        # 把查询结果打包成一个扁平的元组
        result_tuple = tuple(item[0] for item in results)
        return result_tuple

    def get_resource_positions(self,plan_name) -> List:
        # 查询所有满足条件的实体,父实体为None
        if not plan_name:
            entities = self.session.query(Entity) \
                .join(EntityType, Entity.entity_type_id == EntityType.entity_type_id) \
                .filter(
                Entity.scenario_id == self.scenario_id,
                EntityType.entity_type_code == 'ResponseResource',
                Entity.entity_parent_id.is_(None)
            ) \
                .all()
        else:
            # 根据plan_name找到plan的entity_id
            plan_id = self.session.query(Entity.entity_id) \
                .filter(
                Entity.entity_name == plan_name,
                Entity.scenario_id == self.scenario_id
            ).scalar()
            entities = self.session.query(Entity) \
                .join(EntityType, Entity.entity_type_id == EntityType.entity_type_id) \
                .filter(
                Entity.scenario_id == self.scenario_id,
                EntityType.entity_type_code == 'ResponseResource',
                Entity.entity_parent_id == plan_id
            ) \
                .all()

        # 逐个查询实体的属性值
        results = []
        for entity in entities:
            result = self.session.query(AttributeValue.attribute_value) \
                .join(AttributeDefinition,
                      AttributeValue.attribute_definition_id == AttributeDefinition.attribute_definition_id) \
                .join(AttributeCode, AttributeDefinition.attribute_code_id == AttributeCode.attribute_code_id) \
                .filter(
                AttributeValue.entity_id == entity.entity_id,
                AttributeCode.attribute_code_name == 'Location'
            ).all()

            # 把查询结果打包成一个扁平的元组
            result = [item[0] for item in result][0]
            results.append(result)

        return results

    def get_casualties(self) -> List[Any]:
        """获取人员伤亡数据"""
        sql = """
        SELECT av.attribute_value_id, av.entity_id, av.attribute_definition_id, 
               av.attribute_name, av.attribute_value 
        FROM attribute_value av
        JOIN entity e ON av.entity_id = e.entity_id
        JOIN entity_type et ON e.entity_type_id = et.entity_type_id
        JOIN attribute_definition ad ON av.attribute_definition_id = ad.attribute_definition_id
        JOIN attribute_code ac ON ad.attribute_code_id = ac.attribute_code_id
        WHERE e.scenario_id = :scenario_id
        AND et.entity_type_code = 'People'
        AND ac.attribute_code_name = 'CasualtyCondition'
        """
        return self.session.execute(text(sql), {"scenario_id": self.scenario_id}).all()

    def get_emergency_period(self) -> List[Any]:
        """获取应急时长数据"""
        sql = """
        SELECT av.attribute_value_id, av.entity_id, av.attribute_definition_id, 
               av.attribute_name, av.attribute_value 
        FROM attribute_value av
        JOIN entity e ON av.entity_id = e.entity_id
        JOIN entity_type et ON e.entity_type_id = et.entity_type_id
        JOIN attribute_definition ad ON av.attribute_definition_id = ad.attribute_definition_id
        JOIN attribute_code ac ON ad.attribute_code_id = ac.attribute_code_id
        WHERE e.scenario_id = :scenario_id
        AND et.entity_type_code = 'Vehicle'
        AND ac.attribute_code_name = 'EmergencyPeriod'
        """
        return self.session.execute(text(sql), {"scenario_id": self.scenario_id}).all()

    def get_resource_usage(self, plan_name: Optional[str] = None) -> Dict[str, Any]:
        """获取资源使用情况"""
        if plan_name:
            # 先获取plan_id
            plan_sql = """
            SELECT entity_id FROM entity
            WHERE entity_name = :plan_name
            AND scenario_id = :scenario_id
            """
            plan_id = self.session.execute(text(plan_sql),
                                           {"plan_name": plan_name,
                                            "scenario_id": self.scenario_id}).scalar()

            if not plan_id:
                return {}

            sql = """
            SELECT av.*, ac.attribute_code_name FROM attribute_value av
            JOIN entity e ON av.entity_id = e.entity_id
            JOIN attribute_definition ad ON av.attribute_definition_id = ad.attribute_definition_id
            JOIN attribute_code ac ON ad.attribute_code_id = ac.attribute_code_id
            WHERE e.entity_parent_id = :plan_id
            AND e.scenario_id = :scenario_id
            AND ac.attribute_code_name IN ('AidResource', 'TowResource', 
                                         'FirefightingResource', 'RescueResource')
            """
            results = self.session.execute(text(sql),
                                           {"plan_id": plan_id,
                                            "scenario_id": self.scenario_id}).all()
        else:
            sql = """
            SELECT av.*, ac.attribute_code_name FROM attribute_value av
            JOIN entity e ON av.entity_id = e.entity_id
            JOIN attribute_definition ad ON av.attribute_definition_id = ad.attribute_definition_id
            JOIN attribute_code ac ON ad.attribute_code_id = ac.attribute_code_id
            WHERE e.entity_parent_id IS NULL
            AND e.scenario_id = :scenario_id
            AND ac.attribute_code_name IN ('AidResource', 'TowResource', 
                                         'FirefightingResource', 'RescueResource')
            """
            results = self.session.execute(text(sql), {"scenario_id": self.scenario_id}).all()

        return {result.attribute_code_name: result[0] for result in results}

    def get_related_resource(self, plan_name: Optional[str] = None) -> Dict[str, Any]:
        """获取处置时长数据"""

        if plan_name:
            plan_sql = """
            SELECT entity_id FROM entity
            WHERE entity_name = :plan_name
            AND scenario_id = :scenario_id
            """
            plan_id = self.session.execute(text(plan_sql),
                                           {"plan_name": plan_name,
                                            "scenario_id": self.scenario_id}).scalar()

            if not plan_id:
                return {}

            action_sql = """
            SELECT e.entity_id FROM entity e
            JOIN entity_type et ON e.entity_type_id = et.entity_type_id
            WHERE e.entity_parent_id = :plan_id
            AND e.scenario_id = :scenario_id
            AND et.entity_type_code = 'ResponseAction'
            """
            action_ids = self.session.execute(text(action_sql),
                                              {"plan_id": plan_id,
                                               "scenario_id": self.scenario_id}).scalars().all()
        else:
            action_sql = """
            SELECT e.entity_id FROM entity e
            JOIN entity_type et ON e.entity_type_id = et.entity_type_id
            WHERE e.entity_parent_id IS NULL
            AND e.scenario_id = :scenario_id
            AND et.entity_type_code = 'ResponseAction'
            """
            action_ids = self.session.execute(text(action_sql),
                                              {"scenario_id": self.scenario_id}).scalars().all()

        if not action_ids:
            return {}

        ids_str = ','.join(str(id) for id in action_ids)
        attribute_sql = f"""
        SELECT av.*, ac.attribute_code_name 
        FROM attribute_value av
        JOIN attribute_definition ad ON av.attribute_definition_id = ad.attribute_definition_id
        JOIN attribute_code ac ON ad.attribute_code_id = ac.attribute_code_id
        WHERE av.entity_id IN ({ids_str})
        AND ac.attribute_code_name IN ('BehaviorType', 'ImplementationCondition', 'Duration')
        """
        results = self.session.execute(text(attribute_sql)).all()

        result_dict = defaultdict(list)
        for result in results:
            result_dict[result.attribute_code_name].append(result.attribute_value)

        return dict(result_dict)

    def get_emergency_type(self) -> int:
        """获取应急类型数据"""
        # 查看有没有vehicle且属于承灾体的entity
        sql = """
        SELECT * FROM entity e
        JOIN entity_category ec ON e.entity_id = ec.entity_id
        WHERE e.scenario_id = :scenario_id
        AND e.entity_type_id = (SELECT entity_type_id FROM entity_type WHERE entity_type_code = 'Vehicle')
        AND ec.category_id = (SELECT category_id FROM category WHERE category_name = 'AffectedElement')
        """
        # 执行查询，看是不是空，如果不是，返回Collision_Acident
        if self.session.execute(text(sql), {"scenario_id": self.scenario_id}).all():
            return 2

        # 查看抛洒与侧翻情况
        results = self.session.query(AttributeValue.attribute_value) \
            .join(Entity, AttributeValue.entity_id == Entity.entity_id) \
            .join(EntityType, Entity.entity_type_id == EntityType.entity_type_id) \
            .join(AttributeDefinition,
                  AttributeValue.attribute_definition_id == AttributeDefinition.attribute_definition_id) \
            .join(AttributeCode, AttributeDefinition.attribute_code_id == AttributeCode.attribute_code_id) \
            .filter(
            Entity.scenario_id == self.scenario_id,
            EntityType.entity_type_code == 'Vehicle',
            AttributeCode.attribute_code_name.in_(['SpillCondition', 'RollOverCondition'])
        ).all()

        # 检查返回的每个 attribute_value
        for (value,) in results:
            # 根据数据类型做判断，可根据实际情况调整
            if value in (1, True) or str(value).lower() in ('1', 'true'):
                return 0

        return 1


    def get_all_plan_ids(self) -> List[str]:
        """获取所有计划名称"""
        sql = """
        SELECT entity_id FROM entity
        WHERE entity_type_id = (SELECT entity_type_id FROM entity_type WHERE entity_type_code = 'ResponsePlan')
        AND scenario_id = :scenario_id
        """
        return [result[0] for result in self.session.execute(text(sql), {"scenario_id": self.scenario_id}).all()]

    def collect_all_data(self, plan_name: Optional[str] = None) -> Dict[str, Any]:
        """
        收集所有数据

        Args:
            plan_name: 可选的计划名称。若指定，获取该计划的资源使用和处置时长数据；
                      若不指定，获取parent_id为空的资源使用和处置时长数据

        Returns:
            包含所有收集数据的字典
        """
        data = {
            'road_passibility': self.get_road_passibility(),
            'road_damage': self.get_road_damage(),
            'casualties': self.get_casualties(),
            'related_resource': self.get_related_resource(plan_name),
            'emergency_period': self.get_emergency_period(),
            'emergency_type': self.get_emergency_type(),
            'road_position':self.get_road_position(),
            'resource_positions': self.get_resource_positions(plan_name)
        }
        print(f"data: {data}")

        return data


def get_coordinates_from_stake(road_name, stake_number, api_key):
    """
    根据道路名称和桩号查询经纬度。

    :param road_name: 道路名称，如 "山西省朔州市某高速公路"
    :param stake_number: 桩号，例如 "1"
    :param api_key: 你的高德地图 API Key
    :return: 如果查询成功返回 (经度, 纬度) 的元组，否则返回 None
    """
    # 构造查询地址，例如 "山西省朔州市某高速公路 桩号 1"
    address = f"{road_name} 桩号 {stake_number}"
    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {
        'address': address,
        'key': api_key
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # 检查请求是否成功
        data = response.json()
        if data.get('status') == '1' and data.get('geocodes'):
            # 取第一个匹配结果
            location = data['geocodes'][0]['location']  # 格式 "经度,纬度"
            lon, lat = location.split(',')
            return lon, lat
        else:
            print("查询失败，返回数据:", data)
            return None
    except Exception as e:
        print("请求异常:", e)
        return None


def get_driving_distance(origin, destination, api_key):
    """
    根据起点和终点坐标调用高德驾车路径规划 API 获取行驶距离。

    :param origin: 起点坐标元组 (经度, 纬度)，例如 (112.4328, 39.338005)
    :param destination: 终点坐标元组 (经度, 纬度)
    :param api_key: 高德地图 API Key
    :return: 行驶距离（单位：米），如果查询失败返回 None
    """
    url = "https://restapi.amap.com/v3/direction/driving"
    origin_str = f"{origin[0]},{origin[1]}"
    destination_str = f"{destination[0]},{destination[1]}"
    params = {
        "origin": origin_str,
        "destination": destination_str,
        "key": api_key,
        # 可以设置 extensions 参数为 "all" 以获得更详细的路径信息
        "extensions": "base"
    }

    response = requests.get(url, params=params)
    data = response.json()
    if data.get("status") == "1" and data.get("route"):
        paths = data["route"].get("paths", [])
        if paths:
            first_path = paths[0]
            distance = first_path.get("distance")  # 单位为米，返回的是字符串
            return int(distance) if distance else None
    return None

def get_driving_time(origin, destination, api_key):
    """
    根据起点和终点坐标调用高德驾车路径规划 API 获取行驶时间。

    :param origin: 起点坐标元组 (经度, 纬度)，例如 (112.4328, 39.338005)
    :param destination: 终点坐标元组 (经度, 纬度)
    :param api_key: 高德地图 API Key
    :return: 行驶时间（单位：s），如果查询失败返回 None
    """
    url = "https://restapi.amap.com/v3/direction/driving"
    origin_str = f"{origin[0]},{origin[1]}"
    destination_str = f"{destination[0]},{destination[1]}"
    params = {
        "origin": origin_str,
        "destination": destination_str,
        "key": api_key,
        # 可以设置 extensions 参数为 "all" 以获得更详细的路径信息
        "extensions": "base"
    }

    response = requests.get(url, params=params)
    data = response.json()
    if data.get("status") != "1":
        print("请求失败，返回数据:", data)

    if data.get("status") == "1" and data.get("route"):
        paths = data["route"].get("paths", [])
        if paths:
            first_path = paths[0]
            duration = first_path.get("duration")  # 单位为秒
            if duration:
                print(f"duration: {duration}")
            else:
                print("duration is None")
                print("data: ", data)
            return int(duration) if duration else None
    return None

def get_coordinates_from_stake_by_file(stake_number):
    try:
        # 设置 Excel 文件路径
        excel_path = os.path.join(os.path.dirname(__file__), '../data/required_information/01_上海路网_申字型_中环路桩号数据及关联关系(1).xlsx')

        # 读取 Excel 文件中的数据，指定需要的列（桩号、经度、纬度）
        df = pd.read_excel(excel_path, header=0)
        print(df.head())

        # 查找给定桩号的行
        stake_data = df[df['桩号名称'] == stake_number]

        if not stake_data.empty:
            # 提取经纬度
            longitude = stake_data['经度'].values[0]
            latitude = stake_data['维度'].values[0]
            print(f"桩号 {stake_number} 对应的经纬度为 ({longitude}, {latitude})")
            return (longitude, latitude)
        else:
            print(f"未找到桩号 {stake_number} 的数据")
            return None
    except Exception as e:
        print(f"请求异常: {e}")
        return None



def convert_to_evidence(data):
    print(f"3525data: {data}")

    evidence = dict()
    resource_nodes = ["AidResource", "TowResource", "FirefightingResource", "RescueResource"]
    for node in resource_nodes:
        evidence[node] = 0  # 默认未使用
    # 处理 road_passibility
    road_passibility_data = data.get('road_passibility', [])
    if road_passibility_data:
        print(f"153315{road_passibility_data}")
        # 检查是否有任何一条记录的 ClosureCondition 为不通行状态
        impassable_values = {'1', 'true'}
        # 任何一条记录为不通行，整体就判定为不通行
        is_impassable = any(str(record[4]).strip().lower() in impassable_values for record in road_passibility_data)
        evidence['roadPassibility'] = 0 if is_impassable else 1

    # 处理 road_damage
    road_damage_data = data.get('road_damage', [])
    if road_damage_data:
        # 有任意一条记录表示损坏，就认为是损坏状态
        damage_values = {'1', 'true'}
        is_damaged = any(str(record[4]).strip().lower() in damage_values for record in road_damage_data)
        evidence['roadLoss'] = 1 if is_damaged else 0

    # 处理 casualties
    casualties_data = data.get('casualties', [])
    if casualties_data:
        # 假设 'True' 表示有 Casualties，'False' 或其他表示无
        casualty_condition = str(casualties_data[0][-1]).lower()
        if casualty_condition in ('1', 'true'):
            evidence['casualties'] = 1
        else:
            evidence['casualties'] = 0

    # 处理 emergency_period
    emergency_period_data = data.get('emergency_period', [])
    emergency_period_map_dict = {
        '凌晨': 'Earlymorning',
        '上午': 'Morning',
        '下午': 'Afternoon',
        '晚上': 'Evening',
        'Earlymorning': 'Earlymorning',
        'Morning': 'Morning',
        'Afternoon': 'Afternoon',
        'Evening': 'Evening'
    }
    if emergency_period_data:
        # 凌晨 上午 下午 晚上	0/1/2/3
        emergency_period = emergency_period_data[0][-1]
        emergency_period_map = emergency_period_map_dict.get(emergency_period, 'Unknown')
        if emergency_period == '凌晨' or emergency_period_map == 'Earlymorning':
            evidence['emergencyPeriod'] = 0
        elif emergency_period == '上午' or emergency_period_map == 'Morning':
            evidence['emergencyPeriod'] = 1
        elif emergency_period == '下午' or emergency_period_map == 'Afternoon':
            evidence['emergencyPeriod'] = 2
        elif emergency_period == '晚上' or emergency_period_map == 'Evening':
            evidence['emergencyPeriod'] = 3

    # 处理 emergency_type
    evidence['emergencyType'] = data.get('emergency_type', 0)

    # 处理 related_resource
    related_resource = data.get('related_resource', {})
    behavior_types = related_resource.get('BehaviorType', [])
    implementation_conditions = related_resource.get('ImplementationCondition', [])
    durations = related_resource.get('Duration', [])

    # 定义 BehaviorType 到资源字段的映射
    behavior_to_resource = {
        '抢修': 'RescueResource',
        '牵引': 'TowResource',
        '救助': 'AidResource',
        '消防': 'FirefightingResource'

    }

    for i in range(len(behavior_types)):
        behavior = behavior_types[i]
        impl_condition = implementation_conditions[i] if i < len(implementation_conditions) else None
        duration = durations[i] if i < len(durations) else None

        if behavior is None:
            continue  # 跳过没有行为类型的项

        resource_key = behavior_to_resource.get(behavior)
        if resource_key:
            # 检查 ImplementationCondition 是否为 '1' 或 'true'（不区分大小写）
            if isinstance(impl_condition, str):
                impl_condition_clean = impl_condition.strip().lower()
                is_active = impl_condition_clean in ['1', 'true']
            else:
                is_active = bool(int(impl_condition)) if impl_condition is not None else False

            if is_active:
                evidence[resource_key] = 1  # 设置为 1
            # 如果已经为 1，不需要改变'


    # 处理 Duration 列表中的每一项并求和
    # 定义 Duration 字符串到数值的映射
    duration_mapping = {
        '0-15min': 0,
        '15-30min': 1,
        '30-60min': 2,
        '60min+': 3
    }

    total_duration_value = 0
    # for duration in durations:
    #     if duration is not None:
    #         total_duration_value += int(duration)
    for duration in durations:
        if duration is not None:
            total_duration_value = max(total_duration_value, int(duration))

    # 根据总和转换为 disposalDuration
    if total_duration_value <= 15:
        disposal_duration = 0
    elif total_duration_value <= 30:
        disposal_duration = 1
    elif total_duration_value <= 60:
        disposal_duration = 2
    else:
        disposal_duration = 3

    evidence['disposalDuration'] = disposal_duration

    # 处理 road_position和resource_positions
    road_position = data.get('road_position', [])
    resource_positions = data.get('resource_positions', [])
    if road_position and resource_positions:
        road_name, start_stake, end_stake = road_position
        print("道路名称:", road_name)
        print("起点桩号:", start_stake)
        print("终点桩号:", end_stake)

        config_path = os.path.join(os.path.dirname(__file__), '../config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        api_key = config.get('gaode-map')['web_service_key']
        emergency_speed = config.get('emergency_speed', 60)
        # 分别获取起点和终点桩号的经纬度
        # start_coordinates = get_coordinates_from_stake(road_name, start_stake, api_key)
        # end_coordinates = get_coordinates_from_stake(road_name, end_stake, api_key)
        start_coordinates = get_coordinates_from_stake_by_file(start_stake)
        end_coordinates = get_coordinates_from_stake_by_file(end_stake)

        if start_coordinates and end_coordinates:
            # 转换成 float 类型进行计算
            start_lon, start_lat = map(float, start_coordinates)
            end_lon, end_lat = map(float, end_coordinates)

            # 计算平均经纬度
            avg_lon = (start_lon + end_lon) / 2
            avg_lat = (start_lat + end_lat) / 2

            print("起点坐标:", start_coordinates)
            print("终点坐标:", end_coordinates)
            print("平均坐标:", (avg_lon, avg_lat))
        else:
            print("无法获取桩号对应的坐标")
            CustomWarningDialog("警告","无法获取桩号对应的坐标").exec_()
            return evidence

        pattern = r'(.+?)\s*\(\s*([-+]?\d+\.\d+)\s*,\s*([-+]?\d+\.\d+)\s*\)'

        # 遍历 resource_positions 列表，使用正则表达式提取地址和经纬度
        distance = 0
        time = 0
        for resource in resource_positions:
            match = re.search(pattern, resource)
            if match:
                # 提取捕获的各组内容，并去除两端空白字符
                address = match.group(1).strip()
                latitude = match.group(2)
                longitude = match.group(3)
                print("地址:", address)
                print("纬度:", latitude)
                print("经度:", longitude)

                # 计算距离
                #distance += get_driving_distance((avg_lon, avg_lat), (float(longitude), float(latitude)), api_key)
                each_time = get_driving_time((avg_lon, avg_lat), (float(longitude), float(latitude)), api_key)
                time = max(each_time,time)
                # 延迟1000毫秒(1秒)
                QThread.msleep(1000)
                QCoreApplication.processEvents()

        #if distance != 0:
            #print("总行驶距离:", distance)
            # time = distance / (emergency_speed * 1000 / 60)
        if time != 0:
            # 秒转分钟
            time = time / 60
            print("预计行驶时间(min):", time)
            # 根据距离判断
            if time <= 15:
                evidence['responseDuration'] = 0
            elif time <= 30:
                evidence['responseDuration'] = 1
            elif time <= 60:
                evidence['responseDuration'] = 2
            else:
                evidence['responseDuration'] = 3

    print(f"3214evidence: {evidence}")




    return evidence

# connection_string = f"mysql+mysqlconnector://Tsing_loong:12345678@localhost:3306/test2?charset=utf8mb4"
# engine = create_engine(connection_string, echo=True)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# session = SessionLocal()
# # 使用示例:
#
# # 创建会话和收集器实例
# collector = PlanDataCollector(session, scenario_id=3)
#
# # 收集数据
# plan_data = collector.collect_all_data(plan_name=None)
#
# # 转换为贝叶斯网络证据
# evidence = convert_to_evidence(plan_data)


# print(evidence)

class PlanData:
    def __init__(self, session, scenario_id, neg_id_gen):
        self.session = session
        self.scenario_id = scenario_id
        self.neg_id_gen = neg_id_gen

    def create_entities_with_negative_ids(self, template_name: str, name: str) -> Dict[int, Any]:
        """
        1. 根据 template_name 查找 Template;
        2. 为每个 Template 构造一个“复制品” JSON 对象(负数ID)，结构与 get_scenario_data 输出保持一致：
           {
             entity_id, entity_name, entity_type_id, ...
             categories: [...],
             attributes: [...],
             behaviors: [...]
           }
           其中 attributes/behaviors 字段，与 get_scenario_data 中的 attribute_value / behavior_value 保持同样的键。
        3. 返回形如: { -1: { ... entityJson ... }, -2: { ... }, ... }
        """
        session: Session = self.session
        neg_id_gen = self.neg_id_gen

        # 先查数据库 Template
        tpl_list: List[Template] = session.query(Template).filter(Template.template_name == template_name).all()
        if not tpl_list:
            print(f"[WARN] 未找到名为 {template_name} 的 template，返回空字典。")
            return {}

        # 用于返回的结果
        replicated_data: Dict[int, Any] = {}

        for tpl in tpl_list:
            # 解析 template_restrict
            if isinstance(tpl.template_restrict, dict):
                restrict_dict = tpl.template_restrict
            else:
                restrict_dict = json.loads(tpl.template_restrict)

            # 取 create 下的 category_type
            create_part = restrict_dict.get("create", {})
            cat_names = create_part.get("category_type", [])
            if isinstance(cat_names, str):
                cat_names = [cat_names]

            # 准备 entity 负数ID
            e_id = neg_id_gen.next_id()

            # entity 的基础字段：与 get_scenario_data 对应
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entity_json = {
                "entity_id": e_id,
                "entity_name": name,
                "entity_type_id": tpl.entity_type_id,
                "entity_parent_id": None,
                "scenario_id": self.scenario_id,  # 你上下文里的场景ID
                "create_time": now_str,
                "update_time": now_str,
                "categories": [],
                "attributes": [],
                "behaviors": []
            }

            # ========== 处理 Categories ==========

            for cname in cat_names:
                cat_obj = session.query(Category).filter_by(category_name=cname).first()
                if cat_obj:
                    entity_json["categories"].append({
                        "category_id": cat_obj.category_id,
                        "category_name": cat_obj.category_name,
                        "description": cat_obj.description
                    })
                else:
                    # 如果数据库不存在该分类，可先用一个占位
                    entity_json["categories"].append({
                        "category_id": 0,
                        "category_name": cname,
                        "description": None
                    })

            # ========== 处理 Attributes ==========
            # template <-> attribute_definitions 多对多
            # 这里产生类似 get_scenario_data 中 attribute_values 的结构
            for attr_def in tpl.attribute_definitions:
                # 给 attribute_value_id 也分配一个负数ID
                av_id = neg_id_gen.next_id()

                # 当我们在 get_scenario_data 中：
                # final_attr_name = av.attribute_name or attr_def.attribute_code.attribute_code_name
                # 这里没有 av.attribute_name(因为是新建), 你可以将其设为 None 或直接用 code_name
                fallback_attr_name = attr_def.attribute_code.attribute_code_name

                attribute_item = {
                    "attribute_value_id": av_id,
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

                    # 我们要类似 get_scenario_data 里: av.attribute_value
                    # 目前还没存任何值 => 可以先初始化为 default_value or None
                    "attribute_value": attr_def.default_value if attr_def.default_value is not None else None,

                    # attribute_name => 在 get_scenario_data 里是 av.attribute_name or code
                    # 这里没有 av.attribute_name, 我们就设为空或直接用 fallback
                    "attribute_name": fallback_attr_name,

                    # referenced_entities => []
                    "referenced_entities": []
                }
                # 如果是人类承灾要素，需要修改属性值
                if template_name == "人类承灾要素":
                    if attribute_item['attribute_code_name'] == 'CasualtyCondition':
                        attribute_item['attribute_value'] = '1'
                entity_json["attributes"].append(attribute_item)

            # ========== 处理 Behaviors ==========
            # template <-> behavior_definitions 多对多
            for bh_def in tpl.behavior_definitions:
                # behavior_value_id => 负数
                bv_id = neg_id_gen.next_id()

                # get_scenario_data 中：
                # final_behavior_name = bv.behavior_name or fallback_code_name
                # 这里“bv.behavior_name”尚不存在(新建), 所以我们可以先赋值 None
                # fallback_code_name = bh_def.behavior_code_ref.behavior_code_name (若 behavior_code_ref 存在)
                code_ref = bh_def.behavior_code_ref
                fallback_code_name = code_ref.behavior_code_name if code_ref else "UnknownBehaviorCode"

                # 你也可以先令 final_behavior_name = None => 让后面回写
                # 或者默认就用 bh_def.china_default_name
                final_behavior_name = None

                behavior_item = {
                    "behavior_value_id": bv_id,
                    "behavior_definition_id": bh_def.behavior_definition_id,

                    "china_default_name": bh_def.china_default_name,
                    "english_default_name": bh_def.english_default_name,

                    "behavior_name": final_behavior_name,  # 先置空; 若需要可用 bh_def.china_default_name
                    "behavior_code_name": fallback_code_name,  # 供 fallback

                    "object_entity_type_id": bh_def.object_entity_type_id,
                    "is_required": bool(bh_def.is_required),
                    "is_multi_valued": bool(bh_def.is_multi_valued),
                    "description": bh_def.description,
                    "create_time": now_str,
                    "update_time": now_str,

                    # object_entities => []
                    "object_entities": []
                }
                entity_json["behaviors"].append(behavior_item)

            # 把本次生成的“复制品”放进返回 dict
            replicated_data[e_id] = entity_json
            print(f"[DEBUG] 生成负数ID实体: {entity_json}")

        return replicated_data


    def _set_attribute_value(self, entity_json: Dict[str, Any], attr_code_name: str, value: Any):
        """
        小工具函数：在 entity_json["attributes"] 中找到 attribute_code_name == attr_code_name，
        然后把 attribute_value 设置为 value.
        """
        for attr in entity_json.get("attributes", []):
            # 注意，这里判断 attr["attribute_code_name"] 是否等于我们要找的 code
            if attr.get("attribute_code_name") == attr_code_name:
                attr["attribute_value"] = value
                break

    def _set_behavior_value(self, entity_json: Dict[str, Any], behavior_code_name: str, name: Optional[str] = None):
        """
        如果 entity_json["behaviors"] 中包含 behavior_code_name 对应的 behavior，可以为其设置一个自定义名称等。
        也可以在 behaviors 里新增 object_entities 引用等。演示用，不一定需要。
        """
        for b in entity_json.get("behaviors", []):
            if b.get("behavior_code_name") == behavior_code_name:
                if name is not None:
                    b["behavior_name"] = name
                break

    def _append_reference(self, entity_json: Dict[str, Any], attr_code_name: str, ref_eid: int):
        """
        小工具函数：在 entity_json["attributes"] 中找到 attr_code_name 对应的一项，
        将 ref_eid 放到 "referenced_entities" 数组里。
        适用于 is_reference=True / is_multi_valued=True 这种属性.
        """
        for attr in entity_json.get("attributes", []):
            if attr.get("attribute_code_name") == attr_code_name:
                # 说明这个属性是一个 reference，可能是多值
                attr["referenced_entities"].append(ref_eid)
                break

    def build_plan_structure(self, plan_input: Dict[str, Any]) -> Dict[int, Any]:
        """
        根据前端给定的 JSON (plan_input)，递归创建应急预案及其下属的 应急行为/应急资源等，返回一个
        { -1: { ...planEntity...}, -2: {...actionEntity...}, -3: {...resource...}, ... } 的大字典.

        plan_input 大致结构：
        {
          "plan_name": "...",
          "emergency_actions": [
            {
              "action_type": "...",
              "duration": "...",
              "implementation_status": "...",
              "resources": [
                { "resource_type": "...", "quantity": 1, ... },
                ...
              ]
            },
            ...
          ],
          "simulation_results": {...}   # 如果有，需要存就处理
        }
        """

        # 1) 创建一个“应急预案”实体
        print(f"[DEBUG] 开始创建应急预案: {plan_input}")
        plan_name_str = plan_input.get("plan_name", "未命名预案")
        plan_entities = self.create_entities_with_negative_ids("应急预案", name=plan_name_str)
        # 假设“应急预案”模板只会返回 1~N 个 entity，通常只有1个
        # 拿到第一个 key
        if not plan_entities:
            # 理论上这里不会发生，除非 DB 里找不到该 template
            return {}

        plan_eid = next(iter(plan_entities.keys()))  # 例如 -1
        plan_json = plan_entities[plan_eid]

        # 2) 在预案实体的 attributes 里，设置 "PlanName" = plan_name_str
        self._set_attribute_value(plan_json, "PlanName", plan_name_str)

        # 如果你还有其他需要存的，比如 simulation_results
        # 目前 DB 没有 "SimulationResults" 这类 attribute_code，
        # 你可以先扩展 attribute_definition 或者这里先跳过
        # 这里仅演示，假如要存成一个 JSON 字符串，放进 "description" (如果 DB 有这个字段)
        # 也可以 `_set_attribute_value(plan_json, "SomeCode", json.dumps(plan_input["simulation_results"]))`
        # 先示例存在 plan_json["description"]:
        # （注意：在真实 get_scenario_data 中 description 可能是 entity 自身字段，不是 attribute）
        plan_json["description"] = json.dumps(plan_input.get("simulation_results", {}), ensure_ascii=False)

        # 3) 处理 actions
        emergency_actions = plan_input.get("emergency_actions", [])

        for action_obj in emergency_actions:
            # 3.1 创建一个“应急行为要素”实体
            action_name = action_obj.get("action_type", "未知行为")
            action_entities = self.create_entities_with_negative_ids("应急行为要素", name=action_name)

            if not action_entities:
                continue
            # 同理，这里假设只会创建1个
            act_eid = next(iter(action_entities.keys()))
            act_json = action_entities[act_eid]

            # 3.2 设置行为自身的属性: BehaviorType, Duration, ImplementationCondition ...
            # 先举例 BehaviorType
            # behavior_type是action_type的 - 后的字符
            behavior_type = action_obj.get("action_type", "未知行为")
            behavior_type = behavior_type.split('-')[-1].strip()
            self._set_attribute_value(act_json, "BehaviorType", behavior_type)
            self._set_attribute_value(act_json, "Duration",       action_obj.get("duration"))
            self._set_attribute_value(act_json, "ImplementationCondition", action_obj.get("implementation_status"))

            # 3.3 把该 action 挂到预案的 "HasAction" 引用属性里 (如果 template_attribute_definition 映射是如此)
            self._append_reference(plan_json, "HasAction", act_eid)

            # 3.4 处理 resources
            resources = action_obj.get("resources", [])
            for res_obj in resources:
                # 创建“应急资源要素”
                res_name = res_obj.get("resource_type", "未知资源")
                resource_entities = self.create_entities_with_negative_ids("应急资源要素", name=res_name)
                if not resource_entities:
                    continue

                res_eid = next(iter(resource_entities.keys()))
                res_json = resource_entities[res_eid]

                # 设置资源属性: ResourceType, ResourceQuantityOrQuality ...
                self._set_attribute_value(res_json, "ResourceType", res_obj.get("resource_category"))
                self._set_attribute_value(res_json, "ResourceQuantityOrQuality", res_obj.get("quantity"))
                self._set_attribute_value(res_json, "Location", res_obj.get("location"))
                # 设置关联属性: AssociatedBehavior
                self._append_reference(res_json, "AssociatedBehavior", act_eid)


                res_json["description"] = f"分类: {res_obj.get('resource_category')} / 位置: {res_obj.get('location')}"


                self._append_reference(plan_json, "HasResource", res_eid)

                # 把 resource_entities 合并进整体字典
                plan_entities.update(resource_entities)

            # 把 action_entities 合并进整体字典
            plan_entities.update(action_entities)

        print(f"[DEBUG] 创建完毕，返回所有实体: {plan_entities}")
        # 最终返回包含 预案 + 所有子实体 的一个大 dict
        self.post_process_entities(plan_entities)
        return plan_entities

    def post_process_entities(self, plan_entities: Dict[int, Dict]) -> None:
        """
        对已生成的负数ID实体做二次修饰，满足以下需求：
          1) 行为的 Duration 只保留数字部分
          2) 资源的 description 只保留位置
          3) 行为/资源 的 entity_parent_id = 预案ID (假定预案ID 就是最先的 key, 或者自己找 "应急预案")
          4) 资源的 AssociatedBehavior => 指向对应行为ID; 如果资源类型=人员，则加到行为的 ImplementingPersonnel; 如果=车辆，则加到 EmergencyVehicles
        """
        # -- (A) 找到预案ID (假设只有一个预案，且key是 -1)
        #    如果实际情况更复杂，可通过 entity_type_id==13 来确定预案实体是谁
        plan_id = None
        for eid, ent in plan_entities.items():
            if ent.get("entity_type_id") == 13:  # 13 => 应急预案
                plan_id = eid
                break

        if plan_id is None:
            print("[WARN] 未找到应急预案实体，跳过后处理")
            return

        plan_json = plan_entities[plan_id]

        # -- (B) 收集所有应急行为、应急资源的 ID
        behavior_ids = []
        resource_ids = []

        for eid, ent in plan_entities.items():
            if eid == plan_id:
                continue  # 跳过预案本身
            etype = ent.get("entity_type_id")
            # 5 => "ResponseAction" (应急行为)
            # 4 => "ResponseResource" (应急资源)
            if etype == 5:  # 应急行为
                behavior_ids.append(eid)
            elif etype == 4:  # 应急资源
                resource_ids.append(eid)

        # -- (C) 给这些行为 / 资源都设置 parent_id = plan_id
        for bid in behavior_ids:
            plan_entities[bid]["entity_parent_id"] = plan_id
        for rid in resource_ids:
            plan_entities[rid]["entity_parent_id"] = plan_id

        # -- (D) 去掉 Duration 里的 " minutes"
        for bid in behavior_ids:
            beh = plan_entities[bid]
            # 找到 attributes 里的 "Duration"
            for attr in beh.get("attributes", []):
                if attr.get("attribute_code_name") == "Duration":
                    val = attr.get("attribute_value")
                    if isinstance(val, str) and "minutes" in val:
                        # 例如 "1 minutes" -> "1"
                        attr["attribute_value"] = val.replace(" minutes", "")
                    # 也可以考虑 val.replace(" ", "") if 只想保留数字
                    # 或者干脆解析成数字 int(val.split()[0]) => 1

        # -- (E) 对资源的 description 只保留 "location"
        #    假设原先 description="分类: 类型A / 位置: 435"
        #    我们要只保留 "435"
        for rid in resource_ids:
            res = plan_entities[rid]
            desc = res.get("description", "")
            # 如果你能统一保证是类似"分类: XXX / 位置: YYY"的格式，可以做字符串解析
            # 简单粗暴一点：只保留最后一部分 => "435"
            # 例如:
            if "位置:" in desc:
                # 取 "位置:" 后面的部分
                location_str = desc.split("位置:")[-1].strip()
                # 如果还包含 '/' 或别的符号可以再进一步 .split('/')
                res["description"] = location_str
            # 如果描述里本身就只有数字，就无需改

        # -- (F) 处理 “AssociatedBehavior” & 资源类型 => 写入行为的 "ImplementingPersonnel"/"EmergencyVehicles"
        #    先做一个小帮助函数来获取 attribute 对象
        def get_attr(ent, code_name: str) -> Optional[Dict]:
            """在 ent["attributes"] 中找到指定 code_name 的那一项"""
            for a in ent.get("attributes", []):
                if a.get("attribute_code_name") == code_name:
                    return a
            return None

        for rid in resource_ids:
            res_ent = plan_entities[rid]
            # 1) 在资源上读取“AssociatedBehavior” => 获取对应的 应急行为ID
            assoc_attr = get_attr(res_ent, "AssociatedBehavior")
            if assoc_attr and "referenced_entities" in assoc_attr and assoc_attr["referenced_entities"]:
                # 假设每个资源只关联一个行为
                action_eid = assoc_attr["referenced_entities"][0]
                if action_eid in behavior_ids:
                    # 2) 根据资源类型，将资源ID添加到对应行为的 ImplementingPersonnel / EmergencyVehicles
                    resource_type = None
                    rtype_attr = get_attr(res_ent, "ResourceType")
                    if rtype_attr:
                        resource_type = rtype_attr.get("attribute_value")

                    if resource_type and isinstance(resource_type, str):
                        beh_ent = plan_entities[action_eid]
                        if "人" in resource_type:  # 例如 "人员"
                            imp_attr = get_attr(beh_ent, "ImplementingPersonnel")
                            if imp_attr:
                                if "referenced_entities" not in imp_attr:
                                    imp_attr["referenced_entities"] = []
                                imp_attr["referenced_entities"].append(rid)
                        elif "车" in resource_type:  # 例如 "车辆"
                            eve_attr = get_attr(beh_ent, "EmergencyVehicles")
                            if eve_attr:
                                if "referenced_entities" not in eve_attr:
                                    eve_attr["referenced_entities"] = []
                                eve_attr["referenced_entities"].append(rid)
            else:
                # 如果资源没有关联行为，您可以选择跳过或进行其他处理
                print(f"[WARN] 资源ID {rid} 没有关联的行为，跳过关联。")

        # 修改就地，无需 return；plan_entities 本身即被改动

    def upsert_posterior_probability(self, plan_name: str, posterior_dict: Dict[str, Dict[str, float]]) -> None:
        """
        根据 posterior_dict 的后验概率数据，以及 plan_name，
        在 posteriori_data 表中做“存在即更新，不存在则插入”。

        posterior_dict 例：
        {
          "ScenarioResilience": {"Good": 0.619..., "Bad": 0.380...},
          "AbsorptionCapacity": {"Good": 0.655..., "Bad": 0.344...},
          ...
        }
        """

        session = self.session

        # 1) 找到对应的“应急预案”实体 (entity_type_id=13)
        plan_entity = session.query(Entity).filter_by(
            entity_name=plan_name,
            entity_type_id=13
        ).first()

        if not plan_entity:
            print(f"[WARN] 未找到名称为 '{plan_name}' 的应急预案实体，无法写 posteriori_data。")
            return

        plan_id = plan_entity.entity_id

        # 2) 遍历 posterior_dict
        for node_name, state_prob_map in posterior_dict.items():
            # 找到对应 bayes_node
            node_obj = session.query(BayesNode).filter_by(bayes_node_name=node_name).first()
            if not node_obj:
                print(f"[WARN] 未在 bayes_node 中找到节点名='{node_name}' 的记录，跳过。")
                continue

            for state_name, probability_value in state_prob_map.items():
                # 找到对应的 bayes_node_state
                state_obj = session.query(BayesNodeState).filter_by(
                    bayes_node_id=node_obj.bayes_node_id,
                    bayes_node_state_name=state_name
                ).first()

                if not state_obj:
                    print(f"[WARN] bayes_node='{node_name}' 下未找到 state='{state_name}'，跳过。")
                    continue

                # 3) 先检查 posteriori_data 是否已有相同记录
                existing_data = session.query(PosterioriData).filter_by(
                    plan_id=plan_id,
                    bayes_node_state_id=state_obj.bayes_node_state_id
                ).first()

                if existing_data:
                    # 已存在 => 更新
                    existing_data.posterior_probability = probability_value
                    existing_data.update_time = datetime.now()
                else:
                    # 不存在 => 新插入
                    new_record = PosterioriData(
                        posterior_probability=probability_value,
                        bayes_node_state_id=state_obj.bayes_node_state_id,
                        plan_id=plan_id
                    )
                    session.add(new_record)

        # 4) 统一提交
        session.commit()
        print("[INFO] posteriori_data 已完成存在即更新、否则插入的操作。")
        updated_plan_info = self.get_plan_by_name(plan_name)
        return updated_plan_info

    def get_plan_by_name(self, plan_name: str) -> Dict[str, Any]:
        """
        新增方法：
        返回指定预案的详细信息，与 get_all_plans() 中对单个预案的结构一致。
        若不存在则返回空字典。
        """
        all_plans = self.get_all_plans()
        return all_plans.get(plan_name, {})


    def get_all_plans(self, change_path = None) -> Dict[str, Any]:
        """
        返回形如:
        {
          "432": {
            "plan_name": "432",
            "emergency_actions": [...],
            "simulation_results": {
              "推演前-较好": "30%",
              "推演前-中等": "0%",
              "推演前-较差": "70%",
              "推演后-较好": "55%",
              "推演后-中等": "0%",
              "推演后-较差": "45%"
            },
            "timestamp": "2025-01-22 21:23:32"
          },
          ...
        }
        """
        session = self.session

        results: Dict[str, Any] = {}

        # 1) 找到所有应急预案实体 (entity_type_id=13 and scenario_id = self.scenario_id)
        plan_entities = session.query(Entity).filter_by(
            entity_type_id=13,
            scenario_id=self.scenario_id
        ).all()

        # 2) 预先取出 “ScenarioResilience” 对应的 bayes_node，用于后续查询
        scenario_resilience_node = session.query(BayesNode).filter_by(bayes_node_name='ScenarioResilience').first()
        # 如果不存在也不致命，可后续跳过

        for plan_ent in plan_entities:
            plan_id = plan_ent.entity_id
            plan_name = plan_ent.entity_name
            plan_create_time = plan_ent.create_time.strftime("%Y-%m-%d %H:%M:%S")

            # ========== (A) 组装 "emergency_actions" ==========

            # 先找该预案下的应急行为 (entity_type_id=5 => "应急行为")
            actions = session.query(Entity).filter_by(
                entity_parent_id=plan_id,
                entity_type_id=5
            ).all()

            action_list = []
            for act in actions:
                action_dict = {
                    "action_type": "",
                    "duration": "0 minutes",               # 缺省值
                    "implementation_status": "False",      # 缺省值
                    "resources": []
                }

                # —— 读取行为属性 (BehaviorType, Duration, ImplementationCondition 等) ——
                attr_values = session.query(AttributeValue).filter_by(entity_id=act.entity_id).all()
                # 把结果放到一个 {attribute_code_name: attribute_value} 的 dict，方便取
                attr_map = { av.attribute_definition.attribute_code.attribute_code_name: av.attribute_value for av in attr_values if av.attribute_definition.attribute_code.attribute_code_name }

                # action_type
                if "BehaviorType" in attr_map and attr_map["BehaviorType"]:
                    action_dict["action_type"] = attr_map["BehaviorType"]

                # duration => 若有值就加上 "minutes"
                if "Duration" in attr_map and attr_map["Duration"]:
                    action_dict["duration"] = f'{attr_map["Duration"]} minutes'

                # implementation_status
                if "ImplementationCondition" in attr_map and attr_map["ImplementationCondition"]:
                    action_dict["implementation_status"] = attr_map["ImplementationCondition"]

                # ========== (A-1) 找到 action 下的资源 (entity_type_id=4 => "应急资源") ==========
                res_subq = (
                    session.query(AttributeValue.entity_id)
                    .join(AttributeDefinition,
                          AttributeValue.attribute_definition_id == AttributeDefinition.attribute_definition_id)
                    .join(AttributeCode, AttributeDefinition.attribute_code_id == AttributeCode.attribute_code_id)
                    .join(AttributeValueReference,
                          AttributeValue.attribute_value_id == AttributeValueReference.attribute_value_id)
                    .filter(AttributeCode.attribute_code_name == "AssociatedBehavior")  # 假定是AssociatedBehavior
                    .filter(AttributeValueReference.referenced_entity_id == act.entity_id)
                    .subquery()
                )

                # 在 entity 表找 resource
                res_entities = (
                    session.query(Entity)
                    .filter(
                        Entity.entity_id.in_(res_subq),
                        Entity.entity_type_id == 4,  # 应急资源
                        Entity.entity_parent_id == plan_id  # 该资源的parent是预案
                    )
                    .all()
                )

                resource_list = []
                for res_ent in res_entities:
                    # 同理，先取资源的所有属性
                    res_attr_values = session.query(AttributeValue).filter_by(entity_id=res_ent.entity_id).all()

                    res_attr_map = {}
                    for rav in res_attr_values:
                        ad = rav.attribute_definition
                        if ad is not None and ad.attribute_code is not None:
                            code_name = ad.attribute_code.attribute_code_name  # 例如 "ResourceType", "ResourceQuantityOrQuality"
                            res_attr_map[code_name] = rav.attribute_value

                    # Demo: 其中 resource_category, location 在示例中没有明确字段，先用示例值
                    # 也可根据实际字段/业务设置
                    resource_item = {
                        "resource_type": res_attr_map.get("ResourceType", "未知资源"),
                        "resource_category": "类型A",  # 示例中写死
                        "quantity": res_attr_map.get("ResourceQuantityOrQuality", 0),
                        "location": res_attr_map.get("Location", "未知位置")
                    }
                    resource_list.append(resource_item)

                action_dict["resources"] = resource_list
                action_list.append(action_dict)

            # ========== (B) 组装 "simulation_results" ==========

            # 假设“推演前-较好/较差”是 ScenarioResilience 在 bayes_node_state 表上记录的 prior 概率
            # “推演后-较好/较差”是 posteriori_data 表中的 posterior_probability
            # 中等暂时置为 0%
            sim_results = {
                "推演前-较好": "0%",
                "推演前-中等": "0%",   # 固定0
                "推演前-较差": "0%",
                "推演后-较好": "0%",
                "推演后-中等": "0%",   # 固定0
                "推演后-较差": "0%"
            }

            if scenario_resilience_node:
                # 取 Good/Bad 两个 state
                good_state = session.query(BayesNodeState).filter_by(
                    bayes_node_id=scenario_resilience_node.bayes_node_id,
                    bayes_node_state_name='Good'
                ).first()

                bad_state = session.query(BayesNodeState).filter_by(
                    bayes_node_id=scenario_resilience_node.bayes_node_id,
                    bayes_node_state_name='Bad'
                ).first()

                # (B-1) 推演前 => 来自 bayes_node_state 自己的 prior 概率
                if good_state:
                    good_prior = good_state.bayes_node_state_prior_probability
                    sim_results["推演前-较好"] = f"{good_prior * 100:.2f}%"

                if bad_state:
                    bad_prior = bad_state.bayes_node_state_prior_probability
                    sim_results["推演前-较差"] = f"{bad_prior * 100:.2f}%"

                # (B-2) 推演后 => 来自 posteriori_data
                #   posteriori_data(plan_id=plan_id, bayes_node_state_id=xx).posterior_probability
                # Good
                if good_state:
                    post_good = session.query(PosterioriData).filter_by(
                        plan_id=plan_id,
                        bayes_node_state_id=good_state.bayes_node_state_id
                    ).first()
                    if post_good:
                        sim_results["推演后-较好"] = f"{post_good.posterior_probability * 100:.2f}%"

                # Bad
                if bad_state:
                    post_bad = session.query(PosterioriData).filter_by(
                        plan_id=plan_id,
                        bayes_node_state_id=bad_state.bayes_node_state_id
                    ).first()
                    if post_bad:
                        sim_results["推演后-较差"] = f"{post_bad.posterior_probability * 100:.2f}%"

            # ========== (C) 最终组装 plan_info ==========
            if change_path:
                # print(f"传入路径：{change_path}")
                # change_path = os.path.abspath(os.path.join(change_path, f"posterior_probabilities.json"))
                print(f"根据以下路径进行调整：{change_path}")
                with open(change_path, 'r') as f:
                    change_dict = json.load(f)
                    # print(f"读取到的数据：{change_dict}")
                    # print(change_dict["ScenarioResilience"]["Good"])
                    # print(change_dict["ScenarioResilience"]["Bad"])
                    good_prior = change_dict["ScenarioResilience"]["Good"]
                    sim_results["推演前-较好"] = f"{good_prior * 100:.2f}%"
                    bad_prior = change_dict["ScenarioResilience"]["Bad"]
                    sim_results["推演前-较差"] = f"{bad_prior * 100:.2f}%"

            plan_info = {
                "plan_name": plan_name,
                "emergency_actions": action_list,
                "simulation_results": sim_results,
                "timestamp": plan_create_time
            }



            # 放进 results，用 plan_name 做 key
            results[plan_name] = plan_info

        return results