"""
XView API Video 类
用于解析和获取视频信息
"""
import re
import json
import html
import logging
from functools import cached_property
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin

from .consts import (
    ROOT_URL,
    REGEX_VIDEO_ID,
    REGEX_VIDEO_ID_ALT,
    REGEX_VIDEO_TITLE,
    REGEX_VIDEO_TITLE_META,
    REGEX_VIDEO_DESCRIPTION,
    REGEX_VIDEO_THUMBNAIL,
    REGEX_VIDEO_DURATION,
    REGEX_VIDEO_DURATION_ALT,
    REGEX_VIDEO_SOURCE,
    REGEX_VIDEO_SOURCE_MP4,
    REGEX_VIDEO_SOURCE_M3U8,
    REGEX_VIDEO_SOURCE_JS,
    REGEX_VIDEO_QUALITY,
    REGEX_VIDEO_VIEWS,
    REGEX_VIDEO_RATING,
    REGEX_VIDEO_LIKES,
    REGEX_VIDEO_UPLOADER,
    REGEX_VIDEO_UPLOADER_ALT,
    REGEX_VIDEO_TAGS,
    REGEX_VIDEO_DATE,
    REGEX_VIDEO_DISABLED,
    REGEX_JSON_LD,
    # 主播个人资料正则
    REGEX_PROFILE_REAL_NAME,
    REGEX_PROFILE_REAL_NAME_ALT,
    REGEX_PROFILE_FOLLOWERS,
    REGEX_PROFILE_FOLLOWERS_ALT,
    REGEX_PROFILE_FOLLOWERS_DATA,
    REGEX_PROFILE_GENDER,
    REGEX_PROFILE_GENDER_ALT,
    REGEX_PROFILE_GENDER_DATA,
    REGEX_PROFILE_INTERESTS,
    REGEX_PROFILE_INTERESTS_ALT,
    REGEX_PROFILE_LOCATION,
    REGEX_PROFILE_LOCATION_ALT,
    REGEX_PROFILE_LOCATION_DATA,
    REGEX_PROFILE_LAST_BROADCAST,
    REGEX_PROFILE_LAST_BROADCAST_ALT,
    REGEX_PROFILE_LANGUAGES,
    REGEX_PROFILE_LANGUAGES_ALT,
    REGEX_PROFILE_BODY_TYPE,
    REGEX_PROFILE_BODY_TYPE_ALT,
    REGEX_PROFILE_BODY_DECORATIONS,
    REGEX_PROFILE_BODY_DECORATIONS_ALT,
    REGEX_PROFILE_AGE,
    REGEX_PROFILE_AGE_ALT,
    REGEX_PROFILE_AGE_DATA,
    REGEX_PROFILE_SOCIAL_MEDIA,
    REGEX_PROFILE_IS_ONLINE,
    REGEX_PROFILE_IS_STREAMING,
)
from .errors import (
    VideoNotFound,
    VideoDisabled,
    InvalidURL,
    ParseError,
    QualityNotAvailable,
)


