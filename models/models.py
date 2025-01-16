# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:07 AM
# @FileName: models.py
# @Software: PyCharm

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
    JSON,
    Table
)
from sqlalchemy.orm import relationship, backref

Base = declarative_base()

# -----------------------------------
# Association Tables (多对多中间表)
# -----------------------------------

entity_category = Table(
    'entity_category',
    Base.metadata,
    Column('entity_id', Integer,
           ForeignKey('entity.entity_id', ondelete='CASCADE', onupdate='RESTRICT'),
           primary_key=True),
    Column('category_id', Integer,
           ForeignKey('category.category_id', ondelete='CASCADE', onupdate='RESTRICT'),
           primary_key=True),
)

template_attribute_definition = Table(
    'template_attribute_definition',
    Base.metadata,
    Column('template_id', Integer,
           ForeignKey('template.template_id', ondelete='CASCADE', onupdate='RESTRICT'),
           primary_key=True),
    Column('attribute_definition_id', Integer,
           ForeignKey('attribute_definition.attribute_definition_id', ondelete='CASCADE', onupdate='RESTRICT'),
           primary_key=True),
)

template_behavior_definition = Table(
    'template_behavior_definition',
    Base.metadata,
    Column('template_id', Integer,
           ForeignKey('template.template_id', ondelete='CASCADE', onupdate='RESTRICT'),
           primary_key=True),
    Column('behavior_definition_id', Integer,
           ForeignKey('behavior_definition.behavior_definition_id', ondelete='CASCADE', onupdate='RESTRICT'),
           primary_key=True),
)

# -----------------------------------
# Model Definitions
# -----------------------------------

class AttributeAspect(Base):
    __tablename__ = 'attribute_aspect'
    attribute_aspect_id = Column(Integer, primary_key=True, autoincrement=True)
    attribute_aspect_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    create_time = Column(DateTime, nullable=False)
    update_time = Column(DateTime, nullable=False)

    attribute_definitions = relationship(
        'AttributeDefinition',
        back_populates='attribute_aspect'
    )


class AttributeCode(Base):
    __tablename__ = 'attribute_code'
    attribute_code_id = Column(Integer, primary_key=True, autoincrement=True)
    attribute_code_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    create_time = Column(DateTime, nullable=False)
    update_time = Column(DateTime, nullable=False)

    # 与 AttributeDefinition 多对一/一对多
    attribute_definitions = relationship('AttributeDefinition', back_populates='attribute_code')


class AttributeType(Base):
    __tablename__ = 'attribute_type'
    attribute_type_id = Column(Integer, primary_key=True, autoincrement=True)
    attribute_type_code = Column(String(50), unique=True, nullable=False)
    attribute_type_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Boolean, default=True, nullable=False)
    create_time = Column(DateTime, nullable=True)
    update_time = Column(DateTime, nullable=True)

    attribute_definitions = relationship('AttributeDefinition', back_populates='attribute_type')


class EntityType(Base):
    __tablename__ = 'entity_type'
    entity_type_id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type_name = Column(String(255), unique=True, nullable=False)
    entity_type_code = Column(String(50), unique=True, nullable=False)
    is_item_type = Column(Boolean, default=False, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Boolean, default=True, nullable=False)
    create_time = Column(DateTime, nullable=True)
    update_time = Column(DateTime, nullable=True)

    entities = relationship('Entity', back_populates='entity_type')
    # 关联: AttributeDefinition 里 reference_target_type_id -> EntityType
    attribute_definitions_as_reference = relationship(
        'AttributeDefinition',
        back_populates='reference_target_type',
        foreign_keys='AttributeDefinition.reference_target_type_id'
    )
    # BehaviorDefinition.object_entity_type_id -> entity_type_id
    behavior_definitions_as_object = relationship(
        'BehaviorDefinition',
        back_populates='object_entity_type',
        foreign_keys='BehaviorDefinition.object_entity_type_id'
    )


