import config
import logging
import gpt_model
import keyboards as skb
import messages_constants as msgc

from aiogram.dispatcher import filters
from aiogram.dispatcher import FSMContext
from schedule import weekly_schedule as wsch
from schedule import general_schedule as gsch
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
storage = MemoryStorage()
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot, storage=storage)


class ScheduleStatesGroup(StatesGroup):
    group = State()


sch_obj = gsch.Schedule()
sch_obj.load_url()
sch_obj.load_available_weeks()

lsm = gsch.LastScheduleMessage()
lsm.load_message_data()

wsch_obj = wsch.WeeklySchedule()


async def anti_flood(*args, **kwargs):
    message = args[0]
    await message.answer(text=msgc.base_messages.get('anti_flood'), parse_mode='Markdown')


@dp.message_handler(commands=['start', 'help'])
@dp.throttled(rate=3)
async def send_welcome(message: types.Message):
    await message.answer(text=msgc.base_messages.get('help'), parse_mode='Markdown')


@dp.message_handler(commands=['sev'])
@dp.throttled(rate=3)
async def sev_command(message: types.Message):
    await message.answer(text=msgc.sevsu_messages.get('sevsu_urls'),
                         reply_markup=skb.get_sevsu_keyboard(),
                         parse_mode='Markdown')


@dp.message_handler(commands=['sch'])
@dp.throttled(anti_flood, rate=10)
async def send_schedule(message: types.Message):
    try:
        if lsm.message_id:
            await bot.edit_message_reply_markup(chat_id=lsm.chat_id, message_id=lsm.message_id, reply_markup=InlineKeyboardMarkup())
    except:
        pass

    wsch_obj.set_default_values()
    print(message.from_user.full_name)

    await message.delete()
    process_message = await message.answer(text=msgc.schedule_messages.get('check'),
                                           parse_mode='Markdown')
    try:
        is_download_required = sch_obj.check_to_download()
        if is_download_required:
            await process_message.delete()
            process_message = await message.answer(text=msgc.schedule_messages.get('update_process'),
                                                   parse_mode='Markdown')

            sch_obj.download()
            sch_obj.save_iit_schedules_data()
            sch_obj.save_url_data()
            sch_obj.define_available_weeks()
            sch_obj.save_available_weeks_data()

            await message.answer(text=msgc.schedule_messages.get('updated'),
                                 parse_mode='Markdown')

        if not sch_obj.available_weeks:
            sch_obj.define_available_weeks()
            sch_obj.save_available_weeks_data()

        await message.answer(text=msgc.schedule_messages.get('group'),
                             reply_markup=skb.get_schedule_groups_keyboard(),
                             parse_mode='Markdown')
        await ScheduleStatesGroup.group.set()
    except:
        await message.answer('♻️ Ошибка при скачивании файла')
    finally:
        await process_message.delete()


@dp.message_handler(filters.Text(equals='🗑️ Отмена'), state='*')
async def cancel_schedule(message: types.Message, state: FSMContext):
    if state is None:
        return
    await message.answer(text=msgc.schedule_messages.get('cancel'),
                         reply_markup=ReplyKeyboardRemove(),
                         parse_mode='Markdown')
    await message.delete()
    await state.finish()


@dp.message_handler(filters.Text(equals=['ИСб-21-1-о', 'ИСб-21-2-о', 'ИСб-21-3-о', 'ПИб-21-1-о']),
                    state=ScheduleStatesGroup.group)
async def schedule_improve_process(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['group'] = int(message.text[-3]) if 'ИС' in message.text else 4

    bot_message = await message.answer(text=msgc.schedule_messages.get('load'),
                                       reply_markup=ReplyKeyboardRemove(),
                                       parse_mode='Markdown')

    try:
        wsch_obj.group_num = data['group']

        if wsch_obj.week_num in sch_obj.available_weeks:  # Проверка на существования недели
            is_schedule_exist = wsch_obj.check_to_create_new()
            if is_schedule_exist:
                wsch_obj.load_data()
            else:
                wsch_obj.create_xlsx()
                wsch_obj.define_weekly_schedule()
                wsch_obj.save_data()

            schedule_day_text = wsch_obj.get_weekly_schedule_day()
            schedule_markup = skb.get_weekly_schedule_keyboard(sch_obj.available_weeks, wsch_obj.week_num)
            schedule_message = await message.answer(text=schedule_day_text,
                                                    reply_markup=schedule_markup,
                                                    parse_mode='Markdown')

            lsm.message_id = schedule_message.message_id
            lsm.chat_id = message.chat.id
            lsm.save_message_data()
        else:
            await message.answer(msgc.schedule_messages.get('holiday'), parse_mode='Markdown')
    except:
        await message.answer('📦 Ошибка при загрузке данных')
    finally:
        await bot_message.delete()
        await state.finish()


@dp.message_handler(filters.Text(startswith='мил ', ignore_case=True))
@dp.throttled(anti_flood, rate=15)
async def send_gpt_request(message: types.Message):
    print(f'Отправитель: {message.from_user.full_name}\nЗапрос: {message.text}\n\n')

    bot_message = await message.answer(text=msgc.get_rand_process_message(),
                                       parse_mode='Markdown')
    try:
        gpt_response = gpt_model.response_to_message(message.text.partition(' ')[2])
        await message.reply(text=gpt_response,
                            parse_mode='Markdown')
    except:
        await message.answer(text=msgc.base_messages.get('error'),
                             parse_mode='Markdown')
    finally:
        await bot_message.delete()


@dp.callback_query_handler(lambda callback: callback.data.startswith('schedule_week'))
async def callback_schedule_weeks(callback: types.CallbackQuery):
    await callback.message.delete()
    bot_message = await callback.message.answer(text=msgc.schedule_messages.get('load'),
                                                reply_markup=ReplyKeyboardRemove(),
                                                parse_mode='Markdown')

    week_num = int(callback.data[callback.data.rfind('_') + 1:])
    if week_num == wsch_obj.week_num:
        await callback.answer('🫵 Эта неделя уже выбрана')
    else:
        wsch_obj.week_num = week_num
        is_schedule_exist = wsch_obj.check_to_create_new()

        if is_schedule_exist:
            wsch_obj.load_data()
        else:
            wsch_obj.create_xlsx()
            wsch_obj.define_weekly_schedule()
            wsch_obj.save_data()

        schedule_day_text = wsch_obj.get_weekly_schedule_day()
        schedule_markup = skb.get_weekly_schedule_keyboard(sch_obj.available_weeks, week_num)
        schedule_message = await callback.message.answer(text=schedule_day_text,
                                                         reply_markup=schedule_markup,
                                                         parse_mode='Markdown')

        lsm.message_id = schedule_message.message_id
        lsm.chat_id = callback.message.chat.id
        lsm.save_message_data()

        await bot_message.delete()
        await callback.answer()


@dp.callback_query_handler(lambda callback: callback.data.startswith('weekly_schedule_day'))
async def callback_weekly_schedule_days(callback: types.CallbackQuery):
    day_num = int(callback.data[-1])
    if day_num == wsch_obj.day_num:
        await callback.answer('🫵 Этот день уже выбран')
    else:
        wsch_obj.day_num = day_num
        schedule_day_text = wsch_obj.get_weekly_schedule_day()
        await callback.message.edit_text(text=schedule_day_text, parse_mode='Markdown')
        schedule_markup = skb.get_weekly_schedule_keyboard(sch_obj.available_weeks, wsch_obj.week_num)
        await callback.message.edit_reply_markup(reply_markup=schedule_markup )
        await callback.answer()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
