def get_key(value):
    key = value.split(":")[1:]
    key = "".join(key).replace("\n", "")
    return key


def get_questions_list(file_path):

    with open(file_path, 'r', encoding='KOI8-R') as file:
        file_content = file.read()

    material = []
    element = {}
    splitted_content = file_content.split("\n\n")
    for line in splitted_content:
        if line.startswith("Вопрос"):
            element["question"] = get_key(line)
            continue

        if line.startswith("Ответ"):
            element["answer"] = get_key(line)

        if element:
            material.append(element)
            element = {}
    return material


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
