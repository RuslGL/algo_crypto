import asyncio
import os

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.methods.delete_my_commands import DeleteMyCommands


from tg.keyboards import Keyboards
from bd.settings import SettingsOperations


load_dotenv()
kbd = Keyboards()

ADMIN_ID = os.getenv('owner_id')
DATABASE_URL = os.getenv('database_url')

telegram_token = str(os.getenv('bot_token'))
channel_id = str(os.getenv('channel'))



dp = Dispatcher()


bot = Bot(token=telegram_token,
          default=DefaultBotProperties(
              parse_mode=ParseMode.HTML,
              link_preview_is_disabled=True
          )
          )

settings_op = SettingsOperations(DATABASE_URL)


prev_message = {}


#  ####### ГЛАВНОЕ МЕНЮ ########
#             ############
#               #####


@dp.message(Command("start"))
@dp.callback_query(F.data == 'main_menu')
async def start(message: types.Message):

    telegram_id = message.from_user.id
    params = await settings_op.get_all_settings()

    # try:
    #     if message:
    #         await bot.delete_message(chat_id=telegram_id, message_id=message.message_id)
    # except:
    #     pass

    try:
        users_prev_message = prev_message.get(telegram_id)
        if users_prev_message:
            await bot.delete_message(chat_id=telegram_id, message_id=users_prev_message)
    except:
        pass
    # except Exception as e:
    #     print(f'Problem with message deletion: {e}')

    new_message = await bot.send_message(
        chat_id=telegram_id,
        text='🟢 УПРАВЛЕНИЕ ТОРГОВЫМИ НАСТРОЙКАМИ',
        reply_markup=await kbd.main_menu(params)
    )

    prev_message[telegram_id] = new_message.message_id

    return


# # ####### НАСТРОЙКИ ########
# #     ############
# #        #####
#

