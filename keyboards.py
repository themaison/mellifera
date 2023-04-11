import sevsu_constants

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

sevsu_markup = InlineKeyboardMarkup(row_width=2)
lk = InlineKeyboardButton(text='👤 Кабинет', url=sevsu_constants.LK_URL)
mudl = InlineKeyboardButton(text='💻 Мудл', url=sevsu_constants.DO_SEVSU_URL)
rocket = InlineKeyboardButton(text='🚀 Рокет-чат', url=sevsu_constants.ROCKET_CHAT_URL)
elective = InlineKeyboardButton(text='🎽 Элективы', url=sevsu_constants.ELECTIVE_URL)
sch = InlineKeyboardButton(text='📖 Расписание', url=sevsu_constants.SCHEDULE_URL)
sevsu_site = InlineKeyboardButton(text='🌊 Сайт', url=sevsu_constants.SEVSU_URL)
sevsu_markup.add(sevsu_site, lk, sch, mudl, rocket, elective)

schedule_groups_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
sg1 = KeyboardButton(text='ИСб-21-1-о')
sg2 = KeyboardButton(text='ИСб-21-2-о')
sg3 = KeyboardButton(text='ИСб-21-3-о')
sg4 = KeyboardButton(text='ПИб-21-1-о')
cancel_schedule = KeyboardButton('🗑️ Отмена')
schedule_groups_markup.add(sg1, sg2, sg3, sg4).add(cancel_schedule)


def get_sevsu_keyboard() -> InlineKeyboardMarkup:
    return sevsu_markup


def get_schedule_groups_keyboard() -> ReplyKeyboardMarkup:
    return schedule_groups_markup


def get_weekly_schedule_keyboard(available_weeks: list, week_num: int) -> InlineKeyboardMarkup:
    weekly_schedule_markup = InlineKeyboardMarkup(row_width=6)
    wsd1 = InlineKeyboardButton('Пн', callback_data='weekly_schedule_day_1')
    wsd2 = InlineKeyboardButton('Вт', callback_data='weekly_schedule_day_2')
    wsd3 = InlineKeyboardButton('Ср', callback_data='weekly_schedule_day_3')
    wsd4 = InlineKeyboardButton('Чт', callback_data='weekly_schedule_day_4')
    wsd5 = InlineKeyboardButton('Пт', callback_data='weekly_schedule_day_5')
    wsd6 = InlineKeyboardButton('Сб', callback_data='weekly_schedule_day_6')
    weekly_schedule_markup.add(wsd1, wsd2, wsd3, wsd4, wsd5, wsd6)

    week_pos = available_weeks.index(week_num)
    if week_pos == 0:
        next_week_button = InlineKeyboardButton(f'🔍 {week_num + 1} Неделя', callback_data=f'schedule_week_{week_num + 1}')
        weekly_schedule_markup.add(next_week_button)
    elif week_pos == len(available_weeks)-1:
        prev_week_button = InlineKeyboardButton(f'🔍 {week_num - 1} Неделя', callback_data=f'schedule_week_{week_num - 1}')
        weekly_schedule_markup.add(prev_week_button)
    else:
        prev_week_button = InlineKeyboardButton(f'🔍 {week_num - 1} Неделя', callback_data=f'schedule_week_{week_num - 1}')
        next_week_button = InlineKeyboardButton(f'🔍 {week_num + 1} Неделя', callback_data=f'schedule_week_{week_num + 1}')
        weekly_schedule_markup.add(prev_week_button, next_week_button)
    return weekly_schedule_markup
