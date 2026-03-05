import vk_api
from vk_api.exceptions import ApiError
import time
import json
import os
from datetime import datetime
import argparse
import sys
import traceback
import uuid
import requests

import lead
from openai import OpenAI

# ────────────────────────────────────────────────
# Константы
# ────────────────────────────────────────────────

TOKEN_FILE = "vk_token.txt"
CLIENT_ID_FILE = "client_id.txt"
NETLOG_URL = "http://netlog.tw1.ru:8080/v1/netlog/create"
APP_NAME = "vk-lead-parser"           # ← можно поменять на своё

MAX_GROUPS = 2
POSTS_PER_GROUPS = 1
DEFAULT_INTERMEDIATE_FILENAME = "vk_result.json"
LOG_DIR = 'log'

# ────────────────────────────────────────────────
# Функции работы с client_id
# ────────────────────────────────────────────────

def get_or_create_client_id():
    if os.path.exists(CLIENT_ID_FILE):
        try:
            with open(CLIENT_ID_FILE, "r", encoding="utf-8") as f:
                cid = f.read().strip()
            if cid and len(cid) > 20:
                return cid
        except:
            pass

    new_id = str(uuid.uuid4())
    try:
        with open(CLIENT_ID_FILE, "w", encoding="utf-8") as f:
            f.write(new_id)
        print(f"Создан новый client_id → {new_id}")
    except Exception as e:
        print(f"Не удалось сохранить client_id: {e}", file=sys.stderr)

    return new_id


# ────────────────────────────────────────────────
# Отправка лога на сервер
# ────────────────────────────────────────────────

def send_netlog_to_server(
    client_id,
    keywords,
    parameters,
    num_before_ai,
    num_after_ai,
    error_msg=None,
    result_before=None,
    result_after=None
):
    payload = {
        "netlog": {
            "client_id": client_id,
            "app_name": APP_NAME,
            "keywords": keywords,
            "parameters": parameters,
            "num_before_ai_filter": num_before_ai,
            "num_after_ai_filter": num_after_ai,
        }
    }

    if error_msg:
        payload["netlog"]["error"] = error_msg

    if result_before:
        payload["netlog"]["result_before_ai_filter"] = result_before

    if result_after:
        payload["netlog"]["result"] = result_after
    print(payload)
    try:
        r = requests.post(
            NETLOG_URL,
            json=payload["netlog"],
            timeout=12,
            headers={"Content-Type": "application/json"}
        )
        r.raise_for_status()

        try:
            resp = r.json()
            netlog_id = resp.get("id")
            if netlog_id:
                print(f"Лог отправлен → netlog id = {netlog_id}")
            else:
                print("Лог отправлен, но id не вернулся")
        except:
            print("Лог отправлен, но ответ не JSON")

    except requests.RequestException as e:
        print(f"Ошибка отправки на {NETLOG_URL}: {e}", file=sys.stderr)


# ────────────────────────────────────────────────
# Остальные функции (без изменений)
# ────────────────────────────────────────────────

def get_token(show_text=True):
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            token = f.read().strip()
        if token:
            if show_text:
                print(f"Токен загружен из {TOKEN_FILE}")
            return token

    token = input("Введите токен ВКонтакте: ").strip()
    if not token:
        print("Токен не может быть пустым")
        sys.exit(1)

    save = input("Сохранить токен? (y/n): ").lower()
    if save in ('y', 'yes'):
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(token)
        print(f"Токен сохранён в {TOKEN_FILE}")

    return token


def search_groups(vk, query, count=100):
    try:
        groups = vk.groups.search(q=query, count=count, sort=6)
        return [group['id'] for group in groups['items']]
    except ApiError as e:
        print(f"Ошибка поиска групп: {e}")
        return []


def search_in_group_wall(vk, group_id, query, count=100, show_text=True):
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
        if e.code != 15 and show_text:
            print(f"Ошибка в группе {group_id}: {e}")
    return found


def global_search_in_communities(vk, keywords, max_groups=MAX_GROUPS, posts_per_group=POSTS_PER_GROUPS, show_text=True):
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
            time.sleep(0.35)

    all_found.sort(key=lambda p: datetime.strptime(p["date"], "%d.%m.%Y %H:%M"), reverse=True)
    return all_found


def print_human_readable(results):
    if not results:
        print("\nНичего не найдено.")
        return

    print(f"\nНайдено постов: {len(results)}")
    print("=" * 80)

    for r in results:
        print(f"\n{r['date']}   |   {r['link']}")
        print(f"Группа: {r['group_id']}")
        print(r['text'])
        print("-" * 80)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Поиск постов ВКонтакте по ключевым словам в публичных сообществах",
        add_help=False,
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        'keywords',
        nargs='?',
        default="битрикс,bitrix,1с-битрикс,битрикс24,б24",
        help="Ключевые слова через запятую\nПример: фриланс,удалёнка,python"
    )

    parser.add_argument('--max-groups', '-g', type=int, default=3)
    parser.add_argument('--posts-per-group', '-p', type=int, default=5)
    parser.add_argument('--help', '-h', action='store_true')
    parser.add_argument('-j', '--json', action='store_true')
    parser.add_argument('-a', '--ai', type=int, default=0)
    parser.add_argument('-o', '--output', default='result.json')
    parser.add_argument('-i', '--intermediate', default='vk_result.json')

    return parser.parse_args()


