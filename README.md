# 🤖 GigaChat API — FastAPI Service

Лёгкий REST-сервис на **FastAPI**, который проксирует запросы к нейросети
**GigaChat** (Сбер) и умеет извлекать структурированные данные из
загруженных PDF/DOCX-документов — с автоматическим fallback на локальный
парсер, если GigaChat недоступен.

<p>
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.115%2B-009688">
  
</p>

\---

## 📑 Содержание

* [Возможности](#-возможности)
* [Архитектура](#-архитектура)
* [Структура проекта](#-структура-проекта)
* [Быстрый старт](#-быстрый-старт)
* [Переменные окружения](#-переменные-окружения)
* [API](#-api)

  * [GET /health](#get-health)
  * [POST /question](#post-question)
  * [POST /extract-pdf](#post-extract-pdf)
* [Формат ответа /extract-pdf](#-формат-ответа-extract-pdf)
* [Как получить credentials GigaChat](#-как-получить-credentials-gigachat)
* [Разработка](#-разработка)

\---

## ✨ Возможности

* 💬 **Чат с GigaChat** — прямой проксирующий эндпоинт `/question`.
* 📄 **Извлечение данных из документов** — загрузка PDF/DOCX и получение
строго структурированного JSON по фиксированному набору категорий
(реквизиты, ФИО, ИНН, банковские данные и т.д.).
* 📊 **Аналитика по договору** — отдельный блок с дословными цитатами
по условиям оплаты, расторжению, гарантии, приёмке и упоминаниям
223-ФЗ / 44-ФЗ / 275-ФЗ.
* 📍 **Координаты на странице** — для PDF сервис возвращает `regions`:
bounding box каждого найденного значения (через PyMuPDF), удобно для
визуальной подсветки/редактирования в PDF-вьюере.
* 🛟 **Локальный fallback** — если GigaChat недоступен или вернул
неожиданный ответ, включается regex-эвристика, которая всё равно
наполняет ответ (сервис никогда не падает в пустой JSON).
* 🔐 **OAuth-кэширование токена** — токен GigaChat запрашивается один раз
и переиспользуется до истечения срока действия.

## 🏗 Архитектура

```
Клиент
  │
  │  POST /extract-pdf (файл)
  ▼
FastAPI router (routes/router.py)
  │
  ├─► services/gigachat.py ─── извлечение текста (pypdf / docx)
  │         │
  │         ├─► GigaChat API (OAuth + chat/completions)
  │         │        │
  │         │        └─ при ошибке ─► local\_llm/example\_llm.py (fallback)
  │         │
  │         └─► PyMuPDF ─── поиск координат значений на странице
  │
  └─► schemas/request.py ─── валидация запроса/ответа (Pydantic)
```

## 📂 Структура проекта

```
.
├── main.py                 # Точка входа: создаёт FastAPI-приложение
├── config.py                # Настройки из .env (pydantic-settings)
├── routes/
│   └── router.py            # /health, /question, /extract-pdf
├── services/
│   └── gigachat.py           # Клиент GigaChat + извлечение категорий
├── schemas/
│   └── request.py            # Pydantic-модели запросов/ответов
├── local\_llm/
│   └── example\_llm.py        # Заглушка локальной модели (fallback)
├── requirements.txt
└── pyproject.toml
```

## 🚀 Быстрый старт

```bash
# 1. Создать виртуальное окружение
python -m venv venv
venv\\Scripts\\activate        # Windows
source venv/bin/activate     # Linux / macOS

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Настроить переменные окружения
cp .env.example .env         # Linux / macOS
copy .env.example .env       # Windows
# затем впишите свои GIGACHAT\_CLIENT\_ID / GIGACHAT\_CLIENT\_SECRET

# 4. Запустить сервер
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

После запуска интерактивная документация доступна на:
**http://localhost:8000/docs** (Swagger UI).

> ⚠️ \*\*Важно:\*\* не храните реальные `client\_id` / `client\_secret` как
> значения по умолчанию в `config.py` — используйте только `.env`,
> который не должен попадать в git (см. `.gitignore`).

## ⚙️ Переменные окружения

|Переменная|Описание|По умолчанию|
|-|-|-|
|`GIGACHAT\_CLIENT\_ID`|ID клиента из кабинета разработчика|*(обязательно)*|
|`GIGACHAT\_CLIENT\_SECRET`|Секретный ключ клиента|*(обязательно)*|
|`GIGACHAT\_SCOPE`|OAuth scope|`GIGACHAT\_API\_PERS`|
|`HOST`|Адрес привязки сервера|`0.0.0.0`|
|`PORT`|Порт сервера|`8000`|

## 📡 API

### `GET /health`

Проверка живости сервиса.

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok"}
```

### `POST /question`

Отправить произвольный текст в GigaChat и получить ответ. При ошибке
GigaChat автоматически используется локальный fallback (`local\_llm`).

```bash
curl -X POST http://localhost:8000/question \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Привет, как дела?"}'
```

```json
{"message": "Привет! Я GigaChat — искусственный интеллект..."}
```

### `POST /extract-pdf`

Загрузить PDF или DOCX и получить структурированные категории +
аналитику + координаты значений на странице.

```bash
curl -X POST http://localhost:8000/extract-pdf \\
  -F "file=@Dogovor.pdf;type=application/pdf"
```

DOCX поддерживается тем же маршрутом (без `regions`, т.к. у формата нет
фиксированной геометрии страниц):

```bash
curl -X POST http://localhost:8000/extract-pdf \\
  -F "file=@Dogovor.docx;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document"
```

## 📦 Формат ответа `/extract-pdf`

```json
{
  "categories": {
    "ФИО директора, подписантов и ответственных сотрудников": \["Иванов И.И."],
    "ИНН, КПП и идентификационный код заказчика": \["7701234567"]
  },
  "analytics": {
    "Условия оплаты: аванс, процент, сумма, сроки перечисления": \[
      "Покупатель обязуется перечислить аванс в размере 30% в течение 5 рабочих дней."
    ]
  },
  "regions": \[
    {
      "category": "ФИО директора, подписантов и ответственных сотрудников",
      "value": "Иванов И.И.",
      "page": 1,
      "x": 120.5,
      "y": 340.2,
      "width": 78.4,
      "height": 11.2
    }
  ]
}
```

**Поля:**

|Поле|Описание|
|-|-|
|`categories`|Отдельные реквизиты/значения по фиксированному списку категорий|
|`analytics`|Дословные цитаты по условиям оплаты, расторжению, гарантии, приёмке, 223-ФЗ/44-ФЗ/275-ФЗ|
|`regions`|Координаты (в points, top-left origin) каждого найденного значения на странице PDF|

**Особенности `regions`:**

* рассчитывается **не GigaChat**, а локально — сервер повторно открывает
PDF через PyMuPDF и ищет точное вхождение каждого значения;
* работает только для `.pdf` — для `.docx` всегда `\[]`;
* для сканов без текстового слоя тоже будет `\[]` (нужен OCR заранее);
* если GigaChat немного изменил словоформу значения, оно может не найтись
точным поиском и просто не попадёт в `regions` (при этом останется в `categories`).

