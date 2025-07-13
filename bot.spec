# -*- mode: python ; coding: utf-8 -*-
import Analysis
import PYZ

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['C:\\Users\\zotki\\PycharmProjects\\IT-Round'],
    binaries=[],
    datas=[
        ('config.py', '.'),
        ('database.py', '.'),
        ('handlers.py', '.'),
        ('reminders.py', '.'),
        ('events.db', '.'),
        ('alembic.ini', '.')
    ],
    hiddenimports=[
        'aiogram',
        'aiogram.filters',
        'aiogram.types',
        'sqlalchemy',
        'sqlalchemy.ext.asyncio',
        'apscheduler',
        'logging',
        'asyncio',
        'datetime'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TelegramBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Для отладки
    icon=None  # Можно добавить bot.ico если нужно
)