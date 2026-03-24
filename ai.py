import os
import re
import time
from mistralai import Mistral


api_key = os.getenv("SECRET_KEY")
client = Mistral(api_key=api_key)

books_folder = "files"


# =========================
# Безопасный запрос к API с retry
# =========================
def safe_chat(messages, retries=5):
    for attempt in range(retries):
        try:
            response = client.chat.complete(
                model="mistral-large-latest",
                messages=messages
            )
            return response
        except Exception as e:
            err_str = str(e)
            if "429" in err_str:
                time.sleep(5)
            elif "503" in err_str or "502" in err_str:
                time.sleep(3)
            else:
                raise e
    return None


# =========================
# Получаем книги по вопросу
# =========================
def get_titles_to_question(question, books_list):
    response = safe_chat([
        {
            "role": "system",
            "content": f"""
Есть список книг:

{books_list}

Определи к каким книгам относится вопрос.

Формат ответа строго:
[книга]
или
[книга1 | книга2]
или
"None" И НИЧЕГО БОЛЬШЕ
"""
        },
        {"role": "user", "content": question}
    ])
    if response is None:
        return "None"
    return response.choices[0].message.content.strip()


# =========================
# Ответ по книгам
# =========================
def get_answers(question, books_list):
    texts = []
    for file in os.listdir(books_folder):
        if file.endswith(".txt"):
            path = os.path.join(books_folder, file)
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()[:12000]
                texts.append(text)

    if not texts:
        return None

    books_text = "\n\n".join(texts)

    response = safe_chat([
        {
            "role": "system",
            "content": """
Ты анализируешь тексты книг.

Отвечай по сути и кратко.
Если книга не относится к вопросу — не упоминай её.
"""
        },
        {
            "role": "user",
            "content": f"""
Список книг:
{books_list}

Тексты книг:
{books_text}

Вопрос:
{question}
"""
        }
    ])
    if response is None:
        return None
    return response.choices[0].message.content.strip()


# =========================
# Поиск по файлам
# =========================
def ask_big_files(files, question):
    answers = []

    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()

        keywords = [w.lower() for w in re.findall(r"\w+", question) if len(w) > 3]
        paragraphs = text.split("\n")
        relevant = []

        for i, p in enumerate(paragraphs):
            p_lower = p.lower()
            if any(k in p_lower for k in keywords):
                start = max(0, i - 3)
                end = min(len(paragraphs), i + 3)
                relevant.append("\n".join(paragraphs[start:end]))

        if not relevant:
            continue

        context = "\n".join(relevant[:10])

        response = safe_chat([
            {"role": "system", "content": "Отвечай только по тексту, кратко и по сути."},
            {"role": "user", "content": f"Текст:\n{context}\n\nВопрос:\n{question}"}
        ])

        if response:
            answer_text = response.choices[0].message.content.strip()
            if answer_text and "нет информации" not in answer_text.lower():
                answers.append(answer_text)

    if not answers:
        return "В текстах нет информации по этому вопросу."

    return answers[0]


# =========================
# Все файлы книг
# =========================
def get_all_book_files():
    return [os.path.join(books_folder, f) for f in os.listdir(books_folder) if f.endswith(".txt")]


# =========================
# Главная функция
# =========================
def test_answer(question, titles_list):
    # Список книг для определения по названиям
    books_list = titles_list

    # 1️⃣ Пытаемся определить книги по названиям
    titles = get_titles_to_question(question, books_list)
    selected_books = []
    if titles != "None":
        selected_books = [
            b.strip().replace("'", "").replace('"', "")
            for b in titles.replace("[", "").replace("]", "").split("|")
        ]

    # 2️⃣ Если книги определены → пробуем ответ по названиям
    answer = None
    if selected_books:
        answer = get_answers(question, selected_books)

    # 3️⃣ Если ответа нет или пусто → ищем по всем текстовым файлам
    if not answer or "None" in answer:
        files = get_all_book_files()
        answer = ask_big_files(files, question)

    return answer.replace('*', '')


# =========================
# Примеры использования
# =========================
'''if __name__ == "__main__":
    print(test_answer("Кто жил в теремке?"))'''