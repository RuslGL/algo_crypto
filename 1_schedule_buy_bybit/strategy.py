import uuid
import asyncio
import os

from datetime import datetime

from dotenv import load_dotenv

from settings import MAIN_URL, ENDPOINTS
from bd.settings import SettingsOperations
from bd.users import UsersOperations


from api.account import find_usdt_budget, get_user_positions, get_order_by_symbol

from api.market import (get_linear_settings, get_linear_price,
                        calculate_purchase_volume, round_price)

from api.trade import (universal_linear_market_buy_order,
                       universal_linear_limit_order, set_lev_linears)



load_dotenv()

DATABASE_URL = os.getenv('database_url')

async def pre_task(settings_op, users_op):

    start = datetime.now()

    task_one = asyncio.create_task(get_linear_settings('BTCUSDT'))  # получаем сетинги на биткоин
    task_two = asyncio.create_task(get_linear_settings('ETHUSDT'))  # получаем сетинги на биткоин
    task_three = asyncio.create_task(settings_op.get_all_settings())  # получаем из БД наши настройки торговли
    task_four = asyncio.create_task(users_op.get_all_users_data())  # получаем из БД данные всех юзеров
    settings_tasks = [task_one, task_two, task_three, task_four]
    results = await asyncio.gather(*settings_tasks)

    BTCUSDT = results[0]  # сетинги на биткоин
    ETHUSDT = results[1]  # сетинги на биткоин
    general_settings = results[2]  # наши настройки торговли
    users = results[3]  # данные всех юзеров


    for_orders = []
    problem_users = []
    valid_users = {}
    budgets = {}

    for _, row in users.iterrows():
        if row['stop_trading']:
            continue  # пропускаем всех у кого статус стоп трейдинг

        # проверяем наличие в базе ключей по каждому юзеру
        if row['api_key'] and row['secret_key']:
            valid_users[row['telegram_id']] = (row['api_key'], row['secret_key'])
            for_orders.append((row['telegram_id'], row['api_key'], row['secret_key']))
        else:
            problem_users.append((row['telegram_id'], 'stopped', 'NO API KEYS'))

            # останавливаем торголю по тем, у кого нет ключей
            await users_op.upsert_user(
                {
                    'telegram_id': row['telegram_id'],
                    'stop_trading': True,
                }
            )


    # создаем и ассинхронно отправляем по всем юзерам запрос по бюджету
    order_tasks = []
    for element in for_orders:
        order_tasks.append(find_usdt_budget(element[0], element[1], element[2]))

    order_results = await asyncio.gather(*order_tasks)


    for element in order_results:
        if element[1] == None:
            problem_users.append((element[0], 'stopped', 'API KEY invalid or expired'))
            await users_op.upsert_user(
                {
                    'telegram_id': element[0],
                    'stop_trading': True,
                }
            )
            continue
        if element[1].get('retMsg') == "Unmatched IP, please check your API key's bound IP addresses.":
            problem_users.append((element[0], 'stopped', 'Unmatched IP in API KEY'))
            await users_op.upsert_user(
                {
                    'telegram_id': element[0],
                    'stop_trading': True,
                }
            )
            continue

        # формируем список бюджетов по все юзерам, по которым биржа отдала данные кошелька
        if element[1].get('retMsg') == 'OK':
            budgets[element[0]] = element[1].get('result').get('list')[0].get('coin')[0].get('walletBalance')


    # выставляем плечи по сеттингам для всех валидных юзеров
    leverage_tasks = []
    for user, items in budgets.items():
        user_set = valid_users.get(user)
        leverage_tasks.append(set_lev_linears(
            user_set[0], user_set[1],
            general_settings.get('trading_pair'),
            general_settings.get('leverage')))

    await asyncio.gather(*leverage_tasks)



    print('problem_users', problem_users)

    print('Время исполнения pre_task', datetime.now() - start)

    return BTCUSDT, ETHUSDT, general_settings, valid_users, budgets


