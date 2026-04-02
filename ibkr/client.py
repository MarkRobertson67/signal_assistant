import threading
import time
from ibapi.client import EClient
from ibapi.wrapper import EWrapper


class IBClient(EWrapper, EClient):
    def __init__(self) -> None:
        EClient.__init__(self, self)
        self.next_order_id = None
        self.connected_event = threading.Event()

    def nextValidId(self, orderId: int) -> None:
        self.next_order_id = orderId
        self.connected_event.set()

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson="") -> None:
        print(f"[IB ERROR] reqId={reqId} code={errorCode} msg={errorString}")

    def start_background_loop(self) -> None:
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        time.sleep(1)
        