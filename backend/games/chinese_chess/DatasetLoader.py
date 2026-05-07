import numpy as np
import torch
from torch.utils.data import Dataset
import json
import os
from .ChineseChessUtils import ChineseChessType, ChineseChessSide

class ChessDataset(Dataset):
    """
    中国象棋神经网络数据集加载器
    负责将大师棋谱解析为 CNN 可读取的 3D 张量 (Tensors)
    """
    def __init__(self, dataset_path=None):
        self.states = []       # 存放棋盘状态的矩阵 X
        self.evaluations = []  # 存放大师对这个局面的打分 Y (用于价值网络 Value Network)
        self.best_moves = []   # 存放大师的走步 Y (用于策略网络 Policy Network)
        
        if dataset_path and os.path.exists(dataset_path):
            self._load_and_parse(dataset_path)
            print(f"[数据层] 成功加载大师棋谱，共提取 {len(self.states)} 个训练样本。")
        else:
            print("[数据层] 数据集不存在或未指定，当前为未初始化状态。")

    def __len__(self):
        return len(self.states)

    def __getitem__(self, idx):
        # 转换为 PyTorch 张量
        x = torch.tensor(self.states[idx], dtype=torch.float32)
        y_value = torch.tensor(self.evaluations[idx], dtype=torch.float32)
        return x, y_value

    @staticmethod
    def board_to_tensor(board):
        """
        🚀 极客核心：将棋盘对象转化为 14 x 10 x 9 的张量
        14个通道顺序: [红車, 红馬, 红炮, 红相, 红仕, 红帥, 红兵, 黑車, 黑馬, 黑砲, 黑象, 黑士, 黑將, 黑卒]
        """
        tensor = np.zeros((14, 10, 9), dtype=np.float32)
        
        # 定义棋子类型到通道索引的映射
        type_to_idx = {
            ChineseChessType.JU: 0, ChineseChessType.MA: 1, ChineseChessType.PAO: 2,
            ChineseChessType.XIANG: 3, ChineseChessType.SHI: 4, ChineseChessType.JIANG: 5,
            ChineseChessType.ZU: 6
        }
        
        for item in board.items.values():
            loc = board.get_location(item)
            if loc:
                # 判断是红方还是黑方，红方 0-6，黑方 7-13
                base_channel = 0 if item.side == ChineseChessSide.UP else 7
                channel = base_channel + type_to_idx[item.type_]
                
                # 在张量的对应位置点亮 (设为 1.0)
                tensor[channel][loc.y][loc.x] = 1.0
                
        return tensor

    def _load_and_parse(self, filepath):
        """解析 JSON 格式的大师对局数据集"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for game in data.get('games', []):
                for step in game.get('steps', []):
                    # 这里假设数据集中存的是已经展开的二维数组，实际工程中通常会直接存储 FEN 串或着法序列
                    if 'board_matrix' in step and 'score' in step:
                        self.states.append(step['board_matrix'])
                        self.evaluations.append(step['score'])
                        
        except Exception as e:
            print(f"[数据层] 数据集解析失败: {e}")

    @staticmethod
    def generate_mock_dataset(output_path="mock_master_games.json", samples=1000):
        """
        [工具函数] 如果没有真实的棋谱，使用此函数生成带有高斯噪声的模拟数据
        用于打通训练 Pipeline，确保神经网络能跑起来
        """
        print(f"正在生成包含 {samples} 个样本的模拟大师数据集...")
        mock_games = {"games": [{"steps": []}]}
        for _ in range(samples):
            # 随机生成一个 14x10x9 的矩阵
            mock_tensor = np.random.choice([0, 1], size=(14, 10, 9), p=[0.95, 0.05]).tolist()
            # 随机生成一个局势评分 (-1.0 到 1.0)
            mock_score = np.random.uniform(-1.0, 1.0)
            mock_games["games"][0]["steps"].append({
                "board_matrix": mock_tensor,
                "score": mock_score
            })
            
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(mock_games, f)
        print(f"模拟数据集已保存至: {output_path}")