"""AI 客戶端測試"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.ai_client import OpenAIClient, AIAnalysisError


class TestOpenAIClient:
    """OpenAI 客戶端測試"""
    
    @pytest.fixture
    def mock_openai_response(self):
        """模擬 OpenAI API 回應"""
        return {
            "attractiveness": 8.5,
            "readability": 7.2,
            "line_compatibility": 9.0,
            "overall_score": 8.2,
            "sentiment": "積極正面",
            "suggestions": [
                "建議加入適當的表情符號增加親和力",
                "可以縮短句子長度提升可讀性"
            ]
        }
    
    @pytest.fixture
    def mock_settings(self):
        """模擬設定"""
        with patch('app.services.ai_client.settings') as mock:
            mock.OPENAI_API_KEY = "test-api-key"
            mock.OPENAI_MODEL = "gpt-4o-mini"
            mock.OPENAI_MAX_TOKENS = 1000
            mock.OPENAI_TEMPERATURE = 0.3
            yield mock
    
    def test_client_initialization_success(self, mock_settings):
        """測試客戶端成功初始化"""
        client = OpenAIClient()
        assert client.model == "gpt-4o-mini"
        assert client.max_tokens == 1000
        assert client.temperature == 0.3
    
    def test_client_initialization_no_api_key(self):
        """測試沒有 API Key 時的錯誤處理"""
        with patch('app.services.ai_client.settings') as mock:
            mock.OPENAI_API_KEY = None
            
            with pytest.raises(AIAnalysisError, match="OPENAI_API_KEY 未設定在環境變數中"):
                OpenAIClient()
    
    def test_build_analysis_prompt(self, mock_settings):
        """測試分析提示詞建構"""
        client = OpenAIClient()
        
        prompt = client._build_analysis_prompt(
            content="測試文案",
            target_audience="B2C", 
            send_scenario="official_account_push"
        )
        
        assert "測試文案" in prompt
        assert "一般消費者" in prompt
        assert "官方帳號推播" in prompt
        assert "JSON" in prompt
    
    @pytest.mark.asyncio
    async def test_analyze_content_success(self, mock_settings, mock_openai_response):
        """測試成功分析文案"""
        with patch('app.services.ai_client.AsyncOpenAI') as mock_openai:
            # 設定 mock 回應
            mock_response = MagicMock()
            mock_response.choices[0].message.content = json.dumps(mock_openai_response)
            
            mock_client = AsyncMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            # 測試
            client = OpenAIClient()
            result = await client.analyze_content(
                content="測試文案",
                target_audience="B2C",
                send_scenario="official_account_push"
            )
            
            assert result["attractiveness"] == 8.5
            assert result["sentiment"] == "積極正面"
            assert len(result["suggestions"]) == 2
    
    @pytest.mark.asyncio
    async def test_analyze_content_json_decode_error(self, mock_settings):
        """測試 JSON 解析錯誤"""
        with patch('app.services.ai_client.AsyncOpenAI') as mock_openai:
            # 設定無效的 JSON 回應
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "invalid json"
            
            mock_client = AsyncMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            client = OpenAIClient()
            
            with pytest.raises(AIAnalysisError, match="AI 回應格式錯誤"):
                await client.analyze_content(
                    content="測試文案",
                    target_audience="B2C",
                    send_scenario="official_account_push"
                )
    
    @pytest.mark.asyncio
    async def test_analyze_content_rate_limit_error(self, mock_settings):
        """測試 API 限流錯誤"""
        with patch('app.services.ai_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.side_effect = Exception("rate_limit exceeded")
            mock_openai.return_value = mock_client
            
            client = OpenAIClient()
            
            with pytest.raises(AIAnalysisError, match="AI 服務使用量超限"):
                await client.analyze_content(
                    content="測試文案",
                    target_audience="B2C",
                    send_scenario="official_account_push"
                )
    
    def test_validate_analysis_result_success(self, mock_settings, mock_openai_response):
        """測試結果驗證成功"""
        client = OpenAIClient()
        # 應該不拋出異常
        client._validate_analysis_result(mock_openai_response)
    
    def test_validate_analysis_result_missing_field(self, mock_settings):
        """測試缺少必要欄位的驗證"""
        client = OpenAIClient()
        invalid_result = {"attractiveness": 8.5}  # 缺少其他欄位
        
        with pytest.raises(AIAnalysisError, match="AI 回應缺少必要欄位"):
            client._validate_analysis_result(invalid_result)
    
    def test_validate_analysis_result_invalid_score(self, mock_settings):
        """測試無效評分的驗證"""
        client = OpenAIClient()
        invalid_result = {
            "attractiveness": 15,  # 超出範圍
            "readability": 7.2,
            "line_compatibility": 9.0,
            "overall_score": 8.2,
            "sentiment": "積極正面",
            "suggestions": ["建議1"]
        }
        
        with pytest.raises(AIAnalysisError, match="評分欄位.*格式錯誤"):
            client._validate_analysis_result(invalid_result)
    
    def test_validate_analysis_result_empty_suggestions(self, mock_settings):
        """測試空建議列表的驗證"""
        client = OpenAIClient()
        invalid_result = {
            "attractiveness": 8.5,
            "readability": 7.2,
            "line_compatibility": 9.0,
            "overall_score": 8.2,
            "sentiment": "積極正面",
            "suggestions": []  # 空陣列
        }
        
        with pytest.raises(AIAnalysisError, match="建議欄位格式錯誤或為空"):
            client._validate_analysis_result(invalid_result)