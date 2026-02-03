import sys
import os
import random
import numpy as np
import tensorflow as tf
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QIcon
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtWidgets import (QApplication, QWidget, QGridLayout, QPushButton, 
                               QMessageBox, QVBoxLayout, QLabel, QStackedWidget, QMainWindow, QGraphicsDropShadowEffect, QHBoxLayout)
from PySide6.QtCore import Qt, QTimer, QUrl


# Cargar el modelo entrenado
# MODEL_PATH = "tictactoe_ia.h5"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "tictactoe_ia.h5")
try:
    model = tf.keras.models.load_model(MODEL_PATH, compile=False)
except Exception as e:
    print(f"Error cargando el modelo: {e}")
    model = None

class NeonButton(QPushButton):
    def __init__(self, text, start_game_callback=None, mode=None):
        super().__init__(text)
        self.start_game_callback = start_game_callback
        self.mode = mode
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont("Segoe UI", 16, QFont.Bold))
        
        # ID de Estilo Neón para coloreado específico si es necesario (ej. Rojo para salir, Azul para otros)
        self.color = QColor(0, 255, 255) # Cian
        if "X" in text: # Pista para multijugador
             self.color = QColor(255, 0, 128) # Rosado/Rojo
        
        # Efecto de Resplandor
        self.glow = QGraphicsDropShadowEffect(self)
        self.glow.setBlurRadius(20)
        self.glow.setColor(self.color)
        self.glow.setOffset(0, 0)
        self.setGraphicsEffect(self.glow)
        
        self.setStyleSheet(f"""
            QPushButton {{
                color: white;
                background-color: rgba(0, 0, 0, 150);
                border: 2px solid {self.color.name()};
                border-radius: 10px;
                padding: 10px;
                margin: 5px;
            }}
            QPushButton:hover {{
                background-color: {self.color.name()};
                color: black;
            }}
        """)
        
        if self.start_game_callback and self.mode:
            self.clicked.connect(lambda: self.start_game_callback(self.mode))


class MainMenu(QWidget):
    def __init__(self, start_game_callback):
        super().__init__()
        self.start_game_callback = start_game_callback
        self.init_ui()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fondo
        painter.fillRect(self.rect(), QColor(10, 10, 30)) # Azul Marino Oscuro
        
        # Cuadrícula
        pen = QPen(QColor(0, 255, 255, 30)) # Cian Tenue
        pen.setWidth(1)
        painter.setPen(pen)
        
        grid_size = 40
        for x in range(0, self.width(), grid_size):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), grid_size):
            painter.drawLine(0, y, self.width(), y)
            
        # Esquinas Decorativas (Estilo Cyberpunk)
        pen.setColor(QColor(0, 255, 255))
        pen.setWidth(3)
        painter.setPen(pen)
        margin = 20
        d = 30 # longitud de línea
        w = self.width()
        h = self.height()
        
        # Arriba Izquierda
        painter.drawLine(margin, margin, margin + d, margin)
        painter.drawLine(margin, margin, margin, margin + d)
        
        # Arriba Derecha
        painter.drawLine(w - margin, margin, w - margin - d, margin)
        painter.drawLine(w - margin, margin, w - margin, margin + d)
        
        # Abajo Izquierda
        painter.drawLine(margin, h - margin, margin + d, h - margin)
        painter.drawLine(margin, h - margin, margin, h - margin - d)
        
        # Abajo Derecha
        painter.drawLine(w - margin, h - margin, w - margin - d, h - margin)
        painter.drawLine(w - margin, h - margin, w - margin, h - margin - d)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        # Título
        title = QLabel("OXIA")
        title.setAlignment(Qt.AlignCenter)
        font = QFont("Arial", 32, QFont.Bold)
        title.setFont(font)
        title.setStyleSheet("color: white; letter-spacing: 5px;")
        
        # Resplandor del Título
        title_glow = QGraphicsDropShadowEffect(self)
        title_glow.setBlurRadius(30)
        title_glow.setColor(QColor(0, 255, 255))
        title_glow.setOffset(0, 0)
        title.setGraphicsEffect(title_glow)
        
        layout.addWidget(title)
        layout.addSpacing(30)

        # Botones
        btn_pvp = NeonButton("JUGADOR VS IA", self.start_game_callback, "ai")
        layout.addWidget(btn_pvp)
        
        btn_pvia = NeonButton("JUGADOR VS JUGADOR", self.start_game_callback, "pvp")
        layout.addWidget(btn_pvia)
        
        # Botón de Salir
        btn_exit = NeonButton("SALIR", lambda _: QApplication.quit(), "exit")
        btn_exit.setStyleSheet(f"""
            QPushButton {{
                color: white;
                background-color: rgba(0, 0, 0, 150);
                border: 2px solid #FF0064; 
                border-radius: 10px;
                padding: 10px;
                margin: 5px;
            }}
            QPushButton:hover {{
                background-color: #FF0064;
                color: black;
            }}
        """)
        # Resplandor Rojo Específico para Salir
        exit_glow = QGraphicsDropShadowEffect(btn_exit)
        exit_glow.setBlurRadius(20)
        exit_glow.setColor(QColor(255, 0, 100))
        exit_glow.setOffset(0, 0)
        btn_exit.setGraphicsEffect(exit_glow)
        
        layout.addWidget(btn_exit)

