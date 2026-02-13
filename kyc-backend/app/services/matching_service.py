from fuzzywuzzy import fuzz


# -----------------------------------
# normalize name (very important)
# -----------------------------------
def normalize_name(name: str) -> str:
    if not name:
        return ""

    return (
        name.lower()
        .replace(".", "")
        .replace(",", "")
        .strip()
    )


# -----------------------------------
# compare names using fuzzy matching
# -----------------------------------
def match_names(user_name: str, ocr_name: str):
    user_name = normalize_name(user_name)
    ocr_name = normalize_name(ocr_name)

    score = fuzz.token_sort_ratio(user_name, ocr_name)

    return {
        "similarity": score,
        "match": score >= 90
    }
