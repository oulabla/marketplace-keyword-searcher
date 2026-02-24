# VK Lead Searcher

Поиск потенциальных лидов ВКонтакте по ключевым словам в публичных сообществах.

Скрипт ищет посты по заданным ключевым словам → выводит результаты → (опционально) пропускает через модель OpenAI для выделения качественных «тёплых» лидов.

Подходит для мониторинга заказов, фриланс-запросов, заявок на услуги, упоминаний продуктов и т.п.  
Примеры запросов: «нужен битрикс», «ищу 1С программиста», «продам USDT», «удалёнка python», «крипта TON».

## Возможности

- Поиск релевантных сообществ по ключевым словам
- Поиск постов на стенах найденных групп
- Сортировка результатов от новых к старым
- Человеческий вывод или чистый JSON
- Опциональная фильтрация через OpenAI (ChatGPT / другие модели)
- Сохранение токена ВКонтакте в файл
- Логирование каждого запуска в `log/log_ГГГГ-ММ-ДД.jsonl` (JSON Lines)
- Полная обработка ошибок с записью в лог (traceback + сообщение)

## Требования

- Python 3.8 – 3.12 (рекомендуется 3.11 или 3.12)
- Библиотеки: `vk-api`, `openai` (если используете ИИ-фильтр)

## Получение токена ВКонтакте

1. Создайте **standalone-приложение** → https://vk.com/apps?act=manage
2. Сформируйте ссылку для Implicit Flow:
https://oauth.vk.com/authorize?client_id=YOUR_APP_ID&scope=groups,wall,offline&redirect_uri=https://oauth.vk.com/blank.html&response_type=token
text3. После авторизации скопируйте `access_token=...` из адресной строки браузера
4. Сохраните токен:
- Создайте файл `vk_token.txt` рядом со скриптом
- Или введите при первом запуске (скрипт предложит сохранить)

**Важно**: токен **не коммитьте** в git!

## Установка и первый запуск (Windows)

```bash
# 1. Установите Python (если ещё нет) → https://www.python.org/downloads/
# 2. Установите Git → https://git-scm.com/download/win

git clone https://github.com/ВАШ_ЛОГИН/marketplace-keyword-searcher.git
# или если репозиторий приватный — используйте SSH или Personal Access Token

cd marketplace-keyword-searcher

python -m venv venv

# Активация (cmd)
venv\Scripts\activate

# Активация (PowerShell — может потребоваться Set-ExecutionPolicy RemoteSigned)
.\venv\Scripts\Activate.ps1

# Установка зависимостей
pip install -r requirements.txt
# или вручную:
# pip install vk-api openai pyyaml

# Первый запуск (попросит токен)
python main.py
Повторный запуск
Bashcd marketplace-keyword-searcher
venv\Scripts\activate      # или .\venv\Scripts\Activate.ps1
python main.py
Примеры запуска
Bash# По умолчанию — битрикс, 3 группы × 5 постов
python main.py

# Крипта — больше охвата
python main.py "крипта,btc,bitcoin,usdt,ton,toncoin" -g 15 -p 40

# Только JSON (удобно для скриптов / пайплайнов)
python main.py "удалёнка python django" -j

# С фильтром через OpenAI (батч 10 постов)
python main.py "нужен битрикс,заказ битрикс24,ищу разработчика битрикс" -g 8 -p 25 -a 10

# Свои имена файлов + большой батч
python main.py фриланс,заказ,удаленка,python -o leads_2026-02.json -i temp_vk.json -a 20

# Справка
python main.py --help
Аргументы командной строки
textkeywords              Ключевые слова через запятую (по умолчанию: битрикс,bitrix,1с-битрикс,битрикс24,б24)

-g, --max-groups      Макс. групп на каждое ключевое слово     (по умолчанию: 3)
-p, --posts-per-group Сколько последних постов проверять в группе (по умолчанию: 5)

-j, --json            Выводить только чистый JSON в stdout
-a, --ai N            Включить фильтр OpenAI, обрабатывать батчами по N постов (0 = выключено)

-o, --output FILE     Имя файла с финальным результатом       (по умолчанию: result.json)
-i, --intermediate FILE  Промежуточный файл до ИИ-обработки (по умолчанию: vk_result.json)

--help, -h            Показать эту справку
Структура проекта
textmarketplace-keyword-searcher/
├── main.py               ← основной скрипт
├── lead.py               ← логика работы с OpenAI + загрузка промпта и ключей
├── prompt.yaml           ← шаблон промпта для модели
├── gpt_cred.yaml         ← ваши OpenAI credentials (api_key, model)
├── vk_token.txt          ← токен ВКонтакте (не коммитить!)
├── requirements.txt      ← зависимости
├── log/                  ← создаётся автоматически
│   └── log_2026-02-24.jsonl   ← построчный JSON-лог запусков
└── README.md
```

## Логи
Каждый запуск записывается одной строкой в файл log/log_ГГГГ-ММ-ДД.jsonl
Содержит:

timestamp, end_time, duration_seconds
keywords
параметры (ai_filter, max_groups, posts_per_group, batch_size_ai)
num_posts_before_ai / num_leads_after_ai
error (если была) → сообщение + traceback

## Пример строки:
JSON{"timestamp":"2026-02-24T14:35:12.345","end_time":"2026-02-24T14:35:38.901","duration_seconds":26.56,"keywords":["битрикс","bitrix24"],"params":{"ai_filter":true,"max_groups":5,"posts_per_group":20,"batch_size_ai":10},"num_posts_before_ai":12,"num_leads_after_ai":4,"error":null}
Удобно смотреть:
Bashtype log\log_2026-02-24.jsonl    # Windows cmd
Get-Content log\log_2026-02-24.jsonl | Select-Object -Last 10   # PowerShell