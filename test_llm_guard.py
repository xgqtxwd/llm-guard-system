"""
LLM安全防护系统测试用例
测试敏感词检测和模型输出限制功能
"""

import unittest
import os
import json
import tempfile
from unittest.mock import Mock, patch

from sensitive_word_detector import SensitiveWordDetector, create_detector
from llm_api_client import QwenAPIClient, SafeLLMClient, create_api_client
from main import LLMGuardSystem


class TestSensitiveWordDetector(unittest.TestCase):
    """敏感词检测器测试"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时敏感词文件
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8')
        test_words = ["敏感词1", "敏感词2", "不当内容", "违规词汇"]
        for word in test_words:
            self.temp_file.write(word + '\n')
        self.temp_file.close()
        
        self.detector = SensitiveWordDetector(
            sensitive_words_file=self.temp_file.name,
            redact=True
        )
    
    def tearDown(self):
        """清理测试环境"""
        os.unlink(self.temp_file.name)
    
    def test_load_sensitive_words(self):
        """测试敏感词加载"""
        self.assertEqual(len(self.detector.sensitive_words), 4)
        self.assertIn("敏感词1", self.detector.sensitive_words)
    
    def test_safe_text(self):
        """测试安全文本"""
        text = "这是一个正常的文本内容"
        sanitized, is_safe, risk = self.detector.scan(text)
        self.assertTrue(is_safe)
        self.assertEqual(risk, 0.0)
        self.assertEqual(sanitized, text)
    
    def test_unsafe_text(self):
        """测试包含敏感词的文本"""
        text = "这个文本包含敏感词1"
        sanitized, is_safe, risk = self.detector.scan(text)
        self.assertFalse(is_safe)
        self.assertGreater(risk, 0.0)
        self.assertIn("[REDACT]", sanitized)
    
    def test_multiple_sensitive_words(self):
        """测试包含多个敏感词的文本"""
        text = "这里有敏感词1和敏感词2"
        sanitized, is_safe, risk = self.detector.scan(text)
        self.assertFalse(is_safe)
        self.assertGreater(risk, 0.0)
    
    def test_case_insensitive(self):
        """测试大小写不敏感"""
        text = "这里有敏感词1的大写版本"
        sanitized, is_safe, risk = self.detector.scan(text)
        self.assertFalse(is_safe)
    
    def test_add_sensitive_words(self):
        """测试动态添加敏感词"""
        original_count = len(self.detector.sensitive_words)
        new_words = ["新敏感词", "另一个敏感词"]
        self.detector.add_sensitive_words(new_words)
        
        self.assertEqual(len(self.detector.sensitive_words), original_count + 2)
        
        # 测试新添加的敏感词是否生效
        text = "这里包含新敏感词"
        sanitized, is_safe, risk = self.detector.scan(text)
        self.assertFalse(is_safe)


class TestQwenAPIClient(unittest.TestCase):
    """通义千问API客户端测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.client = QwenAPIClient(
            api_key="test_key",
            base_url="https://test.api.com",
            model="test-model"
        )
    
    @patch('llm_api_client.OpenAI')
    def test_chat_completion(self, mock_openai):
        """测试聊天完成API"""
        # 模拟API响应
        mock_response = Mock()
        mock_response.id = "test_id"
        mock_response.object = "chat.completion"
        mock_response.created = 1234567890
        mock_response.model = "test-model"
        mock_response.choices = [Mock()]
        mock_response.choices[0].index = 0
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.content = "测试回复"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        messages = [{"role": "user", "content": "测试消息"}]
        result = self.client.chat_completion(messages)
        
        self.assertEqual(result["choices"][0]["message"]["content"], "测试回复")
        self.assertEqual(result["usage"]["total_tokens"], 15)
    
    @patch('llm_api_client.OpenAI')
    def test_simple_chat(self, mock_openai):
        """测试简单聊天接口"""
        # 模拟API响应
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "简单回复"
        
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        response = self.client.simple_chat("测试消息")
        self.assertEqual(response, "简单回复")


