from mistralai import Mistral
import os

api_key = "CZQV58B314sveOcSbZTnfA3RjFupG5PT"

client = Mistral(api_key=api_key)

books = [
    "Колобок",
    "Война и мир",
    "Преступление и наказание",
    "Муму"
]

books_folder = "books"
user_files_folder = "user_files"


def get_titles_to_question(question):
    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {
                "role": "system",
                "content": f"""
Есть список книг:

{books}

Определи к каким книгам относится вопрос.

Формат ответа строго:
[книга]
или
[книга1 | книга2]
или
None
"""
            },
            {"role": "user", "content": question}
        ],
        temperature=0
    )
    return response.choices[0].message.content.strip()


def get_answers(question, books_list):
    texts = []
    for file in os.listdir(books_folder):
        if file.endswith(".txt"):
            path = os.path.join(books_folder, file)
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()[:12000]
                texts.append(f"Файл: {file}\n{text}")

    if not texts:
        return "Не удалось прочитать книги."

    books_text = "\n\n".join(texts)

    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {
                "role": "system",
                "content": """
Ты анализируешь тексты книг.

Нужно определить, в каких из этих книг есть ответ на вопрос.

Ответ должен быть в формате:

В книгах:
- "название книги" (краткое объяснение)
- "название книги" (краткое объяснение)

Если книга не относится к вопросу — не упоминай её.
"""
            },
            {
                "role": "user",
                "content": f"""
Список книг:
{books_list}

Тексты файлов:
{books_text}

Вопрос:
{question}
"""
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()


def get_answer_from_files(question):
    texts = []
    for file in os.listdir(user_files_folder):
        if file.endswith(".txt"):
            path = os.path.join(user_files_folder, file)
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()[:12000]
                texts.append(f"Файл: {file}\n{text}")

    files_text = "\n\n".join(texts)

    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {
                "role": "system",
                "content": """
Отвечай только на основе текста файлов.

Если ответа нет — напиши:
None
"""
            },
            {
                "role": "user",
                "content": f"""
Тексты файлов:

{files_text}

Вопрос:
{question}
"""
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()


def get_file_origin(file_content):
    """
    Определяет, какому произведению принадлежит данный текст.
    Формат строго: "Фамилия И. О. - Название произведения"
    """
    question_text = '''Определи какому произведению относится данный отрывок.
Ответ выведи в виде "Фамилия И. О. - Название произведения".
Например: "Достоевский Ф. М. - Преступление и наказание".
Только строго по примеру, ничего больше не пиши после точки.'''

    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {
                "role": "system",
                "content": "Отвечай только на основе предоставленного текста. Если информации нет в тексте — скажи, что её нет."
            },
            {
                "role": "user",
                "content": f"""Вот содержимое файла:

{file_content}

Вопрос: {question_text}
"""
            }
        ]
    )

    return response.choices[0].message.content.strip()


def test_answer(question):
    titles = get_titles_to_question(question)

    books_list = []
    if titles != "None":
        books_list = [
            b.strip().replace("'", "").replace('"', "")
            for b in titles.replace("[", "").replace("]", "").split("|")
        ]

    result = f"Подходящие книги:{books_list}\n"

    if books_list:
        answer = get_answers(question, books_list)
        result += f"\nОтвет:\n{answer}"
    else:
        answer = get_answer_from_files(question)
        result += f"\nОтвет из файлов:\n{answer}"

    return result



def open_file_to_research_origin(filepath):
    # Вопрос по конкретному файлу
    with open(filepath, "r", encoding="utf-8") as f:
        file_content = f.read(400)
    origin = get_file_origin(file_content)
    return origin
