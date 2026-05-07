from ..BoardGame import Player
from .ChineseChessBoard import ChineseChessBoard
from .ChineseChessStatus import ChineseChessGameStatus
from .ChineseChessAction import ChineseChessAction, ChineseChessMoveAction
from .ChineseChessUtils import ChineseChessSide, ChineseChessType
from .ChineseChessRule import getAllPossibleMoveActions
from ..structs import Location
from termcolor import colored
from .BoardHashTable import BoardHashTable
import random
from typing import List, Tuple, Optional
import time

class ChineseChessPlayer(Player):
    def __init__(self, name, level:int = 1):
        super().__init__(name, level)
        self.side = None

    def prepare(self) -> bool:
        if super().prepare() is False:
            return False
        return True

    def set_side(self, side: ChineseChessSide):
        self.side = side

    def print_playing_info(self, status: ChineseChessGameStatus):
        if status.color == "绿":
            self.print_info(f"正在下{colored('绿', 'green')}棋")
        elif status.color == "红":
            self.print_info(f"正在下{colored('红', 'red')}棋")
        else:
            self.print_info("playing chess")

    # TODO: 考虑无棋可走的情况：可以返回一个认输Action。
    def play(self, status: ChineseChessGameStatus) -> ChineseChessAction:
        self.print_playing_info(status)

        # 随机移动棋子
        actions = getAllPossibleMoveActions(status.board, status.side)
        action = random.choice(actions)
        self.print_info(f"计划把{action.item}从{action.from_}移动到{action.to_}")
        return action


from .ChineseChessNNEvaluator import ChineseChessNNEvaluator

class ChineseChessAIPlayer(ChineseChessPlayer):
    def __init__(self, name, level:int = 1):
        super().__init__(name, level)
        self.evaluator = ChineseChessNNEvaluator() # <--- 换上了神经网络大脑！

    # TODO: 考虑无棋可走的情况：可以返回一个认输Action。
    def play(self, status: ChineseChessGameStatus) -> ChineseChessAction:
        assert(self.side == status.side)
        self.print_playing_info(status)

        actions = getAllPossibleMoveActions(status.board, status.side)

        max_score = 0
        max_score_action = None
        opposite_side = ChineseChessSide.DOWN if self.side == ChineseChessSide.UP else ChineseChessSide.UP

        for action in actions:
            status.board.run(action.item, action.from_, action.to_, action.captured_item)
            self.evaluator.set_status(opposite_side)
            score = 1 - self.evaluator.evaluateBoard(status.board)
            status.board.roll_back(action.item, action.from_, action.to_, action.captured_item)
            if score >= max_score:
                max_score = score
                max_score_action = action

        action = max_score_action
        self.print_info(f"下一步最高的评估分数为{max_score * 100.0} / 100")

        self.print_info(f"计划把{action.item}从{action.from_}移动到{action.to_}")
        return action


