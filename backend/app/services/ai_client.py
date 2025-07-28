"""AI 客戶端 - 處理與 AI 服務的串接"""

import json
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
import asyncio
from app.core.config import settings


class AIAnalysisError(Exception):
    """AI 分析相關的錯誤"""
    pass


class OpenAIClient:
    """OpenAI API 客戶端"""
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise AIAnalysisError("OPENAI_API_KEY 未設定在環境變數中")
        
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
    
    def _build_analysis_prompt(
        self, 
        content: str, 
        target_audience: str, 
        send_scenario: str
    ) -> str:
        """建構分析提示詞"""
        scenario_map = {
            "official_account_push": "官方帳號推播",
            "group_message": "群組訊息",
            "one_on_one_service": "一對一客服"
        }
        
        audience_map = {
            "B2B": "企業客戶",
            "B2C": "一般消費者", 
            "電商": "電商購物"
        }
        
        scenario_text = scenario_map.get(send_scenario, send_scenario)
        audience_text = audience_map.get(target_audience, target_audience)
        
        return f"""請分析以下 Line 文案的品質，並提供評分和建議。

文案內容："{content}"
目標受眾：{audience_text}
發送場景：{scenario_text}

請從以下維度分析並以 JSON 格式回傳結果：

1. attractiveness (1-10分): 文案的吸引力，考慮是否能引起目標受眾注意
2. readability (1-10分): 可讀性，考慮句子長度、用詞難易度、結構清晰度
3. line_compatibility (1-10分): Line 平台相容性，考慮表情符號使用、訊息長度、排版等
4. overall_score (1-10分): 綜合評分
5. sentiment (字串): 情感傾向分析 (如：積極正面、中性、消極負面等)
6. suggestions (字串陣列): 3-5個具體的改善建議

回傳格式（純 JSON，無其他文字）：
{{
  "attractiveness": 8.5,
  "readability": 7.2,
  "line_compatibility": 9.0,
  "overall_score": 8.2,
  "sentiment": "積極正面",
  "suggestions": [
    "建議加入適當的表情符號增加親和力",
    "可以縮短句子長度提升可讀性"
  ]
}}"""

    async def analyze_content(
        self, 
        content: str, 
        target_audience: str, 
        send_scenario: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """分析文案內容"""
        
        prompt = self._build_analysis_prompt(content, target_audience, send_scenario)
        
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一位專業的 Line 行銷文案分析師，擅長分析文案品質並提供改善建議。"
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    response_format={"type": "json_object"}  # 確保回傳 JSON 格式
                )
                
                # 解析回應
                content_text = response.choices[0].message.content
                if not content_text:
                    raise AIAnalysisError("AI 回應內容為空")
                
                result = json.loads(content_text)
                
                # 驗證回應格式
                self._validate_analysis_result(result)
                
                return result
                
            except json.JSONDecodeError as e:
                if attempt == max_retries - 1:
                    raise AIAnalysisError(f"AI 回應格式錯誤: {e}")
                await asyncio.sleep(1)  # 重試前等待
                
            except Exception as e:
                if "rate_limit" in str(e).lower():
                    raise AIAnalysisError("AI 服務使用量超限，請稍後重試")
                elif "insufficient_quota" in str(e).lower():
                    raise AIAnalysisError("AI 服務配額不足，請聯繫管理員")
                elif attempt == max_retries - 1:
                    raise AIAnalysisError(f"AI 分析失敗: {e}")
                await asyncio.sleep(2 ** attempt)  # 指數退避
        
        raise AIAnalysisError("AI 分析多次重試後失敗")
    
    def _validate_analysis_result(self, result: Dict[str, Any]) -> None:
        """驗證分析結果格式"""
        required_fields = [
            "attractiveness", "readability", "line_compatibility", 
            "overall_score", "sentiment", "suggestions"
        ]
        
        for field in required_fields:
            if field not in result:
                raise AIAnalysisError(f"AI 回應缺少必要欄位: {field}")
        
        # 驗證評分範圍 (1-10)
        score_fields = ["attractiveness", "readability", "line_compatibility", "overall_score"]
        for field in score_fields:
            value = result[field]
            if not isinstance(value, (int, float)) or not (1 <= value <= 10):
                raise AIAnalysisError(f"評分欄位 {field} 格式錯誤: {value}")
        
        # 驗證建議是陣列
        suggestions = result.get("suggestions", [])
        if not isinstance(suggestions, list) or len(suggestions) == 0:
            raise AIAnalysisError("建議欄位格式錯誤或為空")


# 建立全域實例
def get_ai_client() -> OpenAIClient:
    """獲取 AI 客戶端實例"""
    return OpenAIClient()