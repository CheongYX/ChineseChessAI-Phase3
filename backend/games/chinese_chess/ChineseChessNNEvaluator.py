import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

from ..BoardGame import StatusEvaluator
from .ChineseChessBoard import ChineseChessBoard, ChineseChess
from .ChineseChessUtils import ChineseChessType, ChineseChessSide

# ==========================================
# 1. 定义卷积神经网络架构 (大脑皮层)
# ==========================================
class ChessCNN(nn.Module):
    def __init__(self):
        super(ChessCNN, self).__init__()
        # 输入：14个通道 (7种红子 + 7种黑子)，棋盘大小 10行 x 9列
        # 第一层卷积：提取基础特征 (如棋子是否被保护，是否过河)
        self.conv1 = nn.Conv2d(in_channels=14, out_channels=64, kernel_size=3, padding=1)
        # 第二层卷积：提取高级阵型特征 (如重炮、屏风马、车马冷着)
        self.conv2 = nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3, padding=1)
        
        # 全连接层：整合所有空间特征进行最终打分
        # 经过卷积后，图像大小仍为 10x9，通道数变为 128
        self.fc1 = nn.Linear(128 * 10 * 9, 256)
        self.fc2 = nn.Linear(256, 1)

        # 用于存储 Grad-CAM (热力图) 所需的梯度和特征图
        self.gradients = None
        self.activations = None

    def activations_hook(self, grad):
        self.gradients = grad

    def forward(self, x):
        # 激活函数使用 ReLU
        x = F.relu(self.conv1(x))
        x = self.conv2(x) # 重点：在 ReLU 前截获卷积特征
        
        # 注册 Hook：捕获最后一层卷积的特征与梯度，用于生成热力图
        if x.requires_grad:
            x.register_hook(self.activations_hook)
        self.activations = x

        x = F.relu(x)
        
        # 展平多维矩阵为一维向量，喂给全连接层
        x = x.view(-1, 128 * 10 * 9)
        x = F.relu(self.fc1(x))
        
        # 最后一层使用 Tanh，将输出压缩到 [-1, 1] 之间
        # 1 代表红方必胜，-1 代表黑方必胜，0 代表均势
        x = torch.tanh(self.fc2(x))
        return x

# ==========================================
# 2. 棋盘特征提取器 (视神经)
# ==========================================
class BoardConverter:
    @staticmethod
    def board_to_tensor(board: ChineseChessBoard) -> torch.Tensor:
        # 创建一个形状为 (14, 10, 9) 的全零矩阵
        # 14 代表 14 个“特征图” (Channel)
        tensor = np.zeros((14, 10, 9), dtype=np.float32)
        
        # 定义兵种到通道的映射索引
        type_to_index = {
            ChineseChessType.JU: 0,
            ChineseChessType.MA: 1,
            ChineseChessType.PAO: 2,
            ChineseChessType.XIANG: 3,
            ChineseChessType.SHI: 4,
            ChineseChessType.JIANG: 5,
            ChineseChessType.ZU: 6,
        }
        
        # 遍历棋盘，点亮特征图
        for item in board.items.values():
            loc = board.get_location(item)
            if loc is not None: # 如果棋子还在棋盘上
                channel_idx = type_to_index[item.type_]
                # 黑方占据 7-13 通道
                if item.side == ChineseChessSide.UP: 
                    channel_idx += 7
                
                # 在对应通道的 (y, x) 坐标处标记为 1.0
                tensor[channel_idx][loc.y][loc.x] = 1.0
                
        # 增加一个 Batch 维度，形状变为 (1, 14, 10, 9)
        return torch.from_numpy(tensor).unsqueeze(0)

# ==========================================
# 3. 神经网络评估器接口
# ==========================================
class ChineseChessNNEvaluator(StatusEvaluator):
    def __init__(self, model_path=None):
        super().__init__()
        self.side = None
        # 实例化神经网络
        self.model = ChessCNN()
        
        # 如果有训练好的权重文件，就加载它 (未来训练完成后使用)
        if model_path:
            self.model.load_state_dict(torch.load(model_path))
        
        # 设置为推理模式 (不进行梯度更新)
        self.model.eval()

    def set_status(self, side: ChineseChessSide):
        self.side = side

    def evaluateBoard(self, board: ChineseChessBoard) -> float:
        assert self.side is not None
        
        # 核心逻辑1：如果已经将死，直接返回极值
        opposite_side = ChineseChessSide.DOWN if self.side == ChineseChessSide.UP else ChineseChessSide.UP
        if board.get_king_location(self.side) is None:
            return 0.0 # 当前方老将被吃，胜率为0
        elif board.get_king_location(opposite_side) is None:
            return 1.0 # 对方老将被吃，胜率为100%
        if board.check_king_meet():
            return 1.0 # 导致对方老将照面，我方胜率100%

        # 核心逻辑2：将棋盘转换为神经网络可视的张量
        state_tensor = BoardConverter.board_to_tensor(board)
        
        # 核心逻辑3：让神经网络“思考”并打分
        with torch.no_grad():
            output = self.model(state_tensor).item() # 输出在 [-1, 1]
            
        # 核心逻辑4：将神经网络的分数转换为 [0, 1] 之间的概率
        # output 为 1 代表红优，-1 代表黑优
        # 我们需要把它统一为“self.side (当前行动方) 的胜率”
        if self.side == ChineseChessSide.DOWN: # 红方
            win_prob = (output + 1.0) / 2.0 
        else: # 黑方
            win_prob = (-output + 1.0) / 2.0 
            
        return win_prob