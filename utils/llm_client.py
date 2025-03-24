# -*- coding: utf-8 -*-
# @Time    : 2025/3/21 12:16
# @FileName: llm_client.py
# @Software: PyCharm
# -*- coding: utf-8 -*-
# @Time    : 2025/3/21 12:16
# @FileName: llm_client.py
# @Software: PyCharm
import time
import json
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta

from PySide6.QtCore import QCoreApplication

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LLMClient")


class RateLimiter:
    """速率限制器，用于控制API请求频率"""

    def __init__(self, requests_per_minute: int, retry_attempts: int):
        self.requests_per_minute = requests_per_minute
        self.retry_attempts = retry_attempts
        self.request_timestamps = []
        self.last_request_time = None
        # 将在FallbackManager中设置，以便访问模型配置
        self.fallback_manager = None

    def wait_if_needed(self) -> bool:
        """
        检查是否需要等待以符合速率限制
        返回值: 是否允许继续请求
        """
        now = datetime.now()

        # 清理过期的时间戳（1分钟之前的）
        self.request_timestamps = [ts for ts in self.request_timestamps
                                   if now - ts < timedelta(minutes=1)]

        # 检查当前请求是否会超过每分钟限制
        if len(self.request_timestamps) >= self.requests_per_minute:
            oldest_allowed = now - timedelta(minutes=1)
            wait_time = (oldest_allowed - self.request_timestamps[0]).total_seconds() + 0.1
            logger.warning(f"达到速率限制（每分钟{self.requests_per_minute}次请求）。等待 {wait_time:.2f} 秒")
            time.sleep(max(0, wait_time))
            return self.wait_if_needed()  # 递归检查，确保等待后符合条件

        # 记录本次请求的时间戳
        self.request_timestamps.append(now)
        return True

    def get_retry_delay(self, attempt: int) -> float:
        """计算重试延迟时间，使用指数退避策略"""
        if attempt <= 0:
            return 0
        return min(2 ** (attempt - 1), 60)  # 最大等待60秒


class LLMClient(ABC):
    """基础LLM客户端抽象类"""

    def __init__(self, model_config: Dict[str, Any], rate_limiter: RateLimiter):
        self.model_name = model_config.get("model_name", "Unknown")
        self.provider = model_config.get("provider", "Unknown")
        self.api_key = model_config.get("model_api_key", "")
        self.endpoint = model_config.get("endpoint", "")
        self.parameters = model_config.get("parameters", {})
        self.rate_limiter = rate_limiter

    @abstractmethod
    def prepare_request(self, prompt: str) -> Dict[str, Any]:
        """准备API请求的数据，由子类实现"""
        pass

    @abstractmethod
    def parse_response(self, response_data: Dict[str, Any]) -> str:
        """解析API响应，由子类实现"""
        pass

    def send_request(self, prompt: str) -> Optional[str]:
        """发送请求到LLM API，处理重试和错误"""
        for attempt in range(self.rate_limiter.retry_attempts + 1):
            try:
                # 检查速率限制
                self.rate_limiter.wait_if_needed()

                # 准备请求
                request_data = self.prepare_request(prompt)
                headers = self.get_headers()

                # 发送请求
                logger.info(f"发送请求到 {self.model_name} ({self.provider})")
                response = requests.post(
                    self.endpoint,
                    headers=headers,
                    json=request_data,
                    timeout=30  # 30秒超时
                )

                # 检查响应状态
                response.raise_for_status()
                response_data = response.json()

                # 解析响应
                return self.parse_response(response_data)

            except requests.exceptions.RequestException as e:
                logger.error(f"请求错误 ({self.model_name}): {str(e)}")

                if attempt < self.rate_limiter.retry_attempts:
                    retry_delay = self.rate_limiter.get_retry_delay(attempt + 1)
                    logger.info(f"将在 {retry_delay} 秒后重试 (尝试 {attempt + 1}/{self.rate_limiter.retry_attempts})")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"达到最大重试次数 ({self.rate_limiter.retry_attempts})，放弃请求")
                    return None

        return None

    def get_headers(self) -> Dict[str, str]:
        """获取请求头，可由子类重写"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }


class OpenAIClient(LLMClient):
    """OpenAI API 客户端"""

    def prepare_request(self, prompt: str) -> Dict[str, Any]:
        # 使用模型配置中指定的model_version
        model_version = None
        for model_config in self.rate_limiter.fallback_manager.model_configs:
            if model_config.get("model_name") == self.model_name:
                model_version = model_config.get("model_version", "gpt-3.5-turbo")
                break

        request_data = {
            "model": model_version,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": self.parameters.get("temperature", 0.7),
            "max_tokens": self.parameters.get("max_tokens", 2000),
            "top_p": self.parameters.get("top_p", 1.0)
        }
        return request_data

    def parse_response(self, response_data: Dict[str, Any]) -> str:
        try:
            message = response_data.get("choices", [{}])[0].get("message", {})
            content = message.get("content", "")
            return content
        except (KeyError, IndexError) as e:
            logger.error(f"解析OpenAI响应时出错: {str(e)}")
            return "解析响应时出错"


class AnthropicClient(LLMClient):
    """Anthropic API 客户端"""

    def get_headers(self) -> Dict[str, str]:
        """Anthropic API使用x-api-key而非Bearer认证"""
        return {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"  # 使用适当的API版本
        }

    def prepare_request(self, prompt: str) -> Dict[str, Any]:
        # 使用模型配置中指定的model_version
        model_version = None
        for model_config in self.rate_limiter.fallback_manager.model_configs:
            if model_config.get("model_name") == self.model_name:
                model_version = model_config.get("model_version", "claude-3-sonnet-20240229")
                break

        request_data = {
            "model": model_version,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.parameters.get("max_tokens", 1500),
            "temperature": self.parameters.get("temperature", 0.5)
        }
        return request_data

    def parse_response(self, response_data: Dict[str, Any]) -> str:
        try:
            content = response_data.get("content", [{}])[0].get("text", "")
            return content
        except (KeyError, IndexError) as e:
            logger.error(f"解析Anthropic响应时出错: {str(e)}")
            return "解析响应时出错"


class DeepSeekClient(LLMClient):
    """DeepSeek API 客户端"""

    def get_headers(self) -> Dict[str, str]:
        """DeepSeek API使用Bearer认证"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def prepare_request(self, prompt: str) -> Dict[str, Any]:
        # 使用模型配置中指定的model_version
        model_version = None
        for model_config in self.rate_limiter.fallback_manager.model_configs:
            if model_config.get("model_name") == self.model_name:
                model_version = model_config.get("model_version", "deepseek-chat")
                break

        request_data = {
            "model": model_version,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.parameters.get("max_tokens", 1500),
            "temperature": self.parameters.get("temperature", 0.5),
            "top_p": self.parameters.get("top_p", 1.0)
        }
        return request_data

    def parse_response(self, response_data: Dict[str, Any]) -> str:
        try:
            # 根据DeepSeek API的响应格式解析
            content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return content
        except (KeyError, IndexError) as e:
            logger.error(f"解析DeepSeek响应时出错: {str(e)}")
            return "解析响应时出错"


