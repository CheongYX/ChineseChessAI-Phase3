import random
from .ChineseChessUtils import ChineseChessType, ChineseChessSide

class BoardHashTable:
    def __init__(self, pieces_count=14, positions_count=90, max_depth=20):
        # 性能监控探针
        self.hit_cache_counter = 0
        self.conflict_counter = 0
        self.table = {}
        
        # 核心：生成 64 位的随机数用于 Zobrist 异或哈希
        # 两个维度：0 代表 lock（哈希锁），1 代表 key（校验钥，防止哈希碰撞）
        # 14 种棋子类型，90 个棋盘位置
        self.zobrist_keys = [[[random.getrandbits(64) for _ in range(positions_count)] for _ in range(pieces_count)] for _ in range(2)]

    def _get_piece_index(self, item):
        """将棋子映射为 0-13 的一维索引"""
        type_to_idx = {
            ChineseChessType.JU: 0, ChineseChessType.MA: 1, ChineseChessType.PAO: 2,
            ChineseChessType.XIANG: 3, ChineseChessType.SHI: 4, ChineseChessType.JIANG: 5,
            ChineseChessType.ZU: 6
        }
        idx = type_to_idx[item.type_]
        if item.side == ChineseChessSide.DOWN:
            idx += 7
        return idx

    def _get_pos_index(self, loc):
        """将二维坐标映射为 0-89 的一维位置"""
        return loc.y * 9 + loc.x

    def gen_key_for_board(self, board):
        """从零计算当前棋盘的 Zobrist Hash (仅在第一步时调用)"""
        lock = 0
        key = 0
        for item in board.items.values():
            loc = board.get_location(item)
            if loc:
                p_idx = self._get_piece_index(item)
                pos_idx = self._get_pos_index(loc)
                # 利用异或的特性：A ^ B ^ B = A
                lock ^= self.zobrist_keys[0][p_idx][pos_idx]
                key ^= self.zobrist_keys[1][p_idx][pos_idx]
        return (lock, key)

    def gen_key_for_action(self, lock, key, action):
        """极其高效：通过异或(XOR)增量计算走一步棋后的哈希值，不需要重历棋盘"""
        new_lock = lock
        new_key = key
        
        p_idx = self._get_piece_index(action.item)
        from_idx = self._get_pos_index(action.from_)
        to_idx = self._get_pos_index(action.to_)
        
        # 1. 异或掉原来的位置 (相当于把棋子从棋盘上拔起来)
        new_lock ^= self.zobrist_keys[0][p_idx][from_idx]
        new_key ^= self.zobrist_keys[1][p_idx][from_idx]
        
        # 2. 异或上新的位置 (相当于把棋子拍到新格子上)
        new_lock ^= self.zobrist_keys[0][p_idx][to_idx]
        new_key ^= self.zobrist_keys[1][p_idx][to_idx]
        
        # 3. 如果有吃子，异或掉被吃掉的倒霉蛋
        if action.captured_item:
            c_idx = self._get_piece_index(action.captured_item)
            new_lock ^= self.zobrist_keys[0][c_idx][to_idx]
            new_key ^= self.zobrist_keys[1][c_idx][to_idx]
            
        return (new_lock, new_key)

    def get_score(self, lock, key, depth, side):
        """尝试从缓存中读取当前局面的打分"""
        if lock in self.table:
            entry = self.table[lock]
            # 必须满足双重校验防碰撞，且缓存的搜索深度不低于当前要求深度
            if entry['key'] == key and entry['depth'] >= depth and entry['side'] == side:
                self.hit_cache_counter += 1
                return entry['score']
            self.conflict_counter += 1
        return None

    def set_score(self, lock, key, score, depth, side):
        """将艰苦算出来的分数存入缓存"""
        self.table[lock] = {
            'key': key,
            'score': score,
            'depth': depth,
            'side': side
        }