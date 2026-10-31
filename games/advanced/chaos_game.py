from typing import Final

from PyQt6.QtCore import QPointF, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPaintEvent, QPen, QPolygonF
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from core.base_game import BaseGame, Difficulty
from core.game_registry import register_game
from utils.chaos_game_utils import (
    MAX_VERTEX_COUNT,
    MIN_VERTEX_COUNT,
    Point,
    compute_polygon_vertices,
    pick_starting_point,
    step,
)

CANVAS_SIZE_PX: Final[int] = 480
CANVAS_MARGIN_PX: Final[int] = 30
CANVAS_RADIUS_PX: Final[float] = (CANVAS_SIZE_PX / 2) - CANVAS_MARGIN_PX
VERTEX_DOT_RADIUS_PX: Final[float] = 4.0

MAX_POINTS: Final[int] = 30_000
TIMER_INTERVAL_MS: Final[int] = 16  # ~60fps

DEFAULT_POINTS_PER_TICK: Final[int] = 30
MIN_POINTS_PER_TICK: Final[int] = 5
MAX_POINTS_PER_TICK: Final[int] = 150

VERTEX_COUNT_OPTIONS: Final[tuple[int, ...]] = (3, 4, 5, 6)

# One color per possible vertex index, so a point's color shows which
# vertex it was drawn towards -- this is what makes the fractal's
# internal structure visible rather than just a gray blob.
_VERTEX_COLORS: Final[tuple[str, ...]] = (
    "#e53935",  # red
    "#1e88e5",  # blue
    "#43a047",  # green
    "#fb8c00",  # orange
    "#8e24aa",  # purple
    "#00897b",  # teal
)


