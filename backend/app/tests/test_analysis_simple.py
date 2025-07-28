"""簡化版的分析功能測試"""
import pytest
from app.schemas.analysis import AnalysisCreate, TargetAudienceEnum, SendScenarioEnum


def test_analysis_create_schema_validation():
    """測試 AnalysisCreate Schema 的驗證功能"""
    # 測試正常的資料
    valid_data = AnalysisCreate(
        content="這是一個測試文案，用來驗證分析功能是否正常運作。",
        target_audience=TargetAudienceEnum.B2C,
        send_scenario=SendScenarioEnum.OFFICIAL_ACCOUNT_PUSH
    )
    
    assert valid_data.content == "這是一個測試文案，用來驗證分析功能是否正常運作。"
    assert valid_data.target_audience == TargetAudienceEnum.B2C
    assert valid_data.send_scenario == SendScenarioEnum.OFFICIAL_ACCOUNT_PUSH


def test_analysis_create_content_validation():
    """測試內容驗證"""
    from pydantic import ValidationError
    
    # 測試空內容 - Pydantic 會先檢查 min_length
    with pytest.raises(ValidationError):
        AnalysisCreate(
            content="",
            target_audience=TargetAudienceEnum.B2C,
            send_scenario=SendScenarioEnum.OFFICIAL_ACCOUNT_PUSH
        )
    
    # 測試空白內容 - 我們的 validator 會捕捉這個
    with pytest.raises(ValueError, match="文案內容不能為空"):
        AnalysisCreate(
            content="   ",
            target_audience=TargetAudienceEnum.B2C,
            send_scenario=SendScenarioEnum.OFFICIAL_ACCOUNT_PUSH
        )


def test_analysis_create_malicious_content_validation():
    """測試惡意內容驗證"""
    malicious_contents = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "onload=alert('xss')",
        "onerror=alert('xss')"
    ]
    
    for malicious_content in malicious_contents:
        with pytest.raises(ValueError, match="文案內容包含不安全的內容"):
            AnalysisCreate(
                content=malicious_content,
                target_audience=TargetAudienceEnum.B2C,
                send_scenario=SendScenarioEnum.OFFICIAL_ACCOUNT_PUSH
            )


def test_analysis_create_enum_values():
    """測試枚舉值的正確性"""
    # 測試所有目標受眾枚舉
    for audience in TargetAudienceEnum:
        analysis = AnalysisCreate(
            content="測試文案",
            target_audience=audience,
            send_scenario=SendScenarioEnum.OFFICIAL_ACCOUNT_PUSH
        )
        assert analysis.target_audience == audience
    
    # 測試所有發送場景枚舉
    for scenario in SendScenarioEnum:
        analysis = AnalysisCreate(
            content="測試文案",
            target_audience=TargetAudienceEnum.B2C,
            send_scenario=scenario
        )
        assert analysis.send_scenario == scenario