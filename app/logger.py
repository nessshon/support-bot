import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler


def setup_logger() -> None:
    """
    Настроить конфигурацию логгера для приложения.

    Эта функция обеспечивает существование директории для логов, настраивает базовый логгинг
    и устанавливает уровень логирования для конкретных логгеров.

    Логи записываются как в файл с ротацией по времени, так и в консоль.

    - Логи сохраняются в файлы в директории ".logs" с ротацией раз в день.
    - Консольный (stream) обработчик отображает логи в консоли.

    Уровень логирования для логгеров "aiogram.event" и "httpx" установлен на CRITICAL.

    :return: None
    """
    # Обеспечиваем существование директории для логов
    os.makedirs(".logs", exist_ok=True)

    # Настраиваем базовую конфигурацию логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # noqa
        handlers=[
            # Добавляем обработчик с ротацией по времени для записи логов в файл
            TimedRotatingFileHandler(
                filename=f".logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log",
                when="midnight",
                interval=1,
                backupCount=7,  # Храним логи за последние 7 дней
            ),
            # Добавляем консольный обработчик для вывода логов в консоль
            logging.StreamHandler(),
        ]
    )

    # Устанавливаем уровень логирования для логгеров aiogram.event и httpx на CRITICAL
    aiogram_logger = logging.getLogger("aiogram.event")
    aiogram_logger.setLevel(logging.CRITICAL)