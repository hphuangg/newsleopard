"""
發送管道相關例外類別
"""


class ChannelError(Exception):
    """管道基礎例外"""
    pass


class ChannelNotFoundError(ChannelError):
    """管道不存在例外"""
    pass


class ChannelUnavailableError(ChannelError):
    """管道不可用例外"""
    pass


class RateLimitExceededError(ChannelError):
    """頻率限制超過例外"""
    pass


class InvalidRecipientError(ChannelError):
    """無效收件人例外"""
    pass


class ChannelConfigurationError(ChannelError):
    """管道配置錯誤例外"""
    pass