class NeonCell(QPushButton):
    def __init__(self, index, click_callback):
        super().__init__("")
        self.index = index
        self.click_callback = click_callback
        self.setFixedSize(110, 110) # 110px tamaño para diseño compacto
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont("Arial", 56, QFont.Bold))
        
        # Estilo Predeterminado
        self.default_border = QColor(0, 255, 255, 50) # Cian Tenue
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 2px solid {self.default_border.name(QColor.HexArgb)};
                border-radius: 5px;
            }}
        """)
        self.clicked.connect(lambda: self.click_callback(self.index))
        
    def set_marker(self, marker_type):
        # marker_type: "X" (Rojo), "O" (Azul), o "" (Vacío)
        self.setText(marker_type)
        
        if marker_type == "X":
            color = QColor(255, 0, 100) # Rojo/Rosa Neón
        elif marker_type == "O":
            color = QColor(0, 200, 255) # Azul/Cian Neón
        else:
            self.setGraphicsEffect(None)
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: 2px solid {self.default_border.name(QColor.HexArgb)};
                    border-radius: 5px;
                }}
            """)
            return

        # Aplicar Resplandor
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(40)
        glow.setColor(color)
        glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)
        
        # Aplicar CSS
        self.setStyleSheet(f"""
            QPushButton {{
                color: {color.name()};
                background-color: rgba(0, 0, 0, 50);
                border: 2px solid {color.name()};
                border-radius: 5px;
            }}
        """)

class NeonScoreLabel(QLabel):
    def __init__(self, text, color):
        super().__init__(text)
        self.color = color
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Arial", 20, QFont.Bold)) # Aumentado de 14 a 20
        self.setStyleSheet(f"color: {color.name()}; border: 2px solid {color.name()}; border-radius: 5px; padding: 5px;")
        
        # Resplandor
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(20)
        glow.setColor(color)
        glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)

