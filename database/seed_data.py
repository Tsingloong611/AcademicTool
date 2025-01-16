# -*- coding: utf-8 -*-
# @Time    : 12/28/2024 8:16 PM
# @FileName: seed_data.py
# @Software: PyCharm

import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 请确保将下行替换为您实际的 model.py
from models.models import Base
from models.models import (
    AttributeAspect,
    AttributeCode,
    AttributeDefinition,
    AttributeType,
    BehaviorDefinition,
    Category,
    Emergency,
    EntityType,
    Scenario,
    Template,
    # 如果需要在此文件里创建Entity, BehaviorValue等，可以一起导入
)

def seed_attribute_aspect(session):
    # 对应 SQL: INSERT INTO `attribute_aspect` VALUES ...
    data = [
        AttributeAspect(
            attribute_aspect_id=1,
            attribute_aspect_name='Hazard',
            description='致灾',
            create_time='2025-01-14 11:56:36',
            update_time='2025-01-15 11:24:48'
        ),
        AttributeAspect(
            attribute_aspect_id=2,
            attribute_aspect_name='Environmet',
            description='环境',
            create_time='2025-01-14 11:56:45',
            update_time='2025-01-14 11:56:45'
        ),
        AttributeAspect(
            attribute_aspect_id=3,
            attribute_aspect_name='Affected',
            description='承灾',
            create_time='2025-01-15 11:24:24',
            update_time='2025-01-15 11:24:24'
        ),
        AttributeAspect(
            attribute_aspect_id=4,
            attribute_aspect_name='Common',
            description='共有',
            create_time='2025-01-15 11:24:41',
            update_time='2025-01-15 11:24:41'
        ),
    ]
    session.bulk_save_objects(data)
    session.commit()

