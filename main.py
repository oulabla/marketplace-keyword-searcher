import vk_api
from vk_api.exceptions import ApiError
import time
import json
import os
from datetime import datetime
import argparse
import sys


# Токен с правами: groups, wall, offline
TOKEN_FILE = "vk_token.txt"
MAX_GROUPS = 2
POSTS_PER_GROUPS = 1
# KEYWORDS = ['битрикс', 'bitrix', '1с-битрикс', '1c-bitrix', 'битрикс24', 'bitrix24', 'б24']

def get_token(show_text=True):
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            token = f.read().strip()
        if token:
            if show_text:
                print(f"Токен загружен из файла {TOKEN_FILE}")
            return token

    token = input("Введите токен ВКонтакте: ").strip()
    if not token:
        print("Токен не может быть пустым")
        sys.exit(1)

    save = input("Сохранить токен в файл для следующих запусков? (y/n): ").lower()
    if save in ('y', 'yes'):
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(token)
        print(f"Токен сохранён в {TOKEN_FILE}")

    return token

def search_groups(vk, query, count=100):
    """Поиск сообществ по ключевому слову"""
    try:
        groups = vk.groups.search(q=query, count=count, sort=6)  # sort=6 по релевантности
        return [group['id'] for group in groups['items']]
    except ApiError as e:
        print(f"Ошибка поиска групп: {e}")
        return []


def search_in_group_wall(vk, group_id, query, count=100, show_text=True):
    """Поиск постов в стене сообщества"""
    found = []
    try:
        posts = vk.wall.search(owner_id=-group_id, query=query, count=count)
        for post in posts['items']:
            text = post.get('text', '')
            date = time.strftime('%d.%m.%Y %H:%M', time.localtime(post['date']))
            found.append({
                'group_id': group_id,
                'post_id': post['id'],
                'date': date,
                'text': text[:300] + ('...' if len(text) > 300 else ''),
                'link': f"https://vk.com/wall-{group_id}_{post['id']}"
            })
    except ApiError as e:
        if e.code != 15:
            if show_text:# 15 - доступ запрещен, пропускаем закрытые группы
                print(f"Ошибка в группе {group_id}: {e}")
    return found


def global_search_in_communities(vk, keywords, max_groups=MAX_GROUPS, posts_per_group=POSTS_PER_GROUPS, show_text=True, filename='bitrix_vk_search_results.json'):
    all_found = []

    for kw in keywords:
        if show_text:
            print(f"\nПоиск сообществ по '{kw}'...")
        group_ids = search_groups(vk, kw, count=max_groups)
        if show_text:
            print(f"Найдено сообществ: {len(group_ids)}")

        for gid in group_ids:
            if show_text:
                print(f"  Проверяю группу {gid}...")
            results = search_in_group_wall(vk, gid, kw, count=posts_per_group, show_text=show_text)
            if results:
                all_found.extend(results)
            time.sleep(0.35)  # лимит API

    all_found.sort(key=lambda p: datetime.strptime(p["date"], "%d.%m.%Y %H:%M"), reverse=True)

    # Сохраняем в файл для удобства
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_found, f, ensure_ascii=False, indent=2)

    return all_found


def print_human_readable(results):
    if not results:
        print("\nНичего не найдено.")
        return

    print(f"\nНайдено постов: {len(results)}")
    print("=" * 80)

    for r in results[:60]:
        print(f"\n{r['date']}   |   {r['link']}")
        print(f"Группа: {r['group_id']}")
        print(r['text'])
        print("-" * 80)

    if len(results) > 60:
        print(f"\n... ещё {len(results)-60} постов в файле vk_search_results.json")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Поиск постов ВКонтакте по ключевым словам в публичных сообществах",
        add_help=False,  # отключаем стандартный --help, чтобы сделать свой красивый
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        'keywords',
        nargs='?',
        default="битрикс,bitrix,1с-битрикс,битрикс24,б24",
        help="Ключевые слова через запятую (без пробелов вокруг запятой)\nПример: фриланс,удалёнка,python"
    )

    parser.add_argument(
        '--max-groups', '-g',
        type=int,
        default=3,
        help="Макс. количество групп на одно ключевое слово (по умолчанию: 3)"
    )

    parser.add_argument(
        '--posts-per-group', '-p',
        type=int,
        default=5,
        help="Сколько последних постов проверять в каждой группе (по умолчанию: 5)"
    )

    parser.add_argument(
        '--help', '-h',
        action='store_true',
        help="Показать эту справку и выйти"
    )

    parser.add_argument(
        '-j', '--json',
        action='store_true',
        help="Вывести только JSON в stdout (без лишнего текста)"
    )

    parser.add_argument(
        '-o', '--output',
        help="Путь к файлу для сохранения результата (UTF-8 JSON)"
    )

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    if args.help:
        print("""
    Поиск постов ВКонтакте по ключевым словам
    -----------------------------------------

    Примеры использования:

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
      -0, --output          Задать имя файла для сохранения
    """)
        sys.exit(0)

    # Парсим ключевые слова
    keywords = [kw.strip() for kw in args.keywords.split(',') if kw.strip()]

    if not keywords:
        print("Ошибка: не указано ни одного ключевого слова")
        sys.exit(1)

    if args.json is False:
        print(f"Ключевые слова: {', '.join(keywords)}")
        print(f"Групп на слово: {args.max_groups} | Постов в группе: {args.posts_per_group}\n")

    filename = 'bitrix_vk_search_results.json'
    if len(args.output) > 0:
        filename = args.output

    token = get_token(args.json is False)
    vk_session = vk_api.VkApi(token=token)
    vk = vk_session.get_api()

    results = global_search_in_communities(
        vk,
        keywords=keywords,
        max_groups=args.max_groups,
        posts_per_group=args.posts_per_group,
        show_text=args.json is False,
        filename=filename,
    )

    if args.json:
        # Только чистый JSON → ничего больше не печатаем
        json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
    else:
        # Человеческий вывод
        print(f"Ключевые слова: {', '.join(keywords)}")
        print(f"Групп на слово: {args.max_groups} | Постов в группе: {args.posts_per_group}\n")
        print_human_readable(results)