# TODO: move to BoardGame.py
class BoardHashTable():
    def __init__(self, type_number, location_number, N):
        random.seed(10)
        self.type_number = type_number  # 棋子种类
        self.location_number = location_number  # 位置总数
        self.N = N  # 置换表中可存储棋盘的总数为2^N
        self.board_number = (2 ** N)
        self.lock_list = self.create_random_list()
        self.key_list = self.create_random_list()
        self.hash = {}
        self.side = None
        self.hit_cache_counter = 0
        self.conflict_counter = 0


    # TODO: 将hash从字典换成数组
    # TODO: 局面的评估对不同side是可以对等的吗？需要保证evaluation函数的对称性，即evaluate(board, side) = 1 - evaluate(board, opposite_side)
    # NOTE: side为当前局面先手。
    def get_score(self, lock: int, key: int, min_level: int, side: ChineseChessSide) -> Optional[float]:
        if self.side is None:
            return None

        if key in self.hash and ('lock' in self.hash[key]) and (self.hash[key]['lock'] == lock):
            if self.hash[key]['level'] >= min_level:
                self.hit_cache_counter += 1
                if self.hash[key]['score'] == None:
                    return 1.0
                if side == self.side:
                    return self.hash[key]['score']
                else:
                    return 1 - self.hash[key]['score']
        else:
            return None

    def set_score(self, lock: int, key: int, score: float, level: int, side: ChineseChessSide) -> bool:
        if self.side is None:
            self.side = side
        elif self.side != side:
            score = 1 - score

        # print(f"lock: {lock}, key: {key}, score: {score}, level: {level}")
        if key not in self.hash:
            self.hash[key] = {}
            data = self.hash[key]
        else:
            data = self.hash[key]
            if data['lock'] == lock and data['level'] > level:
                return False
            elif data['lock'] != lock:
                self.conflict_counter += 1

        data['lock'] = lock
        data['level'] = level
        data['score'] = score

        return True

    def create_random_list(self):
        result = []
        # factor = 100000007
        for i in range(self.type_number * self.location_number):
            rnd = random.randrange(self.board_number)
            result.append(rnd)
        return result

    # TODO: how to cache functions
    def get_type_id(self, item) -> int:
        type_map = {
            ChineseChessType.JU: 0,
            ChineseChessType.MA: 1,
            ChineseChessType.PAO: 2,
            ChineseChessType.XIANG: 3,
            ChineseChessType.SHI: 4,
            ChineseChessType.JIANG: 5,
            ChineseChessType.ZU: 6,
        }
        color_map = {
            "红": 0,
            "绿": 7,
        }
        return type_map[item.type_] + color_map[item.color]

    # TODO: how to cache functions
    def get_id(self, item, loc, width=9):
        if loc:
            type_id = self.get_type_id(item)
            loc_id = loc.y * width + loc.x
            id_ = type_id * self.location_number + loc_id
            return id_
        else:
            return None

    def gen_key_for_board(self, board) -> Tuple[int, int]:
        key = 0
        lock = 0

        for item in board.items.values():
            id_ = self.get_id(item, board.get_location(item))
            if id_:
                key = key ^ self.key_list[id_]
                lock = lock ^ self.lock_list[id_]
        return (lock, key)

    def gen_key_for_action(self, previous_lock, previous_key, action) -> Tuple[int, int]:
        id_ = self.get_id(action.item, action.from_)
        previous_lock = previous_lock ^ self.key_list[id_]
        previous_key = previous_key ^ self.lock_list[id_]

        id_ = self.get_id(action.item, action.to_)
        previous_lock = previous_lock ^ self.key_list[id_]
        previous_key = previous_key ^ self.lock_list[id_]

        if action.captured_item:
            id_ = self.get_id(action.captured_item, action.to_)
            previous_lock = previous_lock ^ self.key_list[id_]
            previous_key = previous_key ^ self.lock_list[id_]

        return (previous_lock, previous_key)

    # # TODO:
    # def gen_key_for_action_reverse(self, previous_lock, previous_key, action) -> Tuple[int, int]:
    #     return previous_key


