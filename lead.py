import json
import yaml
import time
import argparse
from itertools import islice
from typing import List, Dict
from openai import OpenAI


def load_yaml(file_path: str) -> Dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def batched(iterable: List, n: int):
    it = iter(iterable)
    while chunk := list(islice(it, n)):
        yield chunk


def find_leads(messages: List[Dict], client: OpenAI, model: str, prompt_template: str, batch_size: int) -> List[Dict]:
    all_leads = []

    for batch_num, batch in enumerate(batched(messages, batch_size), 1):
        print(f"Батч {batch_num} ({len(batch)} сообщений)")

        batch_payload = []
        text_to_meta = {}

        for msg in batch:
            text = msg.get('text') or msg.get('message') or msg.get('content') or ""
            if not text.strip():
                continue

            payload_item = {
                "text": text,
                "link": msg.get("link", "")
            }
            batch_payload.append(payload_item)

            # сохраняем дату для последующего сопоставления
            text_to_meta[text] = {
                "date": msg.get("date"),
                "link": msg.get("link")
            }

        if not batch_payload:
            continue

        full_prompt = prompt_template + "\n" + json.dumps(batch_payload, ensure_ascii=False, indent=2)

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Отвечай только валидным JSON-массивом."},
                    {"role": "user", "content": full_prompt}
                ]
            )

            leads = json.loads(response.choices[0].message.content)

            if not isinstance(leads, list):
                raise ValueError("Модель вернула не массив")

            print(f"  Найдено лидов: {len(leads)}")

            for lead in leads:
                original_text = lead.get("text", "")
                meta = text_to_meta.get(original_text, {})

                lead["date"] = meta.get("date")
                lead["link"] = meta.get("link")  # гарантируем оригинальный линк

                all_leads.append(lead)

        except Exception as e:
            print(f"  Ошибка батча: {e}")

        time.sleep(0.6)

    return all_leads


def main():
    parser = argparse.ArgumentParser(description='Поиск потенциальных лидов в сообщениях')
    parser.add_argument('-o', '--output', default='messages.json')
    parser.add_argument('-n', '--n', type=int, default=10)
    parser.add_argument('--leads', default='leads_only.json')
    parser.add_argument('--model', default='')
    args = parser.parse_args()

    cred = load_yaml('gpt_cred.yaml')
    api_key = cred.get('api_key') or cred.get('openai', {}).get('api_key')
    ai_model = args.model or cred.get('model')

    if not api_key:
        raise ValueError("API ключ не найден")
    if not ai_model:
        raise ValueError("Модель не указана")

    client = OpenAI(api_key=api_key)

    prompt_template = load_yaml('prompt.yaml').get('prompt')
    if not prompt_template:
        raise ValueError("Промпт не найден")

    with open(args.json, 'r', encoding='utf-8') as f:
        messages: List[Dict] = json.load(f)

    print(f"Загружено {len(messages)} сообщений. Батч размером {args.n}")
    print(f"Модель: {ai_model}\n")

    all_leads = find_leads(messages, client, ai_model, prompt_template, args.n)

    with open(args.leads, 'w', encoding='utf-8') as f:
        json.dump(all_leads, f, ensure_ascii=False, indent=2)

    print(f"\nГотово. Найдено лидов: {len(all_leads)}")
    print(f"Файл лидов: {args.leads}")


if __name__ == "__main__":
    main()
