import asyncio
import os
import time
import hmac
import hashlib
import json
import aiohttp


from dotenv import load_dotenv
from settings import MAIN_URL, ENDPOINTS


load_dotenv()
DATABASE_URL = os.getenv('database_url')


def gen_signature_get(params, timestamp, api_key, secret_key):
    param_str = timestamp + api_key + '5000' + '&'.join([f'{k}={v}' for k, v in params.items()])
    return hmac.new(
        bytes(secret_key, "utf-8"), param_str.encode("utf-8"), hashlib.sha256
    ).hexdigest()

def get_signature_post(data, timestamp, recv_wind, API_KEY, SECRET_KEY):
    query = f'{timestamp}{API_KEY}{recv_wind}{data}'
    return hmac.new(SECRET_KEY.encode('utf-8'), query.encode('utf-8'),
                    hashlib.sha256).hexdigest()


async def post_data(url, data, headers):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, headers=headers) as response:
            return await response.json()

async def post_bybit_signed(url, API_KEY, SECRET_KEY, **kwargs):
    timestamp = int(time.time() * 1000)
    recv_wind = 5000
    data = json.dumps({key: str(value) for key, value in kwargs.items()})
    signature = get_signature_post(data, timestamp, recv_wind, API_KEY, SECRET_KEY)
    headers = {
        'Accept': 'application/json',
        'X-BAPI-SIGN': signature,
        'X-BAPI-API-KEY': API_KEY,
        'X-BAPI-TIMESTAMP': str(timestamp),
        'X-BAPI-RECV-WINDOW': str(recv_wind)
    }

    return await post_data(
        url,
        data,
        headers)

#
# async def get_wallet_balance(api_key, secret_key, coin=None):
#     user_op = UsersOperations(DATABASE_URL)
#
#     url = st.MAIN_URL + st.ENDPOINTS.get('wallet-balance')
#
#     if not api_key:
#         return -1
#     if not secret_key:
#         return -1
#
#     timestamp = str(int(time.time() * 1000))
#     headers = {
#         'X-BAPI-API-KEY': api_key,
#         'X-BAPI-TIMESTAMP': timestamp,
#         'X-BAPI-RECV-WINDOW': '5000'
#     }
#     params = {'accountType': 'UNIFIED'}
#     if coin:
#         params['coin'] = coin
#     headers['X-BAPI-SIGN'] = gen_signature_get(params, timestamp, api_key, secret_key)
#
#     try:
#         async with aiohttp.ClientSession() as session:
#             async with session.get(url, headers=headers, params=params) as response:
#                 data = await response.json()
#         return data.get('result').get('list')[0].get('totalWalletBalance')
#     except:
#         return -1



async def find_usdt_budget(telegram_id, api_key, secret_key):


    url = MAIN_URL + ENDPOINTS.get('wallet-balance')

    if not api_key:
        return telegram_id, -1
    if not secret_key:
        return telegram_id, -1

    timestamp = str(int(time.time() * 1000))
    headers = {
        'X-BAPI-API-KEY': api_key,
        'X-BAPI-TIMESTAMP': timestamp,
        'X-BAPI-RECV-WINDOW': '5000'
    }
    params = {'accountType': 'UNIFIED'}
    params['coin'] = 'USDT'
    headers['X-BAPI-SIGN'] = gen_signature_get(params, timestamp, api_key, secret_key)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                data = await response.json()
        return telegram_id, data  #.get('result').get('list')[0].get('coin')[0].get('walletBalance')
    except:
        return telegram_id, -1


async def get_user_positions(telegram_id, api_key, secret_key, symbol):
    url = MAIN_URL + ENDPOINTS.get('open_positions')

    if not api_key:
        return -1
    if not secret_key:
        return -1

    timestamp = str(int(time.time() * 1000))
    headers = {
        'X-BAPI-API-KEY': api_key,
        'X-BAPI-TIMESTAMP': timestamp,
        'X-BAPI-RECV-WINDOW': '5000'
    }

    params = {
        'category': 'linear',
        'symbol': symbol
        # 'settleCoin': 'USDT',
        # 'limit': 200,

    }

    headers['X-BAPI-SIGN'] = gen_signature_get(params, timestamp, api_key, secret_key)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                data = await response.json()
        if data.get('retMsg') == 'OK':
            return telegram_id, data.get('result').get('list')
        if data.get('retMsg') == 'System error. Please try again later.':
            return -1
        else:
            return -1

    except Exception as e:
        return -1


async def get_order_by_id(telegram_id, api_key, secret_key, orderLinkId):
    url = MAIN_URL + ENDPOINTS.get('open_orders')

    timestamp = str(int(time.time() * 1000))
    headers = {
        'X-BAPI-API-KEY': api_key,
        'X-BAPI-TIMESTAMP': timestamp,
        'X-BAPI-RECV-WINDOW': '5000'
    }

    params = {
        'category': 'linear',
        'orderLinkId': orderLinkId,

    }
    headers['X-BAPI-SIGN'] = gen_signature_get(params, timestamp, api_key, secret_key)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                data = await response.json()
        return telegram_id, orderLinkId, data    #  [data.get('result').get('list')[0].get('orderStatus'), row_data]

    except Exception as e:
        print(e)
        return -1

async def get_order_by_symbol(telegram_id, api_key, secret_key, symbol, orderLinkId):
    url = MAIN_URL + ENDPOINTS.get('open_orders')

    timestamp = str(int(time.time() * 1000))
    headers = {
        'X-BAPI-API-KEY': api_key,
        'X-BAPI-TIMESTAMP': timestamp,
        'X-BAPI-RECV-WINDOW': '5000'
    }
    params = {
        'category': 'linear',
        'symbol': symbol,
        'openOnly': 0,

    }
    headers['X-BAPI-SIGN'] = gen_signature_get(params, timestamp, api_key, secret_key)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                data = await response.json()
        return telegram_id, orderLinkId, data    #  [data.get('result').get('list')[0].get('orderStatus'), row_data]

    except Exception as e:
        print(e)
        return -1


if __name__ == '__main__':

    async def main():
        pass



    asyncio.run(main())
