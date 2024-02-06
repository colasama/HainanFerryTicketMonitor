import requests
import json
import time
from datetime import datetime
from loguru import logger

LOG_FILE = logger.add('./logs/tickets_'+ str(time.strftime("%Y_%m_%d_%H_%M")) + '.log') # 添加Log File
SERVERCHAN_TOKEN = "" # 用于原版Server酱的推送TOKEN
PUSHPLUS_TOKEN = "" # 用于PushPlus的推送TOKEN
PUSHPLUS_GROUP_ID = "" # 用于PushPlus的推送分组ID
PUSH_INTERVAL = 180 # 每次推送间隔时间，单位为秒
DATE_LIST = ["2024-02-06", "2024-02-07", "2024-02-08"]
TARGET_URL = "https://wx.17u.cn/shipapi/ShipVoyageApi/QueryVoyages"

header = {'content-type': 'application/json'}
payload = {"SupplierId":0,
           "DepartDate":"2024-02-05",
           "LineId":"1647",
           "IsRoundTrip":0,
           "IsReturn":0,
           "DepartCity":"",
           "ArriveCity":"",
           "IsShield":0,
           "DepartPorts":[],
           "ArrivePorts":[],
           "DepartTimes":[],
           "ShipNames":[],
           "LineIds":[],
           "ChannelProject":"yhtApplet",
           "VehicleType":"2",
           "Channel":"yhtApplet"}
last_push_time = 0 # 上次推送时间
total_push_times = 0

# 获取票据数据，返回值为request本体，尽可能保证交付到正常数据
def get_tickets(date, retry_times):
    # 超过8次则选择失败，不是很优雅
    if retry_times == 8:
        return None
    
    # 获取票据数据
    r = requests.post(TARGET_URL, headers=header, json=payload, verify=False, timeout=5)

    # 正常获取到了数据
    if r.status_code == 200:
        data = json.loads(r.content.decode("utf8"))
        # 接口上限，重试
        # DEBUG
        logger.trace(data)
        if '接口' in r.content.decode("utf8"):
            # logger.info("第" + str(retry_times + 1) + "次尝试，接口请求已达到上限，正在重新获取...")
            # 一秒钟后继续获取
            time.sleep(1)
            return get_tickets(date, retry_times + 1)
        else:
            logger.info("成功获取到了" + date + "的数据！")
            return r
            
    # 获取失败，重试
    elif r.status_code == 415:
        logger.info("第" + str(retry_times) + "次尝试，415 错误，正在重新获取...")
        return get_tickets(date, retry_times + 1)
    
    return r


# 推送有票通知
def push(date, content):
    global last_push_time
    delta_time = datetime.now().timestamp() - last_push_time
    content = str(content)
    if delta_time < PUSH_INTERVAL:
        logger.warning("还有" + str(round(PUSH_INTERVAL - delta_time, 2)) + "秒才能继续推送。")
        return
    else:
        # 格式化日期显示
        date_str = "2 月 "
        for d in date:
            date_str = date_str + d.replace("2024-02-", "") + " "
        data = {"title": date_str + "日有票", "desp": content}
        # 推送ServerChan，不想使用的话把下面一行注释掉即可
        requests.post(url="https://sctapi.ftqq.com/"+ SERVERCHAN_TOKEN + ".send", headers=header, json=data)
        # 推送PushPlus，不想使用的话把下面两行注释掉即可
        pp_data = {"token": PUSHPLUS_TOKEN, "title": date_str + "日有票", "content": content, "topic": PUSHPLUS_GROUP_ID}
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
        for date in DATE_LIST:
            # Get the request
            payload["DepartDate"] = date
            logger.info(date + " 数据获取中...")
            # 获取票务信息
            r = None
            try:
                r = get_tickets(date, 0)
            except Exception as e:
                logger.error("出现错误：" + str(e))
            if r == None:
                logger.error(date + "获取失败，进行下一个获取...")
            else:
                # 成功获取，进行一个是否有车的判断
                data = json.loads(r.content.decode("utf8"))

                # Mock 数据
                # f = open("./logs/test_data.json", encoding="utf8")
                # content = f.read()
                # data = json.loads(content)

                # logger.debug(data) # 展示数据
                try:
                    # 出发时间
                    for voyage in data["Data"]["Voyages"]:
                        # 余票数量
                        for vehicle in voyage["Vehicles"]:
                            if vehicle["VehicleTicketLeft"] != 0:
                                push_content.append({"出发时间":voyage["DepartDateTime"], "票数":vehicle["VehicleTicketLeft"]})
                                push_dates.add(date)
                except KeyError as e:
                    logger.error("键值错误：" + str(e))
                except Exception as e:
                    logger.error("出现错误：" + str(e))
        # 如果推送列表不为空，则推送
        if push_content != []:
            push(push_dates, push_content)
        else:
            logger.info("现在还没有票票...")
        logger.info("休眠60秒，准备进行下一轮获取。")
        time.sleep(60)