class TestSafeLLMClient(unittest.TestCase):
    """安全LLM客户端测试"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建模拟的API客户端
        self.mock_api_client = Mock()
        self.mock_api_client.simple_chat.return_value = "正常的模型回复"
        
        # 创建临时敏感词文件
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8')
        test_words = ["敏感词", "不当内容"]
        for word in test_words:
            self.temp_file.write(word + '\n')
        self.temp_file.close()
        
        # 创建敏感词检测器
        self.detector = SensitiveWordDetector(
            sensitive_words_file=self.temp_file.name,
            redact=True
        )
        
        # 创建安全客户端
        self.safe_client = SafeLLMClient(self.mock_api_client, self.detector)
    
    def tearDown(self):
        """清理测试环境"""
        os.unlink(self.temp_file.name)
    
    def test_safe_input_and_output(self):
        """测试安全的输入和输出"""
        result = self.safe_client.safe_chat("正常的用户输入")
        
        self.assertTrue(result["input_safe"])
        self.assertTrue(result["output_safe"])
        self.assertFalse(result["blocked"])
        self.assertEqual(result["response"], "正常的模型回复")
    
    def test_unsafe_input(self):
        """测试包含敏感词的输入"""
        result = self.safe_client.safe_chat("这个输入包含敏感词")
        
        self.assertFalse(result["input_safe"])
        self.assertTrue(result["blocked"])
        self.assertEqual(result["block_reason"], "输入包含敏感词")
    
    def test_unsafe_output(self):
        """测试模型输出包含敏感词"""
        # 模拟模型返回包含敏感词的内容
        self.mock_api_client.simple_chat.return_value = "这个回复包含敏感词"
        
        result = self.safe_client.safe_chat("正常输入")
        
        self.assertTrue(result["input_safe"])
        self.assertFalse(result["output_safe"])
        self.assertTrue(result["blocked"])
        self.assertEqual(result["block_reason"], "输出包含敏感词")


class TestLLMGuardSystem(unittest.TestCase):
    """LLM安全防护系统测试"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时配置文件
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        config = {
            "sensitive_detector": {
                "sensitive_words_file": "test_words.txt",
                "match_type": "str",
                "case_sensitive": False,
                "redact": True
            },
            "api_client": {
                "api_key": "test_key",
                "base_url": "https://test.api.com",
                "model": "test-model"
            },
            "safety": {
                "check_input": True,
                "check_output": True,
                "log_blocked_requests": True
            }
        }
        json.dump(config, self.temp_config)
        self.temp_config.close()
        
        # 创建临时敏感词文件
        self.temp_words = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        test_words = ["测试敏感词", "违规内容"]
        for word in test_words:
            self.temp_words.write(word + '\n')
        self.temp_words.close()
        
        # 更新配置中的敏感词文件路径
        with open(self.temp_config.name, 'r') as f:
            config = json.load(f)
        config["sensitive_detector"]["sensitive_words_file"] = self.temp_words.name
        with open(self.temp_config.name, 'w') as f:
            json.dump(config, f)
    
    def tearDown(self):
        """清理测试环境"""
        os.unlink(self.temp_config.name)
        os.unlink(self.temp_words.name)
    
    @patch('main.create_api_client')
    def test_system_initialization(self, mock_create_api):
        """测试系统初始化"""
        mock_api_client = Mock()
        mock_create_api.return_value = mock_api_client
        
        system = LLMGuardSystem(self.temp_config.name)
        
        self.assertIsNotNone(system.sensitive_detector)
        self.assertIsNotNone(system.api_client)
        self.assertIsNotNone(system.safe_client)
    
    @patch('main.create_api_client')
    def test_process_request(self, mock_create_api):
        """测试请求处理"""
        mock_api_client = Mock()
        mock_api_client.simple_chat.return_value = "正常回复"
        mock_create_api.return_value = mock_api_client
        
        system = LLMGuardSystem(self.temp_config.name)
        result = system.process_request("正常的用户输入")
        
        self.assertIn("response", result)
        self.assertIn("input_safe", result)
        self.assertIn("output_safe", result)
        self.assertIn("timestamp", result)
        self.assertIn("processing_time", result)


def run_integration_test():
    """运行集成测试"""
    print("=== 集成测试 ===")
    
    # 检查必要文件是否存在
    if not os.path.exists("sensitive_words.txt"):
        print("❌ 敏感词文件不存在")
        return False
    
    try:
        # 测试敏感词检测器
        print("测试敏感词检测器...")
        detector = create_detector()
        
        test_cases = [
            ("正常文本", True),
            ("这是正常的对话", True),
        ]
        
        for text, expected_safe in test_cases:
            _, is_safe, risk = detector.scan(text)
            status = "✅" if is_safe == expected_safe else "❌"
            print(f"{status} 文本: '{text}' - 安全: {is_safe}, 风险: {risk:.2f}")
        
        print("✅ 敏感词检测器测试完成")
        
        # 测试API客户端（不实际调用API）
        print("测试API客户端配置...")
        api_client = create_api_client()
        info = api_client.get_model_info()
        print(f"✅ API客户端配置: {info}")
        
        print("✅ 集成测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        return False


if __name__ == "__main__":
    # 运行单元测试
    print("=== 单元测试 ===")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # 运行集成测试
    print("\n" + "="*50)
    run_integration_test()