def seed_attribute_code(session):
    # 对应 SQL: INSERT INTO `attribute_code` VALUES ...
    raw_data = [
        (1, 'VehicleType', '车辆类型', '2025-01-15 10:41:42', '2025-01-15 10:41:42'),
        (2, 'CollisionCondition', '碰撞情况', '2025-01-15 10:43:06', '2025-01-15 10:46:42'),
        (3, 'CombustionCondition', '燃爆情况', '2025-01-15 10:43:53', '2025-01-15 10:46:52'),
        (4, 'SpillCondition', '抛洒情况', '2025-01-15 10:46:14', '2025-01-15 10:48:12'),
        (5, 'BreakdownCondition', '抛锚情况', '2025-01-15 10:48:25', '2025-01-15 10:48:25'),
        (6, 'RollOverCondition', '侧翻情况', '2025-01-15 10:48:37', '2025-01-15 10:48:37'),
        (7, 'AbnormalSpeedCondition', '速度异常情况', '2025-01-15 10:48:53', '2025-01-15 10:48:53'),
        (8, 'IIIegalLaneOccupationCondition', '违规占道情况', '2025-01-15 10:49:20', '2025-01-15 10:49:20'),
        (9, 'DrivingDirection', '行驶方向', '2025-01-15 10:49:35', '2025-01-15 10:49:35'),
        (10, 'VehiclePosition', '车辆位置', '2025-01-15 10:49:48', '2025-01-15 10:49:48'),
        (11, 'VehicleSpeed', '车辆速度', '2025-01-15 10:49:58', '2025-01-15 10:49:58'),
        (12, 'VehicleCargo', '车辆货物', '2025-01-15 10:50:13', '2025-01-15 10:50:13'),
        (13, 'VehiclePassengers', '车辆乘客', '2025-01-15 10:50:28', '2025-01-15 10:50:28'),
        (14, 'VehicleComponents', '车辆部件', '2025-01-15 10:50:39', '2025-01-15 10:50:39'),
        (15, 'DrivingRoadSegment', '所行驶路段', '2025-01-15 10:50:53', '2025-01-15 10:50:53'),
        (16, 'DamageCondition', '受损情况', '2025-01-15 10:51:02', '2025-01-15 10:51:02'),
        (17, 'CasualtyCondition', '伤亡情况', '2025-01-15 10:51:18', '2025-01-15 10:51:18'),
        (18, 'AffiliatedVehicle', '所属车辆', '2025-01-15 10:51:37', '2025-01-15 10:51:37'),
        (19, 'RoadName', '道路名称', '2025-01-15 10:51:49', '2025-01-15 10:51:49'),
        (20, 'RoadType', '道路类型', '2025-01-15 10:51:59', '2025-01-15 10:51:59'),
        (21, 'NumberOfLanes', '行车道数', '2025-01-15 10:52:18', '2025-01-15 10:52:18'),
        (22, 'TrafficVolume', '交通量', '2025-01-15 10:52:27', '2025-01-15 10:52:27'),
        (23, 'SegmentStartStakeNumber', '段起点桩号', '2025-01-15 10:52:34', '2025-01-15 10:52:53'),
        (24, 'SegmentEndStakeNumber', '段终点桩号', '2025-01-15 10:53:09', '2025-01-15 10:53:09'),
        (25, 'DesignSpeed', '设计车速', '2025-01-15 10:53:20', '2025-01-15 10:53:20'),
        (26, 'ClosureCondition', '封闭情况', '2025-01-15 10:53:43', '2025-01-15 10:53:43'),
        (27, 'DamageConditon', '受损情况', '2025-01-15 10:53:54', '2025-01-15 10:53:54'),
        (28, 'PollutionCondition', '污染情况', '2025-01-15 10:54:09', '2025-01-15 10:54:09'),
        (29, 'IncludedFacilities', '所含设施', '2025-01-15 10:54:19', '2025-01-15 10:54:19'),
        (30, 'IncludedVehicles', '所含车辆', '2025-01-15 10:54:30', '2025-01-15 10:54:30'),
        (31, 'RoadMaintenanceConditon', '道路养护情况', '2025-01-15 10:54:44', '2025-01-15 10:54:44'),
        (32, 'RoadConstrucetionCondition', '道路施工情况', '2025-01-15 10:54:58', '2025-01-15 10:54:58'),
        (33, 'WeatherType', '气象类型', '2025-01-15 10:55:08', '2025-01-15 10:55:08'),
        (34, 'Rainfall', '降雨量', '2025-01-15 10:55:16', '2025-01-15 10:55:16'),
        (35, 'Visibility', '能见度', '2025-01-15 10:55:25', '2025-01-15 10:55:25'),
        (36, 'WindSpeed', '风速', '2025-01-15 10:55:43', '2025-01-15 10:55:43'),
        (37, 'WindForce', '风力', '2025-01-15 10:55:51', '2025-01-15 10:55:51'),
        (38, 'SnowfallIntensity', '降雪强度', '2025-01-15 10:56:03', '2025-01-15 10:56:03'),
        (39, 'AffectedArea', '作用区域', '2025-01-15 10:56:19', '2025-01-15 10:56:19'),
        (40, 'IncludedLanes', '所含车道', '2025-01-15 10:57:23', '2025-01-15 10:57:23'),
        (41, 'TravelTime', '通行时间', '2025-01-15 10:57:39', '2025-01-15 10:57:39'),
        (42, 'SpeedLimit', '限速值', '2025-01-15 10:57:48', '2025-01-15 10:57:48'),
        (43, 'ResourceType', '资源类型', '2025-01-15 10:58:00', '2025-01-15 10:58:00'),
        (44, 'ResourceUsageCondition', '资源使用情况', '2025-01-15 10:58:10', '2025-01-15 10:58:10'),
        (45, 'ResourceQuantityOrQuality', '资源数（质）量', '2025-01-15 10:58:34', '2025-01-15 10:58:34'),
        (46, 'AssociatedBehavior', '关联行为', '2025-01-15 10:58:48', '2025-01-15 10:58:48'),
        (47, 'BehaviorType', '行为类型', '2025-01-15 10:59:01', '2025-01-15 10:59:01'),
        (48, 'ImplementationCondition', '实施情况', '2025-01-15 10:59:14', '2025-01-15 10:59:14'),
        (49, 'TrafficCapacity', '通行能力', '2025-01-15 11:00:20', '2025-01-15 11:00:20'),
        (50, 'Duration', '持续时间', '2025-01-15 11:08:15', '2025-01-15 11:08:15'),
        (51, 'InvolvedMaterials', '涉及物资', '2025-01-15 11:08:28', '2025-01-15 11:08:28'),
        (52, 'ImplementingPersonnel', '实施人员', '2025-01-15 11:08:41', '2025-01-15 11:08:41'),
        (53, 'EmergencyVehicles', '应急车辆', '2025-01-15 11:08:51', '2025-01-15 11:08:51'),
        (54, 'TargetOfImplementation', '实施对象', '2025-01-15 11:09:12', '2025-01-15 11:09:12'),
    ]
    objs = []
    for r in raw_data:
        objs.append(AttributeCode(
            attribute_code_id=r[0],
            attribute_code_name=r[1],
            description=r[2],
            create_time=r[3],
            update_time=r[4]
        ))
    session.bulk_save_objects(objs)
    session.commit()

