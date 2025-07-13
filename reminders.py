import logging
from datetime import datetime, timedelta

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from database import Event, SessionLocal

scheduler = AsyncIOScheduler()


async def check_reminders(bot: Bot):
    # Создаем новую сессию для каждого выполнения
    db = SessionLocal()
    try:
        now = datetime.now()
        check_window_start = now + timedelta(minutes=57)
        check_window_end = now + timedelta(minutes=62)

        # Получаем события для напоминания
        events = db.execute(
            select(Event)
            .where(Event.event_date.between(check_window_start, check_window_end))
            .where(Event.reminder_sent == False)
        ).scalars().all()

        for event in events:
            try:
                await bot.send_message(
                    chat_id=event.user_id,
                    text=f"🔔 Напоминание: {event.name} в {event.event_date.strftime('%H:%M')}"
                )
                event.reminder_sent = True
                db.commit()
            except Exception as e:
                logging.error(f"Ошибка отправки напоминания: {e}")
                db.rollback()

    except Exception as e:
        logging.error(f"Ошибка проверки напоминаний: {e}")
    finally:
        db.close()  # Важно закрыть сессию


def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_reminders,
        'interval',
        minutes=5,
        args=[bot],
        id='reminder_job',
        replace_existing=True
    )
    scheduler.start()