def safe_date_key(item):
    if item.get("date") is None:
        return datetime.min
    try:
        return datetime.strptime(item["date"], "%d.%m.%Y %H:%M")
    except:
        return datetime.min


def write_log(log_data):
    os.makedirs(LOG_DIR, exist_ok=True)
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(LOG_DIR, f'log_{today}.jsonl')

    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False)
            f.write('\n')
    except Exception as e:
        print(f"Ошибка записи лога {log_file}: {e}", file=sys.stderr)


# ────────────────────────────────────────────────
# Главный блок
# ────────────────────────────────────────────────

if __name__ == "__main__":
    error_info = None
    num_before_ai = 0
    num_after_ai = 0
    start_time = datetime.now().isoformat()
    results = []
    all_leads = []

    try:
        args = parse_args()

        if args.help:
            print("""
Поиск постов ВКонтакте по ключевым словам
-----------------------------------------

Примеры:
  python main.py
  python main.py "фриланс,удалёнка"
  python main.py битрикс -g 10 -p 20 -a 30
  python main.py --help
            """)
            sys.exit(0)

        keywords = [kw.strip() for kw in args.keywords.split(',') if kw.strip()]
        if not keywords:
            print("Ошибка: не указаны ключевые слова")
            sys.exit(1)

        client_id = get_or_create_client_id()

        if not args.json:
            print(f"Ключевые слова: {', '.join(keywords)}")
            print(f"Групп на слово: {args.max_groups} | Постов в группе: {args.posts_per_group}")
            print(f"client_id: {client_id}\n")

        token = get_token(not args.json)
        vk_session = vk_api.VkApi(token=token)
        vk = vk_session.get_api()

        results = global_search_in_communities(
            vk,
            keywords=keywords,
            max_groups=args.max_groups,
            posts_per_group=args.posts_per_group,
            show_text=not args.json
        )
        num_before_ai = len(results)

        if args.ai > 0:
            if not args.json:
                print_human_readable(results)

            vk_result_filename = args.intermediate or DEFAULT_INTERMEDIATE_FILENAME
            with open(vk_result_filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            api_key, ai_model = lead.get_gpt_cred()
            if not api_key or not ai_model:
                raise ValueError("Не удалось загрузить OpenAI credentials")

            client = OpenAI(api_key=api_key)
            prompt_template = lead.get_prompt_text()
            if not prompt_template:
                raise ValueError("Промпт не найден")

            if not args.json:
                print(f"Обработка через AI (батч {args.ai}, модель {ai_model})...")

            all_leads = lead.find_leads(results, client, ai_model, prompt_template, args.ai)
            all_leads.sort(key=safe_date_key, reverse=True)
            num_after_ai = len(all_leads)

            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(all_leads, f, ensure_ascii=False, indent=2)

        elif args.json:
            json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            num_after_ai = num_before_ai
        else:
            print_human_readable(results)
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            num_after_ai = num_before_ai

    except Exception as e:
        error_info = {
            'message': str(e),
            'traceback': traceback.format_exc()
        }
        num_after_ai = num_before_ai

    finally:
        # Локальный лог
        log_data = {
            'timestamp': start_time,
            'keywords': keywords if 'keywords' in locals() else [],
            'params': {
                'ai_filter': args.ai > 0 if 'args' in locals() else False,
                'max_groups': args.max_groups if 'args' in locals() else 0,
                'posts_per_group': args.posts_per_group if 'args' in locals() else 0
            },
            'num_before_ai': num_before_ai,
            'num_after_ai': num_after_ai,
            'error': error_info
        }
        write_log(log_data)

        # Отправка на сервер
        parameters = {
            'ai_batch_size': args.ai if 'args' in locals() else 0,
            'max_groups': args.max_groups if 'args' in locals() else 0,
            'posts_per_group': args.posts_per_group if 'args' in locals() else 0,
            'output_file': args.output if 'args' in locals() else None,
            'intermediate_file': args.intermediate if 'args' in locals() else None,
        }

        # Подготавливаем данные в ожидаемом формате (массив → объект с items)
        result_before_wrapped = None
        if num_before_ai > 0 and 'results' in locals() and isinstance(results, list):
            result_before_wrapped = {"items": results}

        result_after_wrapped = None
        if num_after_ai > 0 and 'all_leads' in locals() and isinstance(all_leads, list):
            result_after_wrapped = {"items": all_leads}

        send_netlog_to_server(
            client_id=client_id if 'client_id' in locals() else "unknown",
            keywords=keywords if 'keywords' in locals() else [],
            parameters=parameters,
            num_before_ai=num_before_ai,
            num_after_ai=num_after_ai,
            error_msg=error_info['message'] if error_info else None,
            result_before=result_before_wrapped,
            result_after=result_after_wrapped
        )

        if error_info:
            print(f"\nПроизошла ошибка:\n{error_info['message']}")
            print(error_info['traceback'])
            sys.exit(1)