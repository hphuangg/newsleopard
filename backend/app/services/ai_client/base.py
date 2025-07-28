"""AI 客戶端抽象基類"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class AIClientBase(ABC):
    """AI 客戶端抽象基類"""
    
    def __init__(self, model: str, max_tokens: int = 1000, temperature: float = 0.3):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
    
    @abstractmethod
    async def analyze_content(
        self, 
        content: str, 
        target_audience: str, 
        send_scenario: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """分析文案內容
        
        Args:
            content: 文案內容
            target_audience: 目標受眾
            send_scenario: 發送場景
            max_retries: 最大重試次數
            
        Returns:
            分析結果字典，包含評分和建議
            
        Raises:
            AIServiceException: AI 服務相關錯誤
        """
        pass
    
    @abstractmethod
    def validate_analysis_result(self, result: Dict[str, Any]) -> None:
        """驗證分析結果格式
        
        Args:
            result: AI 回傳的分析結果
            
        Raises:
            AIServiceException: 結果格式錯誤
        """
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """獲取模型資訊"""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }