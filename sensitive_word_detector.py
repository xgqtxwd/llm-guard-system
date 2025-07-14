"""
敏感词检测模块
基于llm-guard的BanSubstrings扫描器实现敏感词检测功能
"""

import os
import logging
from typing import List, Tuple, Optional
from llm_guard.input_scanners import BanSubstrings
from llm_guard.input_scanners.ban_substrings import MatchType

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SensitiveWordDetector:
    """敏感词检测器"""
    
    def __init__(self, 
                 sensitive_words_file: str = "sensitive_words.txt",
                 match_type: MatchType = MatchType.STR,
                 case_sensitive: bool = False,
                 redact: bool = True,
                 contains_all: bool = False):
        """
        初始化敏感词检测器
        
        Args:
            sensitive_words_file: 敏感词文件路径
            match_type: 匹配类型 (STR: 字符串级别, WORD: 单词级别)
            case_sensitive: 是否区分大小写
            redact: 是否在输出中用[REDACT]替换敏感词
            contains_all: 是否需要包含所有敏感词才触发
        """
        self.sensitive_words_file = sensitive_words_file
        self.match_type = match_type
        self.case_sensitive = case_sensitive
        self.redact = redact
        self.contains_all = contains_all
        
        # 加载敏感词列表
        self.sensitive_words = self._load_sensitive_words()
        
        # 初始化BanSubstrings扫描器
        self.scanner = BanSubstrings(
            substrings=self.sensitive_words,
            match_type=self.match_type,
            case_sensitive=self.case_sensitive,
            redact=self.redact,
            contains_all=self.contains_all
        )
        
        logger.info(f"敏感词检测器初始化完成，加载了 {len(self.sensitive_words)} 个敏感词")
    
    def _load_sensitive_words(self) -> List[str]:
        """从文件加载敏感词列表"""
        if not os.path.exists(self.sensitive_words_file):
            logger.error(f"敏感词文件不存在: {self.sensitive_words_file}")
            return []
        
        try:
            with open(self.sensitive_words_file, 'r', encoding='utf-8') as f:
                words = [line.strip() for line in f if line.strip()]
            logger.info(f"成功加载 {len(words)} 个敏感词")
            return words
        except Exception as e:
            logger.error(f"加载敏感词文件失败: {e}")
            return []
    
    def scan(self, text: str) -> Tuple[str, bool, float]:
        """
        扫描文本中的敏感词
        
        Args:
            text: 待检测的文本
            
        Returns:
            Tuple[str, bool, float]: (处理后的文本, 是否通过检测, 风险评分)
        """
        if not text:
            return text, True, 0.0
        
        try:
            sanitized_text, is_valid, risk_score = self.scanner.scan(text)
            
            if not is_valid:
                logger.warning(f"检测到敏感词，风险评分: {risk_score}")
                logger.debug(f"原文本: {text[:100]}...")
                logger.debug(f"处理后: {sanitized_text[:100]}...")
            
            return sanitized_text, is_valid, risk_score
            
        except Exception as e:
            logger.error(f"敏感词扫描失败: {e}")
            return text, False, 1.0
    
    def is_safe(self, text: str) -> bool:
        """
        简单检查文本是否安全（不包含敏感词）
        
        Args:
            text: 待检测的文本
            
        Returns:
            bool: True表示安全，False表示包含敏感词
        """
        _, is_valid, _ = self.scan(text)
        return is_valid
    
    def get_sanitized_text(self, text: str) -> str:
        """
        获取清理后的文本（敏感词被替换为[REDACT]）
        
        Args:
            text: 待处理的文本
            
        Returns:
            str: 清理后的文本
        """
        sanitized_text, _, _ = self.scan(text)
        return sanitized_text
    
    def add_sensitive_words(self, words: List[str]) -> None:
        """
        动态添加敏感词
        
        Args:
            words: 要添加的敏感词列表
        """
        self.sensitive_words.extend(words)
        
        # 重新初始化扫描器
        self.scanner = BanSubstrings(
            substrings=self.sensitive_words,
            match_type=self.match_type,
            case_sensitive=self.case_sensitive,
            redact=self.redact,
            contains_all=self.contains_all
        )
        
        logger.info(f"添加了 {len(words)} 个敏感词，当前总数: {len(self.sensitive_words)}")
    
    def get_stats(self) -> dict:
        """获取检测器统计信息"""
        return {
            "total_sensitive_words": len(self.sensitive_words),
            "match_type": self.match_type.value,
            "case_sensitive": self.case_sensitive,
            "redact": self.redact,
            "contains_all": self.contains_all
        }


def create_detector(config: Optional[dict] = None) -> SensitiveWordDetector:
    """
    创建敏感词检测器的工厂函数
    
    Args:
        config: 配置字典
        
    Returns:
        SensitiveWordDetector: 敏感词检测器实例
    """
    if config is None:
        config = {}
    
    return SensitiveWordDetector(
        sensitive_words_file=config.get("sensitive_words_file", "sensitive_words.txt"),
        match_type=MatchType.STR if config.get("match_type", "str") == "str" else MatchType.WORD,
        case_sensitive=config.get("case_sensitive", False),
        redact=config.get("redact", True),
        contains_all=config.get("contains_all", False)
    )


if __name__ == "__main__":
    # 测试代码
    detector = create_detector()
    
    # 测试文本
    test_texts = [
        "这是一个正常的文本",
        "这个文本包含一些不当内容",
        "校园生活很美好",
        "今天天气不错"
    ]
    
    print("=== 敏感词检测测试 ===")
    for text in test_texts:
        sanitized, is_safe, risk = detector.scan(text)
        print(f"原文: {text}")
        print(f"安全: {is_safe}, 风险: {risk:.2f}")
        print(f"处理后: {sanitized}")
        print("-" * 50)
    
    # 显示统计信息
    print("=== 检测器统计信息 ===")
    stats = detector.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
