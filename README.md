# Chinese Chess AI System

A full-stack Chinese Chess game system built with React and Python. This project includes not only a complete chess rules engine but also an AI opponent brain integrating Minimax (Alpha-Beta Pruning) and MCTS (Monte Carlo Tree Search).

## 🌟 Core Features

- **🎮 Modern Frontend Interface**: Visual chessboard built with React + TailwindCSS, supporting a seamless interactive experience, valid move hints, and move history.
- **🧠 Multi-Algorithm AI Engine**:
  - **Alpha-Beta Pruning**: Traditional efficient search combined with Zobrist Hashing and Position Value Matrices.
  - **MCTS (Monte Carlo Tree Search)**: Self-play simulation supporting the UCT algorithm.
- **📐 Strict Rules Engine**: Fully implements the complex rules of Chinese Chess (e.g., horse blocking, elephant blocking/eyes, flying general/kings cannot face each other, etc.).
- **💾 Endgame Loading System**: Supports reading and configuring complex endgame states (e.g., JJ Chess Endgames).

## 📁 Directory Structure

- `/frontend` - React visual interaction layer
- `/backend` - Python core game logic and AI algorithms

## 🚀 Quick Start

### Frontend (UI)

``` bash
cd frontend
npm install
npm run dev
```

### Backend (AI Engine)

```
cd backend
pip install -r requirements.txt
python draft.py
```

## 🛠️ Tech Stack

- **Frontend**: React, Vite, TailwindCSS
- **Backend**: Python 3.x
- **Algorithms**: Minimax, Alpha-Beta Pruning, Monte Carlo Tree Search (MCTS), Zobrist Hashing

## 📝 TODO List

- [x] Complete basic rules engine (Phase 1)
- [x] Implement Minimax search tree
- [ ] Integrate frontend-backend API communication (Phase 2)
- [ ] Introduce CNN neural network evaluation function (Phase 3)