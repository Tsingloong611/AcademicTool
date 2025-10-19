# -*- coding: utf-8 -*-
# @Time    : 12/3/2024 10:06 AM
# @FileName: db_manager_config.py
# @Software: PyCharm
from sqlalchemy import create_engine
from sqlalchemy.dialects.mysql import pymysql
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine, text
from models.models import Base
from database import seed_data


class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None

    def connect(self, username, password, host, port, database):
        try:
            connection_string = f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}?charset=utf8mb4"
            self.engine = create_engine(connection_string, echo=False)

            # ✅ 设置 lc_messages
            with self.engine.connect() as connection:
                connection.execute(text("SET lc_messages = 'en_US'"))

            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

            # 创建所有表（如果尚未创建）
            Base.metadata.create_all(bind=self.engine)

            # 添加种子数据
            seed_data.seed_all(self.get_session())

            print("数据库连接成功")
            return True, "连接成功"
        except Exception as e:
            return False, str(e)

    def get_session(self):
        if self.SessionLocal:
            return self.SessionLocal()
        else:
            return None

    def get_connection_info(self):
        """
        使用 SQLAlchemy 查询数据库信息。
        返回一个字典包含用户名、主机、端口、数据库名。
        """
        info = {}
        if not self.engine:
            print("未连接到数据库")
            return None

        try:
            with self.engine.connect() as connection:
                # 获取当前用户
                user = connection.execute(text("SELECT USER();")).scalar()
                info['username'] = user
                # 获取当前数据库
                database = connection.execute(text("SELECT DATABASE();")).scalar()
                info['database'] = database
                # 获取服务器主机名
                hostname = connection.execute(text("SELECT @@hostname;")).scalar()
                info['host'] = hostname
                # 获取服务器端口
                port_result = connection.execute(text("SHOW VARIABLES LIKE 'port';")).fetchone()
                port = port_result[1] if port_result else None  # 使用索引 1 获取端口值
                info['port'] = port

                return info
        except Exception as e:
            print(f"获取连接信息失败: {e}")
            return None