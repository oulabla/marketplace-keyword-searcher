import vk_api
from vk_api.exceptions import ApiError
import time
import json
import os

# Токен с правами: groups, wall, offline
TOKEN_FILE = "vk_token.txt"
MAX_GROUPS = 100
POSTS_PER_GROUPS = 100
KEYWORDS = ['битрикс', 'bitrix', '1с-битрикс', '1c-bitrix', 'битрикс24', 'bitrix24', 'б24']

def get_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            token = f.read().strip()
        if token:
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


def search_groups(query, count=100):
    """Поиск сообществ по ключевому слову"""
    try:
        groups = vk.groups.search(q=query, count=count, sort=6)  # sort=6 по релевантности
        return [group['id'] for group in groups['items']]
    except ApiError as e:
        print(f"Ошибка поиска групп: {e}")
        return []


def search_in_group_wall(group_id, query, count=100):
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
        if e.code != 15:  # 15 - доступ запрещен, пропускаем закрытые группы
            print(f"Ошибка в группе {group_id}: {e}")
    return found


def global_search_in_communities(keywords, max_groups=MAX_GROUPS, posts_per_group=POSTS_PER_GROUPS):
    all_found = []

    for kw in keywords:
        print(f"\nПоиск сообществ по '{kw}'...")
        group_ids = search_groups(kw, count=max_groups)
        print(f"Найдено сообществ: {len(group_ids)}")

        for gid in group_ids:
            print(f"  Проверяю группу {gid}...")
            results = search_in_group_wall(gid, kw, count=posts_per_group)
            if results:
                all_found.extend(results)
            time.sleep(0.35)  # лимит API

    # Сохраняем в файл для удобства
    with open('bitrix_vk_search_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_found, f, ensure_ascii=False, indent=2)

    return all_found


def print_results(results):
    print(f"\n{'=' * 80}")
    print(f"Всего найдено постов: {len(results)}")
    for r in results[:50]:  # Показываем первые 50
        print(f"\nДата: {r['date']}")
        print(f"Группа: {r['group_id']}")
        print(f"Текст: {r['text']}")
        print(f"Ссылка: {r['link']}")
    if len(results) > 50:
        print(f"...и ещё {len(results) - 50} результатов в файле bitrix_vk_search_results.json")

if __name__ == "__main__":
    token = get_token()
    vk_session = vk_api.VkApi(token=token)
    vk = vk_session.get_api()

    results = global_search_in_communities(KEYWORDS)
    print_results(results)