# Chinese Chess AI System - Full-Stack Chess Engine with XAI Visualization

This is an experimental Chinese Chess AI sandbox built on a modern full-stack architecture (React + FastAPI). Evolving from a traditional heuristic search engine (Minimax + Alpha-Beta pruning), this project deeply integrates state caching (Zobrist Hashing) and Deep Learning (PyTorch CNN) evaluation modules, while introducing a pioneering **offline algorithmic visualization (XAI)** engine.

## ✨ Core Features

### 1. Extremely Decoupled Full-Stack Architecture
* **Frontend (React):** A pure view layer and interaction engine. It abandons redundant animations to provide a controlled, dashboard-style monitoring interface. It supports dynamic adjustments of the AI's **Search Depth** and **Branch Limit**.
* **Backend (FastAPI):** Handles high-concurrency computational loads and core game logic, effectively isolating frontend performance bottlenecks (e.g., browser memory limits when rendering massive DOM nodes).

### 2. Efficient Heuristic Engine & State Caching
* **Alpha-Beta Pruning:** Integrated with the Minimax algorithm to effectively intercept meaningless branches during ultra-deep searches.
* **Zobrist Hashing (Transposition Table):** Utilizes 64-bit hash fingerprints to cache evaluated board states. It achieves an impressive 20%+ Cache Hit rate in deep matches with zero hash collisions, enabling $O(1)$ time complexity for state reuse.

### 3. Explainable AI (XAI) Visual Engine
To break the "black box" nature of AI decision-making, the system features a custom built `AIVisualizer` offline rendering engine:
* **High-Res Decision Tree Archiving:** After every AI move, the backend uses `matplotlib` to automatically render and physically save the complete game tree. It accurately tags **Pruned Nodes (✂️)** and **Cache Hit Nodes (⚡ Yellow)**.
* **CNN Spatial Attention (Grad-CAM):** Phase 3 introduces a Convolutional Neural Network. By extracting gradients through real-time forward and backward passes, it reduces the dimensionality of high-level feature maps into a 10x9 board heatmap, visually demonstrating the AI's spatial attention distribution for its current decision.


## 📸 Showcase

![Minimalist Frontend Console: Supports Player ID session isolation and real-time status monitoring.](/frontend/public/images/frontend.png)
*Minimalist Frontend Console: Supports Player ID session isolation and real-time status monitoring.*

![Offline Computational Graph: Accurately records the algorithmic pruning loss-stops and cache reuse mechanisms.](/backend/data/sessions/CYX_20260507_114743/第4回合_Tree.png)
*Offline Computational Graph: Accurately records the algorithmic pruning loss-stops and cache reuse mechanisms.*

![Spatial Attention Distribution: Showcases the focal evaluation of board positions by the CNN model.](/backend/data/sessions/CYX_20260507_114743/第4回合_Heatmap.png)
*Spatial Attention Distribution: Showcases the focal evaluation of board positions by the CNN model.*

## 📂 Project Structure

```text
ChineseChessAI/
├── frontend/                # React View Layer
│   ├── src/
│   │   └── App.jsx          # Core console UI and logic interception
│   └── package.json
├── backend/                 # FastAPI Computational Layer
│   ├── main.py              # Core API routing and game engine dispatch
│   ├── games/
│   │   └── chinese_chess/   # Chess rule engine, state machine, and AI logic
│   │       ├── ChineseChessNNEvaluator.py # CNN evaluator and tensor conversion
│   │       ├── ChineseChessPlayer.py      # Minimax & Alpha-Beta search brain
│   │       └── Visualizer.py              # Matplotlib offline rendering & heatmap engine
│   └── data/
│       └── sessions/        # [Auto-generated] Stores all offline logs and high-res decision tree images
└── README.md
```




### 2. Start the Frontend (React)

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server (runs on http://localhost:3000 by default)
npm start
```

### 3. Run the Experiment
1. Open your browser and navigate to `http://localhost:3000`.
2. Enter a **Player ID** (e.g., `WangTianyi`) to establish a unique match session.
3. Adjust the Depth and Branch Limit, and play against the AI.
4. Open the `backend/data/sessions/` directory in your project to view the automatically generated offline high-res game trees and heatmap logs!

---

## 📝 Background & Reflection

This project originally stems from an Object-Oriented Programming (OOP) final assignment during my sophomore year in 2022. After experiencing limitations such as "state desynchronization" and frontend "computational exhaustion," the architecture was completely refactored and rewritten in 2026. 

Acknowledging early code limitations helps better define current engineering growth. The current Phase 3 successfully shifts from pure rule-based heuristics to a "connectionist" feature evaluation, laying a solid physical and logical foundation for future large-scale dataset pre-training.

## 📝 TODO List

- [x] Complete basic rules engine (Phase 1)
- [x] Implement Minimax search tree
- [x] Integrate frontend-backend API communication (Phase 2)
- [x] Introduce CNN neural network evaluation function (Phase 3)