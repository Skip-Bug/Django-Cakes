# CakeBake

[![GitHub Репозиторий](https://img.shields.io/badge/Репозиторий-GitHub-blue?logo=github)](https://github.com/Skip-Bug/Django-Cakes)
[![Лицензия MIT](https://img.shields.io/badge/Лицензия-MIT-blue.svg)](LICENSE)
[![Демо сайта](https://img.shields.io/badge/Демо-сайт-brightgreen)](http://46.19.68.158/)

Сервис заказа тортов на Django. Командный проект.

Пользователь собирает торт в конструкторе или выбирает готовый из каталога. Затем указывает адрес и время доставки, применяет промокод и оплачивает заказ онлайн.

## Требования

- Python 3.12+

```bash
python --version
```

> В зависимости от операционной системы команда `python` может называться `python3` — используйте её и в остальных командах этого README.

## Возможности

- Конструктор торта: уровни, форма, топпинг, ягоды, декор, надпись
- Каталог готовых тортов с фото, ценой и весом
- Вход по номеру телефона через код из SMS
- Личный кабинет: история заказов и профиль
- Промокоды: скидка процентом или фиксированной суммой
- Срочный заказ: наценка +20% (доставка раньше чем через сутки)
- Оплата картой онлайн или наличными
- История заказа: статусы, оплата, жалобы, комментарии

## Как запустить проект локально

- Клонируйте репозиторий и перейдите в папку проекта:

  ```bash
  git clone https://github.com/Skip-Bug/Django-Cakes.git
  cd Django-Cakes
  ```

- Создайте и активируйте виртуальное окружение:

  ```bash
  python -m venv .venv
  # Windows
  .venv\Scripts\activate
  # Linux/Mac
  source .venv/bin/activate
  ```

- Установите зависимости:

  ```bash
  pip install -r requirements.txt
  ```

- Создайте файл `.env` в корне проекта и заполните его:

  ```
  # Обязательно
  SECRET_KEY=ваш-секретный-ключ

  # Необязательно
  DEBUG=True
  ALLOWED_HOSTS=127.0.0.1,localhost
  JIVOSITE_WIDGET_ID=
  SMSRU_API_ID=
  SMSRU_FROM=
  SMSRU_TIMEOUT=10
  OTP_LOG_TO_CONSOLE=
  OTP_DEMO_MODE=False
  ```

  Где взять ключи:
  - `SMSRU_API_ID` — ключ API в личном кабинете [SMS.ru](https://sms.ru/);
  - `JIVOSITE_WIDGET_ID` — id виджета онлайн-чата [JivoSite](https://www.jivo.ru/).

  Файл `.env` **не коммитится** в Git — он уже добавлен в `.gitignore`.

- Примените миграции:

  ```bash
  python manage.py migrate
  ```

- Заполните базу демо-данными (две команды):

  ```bash
  # части и варианты конструктора торта
  python manage.py demo_part
  # готовые торты каталога
  python manage.py demo_ready_cake
  ```

- Создайте суперпользователя для доступа в админку:

  ```bash
  python manage.py createsuperuser
  ```

- Запустите сервер разработки:

  ```bash
  python manage.py runserver
  ```

Сайт будет доступен по адресу http://127.0.0.1:8000/, админка - http://127.0.0.1:8000/admin/.

> Коды подтверждения отправляются через SMS.ru, если задан `SMSRU_API_ID`. Без него (или в демо-режиме `OTP_DEMO_MODE`) код печатается в консоль сервера.

## База данных

Проект использует SQLite — файл `db.sqlite3` создаётся автоматически при первом запуске `python manage.py migrate`. База не коммитится в Git (добавлена в `.gitignore`).

## Линтинг

Код проверяется линтером [ruff](https://docs.astral.sh/ruff/) (настройки в `pyproject.toml`). Та же проверка запускается в CI (`.github/workflows/ruff.yml`).

```bash
ruff check .
ruff format .
```

Через pre-commit (проверка перед каждым коммитом):

```bash
pre-commit install
pre-commit run --all-files
```

## Структура проекта

- `config/` — настройки и корневые URL проекта
- `apps/accounts/` — пользователь, вход по телефону и одноразовые коды (OTP)
- `apps/custom_cake/` — конструктор торта: части и варианты
- `apps/ready_cake/` — каталог готовых тортов
- `apps/orders/` — оформление заказов, промокоды, оплата и история
- `templates/`, `static/`, `media/` — шаблоны, статика и загруженные файлы

## Зависимости проекта

Все зависимости зафиксированы в `requirements.txt`:

| Пакет                    | Версия | Назначение                                                             |
| ------------------------ | ------ | ---------------------------------------------------------------------- |
| Django                   | 6.1.1  | основной веб-фреймворк                                                 |
| environs                 | 15.2.0 | чтение переменных окружения из `.env` (SECRET_KEY и т.д.)              |
| Pillow                   | 12.3.0 | работа с изображениями, требуется для полей `ImageField` (фото тортов) |
| django-phonenumber-field | 8.5.\* | хранение и валидация номера телефона пользователя                      |
| ruff                     | 0.16.9 | линтер и форматтер кода                                                |
| pre-commit               | 4.6.2  | git-хуки для авто-проверки кода перед коммитом                         |
