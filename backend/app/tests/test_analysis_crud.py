import pytest
from app.crud.analysis import crud_analysis
from app.schemas.analysis import AnalysisCreate, TargetAudienceEnum, SendScenarioEnum


def test_create_analysis_record(db):
    """測試建立分析記錄"""
    # 準備測試資料
    analysis_data = AnalysisCreate(
        content="這是一個測試文案，用來驗證分析功能是否正常運作。",
        target_audience=TargetAudienceEnum.B2C,
        send_scenario=SendScenarioEnum.OFFICIAL_ACCOUNT_PUSH
    )
    
    # 執行建立操作
    result = crud_analysis.create(db, obj_in=analysis_data)
    
    # 驗證結果
    assert result.id is not None
    assert result.analysis_id is not None
    assert result.content == analysis_data.content
    assert result.target_audience == "B2C"
    assert result.send_scenario == "official_account_push"
    assert result.status == "pending"
    assert result.created_at is not None
    assert result.updated_at is not None


def test_create_analysis_record_with_different_enums(db):
    """測試使用不同枚舉值建立分析記錄"""
    analysis_data = AnalysisCreate(
        content="電商專用的行銷文案測試",
        target_audience=TargetAudienceEnum.ECOMMERCE,
        send_scenario=SendScenarioEnum.GROUP_MESSAGE
    )
    
    result = crud_analysis.create(db, obj_in=analysis_data)
    
    assert result.target_audience == "電商"
    assert result.send_scenario == "group_message"


def test_create_analysis_record_validates_content_length():
    """測試內容長度驗證"""
    # 測試空內容
    with pytest.raises(ValueError):
        AnalysisCreate(
            content="",
            target_audience=TargetAudienceEnum.B2C,
            send_scenario=SendScenarioEnum.OFFICIAL_ACCOUNT_PUSH
        )
    
    # 測試過長內容
    long_content = "a" * 2001
    with pytest.raises(ValueError):
        AnalysisCreate(
            content=long_content,
            target_audience=TargetAudienceEnum.B2C,
            send_scenario=SendScenarioEnum.OFFICIAL_ACCOUNT_PUSH
        )


def test_create_analysis_record_validates_malicious_content():
    """測試惡意內容驗證"""
    malicious_contents = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "onload=alert('xss')",
        "onerror=alert('xss')"
    ]
    
    for malicious_content in malicious_contents:
        with pytest.raises(ValueError):
            AnalysisCreate(
                content=malicious_content,
                target_audience=TargetAudienceEnum.B2C,
                send_scenario=SendScenarioEnum.OFFICIAL_ACCOUNT_PUSH
            )