class ChineseChessMaxMinAIPlayer(ChineseChessAIPlayer):
    def __init__(self, name, search_level, level:int = 1):
        super().__init__(name, level)
        self.search_level = search_level
        self.branch_limit = 4  # 新增默认分支宽度

    def prepare(self) -> bool:
        if super().prepare() is False:
            return False
        self.hash_table = BoardHashTable(14, 90, 20)
        return True

    # 当前棋局，以side为先手，所有action中，让side获得最高分的走法
    def search(self, board: ChineseChessBoard, lock: int, key: int, side: ChineseChessSide, search_level: int, threshold_max: float = 1, tree_node: dict = None) -> Tuple[ChineseChessAction, float]:
        assert search_level >= 1

        actions = getAllPossibleMoveActions(board, side)
        opposite_side = ChineseChessSide.DOWN if side == ChineseChessSide.UP else ChineseChessSide.UP

        direct_scores = {}
        for action in actions:
            board.run(action.item, action.from_, action.to_, action.captured_item)
            (new_lock, new_key) = self.hash_table.gen_key_for_action(lock, key, action)
            t_score = self.hash_table.get_score(new_lock, new_key, 0, opposite_side)
            if t_score is None:
                self.evaluator.set_status(opposite_side)
                t_score = self.evaluator.evaluateBoard(board)
                self.hash_table.set_score(new_lock, new_key, t_score, 0, opposite_side)
                if t_score == None:
                    t_score = 1.0
                self.evaluate_counter += 1
            score = 1 - t_score
            direct_scores[action] = score
            board.roll_back(action.item, action.from_, action.to_, action.captured_item)

        actions = sorted(actions, key=lambda action: 1 - direct_scores[action])

        assert len(actions) >= 0
        max_score = 0
        max_score_action = actions[0] if actions else None
        
        # 读取动态分支宽度限制
        max_tree_branches = getattr(self, 'branch_limit', 4)
        branch_count = 0

        for action in actions:
            child_node = None
            if tree_node is not None and branch_count < max_tree_branches:
                captured_stmt = f"\n吃{action.captured_item.name}" if action.captured_item else ""
                child_node = {
                    'action': f"{action.item.name} {action.from_}->{action.to_}{captured_stmt}",
                    'pruned': False,
                    'score': None,
                    'type': 'min' if side == self.side else 'max',
                    'children': []
                }
                tree_node['children'].append(child_node)
                branch_count += 1

            board.run(action.item, action.from_, action.to_, action.captured_item)

            direct_score = direct_scores[action]
            if search_level > 1 and direct_score != 1 and direct_score != 0:
                (new_lock, new_key) = self.hash_table.gen_key_for_action(lock, key, action)
                t_score = self.hash_table.get_score(new_lock, new_key, search_level - 1, opposite_side)
                if t_score is None:
                    (t_action, t_score) = self.search(board, new_lock, new_key, opposite_side, search_level - 1, 1 - max_score, tree_node=child_node)
                else:
                    # 命中缓存的节点可视化
                    if child_node is not None:
                        child_node['children'].append({
                            'action': '⚡命中缓存\n(Cache Hit)',
                            'pruned': False,
                            'score': 1 - t_score,
                            'type': 'min' if side == self.side else 'max',
                            'children': []
                        })
                score = 1 - t_score
            else:
                score = direct_score

            if child_node is not None:
                child_node['score'] = score

            board.roll_back(action.item, action.from_, action.to_, action.captured_item)

            if score > max_score:
                max_score = score
                max_score_action = action

            if max_score >= threshold_max:
                if child_node is not None:
                    child_node['pruned'] = True
                return (max_score_action, max_score)

        self.hash_table.set_score(lock, key, max_score, search_level, side)
        return (max_score_action, max_score)

    # TODO: 考虑无棋可走的情况：可以返回一个认输Action。
    def play(self, status: ChineseChessGameStatus) -> ChineseChessAction:
        assert(self.side == status.side)
        self.print_playing_info(status)

        import time
        start = time.time()

        self.evaluate_counter = 0
        self.hash_table.hit_cache_counter = 0
        self.hash_table.conflict_counter = 0

        (lock, key) = self.hash_table.gen_key_for_board(status.board)
        
        # 初始化根节点用于可视化
        root_node = {
            'action': '当前局面\n(Root)',
            'pruned': False,
            'score': None,
            'type': 'max',
            'children': []
        }
        
        (action, max_score) = self.search(status.board, lock, key, status.side, self.search_level, tree_node=root_node)
        root_node['score'] = max_score
        
        # 将 JSON 树存入实例变量供 FastAPI 读取
        self.last_tree_data = root_node  

        end = time.time()

        evaluate_counter = self.evaluate_counter
        hit_cache_counter = self.hash_table.hit_cache_counter
        board_counter = evaluate_counter + hit_cache_counter
        hit_cache_ratio = hit_cache_counter * 100.0 / board_counter if board_counter > 0 else 0
        conflict_counter = self.hash_table.conflict_counter
        print(f"\n[系统监控] 下一步最高的评估分数为{round(max_score * 100.0, 2)} / 100，计算用时：{round(end - start, 2)}秒，评估局面{evaluate_counter}次，使用缓存{hit_cache_counter}次({round(hit_cache_ratio, 2)}%)，哈希冲突{conflict_counter}次。")

        self.print_info(f"计划把{action.item}从{action.from_}移动到{action.to_}")
        return action