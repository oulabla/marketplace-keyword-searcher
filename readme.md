# Инструкция с нуля для Windows
Устанавливем питон https://www.python.org/downloads/release/python-3142/

Устанавливем гит https://git-scm.com/install/windows
# Заходим в папку где будет проект там делаем
git clone https://github.com/oulabla/marketplace-keyword-searcher

cd marketplace-keyword-searcher

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

python main.py # он попросит токен для ВК надо отдать текст из файла vk_token который в телеге
 
--------------------------------


# VK Bitrix / Bitrix24 Search

Скрипт ищет упоминания слов «битрикс», «bitrix», «битрикс24», «б24» и их вариаций  
в постах на стенах **публичных сообществ** ВКонтакте.

Используемые методы VK API:
- `groups.search` — поиск релевантных сообществ  
- `wall.search` — поиск постов по ключевым словам в найденных группах

Результаты сохраняются в файл `bitrix_vk_search_results.json`

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