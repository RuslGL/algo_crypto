import asyncio
import aiohttp

from decimal import Decimal, ROUND_DOWN

from settings import MAIN_URL, ENDPOINTS


async def get_linear_settings(symbol):
    url = MAIN_URL + ENDPOINTS.get('get_instruments_info')

    params = {
        'category': 'linear',
        'symbol': symbol,
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            data = await response.json()

    if data.get('retMsg') == 'OK':
        data = data.get('result').get('list')[0]

        return {
            'name': data.get('symbol'),
            'min_price': data.get('priceFilter').get('minPrice'),
            'max_price': data.get('priceFilter').get('maxPrice'),
            'price_tick_size': data.get('priceFilter').get('tickSize'),
            'max_order_qty': data.get('lotSizeFilter').get('maxOrderQty'),
            'min_order_qty': data.get('lotSizeFilter').get('minOrderQty'),
            'qty_step': data.get('lotSizeFilter').get('qtyStep')
        }
    return -1


async def get_linear_price(symbol):
    url = MAIN_URL + ENDPOINTS.get('get_tick')
    # url = base_url + get_tick

    params = {
        'category': 'linear',
        'symbol': symbol,
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            data = await response.json()

    if data.get('retMsg') == 'OK':
        data = data.get('result').get('list')[0].get('lastPrice')
        return data
    return -1


def calculate_purchase_volume(sum_amount, price, min_volume, tick):
    sum_amount = Decimal(str(sum_amount))
    price = Decimal(str(price))
    min_volume = Decimal(str(min_volume))
    tick = Decimal(str(tick))

    volume = sum_amount / price
    rounded_volume = (volume // tick) * tick

    if rounded_volume < min_volume:
        return -1

    return float(rounded_volume.quantize(tick, rounding=ROUND_DOWN))


def adjust_quantity(quantity, min_volume, tick):
    quantity = Decimal(str(quantity))
    min_volume = Decimal(str(min_volume))
    tick = Decimal(str(tick))

    adjusted_quantity = (quantity // tick) * tick

    if adjusted_quantity < min_volume:
        return -1

    return float(adjusted_quantity)


def round_price(price, tick_size):
    price = Decimal(str(price))
    tick_size = Decimal(str(tick_size))
    return float((price // tick_size) * tick_size)


if __name__ == '__main__':
    async def main():
        pass

    asyncio.run(main())
