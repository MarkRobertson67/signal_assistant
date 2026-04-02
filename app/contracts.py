from ibapi.contract import Contract


def stock_contract(symbol: str, exchange: str = "SMART", currency: str = "USD") -> Contract:
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.exchange = exchange
    contract.currency = currency
    contract.primaryExchange = "NASDAQ"
    return contract
