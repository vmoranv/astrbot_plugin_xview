"""
XView API 自定义异常类
"""


class XViewError(Exception):
    """XView API 基础异常类"""
    pass


class VideoNotFound(XViewError):
    """视频未找到异常"""
    def __init__(self, message="视频不存在或已被删除"):
        self.message = message
        super().__init__(self.message)


class VideoDisabled(XViewError):
    """视频已禁用异常"""
    def __init__(self, message="视频已被禁用或因版权问题被删除"):
        self.message = message
        super().__init__(self.message)


class InvalidURL(XViewError):
    """无效 URL 异常"""
    def __init__(self, message="提供的 URL 无效，无法提取视频 ID"):
        self.message = message
        super().__init__(self.message)


class NetworkError(XViewError):
    """网络请求异常"""
    def __init__(self, message="网络请求失败"):
        self.message = message
        super().__init__(self.message)


class ParseError(XViewError):
    """解析异常"""
    def __init__(self, message="解析视频信息失败"):
        self.message = message
        super().__init__(self.message)


class QualityNotAvailable(XViewError):
    """请求的质量不可用"""
    def __init__(self, message="请求的视频质量不可用"):
        self.message = message
        super().__init__(self.message)


class DownloadError(XViewError):
    """下载异常"""
    def __init__(self, message="视频下载失败"):
        self.message = message
        super().__init__(self.message)


class ConfigurationError(XViewError):
    """配置异常"""
    def __init__(self, message="插件配置错误"):
        self.message = message
        super().__init__(self.message)