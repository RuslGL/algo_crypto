import uuid
import asyncio

from settings import MAIN_URL, ENDPOINTS


from api.account import find_usdt_budget, get_user_positions

from api.market import (get_linear_settings, get_linear_price,
                        calculate_purchase_volume, round_price)

from api.trade import (universal_linear_market_buy_order,
                       universal_linear_limit_order, set_lev_linears)


if __name__ == '__main__':

    import os
    from dotenv import load_dotenv

    load_dotenv()

    api_key = str(os.getenv('api_key'))
    secret_key = str(os.getenv('secret_key'))

    url = MAIN_URL + ENDPOINTS['place_order']

    symbol = 'BTCUSDT'
    side = 'Sell'


    async def main():
        pass

        # # poluchaem nastroyki na torguemuyu paru
        BTCUSDT_settings = await get_linear_settings(symbol)
        print('\nНастройки торговли')
        print(BTCUSDT_settings)
        #
        BTCUSDT_last_price = await get_linear_price(symbol)
        print('\nПоследняя цена')
        print(BTCUSDT_last_price)
        #
        balance = float(await find_usdt_budget(api_key, secret_key))
        print('\nБаланс юзера')
        print(balance)
        #
        qty = calculate_purchase_volume(balance * 0.995, BTCUSDT_last_price,
                                        BTCUSDT_settings.get('min_order_qty'),
                                        BTCUSDT_settings.get('qty_step'))
        print('\nКоличество к покупке')
        print(qty)
        #
        # размещаем первичный ордер
        orderLinkId = uuid.uuid4().hex[:12]
        res = await universal_linear_market_buy_order(url, api_key, secret_key, symbol, qty, orderLinkId)
        print('\nРезультат размещения первичного ордера')
        print(res)


        # # если повторная закупка можем закрывать по средней цене?
        position_status = await get_user_positions(api_key, secret_key, symbol)
        print('\nПроверяем позицию')
        print(position_status)
        #
        print('\nЦена входа в позицию')
        entry_price = position_status[0].get('avgPrice')
        print(entry_price)
        #
        target_price = float(entry_price) * 1.05
        # Таргетный профит
        target_price = round_price(target_price, BTCUSDT_settings.get('price_tick_size'))

        print('\nТаргет цена')
        print(target_price)


        orderLinkId = uuid.uuid4().hex[:12]
        print('prev order orderLinkId', orderLinkId)
        prev_order_orderLinkId = '052dfa997409'

        res_two = await universal_linear_limit_order(url, api_key, secret_key,
                                                     symbol, side, qty,
                                                     target_price, orderLinkId)

        print('\nПроверяем результат размещения тейк ордера')
        print(res_two)


        # leverage = 2
        # set_lev = await set_lev_linears(api_key, secret_key, symbol, leverage)
        # print(f'\nУстановили плечо {leverage}')
        # print(set_lev)

    asyncio.run(main())
