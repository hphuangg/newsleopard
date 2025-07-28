"""Claude API 客戶端實作（預留）"""

import json
import asyncio
from typing import Dict, Any

from .base import AIClientBase
from app.core.config import settings
from app.core.exceptions import (
    AIServiceException,
    create_configuration_error,
    create_ai_invalid_response_error
)
from app.services.prompts import build_analysis_prompt


class ClaudeClient(AIClientBase):
    """Claude API 客戶端（預留實作）"""
    
    def __init__(self):
        claude_settings = settings.ai.claude
        
        if not claude_settings.api_key:
            raise create_configuration_error("Claude API Key")
        
        super().__init__(
            model=claude_settings.model,
            max_tokens=claude_settings.max_tokens,
            temperature=claude_settings.temperature
        )
        
        # TODO: 初始化 Claude 客戶端
        # self.client = AnthropicClient(api_key=claude_settings.api_key)
        self.timeout = claude_settings.timeout
        self.max_retries = claude_settings.max_retries
    
    async def analyze_content(
        self, 
        content: str, 
        target_audience: str, 
        send_scenario: str,
        max_retries: int = None
    ) -> Dict[str, Any]:
        """使用 Claude API 分析文案內容（預留實作）"""
        
        # TODO: 實作 Claude API 呼叫
        raise AIServiceException(
            code="AI_SERVICE_UNAVAILABLE",
            message="Claude 客戶端尚未實作，請使用 OpenAI"
        )
    
    def validate_analysis_result(self, result: Dict[str, Any]) -> None:
        """驗證 Claude 分析結果格式"""
        # 與 OpenAI 使用相同的驗證邏輯
        required_fields = [
            "attractiveness", "readability", "line_compatibility", 
            "overall_score", "sentiment", "suggestions"
        ]
        
        for field in required_fields:
            if field not in result:
                raise create_ai_invalid_response_error(f"缺少必要欄位: {field}")
        
        # 驗證評分範圍 (1-10)
        score_fields = ["attractiveness", "readability", "line_compatibility", "overall_score"]
        for field in score_fields:
            value = result[field]
            if not isinstance(value, (int, float)) or not (1 <= value <= 10):
                raise create_ai_invalid_response_error(f"評分欄位 {field} 格式錯誤: {value}")
        
        # 驗證建議是陣列且非空
        suggestions = result.get("suggestions", [])
        if not isinstance(suggestions, list) or len(suggestions) == 0:
            raise create_ai_invalid_response_error("建議欄位格式錯誤或為空")