"""Language configuration and translation utilities."""

# Global language state (Japanese is default)
_current_language = "ja"


def set_language(language_code: str):
    """Set the current language.
    
    Args:
        language_code: "ja" for Japanese or "en" for English
    """
    global _current_language
    _current_language = language_code


def get_language() -> str:
    """Get the current language code.
    
    Returns:
        The current language code ("ja" or "en")
    """
    return _current_language


# Translation dictionaries
TRANSLATIONS = {
    "ja": {
        # main.py
        "app_title": "モンスターバトル",
        
        # home_screen.py
        "home_title": "モンスターバトル",
        "home_subtitle": "D&D モンスタービューアー",
        "home_description": "2体のモンスターを選んで、ステータスカードを見比べよう",
        "home_button": "モンスターを見る",
        
        # monster_selection_screen.py
        "selection_error_loading": "モンスターの読み込みに失敗しました",
        "selection_error_connection": "インターネット接続を確認してください",
        "selection_back_button": "← もどる",
        "selection_dropdown1": "モンスター1を選択",
        "selection_dropdown2": "モンスター2を選択",
        "selection_error_validation": "モンスターを2体選んでください！",
        "selection_tooltip_back": "ホームにもどる",
        "selection_title": "モンスター選択",
        "selection_description": "見比べる2体のモンスターを選んでください",
        "selection_label1": "モンスター1",
        "selection_label2": "モンスター2",
        "selection_button": "🃏 カードを見る",
        
        # cards_screen.py
        "cards_error_loading": "モンスター情報の読み込みに失敗しました",
        "cards_error_connection": "インターネット接続を確認してください",
        "cards_back_button": "← もどる",
        "cards_defense": "防御 (AC): ",
        "cards_strength": "筋力 (STR): ",
        "cards_tooltip_back": "モンスター選択にもどる",
        "cards_title": "モンスターカード",
    },
    "en": {
        # main.py
        "app_title": "Monster Battle",
        
        # home_screen.py
        "home_title": "Monster Battle",
        "home_subtitle": "D&D Monster Viewer",
        "home_description": "Select 2 monsters and compare their stat cards",
        "home_button": "View Monsters",
        
        # monster_selection_screen.py
        "selection_error_loading": "Failed to load monsters",
        "selection_error_connection": "Please check your internet connection",
        "selection_back_button": "← Back",
        "selection_dropdown1": "Select Monster 1",
        "selection_dropdown2": "Select Monster 2",
        "selection_error_validation": "Please select 2 monsters!",
        "selection_tooltip_back": "Go back to home",
        "selection_title": "Monster Selection",
        "selection_description": "Select 2 monsters to compare",
        "selection_label1": "Monster 1",
        "selection_label2": "Monster 2",
        "selection_button": "🃏 View Cards",
        
        # cards_screen.py
        "cards_error_loading": "Failed to load monster information",
        "cards_error_connection": "Please check your internet connection",
        "cards_back_button": "← Back",
        "cards_defense": "Defense (AC): ",
        "cards_strength": "Strength (STR): ",
        "cards_tooltip_back": "Back to monster selection",
        "cards_title": "Monster Cards",
    }
}


def t(key: str) -> str:
    """Get a translated string for the current language.
    
    Args:
        key: The translation key
        
    Returns:
        The translated string, or the key itself if not found
    """
    language = get_language()
    return TRANSLATIONS.get(language, {}).get(key, key)
