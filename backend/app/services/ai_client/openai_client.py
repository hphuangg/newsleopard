"""OpenAI API 客戶端實作"""

import json
import asyncio
from typing import Dict, Any
from openai import AsyncOpenAI

from .base import AIClientBase
from app.core.config import settings
from app.core.exceptions import (
    AIServiceException, 
    create_ai_rate_limit_error,
    create_ai_quota_exceeded_error, 
    create_ai_invalid_response_error,
    create_configuration_error
)
from app.services.prompts import build_analysis_prompt, SYSTEM_PROMPT


class OpenAIClient(AIClientBase):
    """OpenAI API 客戶端"""
    
    def __init__(self):
        openai_settings = settings.ai.openai
        
        if not openai_settings.api_key:
            raise create_configuration_error("OpenAI API Key")
        
        super().__init__(
            model=openai_settings.model,
            max_tokens=openai_settings.max_tokens,
            temperature=openai_settings.temperature
        )
        
        self.client = AsyncOpenAI(
            api_key=openai_settings.api_key,
            organization=openai_settings.organization
        )
        self.timeout = openai_settings.timeout
        self.max_retries = openai_settings.max_retries
    
    async def analyze_content(
        self, 
        content: str, 
        target_audience: str, 
        send_scenario: str,
        max_retries: int = None
    ) -> Dict[str, Any]:
        """使用 OpenAI API 分析文案內容"""
        
        max_retries = max_retries or self.max_retries
        prompt = build_analysis_prompt(content, target_audience, send_scenario)
        
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    response_format={"type": "json_object"},
                    timeout=self.timeout
                )
                
                # 解析回應
                content_text = response.choices[0].message.content
                if not content_text:
                    raise create_ai_invalid_response_error("AI 回應內容為空")
                
                result = json.loads(content_text)
                
                # 驗證回應格式
                self.validate_analysis_result(result)
                
                return result
                
            except json.JSONDecodeError as e:
                if attempt == max_retries - 1:
                    raise create_ai_invalid_response_error(f"JSON 解析失敗: {e}")
                await asyncio.sleep(1)
                
            except Exception as e:
                error_str = str(e).lower()
                
                if "rate_limit" in error_str:
                    retry_after = self._extract_retry_after(str(e))
                    raise create_ai_rate_limit_error(retry_after)
                elif "insufficient_quota" in error_str or "quota" in error_str:
                    raise create_ai_quota_exceeded_error()
                elif attempt == max_retries - 1:
                    raise AIServiceException(
                        code="AI_NETWORK_ERROR",
                        message=f"OpenAI API 呼叫失敗: {e}"
                    )
                
                # 指數退避重試
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
        
        raise AIServiceException(
            code="AI_SERVICE_UNAVAILABLE",
            message="OpenAI 服務多次重試後仍然失敗"
        )
    
    def validate_analysis_result(self, result: Dict[str, Any]) -> None:
        """驗證 OpenAI 分析結果格式"""
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
    
    def _extract_retry_after(self, error_message: str) -> int:
        """從錯誤訊息中提取重試間隔"""
        # 簡單的重試間隔提取邏輯
        import re
        match = re.search(r'retry after (\d+)', error_message)
        if match:
            return int(match.group(1))
        return 60  # 預設 60 秒