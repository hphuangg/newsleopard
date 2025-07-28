"""分析 API 測試"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.analysis import AnalysisCreate, TargetAudienceEnum, SendScenarioEnum
from app.core.exceptions import AIServiceException, AnalysisErrorCode


client = TestClient(app)


class TestAnalysisAPI:
    """分析 API 測試"""
    
    @pytest.fixture
    def mock_db_session(self):
        """模擬資料庫 session"""
        return MagicMock()
    
    @pytest.fixture
    def mock_analysis_service(self):
        """模擬分析服務"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_analysis_record(self):
        """模擬分析記錄"""
        record = MagicMock()
        record.analysis_id = uuid4()
        record.id = 1
        record.content = "測試文案"
        record.target_audience = "B2C"
        record.send_scenario = "official_account_push"
        record.status = "completed"
        record.created_at = datetime.utcnow()
        record.attractiveness = 8.5
        record.readability = 7.2
        record.line_compatibility = 9.0
        record.overall_score = 8.2
        record.sentiment = "積極正面"
        record.suggestions = ["建議1", "建議2"]
        return record
    
    @pytest.fixture
    def analysis_request_data(self):
        """分析請求資料"""
        return {
            "content": "這是一個測試文案，用來驗證 API 功能是否正常運作。",
            "target_audience": "B2C",
            "send_scenario": "official_account_push"
        }
    
    def test_create_analysis_success(
        self, 
        mock_analysis_service, 
        mock_analysis_record, 
        analysis_request_data
    ):
        """測試成功建立分析"""
        
        # 設定 mock 服務回應
        mock_analysis_service.create_and_analyze.return_value = mock_analysis_record
        mock_analysis_service.convert_to_response.return_value = MagicMock(
            analysis_id=mock_analysis_record.analysis_id,
            status="completed",
            created_at=mock_analysis_record.created_at,
            results=MagicMock(
                attractiveness=8.5,
                readability=7.2,
                line_compatibility=9.0,
                overall_score=8.2,
                sentiment="積極正面",
                suggestions=["建議1", "建議2"]
            )
        )
        
        # 使用依賴覆寫
        with patch('app.api.v1.endpoints.analysis.get_analysis_service', return_value=mock_analysis_service):
            with patch('app.api.v1.endpoints.analysis.get_db', return_value=MagicMock()):
                response = client.post("/api/v1/analyze", json=analysis_request_data)
        
        # 驗證回應
        assert response.status_code == 201
        response_data = response.json()
        assert "analysis_id" in response_data
        assert response_data["status"] == "completed"
        assert "results" in response_data
        assert response_data["results"]["attractiveness"] == 8.5
    
    def test_create_analysis_invalid_input(self):
        """測試無效輸入的驗證"""
        
        invalid_data = {
            "content": "",  # 空內容
            "target_audience": "INVALID",  # 無效受眾
            "send_scenario": "invalid_scenario"  # 無效場景
        }
        
        response = client.post("/api/v1/analyze", json=invalid_data)
        
        # 應該回傳 422 驗證錯誤
        assert response.status_code == 422
    
    def test_create_analysis_ai_rate_limit_error(self, mock_analysis_service):
        """測試 AI 服務限流錯誤"""
        
        # 設定服務拋出限流錯誤
        error = AIServiceException(
            code=AnalysisErrorCode.AI_RATE_LIMIT_EXCEEDED,
            message="AI 服務使用量超限",
            retry_after=60
        )
        mock_analysis_service.create_and_analyze.side_effect = error
        
        analysis_request_data = {
            "content": "測試文案",
            "target_audience": "B2C",
            "send_scenario": "official_account_push"
        }
        
        with patch('app.api.v1.endpoints.analysis.get_analysis_service', return_value=mock_analysis_service):
            with patch('app.api.v1.endpoints.analysis.get_db', return_value=MagicMock()):
                response = client.post("/api/v1/analyze", json=analysis_request_data)
        
        # 應該回傳 429 Too Many Requests
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] == "60"
        
        response_data = response.json()
        assert response_data["error"]["code"] == "AI_RATE_LIMIT_EXCEEDED"
    
    def test_create_analysis_ai_quota_error(self, mock_analysis_service):
        """測試 AI 服務配額錯誤"""
        
        # 設定服務拋出配額錯誤
        error = AIServiceException(
            code=AnalysisErrorCode.AI_QUOTA_EXCEEDED,
            message="AI 服務配額不足"
        )
        mock_analysis_service.create_and_analyze.side_effect = error
        
        analysis_request_data = {
            "content": "測試文案",
            "target_audience": "B2C",
            "send_scenario": "official_account_push"
        }
        
        with patch('app.api.v1.endpoints.analysis.get_analysis_service', return_value=mock_analysis_service):
            with patch('app.api.v1.endpoints.analysis.get_db', return_value=MagicMock()):
                response = client.post("/api/v1/analyze", json=analysis_request_data)
        
        # 應該回傳 503 Service Unavailable
        assert response.status_code == 503
        response_data = response.json()
        assert response_data["error"]["code"] == "AI_QUOTA_EXCEEDED"
    
    def test_get_analysis_success(self, mock_analysis_service, mock_analysis_record):
        """測試成功查詢分析結果"""
        
        analysis_id = uuid4()
        
        # 設定服務回應
        mock_analysis_service.get_analysis_by_id.return_value = mock_analysis_record
        mock_analysis_service.convert_to_response.return_value = MagicMock(
            analysis_id=analysis_id,
            status="completed",
            created_at=mock_analysis_record.created_at,
            results=MagicMock(
                attractiveness=8.5,
                readability=7.2,
                line_compatibility=9.0,
                overall_score=8.2,
                sentiment="積極正面",
                suggestions=["建議1", "建議2"]
            )
        )
        
        with patch('app.api.v1.endpoints.analysis.get_analysis_service', return_value=mock_analysis_service):
            with patch('app.api.v1.endpoints.analysis.get_db', return_value=MagicMock()):
                response = client.get(f"/api/v1/analyze/{analysis_id}")
        
        # 驗證回應
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "completed"
        assert "results" in response_data
    
    def test_get_analysis_not_found(self, mock_analysis_service):
        """測試查詢不存在的分析記錄"""
        
        analysis_id = uuid4()
        
        # 設定服務回傳 None
        mock_analysis_service.get_analysis_by_id.return_value = None
        
        with patch('app.api.v1.endpoints.analysis.get_analysis_service', return_value=mock_analysis_service):
            with patch('app.api.v1.endpoints.analysis.get_db', return_value=MagicMock()):
                response = client.get(f"/api/v1/analyze/{analysis_id}")
        
        # 應該回傳 404 Not Found
        assert response.status_code == 404
        response_data = response.json()
        assert response_data["error"]["code"] == "ANALYSIS_NOT_FOUND"
    
    def test_get_analysis_invalid_uuid(self):
        """測試無效的 UUID 格式"""
        
        invalid_uuid = "invalid-uuid-format"
        
        response = client.get(f"/api/v1/analyze/{invalid_uuid}")
        
        # 應該回傳 422 驗證錯誤
        assert response.status_code == 422
    
    def test_create_analysis_content_length_validation(self):
        """測試內容長度驗證"""
        
        # 測試過長內容
        long_content = "a" * 2001
        long_content_data = {
            "content": long_content,
            "target_audience": "B2C",
            "send_scenario": "official_account_push"
        }
        
        response = client.post("/api/v1/analyze", json=long_content_data)
        
        # 應該回傳驗證錯誤
        assert response.status_code == 422
    
    def test_create_analysis_malicious_content_validation(self):
        """測試惡意內容驗證"""
        
        malicious_data = {
            "content": "<script>alert('xss')</script>",
            "target_audience": "B2C",
            "send_scenario": "official_account_push"
        }
        
        response = client.post("/api/v1/analyze", json=malicious_data)
        
        # 應該回傳驗證錯誤
        assert response.status_code == 422


class TestAnalysisAPIIntegration:
    """分析 API 整合測試"""
    
    def test_api_documentation_generation(self):
        """測試 API 文檔生成"""
        
        response = client.get("/docs")
        assert response.status_code == 200
        
        # 測試 OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        
        # 驗證分析 API 在 schema 中
        paths = schema.get("paths", {})
        assert "/api/v1/analyze" in paths
        assert "/api/v1/analyze/{analysis_id}" in paths
        
        # 驗證 POST /analyze 端點
        analyze_post = paths["/api/v1/analyze"]["post"]
        assert analyze_post["tags"] == ["analysis"]
        assert "requestBody" in analyze_post
        assert "responses" in analyze_post
    
    def test_endpoint_tags_and_metadata(self):
        """測試端點標籤和元資料"""
        
        response = client.get("/openapi.json")
        schema = response.json()
        
        # 檢查分析端點的標籤
        analyze_post = schema["paths"]["/api/v1/analyze"]["post"]  
        assert "analysis" in analyze_post["tags"]
        
        analyze_get = schema["paths"]["/api/v1/analyze/{analysis_id}"]["get"]
        assert "analysis" in analyze_get["tags"]