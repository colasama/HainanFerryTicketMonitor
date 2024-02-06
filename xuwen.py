import requests
import json
import time
from datetime import datetime
from loguru import logger
from bs4 import BeautifulSoup

LOG_FILE = logger.add('./logs/xw_tickets_'+ str(time.strftime("%Y_%m_%d_%H_%M")) + '.log') # 添加Log File
SERVERCHAN_TOKEN = "" # 用于原版方糖的推送TOKEN
PUSHPLUS_TOKEN = "" # 用于PushPlus的推送TOKEN
PUSHPLUS_GROUP_ID = "" # 用于PushPlus的推送分组ID
XY_TARGET_URL = "http://hxwx.digitalstrait.cn/WxFerryMobile/FlightList/Index?shipLineCode=HKHA&portCode=101&ticketTypeCode=2&energyTypeCode=0&carTypeCode=12&carTypeName=%E5%B0%8F%E5%9E%8B%E5%AE%A2%E8%BD%A6%EF%BC%8812%E5%BA%A7%E4%BB%A5%E4%B8%8B%EF%BC%89%E3%80%81%E8%BD%BF%E8%BD%A6"
XH_TARGET_URL = "http://hxwx.digitalstrait.cn/WxFerryMobile/FlightList/Index?shipLineCode=HKHA&portCode=102&ticketTypeCode=2&energyTypeCode=0&carTypeCode=12&carTypeName=%E5%B0%8F%E5%9E%8B%E5%AE%A2%E8%BD%A6%EF%BC%8812%E5%BA%A7%E4%BB%A5%E4%B8%8B%EF%BC%89%E3%80%81%E8%BD%BF%E8%BD%A6"
TARGET_URLS = [XH_TARGET_URL, XY_TARGET_URL]
TARGET_PORT_NAMES = ["新海港", "秀英港"]
PUSH_INTERVAL = 60 # 每次推送间隔时间，单位为秒
DATE_LIST = ["6", "7", "8"]
header = {'Cookie': 'SF_cookie_2=xxx; ASP.NET_SessionId=xxx; ShipLine=1; StartPort=2; TicketType=2; EnergyType=0'}

# DATE_LIST = ["2024-02-04"]
last_push_time = 0 # 上次推送时间
total_push_times = 0

# 获取票据数据，返回值为request本体，尽可能保证交付到正常数据
def get_tickets(target_url, date, retry_times):
    # 超过8次则选择失败，不是很优雅
    if retry_times == 8:
        return None
    
    # 获取票据数据
    r = requests.get(target_url + "&clickDay=2024-2-" + date, headers=header, verify=False, timeout=15)

    # 正常获取到了数据
    if r.status_code == 200:
        logger.info("成功获取到了" + date + "的数据！")
        return r
            
    # 获取失败，重试
    else:
        logger.info("第" + str(retry_times) + "次尝试，正在重新获取...")
        return get_tickets(date, retry_times + 1)
    
    return r


# 推送有票通知
def push(port_name, date):
    global last_push_time
    delta_time = datetime.now().timestamp() - last_push_time
    
    if delta_time < PUSH_INTERVAL:
        logger.warning("还有" + str(round(PUSH_INTERVAL - delta_time, 2)) + "秒才能继续推送。")
        return
    else:
        # 格式化日期显示
        date_str = port_name + " 2 月 "
        for d in date:
            date_str = date_str + d + " "
        data = {"title": date_str + "日有票", "desp": "Null"}
        # 推送ServerChan
        requests.post(url="https://sctapi.ftqq.com/"+ SERVERCHAN_TOKEN + ".send", headers=header, json=data)
        # 推送PushPlus
        pp_data = {"token": PUSHPLUS_TOKEN, "title": date_str + "日有票", "content": "Null", "topic": PUSHPLUS_GROUP_ID}
        requests.post(url="http://www.pushplus.plus/send", headers=header, json=pp_data)

        # 成功推送并修改推送时间
        logger.success(date_str + "日有票信息成功推送！")
        last_push_time = datetime.now().timestamp()

    
# Main
if __name__ == "__main__":
    # 关闭SSL提醒
    requests.packages.urllib3.disable_warnings()
    while True:
        push_dates = set()
        push_content = []
        for url in TARGET_URLS:
            for date in DATE_LIST:
                # Get the request
                logger.info(date + " 数据获取中...")
                # 获取票务信息
                r = None
                try:
                    r = get_tickets(url, date, 0)
                except Exception as e:
                    logger.error("出现错误：" + str(e))
                if r == None:
                    logger.error(date + "获取失败，进行下一个获取...")
                else:
                    try:
                        bs = BeautifulSoup(r.content.decode("utf8"), 'lxml')
                        for target in bs.find_all(class_="shiplinebtn"):
                            if "售完" in str(target):
                                pass
                            else:
                                push_dates.add(date)
                    except KeyError as e:
                        logger.error("键值错误：" + str(e))
                    except Exception as e:
                        logger.error("出现错误：" + str(e))
        # 如果推送列表不为空，则推送
        if len(push_dates) != 0:
            if url == XH_TARGET_URL:
                push(TARGET_PORT_NAMES[0], push_dates)
            else:
                push(TARGET_PORT_NAMES[1], push_dates)
        else:
            logger.info("现在还没有票票...")
        logger.info("休眠30秒，准备进行下一轮获取。")
        time.sleep(30)