class AttributeDefinition(Base):
    __tablename__ = 'attribute_definition'
    attribute_definition_id = Column(Integer, primary_key=True, autoincrement=True)
    china_default_name = Column(String(255), nullable=False)
    english_default_name = Column(String(255), nullable=False)
    attribute_code_id = Column(Integer, ForeignKey('attribute_code.attribute_code_id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False)
    attribute_type_id = Column(Integer, ForeignKey('attribute_type.attribute_type_id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False)
    attribute_aspect_id = Column(Integer, ForeignKey('attribute_aspect.attribute_aspect_id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False)
    is_required = Column(Boolean, default=True, nullable=False)
    is_multi_valued = Column(Boolean, default=False, nullable=False)
    is_reference = Column(Boolean, default=False, nullable=False)
    reference_target_type_id = Column(Integer, ForeignKey('entity_type.entity_type_id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=True)
    default_value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    create_time = Column(DateTime, nullable=False)
    update_time = Column(DateTime, nullable=False)

    attribute_aspect = relationship('AttributeAspect', back_populates='attribute_definitions')
    attribute_code = relationship('AttributeCode', back_populates='attribute_definitions')
    attribute_type = relationship('AttributeType', back_populates='attribute_definitions')
    reference_target_type = relationship('EntityType', back_populates='attribute_definitions_as_reference')
    attribute_values = relationship('AttributeValue', back_populates='attribute_definition', passive_deletes=True)

    # EnumValue
    enum_values = relationship('EnumValue', back_populates='attribute_definition', passive_deletes=True)

    # 与 template 的多对多
    templates = relationship(
        'Template',
        secondary=template_attribute_definition,
        back_populates='attribute_definitions'
    )


class Category(Base):
    __tablename__ = 'category'
    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    create_time = Column(DateTime, nullable=False)
    update_time = Column(DateTime, nullable=False)

    # category <-> entity (多对多)
    entities = relationship(
        'Entity',
        secondary=entity_category,
        back_populates='categories'
    )

    # category <-> template (一对多)
    templates = relationship('Template', back_populates='category')


class Emergency(Base):
    __tablename__ = 'emergency'
    emergency_id = Column(Integer, primary_key=True, autoincrement=True)
    emergency_name = Column(String(255), unique=True, nullable=False)
    emergency_description = Column(Text, nullable=True)
    emergency_create_time = Column(DateTime, nullable=False)
    emergency_update_time = Column(DateTime, nullable=False)

    scenarios = relationship(
        'Scenario',
        back_populates='emergency',
        passive_deletes=True
    )


class Scenario(Base):
    __tablename__ = 'scenario'
    scenario_id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_name = Column(String(255), unique=True, nullable=False)
    scenario_description = Column(Text, nullable=True)
    scenario_create_time = Column(DateTime, nullable=False)
    scenario_update_time = Column(DateTime, nullable=False)
    emergency_id = Column(Integer, ForeignKey('emergency.emergency_id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)

    emergency = relationship('Emergency', back_populates='scenarios')

    # scenario -> entity
    entities = relationship('Entity', back_populates='scenario', passive_deletes=True)
    # scenario -> bayes
    bayes = relationship('Bayes', back_populates='scenario', passive_deletes=True)
    # scenario -> owl
    owls = relationship('Owl', back_populates='scenario', passive_deletes=True)


class Entity(Base):
    __tablename__ = 'entity'
    entity_id = Column(Integer, primary_key=True, autoincrement=True)
    entity_name = Column(String(255), nullable=False, index=True)
    entity_type_id = Column(Integer, ForeignKey('entity_type.entity_type_id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    entity_parent_id = Column(Integer, ForeignKey('entity.entity_id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=True)
    scenario_id = Column(Integer, ForeignKey('scenario.scenario_id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    create_time = Column(DateTime, nullable=False)
    update_time = Column(DateTime, nullable=False)

    entity_type = relationship('EntityType', back_populates='entities')
    parent = relationship(
        'Entity',
        remote_side=[entity_id],
        backref='children',
        passive_deletes=True
    )
    scenario = relationship('Scenario', back_populates='entities')

    categories = relationship(
        'Category',
        secondary=entity_category,
        back_populates='entities'
    )

    # entity -> attribute_values
    attribute_values = relationship(
        'AttributeValue',
        back_populates='entity',
        passive_deletes=True
    )

    # entity -> behavior_values
    behavior_values = relationship(
        'BehaviorValue',
        back_populates='subject_entity',
        passive_deletes=True
    )

    # entity -> posteriori_data
    posteriori_data = relationship(
        'PosterioriData',
        back_populates='plan',
        passive_deletes=True
    )


class AttributeValue(Base):
    __tablename__ = 'attribute_value'
    attribute_value_id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(Integer, ForeignKey('entity.entity_id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False, index=True)
    attribute_definition_id = Column(Integer, ForeignKey('attribute_definition.attribute_definition_id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False, index=True)
    attribute_name = Column(String(255), nullable=True)  # 新增字段
    attribute_value = Column(Text, nullable=True)
    create_time = Column(DateTime, nullable=False)
    update_time = Column(DateTime, nullable=False)

    entity = relationship('Entity', back_populates='attribute_values')
    attribute_definition = relationship('AttributeDefinition', back_populates='attribute_values')

    # attribute_value -> references
    references = relationship(
        'AttributeValueReference',
        back_populates='attribute_value',
        passive_deletes=True
    )


class AttributeValueReference(Base):
    __tablename__ = 'attribute_value_reference'
    attribute_value_id = Column(
        Integer,
        ForeignKey('attribute_value.attribute_value_id', ondelete='CASCADE', onupdate='RESTRICT'),
        primary_key=True
    )
    referenced_entity_id = Column(
        Integer,
        ForeignKey('entity.entity_id', ondelete='CASCADE', onupdate='RESTRICT'),
        primary_key=True
    )

    attribute_value = relationship('AttributeValue', back_populates='references')
    referenced_entity = relationship('Entity')


class Bayes(Base):
    __tablename__ = 'bayes'
    bayes_id = Column(Integer, primary_key=True, autoincrement=True)
    bayes_file_path = Column(String(255), nullable=False)
    scenario_id = Column(Integer, ForeignKey('scenario.scenario_id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)

    scenario = relationship('Scenario', back_populates='bayes')
    nodes = relationship('BayesNode', back_populates='bayes', passive_deletes=True)


class BayesNode(Base):
    __tablename__ = 'bayes_node'
    bayes_node_id = Column(Integer, primary_key=True, autoincrement=True)
    bayes_node_name = Column(String(255), nullable=False)
    bayes_id = Column(Integer, ForeignKey('bayes.bayes_id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)

    bayes = relationship('Bayes', back_populates='nodes')
    states = relationship('BayesNodeState', back_populates='bayes_node', passive_deletes=True)

    # 多对多自关联
    target_nodes = relationship(
        'BayesNode',
        secondary='bayes_node_target',
        primaryjoin='BayesNode.bayes_node_id == BayesNodeTarget.source_node_id',
        secondaryjoin='BayesNode.bayes_node_id == BayesNodeTarget.target_node_id',
        backref='source_nodes'
    )


class BayesNodeTarget(Base):
    __tablename__ = 'bayes_node_target'
    source_node_id = Column(Integer, ForeignKey('bayes_node.bayes_node_id', ondelete='CASCADE', onupdate='RESTRICT'), primary_key=True)
    target_node_id = Column(Integer, ForeignKey('bayes_node.bayes_node_id', ondelete='CASCADE', onupdate='RESTRICT'), primary_key=True)


class BayesNodeState(Base):
    __tablename__ = 'bayes_node_state'
    bayes_node_state_id = Column(Integer, primary_key=True, autoincrement=True)
    bayes_node_state_name = Column(String(255), nullable=False)
    bayes_node_state_prior_probability = Column(Float, nullable=False)
    bayes_node_id = Column(Integer, ForeignKey('bayes_node.bayes_node_id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    create_time = Column(DateTime, nullable=False)
    update_time = Column(DateTime, nullable=False)

    bayes_node = relationship('BayesNode', back_populates='states')
    posteriori_data = relationship('PosterioriData', back_populates='bayes_node_state', passive_deletes=True)


#
# 新增：BehaviorCode & BehaviorNameCode
#
class BehaviorCode(Base):
    """
    对应 behavior_code 表
    """
    __tablename__ = 'behavior_code'
    behavior_code_id = Column(Integer, primary_key=True, autoincrement=True)
    behavior_code_name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    create_time = Column(DateTime, nullable=False)
    update_time = Column(DateTime, nullable=False)

    # 一个 BehaviorCode 可以对应多个 BehaviorDefinition
    behavior_definitions = relationship('BehaviorDefinition', back_populates='behavior_code_ref', passive_deletes=True)

    # behavior_code <-> behavior_name_code (1对1 或 1对多)
    behavior_name_codes = relationship('BehaviorNameCode', back_populates='behavior_code', passive_deletes=True)


class BehaviorNameCode(Base):
    """
    对应 behavior_name_code 表
    记录了 behavior_code_id 与外部某些名字的对应关系(若需要)
    """
    __tablename__ = 'behavior_name_code'
    behavior_code_id = Column(
        Integer,
        ForeignKey('behavior_code.behavior_code_id', ondelete='CASCADE', onupdate='RESTRICT'),
        primary_key=True
    )
    behavior_name = Column(String(255), nullable=False)

    behavior_code = relationship('BehaviorCode', back_populates='behavior_name_codes')


class BehaviorDefinition(Base):
    __tablename__ = 'behavior_definition'
    behavior_definition_id = Column(Integer, primary_key=True, autoincrement=True)
    china_default_name = Column(String(255), nullable=False)
    english_default_name = Column(String(255), nullable=False)
    behavior_code = Column(
        Integer,
        ForeignKey('behavior_code.behavior_code_id', ondelete='CASCADE', onupdate='RESTRICT'),
        nullable=False,
        index=True
    )
    is_required = Column(Boolean, default=True, nullable=False)
    object_entity_type_id = Column(Integer, ForeignKey('entity_type.entity_type_id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    is_multi_valued = Column(Boolean, default=False, nullable=False)
    description = Column(Text, nullable=True)
    create_time = Column(DateTime, nullable=False)
    update_time = Column(DateTime, nullable=False)

    # 关联到 BehaviorCode
    behavior_code_ref = relationship('BehaviorCode', back_populates='behavior_definitions')

    # 指向 EntityType
    object_entity_type = relationship('EntityType', back_populates='behavior_definitions_as_object')

    # 与 BehaviorValue 的一对多
    behavior_values = relationship('BehaviorValue', back_populates='behavior_definition', passive_deletes=True)

    # 与 template 的多对多
    templates = relationship(
        'Template',
        secondary=template_behavior_definition,
        back_populates='behavior_definitions'
    )


class BehaviorValue(Base):
    __tablename__ = 'behavior_value'
    behavior_value_id = Column(Integer, primary_key=True, autoincrement=True)
    behavior_definition_id = Column(
        Integer,
        ForeignKey('behavior_definition.behavior_definition_id', ondelete='CASCADE', onupdate='RESTRICT'),
        nullable=False,
        index=True
    )
    subject_entity_id = Column(
        Integer,
        ForeignKey('entity.entity_id', ondelete='CASCADE', onupdate='RESTRICT'),
        nullable=False,
        index=True
    )
    create_time = Column(DateTime, nullable=False)
    update_time = Column(DateTime, nullable=False)

    behavior_definition = relationship('BehaviorDefinition', back_populates='behavior_values')
    subject_entity = relationship('Entity', back_populates='behavior_values')

    references = relationship(
        'BehaviorValueReference',
        back_populates='behavior_value',
        passive_deletes=True
    )


class BehaviorValueReference(Base):
    __tablename__ = 'behavior_value_reference'
    behavior_value_id = Column(
        Integer,
        ForeignKey('behavior_value.behavior_value_id', ondelete='CASCADE', onupdate='RESTRICT'),
        primary_key=True
    )
    object_entity_id = Column(
        Integer,
        ForeignKey('entity.entity_id', ondelete='CASCADE', onupdate='RESTRICT'),
        primary_key=True
    )

    behavior_value = relationship('BehaviorValue', back_populates='references')
    object_entity = relationship('Entity')


class EnumValue(Base):
    __tablename__ = 'enum_value'
    enum_value_id = Column(Integer, primary_key=True, autoincrement=True)
    enum_value = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    attribute_definition_id = Column(
        Integer,
        ForeignKey('attribute_definition.attribute_definition_id', ondelete='RESTRICT', onupdate='RESTRICT'),
        nullable=False,
        index=True
    )
    create_time = Column(DateTime, nullable=True)
    update_time = Column(DateTime, nullable=True)

    attribute_definition = relationship('AttributeDefinition', back_populates='enum_values')


class OwlType(Base):
    __tablename__ = 'owl_type'
    owl_type_id = Column(Integer, primary_key=True, autoincrement=True)
    owl_type_name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    create_time = Column(DateTime, nullable=False)
    update_time = Column(DateTime, nullable=False)

    owls = relationship(
        'Owl',
        back_populates='owl_type',
        passive_deletes=True
    )


class Owl(Base):
    __tablename__ = 'owl'
    owl_id = Column(Integer, primary_key=True, autoincrement=True)
    owl_type_id = Column(Integer, ForeignKey('owl_type.owl_type_id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False, index=True)
    owl_file_path = Column(String(255), nullable=False)
    scenario_id = Column(Integer, ForeignKey('scenario.scenario_id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False, index=True)

    owl_type = relationship('OwlType', back_populates='owls')
    scenario = relationship('Scenario', back_populates='owls')

    classes = relationship('OwlClass', back_populates='owl', passive_deletes=True)


class OwlClass(Base):
    __tablename__ = 'owl_class'
    owl_class_id = Column(Integer, primary_key=True, autoincrement=True)
    owl_class_name = Column(String(255), nullable=False, index=True)
    owl_class_parent = Column(Integer, ForeignKey('owl_class.owl_class_id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=True)
    owl_id = Column(Integer, ForeignKey('owl.owl_id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False, index=True)

    owl = relationship('Owl', back_populates='classes')
    parent_class = relationship(
        'OwlClass',
        remote_side=[owl_class_id],
        backref='child_classes',
        passive_deletes=True
    )

    attributes = relationship('OwlClassAttribute', back_populates='owl_class', passive_deletes=True)
    behaviors = relationship('OwlClassBehavior', back_populates='owl_class', passive_deletes=True)


class OwlClassAttribute(Base):
    __tablename__ = 'owl_class_attribute'
    owl_class_attribute_id = Column(Integer, primary_key=True, autoincrement=True)
    owl_class_attribute_name = Column(String(255), nullable=False)
    owl_class_attribute_range = Column(String(255), nullable=False)
    owl_class_id = Column(Integer, ForeignKey('owl_class.owl_class_id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False, index=True)
    create_time = Column(DateTime, nullable=False)
    update_time = Column(DateTime, nullable=False)

    owl_class = relationship('OwlClass', back_populates='attributes')


class OwlClassBehavior(Base):
    __tablename__ = 'owl_class_behavior'
    owl_class_behavior_id = Column(Integer, primary_key=True, autoincrement=True)
    owl_class_behavior_name = Column(String(255), nullable=False)
    owl_class_behavior_range = Column(String(255), nullable=False)
    owl_class_id = Column(Integer, ForeignKey('owl_class.owl_class_id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False, index=True)
    create_time = Column(DateTime, nullable=False)
    update_time = Column(DateTime, nullable=False)

    owl_class = relationship('OwlClass', back_populates='behaviors')


class PosterioriData(Base):
    __tablename__ = 'posteriori_data'
    posteriori_data_id = Column(Integer, primary_key=True, autoincrement=True)
    posterior_probability = Column(Float, nullable=False)
    bayes_node_state_id = Column(Integer, ForeignKey('bayes_node_state.bayes_node_state_id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    plan_id = Column(Integer, ForeignKey('entity.entity_id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    create_time = Column(DateTime, nullable=False)
    update_time = Column(DateTime, nullable=False)

    bayes_node_state = relationship('BayesNodeState', back_populates='posteriori_data', passive_deletes=True)
    plan = relationship('Entity', back_populates='posteriori_data', passive_deletes=True)


class Template(Base):
    __tablename__ = 'template'
    template_id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type_id = Column(Integer, ForeignKey('entity_type.entity_type_id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey('category.category_id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False, index=True)
    template_name = Column(String(255), unique=True, nullable=False)
    template_restrict = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    create_time = Column(DateTime, nullable=False)
    update_time = Column(DateTime, nullable=False)

    entity_type = relationship('EntityType')
    category = relationship('Category', back_populates='templates')

    attribute_definitions = relationship(
        'AttributeDefinition',
        secondary=template_attribute_definition,
        back_populates='templates'
    )
    behavior_definitions = relationship(
        'BehaviorDefinition',
        secondary=template_behavior_definition,
        back_populates='templates'
    )
