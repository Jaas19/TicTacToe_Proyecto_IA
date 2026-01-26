import numpy as np
import random
from collections import deque
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
import tensorflow as tf


class GameRules:
    @staticmethod
    def check_winner(board, marker, empty_marker):
        rows = [
            board[0:3], board[3:6], board[6:9],
            board[0::3], board[1::3], board[2::3],
            board[0::4], board[2:7:2]
        ]
        for row in rows:
            if row[0] == row[1] == row[2] == marker and row[0] != empty_marker:
                return True
        return False

    @staticmethod
    def is_full(board, empty_marker):
        return not any(tile == empty_marker for tile in board)


class Minimax:
    def __init__(self):
        self.AI = [0, 0, 1]
        self.PLAYER = [0, 1, 0]
        self.EMPTY = [1, 0, 0]

    def get_scores(self, board):
        scores = []
        for i in range(9):
            if board[i] != self.EMPTY:
                scores.append(-999)
            else:
                board[i] = self.AI
                score = self._recursive_solve(board, depth=0, is_ai_turn=False)
                scores.append(score)
                board[i] = self.EMPTY
        return scores

    def _recursive_solve(self, board, depth, is_ai_turn):
        if GameRules.check_winner(board, self.AI, self.EMPTY):
            return 10 - depth
        if GameRules.check_winner(board, self.PLAYER, self.EMPTY):
            return -10 + depth
        if GameRules.is_full(board, self.EMPTY):
            return 0

        if is_ai_turn:
            best_score = -1000
            for i in range(9):
                if board[i] == self.EMPTY:
                    board[i] = self.AI
                    score = self._recursive_solve(board, depth + 1, False)
                    board[i] = self.EMPTY
                    best_score = max(best_score, score)
            return best_score
        else:
            best_score = 1000
            for i in range(9):
                if board[i] == self.EMPTY:
                    board[i] = self.PLAYER
                    score = self._recursive_solve(board, depth + 1, True)
                    board[i] = self.EMPTY
                    best_score = min(best_score, score)
            return best_score


class TicTacToeEnv:
    def __init__(self):
        self.AI_MARKER = [0, 0, 1]
        self.PLAYER_MARKER = [0, 1, 0]
        self.EMPTY_MARKER = [1, 0, 0]

        self.board = []
        self.done = False
        self.difficulty = "minimax"

        self.enemy_brain = Minimax()
        self.enemy_brain.AI = self.PLAYER_MARKER
        self.enemy_brain.PLAYER = self.AI_MARKER

        self.reset()

    def reset(self):
        self.board = [list(self.EMPTY_MARKER) for _ in range(9)]
        self.done = False
        return self._get_flat_state()

    def _get_flat_state(self):
        return np.array(self.board).flatten()

    def step(self, action):
        if self.board[action] != self.EMPTY_MARKER:
            return self._get_flat_state(), -10, True

        self.board[action] = list(self.AI_MARKER)

        if GameRules.check_winner(self.board, self.AI_MARKER, self.EMPTY_MARKER):
            return self._get_flat_state(), 10, True

        if GameRules.is_full(self.board, self.EMPTY_MARKER):
            return self._get_flat_state(), 0, True

        if self.difficulty == "random":
            possible_moves = [i for i, x in enumerate(self.board) if x == self.EMPTY_MARKER]
            if possible_moves:
                enemy_action = random.choice(possible_moves)
            else:
                enemy_action = -1
        else:
            scores = self.enemy_brain.get_scores(self.board)
            enemy_action = np.argmax(scores)

        if enemy_action != -1:
            self.board[enemy_action] = list(self.PLAYER_MARKER)

        if GameRules.check_winner(self.board, self.PLAYER_MARKER, self.EMPTY_MARKER):
            return self._get_flat_state(), -10, True

        if GameRules.is_full(self.board, self.EMPTY_MARKER):
            return self._get_flat_state(), 0, True

        return self._get_flat_state(), 0, False


