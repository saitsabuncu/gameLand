import random
from typing import Final

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QGridLayout, QLabel, QPushButton, QVBoxLayout

from core.achievements import Achievement
from core.base_game import BaseGame, Difficulty
from core.game_registry import register_game

HANGMAN_UNLOCK_DESCRIPTION: Final[str] = (
    "Bu oyunu açmak için Number Guessing, Math Quiz Challenge veya "
    "Asal Sayı Avcısı'ndan birinde en az İyi/Harika seviyesinde bir "
    "sonuç almalısın."
)

MAX_WRONG_GUESSES: Final[int] = 6

WORD_CATEGORIES: Final[dict[str, list[str]]] = {
    "Hayvanlar": [
        "kedi", "köpek", "aslan", "kaplan", "fil",
        "zürafa", "tavşan", "kartal", "balina", "penguen",
    ],
    "Meyveler": [
        "elma", "armut", "muz", "karpuz", "çilek",
        "kiraz", "portakal", "ananas", "nar", "incir",
    ],
    "Meslekler": [
        "doktor", "mühendis", "öğretmen", "avukat", "pilot",
        "hemşire", "mimar", "polis", "aşçı", "yazar",
    ],
}

# Explicit lowercase->uppercase map: Python's str.upper() is not
# Turkish-locale-aware ('i'.upper() == 'I', not 'İ'), so the Turkish
# alphabet is defined here with its correct casing.
TURKISH_ALPHABET: Final[list[tuple[str, str]]] = [
    ("a", "A"), ("b", "B"), ("c", "C"), ("ç", "Ç"), ("d", "D"), ("e", "E"), ("f", "F"),
    ("g", "G"), ("ğ", "Ğ"), ("h", "H"), ("ı", "I"), ("i", "İ"), ("j", "J"), ("k", "K"),
    ("l", "L"), ("m", "M"), ("n", "N"), ("o", "O"), ("ö", "Ö"), ("p", "P"), ("r", "R"),
    ("s", "S"), ("ş", "Ş"), ("t", "T"), ("u", "U"), ("ü", "Ü"), ("v", "V"), ("y", "Y"), ("z", "Z"),
]
LOWER_TO_UPPER: Final[dict[str, str]] = dict(TURKISH_ALPHABET)
KEYBOARD_COLUMNS: Final[int] = 7

# Index = wrong guess count (0..MAX_WRONG_GUESSES), ASCII hangman stages.
HANGMAN_STAGES: Final[list[str]] = [
    "  +---+\n  |   |\n      |\n      |\n      |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n      |\n      |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n  |   |\n      |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n /|   |\n      |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n /|\\  |\n      |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n /|\\  |\n /    |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n /|\\  |\n / \\  |\n      |\n=========",
]


def _to_display_upper(letter: str) -> str:
    return LOWER_TO_UPPER.get(letter, letter.upper())


def _word_to_display_upper(word: str) -> str:
    return "".join(_to_display_upper(letter) for letter in word)


@register_game(
    display_name="Hangman",
    difficulty=Difficulty.BEGINNER,
    required_achievements=frozenset({
        Achievement.NUMBER_GUESSING_GOOD_OR_BETTER,
        Achievement.MATH_QUIZ_GOOD_OR_BETTER,
        Achievement.PRIME_HUNTER_GOOD_OR_BETTER,
    }),
    unlock_description=HANGMAN_UNLOCK_DESCRIPTION,
)
class HangmanGame(BaseGame):
    """Classic hangman: 6 wrong guesses allowed, on-screen Turkish keyboard."""

    def __init__(self) -> None:
        super().__init__()
        self._category: str = ""
        self._word: str = ""
        self._guessed_letters: set[str] = set()
        self._wrong_count: int = 0
        self._letter_buttons: dict[str, QPushButton] = {}

        self._category_label = QLabel()
        self._hangman_label = QLabel()
        self._hangman_label.setFont(QFont("Courier New", 12))
        self._word_label = QLabel()
        self._word_label.setStyleSheet("font-size: 22px; font-weight: 600; letter-spacing: 4px;")
        self._status_label = QLabel()

        self._keyboard_layout = QGridLayout()
        self._keyboard_layout.setSpacing(4)
        self._build_keyboard()

        layout = QVBoxLayout(self)
        layout.addWidget(self._category_label)
        layout.addWidget(self._hangman_label)
        layout.addWidget(self._word_label)
        layout.addWidget(self._status_label)
        layout.addLayout(self._keyboard_layout)
        layout.addStretch(1)

    def _build_keyboard(self) -> None:
        for index, (lower, upper) in enumerate(TURKISH_ALPHABET):
            button = QPushButton(upper)
            button.setFixedSize(40, 36)
            button.clicked.connect(lambda _checked, letter=lower: self._handle_letter_clicked(letter))
            row, column = divmod(index, KEYBOARD_COLUMNS)
            self._keyboard_layout.addWidget(button, row, column)
            self._letter_buttons[lower] = button

    def start(self) -> None:
        self._category = random.choice(list(WORD_CATEGORIES.keys()))
        self._word = random.choice(WORD_CATEGORIES[self._category])
        self._guessed_letters = set()
        self._wrong_count = 0

        self._category_label.setText(f"Kategori: {self._category}")
        self._status_label.clear()
        for button in self._letter_buttons.values():
            button.setEnabled(True)
        self._update_hangman_label()
        self._update_word_label()

    def reset(self) -> None:
        self.start()

    def _handle_letter_clicked(self, letter: str) -> None:
        self._letter_buttons[letter].setEnabled(False)
        self._guessed_letters.add(letter)

        if letter in self._word:
            self._update_word_label()
            if self._is_word_fully_guessed():
                self._handle_win()
        else:
            self._wrong_count += 1
            self._update_hangman_label()
            if self._wrong_count >= MAX_WRONG_GUESSES:
                self._handle_loss()

    def _is_word_fully_guessed(self) -> bool:
        return all(letter in self._guessed_letters for letter in self._word)

    def _update_word_label(self) -> None:
        display = " ".join(
            _to_display_upper(letter) if letter in self._guessed_letters else "_"
            for letter in self._word
        )
        self._word_label.setText(display)

    def _update_hangman_label(self) -> None:
        self._hangman_label.setText(HANGMAN_STAGES[self._wrong_count])

    def _handle_win(self) -> None:
        self._status_label.setText(f"Kazandın! 🎉 Kelime: {_word_to_display_upper(self._word)}")
        self._disable_all_letters()

    def _handle_loss(self) -> None:
        self._status_label.setText(f"Kaybettin! 💀 Kelime: {_word_to_display_upper(self._word)} idi.")
        self._disable_all_letters()

    def _disable_all_letters(self) -> None:
        for button in self._letter_buttons.values():
            button.setEnabled(False)
