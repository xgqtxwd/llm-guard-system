"""
LLM API客户端模块
集成通义千问API，实现模型调用和响应处理
"""

import os
import logging
from typing import Dict, List, Optional, Any
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QwenAPIClient:
    """通义千问API客户端"""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 model: str = "qwen-plus",
                 max_tokens: int = 2000,
                 temperature: float = 0.7):
        """
        初始化API客户端
        
        Args:
            api_key: API密钥
            base_url: API基础URL
            model: 模型名称
            max_tokens: 最大token数
            temperature: 温度参数
        """
        self.api_key = api_key or os.getenv("QWEN_API_KEY", "sk-0255691784e8432b9f8f68350fb6ffbb")
        self.base_url = base_url or os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # 初始化OpenAI客户端（兼容通义千问API）
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        logger.info(f"通义千问API客户端初始化完成，模型: {self.model}")
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       **kwargs) -> Dict[str, Any]:
        """
        调用聊天完成API
        
        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "..."}]
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: API响应
        """
        try:
            # 合并参数
            params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                **kwargs
            }
            
            logger.debug(f"发送API请求: {params}")
            
            # 调用API
            response = self.client.chat.completions.create(**params)
            
            # 转换为字典格式
            result = {
                "id": response.id,
                "object": response.object,
                "created": response.created,
                "model": response.model,
                "choices": [
                    {
                        "index": choice.index,
                        "message": {
                            "role": choice.message.role,
                            "content": choice.message.content
                        },
                        "finish_reason": choice.finish_reason
                    }
                    for choice in response.choices
                ],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if response.usage else None
            }
            
            logger.info(f"API调用成功，使用token: {result.get('usage', {}).get('total_tokens', 'N/A')}")
            return result
            
        except Exception as e:
            logger.error(f"API调用失败: {e}")
            raise
    
    def simple_chat(self, user_message: str, system_message: Optional[str] = None) -> str:
        """
        简单聊天接口
        
        Args:
            user_message: 用户消息
            system_message: 系统消息（可选）
            
        Returns:
            str: 模型回复
        """
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.chat_completion(messages)
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"简单聊天失败: {e}")
            return f"抱歉，处理您的请求时出现错误: {str(e)}"
    
    def stream_chat(self, messages: List[Dict[str, str]], **kwargs):
        """
        流式聊天接口
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Yields:
            str: 流式响应内容
        """
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "stream": True,
                **kwargs
            }
            
            stream = self.client.chat.completions.create(**params)
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"流式聊天失败: {e}")
            yield f"抱歉，处理您的请求时出现错误: {str(e)}"
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "base_url": self.base_url
        }


class SafeLLMClient:
    """安全的LLM客户端，集成敏感词检测"""
    
    def __init__(self, 
                 api_client: QwenAPIClient,
                 sensitive_detector=None):
        """
        初始化安全LLM客户端
        
        Args:
            api_client: API客户端
            sensitive_detector: 敏感词检测器
        """
        self.api_client = api_client
        self.sensitive_detector = sensitive_detector
        
        logger.info("安全LLM客户端初始化完成")
    
    def safe_chat(self, 
                  user_message: str, 
                  system_message: Optional[str] = None,
                  check_input: bool = True,
                  check_output: bool = True) -> Dict[str, Any]:
        """
        安全聊天接口，包含输入输出敏感词检测
        
        Args:
            user_message: 用户消息
            system_message: 系统消息
            check_input: 是否检查输入
            check_output: 是否检查输出
            
        Returns:
            Dict[str, Any]: 包含响应和安全检查结果的字典
        """
        result = {
            "original_input": user_message,
            "input_safe": True,
            "input_risk_score": 0.0,
            "sanitized_input": user_message,
            "response": "",
            "output_safe": True,
            "output_risk_score": 0.0,
            "sanitized_output": "",
            "blocked": False,
            "block_reason": ""
        }
        
        # 检查输入
        if check_input and self.sensitive_detector:
            sanitized_input, input_safe, input_risk = self.sensitive_detector.scan(user_message)
            result.update({
                "input_safe": input_safe,
                "input_risk_score": input_risk,
                "sanitized_input": sanitized_input
            })
            
            if not input_safe:
                result.update({
                    "blocked": True,
                    "block_reason": "输入包含敏感词",
                    "response": "抱歉，您的输入包含不当内容，无法处理。"
                })
                logger.warning(f"输入被阻止，风险评分: {input_risk}")
                return result
        
        # 调用模型
        try:
            response = self.api_client.simple_chat(user_message, system_message)
            result["response"] = response
            
            # 检查输出
            if check_output and self.sensitive_detector:
                sanitized_output, output_safe, output_risk = self.sensitive_detector.scan(response)
                result.update({
                    "output_safe": output_safe,
                    "output_risk_score": output_risk,
                    "sanitized_output": sanitized_output
                })
                
                if not output_safe:
                    result.update({
                        "blocked": True,
                        "block_reason": "输出包含敏感词",
                        "response": "抱歉，模型生成的内容包含不当信息，已被过滤。",
                        "sanitized_output": sanitized_output
                    })
                    logger.warning(f"输出被过滤，风险评分: {output_risk}")
            
        except Exception as e:
            result.update({
                "blocked": True,
                "block_reason": f"API调用失败: {str(e)}",
                "response": "抱歉，服务暂时不可用，请稍后重试。"
            })
            logger.error(f"API调用失败: {e}")
        
        return result


def create_api_client(config: Optional[Dict[str, Any]] = None) -> QwenAPIClient:
    """
    创建API客户端的工厂函数
    
    Args:
        config: 配置字典
        
    Returns:
        QwenAPIClient: API客户端实例
    """
    if config is None:
        config = {}
    
    return QwenAPIClient(
        api_key=config.get("api_key"),
        base_url=config.get("base_url"),
        model=config.get("model", "qwen-plus"),
        max_tokens=config.get("max_tokens", 2000),
        temperature=config.get("temperature", 0.7)
    )


if __name__ == "__main__":
    # 测试代码
    client = create_api_client()
    
    # 测试简单聊天
    print("=== API客户端测试 ===")
    response = client.simple_chat("你好，请介绍一下你自己")
    print(f"模型回复: {response}")
    
    # 显示模型信息
    print("\n=== 模型信息 ===")
    info = client.get_model_info()
    for key, value in info.items():
        print(f"{key}: {value}")
