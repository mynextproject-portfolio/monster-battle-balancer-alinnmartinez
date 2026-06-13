import flet as ft
from ui_constants import (
    SPACING_SM, SPACING_LG, SPACING_XL,
    BUTTON_HEIGHT_LG, BUTTON_WIDTH_LG,
    TEXT_SIZE_LG, TEXT_SIZE_XL
)


def language_selection_screen(page: ft.Page, on_language_selected):
    """Render the language selection screen.

    Args:
        page: The Flet page object
        on_language_selected: Callback function to proceed with selected language
    """
    def handle_japanese(e):
        """Handle Japanese language selection."""
        on_language_selected("ja")

    def handle_english(e):
        """Handle English language selection."""
        on_language_selected("en")

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(height=SPACING_XL * 2),  # Spacer
                ft.Icon(
                    name=ft.Icons.LANGUAGE,
                    size=120,
                    color=ft.Colors.BLUE_400,
                ),
                ft.Container(height=SPACING_LG),
                ft.Text(
                    "言語を選択 / Select Language",
                    size=48,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_400,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=SPACING_XL * 2),
                # Japanese button (first option)
                ft.ElevatedButton(
                    "日本語 (Japanese)",
                    width=BUTTON_WIDTH_LG,
                    height=BUTTON_HEIGHT_LG,
                    on_click=handle_japanese,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.RED_700,
                        color=ft.Colors.WHITE,
                    ),
                ),
                ft.Container(height=SPACING_LG),
                # English button (second option)
                ft.ElevatedButton(
                    "English",
                    width=BUTTON_WIDTH_LG,
                    height=BUTTON_HEIGHT_LG,
                    on_click=handle_english,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE_700,
                        color=ft.Colors.WHITE,
                    ),
                ),
                ft.Container(height=SPACING_XL),
                ft.Text(
                    "日本語がデフォルトです。 / Japanese is the default.",
                    size=TEXT_SIZE_LG,
                    color=ft.Colors.GREY_400,
                    text_align=ft.TextAlign.CENTER,
                    italic=True,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        expand=True,
    )
