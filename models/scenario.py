# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:07 AM
# @FileName: scenario.py
# @Software: PyCharm

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database.db_config import Base

class Scenario(Base):
    __tablename__ = 'scenarios'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default='Inactive')
    owl_status = Column(String(50), default='Unknown')      # 新增字段
    bayes_status = Column(String(50), default='Unknown')    # 新增字段
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 与 ScenarioElement 的关系（一个情景有多个情景要素）
    scenario_elements = relationship("ScenarioElement", back_populates="scenario", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Scenario(id={self.id}, name='{self.name}', status='{self.status}')>"

class ScenarioElement(Base):
    __tablename__ = 'scenario_elements'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    scenario_id = Column(Integer, ForeignKey('scenarios.id'), nullable=False)

    # 与 Scenario 的关系
    scenario = relationship("Scenario", back_populates="scenario_elements")

    # 与 AttributeModel 和 BehaviorModel 的关系（一个情景要素有一个属性模型和一个行为模型）
    attribute_model = relationship("AttributeModel", back_populates="scenario_element", uselist=False, cascade="all, delete-orphan")
    behavior_model = relationship("BehaviorModel", back_populates="scenario_element", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ScenarioElement(id={self.id}, name='{self.name}')>"

class AttributeModel(Base):
    __tablename__ = 'attribute_models'

    id = Column(Integer, primary_key=True, index=True)
    attribute = Column(Text, nullable=True)
    scenario_element_id = Column(Integer, ForeignKey('scenario_elements.id'), nullable=False)

    # 与 ScenarioElement 的关系
    scenario_element = relationship("ScenarioElement", back_populates="attribute_model")

    def __repr__(self):
        return f"<AttributeModel(id={self.id})>"

class BehaviorModel(Base):
    __tablename__ = 'behavior_models'

    id = Column(Integer, primary_key=True, index=True)
    behavior = Column(Text, nullable=True)
    scenario_element_id = Column(Integer, ForeignKey('scenario_elements.id'), nullable=False)

    # 与 ScenarioElement 的关系
    scenario_element = relationship("ScenarioElement", back_populates="behavior_model")

    def __repr__(self):
        return f"<BehaviorModel(id={self.id})>"