import logging
from logging import Logger
import smtplib
import os
import traceback
from abc import ABC
from pathlib import Path
from datetime import datetime
from email.message import EmailMessage
from queue import Empty, Queue
from threading import Thread
from typing import Any, Type, Dict, List, Optional

from vnpy.event import Event, EventEngine
from .app import BaseApp
from .event import (
    EVENT_TICK,
    EVENT_ORDER,
    EVENT_TRADE,
    EVENT_POSITION,
    EVENT_ACCOUNT,
    EVENT_CONTRACT,
    EVENT_LOG,
    EVENT_QUOTE
)
from .gateway import BaseGateway
from .object import (
    CancelRequest,
    LogData,
    OrderRequest,
    QuoteData,
    QuoteRequest,
    SubscribeRequest,
    HistoryRequest,
    OrderData,
    BarData,
    TickData,
    TradeData,
    PositionData,
    AccountData,
    ContractData,
    Exchange
)
from .setting import SETTINGS
from .utility import get_folder_path, TRADER_DIR
from .converter import OffsetConverter
from .locale import _


class MainEngine:
    """
    作为交易平台的核心。
    """

    def __init__(self, event_engine: EventEngine = None) -> None:
        """
        初始化主引擎。

        参数：
        - event_engine (EventEngine, 可选): 事件引擎实例。如果未提供，则创建一个新的事件引擎。

        返回：
        - None
        """
        if event_engine:
            self.event_engine: EventEngine = event_engine
        else:
            self.event_engine = EventEngine()
        self.event_engine.start()

        # 初始化存储网关、引擎和应用程序的字典以及交易所列表
        self.gateways: Dict[str, BaseGateway] = {}
        self.engines: Dict[str, BaseEngine] = {}
        self.apps: Dict[str, BaseApp] = {}
        self.exchanges: List[Exchange] = []

        os.chdir(TRADER_DIR)    # 更改工作目录
        self.init_engines()     # 初始化功能引擎

    def add_engine(self, engine_class: Any) -> "BaseEngine":
        """
        添加功能引擎。

        参数：
        - engine_class (Any): 引擎类。

        返回：
        - BaseEngine: 新添加的引擎实例。
        """
        engine: BaseEngine = engine_class(self, self.event_engine)
        self.engines[engine.engine_name] = engine
        return engine

    def add_gateway(self, gateway_class: Type[BaseGateway], gateway_name: str = "") -> BaseGateway:
        """
        添加网关。

        参数：
        - gateway_class (Type[BaseGateway]): 网关类。
        - gateway_name (str, 可选): 网关名称，默认使用网关类的默认名称。

        返回：
        - BaseGateway: 新添加的网关实例。
        """
        if not gateway_name:
            gateway_name: str = gateway_class.default_name

        gateway: BaseGateway = gateway_class(self.event_engine, gateway_name)
        self.gateways[gateway_name] = gateway

        # 将网关支持的交易所添加到引擎中
        for exchange in gateway.exchanges:
            if exchange not in self.exchanges:
                self.exchanges.append(exchange)

        return gateway

    def add_app(self, app_class: Type[BaseApp]) -> "BaseEngine":
        """
        添加应用程序。

        参数：
        - app_class (Type[BaseApp]): 应用程序类。

        返回：
        - BaseEngine: 新添加的应用程序对应的引擎实例。
        """
        app: BaseApp = app_class()
        self.apps[app.app_name] = app

        engine: BaseEngine = self.add_engine(app.engine_class)
        return engine

    def init_engines(self) -> None:
        """
        初始化所有引擎。

        返回：
        - None
        """
        self.add_engine(LogEngine)
        self.add_engine(OmsEngine)
        self.add_engine(EmailEngine)

    def write_log(self, msg: str, source: str = "") -> None:
        """
        记录带有特定消息的日志事件。

        参数：
        - msg (str): 日志消息。
        - source (str, 可选): 日志来源，默认为空字符串。

        返回：
        - None
        """
        log: LogData = LogData(msg=msg, gateway_name=source)
        event: Event = Event(EVENT_LOG, log)
        self.event_engine.put(event)

    def get_gateway(self, gateway_name: str) -> BaseGateway:
        """
        根据名称返回网关对象。

        参数：
        - gateway_name (str): 网关名称。

        返回：
        - BaseGateway: 网关对象，如果找不到则返回None，并记录日志。
        """
        gateway: BaseGateway = self.gateways.get(gateway_name, None)
        if not gateway:
            self.write_log(_("找不到底层接口：{}").format(gateway_name))
        return gateway

    def get_engine(self, engine_name: str) -> "BaseEngine":
        """
        根据名称返回引擎对象。

        参数：
        - engine_name (str): 引擎名称。

        返回：
        - BaseEngine: 引擎对象，如果找不到则返回None，并记录日志。
        """
        engine: BaseEngine = self.engines.get(engine_name, None)
        if not engine:
            self.write_log(_("找不到引擎：{}").format(engine_name))
        return engine

    def get_default_setting(self, gateway_name: str) -> Optional[Dict[str, Any]]:
        """
        获取特定网关的默认设置字典。

        参数：
        - gateway_name (str): 网关名称。

        返回：
        - Optional[Dict[str, Any]]: 默认设置字典，如果找不到网关则返回None。
        """
        gateway: BaseGateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.get_default_setting()
        return None

    def get_all_gateway_names(self) -> List[str]:
        """
        获取主引擎中添加的所有网关名称。

        返回：
        - List[str]: 所有网关名称列表。
        """
        return list(self.gateways.keys())

    def get_all_apps(self) -> List[BaseApp]:
        """
        获取所有应用程序对象。

        返回：
        - List[BaseApp]: 所有应用程序对象列表。
        """
        return list(self.apps.values())

    def get_all_exchanges(self) -> List[Exchange]:
        """
        获取所有交易所。

        返回：
        - List[Exchange]: 所有交易所列表。
        """
        return self.exchanges

    def connect(self, setting: dict, gateway_name: str) -> None:
        """
        启动特定网关的连接。

        参数：
        - setting (dict): 连接设置。
        - gateway_name (str): 网关名称。

        返回：
        - None
        """
        gateway: BaseGateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.connect(setting)

    def subscribe(self, req: SubscribeRequest, gateway_name: str) -> None:
        """
        订阅特定网关的行情数据更新。

        参数：
        - req (SubscribeRequest): 订阅请求。
        - gateway_name (str): 网关名称。

        返回：
        - None
        """
        gateway: BaseGateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.subscribe(req)

    def send_order(self, req: OrderRequest, gateway_name: str) -> str:
        """
        向特定网关发送新的订单请求。

        参数：
        - req (OrderRequest): 订单请求。
        - gateway_name (str): 网关名称。

        返回：
        - str: 订单ID，如果找不到网关则返回空字符串。
        """
        gateway: BaseGateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.send_order(req)
        else:
            return ""

    def cancel_order(self, req: CancelRequest, gateway_name: str) -> None:
        """
        向特定网关发送取消订单请求。

        参数：
        - req (CancelRequest): 取消请求。
        - gateway_name (str): 网关名称。

        返回：
        - None
        """
        gateway: BaseGateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.cancel_order(req)

    def send_quote(self, req: QuoteRequest, gateway_name: str) -> str:
        """
        向特定网关发送新的报价请求。

        参数：
        - req (QuoteRequest): 报价请求。
        - gateway_name (str): 网关名称。

        返回：
        - str: 报价ID，如果找不到网关则返回空字符串。
        """
        gateway: BaseGateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.send_quote(req)
        else:
            return ""

    def cancel_quote(self, req: CancelRequest, gateway_name: str) -> None:
        """
        向特定网关发送取消报价请求。

        参数：
        - req (CancelRequest): 取消请求。
        - gateway_name (str): 网关名称。

        返回：
        - None
        """
        gateway: BaseGateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.cancel_quote(req)

    def query_history(self, req: HistoryRequest, gateway_name: str) -> Optional[List[BarData]]:
        """
        从特定网关查询历史K线数据。

        参数：
        - req (HistoryRequest): 查询请求。
        - gateway_name (str): 网关名称。

        返回：
        - Optional[List[BarData]]: 历史K线数据列表，如果找不到网关则返回None。
        """
        gateway: BaseGateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.query_history(req)
        else:
            return None

    def close(self) -> None:
        """
        在程序退出前确保每个网关和应用程序都正确关闭。

        返回：
        - None
        """
        # 先停止事件引擎以防止新的定时器事件
        self.event_engine.stop()

        for engine in self.engines.values():
            engine.close()

        for gateway in self.gateways.values():
            gateway.close()


