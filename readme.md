### Инструкция с нуля для Windows
Устанавливем питон https://www.python.org/downloads/release/python-3142/

Устанавливем гит https://git-scm.com/install/windows
### Заходим в папку где будет проект там делаем
```bash
git clone https://github.com/oulabla/marketplace-keyword-searcher

cd marketplace-keyword-searcher

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

python main.py # он попросит токен для ВК надо отдать текст из файла vk_token который в телеге
````
### Для повторного запуска заходим в папку .../marketplace-keyword-searcher
```bash
venv\Scripts\activate

python main.py
```
--------------------------------


# VK Lead Searcher

Поиск потенциальных лидов ВКонтакте по ключевым словам в публичных сообществах.

Скрипт ищет посты по заданным ключевым словам → выводит результаты в удобном виде или в JSON → (опционально) пропускает их через ChatGPT/OpenAI для фильтрации качественных лидов.

Подходит для поиска заказов, фриланс-запросов, заявок на услуги, упоминаний конкретных продуктов и т.д. (например: «нужен битрикс», «ищу 1С программиста», «продам биткоин» и т.п.)

## Возможности

- Поиск групп по ключевым словам
- Поиск постов на стенах найденных сообществ
- Фильтрация по дате (сортировка от новых к старым)
- Вывод в человеческом виде или чистый JSON
- Опциональная обработка через OpenAI (ChatGPT) для выделения «тёплых» лидов
- Сохранение токена ВКонтакте в файл
- Аргументы командной строки для гибкой настройки

## Требования

- Python 3.8+
- Библиотека `vk-api`

## Получение токена

1. Создайте standalone-приложение: https://vk.com/apps?act=manage  
2. Сформируйте ссылку (замените `YOUR_APP_ID`):


3. После авторизации скопируйте `access_token=...` из адресной строки

4. Варианты сохранения токена:
- Создайте файл `vk_token.txt` рядом с `main.py` и вставьте туда токен  
- Или введите токен при первом запуске (скрипт предложит сохранить)


## Структура файлов
```
textvk-lead-searcher/
├── main.py               ← основной скрипт
├── lead.py               ← логика работы с OpenAI (фильтрация лидов)
├── prompt.yaml           ← шаблон промпта для GPT
├── gpt_cred.yaml         ← ваши OpenAI ключи (api_key и model)
└── vk_token.txt          ← будет создан автоматически (не коммитьте в git!)
Примеры запуска
Bash# Самый простой запуск (поиск по битриксу, 3 группы × 5 постов)
python main.py
Bash# Поиск по крипте, больше групп и постов
python main.py "крипта,btc,bitcoin,usdt,ton" -g 12 -p 30
Bash# Только JSON в консоль (удобно для пайплайнов)
python main.py "удалёнка python" -j
Bash# С обработкой через GPT (берёт по 8 постов за раз)
python main.py "нужен битрикс,заказ битрикс24" -g 5 -p 15 -a 8
Bash# Сохранение в конкретный файл
python main.py фриланс,заказ,удаленка -o leads_2026-02.json -a 10
```
## Установка и запуск (рекомендуется через venv)

```bash
# 1. Создаём виртуальное окружение
python -m venv venv

# 2. Активируем окружение

# Windows (cmd)
venv\Scripts\activate

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate

# 3. Устанавливаем зависимости

# Если есть requirements.txt (рекомендуемый способ)
pip install -r requirements.txt

# Или вручную
pip install vk-api

# Запуск скрипта
python main.py

python main.py "битрикс,bitrix,1с-битрикс,битрикс24,б24"
python main.py крипта,btc,bitcoin -g 10 -p 20
python main.py --help

Аргументы:

keywords              Ключевые слова через запятую (без кавычек, если нет пробелов)
                    По умолчанию: битрикс,bitrix,1с-битрикс,битрикс24,б24

-g, --max-groups      Макс. кол-во групп на каждое слово     (по умолчанию 3)
-p, --posts-per-group Кол-во последних постов в группе       (по умолчанию 5)
-j, --json            Только JSON в вывод
-h, --help            Показать эту справку