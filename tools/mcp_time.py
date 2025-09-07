from mcp.server.fastmcp import FastMCP

import datetime

mcp = FastMCP("Time", port=1234)

@mcp.tool()
async def get_time_by_timezone(timezone: str = "Asia/Shanghai") -> str:
    """
    获取指定时区的当前时间，返回格式如 2025-09-06 15:30:00。参数 timezone 例如 'Asia/Shanghai'、'UTC'、'America/New_York'。
    """
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo(timezone)
        now = datetime.datetime.now(tz)
        return now.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        # 回退到北京时间
        utc_now = datetime.datetime.utcnow()
        beijing_now = utc_now + datetime.timedelta(hours=8)
        return beijing_now.strftime("%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    mcp.run(transport="stdio")