# API-сервис сокращения ссылок fastlink

## Функционал сервиса

Сервис позволяет заменить оригинальный URL короткой уникальной ссылкой, имеет функции управления кокроткими ссылками, поиска оригинального URL, вывода статистики использования коротких ссылок.
Скринкасты с демонстрацией работы:

[01](https://disk.yandex.ru/i/0KNqFsSbww-UPA)   
[02](https://disk.yandex.ru/i/eorWRw0Ux17j0Q)    
[03](https://disk.yandex.ru/i/eorWRw0Ux17j0Q)  


### Установка сервиса 

установка:  
`docker-compose up --build`

### Структура проекта:
fastlinks/
```
│── .env                        # переменные окружения (пароли/пути)
│── .gitignore                  # игнорируемые файлы для Git
│── alembic.ini                 # конфигурация Alembic для миграций
│── cache.py                    # функции для работы с кэшем (Redis)
│── config.py                   # конфигурации, подгружаются из  .env
│── docker-compose.yml          # файл для управления контейнерами
│── Dockerfile                  # файл для создания образа Docker
│── main.py                     # запуск приложения
│── requirements.txt            # зависимости
│── migrations/                 # миграции Alembic
│   ├── versions/               # версии миграций
│── models/                     
│   ├── models.py               # инициализация моделей
│── routers/                    
│   ├── auth_routes.py          # эндпоинты для аутентификации
│   ├── links.py                # эндпоинты для управления ссылками
│── services.py                 # вспомогательные функции для реализации работы эндпоинтов
│── auth/                       
│   ├── db.py                   # подключение к базе данных
│   ├── schemas.py              # pydantic схемы для валидации данных
│   ├── users.py                # аутентикация пользователей
```
### Окружение
- python 3.9  
- PostgreSQL17  
- Redis  7.2.7
- FasAPI
- sqlalchemy  
- Alembic
- Pydantic


### Доступные эндпоинты:  

Эндпоинты аутентификации (Auth) (стандартные из библиотеки `fastapi-users`)
```
    POST /auth/jwt/login: Выполняет аутентификацию пользователя и выдает JWT токен.
    POST /auth/jwt/logout: Завершает сеанс пользователя и аннулирует JWT токен.
    POST /auth/register: Регистрирует нового пользователя.
    POST /auth/forgot-password: Запрашивает сброс пароля.
    POST /auth/reset-password: Сбрасывает пароль пользователя.
    POST /auth/request-verify-token: Запрашивает токен для верификации.
    POST /auth/verify: Верифицирует пользователя по токену.
```
Эндпоинты для проверки аутентифицирован ли пользователь (default) 
```
    GET /protected-route: Возвращает имя авторизованного пользователя.
    GET /unprotected-route: Доступен для всех пользователей
```
Эндпоинты управления ссылками (Links)
```
    POST /links/shorten: Создает короткую ссылку для оригинального URL
    GET /links/{short_code}: Перенаправляет на оригинальный URL по указанной короткой ссылке
    DELETE /links/{short_code}: Удаляет короткую ссылку
    PUT /links/{short_code}: Обновляет существующую короткую ссылку. Этот эндпоинт генерирует новую короткую ссылку для оригинального URL
    GET /links/{short_code}/stats: Показывает сколько раз кликали на короткую ссылку и время последнего клика
    POST /links/shorten/custom: Позволяет задать кастомный алиас для ссылки и изменить время жизни существующей ссылки
    GET /links/search: Ищет короткую ссылку по указанному оригинальному URL
````

### Описание структры БД:

содержит две основные таблицы:
1. user
```
    id = Column(UUID, primary_key=True, index=True)  # Уникальный идентификатор пользователя
    email = Column(String, unique=True, nullable=False)  # Уникальный адрес электронной почты
    username = Column(String, unique=True, nullable=False)  # Уникальное имя пользователя
    hashed_password = Column(String, nullable=False)  # Хешированный пароль пользователя
    registered_at = Column(DateTime(timezone=True), default=func.now())  # Дата регистрации
    is_active = Column(Boolean, default=True, nullable=False)  # Активен ли пользователь
    is_superuser = Column(Boolean, default=False, nullable=False)  # Является ли пользователь суперпользователем
    is_verified = Column(Boolean, default=False, nullable=False)  # Подтвержден ли адрес электронной почты
    links = relationship("Link", back_populates="user", cascade="all, delete-orphan")  # Связь с таблицей links

```


2. links
```
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))  # Уникальный идентификатор ссылки
    original_url = Column(String, nullable=False)  # Оригинальный URL, который сокращается
    short_code = Column(String, unique=True, nullable=False)  # Уникальный короткий код для ссылки
    custom_alias = Column(String, unique=True, nullable=True)  # Алиас для ссылки
    clicks = Column(Integer, default=0)  # Количество кликов/переходов по короткой ссылке
    created_at = Column(DateTime(timezone=True), default=func.now())  # Дата создания ссылки
    last_accessed = Column(DateTime(timezone=True), nullable=True)  # Дата последнего перехода по ссылке
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Дата истечения срока действия ссылки
    user_id = Column(UUID, ForeignKey("user.id"), nullable=True)  # Идентификатор пользователя, создавшего ссылку
    user = relationship("User", back_populates="links")  # Связь с таблицей пользователей links
```

Локальный деплой

﻿<img width="2135" alt="image" src="https://github.com/user-attachments/assets/67b6be8a-c6cf-4ad6-acfe-1bb461340808" />