def seed_attribute_type(session):
    # 对应 SQL: INSERT INTO `attribute_type` VALUES ...
    data = [
        AttributeType(attribute_type_id=1, attribute_type_code='String', attribute_type_name='字符串',
                      description=None, status=True, create_time='2025-01-15 11:10:14', update_time='2025-01-15 11:10:14'),
        AttributeType(attribute_type_id=2, attribute_type_code='Real', attribute_type_name='数值型',
                      description=None, status=True, create_time='2025-01-15 11:10:14', update_time='2025-01-15 11:10:14'),
        AttributeType(attribute_type_id=3, attribute_type_code='Bool', attribute_type_name='布尔型',
                      description=None, status=True, create_time='2025-01-15 11:10:14', update_time='2025-01-15 11:10:14'),
        AttributeType(attribute_type_id=4, attribute_type_code='Enum', attribute_type_name='枚举型',
                      description=None, status=True, create_time='2025-01-15 11:10:14', update_time='2025-01-15 11:10:14'),
        AttributeType(attribute_type_id=5, attribute_type_code='Item', attribute_type_name='Item',
                      description='实体-Item级', status=True, create_time='2025-01-15 11:10:14', update_time='2025-01-15 11:10:14'),
        AttributeType(attribute_type_id=6, attribute_type_code='Entity', attribute_type_name='Entity',
                      description='实体-非Item级', status=True, create_time='2025-01-15 11:10:14', update_time='2025-01-15 11:10:14'),
    ]
    session.bulk_save_objects(data)
    session.commit()