@dp.callback_query(F.data.in_(['turn_trade_on', 'turn_trade_off']))
async def trade_setting(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    action = callback_query.data

    try:
        users_prev_message = prev_message.get(telegram_id)
        if users_prev_message:
            await bot.delete_message(chat_id=telegram_id, message_id=users_prev_message)
    except:
        pass
    # except Exception as e:
    #     print(f'Problem with message deletion: {e}')

    if action == 'turn_trade_off':
        await settings_op.upsert_settings({"stop_trading": True})
    elif action == 'turn_trade_on':
        await settings_op.upsert_settings({"stop_trading": False})

    params = await settings_op.get_all_settings()

    new_message = await bot.send_message(
        chat_id=telegram_id,
        text='🟢 УПРАВЛЕНИЕ ТОРГОВЫМИ НАСТРОЙКАМИ',
        reply_markup=await kbd.main_menu(params)
    )

    prev_message[telegram_id] = new_message.message_id

    return


@dp.callback_query(F.data == 'change_pair')
async def change_pair(message):
    telegram_id = message.from_user.id

    try:
        users_prev_message = prev_message.get(telegram_id)
        if users_prev_message:
            await bot.delete_message(chat_id=telegram_id, message_id=users_prev_message)
    except:
        pass
    # except Exception as e:
    #     print(f'Problem with message deletion: {e}')

    new_message = await bot.send_message(
        chat_id=telegram_id,
        text='🟢 ВЫБЕРИТЕ ТОРГУЕМУЮ ПАРУ',
        reply_markup=await kbd.pair_menu()
    )

    prev_message[telegram_id] = new_message.message_id

    return


@dp.callback_query(F.data.in_(['switch_to_btc', 'switch_to_eth']))
async def pair_setting(callback_query):
    telegram_id = callback_query.from_user.id
    action = callback_query.data

    try:
        users_prev_message = prev_message.get(telegram_id)
        if users_prev_message:
            await bot.delete_message(chat_id=telegram_id, message_id=users_prev_message)
    except:
        pass
    # except Exception as e:
    #     print(f'Problem with message deletion: {e}')

    if action == 'switch_to_btc':
        await settings_op.upsert_settings({"trading_pair": 'BTCUSDT'})
    if action == 'switch_to_eth':
        await settings_op.upsert_settings({"trading_pair": 'ETHUSDT'})

    params = await settings_op.get_all_settings()

    new_message = await bot.send_message(
        chat_id=telegram_id,
        text='🟢 УПРАВЛЕНИЕ ТОРГОВЫМИ НАСТРОЙКАМИ',
        reply_markup=await kbd.main_menu(params)
    )

    prev_message[telegram_id] = new_message.message_id

    return


@dp.callback_query(F.data == 'razmer_posizii')
async def change_pair(message):
    telegram_id = message.from_user.id

    try:
        users_prev_message = prev_message.get(telegram_id)
        if users_prev_message:
            await bot.delete_message(chat_id=telegram_id, message_id=users_prev_message)
    except:
        pass
    # except Exception as e:
    #     print(f'Problem with message deletion: {e}')

    new_message = await bot.send_message(
        chat_id=telegram_id,
        text='🟢 ВЫБЕРИТЕ РАЗМЕР ПОЗИЦИИ',
        reply_markup=await kbd.position_size_menu()
    )

    prev_message[telegram_id] = new_message.message_id

    return


@dp.callback_query(F.data.in_(['switch_to_25', 'switch_to_50',
                               'switch_to_75', 'switch_to_100',]))
async def size_setting(callback_query):
    telegram_id = callback_query.from_user.id
    action = callback_query.data

    try:
        users_prev_message = prev_message.get(telegram_id)
        if users_prev_message:
            await bot.delete_message(chat_id=telegram_id, message_id=users_prev_message)
    except:
        pass
    # except Exception as e:
    #     print(f'Problem with message deletion: {e}')


    if action == 'switch_to_25':
        await settings_op.upsert_settings({"razmer_posizii": 25})
    if action == 'switch_to_50':
        await settings_op.upsert_settings({"razmer_posizii": 50})
    if action == 'switch_to_75':
        await settings_op.upsert_settings({"razmer_posizii": 75})
    if action == 'switch_to_100':
        await settings_op.upsert_settings({"razmer_posizii": 100})

    params = await settings_op.get_all_settings()

    new_message = await bot.send_message(
        chat_id=telegram_id,
        text='🟢 УПРАВЛЕНИЕ ТОРГОВЫМИ НАСТРОЙКАМИ',
        reply_markup=await kbd.main_menu(params)
    )

    prev_message[telegram_id] = new_message.message_id

    return

@dp.callback_query(F.data == 'leverage')
async def change_pair(message):
    telegram_id = message.from_user.id

    try:
        users_prev_message = prev_message.get(telegram_id)
        if users_prev_message:
            await bot.delete_message(chat_id=telegram_id, message_id=users_prev_message)
    except:
        pass
    # except Exception as e:
    #     print(f'Problem with message deletion: {e}')

    new_message = await bot.send_message(
        chat_id=telegram_id,
        text='🟢 ВЫБЕРИТЕ РАЗМЕР ПЛЕЧА',
        reply_markup=await kbd.leverage_size_menu()
    )

    prev_message[telegram_id] = new_message.message_id

    return


@dp.callback_query(F.data.in_(['switch_lev_to_1', 'switch_lev_to_2',
                               'switch_lev_to_3', 'switch_lev_to_5',]))
async def leverage_setting(callback_query):
    telegram_id = callback_query.from_user.id
    action = callback_query.data

    try:
        users_prev_message = prev_message.get(telegram_id)
        if users_prev_message:
            await bot.delete_message(chat_id=telegram_id, message_id=users_prev_message)
    except:
        pass
    # except Exception as e:
    #     print(f'Problem with message deletion: {e}')

    if action == 'switch_lev_to_1':
        await settings_op.upsert_settings({"leverage": 1})
    if action == 'switch_lev_to_2':
        await settings_op.upsert_settings({"leverage": 2})
    if action == 'switch_lev_to_3':
        await settings_op.upsert_settings({"leverage": 3})
    if action == 'switch_lev_to_5':
        await settings_op.upsert_settings({"leverage": 5})

    params = await settings_op.get_all_settings()

    new_message = await bot.send_message(
        chat_id=telegram_id,
        text='🟢 УПРАВЛЕНИЕ ТОРГОВЫМИ НАСТРОЙКАМИ',
        reply_markup=await kbd.main_menu(params)
    )

    prev_message[telegram_id] = new_message.message_id

    return


#  ####### НЕИЗВЕСТНЫЕ СООБЩЕНИЯ ########
#             ############
#               #####
@dp.message()
async def unknown_message(message: types.Message):
    telegram_id = message.from_user.id

    try:
        users_prev_message = prev_message.get(telegram_id)
        if users_prev_message:
            await bot.delete_message(chat_id=telegram_id, message_id=users_prev_message)
    except:
        pass
    # except Exception as e:
    #     print(f'Problem with message deletion: {e}')

    params = {

    }
    new_message = await bot.send_message(
        chat_id=telegram_id,
        text='Невозможно распознать ваше сообщение, пожалуйста, воспользуйтесь кнопками меню',
        reply_markup=await kbd.main_menu(params)
    )

    prev_message[telegram_id] = new_message.message_id


#  ####### ЗАПУСК БОТА ########
#             ############
#               #####


async def start_bot():
    await bot.delete_webhook(drop_pending_updates=False)

    try:
        await dp.start_polling(bot, polling_timeout=1)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(start_bot())


