"""分析服務測試"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.services.analysis_service import AnalysisService
from app.services.ai_client import AIAnalysisError
from app.schemas.analysis import AnalysisCreate, TargetAudienceEnum, SendScenarioEnum


class TestAnalysisService:
    """分析服務測試"""
    
    @pytest.fixture
    def mock_db(self):
        """模擬資料庫 session"""
        return MagicMock()
    
    @pytest.fixture
    def mock_ai_client(self):
        """模擬 AI 客戶端"""
        mock_client = AsyncMock()
        mock_client.model = "gpt-4o-mini"
        return mock_client
    
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
            content="這是一個測試文案，用來驗證分析功能是否正常運作。",
            target_audience=TargetAudienceEnum.B2C,
            send_scenario=SendScenarioEnum.OFFICIAL_ACCOUNT_PUSH
        )
    
    @pytest.fixture
    def ai_analysis_result(self):
        """AI 分析結果"""
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
    
    def test_service_initialization(self, mock_ai_client):
        """測試服務初始化"""
        service = AnalysisService(ai_client=mock_ai_client)
        assert service.ai_client == mock_ai_client
    
    @pytest.mark.asyncio
    async def test_create_and_analyze_success(
        self, 
        mock_db, 
        mock_ai_client, 
        mock_analysis_record, 
        analysis_data, 
        ai_analysis_result
    ):
        """測試成功建立並分析"""
        
        # 設定 mock 行為
        with patch('app.services.analysis_service.crud_analysis') as mock_crud:
            mock_crud.create.return_value = mock_analysis_record
            mock_ai_client.analyze_content.return_value = ai_analysis_result
            
            service = AnalysisService(ai_client=mock_ai_client)
            
            # 執行測試
            result = await service.create_and_analyze(mock_db, analysis_data)
            
            # 驗證
            mock_crud.create.assert_called_once_with(mock_db, obj_in=analysis_data)
            mock_ai_client.analyze_content.assert_called_once_with(
                content=analysis_data.content,
                target_audience=analysis_data.target_audience.value,
                send_scenario=analysis_data.send_scenario.value
            )
            
            # 驗證記錄被更新為完成狀態
            assert mock_analysis_record.status == "completed"
            assert mock_analysis_record.attractiveness == 8.5
            assert mock_analysis_record.readability == 7.2
            assert mock_analysis_record.sentiment == "積極正面"
            mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_create_and_analyze_ai_error(
        self, 
        mock_db, 
        mock_ai_client, 
        mock_analysis_record, 
        analysis_data
    ):
        """測試 AI 分析失敗的處理"""
        
        # 設定 AI 客戶端拋出錯誤
        error_message = "AI 服務使用量超限，請稍後重試"
        mock_ai_client.analyze_content.side_effect = AIAnalysisError(error_message)
        
        with patch('app.services.analysis_service.crud_analysis') as mock_crud:
            mock_crud.create.return_value = mock_analysis_record
            
            service = AnalysisService(ai_client=mock_ai_client)
            
            # 執行測試
            result = await service.create_and_analyze(mock_db, analysis_data)
            
            # 驗證記錄被標記為失敗
            assert mock_analysis_record.status == "failed"
            assert mock_analysis_record.error_message == error_message
            assert mock_analysis_record.processing_time > 0
            mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_create_and_analyze_unexpected_error(
        self, 
        mock_db, 
        mock_ai_client, 
        mock_analysis_record, 
        analysis_data
    ):
        """測試未預期錯誤的處理"""
        
        # 設定未預期的錯誤
        mock_ai_client.analyze_content.side_effect = Exception("網路連線錯誤")
        
        with patch('app.services.analysis_service.crud_analysis') as mock_crud:
            mock_crud.create.return_value = mock_analysis_record
            
            service = AnalysisService(ai_client=mock_ai_client)
            
            # 執行測試
            result = await service.create_and_analyze(mock_db, analysis_data)
            
            # 驗證記錄被標記為失敗
            assert mock_analysis_record.status == "failed"
            assert "系統錯誤" in mock_analysis_record.error_message
            mock_db.commit.assert_called()
    
    def test_get_analysis_by_id(self, mock_db, mock_ai_client):
        """測試根據 ID 查詢分析記錄"""
        analysis_id = uuid4()
        
        with patch('app.services.analysis_service.crud_analysis') as mock_crud:
            service = AnalysisService(ai_client=mock_ai_client)
            
            # 執行測試
            service.get_analysis_by_id(mock_db, analysis_id)
            
            # 驗證
            mock_crud.get_by_analysis_id.assert_called_once_with(
                mock_db, analysis_id=analysis_id
            )
    
    def test_convert_to_response_completed(self, mock_ai_client, mock_analysis_record):
        """測試轉換完成狀態的記錄為回應格式"""
        # 設定完成狀態的記錄
        mock_analysis_record.status = "completed"
        mock_analysis_record.attractiveness = 8.5
        mock_analysis_record.readability = 7.2
        mock_analysis_record.line_compatibility = 9.0
        mock_analysis_record.overall_score = 8.2
        mock_analysis_record.sentiment = "積極正面"
        mock_analysis_record.suggestions = ["建議1", "建議2"]
        
        service = AnalysisService(ai_client=mock_ai_client)
        
        # 執行測試
        response = service.convert_to_response(mock_analysis_record)
        
        # 驗證
        assert response.analysis_id == mock_analysis_record.analysis_id
        assert response.status == "completed"
        assert response.results is not None
        assert response.results.attractiveness == 8.5
        assert response.results.sentiment == "積極正面"
    
    def test_convert_to_response_pending(self, mock_ai_client, mock_analysis_record):
        """測試轉換待處理狀態的記錄為回應格式"""
        # 設定待處理狀態的記錄
        mock_analysis_record.status = "pending"
        
        service = AnalysisService(ai_client=mock_ai_client)
        
        # 執行測試
        response = service.convert_to_response(mock_analysis_record)
        
        # 驗證
        assert response.analysis_id == mock_analysis_record.analysis_id
        assert response.status == "pending"
        assert response.results is None  # 未完成時不包含結果
    
    def test_update_analysis_results(self, mock_db, mock_ai_client, mock_analysis_record, ai_analysis_result):
        """測試更新分析結果"""
        service = AnalysisService(ai_client=mock_ai_client)
        
        # 執行測試
        result = service._update_analysis_results(
            db=mock_db,
            db_analysis=mock_analysis_record,
            ai_result=ai_analysis_result,
            processing_time=1.5
        )
        
        # 驗證
        assert mock_analysis_record.status == "completed"
        assert mock_analysis_record.attractiveness == 8.5
        assert mock_analysis_record.processing_time == 1.5
        assert mock_analysis_record.ai_model_used == mock_ai_client.model
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_analysis_record)
    
    def test_mark_analysis_failed(self, mock_db, mock_ai_client, mock_analysis_record):
        """測試標記分析失敗"""
        service = AnalysisService(ai_client=mock_ai_client)
        error_message = "測試錯誤"
        processing_time = 2.0
        
        # 執行測試
        result = service._mark_analysis_failed(
            db=mock_db,
            db_analysis=mock_analysis_record,
            error_message=error_message,
            processing_time=processing_time
        )
        
        # 驗證
        assert mock_analysis_record.status == "failed"
        assert mock_analysis_record.error_message == error_message
        assert mock_analysis_record.processing_time == processing_time
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_analysis_record)