def seed_entity_type(session):
    # 对应 SQL: INSERT INTO `entity_type` VALUES ...
    data = [
        EntityType(entity_type_id=1, entity_type_name='车辆', entity_type_code='Vehicle',
                   is_item_type=False, description=None, status=True,
                   create_time='2025-01-15 11:10:57', update_time='2025-01-15 11:10:57'),
        EntityType(entity_type_id=2, entity_type_name='路段', entity_type_code='Road',
                   is_item_type=False, description=None, status=True,
                   create_time='2025-01-15 11:10:57', update_time='2025-01-15 11:10:57'),
        EntityType(entity_type_id=3, entity_type_name='自然环境', entity_type_code='Meteorology',
                   is_item_type=False, description=None, status=True,
                   create_time='2025-01-15 11:10:57', update_time='2025-01-15 11:10:57'),
        EntityType(entity_type_id=4, entity_type_name='应急资源', entity_type_code='ResponseResource',
                   is_item_type=False, description=None, status=True,
                   create_time='2025-01-15 11:10:57', update_time='2025-01-15 11:10:57'),
        EntityType(entity_type_id=5, entity_type_name='应急行为', entity_type_code='ResponseAction',
                   is_item_type=False, description=None, status=True,
                   create_time='2025-01-15 11:10:57', update_time='2025-01-15 11:10:57'),
        EntityType(entity_type_id=6, entity_type_name='车辆部件', entity_type_code='VehiclePart',
                   is_item_type=True, description=None, status=True,
                   create_time='2025-01-15 11:10:57', update_time='2025-01-15 11:10:57'),
        EntityType(entity_type_id=7, entity_type_name='承载物', entity_type_code='VehicleLoad',
                   is_item_type=True, description=None, status=True,
                   create_time='2025-01-15 11:10:57', update_time='2025-01-15 11:10:57'),
        EntityType(entity_type_id=8, entity_type_name='基础设施', entity_type_code='Facility',
                   is_item_type=True, description=None, status=True,
                   create_time='2025-01-15 11:10:57', update_time='2025-01-15 11:10:57'),
        EntityType(entity_type_id=11, entity_type_name='车道', entity_type_code='Lane',
                   is_item_type=True, description=None, status=True,
                   create_time='2025-01-15 11:10:57', update_time='2025-01-15 11:15:38'),
        EntityType(entity_type_id=12, entity_type_name='人类', entity_type_code='People',
                   is_item_type=True, description=None, status=True,
                   create_time='2025-01-15 11:10:57', update_time='2025-01-15 11:15:35'),
        EntityType(entity_type_id=13, entity_type_name='应急预案', entity_type_code='ResponsePlan',
                   is_item_type=False, description=None, status=True,
                   create_time='2025-01-15 11:10:57', update_time='2025-01-15 11:15:32'),
    ]
    session.bulk_save_objects(data)
    session.commit()