class _ChaosCanvas(QWidget):
    """Paints the polygon's vertices and every generated point so far.

    Points are kept grouped by which vertex they were drawn towards
    (`_points_by_color`) so paintEvent can batch-draw each color in one
    QPainter.drawPoints() call -- fast even at tens of thousands of points,
    since looping drawPoint() one call at a time would not keep up with a
    60fps timer at this volume.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(CANVAS_SIZE_PX, CANVAS_SIZE_PX)
        self._vertices: list[QPointF] = []
        self._points_by_color: dict[int, list[QPointF]] = {}

    def set_vertices(self, vertices: list[Point]) -> None:
        self._vertices = [QPointF(vertex.x, vertex.y) for vertex in vertices]
        self.update()

    def clear_points(self) -> None:
        self._points_by_color.clear()
        self.update()

    def add_points(self, points_with_color: list[tuple[QPointF, int]]) -> None:
        for point, color_index in points_with_color:
            self._points_by_color.setdefault(color_index, []).append(point)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#ffffff"))

        for color_index, points in self._points_by_color.items():
            painter.setPen(QPen(QColor(_VERTEX_COLORS[color_index]), 1.5))
            painter.drawPoints(QPolygonF(points))

        painter.setPen(QPen(QColor("#333333"), 1))
        painter.setBrush(QColor("#333333"))
        for vertex in self._vertices:
            painter.drawEllipse(vertex, VERTEX_DOT_RADIUS_PX, VERTEX_DOT_RADIUS_PX)


@register_game(
    display_name="Fraktal ve Kaos Oyunları",
    difficulty=Difficulty.ADVANCED,
    instructions=(
        "Klasik 'Kaos Oyunu' (Chaos Game): ekrandaki nokta her adımda, "
        "rastgele seçilen bir köşeye doğru yolun tam yarısına taşınır. "
        "Binlerce kez tekrarlanan bu basit, rastgele kural, sonunda "
        "şaşırtıcı şekilde düzenli bir fraktal desen oluşturur.\n\n"
        "3 köşe (üçgen) seçiliyken kısıtlama yok -- bu tam olarak "
        "Sierpinski Üçgeni'ni üretir: üçgenin tam ortası asla "
        "doldurulmaz. 4, 5 ve 6 köşede ise ardı ardına aynı köşenin "
        "(ya da bir önceki seçimin) iki kez seçilmesi engellenir -- "
        "bu kısıtlama olmasaydı nokta bulutu köşegenleri tamamen "
        "düzensizce doldururdu; kısıtlama sayesinde kendine benzer bir "
        "desen ortaya çıkar.\n\n"
        "Her nokta, yöneldiği köşenin rengiyle çizilir -- bu, fraktalın "
        "iç yapısını gözle görülür kılar. Üstteki menüden köşe sayısını "
        "değiştirebilir, hız kaydırıcısıyla çizim hızını "
        "ayarlayabilirsin. 'P' tuşu (ya da ▶️/⏸ butonu) çizimi "
        "duraklatır/devam ettirir."
    ),
)
class ChaosGameGame(BaseGame):
    """The Chaos Game: animated midpoint-iteration fractal generator.

    This is the project's second timer-driven game (after Math
    Countdown), so toggle_pause() genuinely starts/stops the QTimer --
    and the on-screen play/pause button calls the exact same method as
    the P-key shortcut, so there is only one pause/resume code path.
    """

    def __init__(self) -> None:
        super().__init__()
        self._vertices: list[Point] = []
        self._current_point: Point = Point(0.0, 0.0)
        self._previous_index: int | None = None
        self._previous_previous_index: int | None = None
        self._generated_count: int = 0
        self._is_running: bool = False
        self._is_complete: bool = False

        self._timer = QTimer(self)
        self._timer.setInterval(TIMER_INTERVAL_MS)
        self._timer.timeout.connect(self._handle_tick)

        self._vertex_count_combo = QComboBox()
        for vertex_count in VERTEX_COUNT_OPTIONS:
            self._vertex_count_combo.addItem(f"{vertex_count} köşe", userData=vertex_count)
        self._vertex_count_combo.currentIndexChanged.connect(self._handle_vertex_count_changed)

        self._play_pause_button = QPushButton()
        self._play_pause_button.clicked.connect(self.toggle_pause)

        self._speed_slider = QSlider(Qt.Orientation.Horizontal)
        self._speed_slider.setRange(MIN_POINTS_PER_TICK, MAX_POINTS_PER_TICK)
        self._speed_slider.setValue(DEFAULT_POINTS_PER_TICK)
        self._speed_slider.setFixedWidth(160)
        self._speed_slider.valueChanged.connect(self._handle_speed_changed)
        self._points_per_tick: int = DEFAULT_POINTS_PER_TICK

        self._status_label = QLabel()
        self._status_label.setStyleSheet("font-size: 14px;")

        self._canvas = _ChaosCanvas()

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Köşe sayısı:"))
        controls_layout.addWidget(self._vertex_count_combo)
        controls_layout.addSpacing(16)
        controls_layout.addWidget(self._play_pause_button)
        controls_layout.addSpacing(16)
        controls_layout.addWidget(QLabel("Hız:"))
        controls_layout.addWidget(self._speed_slider)
        controls_layout.addStretch(1)

        canvas_centering_layout = QHBoxLayout()
        canvas_centering_layout.addStretch(1)
        canvas_centering_layout.addWidget(self._canvas)
        canvas_centering_layout.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(controls_layout)
        layout.addWidget(self._status_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(8)
        layout.addLayout(canvas_centering_layout)
        layout.addStretch(1)

    def start(self) -> None:
        self._timer.stop()
        vertex_count = self._vertex_count_combo.currentData() or MIN_VERTEX_COUNT
        center = Point(CANVAS_SIZE_PX / 2, CANVAS_SIZE_PX / 2)
        self._vertices = compute_polygon_vertices(vertex_count, center, CANVAS_RADIUS_PX)
        self._current_point = pick_starting_point(self._vertices)
        self._previous_index = None
        self._previous_previous_index = None
        self._generated_count = 0
        self._is_complete = False

        self._canvas.set_vertices(self._vertices)
        self._canvas.clear_points()
        self._update_status_label()

        self._is_running = True
        self._timer.start()
        self._update_play_pause_button()

    def reset(self) -> None:
        self.start()

    def toggle_pause(self) -> None:
        if self._is_complete:
            return
        self._is_running = not self._is_running
        if self._is_running:
            self._timer.start()
        else:
            self._timer.stop()
        self._update_play_pause_button()

    def _handle_vertex_count_changed(self, _index: int) -> None:
        self.start()

    def _handle_speed_changed(self, value: int) -> None:
        self._points_per_tick = value

    def _handle_tick(self) -> None:
        points_to_generate = min(self._points_per_tick, MAX_POINTS - self._generated_count)
        new_points: list[tuple[QPointF, int]] = []
        for _ in range(points_to_generate):
            self._current_point, chosen_index = step(
                self._current_point, self._vertices, self._previous_index, self._previous_previous_index
            )
            self._previous_previous_index = self._previous_index
            self._previous_index = chosen_index
            new_points.append((QPointF(self._current_point.x, self._current_point.y), chosen_index))

        self._generated_count += len(new_points)
        self._canvas.add_points(new_points)
        self._update_status_label()

        if self._generated_count >= MAX_POINTS:
            self._timer.stop()
            self._is_running = False
            self._is_complete = True
            self._update_play_pause_button()
            self._status_label.setText(
                f"Tamamlandı: {MAX_POINTS} nokta çizildi. Köşe sayısını değiştirip tekrar deneyebilirsin."
            )

    def _update_status_label(self) -> None:
        if not self._is_complete:
            self._status_label.setText(f"{self._generated_count} / {MAX_POINTS} nokta")

    def _update_play_pause_button(self) -> None:
        self._play_pause_button.setText("⏸ Duraklat" if self._is_running else "▶️ Devam Et")
        self._play_pause_button.setEnabled(not self._is_complete)
