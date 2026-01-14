def get_line_content(value):
    key = value.split(":")[1:]
    key = "".join(key).replace("\n", "")
    return key


def get_questions_list(file_path):

    with open(file_path, 'r', encoding='KOI8-R') as file:
        file_content = file.read()

    questions_list = []
    question = {}
    splitted_content = file_content.split("\n\n")
    for line in splitted_content:
        if line.startswith("Вопрос"):
            question["question"] = get_line_content(line)
            continue

        if line.startswith("Ответ"):
            question["answer"] = get_line_content(line)

        if question:
            questions_list.append(question)
            question = {}
    return questions_list


def format_answer(answer: str) -> str:
    answer = answer[:-1]
    clean_answer = ""
    for char in answer:
        if char == "(":
            break
        clean_answer += char
    clean_answer = clean_answer.lower()
    if clean_answer[-1] == " ":
        return clean_answer[:-1]
    return clean_answer
