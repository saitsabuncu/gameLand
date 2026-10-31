from enum import Enum, auto
from typing import Final

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from core.base_game import BaseGame, Difficulty
from core.game_registry import register_game
from utils.monty_hall_utils import (
    DOOR_COUNT,
    SimulationResult,
    pick_host_door,
    pick_random_door,
    remaining_switch_door,
    run_simulation,
)

DOOR_CLOSED_SYMBOL: Final[str] = "🚪"
DOOR_GOAT_SYMBOL: Final[str] = "🐐"
DOOR_CAR_SYMBOL: Final[str] = "🚗"

SIMULATION_ROUNDS_MIN: Final[int] = 10
SIMULATION_ROUNDS_MAX: Final[int] = 100_000
SIMULATION_ROUNDS_DEFAULT: Final[int] = 1_000


class _RoundPhase(Enum):
    CHOOSING_DOOR = auto()
    AWAITING_SWITCH_DECISION = auto()
    REVEALED = auto()


@register_game(
    display_name="Monty Hall Problemi Simülasyonu",
    difficulty=Difficulty.INTERMEDIATE,
    instructions=(
        "3 kapıdan birinin arkasında araba, diğer ikisinin arkasında keçi var. "
        "Bir kapı seç; sunucu (Monty), arabanın olmadığı ve senin seçmediğin "
        "kapılardan birini açıp bir keçi gösterir. Ardından kararını ver: "
        "SEÇİMİNİ DEĞİŞTİR ya da AYNI KAPIDA KAL.\n\n"
        "Sezgiye aykırı ama matematiksel gerçek: değiştirmek kazanma şansını "
        "üçte birden üçte ikiye çıkarır (≈%66.7), aynı kapıda kalmak ise üçte "
        "bir (≈%33.3) olarak kalır. Bunun nedeni, sunucunun hangi kapıyı "
        "açacağını rastgele değil, kuralla (asla arabayı açmaz) seçmesi.\n\n"
        "Alttaki 'Simüle Et' ile yüzlerce/binlerce turu anında oynatıp bu "
        "oranların gerçekte nasıl oluştuğunu istatistik panelinde "
        "gözlemleyebilirsin -- manuel oynadığın turlar da aynı istatistiklere "
        "eklenir."
    ),
)
class MontyHallGame(BaseGame):
    """Monty Hall problem: manual play plus a bulk-simulation stats panel.

    Manual rounds and the bulk simulator both feed the same running
    switch/stay tally, so the displayed win rates converge toward the
    textbook 2/3 vs 1/3 split regardless of which mode produced them.
    """

    def __init__(self) -> None:
        super().__init__()
        self._phase: _RoundPhase = _RoundPhase.CHOOSING_DOOR
        self._car_door: int = 0
        self._player_choice: int | None = None
        self._host_door: int | None = None
        self._total_switch_wins: int = 0
        self._total_switch_attempts: int = 0
        self._total_stay_wins: int = 0
        self._total_stay_attempts: int = 0

        self._status_label = QLabel()
        self._result_label = QLabel()
        self._result_label.setStyleSheet("font-size: 18px; font-weight: 600;")

        self._door_buttons: list[QPushButton] = []
        door_row_layout = QHBoxLayout()
        for door_index in range(DOOR_COUNT):
            door_button = QPushButton(DOOR_CLOSED_SYMBOL)
            door_button.setFixedSize(80, 80)
            door_button.setStyleSheet("font-size: 32px;")
            door_button.clicked.connect(
                lambda _checked, door=door_index: self._handle_door_clicked(door)
            )
            self._door_buttons.append(door_button)
            door_row_layout.addWidget(door_button)

        self._switch_button = QPushButton("🔄 Seçimini Değiştir")
        self._switch_button.clicked.connect(lambda: self._handle_decision(switch=True))
        self._stay_button = QPushButton("✋ Aynı Kapıda Kal")
        self._stay_button.clicked.connect(lambda: self._handle_decision(switch=False))
        decision_row_layout = QHBoxLayout()
        decision_row_layout.addWidget(self._switch_button)
        decision_row_layout.addWidget(self._stay_button)

        self._stats_label = QLabel()

        self._simulation_rounds_spinbox = QSpinBox()
        self._simulation_rounds_spinbox.setRange(SIMULATION_ROUNDS_MIN, SIMULATION_ROUNDS_MAX)
        self._simulation_rounds_spinbox.setValue(SIMULATION_ROUNDS_DEFAULT)
        self._simulation_rounds_spinbox.setSuffix(" tur")

        simulate_button = QPushButton("⚡ Simüle Et")
        simulate_button.clicked.connect(self._handle_simulate_clicked)

        reset_stats_button = QPushButton("İstatistikleri Sıfırla")
        reset_stats_button.clicked.connect(self._handle_reset_stats_clicked)

        simulation_row_layout = QHBoxLayout()
        simulation_row_layout.addWidget(self._simulation_rounds_spinbox)
        simulation_row_layout.addWidget(simulate_button)
        simulation_row_layout.addWidget(reset_stats_button)
        simulation_row_layout.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(self._status_label)
        layout.addLayout(door_row_layout)
        layout.addLayout(decision_row_layout)
        layout.addWidget(self._result_label)
        layout.addWidget(self._stats_label)
        layout.addLayout(simulation_row_layout)
        layout.addStretch(1)

    def start(self) -> None:
        self._begin_new_round()
        self._update_stats_label()

    def reset(self) -> None:
        self._total_switch_wins = 0
        self._total_switch_attempts = 0
        self._total_stay_wins = 0
        self._total_stay_attempts = 0
        self.start()

    def _begin_new_round(self) -> None:
        self._phase = _RoundPhase.CHOOSING_DOOR
        self._car_door = pick_random_door()
        self._player_choice = None
        self._host_door = None
        self._result_label.clear()
        self._status_label.setText("Bir kapı seç 🚪")
        self._set_decision_buttons_visible(False)
        self._render_doors()

    def _handle_door_clicked(self, door_index: int) -> None:
        if self._phase != _RoundPhase.CHOOSING_DOOR:
            return
        self._player_choice = door_index
        self._host_door = pick_host_door(self._car_door, door_index)
        self._phase = _RoundPhase.AWAITING_SWITCH_DECISION
        self._status_label.setText(
            f"Monty, {self._host_door + 1}. kapıyı açtı -- arkasında keçi var. "
            "Şimdi karar ver:"
        )
        self._set_decision_buttons_visible(True)
        self._render_doors()

    def _handle_decision(self, switch: bool) -> None:
        if self._phase != _RoundPhase.AWAITING_SWITCH_DECISION:
            return
        assert self._player_choice is not None
        assert self._host_door is not None

        final_choice = (
            remaining_switch_door(self._player_choice, self._host_door)
            if switch
            else self._player_choice
        )
        won = final_choice == self._car_door
        self._record_round_outcome(switch=switch, won=won)

        self._phase = _RoundPhase.REVEALED
        self._player_choice = final_choice
        self._set_decision_buttons_visible(False)
        self._status_label.setText("Tur bitti -- yeniden başlamak için 'R' tuşuna bas.")
        self._result_label.setText(
            f"{'🎉 Kazandın!' if won else '😢 Kaybettin.'} "
            f"({'Değiştirdin' if switch else 'Kaldın'} -- araba {self._car_door + 1}. kapıdaydı)"
        )
        self._render_doors()
        self._update_stats_label()

    def _record_round_outcome(self, switch: bool, won: bool) -> None:
        if switch:
            self._total_switch_attempts += 1
            self._total_switch_wins += 1 if won else 0
        else:
            self._total_stay_attempts += 1
            self._total_stay_wins += 1 if won else 0

    def _handle_simulate_clicked(self) -> None:
        rounds = self._simulation_rounds_spinbox.value()
        result: SimulationResult = run_simulation(rounds)
        self._total_switch_attempts += result.rounds
        self._total_switch_wins += result.switch_wins
        self._total_stay_attempts += result.rounds
        self._total_stay_wins += result.stay_wins
        self._status_label.setText(f"{result.rounds} tur simüle edildi.")
        self._update_stats_label()

    def _handle_reset_stats_clicked(self) -> None:
        self._total_switch_wins = 0
        self._total_switch_attempts = 0
        self._total_stay_wins = 0
        self._total_stay_attempts = 0
        self._update_stats_label()

    def _set_decision_buttons_visible(self, visible: bool) -> None:
        self._switch_button.setVisible(visible)
        self._stay_button.setVisible(visible)

    def _render_doors(self) -> None:
        for door_index, door_button in enumerate(self._door_buttons):
            door_button.setText(self._door_symbol_for(door_index))
            door_button.setEnabled(
                self._phase == _RoundPhase.CHOOSING_DOOR and door_index != self._player_choice
            )

    def _door_symbol_for(self, door_index: int) -> str:
        if self._phase == _RoundPhase.CHOOSING_DOOR:
            return DOOR_CLOSED_SYMBOL
        if self._phase == _RoundPhase.AWAITING_SWITCH_DECISION:
            return DOOR_GOAT_SYMBOL if door_index == self._host_door else DOOR_CLOSED_SYMBOL
        # _RoundPhase.REVEALED: every door is shown.
        return DOOR_CAR_SYMBOL if door_index == self._car_door else DOOR_GOAT_SYMBOL

    def _update_stats_label(self) -> None:
        total_rounds = self._total_switch_attempts + self._total_stay_attempts
        if total_rounds == 0:
            self._stats_label.setText("İstatistik: henüz tur oynanmadı.")
            return

        switch_rate = self._win_rate(self._total_switch_wins, self._total_switch_attempts)
        stay_rate = self._win_rate(self._total_stay_wins, self._total_stay_attempts)
        self._stats_label.setText(
            f"İstatistik ({total_rounds} tur) -- "
            f"Değiştirdi: {self._total_switch_wins}/{self._total_switch_attempts} "
            f"kazanç ({switch_rate:.1%})  |  "
            f"Kaldı: {self._total_stay_wins}/{self._total_stay_attempts} "
            f"kazanç ({stay_rate:.1%})"
        )

    @staticmethod
    def _win_rate(wins: int, attempts: int) -> float:
        return wins / attempts if attempts else 0.0