class Video:
    """
    视频对象类，用于解析和获取 XView 视频信息
    """

    def __init__(self, video_id: str, html_content: Optional[str] = None):
        """
        初始化视频对象

        Args:
            video_id: 视频 ID
            html_content: 可选的 HTML 内容（如果已经获取）
        """
        self._video_id = video_id
        self._html_content = html_content
        self._json_ld_data: Optional[Dict[str, Any]] = None
        self._video_sources: Optional[List[Dict[str, str]]] = None
        self.logger = logging.getLogger("XView API - [Video]")

    @classmethod
    def from_url(cls, url: str, html_content: Optional[str] = None) -> "Video":
        """
        从 URL 创建 Video 对象

        Args:
            url: 视频 URL
            html_content: 可选的 HTML 内容

        Returns:
            Video 对象
        """
        video_id = cls._extract_video_id(url)
        return cls(video_id, html_content)

    @staticmethod
    def _extract_video_id(url: str) -> str:
        """
        从 URL 中提取视频 ID

        Args:
            url: 视频 URL

        Returns:
            视频 ID

        Raises:
            InvalidURL: 无法从 URL 中提取视频 ID
        """
        # 尝试从完整 URL 中提取
        if url.startswith(("http://", "https://")):
            match = REGEX_VIDEO_ID.search(url)
            if match:
                return match.group(1)

            match = REGEX_VIDEO_ID_ALT.search(url)
            if match:
                return match.group(1)

        # 假设输入的就是视频 ID
        if url.isdigit():
            return url

        raise InvalidURL(f"无法从 URL 中提取视频 ID: {url}")

    def set_html_content(self, content: str) -> None:
        """
        设置 HTML 内容并清除缓存

        Args:
            content: HTML 内容
        """
        self._html_content = html.unescape(content)
        # 清除所有缓存属性
        for attr in list(self.__dict__.keys()):
            if attr.startswith('_cached_'):
                delattr(self, attr)

    def _check_video_status(self) -> None:
        """
        检查视频是否可用

        Raises:
            VideoNotFound: 视频不存在
            VideoDisabled: 视频已被禁用
        """
        if not self._html_content:
            raise VideoNotFound("HTML 内容未加载")

        # 检查是否为 404 或错误页面
        if REGEX_VIDEO_DISABLED.search(self._html_content):
            raise VideoDisabled("视频已被删除或禁用")

    def _parse_json_ld(self) -> Dict[str, Any]:
        """
        解析 JSON-LD 数据

        Returns:
            JSON-LD 数据字典
        """
        if self._json_ld_data is not None:
            return self._json_ld_data

        self._json_ld_data = {}

        if not self._html_content:
            return self._json_ld_data

        matches = REGEX_JSON_LD.findall(self._html_content)
        for match in matches:
            try:
                data = json.loads(match.strip(), strict=False)
                if isinstance(data, dict):
                    self._json_ld_data.update(self._flatten_dict(data))
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            self._json_ld_data.update(self._flatten_dict(item))
            except json.JSONDecodeError:
                continue

        return self._json_ld_data

    @staticmethod
    def _flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """
        将嵌套字典展平

        Args:
            d: 要展平的字典
            parent_key: 父键
            sep: 分隔符

        Returns:
            展平后的字典
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(Video._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    @property
    def video_id(self) -> str:
        """获取视频 ID"""
        return self._video_id

    @property
    def url(self) -> str:
        """获取视频完整 URL"""
        return getattr(self, '_url', f"{ROOT_URL}{self._video_id}/")
    
    @url.setter
    def url(self, value: str) -> None:
        """设置视频 URL"""
        self._url = value

    @cached_property
    def title(self) -> Optional[str]:
        """获取视频标题"""
        if not self._html_content:
            return None

        # 尝试从 og:title 获取
        match = REGEX_VIDEO_TITLE_META.search(self._html_content)
        if match:
            return html.unescape(match.group(1).strip())

        # 尝试从 title 标签获取
        match = REGEX_VIDEO_TITLE.search(self._html_content)
        if match:
            title = html.unescape(match.group(1).strip())
            # 移除网站名称后缀
            if " - " in title:
                title = title.rsplit(" - ", 1)[0]
            return title

        # 尝试从 JSON-LD 获取
        json_ld = self._parse_json_ld()
        if "name" in json_ld:
            return json_ld["name"]

        return None

    @cached_property
    def description(self) -> Optional[str]:
        """获取视频描述"""
        if not self._html_content:
            return None

        match = REGEX_VIDEO_DESCRIPTION.search(self._html_content)
        if match:
            return html.unescape(match.group(1).strip())

        json_ld = self._parse_json_ld()
        if "description" in json_ld:
            return json_ld["description"]

        return None

    @cached_property
    def thumbnail(self) -> Optional[str]:
        """获取视频缩略图 URL"""
        if not self._html_content:
            return None

        match = REGEX_VIDEO_THUMBNAIL.search(self._html_content)
        if match:
            return match.group(1)

        json_ld = self._parse_json_ld()
        if "thumbnailUrl" in json_ld:
            return json_ld["thumbnailUrl"]

        return None

    @cached_property
    def duration(self) -> Optional[int]:
        """获取视频时长（秒）"""
        if not self._html_content:
            return None

        match = REGEX_VIDEO_DURATION.search(self._html_content)
        if match:
            try:
                duration_str = match.group(1).strip()
                if duration_str and duration_str.isdigit():
                    return int(duration_str)
            except (ValueError, TypeError):
                pass

        match = REGEX_VIDEO_DURATION_ALT.search(self._html_content)
        if match:
            try:
                duration_str = match.group(1).strip()
                if duration_str and duration_str.isdigit():
                    return int(duration_str)
            except (ValueError, TypeError):
                pass

        json_ld = self._parse_json_ld()
        if "duration" in json_ld:
            duration_str = json_ld["duration"]
            # ISO 8601 格式解析
            if isinstance(duration_str, str) and duration_str.startswith("PT"):
                return self._parse_iso_duration(duration_str)

        return None

    @staticmethod
    def _parse_iso_duration(duration_str: str) -> int:
        """
        解析 ISO 8601 时长格式

        Args:
            duration_str: ISO 8601 时长字符串 (如 "PT1H30M45S")

        Returns:
            秒数
        """
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str, re.IGNORECASE)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            return hours * 3600 + minutes * 60 + seconds
        return 0

    @property
    def duration_formatted(self) -> Optional[str]:
        """获取格式化的视频时长"""
        duration = self.duration
        if duration is None:
            return None

        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    @cached_property
    def views(self) -> Optional[int]:
        """获取观看次数"""
        if not self._html_content:
            return None

        match = REGEX_VIDEO_VIEWS.search(self._html_content)
        if match:
            views_str = match.group(1).replace(",", "").strip()
            if views_str and views_str.isdigit():
                return int(views_str)

        json_ld = self._parse_json_ld()
        if "interactionCount" in json_ld:
            try:
                return int(json_ld["interactionCount"])
            except (ValueError, TypeError):
                pass

        return None

    @cached_property
    def rating(self) -> Optional[float]:
        """获取视频评分"""
        if not self._html_content:
            return None

        match = REGEX_VIDEO_RATING.search(self._html_content)
        if match:
            try:
                rating_str = match.group(1).strip()
                if rating_str:
                    return float(rating_str)
            except (ValueError, TypeError):
                pass

        json_ld = self._parse_json_ld()
        if "aggregateRating_ratingValue" in json_ld:
            try:
                return float(json_ld["aggregateRating_ratingValue"])
            except (ValueError, TypeError):
                pass

        return None

    @cached_property
    def likes(self) -> Optional[int]:
        """获取点赞数"""
        if not self._html_content:
            return None

        match = REGEX_VIDEO_LIKES.search(self._html_content)
        if match:
            try:
                likes_str = match.group(1).replace(",", "").strip()
                if likes_str and likes_str.isdigit():
                    return int(likes_str)
            except (ValueError, TypeError):
                pass

        return None

    @cached_property
    def uploader(self) -> Optional[str]:
        """获取上传者"""
        if not self._html_content:
            return None

        match = REGEX_VIDEO_UPLOADER.search(self._html_content)
        if match:
            return match.group(1)

        match = REGEX_VIDEO_UPLOADER_ALT.search(self._html_content)
        if match:
            return match.group(1)

        json_ld = self._parse_json_ld()
        if "author_name" in json_ld:
            return json_ld["author_name"]

        return None

    @cached_property
    def tags(self) -> List[str]:
        """获取视频标签"""
        if not self._html_content:
            return []

        matches = REGEX_VIDEO_TAGS.findall(self._html_content)
        return list(set(matches))

    @cached_property
    def publish_date(self) -> Optional[str]:
        """获取发布日期"""
        if not self._html_content:
            return None

        match = REGEX_VIDEO_DATE.search(self._html_content)
        if match:
            return match.group(1)

        json_ld = self._parse_json_ld()
        if "uploadDate" in json_ld:
            return json_ld["uploadDate"]

        return None

    # ==================== 主播个人资料属性 ====================

    @cached_property
    def real_name(self) -> Optional[str]:
        """获取主播真名"""
        if not self._html_content:
            return None

        for pattern in [REGEX_PROFILE_REAL_NAME, REGEX_PROFILE_REAL_NAME_ALT]:
            match = pattern.search(self._html_content)
            if match:
                return html.unescape(match.group(1).strip())

        return None

    @cached_property
    def followers(self) -> Optional[int]:
        """获取关注者数量"""
        if not self._html_content:
            return None

        for pattern in [REGEX_PROFILE_FOLLOWERS, REGEX_PROFILE_FOLLOWERS_ALT, REGEX_PROFILE_FOLLOWERS_DATA]:
            match = pattern.search(self._html_content)
            if match:
                try:
                    return int(match.group(1).replace(",", "").strip())
                except (ValueError, TypeError):
                    continue

        return None

    @cached_property
    def gender(self) -> Optional[str]:
        """获取性别 (如: A Woman, A Man, A Couple, Trans)"""
        if not self._html_content:
            return None

        for pattern in [REGEX_PROFILE_GENDER, REGEX_PROFILE_GENDER_ALT, REGEX_PROFILE_GENDER_DATA]:
            match = pattern.search(self._html_content)
            if match:
                return html.unescape(match.group(1).strip())

        return None

    @cached_property
    def interested_in(self) -> Optional[str]:
        """获取兴趣对象 (如: 女性, 男士, 情侣, 跨性别者)"""
        if not self._html_content:
            return None

        for pattern in [REGEX_PROFILE_INTERESTS, REGEX_PROFILE_INTERESTS_ALT]:
            match = pattern.search(self._html_content)
            if match:
                return html.unescape(match.group(1).strip())

        return None

    @cached_property
    def location(self) -> Optional[str]:
        """获取位置/国家"""
        if not self._html_content:
            return None

        for pattern in [REGEX_PROFILE_LOCATION, REGEX_PROFILE_LOCATION_ALT, REGEX_PROFILE_LOCATION_DATA]:
            match = pattern.search(self._html_content)
            if match:
                return html.unescape(match.group(1).strip())

        return None

    @cached_property
    def last_broadcast(self) -> Optional[str]:
        """获取上次直播时间"""
        if not self._html_content:
            return None

        for pattern in [REGEX_PROFILE_LAST_BROADCAST, REGEX_PROFILE_LAST_BROADCAST_ALT]:
            match = pattern.search(self._html_content)
            if match:
                return html.unescape(match.group(1).strip())

        return None

    @cached_property
    def languages(self) -> Optional[str]:
        """获取语言"""
        if not self._html_content:
            return None

        for pattern in [REGEX_PROFILE_LANGUAGES, REGEX_PROFILE_LANGUAGES_ALT]:
            match = pattern.search(self._html_content)
            if match:
                return html.unescape(match.group(1).strip())

        return None

    @cached_property
    def body_type(self) -> Optional[str]:
        """获取体型"""
        if not self._html_content:
            return None

        for pattern in [REGEX_PROFILE_BODY_TYPE, REGEX_PROFILE_BODY_TYPE_ALT]:
            match = pattern.search(self._html_content)
            if match:
                return html.unescape(match.group(1).strip())

        return None

    @cached_property
    def body_decorations(self) -> Optional[str]:
        """获取身体装饰 (如: Ink-free, pierced ears)"""
        if not self._html_content:
            return None

        for pattern in [REGEX_PROFILE_BODY_DECORATIONS, REGEX_PROFILE_BODY_DECORATIONS_ALT]:
            match = pattern.search(self._html_content)
            if match:
                return html.unescape(match.group(1).strip())

        return None

    @cached_property
    def age(self) -> Optional[int]:
        """获取年龄"""
        if not self._html_content:
            return None

        for pattern in [REGEX_PROFILE_AGE, REGEX_PROFILE_AGE_ALT, REGEX_PROFILE_AGE_DATA]:
            match = pattern.search(self._html_content)
            if match:
                try:
                    return int(match.group(1).strip())
                except (ValueError, TypeError):
                    continue

        return None

    @cached_property
    def social_media(self) -> List[str]:
        """获取社交媒体链接列表"""
        if not self._html_content:
            return []

        matches = REGEX_PROFILE_SOCIAL_MEDIA.findall(self._html_content)
        # 去重并返回
        return list(set(matches))

    @cached_property
    def is_online(self) -> bool:
        """检查是否在线直播"""
        if not self._html_content:
            return False

        if REGEX_PROFILE_IS_ONLINE.search(self._html_content):
            return True
        if REGEX_PROFILE_IS_STREAMING.search(self._html_content):
            return True

        return False

    def _extract_video_sources(self) -> List[Dict[str, str]]:
        """
        提取所有可用的视频源

        Returns:
            视频源列表，每个元素包含 url 和 quality
        """
        if self._video_sources is not None:
            return self._video_sources

        self._video_sources = []

        if not self._html_content:
            return self._video_sources

        # 从 source 标签提取
        for match in REGEX_VIDEO_SOURCE.finditer(self._html_content):
            url = match.group(1)
            quality = self._detect_quality(url)
            self._video_sources.append({"url": url, "quality": quality, "format": self._detect_format(url)})

        # 从 MP4 链接提取
        for match in REGEX_VIDEO_SOURCE_MP4.finditer(self._html_content):
            url = match.group(1)
            if not any(s["url"] == url for s in self._video_sources):
                quality = self._detect_quality(url)
                self._video_sources.append({"url": url, "quality": quality, "format": "mp4"})

        # 从 M3U8 链接提取
        for match in REGEX_VIDEO_SOURCE_M3U8.finditer(self._html_content):
            url = match.group(1)
            if not any(s["url"] == url for s in self._video_sources):
                quality = self._detect_quality(url)
                self._video_sources.append({"url": url, "quality": quality, "format": "m3u8"})

        # 从 JS 变量提取
        for match in REGEX_VIDEO_SOURCE_JS.finditer(self._html_content):
            url = match.group(1)
            fmt = match.group(2).lower()
            if not any(s["url"] == url for s in self._video_sources):
                quality = self._detect_quality(url)
                self._video_sources.append({"url": url, "quality": quality, "format": fmt})

        # 从 JSON-LD 提取
        json_ld = self._parse_json_ld()
        if "contentUrl" in json_ld:
            url = json_ld["contentUrl"]
            if not any(s["url"] == url for s in self._video_sources):
                quality = self._detect_quality(url)
                self._video_sources.append({"url": url, "quality": quality, "format": self._detect_format(url)})

        return self._video_sources

    @staticmethod
    def _detect_quality(url: str) -> int:
        """
        从 URL 中检测视频质量

        Args:
            url: 视频 URL

        Returns:
            视频质量（如 720, 1080）
        """
        match = REGEX_VIDEO_QUALITY.search(url)
        if match:
            return int(match.group(1))
        return 0  # 未知质量

    @staticmethod
    def _detect_format(url: str) -> str:
        """
        从 URL 中检测视频格式

        Args:
            url: 视频 URL

        Returns:
            视频格式
        """
        url_lower = url.lower()
        if ".mp4" in url_lower:
            return "mp4"
        elif ".m3u8" in url_lower:
            return "m3u8"
        elif ".webm" in url_lower:
            return "webm"
        return "unknown"

    @property
    def video_sources(self) -> List[Dict[str, str]]:
        """获取所有视频源"""
        return self._extract_video_sources()

    @property
    def available_qualities(self) -> List[int]:
        """获取可用的视频质量列表"""
        sources = self._extract_video_sources()
        qualities = sorted(set(s["quality"] for s in sources if s["quality"] > 0), reverse=True)
        return qualities

    def get_video_url(self, quality: str = "best") -> Optional[str]:
        """
        获取指定质量的视频 URL

        Args:
            quality: 质量选项 (best/worst/half) 或具体数值 (720/1080)

        Returns:
            视频 URL
        """
        sources = self._extract_video_sources()
        if not sources:
            return None

        # 过滤出 MP4 格式
        mp4_sources = [s for s in sources if s["format"] == "mp4"]
        if not mp4_sources:
            mp4_sources = sources  # 如果没有 MP4，使用所有源

        # 按质量排序
        sorted_sources = sorted(mp4_sources, key=lambda x: x["quality"], reverse=True)

        if quality == "best":
            return sorted_sources[0]["url"]
        elif quality == "worst":
            return sorted_sources[-1]["url"]
        elif quality == "half":
            mid_idx = len(sorted_sources) // 2
            return sorted_sources[mid_idx]["url"]
        else:
            # 尝试匹配具体质量
            try:
                target_quality = int(quality.replace("p", ""))
                for source in sorted_sources:
                    if source["quality"] == target_quality:
                        return source["url"]
                # 没有精确匹配，返回最接近的
                closest = min(sorted_sources, key=lambda x: abs(x["quality"] - target_quality))
                return closest["url"]
            except ValueError:
                return sorted_sources[0]["url"]  # 默认返回最佳质量

    def to_dict(self) -> Dict[str, Any]:
        """
        将视频信息转换为字典

        Returns:
            视频信息字典
        """
        return {
            "video_id": self.video_id,
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "thumbnail": self.thumbnail,
            "duration": self.duration,
            "duration_formatted": self.duration_formatted,
            "views": self.views,
            "rating": self.rating,
            "likes": self.likes,
            "uploader": self.uploader,
            "tags": self.tags,
            "publish_date": self.publish_date,
            "available_qualities": self.available_qualities,
            # 主播个人资料
            "real_name": self.real_name,
            "followers": self.followers,
            "gender": self.gender,
            "interested_in": self.interested_in,
            "location": self.location,
            "last_broadcast": self.last_broadcast,
            "languages": self.languages,
            "body_type": self.body_type,
            "body_decorations": self.body_decorations,
            "age": self.age,
            "social_media": self.social_media,
            "is_online": self.is_online,
        }

    def __repr__(self) -> str:
        return f"Video(id={self.video_id}, title={self.title})"