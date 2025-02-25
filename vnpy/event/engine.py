"""
Event-driven framework of VeighNa framework.
"""

from collections import defaultdict
from queue import Empty, Queue
from threading import Thread
from time import sleep
from typing import Any, Callable, List

EVENT_TIMER = "eTimer"


class Event:
    """
    事件对象包含一个类型字符串，用于事件引擎分发事件，以及一个数据对象，包含实际的数据。
    """

    def __init__(self, type: str, data: Any = None) -> None:
        """
        初始化事件对象。

        :param type: 事件类型，用于事件分发。
        :param data: 事件数据，包含实际信息，默认为 None。
        """
        self.type: str = type
        self.data: Any = data


# 定义事件引擎中使用的处理器函数类型。
HandlerType: callable = Callable[[Event], None]


class EventEngine:
    """
    事件引擎根据事件类型将事件对象分发给已注册的处理器。

    它还每隔指定的时间间隔生成一个定时器事件，可用于定时目的。
    """

    def __init__(self, interval: int = 1) -> None:
        """
        如果未指定时间间隔，默认每秒生成一次定时器事件。

        :param interval: 定时器事件的时间间隔，默认为 1 秒。
        """
        self._interval: int = interval
        self._queue: Queue = Queue()
        self._active: bool = False
        self._thread: Thread = Thread(target=self._run)
        self._timer: Thread = Thread(target=self._run_timer)
        self._handlers: defaultdict = defaultdict(list)
        self._general_handlers: List = []

    def _run(self) -> None:
        """
        从队列中获取事件并处理它。
        """
        while self._active:
            try:
                event: Event = self._queue.get(block=True, timeout=1)
                self._process(event)
            except Empty:
                pass

    def _process(self, event: Event) -> None:
        """
        首先将事件分发给已注册监听该类型的处理器。

        然后将事件分发给所有类型的通用处理器。
        """
        if event.type in self._handlers:
            [handler(event) for handler in self._handlers[event.type]]

        if self._general_handlers:
            [handler(event) for handler in self._general_handlers]

    def _run_timer(self) -> None:
        """
        每隔指定的时间间隔休眠并生成一个定时器事件。
        """
        while self._active:
            sleep(self._interval)
            event: Event = Event(EVENT_TIMER)
            self.put(event)

    def start(self) -> None:
        """
        启动事件引擎以处理事件并生成定时器事件。
        """
        self._active = True
        self._thread.start()
        self._timer.start()

    def stop(self) -> None:
        """
        停止事件引擎。
        """
        self._active = False
        self._timer.join()
        self._thread.join()

    def put(self, event: Event) -> None:
        """
        将事件对象放入事件队列。

        :param event: 要放入队列的事件对象。
        """
        self._queue.put(event)

    def register(self, type: str, handler: HandlerType) -> None:
        """
        为特定事件类型注册一个新的处理器函数。每个函数只能为每个事件类型注册一次。

        :param type: 事件类型。
        :param handler: 处理器函数。
        """
        handler_list: list = self._handlers[type]
        if handler not in handler_list:
            handler_list.append(handler)

    def unregister(self, type: str, handler: HandlerType) -> None:
        """
        从事件引擎中注销已有的处理器函数。

        :param type: 事件类型。
        :param handler: 处理器函数。
        """
        handler_list: list = self._handlers[type]

        if handler in handler_list:
            handler_list.remove(handler)

        if not handler_list:
            self._handlers.pop(type)

    def register_general(self, handler: HandlerType) -> None:
        """
        为所有事件类型注册一个新的处理器函数。每个函数只能为每个事件类型注册一次。

        :param handler: 处理器函数。
        """
        if handler not in self._general_handlers:
            self._general_handlers.append(handler)

    def unregister_general(self, handler: HandlerType) -> None:
        """
        注销已有的通用处理器函数。

        :param handler: 处理器函数。
        """
        if handler in self._general_handlers:
            self._general_handlers.remove(handler)
