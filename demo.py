"""
LLM安全防护系统演示脚本
展示敏感词检测和模型输出限制功能
"""

import json
import time
from main import LLMGuardSystem
from sensitive_word_detector import create_detector

def print_separator(title=""):
    """打印分隔线"""
    print("\n" + "="*60)
    if title:
        print(f" {title} ")
        print("="*60)

def print_result(result, show_details=True):
    """格式化打印结果"""
    print(f"🤖 助手回复: {result['response']}")
    
    if show_details:
        print(f"\n📊 安全检查结果:")
        print(f"   输入安全: {'✅' if result['input_safe'] else '❌'}")
        print(f"   输出安全: {'✅' if result['output_safe'] else '❌'}")
        print(f"   输入风险评分: {result['input_risk_score']:.2f}")
        print(f"   输出风险评分: {result['output_risk_score']:.2f}")
        print(f"   处理时间: {result['processing_time']:.2f}秒")
        
        if result['blocked']:
            print(f"   🚫 阻止原因: {result['block_reason']}")

def demo_basic_functionality():
    """演示基本功能"""
    print_separator("基本功能演示")
    
    # 初始化系统
    print("🚀 正在初始化LLM安全防护系统...")
    system = LLMGuardSystem()
    print("✅ 系统初始化完成！")
    
    # 测试正常对话
    print("\n📝 测试1: 正常对话")
    print("👤 用户: 你好，请介绍一下你自己")
    result = system.process_request("你好，请介绍一下你自己")
    print_result(result, show_details=False)
    
    # 测试技术问题
    print("\n📝 测试2: 技术问题")
    print("👤 用户: 请解释一下什么是机器学习")
    result = system.process_request("请解释一下什么是机器学习")
    print_result(result, show_details=False)

def demo_sensitive_word_detection():
    """演示敏感词检测功能"""
    print_separator("敏感词检测演示")
    
    # 创建检测器
    detector = create_detector()
    
    # 测试用例
    test_cases = [
        "这是一个正常的文本内容",
        "今天天气很好，适合出门",
        "我喜欢学习编程和技术",
        "请帮我写一个Python程序"
    ]
    
    print("🔍 测试敏感词检测功能:")
    for i, text in enumerate(test_cases, 1):
        print(f"\n📝 测试{i}: {text}")
        sanitized, is_safe, risk_score = detector.scan(text)
        
        status = "✅ 安全" if is_safe else "❌ 包含敏感词"
        print(f"   结果: {status}")
        print(f"   风险评分: {risk_score:.2f}")
        if not is_safe:
            print(f"   处理后: {sanitized}")

def demo_system_stats():
    """演示系统统计信息"""
    print_separator("系统统计信息")
    
    system = LLMGuardSystem()
    stats = system.get_system_stats()
    
    print("📊 系统配置和统计:")
    print(f"   敏感词总数: {stats['detector_stats']['total_sensitive_words']}")
    print(f"   匹配模式: {stats['detector_stats']['match_type']}")
    print(f"   区分大小写: {stats['detector_stats']['case_sensitive']}")
    print(f"   自动替换: {stats['detector_stats']['redact']}")
    print(f"   使用模型: {stats['api_info']['model']}")
    print(f"   最大Token: {stats['api_info']['max_tokens']}")
    print(f"   温度参数: {stats['api_info']['temperature']}")

def demo_interactive_mode():
    """演示交互模式"""
    print_separator("交互模式演示")
    
    print("🎮 启动交互模式演示...")
    print("💡 提示: 输入 'quit' 退出演示")
    
    system = LLMGuardSystem()
    
    # 预设一些演示对话
    demo_conversations = [
        "你能帮我写一首关于春天的诗吗？",
        "请解释一下区块链技术的原理",
        "如何学习Python编程？",
        "quit"
    ]
    
    for conversation in demo_conversations:
        print(f"\n👤 用户: {conversation}")
        
        if conversation.lower() == 'quit':
            print("👋 演示结束，感谢使用！")
            break
        
        # 模拟用户输入延迟
        time.sleep(1)
        
        result = system.process_request(conversation)
        print_result(result, show_details=True)
        
        # 添加一些延迟使演示更自然
        time.sleep(2)

def demo_configuration():
    """演示配置功能"""
    print_separator("配置功能演示")
    
    print("⚙️ 当前配置文件内容:")
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(json.dumps(config, indent=2, ensure_ascii=False))
        
        print("\n💡 配置说明:")
        print("   - sensitive_detector: 敏感词检测器配置")
        print("   - api_client: API客户端配置")
        print("   - safety: 安全检查配置")
        
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")

def main():
    """主演示函数"""
    print("🎉 欢迎使用LLM安全防护系统演示程序！")
    print("📋 本演示将展示以下功能:")
    print("   1. 基本对话功能")
    print("   2. 敏感词检测")
    print("   3. 系统统计信息")
    print("   4. 配置功能")
    print("   5. 交互模式")
    
    try:
        # 1. 基本功能演示
        demo_basic_functionality()
        
        # 2. 敏感词检测演示
        demo_sensitive_word_detection()
        
        # 3. 系统统计演示
        demo_system_stats()
        
        # 4. 配置演示
        demo_configuration()
        
        # 5. 交互模式演示
        demo_interactive_mode()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        print("💡 请检查配置文件和网络连接")
    
    print_separator("演示结束")
    print("🎯 演示完成！")
    print("📚 更多信息请查看 README.md 文档")
    print("🔧 如需自定义配置，请编辑 config.json 文件")

if __name__ == "__main__":
    main()
