# -*- coding: utf-8 -*-
# @Time    : 12/5/2024 11:24 AM
# @FileName: server_manager.py
# @Software: PyCharm


import json
import os
import uuid
from typing import List, Dict, Any
from cryptography.fernet import Fernet
import logging

class ServerManager:
    def __init__(self, filename: str = "servers.json"):
        # 获取当前脚本的绝对路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建 data 目录的绝对路径
        self.filepath = os.path.join(script_dir, "..", "data", filename)
        print(f"Servers file path: {self.filepath}")  # 调试信息
        self.key = self.load_key()
        self.cipher = Fernet(self.key)
        self.servers = self.load_servers()

    def load_key(self) -> bytes:
        key_file = os.path.join(os.path.dirname(self.filepath), "secret.key")
        if not os.path.exists(key_file):
            key = Fernet.generate_key()
            try:
                with open(key_file, "wb") as f:
                    f.write(key)
                print(f"Generated encryption key and saved to {key_file}")
            except Exception as e:
                print(f"Error saving encryption key: {e}")
                raise
            return key
        else:
            try:
                with open(key_file, "rb") as f:
                    key = f.read()
                return key
            except Exception as e:
                print(f"Error loading encryption key: {e}")
                raise

    def load_servers(self) -> List[Dict[str, Any]]:
        directory = os.path.dirname(self.filepath)
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                print(f"Created directory: {directory}")
            except Exception as e:
                print(f"Error creating directory {directory}: {e}")
                return []

        if not os.path.exists(self.filepath):
            return []

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                servers = json.load(f)
            # 解密密码
            for server in servers:
                if server.get('save_password') and 'password' in server and server['password']:
                    server['password'] = self.cipher.decrypt(server['password'].encode()).decode()
            logging.info("Successfully loaded servers.")
            return servers
        except Exception as e:
            logging.error(f"Error loading servers: {e}")
            return []

    def save_servers(self):
        directory = os.path.dirname(self.filepath)
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                print(f"Created directory: {directory}")
            except Exception as e:
                print(f"Error creating directory {directory}: {e}")
                return

        try:
            # 加密密码
            servers_to_save = []
            for server in self.servers:
                server_copy = server.copy()
                if server_copy.get('save_password') and 'password' in server_copy and server_copy['password']:
                    server_copy['password'] = self.cipher.encrypt(server_copy['password'].encode()).decode()
                servers_to_save.append(server_copy)

            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(servers_to_save, f, indent=4, ensure_ascii=False)
            logging.info("Successfully saved servers.")
        except Exception as e:
            logging.error(f"Error saving servers: {e}")

    def add_server(self, server: Dict[str, Any]):
        server['id'] = str(uuid.uuid4())
        self.servers.append(server)
        self.save_servers()

    def update_server(self, server_id: str, updated_server: Dict[str, Any]):
        for server in self.servers:
            if server['id'] == server_id:
                # 如果密码被更新，进行加密
                if 'password' in updated_server:
                    server['password'] = updated_server['password']
                server.update(updated_server)
                self.save_servers()
                return True
        return False

    def delete_server(self, server_id: str):
        original_length = len(self.servers)
        self.servers = [s for s in self.servers if s['id'] != server_id]
        if len(self.servers) < original_length:
            self.save_servers()
            return True
        return False

    def get_server(self, server_id: str) -> Dict[str, Any]:
        for server in self.servers:
            if server['id'] == server_id:
                return server
        return {}

    def get_all_servers(self) -> List[Dict[str, Any]]:
        return self.servers