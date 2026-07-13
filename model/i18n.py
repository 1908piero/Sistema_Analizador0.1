import json
import os

_current_lang = "es"
_strings = {}

_DIR = os.path.dirname(os.path.abspath(__file__))
_I18N_DIR = os.path.join(os.path.dirname(_DIR), "i18n")


def _load_lang(lang: str):
    global _strings
    path = os.path.join(_I18N_DIR, f"{lang}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            _strings = json.load(f)
    else:
        _strings = {}


def set_language(lang: str):
    global _current_lang
    _current_lang = lang
    _load_lang(lang)


def _(key: str) -> str:
    return _strings.get(key, key)


def current_lang() -> str:
    return _current_lang


# Load default
_load_lang("es")
