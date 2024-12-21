import uuid
import asyncio
import os
import traceback

from datetime import datetime

from dotenv import load_dotenv

from settings import MAIN_URL, ENDPOINTS
from bd.settings import SettingsOperations
from bd.users import UsersOperations


from api.account import find_usdt_budget, get_user_positions, get_order_by_symbol

from api.market import (get_linear_settings, get_linear_price,
                        calculate_purchase_volume, round_price)

from api.trade import (universal_linear_market_buy_order,
                       universal_linear_limit_order, set_lev_linears, amend_linear_limit_order)



load_dotenv()

DATABASE_URL = os.getenv('database_url')

async def pre_task(settings_op, users_op):

    start = datetime.now()

    task_one = asyncio.create_task(get_linear_settings('BTCUSDT'))  # получаем сетинги на биткоин
    task_two = asyncio.create_task(get_linear_settings('ETHUSDT'))  # получаем сетинги на биткоин
    task_three = asyncio.create_task(settings_op.get_all_settings())  # получаем из БД наши настройки торговли
    task_four = asyncio.create_task(users_op.get_all_users_data())  # получаем из БД данные всех юзеров
    settings_tasks = [task_one, task_two, task_three, task_four]

    try:
        results = await asyncio.gather(*settings_tasks)
    except Exception as e:
        print(f"Ошибка в процессе получения первоначальных настроек: {e}")
        traceback.print_exc()
        try:
            results = await asyncio.gather(*settings_tasks)
        except Exception as e:
            print(f"Ошибка в процессе повтороного получения первоначальных настроек: {e}")
            traceback.print_exc()


    BTCUSDT = results[0]  # сетинги на биткоин
    ETHUSDT = results[1]  # сетинги на биткоин
    general_settings = results[2]  # наши настройки торговли
    users = results[3]  # данные всех юзеров


    for_orders = []
    problem_users = []
    valid_users = {}
    budgets = {}

    for _, row in users.iterrows():
        try:
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
        except Exception as e:
            print(f"Ошибка в процессе получения настроек отдельного юзера: {e}")
            traceback.print_exc()


    # создаем и ассинхронно отправляем по всем юзерам запрос по бюджету
    order_tasks = []
    for element in for_orders:
        order_tasks.append(find_usdt_budget(element[0], element[1], element[2]))

    try:
        order_results = await asyncio.gather(*order_tasks)
    except Exception as e:
        print(f"Ошибка в процессе получения бюджетов пользователей: {e}")
        traceback.print_exc()
        try:
            order_results = await asyncio.gather(*order_tasks)
        except Exception as e:
            print(f"Ошибка в процессе повтороного получения бюджетов пользователей: {e}")
            traceback.print_exc()


    for element in order_results:
        try:
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
        except Exception as e:
            print(f"Ошибка в процессе обработки результатов запросов на получение бюджетов по отдельному юзеру: {e}")
            traceback.print_exc()


    # выставляем плечи по сеттингам для всех валидных юзеров
    leverage_tasks = []
    for user, items in budgets.items():
        try:
            user_set = valid_users.get(user)
            leverage_tasks.append(set_lev_linears(
                user_set[0], user_set[1],
                general_settings.get('trading_pair'),
                general_settings.get('leverage')))
        except Exception as e:
            print(f"Ошибка в процессе подготовки ордеров для установки плечей по отдельному юзеру: {e}")
            traceback.print_exc()

    try:
        await asyncio.gather(*leverage_tasks)
    except Exception as e:
        print(f"Ошибка в процессе изменения плечей по пользователям: {e}")
        traceback.print_exc()
        try:
            await asyncio.gather(*leverage_tasks)
        except Exception as e:
            print(f"Ошибка в процессе повторной попытки изменения плечей по пользователям: {e}")
            traceback.print_exc()

    print('problem_users', problem_users)
    print('Время исполнения pre_task', datetime.now() - start)

    return BTCUSDT, ETHUSDT, general_settings, valid_users, budgets, problem_users


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

    # получаем последние цены на бирже
    try:
        last_price = await get_linear_price(trading_pair)
    except Exception as e:
        print(f"Ошибка в получения цен на пары: {e}")
        traceback.print_exc()
        try:
            last_price = await get_linear_price(trading_pair)
        except Exception as e:
            print(f"Ошибка в попытке повторного получения цен на пары: {e}")
            traceback.print_exc()


    # создаем таски на покупк для всех юзеров
    orders_tasks = []
    for user, items in budgets.items():
        try:
            user_set = valid_users.get(user)


            orderLinkId = uuid.uuid4().hex[:34]
            balance = float(budgets.get(user))
            qty = calculate_purchase_volume(balance * 0.995, last_price,
                                            actual_settings.get('min_order_qty'),
                                            actual_settings.get('qty_step'))
            if qty == -1:
                print('report not enough budget')
                continue

            api_key = user_set[0]
            secret_key = user_set[1]

            orders_tasks.append(
                universal_linear_market_buy_order(user, api_key, secret_key, trading_pair, qty, orderLinkId))
        except Exception as e:
            print(f"Ошибка в подготовке ордера по отдельному юзеру: {e}")
            traceback.print_exc()

    # ассинхронно пушим на биржу все ордера и получаем респонс от биржи
    orders_result = await asyncio.gather(*orders_tasks)
    print('Время размещения первичных ордеров main_task', datetime.now() - start)
    # not enough udget - leverago or removed [(666038149, '01af001fe5ad', {'retCode': 110007, 'retMsg': 'ab not enough for new order', 'result': {}, 'retExtInfo': {}, 'time': 1734443351934})]
    # good response [(666038149, '40344f7b3769', {'retCode': 0, 'retMsg': 'OK', 'result': {'orderId': 'ea123021-ea84-4a37-9dc5-fa72eac814d4', 'orderLinkId': '40344f7b3769'}, 'retExtInfo': {}, 'time': 1734443396670})]


    open_positions = []
    open_orders = []

    # по каждому валидному респонсу на ордера
    for element in orders_result:
        try:
            if element[2].get('retMsg') == 'OK':
                print('get info and prepare orders')
                user = element[0]
                user_set = valid_users.get(user)
                api_key = user_set[0]
                secret_key = user_set[1]

                # получаем открытые позиции по юзеру с валидным респонсом
                open_positions.append(
                    get_user_positions(user, api_key, secret_key, trading_pair))

                # получаем открытые ордера по символу, который только что купили для каждого юзера
                open_orders.append(
                    get_order_by_symbol(user, api_key, secret_key, trading_pair, element[1]))


            # не хватает бюджета - причина либо неверное плечо (не хватает ликвидности), либо юзер изменил остаток
            elif element[2].get('retMsg') == 'ab not enough for new order':
                print('report lack of budget due to leverages or usdt removal by user')
        except Exception as e:
            print(f"Ошибка в подготовке ордеров на получение инфо об открытых ордерах и позициях у отдельного юзера: {e}")
            traceback.print_exc()

    # ассинхронно пушим на биржу одновеменно все ордера на получение открытых позиций, следующим шагом на получение всех открытых ордеров

    open_positions = await asyncio.gather(*open_positions)
    try:
        open_orders = await asyncio.gather(*open_orders)
    except Exception as e:
        print(f"Ошибка в получения информации об открытых ордерах: {e}")
        traceback.print_exc()

    # print('cancel for test')
    # await asyncio.sleep(5)
    # print('open_positions', open_positions)
    # print('open_orders', open_orders)


    target_per_cent = 1 + (general_settings.get('teyk_profit')/100)
    print('target_per_cent', target_per_cent)
    for index, position in enumerate(open_positions):
        try:
            user = position[0]
            result_position = position[1]

            close_price = None

            user_orders = open_orders[index]
            if user == user_orders[0]:

                # может по позиции проверить? или по обоим?
                if user_orders[2].get('retMsg') == 'OK':
                    open_orders = user_orders[2].get('result').get('list')
                    user_set = valid_users.get(user)
                    api_key = user_set[0]
                    secret_key = user_set[1]

                    if not open_orders:
                        print('price = AVG position price')
                        print(position)
                        entry_price = position[1][0].get('avgPrice')
                        target_price = float(entry_price) * target_per_cent
                        size = position[1][0].get('size')
                        target_price = round_price(target_price, BTCUSDT_settings.get('price_tick_size'))
                        print('TP target price', target_price)
                        print('TP size', size)

                        orderLinkId = uuid.uuid4().hex[:34]

                        res_two = await universal_linear_limit_order(api_key, secret_key,
                                                                     trading_pair, size,
                                                                     target_price, orderLinkId)
                        print('New order', res_two)

                    else:
                        print('Buy with last price')
                        print('open_orders', open_orders[0])
                        prev_order_orderLinkId = open_orders[0].get('orderLinkId')
                        price = open_orders[0].get('price')

                        if not price:
                            print('Рассчитать заново')

                        size = position[1][0].get('size')

                        res_three = await amend_linear_limit_order(api_key, secret_key,
                                                 trading_pair, size, prev_order_orderLinkId)
                        print('res_three', res_three)
                        if res_three.get('retMsg') == 'order not exists or too late to replace':
                            print('order not exists or too late to replace')
                            entry_price = position[1][0].get('avgPrice')
                            target_price = float(entry_price) * target_per_cent
                            size = position[1][0].get('size')
                            target_price = round_price(target_price, BTCUSDT_settings.get('price_tick_size'))
                            print('TP target price', target_price)
                            print('TP size', size)

                            orderLinkId = uuid.uuid4().hex[:34]

                            res_four = await universal_linear_limit_order(api_key, secret_key,
                                                                         trading_pair, size,
                                                                         target_price, orderLinkId)
                            print('New order, res four', res_four)
            else:
                print('error in users indexing')
        except Exception as e:
            print(f"Ошибка в установке ордеров на продажу по отдельному юзеру: {e}")
            traceback.print_exc()
    print('Время исполнения main_task', datetime.now() - start)


if __name__ == '__main__':



    async def main():

        settings_op = SettingsOperations(DATABASE_URL)
        users_op = UsersOperations(DATABASE_URL)

        BTCUSDT_settings, ETHUSDT_settings, general_settings, valid_users, budgets, problem_users = await pre_task(settings_op,
                                                                                                    users_op)

        await main_task(BTCUSDT_settings, ETHUSDT_settings, general_settings, valid_users, budgets)

    asyncio.run(main())
