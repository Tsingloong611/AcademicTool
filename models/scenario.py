# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:07 AM
# @FileName: scenario.py
# @Software: PyCharm
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from database.db_config import Base

class Scenario(Base):
    __tablename__ = 'scenarios'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default='Inactive')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Scenario(id={self.id}, name='{self.name}', status='{self.status}')>"