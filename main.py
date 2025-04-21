from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api.all import *
from typing import Optional
import aiohttp

async def Get_Weather(location: Optional[str] = None, api_key: Optional[str] = None) -> str:
    """获取指定位置的天气状况（如：晴、雨等）
    
    Args:
        location (Optional[str]): 城市名称（如 "Beijing"），如果为 None，则自动检测当前位置
    
    Returns:
        str: 天气状况（如 "Sunny"），如果请求失败则返回空字符串 ""
    """
    try:
        geo_api_url = f'https://geoapi.qweather.com/v2/city/lookup?key={api_key}&number=1&location={location}'
        conn_ssl = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.request('GET', url=geo_api_url, connector=conn_ssl) as response:
            geoapi_json = await response.json()
            await conn_ssl.close()

        if geoapi_json['code'] == '404':
            return "查不到这个城市的天气。"

        elif geoapi_json['code'] != '200':
            return f"查询失败：{geoapi_json}"

        country = geoapi_json["location"][0]["country"]
        adm1 = geoapi_json["location"][0]["adm1"]
        adm2 = geoapi_json["location"][0]["adm2"]
        city_id = geoapi_json["location"][0]["id"]

        # 请求现在天气api
        conn_ssl = aiohttp.TCPConnector(verify_ssl=False)
        now_weather_api_url = f'https://devapi.qweather.com/v7/weather/now?key={api_key}&location={city_id}'
        async with aiohttp.request('GET', url=now_weather_api_url, connector=conn_ssl) as response:
            now_weather_api_json = await response.json()
            await conn_ssl.close()

        # 请求预报天气api
        conn_ssl = aiohttp.TCPConnector(verify_ssl=False)
        weather_forecast_api_url = f'https://devapi.qweather.com/v7/weather/7d?key={api_key}&location={city_id}'
        async with aiohttp.request('GET', url=weather_forecast_api_url, connector=conn_ssl) as response:
            weather_forecast_api_json = await response.json()
            await conn_ssl.close()
        out_message = compose_weather_message(country, adm1, adm2, now_weather_api_json, weather_forecast_api_json)
        return out_message
    except aiohttp.ClientError as e:
        print(f"请求失败: {e}")
        return ""
@staticmethod
def compose_weather_message(country, adm1, adm2, now_weather_api_json, weather_forecast_api_json):
    update_time = now_weather_api_json['updateTime']
    now_temperature = now_weather_api_json['now']['temp']
    now_feelslike = now_weather_api_json['now']['feelsLike']
    now_weather = now_weather_api_json['now']['text']
    now_wind_direction = now_weather_api_json['now']['windDir']
    now_wind_scale = now_weather_api_json['now']['windScale']
    now_humidity = now_weather_api_json['now']['humidity']
    now_precip = now_weather_api_json['now']['precip']
    now_visibility = now_weather_api_json['now']['vis']
    now_uvindex = weather_forecast_api_json['daily'][0]['uvIndex']

    message = (
        f"{country}{adm1}{adm2} 实时天气☁️\n"
        f"⏰更新时间：{update_time}\n\n"
        f"🌡️当前温度：{now_temperature}℃\n"
        f"🌡️体感温度：{now_feelslike}℃\n"
        f"☁️天气：{now_weather}\n"
        f"☀️紫外线指数：{now_uvindex}\n"
        f"🌬️风向：{now_wind_direction}\n"
        f"🌬️风力：{now_wind_scale}级\n"
        f"💦湿度：{now_humidity}%\n"
        f"🌧️降水量：{now_precip}mm/h\n"
        f"👀能见度：{now_visibility}km\n\n"
        f"☁️未来3天 {adm2} 天气：\n"
    )
    for day in weather_forecast_api_json['daily'][1:4]:
        date = '.'.join([i.lstrip('0') for i in day['fxDate'].split('-')[1:]])
        weather = day['textDay']
        max_temp = day['tempMax']
        min_temp = day['tempMin']
        uv_index = day['uvIndex']
        message += f'{date} {weather} 最高🌡️{max_temp}℃ 最低🌡️{min_temp}℃ ☀️紫外线:{uv_index}\n'

    return message

@register("astrbot_plugin_weather_wttr_in", "xiewoc", "使用wttr.in查询天气的llm工具", "1.0.1", "https://github.com/xiewoc/astrbot_plugin_weather_wttr_in")
class astrbot_plugin_weather_wttr_in(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.weather_api_key = config.get("weather_api_key", "")
    
    @llm_tool(name="get_weather") 
    async def get_weather(self, event: AstrMessageEvent, location: Optional[str] = None) -> MessageEventResult:
        '''天气查询工具，获取指定地点的实时及未来3天天气信息。

        Args:
            location(string): 地点（仅支持中文，如：北京）
        '''
        if not self.weather_api_key:
            return "current weather(condition,temperature,wind,location): 天气查询工具暂不可用。"
        resp = "current weather(condition,temperature,wind,location):" + str(await Get_Weather(location, self.weather_api_key))
        return resp
