# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:07 AM
# @FileName: models.py
# @Software: PyCharm

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey,
    UniqueConstraint, PrimaryKeyConstraint, Index, func
)
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import expression

Base = declarative_base()

# ========================
# 1. ElementType (要素类型)
# ========================
class ElementType(Base):
    __tablename__ = 'element_type'

    element_type_id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    # 对于 TINYINT(1)，可以使用 Boolean 或直接用 TINYINT(1)
    status = Column(TINYINT(1), nullable=False, server_default="1")
    create_time = Column(DateTime, server_default=func.now())
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ElementType(name={self.name}, code={self.code})>"


# ==========================
# 2. AttributeType (属性类型)
# ==========================
class AttributeType(Base):
    __tablename__ = 'attribute_type'

    attribute_type_id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(TINYINT(1), nullable=False, server_default="1")
    create_time = Column(DateTime, server_default=func.now())
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<AttributeType(name={self.name}, code={self.code})>"


# =======================
# 3. OwlType (OWL本体类型)
# =======================
class OwlType(Base):
    __tablename__ = 'owl_type'

    owl_type_id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(TINYINT(1), nullable=False, server_default="1")
    create_time = Column(DateTime, server_default=func.now())
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<OwlType(name={self.name}, code={self.code})>"


# =====================
# 4. EnumValue (枚举值)
# =====================
class EnumValue(Base):
    __tablename__ = 'enum_value'

    enum_value_id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    def __repr__(self):
        return f"<EnumValue(value={self.value})>"


# ===============================
# 5. Emergency (突发事件基本信息)
# ===============================
class Emergency(Base):
    __tablename__ = 'emergency'

    emergency_id = Column(Integer, primary_key=True, autoincrement=True)
    emergency_name = Column(String(255), nullable=False, unique=True, index=True)
    emergency_description = Column(Text, nullable=True)
    emergency_create_time = Column(DateTime, server_default=func.now())
    emergency_update_time = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Emergency(name={self.emergency_name})>"


