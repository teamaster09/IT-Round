from datetime import datetime, timedelta

from aiogram import Router, types, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.testing.plugin.plugin_base import logging

from database import get_week_schedule, Session, engine, Event, \
    Schedule, SessionLocal, Weekday, get_db, create_event
from reminders import check_reminders

# Создаем роутер
router = Router()

class Form(StatesGroup):
    waiting_for_event_data = State()

# Главное меню (для /start и /help)
async def show_main_menu(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📅 Сегодня"), types.KeyboardButton(text="📆 Завтра")],
            [types.KeyboardButton(text="🗓 Неделя"), types.KeyboardButton(text="➕ Добавить")],
            [types.KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )
    help_text = (
        "ℹ️ Доступные команды:\n"
        "/today - Расписание на сегодня\n"
        "/tomorrow - На завтра\n"
        "/week - На неделю\n"
        "/add - Добавить событие\n\n"
        "Или используйте кнопки ниже 👇"
    )
    await message.answer(help_text, reply_markup=keyboard)

# Обработчики команд
@router.message(CommandStart())
@router.message(Command("start"))
@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def handle_start_help(message: types.Message):
    await show_main_menu(message)

@router.message(Command("today", "tomorrow"))
@router.message(F.text.in_(["📅 Сегодня", "📆 Завтра"]))
async def handle_daily_schedule(message: Message):
    # Определяем тип дня для всех вариантов вызова
    if (message.text == "📅 Сегодня" or
            isinstance(message.text, str) and message.text.startswith('/today')):
        day_type = "today"
    elif (message.text == "📆 Завтра" or
          isinstance(message.text, str) and message.text.startswith('/tomorrow')):
        day_type = "tomorrow"
    else:
        await message.answer("Неизвестный запрос")
        return

    # Создаем сессию БД
    db = SessionLocal()
    try:
        schedule = await get_daily_schedule(day_type, db)

        if schedule:
            await message.answer(schedule, parse_mode="HTML",  reply_markup=get_main_keyboard())
        else:
            await message.answer("Занятий нет",  reply_markup=get_main_keyboard())
    except Exception as e:
        await message.answer("Произошла ошибка при получении расписания",  reply_markup=get_main_keyboard())
        logging.error(f"Ошибка: {str(e)}")
    finally:
        db.close()  # Важно закрыть сессию

@router.message(Command("week"))
@router.message(F.text == "🗓 Неделя")
async def handle_week_schedule(message: Message):
    db = SessionLocal()
    try:
        schedule = await get_week_schedule(db)

        if schedule:
            for i in range(0, len(schedule), 4000):
                await message.answer(schedule[i:i + 4000], parse_mode="HTML",  reply_markup=get_main_keyboard())
        else:
            await message.answer("Расписание на неделю не найдено")
    except Exception as e:
        await message.answer("Произошла ошибка при получении расписания",  reply_markup=get_main_keyboard())
        logging.error(f"Ошибка: {str(e)}")
    finally:
        db.close()

async def get_daily_schedule(day: str, db: Session) -> str:
    """Возвращает расписание на сегодня/завтра"""
    try:
        # Определяем день недели
        target_date = datetime.now()
        if day == "tomorrow":
            target_date += timedelta(days=1)

        weekday_en = target_date.strftime("%A")
        weekdays_map = {
            "Monday": Weekday.MONDAY,
            "Tuesday": Weekday.TUESDAY,
            "Wednesday": Weekday.WEDNESDAY,
            "Thursday": Weekday.THURSDAY,
            "Friday": Weekday.FRIDAY,
            "Saturday": Weekday.SATURDAY,
            "Sunday": Weekday.SUNDAY
        }
        weekday = weekdays_map.get(weekday_en)

        if not weekday:
            return "Неизвестный день недели"

        # Получаем расписание (используем enum)
        schedules = db.execute(
            select(Schedule)
            .where(Schedule.weekday == weekday)  # Сравниваем с enum!
            .order_by(Schedule.group, Schedule.start_time)
        ).scalars().all()

        if not schedules:
            return None

        # Форматируем результат
        message = f"📅 Расписание на {weekday.display_name}:\n\n"
        current_group = None

        for item in schedules:
            if item.group != current_group:
                message += f"👥 <b>Группа {item.group}</b>:\n"
                current_group = item.group

            # Проверка на случай None в времени
            start = item.start_time.strftime('%H:%M') if item.start_time else "??:??"
            end = item.end_time.strftime('%H:%M') if item.end_time else "??:??"

            message += (
                f"🕒 {start}-{end} "
                f"{item.subject} ({item.room}, {item.teacher})\n"
            )

        return message

    except Exception as e:
        logging.error(f"Ошибка при получении расписания: {str(e)}")
        return None


async def get_week_schedule(db: Session) -> str:
    """Возвращает расписание на всю неделю"""
    try:
        weekdays = [
            Weekday.MONDAY,
            Weekday.TUESDAY,
            Weekday.WEDNESDAY,
            Weekday.THURSDAY,
            Weekday.FRIDAY,
            Weekday.SATURDAY,
            Weekday.SUNDAY
        ]
        messages = []

        for day in weekdays:
            schedules = db.execute(
                select(Schedule)
                .where(Schedule.weekday == day)  # Сравниваем с enum
                .order_by(Schedule.group, Schedule.start_time)
            ).scalars().all()

            if not schedules:
                messages.append(f"📅 {day.display_name}: Занятий нет\n")
                continue

            day_message = f"📅 <b>{day.display_name}</b>:\n\n"
            current_group = None

            for item in schedules:
                if item.group != current_group:
                    day_message += f"👥 <b>Группа {item.group}</b>:\n"
                    current_group = item.group

                day_message += (
                    f"🕒 {item.start_time.strftime('%H:%M')}-{item.end_time.strftime('%H:%M')} "
                    f"{item.subject} ({item.room}, {item.teacher})\n"
                )

            messages.append(day_message)

        return "\n".join(messages)

    finally:
        db.close()

@router.message(Command("add"))
@router.message(F.text == "➕ Добавить")
async def handle_add_event(message: types.Message, state: FSMContext):
    await message.answer("Введите данные в формате: Название Дата Время\nПример: Контрольная 2025-07-13 15:00")
    await state.set_state(Form.waiting_for_event_data)

@router.message(Form.waiting_for_event_data)
async def process_event_data(message: types.Message, state: FSMContext):
    db = next(get_db())
    args = message.text.split()
    if len(args) < 3:
        await message.answer("❌ Ошибка. Формат: Название ГГГГ-ММ-ДД ЧЧ:ММ\n(Название должно состоять из одного слова)\nПопробуйте еще раз",  reply_markup=get_main_keyboard())
        return

    try:
        await create_event(message)
        await message.answer(f"✅ Событие '{args[0]}' добавлено на {args[1]} {args[2]}!",  reply_markup=get_main_keyboard())
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}\nПопробуйте еще раз",  reply_markup=get_main_keyboard())

def get_main_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📅 Сегодня"), types.KeyboardButton(text="📆 Завтра")],
            [types.KeyboardButton(text="🗓 Неделя"), types.KeyboardButton(text="➕ Добавить")]
        ],
        resize_keyboard=True,
        persistent = True  # Ключевой параметр!
    )

@router.message(Command("debug_db"))
async def debug_db(message: types.Message):
    # Создаем новую сессию для каждого запроса
    with Session(engine) as session:
        events = session.query(Event).all()
        for e in events:
            await message.answer(f"{e.name} в {e.event_date.strftime('%d.%m.%Y %H:%M')}")
        # Сессия автоматически закроется после выхода из блока with

@router.message(Command("force_check"))
async def force_check(message: types.Message, bot: Bot):  # Добавляем bot в параметры
    await check_reminders(bot)
    await message.answer("Проверка выполнена!")


@router.message(Command("schedule"))
async def handle_schedule_info(message: types.Message):
    await message.answer("ℹ️ Информация о расписании...")