import re


def join_keywords(keyword_list):
    return " ".join(keyword_list) if keyword_list else ""


def is_valid_keyword(keyword):
    if not keyword or not isinstance(keyword, str):
        return False

    if (
        (keyword.find("\n") != -1)
        or (len(keyword.split("\n")) > 1)
        or re.search(r"\n", keyword)
        or (keyword.count("\n") > 0)
        or "Keyword" in keyword
        or "Keyword" in keyword
        or "keyword" in keyword
    ):
        return False
    return True


def is_valid_keyword_list(keywords_list):
    if not keywords_list or not isinstance(keywords_list, list):
        return False

    joint_keyword = join_keywords(keywords_list)

    return is_valid_keyword(joint_keyword)
