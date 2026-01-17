"""
XView API 常量定义
"""
import re

# 基础 URL
ROOT_URL = "https://secure.xview.tv/"

# HTTP 请求头 - 模拟真实浏览器访问
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Cache-Control": "max-age=0",
    "Referer": "https://secure.xview.tv/",
    # 年龄验证 Cookie - 绕过年龄确认对话框
    "Cookie": "agreeterms=1; age_verified=1; sbr=sec:xview.tv; has_signing_key=1",
}

# 正则表达式 - 提取视频 ID
REGEX_VIDEO_ID = re.compile(r"/video/(\d+)")
REGEX_VIDEO_ID_ALT = re.compile(r"video[/-](\d+)")

# 正则表达式 - 提取视频信息
REGEX_VIDEO_TITLE = re.compile(r'<title>([^<]+)</title>', re.IGNORECASE)
REGEX_VIDEO_TITLE_META = re.compile(r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']', re.IGNORECASE)
REGEX_VIDEO_DESCRIPTION = re.compile(r'<meta\s+property=["\']og:description["\']\s+content=["\']([^"\']+)["\']', re.IGNORECASE)
REGEX_VIDEO_THUMBNAIL = re.compile(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', re.IGNORECASE)
REGEX_VIDEO_DURATION = re.compile(r'<meta\s+property=["\']video:duration["\']\s+content=["\'](\d+)["\']', re.IGNORECASE)
REGEX_VIDEO_DURATION_ALT = re.compile(r'duration["\']?\s*[:=]\s*["\']?(\d+)', re.IGNORECASE)

# 正则表达式 - 提取视频源
REGEX_VIDEO_SOURCE = re.compile(r'<source\s+src=["\']([^"\']+)["\']', re.IGNORECASE)
REGEX_VIDEO_SOURCE_MP4 = re.compile(r'(https?://[^"\'<>\s]+\.mp4[^"\'<>\s]*)', re.IGNORECASE)
REGEX_VIDEO_SOURCE_M3U8 = re.compile(r'(https?://[^"\'<>\s]+\.m3u8[^"\'<>\s]*)', re.IGNORECASE)
REGEX_VIDEO_SOURCE_JS = re.compile(r'(?:source|src|video_url|videoUrl|file)["\']?\s*[:=]\s*["\']([^"\']+\.(mp4|m3u8)[^"\']*)["\']', re.IGNORECASE)

# 正则表达式 - 提取视频质量选项
REGEX_VIDEO_QUALITY = re.compile(r'(\d{3,4})p', re.IGNORECASE)

# 正则表达式 - 提取观看次数和评分
REGEX_VIDEO_VIEWS = re.compile(r'(?:views?|播放)["\']?\s*[:=]?\s*["\']?([\d,]+)', re.IGNORECASE)
REGEX_VIDEO_RATING = re.compile(r'(?:rating|评分)["\']?\s*[:=]?\s*["\']?([\d.]+)', re.IGNORECASE)
REGEX_VIDEO_LIKES = re.compile(r'(?:likes?|喜欢)["\']?\s*[:=]?\s*["\']?([\d,]+)', re.IGNORECASE)

# 正则表达式 - 提取上传者信息
REGEX_VIDEO_UPLOADER = re.compile(r'(?:uploader|author|user)["\']?\s*[:=]\s*["\']([^"\']+)["\']', re.IGNORECASE)
REGEX_VIDEO_UPLOADER_ALT = re.compile(r'<a[^>]+href=["\'][^"\']*(?:user|profile|channel)/([^"\'"/]+)["\']', re.IGNORECASE)

# 正则表达式 - 提取标签
REGEX_VIDEO_TAGS = re.compile(r'<a[^>]+href=["\'][^"\']*(?:tag|category)/([^"\'"/]+)["\']', re.IGNORECASE)

# 正则表达式 - 提取发布日期
REGEX_VIDEO_DATE = re.compile(r'(?:upload|date|published)["\']?\s*[:=]\s*["\']?(\d{4}[-/]\d{2}[-/]\d{2})', re.IGNORECASE)

# 正则表达式 - 检测视频是否被禁用/删除
REGEX_VIDEO_DISABLED = re.compile(r'(?:video\s*(?:not\s*found|removed|deleted|disabled)|404|error)', re.IGNORECASE)

# 正则表达式 - JSON-LD 数据
REGEX_JSON_LD = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.IGNORECASE | re.DOTALL)

# 正则表达式 - 主播个人资料信息 (xview.tv div 结构)
# 格式: <div class="label">标签:</div>\n<div class="data">值</div>

# 通用 div.label + div.data 模式匹配函数用的基础模式
def _make_profile_regex(label_pattern: str) -> re.Pattern:
    """创建匹配 div.label + div.data 结构的正则表达式"""
    return re.compile(
        rf'<div[^>]*class=["\']label["\'][^>]*>\s*{label_pattern}[:\s：]*</div>\s*<div[^>]*class=["\']data["\'][^>]*>\s*([^<]+?)\s*</div>',
        re.IGNORECASE | re.DOTALL
    )

# 真名
REGEX_PROFILE_REAL_NAME = _make_profile_regex(r'(?:Real\s*Name|真名)')
REGEX_PROFILE_REAL_NAME_ALT = re.compile(r'(?:Real\s*Name|真名)[:\s：]*</div>\s*<div[^>]*>\s*([^<]+)', re.IGNORECASE)

