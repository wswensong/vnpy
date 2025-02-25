"""
Basic data structure used for general trading function in the trading platform.
"""

from dataclasses import dataclass, field
from datetime import datetime
from logging import INFO
from typing import Optional

from .constant import Direction, Exchange, Interval, Offset, Status, Product, OptionType, OrderType

ACTIVE_STATUSES = set([Status.SUBMITTING, Status.NOTTRADED, Status.PARTTRADED])


@dataclass
class BaseData:
    """
    任何数据对象都需要一个gateway_name作为源，
    并且应该继承基础数据类。

    Attributes:
        gateway_name (str): 数据的网关名称，用作数据来源的标识。
        extra (Optional[dict]): 用于存储额外信息的字典，初始默认为None。
    """

    gateway_name: str

    extra: Optional[dict] = field(default=None, init=False)


@dataclass
class TickData(BaseData):
    """
    Tick数据包含以下信息：
        * 最新市场成交信息
        * 深度行情快照
        * 当日市场统计信息

    参数说明：
    :param symbol: 交易品种代码
    :param exchange: 交易所枚举类型
    :param datetime: Tick数据的时间戳

    :param name: 合约名称，默认为空字符串
    :param volume: 成交量，默认为0
    :param turnover: 成交额，默认为0
    :param open_interest: 持仓量，默认为0
    :param last_price: 最新价，默认为0
    :param last_volume: 最新成交量，默认为0
    :param limit_up: 涨停价，默认为0
    :param limit_down: 跌停价，默认为0

    :param open_price: 开盘价，默认为0
    :param high_price: 最高价，默认为0
    :param low_price: 最低价，默认为0
    :param pre_close: 昨收盘价，默认为0

    :param bid_price_1: 买1价，默认为0
    :param bid_price_2: 买2价，默认为0
    :param bid_price_3: 买3价，默认为0
    :param bid_price_4: 买4价，默认为0
    :param bid_price_5: 买5价，默认为0

    :param ask_price_1: 卖1价，默认为0
    :param ask_price_2: 卖2价，默认为0
    :param ask_price_3: 卖3价，默认为0
    :param ask_price_4: 卖4价，默认为0
    :param ask_price_5: 卖5价，默认为0

    :param bid_volume_1: 买1量，默认为0
    :param bid_volume_2: 买2量，默认为0
    :param bid_volume_3: 买3量，默认为0
    :param bid_volume_4: 买4量，默认为0
    :param bid_volume_5: 买5量，默认为0

    :param ask_volume_1: 卖1量，默认为0
    :param ask_volume_2: 卖2量，默认为0
    :param ask_volume_3: 卖3量，默认为0
    :param ask_volume_4: 卖4量，默认为0
    :param ask_volume_5: 卖5量，默认为0

    :param localtime: 本地时间，默认为None
    """

    symbol: str
    exchange: Exchange
    datetime: datetime

    name: str = ""
    volume: float = 0
    turnover: float = 0
    open_interest: float = 0
    last_price: float = 0
    last_volume: float = 0
    limit_up: float = 0
    limit_down: float = 0

    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    pre_close: float = 0

    bid_price_1: float = 0
    bid_price_2: float = 0
    bid_price_3: float = 0
    bid_price_4: float = 0
    bid_price_5: float = 0

    ask_price_1: float = 0
    ask_price_2: float = 0
    ask_price_3: float = 0
    ask_price_4: float = 0
    ask_price_5: float = 0

    bid_volume_1: float = 0
    bid_volume_2: float = 0
    bid_volume_3: float = 0
    bid_volume_4: float = 0
    bid_volume_5: float = 0

    ask_volume_1: float = 0
    ask_volume_2: float = 0
    ask_volume_3: float = 0
    ask_volume_4: float = 0
    ask_volume_5: float = 0

    localtime: datetime = None

    def __post_init__(self) -> None:
        """
        初始化后处理函数，生成vt_symbol。
        """
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"


@dataclass
class BarData(BaseData):
    """
    K线数据类，表示特定交易周期的K线数据，继承自BaseData。
    
    参数:
        symbol (str): 交易合约代码
        exchange (Exchange): 交易所枚举类型
        datetime (datetime): K线时间戳
        
        interval (Interval, 可选): K线周期，默认为None
        volume (float, 可选): 成交量，默认为0
        turnover (float, 可选): 成交额，默认为0
        open_interest (float, 可选): 持仓量，默认为0
        open_price (float, 可选): 开盘价，默认为0
        high_price (float, 可选): 最高价，默认为0
        low_price (float, 可选): 最低价，默认为0
        close_price (float, 可选): 收盘价，默认为0
    """

    symbol: str
    exchange: Exchange
    datetime: datetime

    interval: Interval = None
    volume: float = 0
    turnover: float = 0
    open_interest: float = 0
    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    close_price: float = 0

    def __post_init__(self) -> None:
        """
        初始化方法，在dataclass实例化后自动调用。
        
        总结:
            该方法用于在初始化后设置vt_symbol属性，格式为"{symbol}.{exchange.value}"。
        """
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"


