from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api.all import *
from typing import Optional
import aiohttp

async def Get_Weather(location: Optional[str] = None) -> str:
    """获取指定位置的天气状况（如：晴、雨等）
    
    Args:
        location (Optional[str]): 城市名称（如 "Beijing"），如果为 None，则自动检测当前位置
    
    Returns:
        str: 天气状况（如 "Sunny"），如果请求失败则返回空字符串 ""
    """
    # 构造基本 URL
    base_url = "https://wttr.in"
    
    # 如果 location 不为 None，则添加到 URL 路径
    if location:
        url = f"{base_url}/{location}"
    else:
        url = base_url

    # 设置查询参数
    params = {
        "format": "%C+%t+%w+%l"  # 天气，实际温度，风，地点
    }

    try:
        # 使用 aiohttp 发送异步 GET 请求
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()  # 如果状态码不是 200，抛出异常

                weather_condition = (await response.text()).strip()
                print(f"当前天气状况: {weather_condition}")
                return weather_condition

    except aiohttp.ClientError as e:
        print(f"请求失败: {e}")
        return ""

@register("astrbot_plugin_weather_wttr_in", "xiewoc", "使用wttr.in查询天气的llm工具", "1.0.0", "https://github.com/xiewoc/astrbot_plugin_weather_wttr_in")
class astrbot_plugin_weather_wttr_in(Star):
    def __init__(self, context: Context):
        super().__init__(context)
    
    @llm_tool(name="get_weather") 
    async def get_weather(self, event: AstrMessageEvent, location: Optional[str] = None) -> MessageEventResult:
        '''获取天气信息。

        Args:
            location(string): 地点（地点为英文名，eg. Beijing，若用户未声明地点或要查询当前地点的天气则为''）
        '''
        resp = "current weather(condition,temperature,wind,location):" + str(await Get_Weather(location))
        return resp