class BaseEngine(ABC):
    """
    实现功能引擎的抽象类。
    """

    def __init__(
        self,
        main_engine: MainEngine,
        event_engine: EventEngine,
        engine_name: str,
    ) -> None:
        """
        初始化基础引擎。

        参数：
        - main_engine (MainEngine): 主引擎实例。
        - event_engine (EventEngine): 事件引擎实例。
        - engine_name (str): 引擎名称。

        返回：
        - None
        """
        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine
        self.engine_name: str = engine_name

    def close(self) -> None:
        """
        关闭引擎。

        返回：
        - None
        """
        pass


class LogEngine(BaseEngine):
    """
    使用logging模块处理日志事件并输出。
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """
        初始化日志引擎。

        参数：
        - main_engine (MainEngine): 主引擎实例。
        - event_engine (EventEngine): 事件引擎实例。

        返回：
        - None
        """
        super(LogEngine, self).__init__(main_engine, event_engine, "log")

        if not SETTINGS["log.active"]:
            return

        self.level: int = SETTINGS["log.level"]

        self.logger: Logger = logging.getLogger("veighna")
        self.logger.setLevel(self.level)

        self.formatter: logging.Formatter = logging.Formatter(
            "%(asctime)s  %(levelname)s: %(message)s"
        )

        self.add_null_handler()

        if SETTINGS["log.console"]:
            self.add_console_handler()

        if SETTINGS["log.file"]:
            self.add_file_handler()

        self.register_event()

    def add_null_handler(self) -> None:
        """
        为logger添加null处理器。

        返回：
        - None
        """
        null_handler: logging.NullHandler = logging.NullHandler()
        self.logger.addHandler(null_handler)

    def add_console_handler(self) -> None:
        """
        添加控制台输出日志。

        返回：
        - None
        """
        console_handler: logging.StreamHandler = logging.StreamHandler()
        console_handler.setLevel(self.level)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)

    def add_file_handler(self) -> None:
        """
        添加文件输出日志。

        返回：
        - None
        """
        today_date: str = datetime.now().strftime("%Y%m%d")
        filename: str = f"vt_{today_date}.log"
        log_path: Path = get_folder_path("log")
        file_path: Path = log_path.joinpath(filename)

        file_handler: logging.FileHandler = logging.FileHandler(
            file_path, mode="a", encoding="utf8"
        )
        file_handler.setLevel(self.level)
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)

    def register_event(self) -> None:
        """
        注册日志事件处理器。

        返回：
        - None
        """
        self.event_engine.register(EVENT_LOG, self.process_log_event)

    def process_log_event(self, event: Event) -> None:
        """
        处理日志事件。

        参数：
        - event (Event): 日志事件。

        返回：
        - None
        """
        log: LogData = event.data
        self.logger.log(log.level, log.msg)


class OmsEngine(BaseEngine):
    """
    提供订单管理系统功能。
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """
        初始化OmsEngine实例。

        参数:
            main_engine (MainEngine): 主引擎实例。
            event_engine (EventEngine): 事件引擎实例。
        """
        super(OmsEngine, self).__init__(main_engine, event_engine, "oms")

        # 初始化数据字典，用于存储市场行情、订单、成交、持仓、账户、合约和报价数据
        self.ticks: Dict[str, TickData] = {}
        self.orders: Dict[str, OrderData] = {}
        self.trades: Dict[str, TradeData] = {}
        self.positions: Dict[str, PositionData] = {}
        self.accounts: Dict[str, AccountData] = {}
        self.contracts: Dict[str, ContractData] = {}
        self.quotes: Dict[str, QuoteData] = {}

        # 存储活跃的订单和报价
        self.active_orders: Dict[str, OrderData] = {}
        self.active_quotes: Dict[str, QuoteData] = {}

        # 存储每个网关的OffsetConverter实例
        self.offset_converters: Dict[str, OffsetConverter] = {}

        # 添加查询函数到主引擎
        self.add_function()
        # 注册事件处理器
        self.register_event()

    def add_function(self) -> None:
        """
        将查询函数添加到主引擎中。
        """
        self.main_engine.get_tick = self.get_tick
        self.main_engine.get_order = self.get_order
        self.main_engine.get_trade = self.get_trade
        self.main_engine.get_position = self.get_position
        self.main_engine.get_account = self.get_account
        self.main_engine.get_contract = self.get_contract
        self.main_engine.get_quote = self.get_quote

        self.main_engine.get_all_ticks = self.get_all_ticks
        self.main_engine.get_all_orders = self.get_all_orders
        self.main_engine.get_all_trades = self.get_all_trades
        self.main_engine.get_all_positions = self.get_all_positions
        self.main_engine.get_all_accounts = self.get_all_accounts
        self.main_engine.get_all_contracts = self.get_all_contracts
        self.main_engine.get_all_quotes = self.get_all_quotes
        self.main_engine.get_all_active_orders = self.get_all_active_orders
        self.main_engine.get_all_active_quotes = self.get_all_active_quotes

        self.main_engine.update_order_request = self.update_order_request
        self.main_engine.convert_order_request = self.convert_order_request
        self.main_engine.get_converter = self.get_converter

    def register_event(self) -> None:
        """
        注册事件处理器。
        """
        self.event_engine.register(EVENT_TICK, self.process_tick_event)
        self.event_engine.register(EVENT_ORDER, self.process_order_event)
        self.event_engine.register(EVENT_TRADE, self.process_trade_event)
        self.event_engine.register(EVENT_POSITION, self.process_position_event)
        self.event_engine.register(EVENT_ACCOUNT, self.process_account_event)
        self.event_engine.register(EVENT_CONTRACT, self.process_contract_event)
        self.event_engine.register(EVENT_QUOTE, self.process_quote_event)

    def process_tick_event(self, event: Event) -> None:
        """
        处理市场行情事件。

        参数:
            event (Event): 包含TickData的事件对象。
        """
        tick: TickData = event.data
        self.ticks[tick.vt_symbol] = tick

    def process_order_event(self, event: Event) -> None:
        """
        处理订单事件。

        参数:
            event (Event): 包含OrderData的事件对象。
        """
        order: OrderData = event.data
        self.orders[order.vt_orderid] = order

        # 如果订单是活跃的，则更新字典中的数据
        if order.is_active():
            self.active_orders[order.vt_orderid] = order
        # 否则，从字典中移除不活跃的订单
        elif order.vt_orderid in self.active_orders:
            self.active_orders.pop(order.vt_orderid)

        # 更新OffsetConverter中的订单数据
        converter: OffsetConverter = self.offset_converters.get(order.gateway_name, None)
        if converter:
            converter.update_order(order)

    def process_trade_event(self, event: Event) -> None:
        """
        处理成交事件。

        参数:
            event (Event): 包含TradeData的事件对象。
        """
        trade: TradeData = event.data
        self.trades[trade.vt_tradeid] = trade

        # 更新OffsetConverter中的成交数据
        converter: OffsetConverter = self.offset_converters.get(trade.gateway_name, None)
        if converter:
            converter.update_trade(trade)

    def process_position_event(self, event: Event) -> None:
        """
        处理持仓事件。

        参数:
            event (Event): 包含PositionData的事件对象。
        """
        position: PositionData = event.data
        self.positions[position.vt_positionid] = position

        # 更新OffsetConverter中的持仓数据
        converter: OffsetConverter = self.offset_converters.get(position.gateway_name, None)
        if converter:
            converter.update_position(position)

    def process_account_event(self, event: Event) -> None:
        """
        处理账户事件。

        参数:
            event (Event): 包含AccountData的事件对象。
        """
        account: AccountData = event.data
        self.accounts[account.vt_accountid] = account

    def process_contract_event(self, event: Event) -> None:
        """
        处理合约事件。

        参数:
            event (Event): 包含ContractData的事件对象。
        """
        contract: ContractData = event.data
        self.contracts[contract.vt_symbol] = contract

        # 初始化每个网关的OffsetConverter
        if contract.gateway_name not in self.offset_converters:
            self.offset_converters[contract.gateway_name] = OffsetConverter(self)

    def process_quote_event(self, event: Event) -> None:
        """
        处理报价事件。

        参数:
            event (Event): 包含QuoteData的事件对象。
        """
        quote: QuoteData = event.data
        self.quotes[quote.vt_quoteid] = quote

        # 如果报价是活跃的，则更新字典中的数据
        if quote.is_active():
            self.active_quotes[quote.vt_quoteid] = quote
        # 否则，从字典中移除不活跃的报价
        elif quote.vt_quoteid in self.active_quotes:
            self.active_quotes.pop(quote.vt_quoteid)

    def get_tick(self, vt_symbol: str) -> Optional[TickData]:
        """
        根据vt_symbol获取最新的市场行情数据。

        参数:
            vt_symbol (str): 合约标识符。

        返回:
            Optional[TickData]: 市场行情数据，如果不存在则返回None。
        """
        return self.ticks.get(vt_symbol, None)

    def get_order(self, vt_orderid: str) -> Optional[OrderData]:
        """
        根据vt_orderid获取最新的订单数据。

        参数:
            vt_orderid (str): 订单标识符。

        返回:
            Optional[OrderData]: 订单数据，如果不存在则返回None。
        """
        return self.orders.get(vt_orderid, None)

    def get_trade(self, vt_tradeid: str) -> Optional[TradeData]:
        """
        根据vt_tradeid获取成交数据。

        参数:
            vt_tradeid (str): 成交标识符。

        返回:
            Optional[TradeData]: 成交数据，如果不存在则返回None。
        """
        return self.trades.get(vt_tradeid, None)

    def get_position(self, vt_positionid: str) -> Optional[PositionData]:
        """
        根据vt_positionid获取最新的持仓数据。

        参数:
            vt_positionid (str): 持仓标识符。

        返回:
            Optional[PositionData]: 持仓数据，如果不存在则返回None。
        """
        return self.positions.get(vt_positionid, None)

    def get_account(self, vt_accountid: str) -> Optional[AccountData]:
        """
        根据vt_accountid获取最新的账户数据。

        参数:
            vt_accountid (str): 账户标识符。

        返回:
            Optional[AccountData]: 账户数据，如果不存在则返回None。
        """
        return self.accounts.get(vt_accountid, None)

    def get_contract(self, vt_symbol: str) -> Optional[ContractData]:
        """
        根据vt_symbol获取合约数据。

        参数:
            vt_symbol (str): 合约标识符。

        返回:
            Optional[ContractData]: 合约数据，如果不存在则返回None。
        """
        return self.contracts.get(vt_symbol, None)

    def get_quote(self, vt_quoteid: str) -> Optional[QuoteData]:
        """
        根据vt_quoteid获取最新的报价数据。

        参数:
            vt_quoteid (str): 报价标识符。

        返回:
            Optional[QuoteData]: 报价数据，如果不存在则返回None。
        """
        return self.quotes.get(vt_quoteid, None)

    def get_all_ticks(self) -> List[TickData]:
        """
        获取所有市场行情数据。

        返回:
            List[TickData]: 所有市场行情数据列表。
        """
        return list(self.ticks.values())

    def get_all_orders(self) -> List[OrderData]:
        """
        获取所有订单数据。

        返回:
            List[OrderData]: 所有订单数据列表。
        """
        return list(self.orders.values())

    def get_all_trades(self) -> List[TradeData]:
        """
        获取所有成交数据。

        返回:
            List[TradeData]: 所有成交数据列表。
        """
        return list(self.trades.values())

    def get_all_positions(self) -> List[PositionData]:
        """
        获取所有持仓数据。

        返回:
            List[PositionData]: 所有持仓数据列表。
        """
        return list(self.positions.values())

    def get_all_accounts(self) -> List[AccountData]:
        """
        获取所有账户数据。

        返回:
            List[AccountData]: 所有账户数据列表。
        """
        return list(self.accounts.values())

    def get_all_contracts(self) -> List[ContractData]:
        """
        获取所有合约数据。

        返回:
            List[ContractData]: 所有合约数据列表。
        """
        return list(self.contracts.values())

    def get_all_quotes(self) -> List[QuoteData]:
        """
        获取所有报价数据。

        返回:
            List[QuoteData]: 所有报价数据列表。
        """
        return list(self.quotes.values())

    def get_all_active_orders(self, vt_symbol: str = "") -> List[OrderData]:
        """
        根据vt_symbol获取所有活跃订单。如果vt_symbol为空，则返回所有活跃订单。

        参数:
            vt_symbol (str): 合约标识符，默认为空。

        返回:
            List[OrderData]: 活跃订单数据列表。
        """
        if not vt_symbol:
            return list(self.active_orders.values())
        else:
            active_orders: List[OrderData] = [
                order
                for order in self.active_orders.values()
                if order.vt_symbol == vt_symbol
            ]
            return active_orders

    def get_all_active_quotes(self, vt_symbol: str = "") -> List[QuoteData]:
        """
        根据vt_symbol获取所有活跃报价。如果vt_symbol为空，则返回所有活跃报价。

        参数:
            vt_symbol (str): 合约标识符，默认为空。

        返回:
            List[QuoteData]: 活跃报价数据列表。
        """
        if not vt_symbol:
            return list(self.active_quotes.values())
        else:
            active_quotes: List[QuoteData] = [
                quote
                for quote in self.active_quotes.values()
                if quote.vt_symbol == vt_symbol
            ]
            return active_quotes

    def update_order_request(self, req: OrderRequest, vt_orderid: str, gateway_name: str) -> None:
        """
        更新订单请求到OffsetConverter。

        参数:
            req (OrderRequest): 订单请求对象。
            vt_orderid (str): 订单标识符。
            gateway_name (str): 网关名称。
        """
        converter: OffsetConverter = self.offset_converters.get(gateway_name, None)
        if converter:
            converter.update_order_request(req, vt_orderid)

    def convert_order_request(
        self,
        req: OrderRequest,
        gateway_name: str,
        lock: bool,
        net: bool = False
    ) -> List[OrderRequest]:
        """
        根据给定模式转换原始订单请求。

        参数:
            req (OrderRequest): 订单请求对象。
            gateway_name (str): 网关名称。
            lock (bool): 是否锁定。
            net (bool): 是否净头寸，默认为False。

        返回:
            List[OrderRequest]: 转换后的订单请求列表。
        """
        converter: OffsetConverter = self.offset_converters.get(gateway_name, None)
        if not converter:
            return [req]

        reqs: List[OrderRequest] = converter.convert_order_request(req, lock, net)
        return reqs

    def get_converter(self, gateway_name: str) -> OffsetConverter:
        """
        获取特定网关的OffsetConverter对象。

        参数:
            gateway_name (str): 网关名称。

        返回:
            OffsetConverter: OffsetConverter对象，如果不存在则返回None。
        """
        return self.offset_converters.get(gateway_name, None)