# 关注者
REGEX_PROFILE_FOLLOWERS = _make_profile_regex(r'(?:Followers|关注者)')
REGEX_PROFILE_FOLLOWERS_ALT = re.compile(r'(?:Followers|关注者)[:\s：]*</div>\s*<div[^>]*>\s*([\d,]+)', re.IGNORECASE)
REGEX_PROFILE_FOLLOWERS_DATA = re.compile(r'(?:follower_count|num_followers)["\']?\s*[:=]\s*["\']?([\d,]+)', re.IGNORECASE)

# 性别
REGEX_PROFILE_GENDER = _make_profile_regex(r'(?:I\s*am|我是)')
REGEX_PROFILE_GENDER_ALT = re.compile(r'(?:I\s*am|我是)[:\s：]*</div>\s*<div[^>]*>\s*([^<]+)', re.IGNORECASE)
REGEX_PROFILE_GENDER_DATA = re.compile(r'(?:gender|sex)["\']?\s*[:=]\s*["\']([^"\']+)["\']', re.IGNORECASE)

# 兴趣对象
REGEX_PROFILE_INTERESTS = _make_profile_regex(r'(?:Interested\s*In|对以下选项有兴趣)[：:]?')
REGEX_PROFILE_INTERESTS_ALT = re.compile(r'(?:Interested\s*In|对以下选项有兴趣)[:\s：]*</div>\s*<div[^>]*>\s*([^<]+)', re.IGNORECASE)

# 位置
REGEX_PROFILE_LOCATION = _make_profile_regex(r'(?:Location|位置)')
REGEX_PROFILE_LOCATION_ALT = re.compile(r'(?:Location|位置)[:\s：]*</div>\s*<div[^>]*>\s*([^<]+)', re.IGNORECASE)
REGEX_PROFILE_LOCATION_DATA = re.compile(r'(?:location|country)["\']?\s*[:=]\s*["\']([^"\']+)["\']', re.IGNORECASE)

# 上次直播时间
REGEX_PROFILE_LAST_BROADCAST = _make_profile_regex(r'(?:Last\s*Broadcast|上次直播时间|上次直播的时间)')
REGEX_PROFILE_LAST_BROADCAST_ALT = re.compile(r'(?:Last\s*Broadcast|上次直播时间|上次直播的时间)[:\s：]*</div>\s*<div[^>]*>\s*([^<]+)', re.IGNORECASE)

# 语言
REGEX_PROFILE_LANGUAGES = _make_profile_regex(r'(?:Languages?|语言)')
REGEX_PROFILE_LANGUAGES_ALT = re.compile(r'(?:Languages?|语言)[:\s：]*</div>\s*<div[^>]*>\s*([^<]+)', re.IGNORECASE)

# 体型
REGEX_PROFILE_BODY_TYPE = _make_profile_regex(r'(?:Body\s*Type|体型)')
REGEX_PROFILE_BODY_TYPE_ALT = re.compile(r'(?:Body\s*Type|体型)[:\s：]*</div>\s*<div[^>]*>\s*([^<]+)', re.IGNORECASE)

# 身体装饰
REGEX_PROFILE_BODY_DECORATIONS = _make_profile_regex(r'(?:Body\s*Decorations?|身体装饰)')
REGEX_PROFILE_BODY_DECORATIONS_ALT = re.compile(r'(?:Body\s*Decorations?|身体装饰)[:\s：]*</div>\s*<div[^>]*>\s*([^<]+)', re.IGNORECASE)

# 年龄 - 需要更严格的匹配，避免匹配到其他数字如 HTTP 429
REGEX_PROFILE_AGE = _make_profile_regex(r'(?:Age|年龄)')
REGEX_PROFILE_AGE_ALT = re.compile(r'<div[^>]*class=["\']label["\'][^>]*>\s*(?:Age|年龄)[:\s：]*</div>\s*<div[^>]*class=["\']data["\'][^>]*>\s*(\d{1,3})\s*</div>', re.IGNORECASE)
# 不再使用过于宽泛的 age 匹配模式，避免误匹配
REGEX_PROFILE_AGE_DATA = re.compile(r'"age"\s*:\s*(\d{1,3})(?:\D|$)', re.IGNORECASE)

# 社交媒体链接
REGEX_PROFILE_SOCIAL_MEDIA = re.compile(r'<a[^>]+href=["\']([^"\']+(?:twitter|x\.com|instagram|snapchat|onlyfans|fansly|tiktok|youtube)[^"\']*)["\'][^>]*>', re.IGNORECASE)

# 是否在线
REGEX_PROFILE_IS_ONLINE = re.compile(r'(?:"is_online"\s*:\s*|"online"\s*:\s*)(true|1|"yes")', re.IGNORECASE)
REGEX_PROFILE_IS_STREAMING = re.compile(r'class=["\'][^"\']*\b(?:online|streaming|live)\b[^"\']*["\']', re.IGNORECASE)

# 质量映射
QUALITY_MAP = {
    "best": -1,
    "worst": 0,
    "half": None,  # 中间质量
    "2160": 2160,
    "1080": 1080,
    "720": 720,
    "480": 480,
    "360": 360,
    "240": 240,
}

# 支持的视频格式
SUPPORTED_FORMATS = ["mp4", "m3u8", "webm"]

# 默认超时设置
DEFAULT_TIMEOUT = 30
REQUEST_TIMEOUT = 60