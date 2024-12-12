from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import os
from dotenv import load_dotenv


load_dotenv()

ADMIN_ID = os.getenv('admin_id')


# Класс для создания клавиатур
class Keyboards:

    def __init__(self):
        # Кнопка для возвращения в главное меню
        self.btn_back_to_main_menu = InlineKeyboardButton(
            text='⬅️В главное меню',
            callback_data='back_to_main_menu'
        )
        # Клавиатура с одной кнопкой для возвращения в главное меню
        self.single_btn_back_to_main_menu = InlineKeyboardMarkup(inline_keyboard=[
            [self.btn_back_to_main_menu],
        ])



#  ####### ГЛАВНОЕ МЕНЮ ########
#             ############
#               #####

    async def main_menu(self, params):
        try:
            if params.get('stop_trading'):
                btn_trade = 'Включить торговлю'
                callback_trade = 'turn_trade_on'
            else:
                btn_trade = 'Выключить торговлю'
                callback_trade = 'turn_trade_off'

            trading_pair = params.get('trading_pair')
            razmer_posizii = params.get('razmer_posizii')
            leverage = params.get('leverage')
            teyk_profit = params.get('teyk_profit')

        except Exception as e:
            pass

        # Торговля вкл/выкл
        btn_1 = InlineKeyboardButton(
            text=btn_trade,
            callback_data=callback_trade,
        )

        # Торг пара
        btn_2 = InlineKeyboardButton(
            text=f'Торгуемая пара {trading_pair}',
            callback_data='change_pair'
        )

        #Grafik
        btn_3 = InlineKeyboardButton(
            text='График торговли',
            callback_data='schedule'
        )

        # Razmer posizii
        btn_4 = InlineKeyboardButton(
            text=f'Размер позиции {razmer_posizii}%',
            callback_data='razmer_posizii'
        )

        # Plecho
        btn_5 = InlineKeyboardButton(
            text=f'Размер плеча {leverage}',
            callback_data='leverage'
        )

        btn_6 = InlineKeyboardButton(
            text=f'Тейк профит {teyk_profit}%',
            callback_data='take_profit'
        )


        our_menu = [[btn_1,],
                    [btn_2],
                    [btn_3],
                    [btn_4],
                    [btn_5],
                    [btn_6]]


        # Проверка на админские права и добавление кнопки
        #if int(params.get('telegram_id')) == int(ADMIN_ID):
        return InlineKeyboardMarkup(inline_keyboard=our_menu)


    async def pair_menu(self):
        btn_1 = InlineKeyboardButton(
            text='BTCUSDT',
            callback_data='switch_to_btc',
        )
        btn_2 = InlineKeyboardButton(
            text='ETHUSDT',
            callback_data='switch_to_eth'
        )

        btn_3 = InlineKeyboardButton(
            text='Вернуться в главное меню',
            callback_data='main_menu',
        )


        our_menu = [[btn_1, btn_2],
                    [btn_3]]

        return InlineKeyboardMarkup(inline_keyboard=our_menu)


    async def position_size_menu(self):
        btn_1 = InlineKeyboardButton(
            text='25%',
            callback_data='switch_to_25',
        )
        btn_2 = InlineKeyboardButton(
            text='50%',
            callback_data='switch_to_50'
        )

        btn_3 = InlineKeyboardButton(
            text='75%',
            callback_data='switch_to_75'
        )

        btn_4 = InlineKeyboardButton(
            text='100%',
            callback_data='switch_to_100'
        )

        btn_5 = InlineKeyboardButton(
            text='Вернуться в главное меню',
            callback_data='main_menu',
        )


        our_menu = [[btn_1, btn_2],
                    [btn_3, btn_4],
                    [btn_5]]

        return InlineKeyboardMarkup(inline_keyboard=our_menu)

    async def leverage_size_menu(self):
        btn_1 = InlineKeyboardButton(
            text='1',
            callback_data='switch_lev_to_1',
        )
        btn_2 = InlineKeyboardButton(
            text='2',
            callback_data='switch_lev_to_2'
        )

        btn_3 = InlineKeyboardButton(
            text='3',
            callback_data='switch_lev_to_3'
        )

        btn_4 = InlineKeyboardButton(
            text='5',
            callback_data='switch_lev_to_5'
        )

        btn_5 = InlineKeyboardButton(
            text='Вернуться в главное меню',
            callback_data='main_menu',
        )


        our_menu = [[btn_1, btn_2],
                    [btn_3, btn_4],
                    [btn_5]]

        return InlineKeyboardMarkup(inline_keyboard=our_menu)