if __name__ == '__main__':
    BTCUSDT_settings = {'name': 'BTCUSDT', 'min_price': '0.10', 'max_price': '199999.80', 'price_tick_size': '0.10',
                        'max_order_qty': '1190.000', 'min_order_qty': '0.001', 'qty_step': '0.001'}

    ETHUSDT_settings = {'name': 'ETHUSDT', 'min_price': '0.01', 'max_price': '19999.98', 'price_tick_size': '0.01',
                        'max_order_qty': '7240.00', 'min_order_qty': '0.01', 'qty_step': '0.01'}

    general_settings = {'name': 'trade_settings', 'stop_trading': True, 'trading_pair': 'BTCUSDT',
                        'razmer_posizii': 25, 'leverage': 1, 'teyk_profit': 5}

    valid_users = {666038149: ('Dxg3WyijHeLQteINGS', 'tgu2JDSf3ck5BAWRel4vVa0Pb4vmdgAN31Au')}

    budgets = {666038149: '685.13909616'}


    async def main_task(BTCUSDT_settings, ETHUSDT_settings, general_settings, valid_users, budgets):
        start = datetime.now()

        trading_pair = general_settings.get('trading_pair')

        if trading_pair == 'BTCUSDT':
            actual_settings = BTCUSDT_settings
        elif trading_pair == 'ETHUSDT':
            actual_settings = ETHUSDT_settings
        else:
            print('Report problem')
            return

        last_price = await get_linear_price(trading_pair)


        orders_tasks = []
        for user, items in budgets.items():
            user_set = valid_users.get(user)


            orderLinkId = uuid.uuid4().hex[:12]
            balance = float(budgets.get(user))
            qty = calculate_purchase_volume(balance * 0.995, last_price,
                                            actual_settings.get('min_order_qty'),
                                            actual_settings.get('qty_step'))
            if qty == -1:
                print('report not enough budget')
                continue

            api_key = user_set[0]
            secret_key = user_set[1]
            # print(
            #     f'telegram_id {user}', '\n',
            #     f'api_key {api_key}', '\n',
            #     f'secret_key {secret_key}', '\n',
            #     f'qty {qty}', '\n',
            #     f'orderLinkId {orderLinkId}', '\n',
            # )
            orders_tasks.append(
                universal_linear_market_buy_order(user, api_key, secret_key, trading_pair, qty, orderLinkId))

        orders_result = await asyncio.gather(*orders_tasks)
        print('Время размещения первичных ордеров main_task', datetime.now() - start)
        print(orders_result)
        # not enough udget - leverago or removed [(666038149, '01af001fe5ad', {'retCode': 110007, 'retMsg': 'ab not enough for new order', 'result': {}, 'retExtInfo': {}, 'time': 1734443351934})]
        # good response [(666038149, '40344f7b3769', {'retCode': 0, 'retMsg': 'OK', 'result': {'orderId': 'ea123021-ea84-4a37-9dc5-fa72eac814d4', 'orderLinkId': '40344f7b3769'}, 'retExtInfo': {}, 'time': 1734443396670})]


        open_positions = []
        open_orders = []

        for element in orders_result:
            if element[2].get('retMsg') == 'OK':
                print('get info and prepare orders')
                user = element[0]
                user_set = valid_users.get(user)
                api_key = user_set[0]
                secret_key = user_set[1]

                # open_positions = await get_user_positions(user, api_key, secret_key, trading_pair)
                # open_orders = await get_order_by_symbol(user, api_key, secret_key, trading_pair, element[1])

                # print('open_positions', open_positions)
                # print('open_orders', open_orders)
                # print('open_orders_list', open_orders[2].get('result').get('list'))

                open_positions.append(
                    get_user_positions(user, api_key, secret_key, trading_pair))

                open_orders.append(
                    get_order_by_symbol(user, api_key, secret_key, trading_pair, element[1]))


                # position_status = await get_user_positions(api_key, secret_key, symbol)

            elif element[2].get('retMsg') == 'ab not enough for new order':
                print('report lack of budget due to leverages or usdt removal by user')

        open_positions = await asyncio.gather(*open_positions)

        open_orders = await asyncio.gather(*open_orders)

        print('open_positions', open_positions)
        # good response open_positions [(666038149, [
        # {'symbol': 'BTCUSDT', 'leverage': '1', 'autoAddMargin': 0, 'avgPrice': '107939.8', 'liqPrice': '539.7', 'riskLimitValue': '2000000',
        # 'takeProfit': '', 'positionValue': '647.6388', 'isReduceOnly': False, 'tpslMode': 'Full', 'riskId': 1, 'trailingStop': '0',
        # 'unrealisedPnl': '-0.0996', 'markPrice': '107923.2', 'adlRankIndicator': 2, 'cumRealisedPnl': '-38.52650837', 'positionMM': '3.238194',
        # 'createdTime': '1723448982069', 'positionIdx': 0, 'positionIM': '647.6388', 'seq': 140592881581634, 'updatedTime': '1734446904612',
        # 'side': 'Buy', 'bustPrice': '', 'positionBalance': '647.6388', 'leverageSysUpdatedTime': '', 'curRealisedPnl': '-0.35620134', 'size': '0.006',
        # 'positionStatus': 'Normal', 'mmrSysUpdatedTime': '', 'stopLoss': '', 'tradeMode': 0, 'sessionAvgPrice': ''}])]

        # no new positions = empty budget open_positions []

        print('open_orders', open_orders)

        # create new take order by avg position price
        # empty open orders response open_orders [(666038149, 666038149,
        # {'retCode': 0, 'retMsg': 'OK', 'result': {'nextPageCursor': '', 'category': 'linear', 'list': []},
        # 'retExtInfo': {}, 'time': 1734446905726})]

        # skip all
        # no new positions = empty budget open_positions []

        # order already exists - change it




        #
        #
        #
        #     set_lev_linears(
        #         user_set[0], user_set[1],
        #         general_settings.get('trading_pair'),
        #         general_settings.get('leverage')))
        #
        # await asyncio.gather(*leverage_tasks)

        print('Время исполнения main_task', datetime.now() - start)
        pass


    #
    #
    #
    # import os
    # from dotenv import load_dotenv
    #
    # load_dotenv()
    #
    # api_key = str(os.getenv('api_key'))
    # secret_key = str(os.getenv('secret_key'))
    #
    # url = MAIN_URL + ENDPOINTS['place_order']
    #
    # symbol = 'BTCUSDT'
    # side = 'Sell'



    async def main():

        settings_op = SettingsOperations(DATABASE_URL)
        users_op = UsersOperations(DATABASE_URL)


        res = await pre_task(settings_op, users_op)
        print(*res, sep='\n')


        await main_task(BTCUSDT_settings, ETHUSDT_settings, general_settings, valid_users, budgets)





        # print(**settings)
        # for element in settings:
        #     print(element, '\n')





        # # # poluchaem nastroyki na torguemuyu paru
        # BTCUSDT_settings = await get_linear_settings(symbol)
        # print('\nНастройки торговли')
        # print(BTCUSDT_settings)
        # #
        # BTCUSDT_last_price = await get_linear_price(symbol)
        # print('\nПоследняя цена')
        # print(BTCUSDT_last_price)
        # #
        # balance = float(await find_usdt_budget(api_key, secret_key))
        # print('\nБаланс юзера')
        # print(balance)
        # #
        # qty = calculate_purchase_volume(balance * 0.995, BTCUSDT_last_price,
        #                                 BTCUSDT_settings.get('min_order_qty'),
        #                                 BTCUSDT_settings.get('qty_step'))
        # print('\nКоличество к покупке')
        # print(qty)
        # #
        # # размещаем первичный ордер
        # orderLinkId = uuid.uuid4().hex[:12]
        # res = await universal_linear_market_buy_order(url, api_key, secret_key, symbol, qty, orderLinkId)
        # print('\nРезультат размещения первичного ордера')
        # print(res)
        #
        #
        # # # если повторная закупка можем закрывать по средней цене?
        # position_status = await get_user_positions(api_key, secret_key, symbol)
        # print('\nПроверяем позицию')
        # print(position_status)
        # #
        # print('\nЦена входа в позицию')
        # entry_price = position_status[0].get('avgPrice')
        # print(entry_price)
        # #
        # target_price = float(entry_price) * 1.05
        # # Таргетный профит
        # target_price = round_price(target_price, BTCUSDT_settings.get('price_tick_size'))
        #
        # print('\nТаргет цена')
        # print(target_price)
        #
        #
        # orderLinkId = uuid.uuid4().hex[:12]
        # print('prev order orderLinkId', orderLinkId)
        # prev_order_orderLinkId = '052dfa997409'
        #
        # res_two = await universal_linear_limit_order(url, api_key, secret_key,
        #                                              symbol, side, qty,
        #                                              target_price, orderLinkId)
        #
        # print('\nПроверяем результат размещения тейк ордера')
        # print(res_two)
        #
        #
        # # leverage = 2
        # # set_lev = await set_lev_linears(api_key, secret_key, symbol, leverage)
        # # print(f'\nУстановили плечо {leverage}')
        # # print(set_lev)

    asyncio.run(main())