def seed_attribute_definition(session):
    # 对应 SQL: INSERT INTO `attribute_definition` VALUES ...
    raw_data = [
        (1, '车辆类型', '车辆类型', 1, 1, 4, 1, 0, 0, None, None, '车辆-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (2, '碰撞情况', '碰撞情况', 2, 3, 1, 1, 0, 0, None, '0', '车辆-致灾体专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (3, '燃爆情况', '燃爆情况', 3, 3, 4, 1, 0, 0, None, '0', '车辆-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (4, '抛洒情况', '抛洒情况', 4, 3, 4, 1, 0, 0, None, '0', '车辆-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (5, '抛锚情况', '抛锚情况', 5, 3, 1, 1, 0, 0, None, '0', '车辆-致灾体专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (6, '侧翻情况', '侧翻情况', 6, 3, 1, 1, 0, 0, None, '0', '车辆-致灾体专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (7, '速度异常情况', '速度异常情况', 7, 1, 1, 0, 0, 0, None, None, '车辆-致灾体专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (8, '违规占道情况', '违规占道情况', 8, 3, 1, 0, 0, 0, None, '0', '车辆-致灾体专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (9, '行驶方向', '行驶方向', 9, 4, 4, 0, 0, 0, None, '正向', '车辆-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (10, '车辆位置', '车辆位置', 10, 1, 4, 1, 0, 0, None, None, '车辆-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (11, '车辆速度', '车辆速度', 11, 2, 4, 1, 0, 0, None, None, '车辆-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (12, '车辆货物', '车辆货物', 12, 5, 4, 0, 1, 1, 7, None, '车辆-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (13, '车辆乘客', '车辆乘客', 13, 5, 4, 0, 1, 1, 12, None, '车辆-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (14, '车辆部件', '车辆部件', 14, 5, 4, 0, 1, 1, 6, None, '车辆-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (15, '所行驶路段', '所行驶路段', 15, 6, 4, 1, 0, 1, 2, None, '车辆-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (16, '受损情况', '受损情况', 16, 3, 3, 1, 0, 0, None, '0', '车辆-承灾体专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (17, '伤亡情况', '伤亡情况', 17, 3, 4, 1, 0, 0, None, '0', '人类', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (18, '所属车辆', '所属车辆', 18, 6, 4, 1, 0, 1, 1, None, '人类', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (19, '道路名称', '道路名称', 19, 1, 4, 0, 0, 0, None, None, '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (20, '道路类型', '道路类型', 20, 4, 4, 1, 0, 0, None, '主路', '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (21, '行车道数', '行车道数', 21, 2, 4, 1, 0, 0, None, None, '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (22, '交通量', '交通量', 22, 2, 4, 1, 0, 0, None, None, '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (23, '段起点桩号', '段起点桩号', 23, 1, 4, 1, 0, 0, None, None, '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (24, '段终点桩号', '段终点桩号', 24, 1, 4, 1, 0, 0, None, None, '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (25, '设计车速', '设计车速', 25, 2, 4, 0, 0, 0, None, None, '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (26, '封闭情况', '封闭情况', 26, 3, 4, 1, 0, 0, None, '0', '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (27, '受损情况', '受损情况', 27, 3, 3, 1, 0, 0, None, '0', '道路-承灾体专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (28, '污染情况', '污染情况', 28, 3, 3, 1, 0, 0, None, '0', '道路-承灾体专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (29, '所含车道', '所含车道', 40, 5, 4, 1, 1, 1, 11, None, '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (30, '所含设施', '所含设施', 29, 5, 4, 0, 1, 1, 8, None, '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (31, '所含车辆', '所含车辆', 30, 6, 4, 1, 1, 1, 1, None, '道路-共有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (32, '道路养护情况', '道路养护情况', 31, 3, 2, 0, 0, 0, None, '0', '道路-环境专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (33, '道路施工情况', '道路施工情况', 32, 3, 2, 0, 0, 0, None, '0', '道路-环境专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (34, '气象类型', '气象类型', 33, 4, 4, 1, 0, 0, None, '晴天', '气象', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (35, '降雨量', '降雨量', 34, 2, 4, 0, 0, 0, None, None, '气象', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (36, '能见度', '能见度', 35, 2, 4, 0, 0, 0, None, None, '气象', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (37, '风速', '风速', 36, 2, 4, 0, 0, 0, None, None, '气象', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (38, '风力', '风力', 37, 2, 4, 0, 0, 0, None, None, '气象', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (39, '降雪强度', '降雪强度', 38, 4, 4, 0, 0, 0, None, '大雪', '气象', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (40, '作用区域', '作用区域', 39, 6, 4, 1, 1, 1, 2, None, '气象', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (41, '通行时间', '通行时间', 41, 2, 4, 0, 0, 0, None, None, '道路-环境专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (42, '通行能力', '通行能力', 49, 2, 4, 0, 0, 0, None, None, '道路-环境专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (43, '限速值', '限速值', 42, 2, 4, 0, 0, 0, None, None, '道路-环境专有', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (44, '资源类型', '资源类型', 43, 4, 4, 1, 0, 0, None, None, '应急资源', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (45, '资源使用情况', '资源使用情况', 44, 3, 4, 0, 0, 0, None, '0', '应急资源', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (46, '资源数（质）量', '资源数（质）量', 45, 2, 4, 0, 0, 0, None, None, '应急资源', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (47, '关联行为', '关联行为', 46, 6, 4, 1, 0, 1, 5, None, '应急资源', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (48, '行为类型', '行为类型', 47, 4, 4, 1, 0, 0, None, None, '应急行为', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (49, '实施情况', '实施情况', 48, 3, 4, 1, 0, 0, None, '0', '应急行为', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (50, '持续时间', '持续时间', 50, 2, 4, 1, 0, 0, None, None, '应急行为', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (51, '涉及物资', '涉及物资', 51, 6, 4, 1, 1, 1, 4, None, '应急行为', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (52, '实施人员', '实施人员', 52, 6, 4, 1, 1, 1, 4, None, '应急行为', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (53, '应急车辆', '应急车辆', 53, 6, 4, 1, 1, 1, 4, None, '应急行为', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
        (54, '实施对象', '实施对象', 54, 6, 4, 1, 1, 1, None, None, '应急行为', '2025-01-15 11:32:39', '2025-01-15 11:32:39'),
    ]
    objs = []
    for d in raw_data:
        objs.append(AttributeDefinition(
            attribute_definition_id=d[0],
            china_default_name=d[1],
            english_default_name=d[2],
            attribute_code_id=d[3],
            attribute_type_id=d[4],
            attribute_aspect_id=d[5],
            is_required=bool(d[6]),
            is_multi_valued=bool(d[7]),
            is_reference=bool(d[8]),
            reference_target_type_id=d[9],
            default_value=d[10],
            description=d[11],
            create_time=d[12],
            update_time=d[13]
        ))
    session.bulk_save_objects(objs)
    session.commit()

def seed_category(session):
    # 对应 SQL: INSERT INTO `category` VALUES ...
    data = [
        Category(
            category_id=1,
            category_name='AffectedElement',
            description='承灾要素',
            create_time='2025-01-15 10:37:25',
            update_time='2025-01-15 10:37:25'
        ),
        Category(
            category_id=2,
            category_name='EnvironmentElement',
            description='环境要素',
            create_time='2025-01-15 10:37:25',
            update_time='2025-01-15 10:37:25'
        ),
        Category(
            category_id=3,
            category_name='HazardElement',
            description='致灾要素',
            create_time='2025-01-15 10:37:25',
            update_time='2025-01-15 10:37:25'
        ),
        Category(
            category_id=4,
            category_name='ResponsePlanElement',
            description='应急预案要素',
            create_time='2025-01-15 10:37:25',
            update_time='2025-01-15 10:37:25'
        ),
        Category(
            category_id=5,
            category_name='Item',
            description=None,
            create_time='2025-01-15 10:37:25',
            update_time='2025-01-15 10:37:25'
        ),
        Category(
            category_id=6,
            category_name='Common',
            description=None,
            create_time='2025-01-15 10:37:38',
            update_time='2025-01-15 10:37:38'
        ),
    ]
    session.bulk_save_objects(data)
    session.commit()

def seed_emergency(session):
    # 对应 SQL: INSERT INTO `emergency` VALUES ...
    e = Emergency(
        emergency_id=1,
        emergency_name='测试',
        emergency_description=None,
        emergency_create_time='2025-01-15 11:11:07',
        emergency_update_time='2025-01-15 11:11:07'
    )
    session.add(e)
    session.commit()

def seed_scenario(session):
    # 对应 SQL: INSERT INTO `scenario` VALUES ...
    s = Scenario(
        scenario_id=1,
        scenario_name='测试',
        scenario_description=None,
        scenario_create_time='2025-01-15 11:11:19',
        scenario_update_time='2025-01-15 11:11:19',
        emergency_id=1
    )
    session.add(s)
    session.commit()

def seed_behavior_definition(session):
    # 对应 SQL: INSERT INTO `behavior_definition` VALUES ...
    raw_data = [
        (1, '车辆行驶', 1, 2, 0, '车辆-共有', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (2, '车辆运载', 0, 7, 0, '车辆-共有', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (3, '车辆离开', 1, 2, 0, '车辆-共有', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (4, '车辆燃爆', 1, 1, 0, '车辆-共有', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (5, '车辆抛洒', 1, 1, 0, '车辆-共有', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (6, '车辆侧翻', 1, 1, 0, '车辆-致灾体专有', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (7, '车辆抛锚', 1, 1, 0, '车辆-致灾体专有', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (8, '车辆撞击', 1, 1, 0, '车辆-致灾体专有', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (9, '车辆转向', 0, 1, 0, '车辆-致灾体专有', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (10, '车辆变道', 0, 11, 0, '车辆-致灾体专有', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (11, '车辆变速', 0, 1, 0, '车辆-共有', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (12, '消防', 1, 8, 1, '应急行为', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (13, '人员救护', 1, 12, 1, '应急行为', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (14, '车辆牵引', 1, 1, 1, '应急行为', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (15, '路面清扫', 1, 2, 1, '应急行为', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (16, '道路抢修', 1, 2, 1, '应急行为', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (17, '道路管制', 0, 2, 0, '应急行为', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
        (18, '危化品处置', 1, 7, 0, '应急行为', '2025-01-15 11:16:03', '2025-01-15 11:16:03'),
    ]
    objs = []
    for b in raw_data:
        objs.append(BehaviorDefinition(
            behavior_definition_id=b[0],
            behavior_name=b[1],
            is_required=bool(b[2]),
            object_entity_type_id=b[3],
            is_multi_valued=bool(b[4]),
            description=b[5],
            create_time=b[6],
            update_time=b[7]
        ))
    session.bulk_save_objects(objs)
    session.commit()

def seed_template(session):
    # 对应 SQL: INSERT INTO `template` VALUES ...
    raw_data = [
        (1, 1, 1, '车辆承灾要素', '{"show": [{}], "create": {"entity_type": "Vehicle", "category_type": ["AffectedElement"]}, "select": {"entity_type": "Vehicle", "category_type": "AffectedElement"}}', None, '2025-01-15 11:46:12', '2025-01-15 11:46:12'),
        (2, 2, 1, '道路承灾要素', '{"show": [{"aspect_type": "Affected"}], "create": {"entity_type": "Road", "category_type": ["AffectedElement", "HazardElement"]}, "select": {"entity_type": "Road", "category_type": "AffectedElement"}}', None, '2025-01-15 12:44:15', '2025-01-15 12:44:15'),
        (3, 12, 5, '人类承灾要素', '{"show": [{"aspect_type": "Hazard"}], "create": {"entity_type": "Road", "category_type": ["AffectedElement", "HazardElement"]}, "select": {"entity_type": "Road", "category_type": "AffectedElement"}}', '展示时仅展示受伤的', '2025-01-15 12:44:42', '2025-01-15 12:44:42'),
        (4, 1, 3, '车辆致灾要素', '{"show": [{}], "create": {"entity_type": "Vehicle", "category_type": "HazardElement"}, "select": {"entity_type": "Vehicle", "category_type": "HazardElement"}}', None, '2025-01-15 12:46:02', '2025-01-15 12:46:02'),
        (5, 2, 2, '道路环境要素', '{"show": [{"aspect_type": "Environment"}], "create": {"entity_type": "Road", "category_type": ["AffectedElement", "HazardElement"]}, "select": {"entity_type": "Road", "category_type": "Environment"}}', None, '2025-01-15 12:47:00', '2025-01-15 12:47:00'),
        (6, 3, 2, '气象环境要素', '{"show": [{}], "create": {"entity_type": "Meteorology", "category_type": "EnvironmentElement"}, "select": {"entity_type": "Meteorology", "category_type": "EnvironmentElement"}}', None, '2025-01-15 12:55:22', '2025-01-15 12:55:22'),
        (7, 4, 4, '应急资源要素', '{"show": [{}], "create": {"entity_type": "ResponseResource", "category_type": "ResponsePlanElement"}, "select": {"entity_type": "ResponseResource", "category_type": "ResponsePlanElement"}}', None, '2025-01-15 12:55:23', '2025-01-15 12:55:23'),
        (8, 5, 4, '应急行为要素', '{"show": [{}], "create": {"entity_type": "ResponseAction", "category_type": "ResponsePlanElement"}, "select": {"entity_type": "ResponseAction", "category_type": "ResponsePlanElement"}}', None, '2025-01-15 12:55:23', '2025-01-15 12:55:23'),
        (9, 8, 5, '基础设施', '{"show": [{}], "create": {"entity_type": "Facility", "category_type": "Item"}, "select": {"entity_type": "Facility", "category_type": "Item"}}', None, '2025-01-15 12:56:36', '2025-01-15 13:02:10'),
    ]
    objs = []
    for t in raw_data:
        objs.append(Template(
            template_id=t[0],
            entity_type_id=t[1],
            category_id=t[2],
            template_name=t[3],
            template_restrict=json.loads(t[4]),
            description=t[5],
            create_time=t[6],
            update_time=t[7]
        ))
    session.bulk_save_objects(objs)
    session.commit()

def seed_template_attribute_definition(session):
    # 对应 SQL: INSERT INTO `template_attribute_definition` VALUES ...
    raw_data = [
        (1, 1), (4, 1), (4, 2), (1, 3), (4, 3), (1, 4), (4, 4), (4, 5), (4, 6), (4, 7),
        (4, 8), (1, 9), (4, 9), (1, 10), (4, 10), (1, 11), (4, 11), (1, 12), (4, 12),
        (1, 13), (4, 13), (1, 14), (4, 14), (1, 15), (4, 15), (1, 16), (3, 17), (3, 18),
        (2, 19), (5, 19), (2, 20), (5, 20), (2, 21), (5, 21), (2, 22), (5, 22), (2, 23),
        (5, 23), (2, 24), (5, 24), (2, 25), (5, 25), (2, 26), (5, 26), (2, 27), (2, 28),
        (2, 29), (5, 29), (2, 30), (5, 30), (2, 31), (5, 31), (5, 32), (5, 33), (6, 34),
        (6, 35), (6, 36), (6, 37), (6, 38), (6, 39), (6, 40), (5, 41), (5, 42), (5, 43),
        (7, 44), (7, 45), (7, 46), (7, 47),
    ]
    for (tid, adid) in raw_data:
        template_obj = session.query(Template).filter_by(template_id=tid).one()
        attr_def_obj = session.query(AttributeDefinition).filter_by(attribute_definition_id=adid).one()
        template_obj.attribute_definitions.append(attr_def_obj)
    session.commit()

def seed_template_behavior_definition(session):
    # 对应 SQL: INSERT INTO `template_behavior_definition` VALUES ...
    raw_data = [
        (1, 1), (4, 1), (1, 2), (4, 2), (1, 3), (4, 3), (1, 4), (4, 4), (1, 5), (4, 5),
        (4, 6), (4, 7), (4, 8), (4, 9), (4, 10), (1, 11), (4, 11), (8, 12), (8, 13),
        (8, 14), (8, 15), (8, 16), (8, 17),
    ]
    for (tid, bid) in raw_data:
        template_obj = session.query(Template).filter_by(template_id=tid).one()
        behav_obj = session.query(BehaviorDefinition).filter_by(behavior_definition_id=bid).one()
        template_obj.behavior_definitions.append(behav_obj)
    session.commit()

def seed_all(session):
    try:

        # 1. 先插入无外键依赖的表
        seed_attribute_aspect(session)
        seed_attribute_code(session)
        seed_attribute_type(session)
        seed_entity_type(session)

        # 2. 再插入依赖表
        seed_attribute_definition(session)
        seed_category(session)
        seed_emergency(session)
        seed_scenario(session)
        seed_behavior_definition(session)
        seed_template(session)

        # 3. 最后插入中间表关联
        seed_template_attribute_definition(session)
        seed_template_behavior_definition(session)

        print("数据插入完成！")
    except Exception as e:
        session.rollback()
        print("数据插入失败:", e)
    finally:
        session.close()

if __name__ == '__main__':
    seed_all()
