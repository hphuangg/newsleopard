"""依賴注入容器"""

from functools import lru_cache
from app.services.analysis_service import AnalysisService
from app.services.ai_client import get_default_ai_client
from app.crud.analysis import AnalysisCRUD


class ServiceContainer:
    """服務容器 - 管理所有服務的生命週期"""
    
    def __init__(self):
        self._services = {}
    
    def get_analysis_service(self) -> AnalysisService:
        """獲取分析服務單例"""
        if 'analysis_service' not in self._services:
            ai_client = get_default_ai_client()
            crud = AnalysisCRUD()
            self._services['analysis_service'] = AnalysisService(
                ai_client=ai_client,
                crud=crud
            )
        return self._services['analysis_service']


# 全域服務容器
_container = ServiceContainer()


@lru_cache()
def get_service_container() -> ServiceContainer:
    """獲取服務容器單例"""
    return _container


def get_analysis_service() -> AnalysisService:
    """FastAPI 依賴注入：獲取分析服務"""
    return get_service_container().get_analysis_service()