# GigaChat API — FastAPI Service

Сервис для взаимодействия с нейросетью GigaChat через REST API.

## endpoints

| Method | Path        | Description               |
|--------|-------------|---------------------------|
| GET    | `/health`   | Проверка статуса сервиса  |
| POST   | `/question` | Отправить вопрос GigaChat |

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
