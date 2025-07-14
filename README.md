# LLM安全防护系统

基于llm-guard开源库实现的敏感词检测和模型输出限制系统，支持通义千问API集成。

## 功能特性

- ✅ **敏感词检测**: 基于llm-guard的BanSubstrings扫描器，支持21930+中文敏感词
- ✅ **输入输出过滤**: 对用户输入和模型输出进行双重安全检查
- ✅ **通义千问集成**: 完整支持通义千问API调用
- ✅ **实时监控**: 详细的日志记录和风险评分
- ✅ **灵活配置**: 支持JSON配置文件和环境变量
- ✅ **交互模式**: 命令行交互界面，方便测试和使用

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置API密钥

编辑 `.env` 文件或 `config.json` 文件，设置您的通义千问API密钥：

```bash
# .env 文件
QWEN_API_KEY=your_api_key_here
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 3. 运行程序

#### 交互模式
```bash
python main.py --interactive
```

#### 直接处理文本
```bash
python main.py --input "您要检测的文本内容"
```

#### 使用自定义配置
```bash
python main.py --config custom_config.json --interactive
```

## 项目结构

```
llm-guard/
├── main.py                    # 主程序入口
├── sensitive_word_detector.py # 敏感词检测模块
├── llm_api_client.py         # LLM API客户端
├── test_llm_guard.py         # 测试用例
├── config.json               # 配置文件
├── .env                      # 环境变量
├── requirements.txt          # 依赖列表
├── sensitive_words.txt       # 敏感词列表
├── （4）拦截关键词列表.xlsx    # 原始敏感词Excel文件
└── README.md                 # 使用文档
```

## 配置说明

### config.json 配置文件

```json
{
  "sensitive_detector": {
    "sensitive_words_file": "sensitive_words.txt",
    "match_type": "str",           // "str" 或 "word"
    "case_sensitive": false,       // 是否区分大小写
    "redact": true,               // 是否用[REDACT]替换敏感词
    "contains_all": false         // 是否需要包含所有敏感词才触发
  },
  "api_client": {
    "api_key": "your_api_key",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "model": "qwen-plus",
    "max_tokens": 2000,
    "temperature": 0.7
  },
  "safety": {
    "check_input": true,          // 是否检查输入
    "check_output": true,         // 是否检查输出
    "log_blocked_requests": true  // 是否记录被阻止的请求
  }
}
```

## API使用示例

### 基础使用

```python
from main import LLMGuardSystem

# 初始化系统
system = LLMGuardSystem("config.json")

# 处理用户请求
result = system.process_request("用户输入的文本")

print(f"回复: {result['response']}")
print(f"输入安全: {result['input_safe']}")
print(f"输出安全: {result['output_safe']}")
```

### 敏感词检测器单独使用

```python
from sensitive_word_detector import create_detector

# 创建检测器
detector = create_detector()

# 检测文本
text = "待检测的文本内容"
sanitized, is_safe, risk_score = detector.scan(text)

print(f"原文: {text}")
print(f"安全: {is_safe}")
print(f"风险评分: {risk_score}")
print(f"处理后: {sanitized}")
```

### API客户端单独使用

```python
from llm_api_client import create_api_client

# 创建API客户端
client = create_api_client({
    "api_key": "your_api_key",
    "model": "qwen-plus"
})

# 简单聊天
response = client.simple_chat("你好，请介绍一下你自己")
print(response)
```

## 测试

运行测试用例：

```bash
python test_llm_guard.py
```

测试包括：
- 敏感词检测功能测试
- API客户端功能测试
- 安全防护系统集成测试

## 日志和监控

系统会自动记录以下信息：
- 敏感词检测结果
- API调用统计
- 被阻止的请求详情
- 系统运行状态

日志文件：`llm_guard.log`

## 性能优化

- 敏感词检测使用高效的字符串匹配算法
- 支持批量处理和异步调用
- 内存使用优化，适合长时间运行

## 安全特性

1. **双重检查**: 输入和输出都进行敏感词检测
2. **风险评分**: 量化安全风险等级
3. **内容替换**: 自动用[REDACT]替换敏感内容
4. **详细日志**: 完整记录安全事件
5. **灵活配置**: 可根据需求调整安全策略

## 常见问题

### Q: 如何添加自定义敏感词？
A: 编辑 `sensitive_words.txt` 文件，每行一个敏感词，或使用API动态添加。

### Q: 如何调整敏感词检测的严格程度？
A: 修改配置文件中的 `match_type`、`case_sensitive` 等参数。

### Q: 支持其他LLM模型吗？
A: 当前主要支持通义千问，可以扩展支持其他OpenAI兼容的API。

### Q: 如何处理误报？
A: 可以调整 `match_type` 为 "word" 模式，或者从敏感词列表中移除误报词汇。

## 许可证

本项目基于MIT许可证开源。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 联系方式

如有问题或建议，请通过GitHub Issues联系我们。
