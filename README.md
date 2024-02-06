# HainanFerryTicketMonitor

因为实在忍不了隔几分钟就看一次余票情况急速写的海南铁路 / 徐闻轮渡余票监控脚本，可以与 Server 酱 / PushPlus 等工具结合进行余票的监控和通知，仅供学习研究参考，禁止用于不限于盈利等用途。

## 使用方法

- 首先安装依赖 `pip install -r requirements.txt`

### 对于铁路港的情况

- 在 `rail.py` 中修改想要监控余票的日期、有票推送的间隔，和推送服务 Token，最后一行可以设置休眠时间
- 根据自己需求参考 81-85 行注释中的内容注释掉相应行来禁用某个推送服务
- `python rail.py` 即可启动余票监控

### 对于徐闻港的情况

- 在 `xuwen.py` 中修改想要监控余票的日期、有票推送的间隔，和推送服务 Token，最后一行可以设置休眠时间
- 通过抓包获得相应 Cookie 并替换掉 `xuwen.py` 中 `header` 变量的内容，在此就不再叙述相关获取方法
- `DATE_LIST` 中的监控日期格式直接为 2 月的日期，需要可以修改 31 行来适配不同月份和日期
- `python xuwen.py` 即可启动余票监控

## 其他

*由于本 README 写的比较匆忙，可能有的地方不太对，欢迎提出 Issue（？*

### 