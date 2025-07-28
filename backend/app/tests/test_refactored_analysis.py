"""重構後的分析功能測試"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.services.analysis_service import AnalysisService
from app.services.ai_client import AIClientBase
from app.core.exceptions import AIServiceException, AnalysisErrorCode
from app.schemas.analysis import AnalysisCreate, TargetAudienceEnum, SendScenarioEnum
from app.crud.analysis import AnalysisCRUD


class MockAIClient(AIClientBase):
    """測試用的 Mock AI 客戶端"""
    
    def __init__(self):
        super().__init__("test-model", 1000, 0.3)
        self.should_fail = False
        self.fail_with = None
        self.response_data = {
            "attractiveness": 8.5,
            "readability": 7.2,
            "line_compatibility": 9.0,
            "overall_score": 8.2,
            "sentiment": "積極正面",
            "suggestions": ["建議1", "建議2"]
        }
    
    async def analyze_content(self, content: str, target_audience: str, send_scenario: str, max_retries: int = 3):
        if self.should_fail:
            raise self.fail_with
        return self.response_data
    
    def validate_analysis_result(self, result):
        # 簡單的驗證邏輯用於測試
        required_fields = ["attractiveness", "readability", "line_compatibility", "overall_score", "sentiment", "suggestions"]
        for field in required_fields:
            if field not in result:
                raise AIServiceException(
                    code=AnalysisErrorCode.AI_INVALID_RESPONSE,
                    message=f"缺少必要欄位: {field}"
                )


class TestRefactoredAnalysisService:
    """重構後的分析服務測試"""
    
    @pytest.fixture
    def mock_db(self):
        """模擬資料庫 session"""
        return MagicMock()
    
    @pytest.fixture
    def mock_ai_client(self):
        """模擬 AI 客戶端"""
        return MockAIClient()
    
    @pytest.fixture
    def mock_crud(self):
        """模擬 CRUD 操作"""
        return MagicMock(spec=AnalysisCRUD)
    
    @pytest.fixture
    def mock_analysis_record(self):
        """模擬分析記錄"""
        record = MagicMock()
        record.analysis_id = uuid4()
        record.id = 1
        record.content = "測試文案"
        record.target_audience = "B2C"
        record.send_scenario = "official_account_push"
        record.status = "pending"
        record.created_at = datetime.utcnow()
        record.updated_at = datetime.utcnow()
        return record
    
    @pytest.fixture
    def analysis_data(self):
        """分析請求資料"""
        return AnalysisCreate(
            content="這是一個測試文案，用來驗證重構後的分析功能。",
            target_audience=TargetAudienceEnum.B2C,
            send_scenario=SendScenarioEnum.OFFICIAL_ACCOUNT_PUSH
        )
    
    def test_service_initialization_with_dependencies(self, mock_ai_client, mock_crud):
        """測試服務依賴注入初始化"""
        service = AnalysisService(ai_client=mock_ai_client, crud=mock_crud)
        
        assert service.ai_client == mock_ai_client
        assert service.crud == mock_crud
    
    def test_service_initialization_with_defaults(self):
        """測試服務使用預設依賴初始化"""
        with patch('app.services.analysis_service.get_default_ai_client') as mock_get_client:
            with patch('app.services.analysis_service.AnalysisCRUD') as mock_crud_class:
                mock_client = MagicMock()
                mock_crud_instance = MagicMock()
                mock_get_client.return_value = mock_client
                mock_crud_class.return_value = mock_crud_instance
                
                service = AnalysisService()
                
                assert service.ai_client == mock_client
                assert service.crud == mock_crud_instance
    
    @pytest.mark.asyncio
    async def test_create_and_analyze_success(
        self, 
        mock_db, 
        mock_ai_client, 
        mock_crud, 
        mock_analysis_record, 
        analysis_data
    ):
        """測試成功建立並分析"""
        # 設定 mock 行為
        mock_crud.create.return_value = mock_analysis_record
        
        service = AnalysisService(ai_client=mock_ai_client, crud=mock_crud)
        
        # 執行測試
        result = await service.create_and_analyze(mock_db, analysis_data)
        
        # 驗證
        mock_crud.create.assert_called_once_with(mock_db, obj_in=analysis_data)
        
        # 驗證記錄被更新為完成狀態
        assert mock_analysis_record.status == "completed"
        assert mock_analysis_record.attractiveness == 8.5
        assert mock_analysis_record.readability == 7.2
        assert mock_analysis_record.sentiment == "積極正面"
        mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_create_and_analyze_ai_service_error(
        self, 
        mock_db, 
        mock_ai_client, 
        mock_crud, 
        mock_analysis_record, 
        analysis_data
    ):
        """測試 AI 服務錯誤處理"""
        # 設定 AI 客戶端拋出錯誤
        error = AIServiceException(
            code=AnalysisErrorCode.AI_RATE_LIMIT_EXCEEDED,
            message="AI 服務使用量超限"
        )
        mock_ai_client.should_fail = True
        mock_ai_client.fail_with = error
        
        mock_crud.create.return_value = mock_analysis_record
        
        service = AnalysisService(ai_client=mock_ai_client, crud=mock_crud)
        
        # 執行測試
        result = await service.create_and_analyze(mock_db, analysis_data)
        
        # 驗證記錄被標記為失敗
        assert mock_analysis_record.status == "failed"
        assert mock_analysis_record.error_message == "AI 服務使用量超限"
        assert mock_analysis_record.processing_time > 0
        mock_db.commit.assert_called()
    
    def test_get_analysis_by_id(self, mock_db, mock_ai_client, mock_crud):
        """測試根據 ID 查詢分析記錄"""
        analysis_id = uuid4()
        
        service = AnalysisService(ai_client=mock_ai_client, crud=mock_crud)
        
        # 執行測試
        service.get_analysis_by_id(mock_db, analysis_id)
        
        # 驗證
        mock_crud.get_by_analysis_id.assert_called_once_with(
            mock_db, analysis_id=analysis_id
        )
    
    def test_convert_to_response_completed(self, mock_ai_client, mock_crud, mock_analysis_record):
        """測試轉換完成狀態的記錄為回應格式"""
        # 設定完成狀態的記錄
        mock_analysis_record.status = "completed"
        mock_analysis_record.attractiveness = 8.5
        mock_analysis_record.readability = 7.2
        mock_analysis_record.line_compatibility = 9.0
        mock_analysis_record.overall_score = 8.2
        mock_analysis_record.sentiment = "積極正面"
        mock_analysis_record.suggestions = ["建議1", "建議2"]
        
        service = AnalysisService(ai_client=mock_ai_client, crud=mock_crud)
        
        # 執行測試
        response = service.convert_to_response(mock_analysis_record)
        
        # 驗證
        assert response.analysis_id == mock_analysis_record.analysis_id
        assert response.status == "completed"
        assert response.results is not None
        assert response.results.attractiveness == 8.5
        assert response.results.sentiment == "積極正面"


class TestAIClientFactory:
    """AI 客戶端工廠測試"""
    
    def test_create_openai_client(self):
        """測試建立 OpenAI 客戶端"""
        from app.services.ai_client.factory import create_ai_client
        
        with patch('app.services.ai_client.factory.OpenAIClient') as mock_openai:
            mock_instance = MagicMock()
            mock_openai.return_value = mock_instance
            
            client = create_ai_client("openai")
            
            assert client == mock_instance
            mock_openai.assert_called_once()
    
    def test_create_unsupported_provider(self):
        """測試建立不支援的 AI 提供商"""
        from app.services.ai_client.factory import create_ai_client
        
        with pytest.raises(ValueError, match="不支援的 AI 提供商"):
            create_ai_client("unsupported")
    
    def test_get_default_client(self):
        """測試獲取預設客戶端"""
        from app.services.ai_client.factory import get_default_ai_client
        
        with patch('app.services.ai_client.factory.create_ai_client') as mock_create:
            mock_client = MagicMock()
            mock_create.return_value = mock_client
            
            client = get_default_ai_client()
            
            assert client == mock_client
            mock_create.assert_called_once_with()


class TestPromptTemplates:
    """提示詞模板測試"""
    
    def test_build_analysis_prompt(self):
        """測試建構分析提示詞"""
        from app.services.prompts import build_analysis_prompt
        
        prompt = build_analysis_prompt(
            content="測試文案",
            target_audience="B2C",
            send_scenario="official_account_push"
        )
        
        assert "測試文案" in prompt
        assert "一般消費者" in prompt
        assert "官方帳號推播" in prompt
    
    def test_prompt_template_validation(self):
        """測試提示詞模板參數驗證"""
        from app.services.prompts.templates import PromptTemplate, PromptVersion
        
        template = PromptTemplate(
            name="test",
            version=PromptVersion.V1_0,
            description="測試模板",
            required_params=["param1", "param2"],
            template="Test {param1} and {param2}"
        )
        
        # 測試成功格式化
        result = template.format(param1="value1", param2="value2")
        assert result == "Test value1 and value2"
        
        # 測試缺少參數
        with pytest.raises(ValueError, match="缺少必要參數"):
            template.format(param1="value1")