class TicTacToeGame(QWidget):
    def __init__(self, back_to_menu_callback):
        super().__init__()
        self.back_to_menu_callback = back_to_menu_callback
        self.layout = QVBoxLayout()
        # Eliminado Qt.AlignCenter para permitir espaciado vertical manual
        self.setLayout(self.layout)
        
        self.layout.addSpacing(5) # Espaciado superior mínimo

        # Etiqueta de Estado
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 18, QFont.Bold)) # Fuente más pequeña para diseño compacto
        self.status_label.setStyleSheet("color: white; letter-spacing: 2px;")
        # Efecto de Resplandor para estado
        status_glow = QGraphicsDropShadowEffect(self)
        status_glow.setBlurRadius(20)
        status_glow.setColor(QColor(255, 255, 255))
        status_glow.setOffset(0, 0)
        self.status_label.setGraphicsEffect(status_glow)
        
        self.layout.addWidget(self.status_label)
        self.layout.addSpacing(5)

        # Diseño de cuadrícula para el tablero
        self.board_widget = QWidget()
        # 3 celdas * 110px + 2 espacios * 10px = 330 + 20 = 350. 
        self.board_widget.setFixedSize(350, 350) 
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(0, 0, 0, 0) 
        self.board_widget.setLayout(self.grid_layout)
        
        # Centrar el tablero
        board_container = QHBoxLayout()
        board_container.addStretch()
        board_container.addWidget(self.board_widget)
        board_container.addStretch()
        self.layout.addLayout(board_container)

        self.layout.addSpacing(20)

        # Barra Inferior (Botón Atrás + Marcador)
        bottom_bar = QHBoxLayout()
        
        # Espaciador
        bottom_bar.addSpacing(20) 
        
        # Botón Atrás (Flecha Llena)
        self.btn_back = NeonButton("◀", self.return_to_menu, "back")
        self.btn_back.setFixedSize(60, 60)
        self.btn_back.setFont(QFont("Arial", 28, QFont.Bold))
        bottom_bar.addWidget(self.btn_back)
        
        bottom_bar.addStretch() 
        
        # Marcador
        self.score_x = NeonScoreLabel("X: 0", QColor(255, 0, 100)) # Rojo
        self.score_o = NeonScoreLabel("O: 0", QColor(0, 200, 255)) # Azul
        
        bottom_bar.addWidget(self.score_x)
        bottom_bar.addSpacing(10)
        bottom_bar.addWidget(self.score_o)
        
        self.layout.addLayout(bottom_bar)
        
        # Estiramiento inferior reducido
        self.layout.addSpacing(10) 

        self.buttons = []
        self.AI_MARKER = [0, 0, 1]
        self.PLAYER_MARKER = [0, 1, 0]
        self.PLAYER2_MARKER = [0, 0, 1] 
        self.EMPTY_MARKER = [1, 0, 0]
        self.state_size = 27
        
        self.game_mode = "ai" 
        self.current_player_symbol = "O" 
        
        # Colores
        self.color_x = "#FF0064" # Rojo Neón
        self.color_o = "#00C8FF" # Azul Neón
        self.color_white = "white"

        # Sonido de Click
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        ruta_sonido = os.path.join(BASE_DIR, "click.wav")
        self.sonido_clic = QSoundEffect()
        self.sonido_clic.setSource(QUrl.fromLocalFile(ruta_sonido))
        self.sonido_clic.setVolume(1.0)  # Volumen al máximo (0.0 a 1.0)

        # Sonido de Victoria
        ruta_win = os.path.join(BASE_DIR, "win.wav")
        self.sonido_ganar = QSoundEffect()
        self.sonido_ganar.setSource(QUrl.fromLocalFile(ruta_win))
        self.sonido_ganar.setVolume(1.0)

        # Sonido de Derrota
        ruta_lose = os.path.join(BASE_DIR, "lose.wav")
        self.sonido_perder = QSoundEffect()
        self.sonido_perder.setSource(QUrl.fromLocalFile(ruta_lose))
        self.sonido_perder.setVolume(1.0)

        # Puntuaciones
        self.scores = {"X": 0, "O": 0}
        
        self.init_board_ui()

    def return_to_menu(self, mode=None):

        self.game_over = True 
        self.reset_board() 
        self.scores = {"X": 0, "O": 0} 
        self.update_scoreboard()
        self.back_to_menu_callback()


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(10, 10, 30)) 
        pen = QPen(QColor(0, 255, 255, 30)) 
        pen.setWidth(1)
        painter.setPen(pen)
        grid_size = 40
        for x in range(0, self.width(), grid_size):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), grid_size):
            painter.drawLine(0, y, self.width(), y)

    def init_board_ui(self):
        self.buttons = []
        for i in range(9):
            btn = NeonCell(i, self.handle_click)
            self.grid_layout.addWidget(btn, i // 3, i % 3)
            self.buttons.append(btn)

    def start_game(self, mode=None):
        # mode puede ser None si se llama desde el temporizador
        if mode:
            self.game_mode = mode
        
        self.reset_board()
        self.update_ui()
        
        if self.game_mode == "ai":
            self.turn = random.choice(["user", "ai"])
            if self.turn == "ai":
                QTimer.singleShot(500, self.ai_move) 
            else:
                 self.status_label.setText("Turno: Jugador")
                 self.status_label.setStyleSheet(f"color: {self.color_o}; letter-spacing: 2px;")
        else:
            self.turn = "player1" 
            self.status_label.setText("Turno: O")
            self.status_label.setStyleSheet(f"color: {self.color_o}; letter-spacing: 2px;") 

    def reset_board(self):
        self.board = [list(self.EMPTY_MARKER) for _ in range(9)]
        self.game_over = False
        self.status_label.setText("") # Limpiar estado
        self.update_ui() # Asegurar visual limpio

    def handle_click(self, idx):
        if self.game_over:
            return

        if self.board[idx] != self.EMPTY_MARKER:
            return

        # Determinar marcador actual basado en el turno
        current_marker = self.PLAYER_MARKER
        if self.game_mode == "pvp" and self.turn == "player2":
             current_marker = self.AI_MARKER 
        
        if self.game_mode == "ai" and self.turn != "user":
            return

        self.sonido_clic.play()

        # Realizar movimiento
        self.board[idx] = list(current_marker)
        self.update_ui()

        if self.check_winner(current_marker):
            # Determinar identidad del ganador para puntuación
            if self.turn == "user" or self.turn == "player1":
                self.end_game("O") # Jugador 1 es O
            else:
                self.end_game("X") # IA/P2 es X
            return

        if self.is_full():
            self.end_game("Empate")
            return

        if self.game_mode == "ai":
            self.turn = "ai"
            self.status_label.setText("Turno: IA")
            self.status_label.setStyleSheet(f"color: {self.color_x}; letter-spacing: 2px;") 
            QTimer.singleShot(500, self.ai_move) 
        elif self.game_mode == "pvp":
            self.turn = "player2" if self.turn == "player1" else "player1"
            is_p2 = (self.turn == "player2")
            turn_name = 'X' if is_p2 else 'O'
            color = self.color_x if is_p2 else self.color_o
            self.status_label.setText(f"Turno: {turn_name}")
            self.status_label.setStyleSheet(f"color: {color}; letter-spacing: 2px;")

    def ai_move(self):
        if self.game_over or not model or self.turn != "ai":
            return
            
        state = np.array(self.board).flatten().reshape(1, self.state_size)
        act_values = model.predict(state, verbose=0)
        action = np.argmax(act_values[0])
        
        # Si está ocupado, encontrar el siguiente libre
        if self.board[action] != self.EMPTY_MARKER:
            free = [i for i, v in enumerate(self.board) if v == self.EMPTY_MARKER]
            if free:
                action = random.choice(free)
            else:
                self.end_game("Empate")
                return

        self.board[action] = list(self.AI_MARKER)
        self.update_ui()
        
        if self.check_winner(self.AI_MARKER):
            self.end_game("X")
            return
            
        if self.is_full():
            self.end_game("Empate")
            return
            
        self.turn = "user"
        self.status_label.setText("Turno: Jugador")
        self.status_label.setStyleSheet(f"color: {self.color_o}; letter-spacing: 2px;")

    def update_ui(self):
        for i, btn in enumerate(self.buttons):
            if self.board[i] == self.AI_MARKER:
                btn.set_marker("X") 
            elif self.board[i] == self.PLAYER_MARKER:
                btn.set_marker("O") 
            else:
                btn.set_marker("")

    def check_winner(self, marker):
        b = self.board
        win_patterns = [
            [0,1,2],[3,4,5],[6,7,8], # filas
            [0,3,6],[1,4,7],[2,5,8], # columnas
            [0,4,8],[2,4,6]          # diagonales
        ]
        for pattern in win_patterns:
            if all(b[i] == marker for i in pattern):
                return True
        return False

    def is_full(self):
        return all(cell != self.EMPTY_MARKER for cell in self.board)

    def end_game(self, winner):
        self.game_over = True
        
        if winner == "X":
            self.sonido_perder.play()
            self.scores["X"] += 1
            self.status_label.setText("¡GANADOR: X!")
            self.status_label.setStyleSheet("color: #FF0066; letter-spacing: 2px;") # Rojo Neón
        elif winner == "O":
            self.sonido_ganar.play()
            self.scores["O"] += 1
            self.status_label.setText("¡GANADOR: O!")
            self.status_label.setStyleSheet("color: #00FFFF; letter-spacing: 2px;") # Azul Neón
        else: # Empate
            self.sonido_perder.play()
            self.status_label.setText("¡EMPATE!")
            self.status_label.setStyleSheet("color: white; letter-spacing: 2px;")
        
        self.update_scoreboard()
        
        # Auto-reinicio después del retraso
        QTimer.singleShot(1500, lambda: self.start_game(None))

    def update_scoreboard(self):
        self.score_x.setText(f"X: {self.scores['X']}")
        self.score_o.setText(f"O: {self.scores['O']}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OXIA")
        self.setFixedSize(440, 600) # Resolución compacta
        self.setWindowFlags(Qt.FramelessWindowHint) # Sin bordes
        
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        self.main_menu = MainMenu(self.start_game)
        self.game_widget = TicTacToeGame(self.show_menu)
        
        self.stacked_widget.addWidget(self.main_menu)
        self.stacked_widget.addWidget(self.game_widget)
        
        self.show_menu()
        
        # Lógica de arrastre de ventana
        self.old_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def show_menu(self):
        self.stacked_widget.setCurrentWidget(self.main_menu)

    def start_game(self, mode):
        self.game_widget.start_game(mode)
        self.stacked_widget.setCurrentWidget(self.game_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.raise_()
    window.activateWindow()
    sys.exit(app.exec())