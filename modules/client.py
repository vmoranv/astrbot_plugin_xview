"""
XView API Client 类
用于发送 HTTP 请求和管理会话
"""
import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin

from .consts import ROOT_URL, HEADERS, DEFAULT_TIMEOUT, REQUEST_TIMEOUT
from .errors import NetworkError, VideoNotFound
from .video import Video


class Client:
    """
    XView API 客户端类
    """

    def __init__(self, proxy: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT):
        """
        初始化客户端

        Args:
            proxy: 代理地址 (如 "http://127.0.0.1:7890")
            timeout: 请求超时时间（秒）
        """
        self.proxy = proxy
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger("XView API - [Client]")

    async def _get_session(self) -> aiohttp.ClientSession:
        """
        获取或创建 aiohttp 会话

        Returns:
            aiohttp.ClientSession
        """
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                ttl_dns_cache=300,
                use_dns_cache=True,
                ssl=False,  # 禁用 SSL 验证
            )
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=HEADERS,
                trust_env=True,
            )
        return self._session

    async def close(self) -> None:
        """关闭会话"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    async def fetch(self, url: str, method: str = "GET", **kwargs) -> str:
        """
        发送 HTTP 请求

        Args:
            url: 请求 URL
            method: HTTP 方法
            **kwargs: 其他 aiohttp 请求参数

        Returns:
            响应文本

        Raises:
            NetworkError: 网络请求失败
        """
        session = await self._get_session()

        # 设置代理
        if self.proxy:
            kwargs["proxy"] = self.proxy

        try:
            async with session.request(method, url, **kwargs) as response:
                if response.status == 404:
                    raise VideoNotFound(f"页面不存在: {url}")
                response.raise_for_status()
                return await response.text()
        except aiohttp.ClientError as e:
            self.logger.error(f"网络请求失败: {e}")
            raise NetworkError(f"网络请求失败: {str(e)}")
        except asyncio.TimeoutError:
            self.logger.error(f"请求超时: {url}")
            raise NetworkError(f"请求超时: {url}")

    async def fetch_bytes(self, url: str, method: str = "GET", **kwargs) -> bytes:
        """
        发送 HTTP 请求并返回字节数据

        Args:
            url: 请求 URL
            method: HTTP 方法
            **kwargs: 其他 aiohttp 请求参数

        Returns:
            响应字节数据
        """
        session = await self._get_session()

        if self.proxy:
            kwargs["proxy"] = self.proxy

        try:
            async with session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                return await response.read()
        except aiohttp.ClientError as e:
            self.logger.error(f"网络请求失败: {e}")
            raise NetworkError(f"网络请求失败: {str(e)}")

    async def get_video(self, video_id: str) -> Video:
        """
        获取视频/房间对象

        Args:
            video_id: 视频 ID、用户名或 URL

        Returns:
            Video 对象
        """
        # 判断是 ID 还是 URL
        if video_id.startswith(("http://", "https://")):
            video = Video.from_url(video_id)
        else:
            video = Video(video_id)

        # 正确的 URL 格式是直接 /{username}/
        # xview.tv 只使用这种格式，不使用 /room/ 或 /video/
        urls_to_try = [
            f"{ROOT_URL}{video.video_id}/",  # 正确格式: /{username}/
        ]

        html_content = None
        last_error = None

        for url in urls_to_try:
            try:
                html_content = await self.fetch(url)
                if html_content and len(html_content) > 1000:
                    video.url = url
                    break
            except Exception as e:
                last_error = e
                continue

        if not html_content:
            if last_error:
                raise last_error
            raise VideoNotFound(f"无法获取视频/房间: {video_id}")

        video.set_html_content(html_content)
        return video

    async def get_video_info(self, video_id: str) -> Dict[str, Any]:
        """
        获取视频信息字典

        Args:
            video_id: 视频 ID 或 URL

        Returns:
            视频信息字典
        """
        video = await self.get_video(video_id)
        return video.to_dict()

    async def get_video_url(self, video_id: str, quality: str = "best") -> Optional[str]:
        """
        获取视频播放 URL

        Args:
            video_id: 视频 ID 或 URL
            quality: 质量选项 (best/worst/half 或具体数值)

        Returns:
            视频播放 URL
        """
        video = await self.get_video(video_id)
        return video.get_video_url(quality)

    async def get_thumbnail(self, video_id: str) -> Optional[str]:
        """
        获取视频缩略图 URL

        Args:
            video_id: 视频 ID 或 URL

        Returns:
            缩略图 URL
        """
        video = await self.get_video(video_id)
        return video.thumbnail

    async def download_thumbnail(self, video_id: str, blur_level: int = 0) -> Optional[bytes]:
        """
        下载视频缩略图

        Args:
            video_id: 视频 ID 或 URL
            blur_level: 模糊程度 (0-100)

        Returns:
            缩略图字节数据
        """
        video = await self.get_video(video_id)
        thumbnail_url = video.thumbnail

        if not thumbnail_url:
            return None

        try:
            image_data = await self.fetch_bytes(thumbnail_url)

            # 如果需要模糊处理
            if blur_level > 0:
                image_data = await self._blur_image(image_data, blur_level)

            return image_data
        except Exception as e:
            self.logger.error(f"下载缩略图失败: {e}")
            return None

    async def _blur_image(self, image_data: bytes, blur_level: int) -> bytes:
        """
        对图片进行模糊处理

        Args:
            image_data: 原始图片数据
            blur_level: 模糊程度 (0-100)

        Returns:
            模糊后的图片数据
        """
        try:
            from PIL import Image, ImageFilter
            import io

            # 将字节转换为 PIL Image
            img = Image.open(io.BytesIO(image_data))

            # 计算模糊半径（基于模糊程度）
            # blur_level 0-100 映射到 radius 0-50
            radius = blur_level / 2

            # 应用高斯模糊
            blurred = img.filter(ImageFilter.GaussianBlur(radius=radius))

            # 如果模糊程度很高，添加像素化效果
            if blur_level > 50:
                # 缩小再放大以产生马赛克效果
                factor = max(1, (blur_level - 50) // 10)
                small_size = (max(1, img.width // (factor * 2)), max(1, img.height // (factor * 2)))
                blurred = blurred.resize(small_size, Image.NEAREST)
                blurred = blurred.resize(img.size, Image.NEAREST)

            # 转换回字节
            output = io.BytesIO()
            blurred.save(output, format='JPEG', quality=85)
            return output.getvalue()

        except ImportError:
            self.logger.warning("PIL 未安装，无法进行图片模糊处理")
            return image_data
        except Exception as e:
            self.logger.error(f"图片模糊处理失败: {e}")
            return image_data

    async def search(self, query: str, page: int = 1) -> List[Dict[str, Any]]:
        """
        搜索视频/房间

        Args:
            query: 搜索关键词
            page: 页码

        Returns:
            视频/房间信息列表
        """
        # 尝试多种搜索 URL 格式
        search_urls = [
            f"{ROOT_URL}?keywords={query}&page={page}",
            f"{ROOT_URL}search/{query}/?page={page}",
            f"{ROOT_URL}tag/{query}/?page={page}",
            f"{ROOT_URL}api/public/cams/?keywords={query}&page={page}",
        ]

        for search_url in search_urls:
            try:
                html_content = await self.fetch(search_url)
                # 解析搜索结果
                videos = self._parse_search_results(html_content)
                if videos:
                    return videos
            except Exception as e:
                self.logger.debug(f"搜索 URL {search_url} 失败: {e}")
                continue

        # 如果所有 URL 都失败，返回空列表
        self.logger.warning(f"搜索 '{query}' 未找到结果")
        return []

    def _parse_search_results(self, html_content: str) -> List[Dict[str, Any]]:
        """
        解析搜索结果页面

        Args:
            html_content: HTML 内容

        Returns:
            视频/房间信息列表
        """
        import re
        from .consts import REGEX_VIDEO_ID

        results = []
        
        # 模式1: 提取房间/视频链接 - 匹配类似 /room/username 或 /video/123 的链接
        room_pattern = re.compile(
            r'<a[^>]+href=["\']/?(?:room|video|profile)/([^"\'/]+)["\'][^>]*>',
            re.DOTALL | re.IGNORECASE
        )
        
        # 模式2: 提取带缩略图的链接（暂不使用，保留备用）
        # thumb_pattern = re.compile(
        #     r'<a[^>]+href=["\']([^"\']*/(?:room|video|profile)/[^"\'/]+)["\'][^>]*>.*?<img[^>]+src=["\']([^"\']+-thumb[^"\']*)["\']',
        #     re.DOTALL | re.IGNORECASE
        # )

        # 模式3: 提取用户名/房间名
        username_pattern = re.compile(
            r'data-(?:username|room|id)=["\']([^"\'/]+)["\']',
            re.IGNORECASE
        )
        
        # 模式4: JSON 数据中的房间信息
        json_room_pattern = re.compile(
            r'["\'](?:username|room_id|id)["\']\s*:\s*["\']([^"\'/]+)["\']',
            re.IGNORECASE
        )

        seen_ids = set()
        
        # 尝试模式1
        for match in room_pattern.finditer(html_content):
            room_id = match.group(1)
            if room_id and room_id not in seen_ids and not room_id.startswith(('css', 'js', 'static')):
                seen_ids.add(room_id)
                results.append({
                    "video_id": room_id,
                    "url": f"{ROOT_URL}{room_id}/",  # 正确格式: /{username}/
                    "thumbnail": "",
                })
        
        # 尝试模式3（如果模式1没找到结果）
        if not results:
            for match in username_pattern.finditer(html_content):
                username = match.group(1)
                if username and username not in seen_ids:
                    seen_ids.add(username)
                    results.append({
                        "video_id": username,
                        "url": f"{ROOT_URL}{username}/",  # 正确格式: /{username}/
                        "thumbnail": "",
                    })
        
        # 尝试模式4
        if not results:
            for match in json_room_pattern.finditer(html_content):
                room_id = match.group(1)
                if room_id and room_id not in seen_ids and len(room_id) > 2:
                    seen_ids.add(room_id)
                    results.append({
                        "video_id": room_id,
                        "url": f"{ROOT_URL}{room_id}/",  # 正确格式: /{username}/
                        "thumbnail": "",
                    })

        return results[:20]  # 最多返回20个结果

    async def get_categories(self) -> List[Dict[str, str]]:
        """
        获取分类列表

        Returns:
            分类列表
        """
        # TODO: 实现分类获取功能
        return []

    async def get_videos_by_category(self, category: str, page: int = 1) -> List[Dict[str, Any]]:
        """
        按分类获取视频

        Args:
            category: 分类名称
            page: 页码

        Returns:
            视频信息列表
        """
        category_url = f"{ROOT_URL}category/{category}?page={page}"

        try:
            html_content = await self.fetch(category_url)
            videos = self._parse_search_results(html_content)
            return videos
        except Exception as e:
            self.logger.error(f"获取分类视频失败: {e}")
            return []