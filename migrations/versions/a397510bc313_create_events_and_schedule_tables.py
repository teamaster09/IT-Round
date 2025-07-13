"""create events and schedule tables

Revision ID: a397510bc313
Revises: 
Create Date: 2025-07-13 19:00:08.659548

"""
from datetime import time
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import table, String, column, Time

from database import Weekday

# revision identifiers, used by Alembic.
revision: str = 'a397510bc313'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Создаем таблицу events
    op.create_table(
        'events',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer),
        sa.Column('name', sa.String),
        sa.Column('event_date', sa.DateTime),
        sa.Column('reminder_sent', sa.Boolean, default=False)
    )

    # Создаем таблицу schedule
    op.create_table(
        'schedule',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('group', sa.String),
        sa.Column('subject', sa.String),
        sa.Column('teacher', sa.String),
        sa.Column('room', sa.String),
        sa.Column('weekday', sa.Enum(Weekday)),
        sa.Column('start_time', sa.Time),
        sa.Column('end_time', sa.Time)
    )

    # Заполнение schedule данными
    schedule_table = table(
        'schedule',
        column('group', String),
        column('subject', String),
        column('teacher', String),
        column('room', String),
        column('weekday', sa.Enum(Weekday)),
        column('start_time', Time),
        column('end_time', Time)
    )

    # Технические предметы для ИТ-специальностей
    subjects = [
        "Математический анализ",
        "Дискретная математика",
        "Алгоритмы и структуры данных",
        "Базы данных",
        "Программирование на Python",
        "Операционные системы",
        "Компьютерные сети",
        "Теория вероятностей",
        "Web-разработка",
        "Искусственный интеллект"
    ]

    teachers = [
        "Иванова А.П.",
        "Петров С.Н.",
        "Сидорова М.В.",
        "Кузнецов Д.А.",
        "Васильева Е.С.",
        "Смирнов И.К.",
        "Федорова Л.М.",
        "Николаев П.О.",
        "Алексеева Т.Д.",
        "Григорьев В.Р."
    ]

    rooms = ["А-101", "А-102", "А-103", "А-104", "А-105", "Б-201", "Б-202", "Б-203", "В-301", "В-302"]

    # Временные слоты для занятий (5 пар в день)
    time_slots = [
        (time(9, 0), time(10, 30)),
        (time(10, 45), time(12, 15)),
        (time(13, 0), time(14, 30)),
        (time(14, 45), time(16, 15)),
        (time(16, 30), time(18, 0))
    ]

    groups = ["ИТ-41", "ИТ-42"]
    weekdays = [Weekday.MONDAY, Weekday.TUESDAY, Weekday.WEDNESDAY, Weekday.THURSDAY, Weekday.FRIDAY]

    # Генерируем данные для расписания
    schedule_data = []
    for group in groups:
        for day in weekdays:
            # Берем 5 случайных предметов для этого дня (без повторений)
            day_subjects = subjects.copy()
            import random
            random.shuffle(day_subjects)
            day_subjects = day_subjects[:5]

            for i, subject in enumerate(day_subjects):
                teacher = random.choice(teachers)
                room = random.choice(rooms)
                start_time, end_time = time_slots[i]

                schedule_data.append({
                    'group': group,
                    'subject': subject,
                    'teacher': teacher,
                    'room': room,
                    'weekday': day,
                    'start_time': start_time,
                    'end_time': end_time
                })

    # Вставляем данные в таблицу
    op.bulk_insert(schedule_table, schedule_data)

    op.bulk_insert(schedule_table, schedule_data)


def downgrade():
    op.drop_table('schedule')
    op.drop_table('events')
