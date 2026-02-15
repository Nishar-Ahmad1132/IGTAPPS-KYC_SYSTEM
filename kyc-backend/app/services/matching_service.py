from rapidfuzz import fuzz

# -------------------------
# CONFIG (PRODUCTION READY)
# -------------------------
STRICT_THRESHOLD = 90     # exact match
LENIENT_THRESHOLD = 75    # acceptable match


# -------------------------
# NORMALIZE NAME
# -------------------------
def normalize_name(name: str) -> str:
    if not name:
        return ""
    name = name.lower()

    # remove punctuation
    name = name.replace(".", "").replace(",", "")

    # remove extra spaces
    name = " ".join(name.split())

    return name


# -------------------------
# NAME MATCHING (FINAL)
# -------------------------
def match_names(user_name: str, ocr_name: str):
    user_name = normalize_name(user_name)
    ocr_name = normalize_name(ocr_name)

    if not user_name or not ocr_name:
        return {
            "score": 0,
            "match": False,
            "level": "NO_DATA"
        }

    # 🔥 Use multiple algorithms (production trick)
    score1 = fuzz.token_sort_ratio(user_name, ocr_name)
    score2 = fuzz.token_set_ratio(user_name, ocr_name)
    score3 = fuzz.partial_ratio(user_name, ocr_name)

    # take best score
    score = max(score1, score2, score3)

    # -------------------------
    # Decision Levels
    # -------------------------
    if score >= STRICT_THRESHOLD:
        level = "STRONG_MATCH"
        match = True
    elif score >= LENIENT_THRESHOLD:
        level = "WEAK_MATCH"
        match = True
    else:
        level = "NO_MATCH"
        match = False

    return {
        "score": round(score, 2),
        "match": match,
        "level": level
    }