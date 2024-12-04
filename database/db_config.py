# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:06 AM
# @FileName: db_config.py
# @Software: PyCharm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 数据库配置
DB_USERNAME = 'Tsing_loong'
DB_PASSWORD = '12345678'
DB_HOST = 'localhost'
DB_PORT = '3306'
DB_NAME = 'test'

DATABASE_URL = f"mysql+mysqlconnector://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# 创建数据库引擎
engine = create_engine(DATABASE_URL, echo=True)

# 创建会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基类
Base = declarative_base()