class EmailEngine(BaseEngine):
    """
    提供邮件发送功能。
    """

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """
        初始化EmailEngine实例。

        参数:
            main_engine (MainEngine): 主引擎实例。
            event_engine (EventEngine): 事件引擎实例。
        """
        super(EmailEngine, self).__init__(main_engine, event_engine, "email")

        # 创建并启动邮件处理线程
        self.thread: Thread = Thread(target=self.run)
        self.queue: Queue = Queue()
        self.active: bool = False

        # 将send_email方法绑定到主引擎
        self.main_engine.send_email = self.send_email

    def send_email(self, subject: str, content: str, receiver: str = "") -> None:
        """
        发送邮件。

        参数:
            subject (str): 邮件主题。
            content (str): 邮件内容。
            receiver (str): 收件人，默认为空表示使用默认收件人。
        """
        # 当发送第一封邮件时启动邮件引擎
        if not self.active:
            self.start()

        # 如果未指定收件人，则使用默认收件人
        if not receiver:
            receiver: str = SETTINGS["email.receiver"]

        msg: EmailMessage = EmailMessage()
        msg["From"] = SETTINGS["email.sender"]
        msg["To"] = receiver
        msg["Subject"] = subject
        msg.set_content(content)

        self.queue.put(msg)

    def run(self) -> None:
        """
        运行邮件发送线程。
        """
        server: str = SETTINGS["email.server"]
        port: int = SETTINGS["email.port"]
        username: str = SETTINGS["email.username"]
        password: str = SETTINGS["email.password"]

        while self.active:
            try:
                msg: EmailMessage = self.queue.get(block=True, timeout=1)

                try:
                    with smtplib.SMTP_SSL(server, port) as smtp:
                        smtp.login(username, password)
                        smtp.send_message(msg)
                except Exception:
                    msg: str = _("邮件发送失败: {}").format(traceback.format_exc())
                    self.main_engine.write_log(msg, "EMAIL")
            except Empty:
                pass

    def start(self) -> None:
        """
        启动邮件引擎。
        """
        self.active = True
        self.thread.start()

    def close(self) -> None:
        """
        关闭邮件引擎。
        """
        if not self.active:
            return

        self.active = False
        self.thread.join()
