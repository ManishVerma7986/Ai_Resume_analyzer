import re

PROTECTED_TOKENS = [
    "C++",
    "C#",
    ".NET",
    "Node.js",
    "scikit-learn",
    "Power BI",
]


def _protect(text: str):
    mapping = {}
    for i, token in enumerate(PROTECTED_TOKENS):
        key = f"__PROT_{i}__"
        mapping[key] = token
        # replace token in a case-insensitive way
        text = re.sub(re.escape(token), key, text, flags=re.IGNORECASE)
    return text, mapping


def _restore(text: str, mapping: dict):
    for key, token in mapping.items():
        text = text.replace(key, token)
    return text


def clean_text(text: str) -> str:
    if not text:
        return ""

    # Protect important tokens that include punctuation
    text_prot, mapping = _protect(text)

    # Lowercase everything (but protected tokens are placeholders)
    text_prot = text_prot.lower()

    # Remove email addresses and urls (for privacy and noise)
    text_prot = re.sub(r"\S+@\S+", " ", text_prot)
    text_prot = re.sub(r"https?://\S+", " ", text_prot)

    # Remove non-alphanumeric characters except basic punctuation used in tokens
    text_prot = re.sub(r"[^a-z0-9_\-\+\#\.\s]", " ", text_prot)

    # Normalize whitespace
    text_prot = re.sub(r"\s+", " ", text_prot).strip()

    # Restore protected tokens (but ensure proper casing)
    restored = _restore(text_prot, mapping)

    return restored


def normalize_text(text: str) -> str:
    # Additional normalization if needed (lemmatization could be added later)
    cleaned = clean_text(text)
    return cleaned
