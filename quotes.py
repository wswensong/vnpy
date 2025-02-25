# ... 其他导入和初始化代码 ...
import time
from settings import N_SHIJIE
from vnpy.event import EventEngine
from vnpy_ctp import CtpGateway
from vnpy.trader.engine import MainEngine, OmsEngine
from vnpy.trader.object import SubscribeRequest, PositionData, OrderRequest
from vnpy.trader.event import *
from vnpy.trader.constant import Exchange, Direction, Offset, OrderType  # 导入必要的常量
from vnpy_ctastrategy import template

# 创建事件引擎实例
event_engine = EventEngine()
# 创建主引擎实例
main_engine = MainEngine(event_engine)
# 添加CTP网关
main_engine.add_gateway(CtpGateway)

# 配置连接设置
# 连接到CTP服务器
main_engine.connect(N_SHIJIE, "CTP")

# 订阅特定合约的行情数据
req = SubscribeRequest(
    symbol="rb2505",
    exchange=Exchange.SHFE  # 使用Exchange枚举类中的成员
)
main_engine.subscribe(req, "CTP")

# 设置回调函数以处理接收到的行情数据
# 在连接成功后查询账户信息
def on_log_with_account(event):
    log = event.data
    msg = f"{log.time}\t{log.msg}"
    print(msg)  # 添加调试信息

# event_engine.register(EVENT_LOG, on_log_with_account)

def on_tick(event):
    tick = event.data
    print(f"最新行情: 合约代码: {tick.symbol}, 最新价: {tick.last_price}")
event_engine.register(EVENT_TICK, on_tick)

# 设置回调函数以处理账户数据
def on_account(event):
    account = event.data
    # print(f"账户信息: 可用资金: {account.available}, 总资产: {account.balance}")
# event_engine.register(EVENT_ACCOUNT, on_account)




def send_buy_order():
    # 发送买入订单
    order_req = OrderRequest(
        symbol="rb2505",
        type=OrderType.MARKET,
        exchange=Exchange.SHFE,
        direction=Direction.LONG,
        offset=Offset.OPEN,
        price=0,  # 0 表示市价单
        volume=2,
        reference="buy_rb2505"
    )
    main_engine.send_order(order_req, "CTP")



# def on_trade(event):
#     trade = event.data
#     print(trade)
#     print(f"成交信息: 合约代码: {trade.symbol}, 成交价格: {trade.price}, 成交数量: {trade.volume}")
# event_engine.register(EVENT_TRADE, on_trade)
#
# # 回调这个函数EVENT_ORDER
# def on_order(event):
#     order = event.data
#     print(f"订单信息: 合约代码: {order.symbol}, 订单状态: {order.status}")
# event_engine.register(EVENT_ORDER, on_order)

# 回调这个函数EVENT_QUOTE
# def on_quote(event):
#     quote = event.data
#     print(quote)
#     print(f"询价信息: 合约代码: {quote.symbol}, 询价价格: {quote.bid_price1}")
# event_engine.register(EVENT_QUOTE, on_quote)

# 保持程序运行
# while True:
#     time.sleep(1)