@dataclass
class OrderData(BaseData):
    """
    订单数据类，用于跟踪特定订单的最新状态，继承自BaseData。

    参数:
        symbol (str): 交易合约代码
        exchange (Exchange): 交易所枚举类型
        orderid (str): 订单ID

        type (OrderType, 可选): 订单类型，默认为限价单（LIMIT）
        direction (Direction, 可选): 买卖方向，默认为None
        offset (Offset, 可选): 开平仓标志，默认为无开平仓（NONE）
        price (float, 可选): 订单价格，默认为0
        volume (float, 可选): 订单数量，默认为0
        traded (float, 可选): 已成交数量，默认为0
        status (Status, 可选): 订单状态，默认为提交中（SUBMITTING）
        datetime (datetime, 可选): 订单时间，默认为None
        reference (str, 可选): 订单备注，默认为空字符串
    """

    symbol: str
    exchange: Exchange
    orderid: str

    type: OrderType = OrderType.LIMIT
    direction: Direction = None
    offset: Offset = Offset.NONE
    price: float = 0
    volume: float = 0
    traded: float = 0
    status: Status = Status.SUBMITTING
    datetime: datetime = None
    reference: str = ""

    def __post_init__(self) -> None:
        """
        初始化方法，在dataclass实例化后自动调用。
        
        总结:
            该方法用于在初始化后设置vt_symbol和vt_orderid属性。
            - vt_symbol格式为"{symbol}.{exchange.value}"
            - vt_orderid格式为"{gateway_name}.{orderid}"
        """
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"
        self.vt_orderid: str = f"{self.gateway_name}.{self.orderid}"

    def is_active(self) -> bool:
        """
        检查订单是否处于活跃状态。

        返回:
            bool: 如果订单状态在ACTIVE_STATUSES集合中，则返回True，否则返回False。
        """
        return self.status in ACTIVE_STATUSES

    def create_cancel_request(self) -> "CancelRequest":
        """
        根据当前订单信息创建取消请求对象。

        返回:
            CancelRequest: 包含订单ID、合约代码和交易所信息的取消请求对象。
        """
        req: CancelRequest = CancelRequest(
            orderid=self.orderid, 
            symbol=self.symbol, 
            exchange=self.exchange
        )
        return req


@dataclass
class TradeData(BaseData):
    """
    Trade data contains information of a fill of an order. One order
    can have several trade fills.
    """

    symbol: str
    exchange: Exchange
    orderid: str
    tradeid: str
    direction: Direction = None

    offset: Offset = Offset.NONE
    price: float = 0
    volume: float = 0
    datetime: datetime = None

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"
        self.vt_orderid: str = f"{self.gateway_name}.{self.orderid}"
        self.vt_tradeid: str = f"{self.gateway_name}.{self.tradeid}"


@dataclass
class PositionData(BaseData):
    """
    持仓数据类，用于跟踪每个持仓的具体信息，继承自BaseData。

    参数:
        symbol (str): 交易合约代码
        exchange (Exchange): 交易所枚举类型
        direction (Direction): 持仓方向（多头或空头）

        volume (float, 可选): 持仓数量，默认为0
        frozen (float, 可选): 冻结数量，默认为0
        price (float, 可选): 平均开仓价格，默认为0
        pnl (float, 可选): 持仓盈亏，默认为0
        yd_volume (float, 可选): 昨日持仓数量，默认为0
    """

    symbol: str
    exchange: Exchange
    direction: Direction

    volume: float = 0
    frozen: float = 0
    price: float = 0
    pnl: float = 0
    yd_volume: float = 0

    def __post_init__(self) -> None:
        """
        初始化方法，在dataclass实例化后自动调用。
        
        总结:
            该方法用于在初始化后设置vt_symbol和vt_positionid属性。
            - vt_symbol格式为"{symbol}.{exchange.value}"
            - vt_positionid格式为"{gateway_name}.{vt_symbol}.{direction.value}"
        """
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"
        self.vt_positionid: str = f"{self.gateway_name}.{self.vt_symbol}.{self.direction.value}"


@dataclass
class AccountData(BaseData):
    """
    账户数据类，包含账户的余额、冻结金额和可用金额信息，继承自BaseData。

    参数:
        accountid (str): 账户ID

        balance (float, 可选): 账户总余额，默认为0
        frozen (float, 可选): 冻结金额，默认为0
    """

    accountid: str

    balance: float = 0
    frozen: float = 0

    def __post_init__(self) -> None:
        """
        初始化方法，在dataclass实例化后自动调用。
        
        总结:
            该方法用于在初始化后设置available和vt_accountid属性。
            - available表示可用金额，计算方式为balance减去frozen。
            - vt_accountid格式为"{gateway_name}.{accountid}"。
        """
        self.available: float = self.balance - self.frozen
        self.vt_accountid: str = f"{self.gateway_name}.{self.accountid}"


