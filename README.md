# XView AstrBot 插件

[![GitHub](https://img.shields.io/badge/GitHub-vmoranv/astrbot__plugin__xview-blue)](https://github.com/vmoranv/astrbot_plugin_xview)

XView 视频解析插件，用于解析 https://secure.xview.tv/ 网站的视频信息。

> ⚠️ **重要**: 
> - xview.tv 是一个**直播平台**（类似 Chaturbate）
> - 需要配置代理才能访问
> - 搜索功能受网站限制，可能无法使用
> - **建议直接从网站获取用户名/ID 来使用**

## 安装

```bash
pip install aiohttp Pillow
```

将插件目录复制到 AstrBot 的 `addons/plugins/` 目录下。

## 配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `proxy` | string | "" | 代理地址（如 `http://127.0.0.1:7890`）**必须** |
| `timeout` | int | 30 | 请求超时时间（秒） |
| `blur_level` | int | 0 | 缩略图模糊程度（0-100，0为不模糊） |

## 命令

| 命令 | 说明 | 用法 |
|------|------|------|
| `/xview <ID>` | 获取完整信息+缩略图 | `/xview username` |
| `/xview_link <ID> [质量]` | 获取播放链接 | `/xview_link username best` |
| `/xview_pic <ID>` | 仅获取缩略图 | `/xview_pic username` |
| `/xview_search <关键词>` | 搜索（受限） | `/xview_search keyword` |

## ⚠️ 如何获取 ID（重要）

由于这是一个直播平台，**必须手动获取 ID**：

1. 访问 https://secure.xview.tv/（需要代理）
2. 在首页找到一个直播间
3. 点击进入，从 URL 中获取用户名
   - URL 格式：`https://secure.xview.tv/房间名`
   - 例如：`https://secure.xview.tv/jenny_taborda` → ID 为 `jenny_taborda`

## 实际使用示例

```bash
# 假设从网站获取到的用户名是 jenny_taborda
/xview jenny_taborda

# 获取播放链接
/xview_link jenny_taborda best

# 获取缩略图
/xview_pic jenny_taborda
```

## 测试

运行真实参数测试脚本验证API功能：

```bash
# 使用默认用户名测试
python test_real.py

# 指定用户名
python test_real.py valerie_james3

# 使用命名参数
python test_real.py --id valerie_james3 --search latina

# 配置代理
python test_real.py --proxy http://127.0.0.1:7890 --id username

# 交互模式
python test_real.py -i
```

## 注意事项

1. **必须配置代理**：该网站需要代理才能访问
2. **搜索功能受限**：由于网站限制，搜索功能可能无法使用，建议直接从网站获取 ID
3. **ID 来源**：ID 是网站上的用户名/房间名，需要自己从网站获取
4. **模糊处理**：缩略图支持模糊处理（需要安装 Pillow）
5. **429限流**：短时间内多次请求可能触发限流，测试脚本自动添加延迟

## License

MIT License
