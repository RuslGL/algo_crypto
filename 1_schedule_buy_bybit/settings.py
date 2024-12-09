IF_TEST = True  # true - development mode

mainnet_url = 'https://api.bybit.com'

demo_url = 'https://api-demo.bybit.com'

if not IF_TEST:
    MAIN_URL = mainnet_url
else:
    MAIN_URL = demo_url


ENDPOINTS = {
    # market endpoints
    'get_instruments_info': '/v5/market/instruments-info',
    'get_tick': '/v5/market/tickers',
    'announcements': '/v5/announcements/index',


    # trade endpoints
    'place_order': '/v5/order/create',
    'cancel_order': '/v5/order/cancel',
    'open_orders': '/v5/order/realtime',
    'amend_order': '/v5/order/amend',
    'linear_tp': '/v5/position/trading-stop',
    'open_positions': '/v5/position/list',
    'cancel_all_orders': '/v5/order/cancel-all',

    # account endpoints
    'wallet-balance': '/v5/account/wallet-balance',
    'get_orders': '/v5/order/realtime',
    'set_leverage': '/v5/position/set-leverage',
}


if __name__ == '__main__':
    print(MAIN_URL)