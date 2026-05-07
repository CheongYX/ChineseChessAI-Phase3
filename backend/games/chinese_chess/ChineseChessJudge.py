from typing import List
from ..BoardGame import Judge
from .ChineseChessStatus import ChineseChessGameStatus
from .ChineseChessConfig import ChineseChessGameConfig
from .ChineseChessAction import ChineseChessAction, ChineseChessMoveAction
from .ChineseChessPlayer import ChineseChessPlayer
from .ChineseChessUtils import ChineseChessSide, down
# ⚠️ 注意：注释掉 getch，防止在 FastAPI 全栈模式下阻塞终端导致服务器卡死
# from ..utils import getch 

class ChineseChessJudge(Judge):
    def __init__(self, config: ChineseChessGameConfig, level: int = 1):
        name = "中国象棋裁判"
        super().__init__(config, name, level)

    def validate_action(self, action: ChineseChessAction, status: ChineseChessGameStatus) -> bool:
        return True

    def control_process(self, status: ChineseChessGameStatus) -> bool:
        # ⚠️ 在网页 API 模式下，所有的悔棋(r)和保存(s)都已经交给前端 React 控制
        # 这里直接 return False，放行程序，绝对不能用 getch() 阻塞
        return False

    def next_player(self, status: ChineseChessGameStatus) -> None:
        status.color = "绿" if status.color == "红" else "红"
        status.side = ChineseChessSide.DOWN if status.side == ChineseChessSide.UP else ChineseChessSide.UP
        status.switch((status.turns_count)%2)

    def check_end(self, status: ChineseChessGameStatus, players: List[ChineseChessPlayer]) -> bool:
        assert len(players) == 2, f"ChineseChessGame MUST have 2 players, {len(players)} are given"

        # 屏蔽终端的按键等待逻辑
        # if self.config.wait_each_turn:
        #     if self.control_process(status):
        #         return True

        if status.turns_count >= self.config.max_turns:
            return True

        # 判断是否一方已经没有将帅
        sides = [ChineseChessSide.UP, ChineseChessSide.DOWN]
        for side in sides:
            king_loc = status.board.get_king_location(side)
            if king_loc is None:
                status.game_end = True
                status.winner_names = [p.name for p in players if p.side != side]
                return True

        # 判断将帅是否见面
        if status.board.check_king_meet():
            status.game_end = True
            current_player_id = status.current_player_id
            # 当前玩家下完后，导致了将帅碰面的情况，所以当前玩家的对手是winner。
            status.winner_names = [players[0].name if current_player_id == 1 else players[1].name]
            return True

        return False

    def printMoveAction(self, action, is_roll_back = False):
        prefix = "撤回" if is_roll_back else ""
        suffix = f"，并吃掉{action.captured_item}。" if action.captured_item else ""
        self.print_info(f"{prefix}把{action.item}从{action.from_}移动到{action.to_}{suffix}")

    def run(self, player: ChineseChessPlayer, action: ChineseChessAction, status: ChineseChessGameStatus) -> bool:

        board = status.board

        # 判断是否未移动
        if action.from_ == action.to_:
            self.print_info(f"把{action.item}从{action.from_}移动到{action.to_}不合法，{player}重玩")
            return False

        board.run(action.item, action.from_, action.to_, action.captured_item)

        # 保存走法
        status.push(action)

        self.printMoveAction(action)

        if self.config.silent_mode is False:
            status.board.print()
        return True