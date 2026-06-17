import flet as ft
from dnd_api import get_monster_details
from models.monster import Monster
from battle import simulate_battle
from ui_constants import (
    SPACING_XS, SPACING_SM, SPACING_LG, SPACING_XL,
    BUTTON_HEIGHT_MD, BUTTON_WIDTH_MD,
    TEXT_SIZE_MD, TEXT_SIZE_LG, TEXT_SIZE_XL,
)
from language_config import t


def battle_screen(page: ft.Page, monster1_index: str, monster2_index: str, on_back, on_fight_again):
    """Simulate a fight between two monsters and display the winner.

    Args:
        page: The Flet page object
        monster1_index: Index of the first monster
        monster2_index: Index of the second monster
        on_back: Callback to return to the cards screen
        on_fight_again: Callback to re-run the same matchup with a fresh random result
    """
    monster1 = get_monster_details(monster1_index)
    monster2 = get_monster_details(monster2_index)

    if not monster1 or not monster2:
        return ft.Column(
            [
                ft.Container(height=SPACING_XL),
                ft.Icon(ft.Icons.ERROR_OUTLINE, size=80, color=ft.Colors.RED_400),
                ft.Container(height=SPACING_LG),
                ft.Text(t("cards_error_loading"), size=TEXT_SIZE_XL, color=ft.Colors.RED_400),
                ft.Text(t("cards_error_connection"), size=TEXT_SIZE_LG, color=ft.Colors.GREY_400),
                ft.Container(height=SPACING_XL),
                ft.ElevatedButton(
                    t("battle_back_button"),
                    on_click=on_back,
                    width=BUTTON_WIDTH_MD,
                    height=BUTTON_HEIGHT_MD,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )

    winner = simulate_battle(monster1, monster2)
    m1_wins = winner is monster1

    def create_monster_card(monster: Monster, color: str, is_winner: bool) -> ft.Container:
        crown = ft.Text("👑", size=36, text_align=ft.TextAlign.CENTER) if is_winner else ft.Container(height=36)
        return ft.Container(
            content=ft.Column(
                [
                    crown,
                    ft.Text(
                        monster.name,
                        size=TEXT_SIZE_XL,
                        weight=ft.FontWeight.BOLD,
                        color=color,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=SPACING_SM),
                    ft.Image(
                        src=monster.image_url if monster.image_url else "",
                        width=180,
                        height=180,
                        fit=ft.ImageFit.CONTAIN,
                        error_content=ft.Icon(ft.Icons.QUESTION_MARK, size=90, color=ft.Colors.GREY_600),
                    ),
                    ft.Container(height=SPACING_SM),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(f"HP: {monster.hp}", size=TEXT_SIZE_MD, color=ft.Colors.GREEN_300, weight=ft.FontWeight.BOLD),
                                ft.Text(f"{t('cards_defense')}{monster.ac}", size=TEXT_SIZE_MD, color=ft.Colors.BLUE_300, weight=ft.FontWeight.BOLD),
                                ft.Text(f"{t('cards_strength')}{monster.strength}", size=TEXT_SIZE_MD, color=ft.Colors.ORANGE_300, weight=ft.FontWeight.BOLD),
                            ],
                            spacing=SPACING_XS,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=10,
                        bgcolor=ft.Colors.BLACK26,
                        border_radius=5,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=SPACING_XS,
            ),
            padding=SPACING_SM,
            border=ft.border.all(3 if is_winner else 2, color),
            border_radius=10,
            width=320,
            bgcolor=ft.Colors.GREY_800,
            opacity=1.0 if is_winner else 0.45,
        )

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(height=SPACING_SM),
                # Header
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            icon_color=ft.Colors.WHITE,
                            on_click=on_back,
                            tooltip=t("battle_tooltip_back"),
                        ),
                        ft.Text(
                            t("battle_title"),
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Container(height=SPACING_LG),
                # Monster cards
                ft.Row(
                    [
                        create_monster_card(monster1, ft.Colors.AMBER_400, m1_wins),
                        ft.Container(
                            content=ft.Text("VS", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_400),
                            width=80,
                            alignment=ft.alignment.center,
                        ),
                        create_monster_card(monster2, ft.Colors.BLUE_400, not m1_wins),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    spacing=SPACING_LG,
                    scroll=ft.ScrollMode.AUTO,
                ),
                ft.Container(height=SPACING_LG),
                # Winner banner
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                t("battle_winner_label"),
                                size=TEXT_SIZE_LG,
                                color=ft.Colors.YELLOW_200,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                winner.name,
                                size=36,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.AMBER_400 if m1_wins else ft.Colors.BLUE_400,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=SPACING_XS,
                    ),
                    padding=ft.padding.symmetric(horizontal=SPACING_XL, vertical=SPACING_SM),
                    bgcolor=ft.Colors.BLACK38,
                    border_radius=12,
                    border=ft.border.all(2, ft.Colors.AMBER_400 if m1_wins else ft.Colors.BLUE_400),
                ),
                ft.Container(height=SPACING_LG),
                # Action buttons
                ft.Row(
                    [
                        ft.ElevatedButton(
                            t("battle_again_button"),
                            on_click=on_fight_again,
                            width=BUTTON_WIDTH_MD,
                            height=BUTTON_HEIGHT_MD,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.RED_700,
                                color=ft.Colors.WHITE,
                            ),
                        ),
                        ft.ElevatedButton(
                            t("battle_back_button"),
                            on_click=on_back,
                            width=BUTTON_WIDTH_MD,
                            height=BUTTON_HEIGHT_MD,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=SPACING_LG,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        ),
        expand=True,
        padding=SPACING_SM,
    )
