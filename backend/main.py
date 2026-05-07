from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os

# 导入游戏核心组件
from games.chinese_chess.ChineseChessGame import ChineseChessGame
from games.chinese_chess.ChineseChessConfig import ChineseChessGameConfig
from games.chinese_chess.ChineseChessPlayer import ChineseChessMaxMinAIPlayer
from games.chinese_chess.ChineseChessUtils import ChineseChessSide
from games.structs import Location
from games.chinese_chess.Visualizer import AIVisualizer
from games.chinese_chess.ChineseChessNNEvaluator import ChineseChessNNEvaluator

app = FastAPI()

# 配置 CORS，允许 React 前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 定义接收前端数据的结构体
class MoveRequest(BaseModel):
    from_x: int
    from_y: int
    to_x: int
    to_y: int
    depth: int = 3
    branch_limit: int = 4
    session_id: str = "DefaultSession"
    turn_count: int = 1

# ==========================================
# 全局游戏状态初始化 (包含 CNN 注入)
# ==========================================
config = ChineseChessGameConfig(silent_mode=True)
ai_player = ChineseChessMaxMinAIPlayer("AI_Black", search_level=3)
ai_player.set_side(ChineseChessSide.UP) # AI 执黑 (上方)

# 🌟 核心：注入 CNN 神经网络评估器 🌟
nn_evaluator = ChineseChessNNEvaluator()
ai_player.evaluator = nn_evaluator

# 初始化一局游戏
game = ChineseChessGame([ai_player, ai_player], config) 
game.prepare()
game_status = game.status
board = game.status.board

@app.post("/api/move")
def play_move(move: MoveRequest):
    global game_status, board, ai_player, nn_evaluator
    
    # 1. 解析并执行玩家 (红方) 的走步
    from_loc = Location(move.from_x, move.from_y)
    to_loc = Location(move.to_x, move.to_y)
    player_item = board.get_chess(from_loc)
    captured_item = board.get_chess(to_loc)
    
    if not player_item:
        return {"status": "error", "error": "起始位置没有棋子！请检查状态同步。"}
        
    board.run(player_item, from_loc, to_loc, captured_item)
    
    # 切换轮次给 AI
    game_status.side = ChineseChessSide.UP 
    
    # 2. AI 开始思考 (动态应用前端传来的深度与宽度限制)
    ai_player.search_level = move.depth
    ai_player.branch_limit = move.branch_limit
    ai_action = ai_player.play(game_status)
    
    if not ai_action:
        return {"status": "game_over", "message": "AI 算力耗尽，已无合法走步，玩家绝杀！"}

    # 3. 执行 AI 的动作
    board.run(ai_action.item, ai_action.from_, ai_action.to_, ai_action.captured_item)
    game_status.side = ChineseChessSide.DOWN # 交还给玩家
    
    # 4. 获取决策树 JSON 数据并存入本地硬盘
    tree_data = getattr(ai_player, 'last_tree_data', None)
    if tree_data:
        try:
            AIVisualizer.save_search_tree_local(tree_data, move.session_id, move.turn_count)
        except Exception as e:
            print(f"[警告] 决策树落盘失败: {e}")
            
    # 🌟 5. 生成 CNN 热力图 (保存到本地 + 传回前端) 🌟
    heatmap_b64 = None
    try:
        heatmap_b64 = AIVisualizer.generate_gradcam_heatmap(nn_evaluator, board, move.session_id, move.turn_count)
        if heatmap_b64:
            print(f"[视觉追踪] 📸 CNN 热力特征图已捕获并发送至前端。")
    except Exception as e:
        print(f"[警告] 热力图生成失败: {e}")
    
    # 6. 返回数据给前端
    return {
        "status": "success",
        "ai_move": {
            "from_x": ai_action.from_.x,
            "from_y": ai_action.from_.y,
            "to_x": ai_action.to_.x,
            "to_y": ai_action.to_.y,
            "piece": ai_action.item.name
        },
        "visualizations": {
            "heatmap": heatmap_b64,  # 将生成的 Heatmap Base64 返回给前端展示
            "tree": None             # 树图已经落盘，不占用网络带宽
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)