# ===============================
# 6. Scenario (情景信息，关联突发事件)
# ===============================
class Scenario(Base):
    __tablename__ = 'scenario'

    scenario_id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_name = Column(String(255), nullable=False, unique=True, index=True)
    scenario_description = Column(Text, nullable=True)
    scenario_create_time = Column(DateTime, server_default=func.now())
    scenario_update_time = Column(DateTime, server_default=func.now(), onupdate=func.now())

    emergency_id = Column(
        Integer,
        ForeignKey('emergency.emergency_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    # 如果需要映射关系，可加 relationship
    # emergency = relationship("Emergency", back_populates="scenarios")

    def __repr__(self):
        return f"<Scenario(name={self.scenario_name})>"


# =============================
# 7. Element (情景中的要素)
# =============================
class Element(Base):
    __tablename__ = 'element'

    element_id = Column(Integer, primary_key=True, autoincrement=True)
    element_name = Column(String(255), nullable=False, index=True)

    element_type_id = Column(
        Integer,
        ForeignKey('element_type.element_type_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    element_parent_id = Column(
        Integer,
        ForeignKey('element.element_id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )
    scenario_id = Column(
        Integer,
        ForeignKey('scenario.scenario_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    def __repr__(self):
        return f"<Element(name={self.element_name})>"


# ================================
# 8. Attribute (要素的属性)
# ================================
class Attribute(Base):
    __tablename__ = 'attribute'

    attribute_id = Column(Integer, primary_key=True, autoincrement=True)
    attribute_name = Column(String(255), nullable=False)
    attribute_type_id = Column(
        Integer,
        ForeignKey('attribute_type.attribute_type_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    is_required = Column(Boolean, nullable=False, server_default=expression.true())
    is_multi_valued = Column(Boolean, nullable=False, server_default=expression.false())

    enum_value_id = Column(
        Integer,
        ForeignKey('enum_value.enum_value_id', ondelete='SET NULL'),
        nullable=True
    )
    attribute_value = Column(Text, nullable=True)

    element_id = Column(
        Integer,
        ForeignKey('element.element_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    def __repr__(self):
        return f"<Attribute(name={self.attribute_name})>"


# ==========================================================
# 9. AttributeAssociation (属性与要素之间的关联关系，多对多)
# ==========================================================
class AttributeAssociation(Base):
    __tablename__ = 'attribute_association'

    attribute_id = Column(
        Integer,
        ForeignKey('attribute.attribute_id', ondelete='CASCADE'),
        primary_key=True
    )
    associated_element_id = Column(
        Integer,
        ForeignKey('element.element_id', ondelete='CASCADE'),
        primary_key=True
    )

    def __repr__(self):
        return f"<AttributeAssociation(attribute_id={self.attribute_id}, element_id={self.associated_element_id})>"


# ==========================
# 10. Behavior (行为模型)
# ==========================
class Behavior(Base):
    __tablename__ = 'behavior'

    behavior_id = Column(Integer, primary_key=True, autoincrement=True)
    behavior_name = Column(String(255), nullable=False)
    is_required = Column(Boolean, nullable=False, server_default=expression.true())
    object_type_id = Column(
        Integer,
        ForeignKey('element_type.element_type_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    is_multi_valued = Column(Boolean, nullable=False, server_default=expression.false())

    element_id = Column(
        Integer,
        ForeignKey('element.element_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    def __repr__(self):
        return f"<Behavior(name={self.behavior_name})>"


# ============================================
# 11. BehaviorObject (行为对象，多对多关系)
# ============================================
class BehaviorObject(Base):
    __tablename__ = 'behavior_object'

    behavior_id = Column(
        Integer,
        ForeignKey('behavior.behavior_id', ondelete='CASCADE'),
        primary_key=True
    )
    object_element_id = Column(
        Integer,
        ForeignKey('element.element_id', ondelete='CASCADE'),
        primary_key=True
    )

    def __repr__(self):
        return f"<BehaviorObject(behavior_id={self.behavior_id}, object_element_id={self.object_element_id})>"


# ====================
# 12. Owl (存储OWL本体)
# ====================
class Owl(Base):
    __tablename__ = 'owl'

    owl_id = Column(Integer, primary_key=True, autoincrement=True)
    owl_type_id = Column(
        Integer,
        ForeignKey('owl_type.owl_type_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    owl_file_path = Column(String(255), nullable=False)

    scenario_id = Column(
        Integer,
        ForeignKey('scenario.scenario_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    def __repr__(self):
        return f"<Owl(id={self.owl_id}, file_path={self.owl_file_path})>"


# ================================
# 13. OwlClass (本体中的类信息)
# ================================
class OwlClass(Base):
    __tablename__ = 'owl_class'

    owl_class_id = Column(Integer, primary_key=True, autoincrement=True)
    owl_class_name = Column(String(255), nullable=False, index=True)

    owl_class_parent = Column(
        Integer,
        ForeignKey('owl_class.owl_class_id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )
    owl_id = Column(
        Integer,
        ForeignKey('owl.owl_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    def __repr__(self):
        return f"<OwlClass(name={self.owl_class_name})>"


# ===================================================
# 14. OwlClassAttribute (本体类的属性信息，关联 OwlClass)
# ===================================================
class OwlClassAttribute(Base):
    __tablename__ = 'owl_class_attribute'

    owl_class_attribute_id = Column(Integer, primary_key=True, autoincrement=True)
    owl_class_attribute_name = Column(String(255), nullable=False)
    owl_class_attribute_range = Column(String(255), nullable=False)

    owl_class_id = Column(
        Integer,
        ForeignKey('owl_class.owl_class_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    def __repr__(self):
        return f"<OwlClassAttribute(name={self.owl_class_attribute_name})>"


# ===================================================
# 15. OwlClassBehavior (本体类的行为信息，关联 OwlClass)
# ===================================================
class OwlClassBehavior(Base):
    __tablename__ = 'owl_class_behavior'

    owl_class_behavior_id = Column(Integer, primary_key=True, autoincrement=True)
    owl_class_behavior_name = Column(String(255), nullable=False)
    owl_class_behavior_range = Column(String(255), nullable=False)

    owl_class_id = Column(
        Integer,
        ForeignKey('owl_class.owl_class_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    def __repr__(self):
        return f"<OwlClassBehavior(name={self.owl_class_behavior_name})>"


# ======================================
# 16. Bayes (存储贝叶斯网络信息，关联情景)
# ======================================
class Bayes(Base):
    __tablename__ = 'bayes'

    bayes_id = Column(Integer, primary_key=True, autoincrement=True)
    bayes_file_path = Column(String(255), nullable=False)
    scenario_id = Column(
        Integer,
        ForeignKey('scenario.scenario_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    def __repr__(self):
        return f"<Bayes(file_path={self.bayes_file_path})>"


# ==================================================
# 17. BayesNode (存储贝叶斯网络节点信息，关联 Bayes)
# ==================================================
class BayesNode(Base):
    __tablename__ = 'bayes_node'

    bayes_node_id = Column(Integer, primary_key=True, autoincrement=True)
    bayes_node_name = Column(String(255), nullable=False)

    bayes_id = Column(
        Integer,
        ForeignKey('bayes.bayes_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    def __repr__(self):
        return f"<BayesNode(name={self.bayes_node_name})>"


# =============================================================
# 18. BayesNodeState (存储贝叶斯节点状态及其先验概率，关联节点)
# =============================================================
class BayesNodeState(Base):
    __tablename__ = 'bayes_node_state'

    bayes_node_state_id = Column(Integer, primary_key=True, autoincrement=True)
    bayes_node_state_name = Column(String(255), nullable=False)
    bayes_node_state_prior_probability = Column(Float, nullable=False)

    bayes_node_id = Column(
        Integer,
        ForeignKey('bayes_node.bayes_node_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    def __repr__(self):
        return (
            f"<BayesNodeState(name={self.bayes_node_state_name}, "
            f"prior={self.bayes_node_state_prior_probability})>"
        )


# =============================================
# 19. BayesNodeTarget (贝叶斯节点多对多关联表)
# =============================================
class BayesNodeTarget(Base):
    __tablename__ = 'bayes_node_target'

    # 多对多时，使用复合主键
    source_node_id = Column(
        Integer,
        ForeignKey('bayes_node.bayes_node_id', ondelete='CASCADE'),
        primary_key=True
    )
    target_node_id = Column(
        Integer,
        ForeignKey('bayes_node.bayes_node_id', ondelete='CASCADE'),
        primary_key=True
    )

    def __repr__(self):
        return f"<BayesNodeTarget(source={self.source_node_id}, target={self.target_node_id})>"


# ===================================================
# 20. PosterioriData (存储后验信息, 关联BayesNodeState)
# ===================================================
class PosterioriData(Base):
    __tablename__ = 'posteriori_data'

    posteriori_data_id = Column(Integer, primary_key=True, autoincrement=True)
    posterior_probability = Column(Float, nullable=False)

    bayes_node_state_id = Column(
        Integer,
        ForeignKey('bayes_node_state.bayes_node_state_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    # plan_id 关联 element_id
    plan_id = Column(
        Integer,
        ForeignKey('element.element_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    def __repr__(self):
        return f"<PosterioriData(id={self.posteriori_data_id})>"


# ==================================
# 21. ElementBase (情景要素默认信息)
# ==================================
class ElementBase(Base):
    __tablename__ = 'element_base'

    element_base_id = Column(Integer, primary_key=True, autoincrement=True)
    element_base_name = Column(String(255), nullable=False)

    element_base_type_id = Column(
        Integer,
        ForeignKey('element_type.element_type_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    element_base_parent_id = Column(
        Integer,
        ForeignKey('element_base.element_base_id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )

    def __repr__(self):
        return f"<ElementBase(name={self.element_base_name})>"


# =======================================
# 22. AttributeBase (要素的默认属性)
# =======================================
class AttributeBase(Base):
    __tablename__ = 'attribute_base'

    attribute_base_id = Column(Integer, primary_key=True, autoincrement=True)
    attribute_base_name = Column(String(255), nullable=False)

    attribute_base_type_id = Column(
        Integer,
        ForeignKey('attribute_type.attribute_type_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    is_required = Column(Boolean, nullable=False, server_default=expression.true())
    is_multi_valued = Column(Boolean, nullable=False, server_default=expression.false())

    enum_value_id = Column(
        Integer,
        ForeignKey('enum_value.enum_value_id', ondelete='SET NULL'),
        nullable=True
    )
    attribute_base_value = Column(Text, nullable=True)

    element_base_id = Column(
        Integer,
        ForeignKey('element_base.element_base_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    def __repr__(self):
        return f"<AttributeBase(name={self.attribute_base_name})>"


# ========================================================
# 23. AttributeBaseAssociation (默认属性与默认要素的关联)
# ========================================================
class AttributeBaseAssociation(Base):
    __tablename__ = 'attribute_base_association'

    attribute_base_id = Column(
        Integer,
        ForeignKey('attribute_base.attribute_base_id', ondelete='CASCADE'),
        primary_key=True
    )
    associated_element_base_id = Column(
        Integer,
        ForeignKey('element_base.element_base_id', ondelete='CASCADE'),
        primary_key=True
    )

    def __repr__(self):
        return (
            f"<AttributeBaseAssociation(attr_base_id={self.attribute_base_id}, "
            f"elem_base_id={self.associated_element_base_id})>"
        )


# =======================================
# 24. BehaviorBase (默认的行为模型)
# =======================================
class BehaviorBase(Base):
    __tablename__ = 'behavior_base'

    behavior_base_id = Column(Integer, primary_key=True, autoincrement=True)
    behavior_base_name = Column(String(255), nullable=False)
    is_required = Column(Boolean, nullable=False, server_default=expression.true())

    object_type_id = Column(
        Integer,
        ForeignKey('element_type.element_type_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    is_multi_valued = Column(Boolean, nullable=False, server_default=expression.false())

    element_base_id = Column(
        Integer,
        ForeignKey('element_base.element_base_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    def __repr__(self):
        return f"<BehaviorBase(name={self.behavior_base_name})>"


# =======================================================
# 25. BehaviorBaseObject (默认行为对象，多对多)
# =======================================================
class BehaviorBaseObject(Base):
    __tablename__ = 'behavior_base_object'

    behavior_base_id = Column(
        Integer,
        ForeignKey('behavior_base.behavior_base_id', ondelete='CASCADE'),
        primary_key=True
    )
    object_element_base_id = Column(
        Integer,
        ForeignKey('element_base.element_base_id', ondelete='CASCADE'),
        primary_key=True
    )

    def __repr__(self):
        return (
            f"<BehaviorBaseObject(behavior_base_id={self.behavior_base_id}, "
            f"object_element_base_id={self.object_element_base_id})>"
        )