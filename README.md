# GigaChat API — FastAPI Service

Сервис для взаимодействия с нейросетью GigaChat через REST API.

## endpoints

| Method | Path            | Description                                  |
|--------|-----------------|----------------------------------------------|
| GET    | `/health`       | Проверка статуса сервиса                     |
| POST   | `/question`     | Отправить вопрос GigaChat                    |
| POST   | `/extract-pdf`  | Загрузить PDF/DOCX-документ и вернуть JSON-ответ |

## Быстрый старт

```bash
# 1. Создай виртуальное окружение
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / macOS

# 2. Установи зависимости
pip install -r requirements.txt

# 3. Скопируй .env → .env и заполни свои credentials
copy .env .env       # Windows
cp .env .env         # Linux / macOS

# 4. Запусти сервер
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Примеры запросов

### Health check
```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

### Отправить вопрос
```bash
curl -X POST http://localhost:8000/question \
  -H "Content-Type: application/json" \
  -d '{"message":"Привет, как дела?"}'
# {"message":"Привет! Я GigaChat — искусственный интеллект..."}
```

### Загрузить документ и запросить извлечение JSON
```bash
curl -X POST http://localhost:8000/extract-pdf \
  -F "file=@Dogovor.pdf;type=application/pdf"
```

Ответ содержит категории (как и раньше) плюс `regions` — координаты каждого
найденного значения на странице PDF (в points, 1/72 дюйма, начало координат
в левом верхнем углу страницы — как в PyMuPDF/pdf.js):

```json
{
  "categories": {
    "ФИО директора, подписантов и ответственных сотрудников": ["Иванов И.И."],
    "ИНН, КПП и идентификационный код заказчика": ["7701234567"]
  },
  "regions": [
    {
      "category": "ФИО директора, подписантов и ответственных сотрудников",
      "value": "Иванов И.И.",
      "page": 1,
      "x": 120.5,
      "y": 340.2,
      "width": 78.4,
      "height": 11.2
    },
    {
      "category": "ИНН, КПП и идентификационный код заказчика",
      "value": "7701234567",
      "page": 1,
      "x": 200.0,
      "y": 410.8,
      "width": 62.1,
      "height": 11.2
    }
  ]
}
```

`regions` рассчитывается **не самим GigaChat** (у него нет доступа к
разметке PDF), а локально: сервер повторно открывает загруженный PDF через
PyMuPDF и ищет на странице точное вхождение каждого значения, которое
GigaChat уже нашёл в тексте. Поэтому:
- работает только для `.pdf` (у `.docx` нет фиксированной геометрии страниц — для него `regions` всегда `[]`);
- для сканов/PDF без текстового слоя `regions` тоже будет пустым (нет текста для поиска — в таком случае имеет смысл сначала прогнать OCR);
- если GigaChat слегка изменил словоформу значения, оно может не найтись точным поиском и просто не попадёт в `regions` (при этом в `categories` останется).

Word документ тоже поддерживается через тот же маршрут (только без `regions`):
```bash
curl -X POST http://localhost:8000/extract-pdf \
  -F "file=@Dogovor.docx;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document"
# {"categories":{...}, "regions":[]}
```

## Переменные окружения

| Переменная             | Описание                              | По умолчанию                     |
|------------------------|---------------------------------------|----------------------------------|
| `GIGACHAT_CLIENT_ID`   | ID клиента из кабинета разработчика   | (обязательно)                    |
| `GIGACHAT_CLIENT_SECRET`| Секретный ключ клиента               | (обязательно)                    |
| `GIGACHAT_SCOPE`       | OAuth scope                           | `GIGACHAT_API_PERS`              |
| `HOST`                 | Адрес привязки сервера                | `0.0.0.0`                        |
| `PORT`                 | Порт сервера                          | `8000`                           |

## Получить credentials

1. Зарегистрируйся на [developers.sber.ru](https://developers.sber.ru/gigachat)
2. Создай приложение в разделе **API**
3. Скопируй `client_id` и `client_secret` в `.env`
