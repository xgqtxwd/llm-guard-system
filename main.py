"""
敏感词检测和模型输出限制主程序
整合敏感词检测、LLM API调用和安全过滤功能
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from sensitive_word_detector import create_detector
from llm_api_client import create_api_client, SafeLLMClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('llm_guard.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class LLMGuardSystem:
    """LLM安全防护系统"""
    
    def __init__(self, config_file: str = "config.json"):
        """
        初始化LLM安全防护系统
        
        Args:
            config_file: 配置文件路径
        """
        self.config = self._load_config(config_file)
        
        # 初始化敏感词检测器
        detector_config = self.config.get("sensitive_detector", {})
        self.sensitive_detector = create_detector(detector_config)
        
        # 初始化API客户端
        api_config = self.config.get("api_client", {})
        self.api_client = create_api_client(api_config)
        
        # 初始化安全LLM客户端
        self.safe_client = SafeLLMClient(self.api_client, self.sensitive_detector)
        
        logger.info("LLM安全防护系统初始化完成")
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "sensitive_detector": {
                "sensitive_words_file": "sensitive_words.txt",
                "match_type": "str",
                "case_sensitive": False,
                "redact": True,
                "contains_all": False
            },
            "api_client": {
                "api_key": "sk-0255691784e8432b9f8f68350fb6ffbb",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "model": "qwen-plus",
                "max_tokens": 2000,
                "temperature": 0.7
            },
            "safety": {
                "check_input": True,
                "check_output": True,
                "log_blocked_requests": True
            }
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                # 合并配置
                for key, value in user_config.items():
                    if isinstance(value, dict) and key in default_config:
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
                logger.info(f"加载配置文件: {config_file}")
            except Exception as e:
                logger.warning(f"加载配置文件失败，使用默认配置: {e}")
        else:
            logger.info("使用默认配置")
        
        return default_config
    
    def process_request(self, user_input: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        处理用户请求
        
        Args:
            user_input: 用户输入
            system_prompt: 系统提示词
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        start_time = datetime.now()
        
        # 获取安全配置
        safety_config = self.config.get("safety", {})
        check_input = safety_config.get("check_input", True)
        check_output = safety_config.get("check_output", True)
        log_blocked = safety_config.get("log_blocked_requests", True)
        
        # 调用安全客户端
        result = self.safe_client.safe_chat(
            user_message=user_input,
            system_message=system_prompt,
            check_input=check_input,
            check_output=check_output
        )
        
        # 添加处理时间
        end_time = datetime.now()
        result["processing_time"] = (end_time - start_time).total_seconds()
        result["timestamp"] = end_time.isoformat()
        
        # 记录被阻止的请求
        if result.get("blocked") and log_blocked:
            self._log_blocked_request(user_input, result)
        
        return result
    
    def _log_blocked_request(self, user_input: str, result: Dict[str, Any]):
        """记录被阻止的请求"""
        log_entry = {
            "timestamp": result["timestamp"],
            "user_input": user_input[:100] + "..." if len(user_input) > 100 else user_input,
            "block_reason": result["block_reason"],
            "input_risk_score": result.get("input_risk_score", 0),
            "output_risk_score": result.get("output_risk_score", 0)
        }
        
        logger.warning(f"请求被阻止: {json.dumps(log_entry, ensure_ascii=False)}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        detector_stats = self.sensitive_detector.get_stats()
        api_info = self.api_client.get_model_info()
        
        return {
            "detector_stats": detector_stats,
            "api_info": api_info,
            "config": self.config
        }
    
    def interactive_mode(self):
        """交互模式"""
        print("=== LLM安全防护系统 ===")
        print("输入 'quit' 或 'exit' 退出")
        print("输入 'stats' 查看系统统计")
        print("输入 'help' 查看帮助")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\n用户: ").strip()
                
                if user_input.lower() in ['quit', 'exit']:
                    print("再见！")
                    break
                
                if user_input.lower() == 'stats':
                    stats = self.get_system_stats()
                    print(json.dumps(stats, indent=2, ensure_ascii=False))
                    continue
                
                if user_input.lower() == 'help':
                    print("可用命令:")
                    print("- quit/exit: 退出程序")
                    print("- stats: 查看系统统计")
                    print("- help: 显示帮助")
                    continue
                
                if not user_input:
                    continue
                
                # 处理请求
                result = self.process_request(user_input)
                
                # 显示结果
                print(f"\n助手: {result['response']}")
                
                # 显示安全信息（如果有风险）
                if not result['input_safe'] or not result['output_safe']:
                    print(f"\n⚠️ 安全提示:")
                    if not result['input_safe']:
                        print(f"  输入风险评分: {result['input_risk_score']:.2f}")
                    if not result['output_safe']:
                        print(f"  输出风险评分: {result['output_risk_score']:.2f}")
                
            except KeyboardInterrupt:
                print("\n\n程序被中断，再见！")
                break
            except Exception as e:
                logger.error(f"处理请求时出错: {e}")
                print(f"抱歉，处理您的请求时出现错误: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM安全防护系统")
    parser.add_argument("--config", default="config.json", help="配置文件路径")
    parser.add_argument("--interactive", action="store_true", help="启动交互模式")
    parser.add_argument("--input", help="直接处理输入文本")
    parser.add_argument("--system", help="系统提示词")
    
    args = parser.parse_args()
    
    try:
        # 初始化系统
        system = LLMGuardSystem(args.config)
        
        if args.interactive:
            # 交互模式
            system.interactive_mode()
        elif args.input:
            # 直接处理输入
            result = system.process_request(args.input, args.system)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            # 默认启动交互模式
            system.interactive_mode()
            
    except Exception as e:
        logger.error(f"系统启动失败: {e}")
        print(f"系统启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
