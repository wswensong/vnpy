from vnpy.event import EventEngine
from vnpy.trader.event import *  # 确保使用正确的事件名称
from vnpy.trader.engine import MainEngine, OmsEngine
from vnpy_ctp import CtpGateway
from vnpy.trader.object import SubscribeRequest
from vnpy.trader.constant import Exchange
from settings import N_SHIJIE



def on_tick_event(event):
    tick = event.data
    print(tick)

def on_log_with_account(event):
    log = event.data
    msg = f"{log.time}\t{log.msg}"
    print(msg)  # 添加调试信息



# 初始化事件引擎
event_engine = EventEngine()


# 初始化主引擎
main_engine = MainEngine(event_engine)

# 添加CTP网关
main_engine.add_gateway(CtpGateway)

# 连接CTP网关
main_engine.connect(N_SHIJIE, "CTP")


# # 订阅特定合约
req = SubscribeRequest(symbol="rb2505C3250", exchange=Exchange.SHFE)
main_engine.subscribe(req, "CTP")

event_engine.register(EVENT_TICK, on_tick_event)  # 确保使用正确的事件名称
event_engine.register(EVENT_LOG, on_log_with_account)