@dataclass
class LogData(BaseData):
    """
    日志数据类，用于在GUI或日志文件中记录日志信息，继承自BaseData。

    参数:
        msg (str): 日志消息内容
        level (int, 可选): 日志级别，默认为INFO级别
    """

    msg: str
    level: int = INFO

    def __post_init__(self) -> None:
        """
        初始化方法，在dataclass实例化后自动调用。
        
        总结:
            该方法用于在初始化后设置time属性，记录当前时间。
            - time表示日志记录的时间，使用datetime.now()获取当前时间。
        """
        self.time: datetime = datetime.now()


@dataclass
class ContractData(BaseData):
    """
    合同数据包含有关每个合同的基本信息。
    """

    symbol: str
    exchange: Exchange
    name: str
    product: Product
    size: float
    pricetick: float

    min_volume: float = 1           # minimum order volume
    max_volume: float = None        # maximum order volume
    stop_supported: bool = False    # whether server supports stop order
    net_position: bool = False      # whether gateway uses net position volume
    history_data: bool = False      # whether gateway provides bar history data

    option_strike: float = 0
    option_underlying: str = ""     # vt_symbol of underlying contract
    option_type: OptionType = None
    option_listed: datetime = None
    option_expiry: datetime = None
    option_portfolio: str = ""
    option_index: str = ""          # for identifying options with same strike price

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"


@dataclass
class QuoteData(BaseData):
    """
    报价数据包含用于跟踪最后状态的信息
    特定报价。
    """

    symbol: str
    exchange: Exchange
    quoteid: str

    bid_price: float = 0.0
    bid_volume: int = 0
    ask_price: float = 0.0
    ask_volume: int = 0
    bid_offset: Offset = Offset.NONE
    ask_offset: Offset = Offset.NONE
    status: Status = Status.SUBMITTING
    datetime: datetime = None
    reference: str = ""

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"
        self.vt_quoteid: str = f"{self.gateway_name}.{self.quoteid}"

    def is_active(self) -> bool:
        """
        检查报价是否处于活动状态。
        """
        return self.status in ACTIVE_STATUSES

    def create_cancel_request(self) -> "CancelRequest":
        """
        从报价创建取消请求对象。
        """
        req: CancelRequest = CancelRequest(
            orderid=self.quoteid, symbol=self.symbol, exchange=self.exchange
        )
        return req


@dataclass
class SubscribeRequest:
    """
    请求发送到特定网关以订阅tick数据更新。
    """

    symbol: str
    exchange: Exchange

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"


@dataclass
class OrderRequest:
    """
    请求发送到特定网关以创建新订单。
    """

    symbol: str
    exchange: Exchange
    direction: Direction
    type: OrderType
    volume: float
    price: float = 0
    offset: Offset = Offset.NONE
    reference: str = ""

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"

    def create_order_data(self, orderid: str, gateway_name: str) -> OrderData:
        """
        从请求创建订单数据。
        """
        order: OrderData = OrderData(
            symbol=self.symbol,
            exchange=self.exchange,
            orderid=orderid,
            type=self.type,
            direction=self.direction,
            offset=self.offset,
            price=self.price,
            volume=self.volume,
            reference=self.reference,
            gateway_name=gateway_name,
        )
        return order


@dataclass
class CancelRequest:
    """
    请求发送到特定网关取消现有订单。
    """

    orderid: str
    symbol: str
    exchange: Exchange

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"


@dataclass
class HistoryRequest:
    """
    请求发送到特定网关查询历史记录数据。
    """

    symbol: str
    exchange: Exchange
    start: datetime
    end: datetime = None
    interval: Interval = None

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"


@dataclass
class QuoteRequest:
    """
    请求发送到特定网关以创建新的报价。
    """

    symbol: str
    exchange: Exchange
    bid_price: float
    bid_volume: int
    ask_price: float
    ask_volume: int
    bid_offset: Offset = Offset.NONE
    ask_offset: Offset = Offset.NONE
    reference: str = ""

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"

    def create_quote_data(self, quoteid: str, gateway_name: str) -> QuoteData:
        """
        Create quote data from request.
        """
        quote: QuoteData = QuoteData(
            symbol=self.symbol,
            exchange=self.exchange,
            quoteid=quoteid,
            bid_price=self.bid_price,
            bid_volume=self.bid_volume,
            ask_price=self.ask_price,
            ask_volume=self.ask_volume,
            bid_offset=self.bid_offset,
            ask_offset=self.ask_offset,
            reference=self.reference,
            gateway_name=gateway_name,
        )
        return quote