class FallbackManager:
    """处理LLM请求的故障转移策略"""

    def __init__(self, config: Dict[str, Any]):
        self.model_configs = config.get("model_list", [])
        self.fallback_policy = config.get("fallback_policy", "sequential")
        self.rate_limiter = RateLimiter(
            config.get("rate_limit", {}).get("requests_per_minute", 60),
            config.get("rate_limit", {}).get("retry_attempts", 3)
        )
        # 添加对FallbackManager的引用，以便在客户端中访问模型配置
        self.rate_limiter.fallback_manager = self
        self.clients = self._create_clients()

    def _create_clients(self) -> Dict[str, LLMClient]:
        """创建所有可用的LLM客户端"""
        clients = {}
        for model_config in self.model_configs:
            model_name = model_config.get("model_name")
            provider = model_config.get("provider", "").lower()

            if provider == "openai":
                clients[model_name] = OpenAIClient(model_config, self.rate_limiter)
            elif provider == "anthropic":
                clients[model_name] = AnthropicClient(model_config, self.rate_limiter)
            elif provider == "deepseek":
                clients[model_name] = DeepSeekClient(model_config, self.rate_limiter)
            else:
                logger.warning(f"不支持的提供商: {provider}")

        return clients

    def get_client(self, model_name: str) -> Optional[LLMClient]:
        """获取指定模型的客户端"""
        return self.clients.get(model_name)

    def get_response_with_fallback(self, model_name: str, prompt: str) -> Optional[str]:
        """
        使用故障转移策略获取响应
        如果指定的模型失败，将尝试其他可用模型
        """
        # 首先尝试指定的模型
        client = self.get_client(model_name)
        if client:
            response = client.send_request(prompt)
            if response:
                return response

            # 如果指定模型失败且启用了顺序故障转移
            if self.fallback_policy.lower() == "sequential":
                logger.info(f"主要模型 {model_name} 失败，尝试故障转移")

                # 尝试其他模型
                for fallback_model, fallback_client in self.clients.items():
                    if fallback_model != model_name:
                        logger.info(f"尝试故障转移到 {fallback_model}")
                        response = fallback_client.send_request(prompt)
                        if response:
                            logger.info(f"故障转移到 {fallback_model} 成功")
                            translated_template = QCoreApplication.translate(self.__class__.__name__,
                                                                             "[使用备选模型 {0} - 原模型不可用]\n\n{1}")
                            return translated_template.format(fallback_model, response)
                logger.error("所有模型都失败")
                return QCoreApplication.translate(self.__class__.__name__,"抱歉，所有可用的AI模型当前都无法响应。请稍后再试。")
        else:
            logger.error(f"找不到指定的模型: {model_name}")
            return None

        return None