class DQNAgent:
    def __init__(self, st_size, ac_size):
        self.state_size = st_size
        self.action_size = ac_size
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.999
        self.learning_rate = 0.001
        self.model = self._build_model()

    def _build_model(self):
        model = Sequential()
        model.add(Dense(64, input_dim=self.state_size, activation='relu'))
        model.add(Dense(64, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='mse', optimizer=Adam(learning_rate=self.learning_rate))
        return model

    def act(self, current_state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        act_values = self.model.predict(current_state, verbose=0)
        return np.argmax(act_values[0])

    def remember(self, current_state, action, reward, next_state_val, is_done):
        self.memory.append((current_state, action, reward, next_state_val, is_done))

    def replay(self, batch_size):
        if len(self.memory) < batch_size:
            return
        minibatch = random.sample(self.memory, batch_size)

        states = np.array([i[0] for i in minibatch])
        next_states = np.array([i[3] for i in minibatch])

        states = np.squeeze(states)
        next_states = np.squeeze(next_states)

        targets = self.model.predict(states, verbose=0)
        next_q_values = self.model.predict(next_states, verbose=0)

        for i, (_, action, reward, _, is_done) in enumerate(minibatch):
            target = reward
            if not is_done:
                target = reward + self.gamma * np.amax(next_q_values[i])
            targets[i][action] = target

        self.model.fit(states, targets, epochs=1, verbose=0)

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def save_model(self, name):
        self.model.save(name)

    def load_model(self, name):
        self.model = tf.keras.models.load_model(name)


def main():
    env = TicTacToeEnv()
    state_size = 27
    action_size = 9
    agent = DQNAgent(state_size, action_size)

    episodes = 5000
    batch_size = 32

    print("--- Training Start ---")

    for e in range(episodes):
        if (e // 20) % 2 == 0:
            env.difficulty = "random"
        else:
            env.difficulty = "minimax"

        if e % 20 == 0:
            print(f">>> Cambiando dificultad a: {env.difficulty}")

        state = env.reset()
        state = np.reshape(state, [1, state_size])
        total_reward = 0

        for _ in range(9):
            action = agent.act(state)
            next_state, reward, done = env.step(action)
            next_state = np.reshape(next_state, [1, state_size])

            agent.remember(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward
            if done:
                break

        if len(agent.memory) > batch_size:
            agent.replay(batch_size)

        if (e + 1) % 10 == 0:
            print(
                f"Episodio: {e + 1}/{episodes} ({env.difficulty}), Puntaje: {total_reward}, Epsilon: {agent.epsilon:.2f}")

    print("--- Fin del entrenamiento ---")

    agent.save_model("tictactoe_ia.h5")
    print("Modelo guardado.")

    print("\n--- Juego de demostración ---")
    state = env.reset()
    state = np.reshape(state, [1, state_size])
    done = False

    env.difficulty = "minimax"
    agent.epsilon = 0

    steps = 0
    while not done:
        act_values = agent.model.predict(state, verbose=0)
        action = np.argmax(act_values[0])

        print(f"\nTurno {steps + 1}: IA elige la casilla {action}")
        next_state, reward, done = env.step(action)
        state = np.reshape(next_state, [1, state_size])

        visual_board = []
        for cell in env.board:
            if cell == env.AI_MARKER:
                visual_board.append("X")
            elif cell == env.PLAYER_MARKER:
                visual_board.append("O")
            else:
                visual_board.append(".")

        print(f"{visual_board[0]} {visual_board[1]} {visual_board[2]}")
        print(f"{visual_board[3]} {visual_board[4]} {visual_board[5]}")
        print(f"{visual_board[6]} {visual_board[7]} {visual_board[8]}")

        if done:
            if reward == 10:
                print("Resultado: GANÓ la IA")
            elif reward == -10:
                print("Resultado: GANÓ EL RIVAL")
            else:
                print("Resultado: Empate")
        steps += 1


if __name__ == "__main__":
    main()