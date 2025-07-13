from datetime import datetime, timedelta
from enum import Enum as PyEnum

from aiogram.types import Message
from sqlalchemy import Enum
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.testing.plugin.plugin_base import logging

SQLALCHEMY_DATABASE_URL = "sqlite:///events.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Для SQLite
    echo=True  # Для отладки
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine  # Явная привязка к engine
)

Base = declarative_base()

class Weekday(PyEnum):
    MONDAY = "Понедельник"
    TUESDAY = "Вторник"
    WEDNESDAY = "Среда"
    THURSDAY = "Четверг"
    FRIDAY = "Пятница"
    SATURDAY = "Суббота"
    SUNDAY = "Воскресенье"

    @property
    def display_name(self):
        return self.value


class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    name = Column(String)
    event_date = Column(DateTime)
    reminder_sent = Column(Boolean, default=False)

class Schedule(Base):
    __tablename__ = 'schedule'
    id = Column(Integer, primary_key=True)
    group = Column(String)         # Например, "ИТ-41"
    subject = Column(String)       # "Математический анализ"
    teacher = Column(String)       # "Иванова А.П."
    room = Column(String)          # "А-105"
    weekday = Column(Enum(Weekday)) # День недели
    start_time = Column(Time)      # Время начала (14:30)
    end_time = Column(Time)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def create_event(message: Message):
    db = next(get_db())  # Получаем сессию БД

    try:
        # Парсим текст сообщения (пример: "Создать событие Встреча 2023-12-31 15:00")
        parts = message.text.split()
        if len(parts) < 3:
            await message.answer("Формат:[название] [дата] [время]")
            return

        event_name = parts[0]
        event_date = datetime.strptime(f"{parts[1]} {parts[2]}", "%Y-%m-%d %H:%M")

        # Создаем событие
        new_event = Event(
            user_id=message.from_user.id,
            name=event_name,
            event_date=event_date
        )

        db.add(new_event)
        db.commit()

    except ValueError:
        await message.answer("❌ Неверный формат даты. Используйте ГГГГ-ММ-ДД ЧЧ:ММ")
    except Exception as e:
        db.rollback()
        await message.answer("❌ Ошибка при создании события")
        logging.error(f"Ошибка создания события: {str(e)}")
    finally:
        db.close()
def get_today_schedule(user_id: int) -> str:
    """Возвращает расписание на сегодня"""
    session = Session()
    today = datetime.now().date()
    events = session.query(Event).filter(
        Event.user_id == user_id,
        Event.event_date >= today,
        Event.event_date < today + timedelta(days=1)
    ).all()
    session.close()
    return format_events(events)

def get_tomorrow_schedule(user_id: int) -> str:
    """Возвращает расписание на завтра"""
    session = Session()
    tomorrow = datetime.now().date() + timedelta(days=1)
    events = session.query(Event).filter(
        Event.user_id == user_id,
        Event.event_date >= tomorrow,
        Event.event_date < tomorrow + timedelta(days=1)
    ).all()
    session.close()
    return format_events(events)

def format_events(events: list[Event]) -> str:
    """Форматирует список событий в текст"""
    if not events:
        return ""
    return "\n".join(
        f"⏰ {e.name} в {e.event_date.strftime('%H:%M')}"
        for e in sorted(events, key=lambda x: x.event_date)
    )


def get_events_for_reminder(start: datetime, end: datetime):
    """Ищет события в временном окне с непрочитанными напоминаниями"""
    session = Session()
    try:
        events = session.query(Event).filter(
            Event.event_date >= start,
            Event.event_date <= end,
            Event.reminder_sent == False
        ).all()
        return events
    finally:
        session.close()


def get_week_schedule(user_id: int) -> str:
    session = Session()
    today = datetime.now().date()
    week_later = today + timedelta(days=7)

    events = session.query(Event).filter(
        Event.user_id == user_id,
        Event.event_date >= today,
        Event.event_date <= week_later
    ).order_by(Event.event_date).all()

    session.close()

    if not events:
        return ""

    schedule = "📅 Расписание на неделю:\n"
    for event in events:
        schedule += f"• {event.event_date.strftime('%A (%d.%m)')}: {event.name} в {event.event_date.strftime('%H:%M')}\n"

    return schedule