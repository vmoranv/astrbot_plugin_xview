"""
XView AstrBot 插件
用于解析 https://secure.xview.tv/ 网站视频信息
"""
import os
import asyncio
import traceback
from pathlib import Path
from typing import Optional, Dict, Any

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp
from astrbot.api.event import MessageChain

try:
    from .modules.client import Client
    from .modules.video import Video
    from .modules.errors import (
        XViewError,
        VideoNotFound,
        VideoDisabled,
        InvalidURL,
        NetworkError,
    )
    from .modules.consts import ROOT_URL
except ImportError:
    from modules.client import Client
    from modules.video import Video
    from modules.errors import (
        XViewError,
        VideoNotFound,
        VideoDisabled,
        InvalidURL,
        NetworkError,
    )
    from modules.consts import ROOT_URL


@register("astrbot_plugin_xview", "vmoranv", "XView 视频解析插件，支持获取视频信息、缩略图等", "1.0.0")
class XViewPlugin(Star):
    """XView 视频解析插件"""

    def __init__(self, context: Context):
        super().__init__(context)
        self._client: Optional[Client] = None
        self._cache_dir: Optional[Path] = None
        self._last_cache_files: list = []

    async def initialize(self):
        """插件初始化"""
        logger.info("XView 插件正在初始化...")

        # 创建缓存目录
        data_path = Path(os.path.dirname(__file__)) / "data"
        self._cache_dir = data_path / "cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        # 初始化客户端
        proxy = self._get_config("proxy", "")
        timeout = self._get_config("timeout", 30)
        self._client = Client(proxy=proxy if proxy else None, timeout=timeout)

        logger.info("XView 插件初始化完成")

    async def terminate(self):
        """插件销毁"""
        logger.info("XView 插件正在销毁...")

        if self._client:
            await self._client.close()

        await self._cleanup_cache()

        logger.info("XView 插件已销毁")

    def _get_config(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        try:
            config = self.context.get_config()
            plugin_config = config.get("astrbot_plugin_xview", {})
            return plugin_config.get(key, default)
        except Exception:
            return default

    async def _cleanup_cache(self):
        """清理上次发送的缓存文件"""
        for file_path in self._last_cache_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"已清理缓存文件: {file_path}")
            except Exception as e:
                logger.warning(f"清理缓存文件失败: {e}")

        self._last_cache_files.clear()

    async def _save_thumbnail(self, image_data: bytes, video_id: str) -> str:
        """保存缩略图到缓存"""
        file_path = self._cache_dir / f"thumb_{video_id}.jpg"
        with open(file_path, "wb") as f:
            f.write(image_data)
        self._last_cache_files.append(str(file_path))
        return str(file_path)

    def _format_video_info(self, video: Video) -> str:
        """格式化视频完整信息"""
        lines = []
        lines.append(f"🎬 标题: {video.title or '未知'}")
        lines.append(f"🆔 ID: {video.video_id}")

        if video.duration_formatted:
            lines.append(f"⏱️ 时长: {video.duration_formatted}")

        if video.views:
            lines.append(f"👁️ 观看: {video.views:,}")

        if video.rating:
            lines.append(f"⭐ 评分: {video.rating}")

        if video.likes:
            lines.append(f"👍 点赞: {video.likes:,}")

        if video.uploader:
            lines.append(f"👤 上传者: {video.uploader}")

        if video.publish_date:
            lines.append(f"📅 发布: {video.publish_date}")

        if video.tags:
            tags_str = ", ".join(video.tags[:5])
            if len(video.tags) > 5:
                tags_str += f" (+{len(video.tags) - 5})"
            lines.append(f"🏷️ 标签: {tags_str}")

        if video.available_qualities:
            qualities_str = ", ".join(f"{q}p" for q in video.available_qualities[:5])
            lines.append(f"📺 可用质量: {qualities_str}")

        lines.append(f"🔗 链接: {video.url}")

        return "\n".join(lines) + "\u200E"

    def _format_error(self, error: Exception) -> str:
        """格式化错误信息"""
        if isinstance(error, VideoNotFound):
            return f"❌ 视频不存在或已被删除\u200E"
        elif isinstance(error, VideoDisabled):
            return f"❌ 视频已被禁用或因版权问题被删除\u200E"
        elif isinstance(error, InvalidURL):
            return f"❌ 无效的视频 ID\u200E"
        elif isinstance(error, NetworkError):
            return f"❌ 网络请求失败，请检查网络连接或代理设置\u200E"
        elif isinstance(error, XViewError):
            return f"❌ {str(error)}\u200E"
        else:
            return f"❌ 发生未知错误: {str(error)}\u200E"

    @filter.command("xview")
    async def cmd_video_info(self, event: AstrMessageEvent, video_id: str = ""):
        """
        获取视频完整信息（带缩略图）
        用法: /xview <ID>
        """
        await self._cleanup_cache()

        if not video_id:
            yield event.plain_result("❌ 请提供视频 ID\n用法: /xview <ID>\u200E")
            return

        try:
            video = await self._client.get_video(video_id)
            info_text = self._format_video_info(video)

            # 获取缩略图
            blur_level = self._get_config("blur_level", 0)
            thumbnail_data = await self._client.download_thumbnail(video_id, blur_level)

            if thumbnail_data:
                thumb_path = await self._save_thumbnail(thumbnail_data, video.video_id)
                chain = [
                    Comp.Image.fromFileSystem(thumb_path),
                    Comp.Plain(info_text),
                ]
                yield event.chain_result(chain)
            else:
                yield event.plain_result(info_text)

        except Exception as e:
            logger.error(f"获取视频信息失败: {traceback.format_exc()}")
            yield event.plain_result(self._format_error(e))

    @filter.command("xview_link")
    async def cmd_video_link(self, event: AstrMessageEvent, video_id: str = "", quality: str = "best"):
        """
        获取视频播放链接
        用法: /xview_link <ID> [质量]
        质量: best/worst/half 或 720/1080
        """
        await self._cleanup_cache()

        if not video_id:
            yield event.plain_result("❌ 请提供视频 ID\n用法: /xview_link <ID> [质量]\u200E")
            return

        try:
            video = await self._client.get_video(video_id)
            video_url = video.get_video_url(quality)
            if video_url:
                yield event.plain_result(f"🔗 播放链接 ({quality}):\n{video_url}\u200E")
            else:
                yield event.plain_result("❌ 未找到视频播放链接\u200E")
        except Exception as e:
            logger.error(f"获取视频链接失败: {traceback.format_exc()}")
            yield event.plain_result(self._format_error(e))

    @filter.command("xview_pic")
    async def cmd_video_thumbnail(self, event: AstrMessageEvent, video_id: str = ""):
        """
        获取视频缩略图
        用法: /xview_pic <ID>
        """
        await self._cleanup_cache()

        if not video_id:
            yield event.plain_result("❌ 请提供视频 ID\n用法: /xview_pic <ID>\u200E")
            return

        try:
            blur_level = self._get_config("blur_level", 0)
            thumbnail_data = await self._client.download_thumbnail(video_id, blur_level)

            if thumbnail_data:
                video = await self._client.get_video(video_id)
                thumb_path = await self._save_thumbnail(thumbnail_data, video.video_id)

                chain = [
                    Comp.Image.fromFileSystem(thumb_path),
                    Comp.Plain(f"📷 {video.title or video_id}\u200E"),
                ]
                yield event.chain_result(chain)
            else:
                yield event.plain_result("❌ 未找到缩略图\u200E")
        except Exception as e:
            logger.error(f"获取缩略图失败: {traceback.format_exc()}")
            yield event.plain_result(self._format_error(e))

    @filter.command("xview_search")
    async def cmd_search(self, event: AstrMessageEvent, query: str = ""):
        """
        搜索视频
        用法: /xview_search <关键词>
        """
        await self._cleanup_cache()

        if not query:
            yield event.plain_result("❌ 请提供搜索关键词\n用法: /xview_search <关键词>\u200E")
            return

        try:
            results = await self._client.search(query)
            if results:
                lines = [f"🔍 搜索 \"{query}\" 结果:"]
                for i, item in enumerate(results[:10], 1):
                    lines.append(f"{i}. {item['video_id']}")
                lines.append("\n💡 使用 /xview <ID> 获取详情")
                yield event.plain_result("\n".join(lines) + "\u200E")
            else:
                yield event.plain_result(f"🔍 未找到 \"{query}\" 相关视频\u200E")
        except Exception as e:
            logger.error(f"搜索失败: {traceback.format_exc()}")
            yield event.plain_result(self._format_error(e))
