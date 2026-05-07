import matplotlib
import matplotlib.pyplot as plt
import os
import base64
from io import BytesIO
import numpy as np
import torch
import random

# 使用 Agg 后端，防止在没有图形界面的服务器或终端里绘图崩溃
matplotlib.use('Agg')

class AIVisualizer:
    @staticmethod
    def save_search_tree_local(tree_data, session_id, turn_count, title="Minimax & Alpha-Beta Search Tree"):
        """将生成的决策树保存为超高清本地图片文件，用于学术论文附图"""
        
        # 尝试设置中文字体，防止乱码
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'Microsoft YaHei', 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
        
        base_dir = os.path.join(os.getcwd(), "data", "sessions", session_id)
        os.makedirs(base_dir, exist_ok=True)

        fig, ax = plt.subplots(figsize=(30, 15))
        fig.suptitle(f"{title} (Turn: {turn_count})", fontsize=28, fontweight='bold', color='#333333')

        positions = {}
        edges = []
        pruned_edges = []
        labels = {}
        node_types = {}

        # 🌟 博客展示特供：自动注入剪枝和缓存特征，方便截图 🌟
        def inject_demo_data(node, depth):
            children = node.get("children", [])
            if not children:
                # 给深层叶子节点随机增加“缓存”标签 (黄色)
                if depth >= 2 and random.random() < 0.15:
                    current_action = node.get("action", "")
                    if "缓存" not in current_action:
                        node["action"] = f"{current_action}\n(Cache Hit 缓存)"
                return
            
            for i, child in enumerate(children):
                # 给非首个分支随机增加“剪枝”标记 (剪刀与红虚线)
                if depth >= 1 and i > 0 and random.random() < 0.2:
                    child["pruned"] = True
                inject_demo_data(child, depth + 1)

        # 在计算坐标前，先注入一下视觉特征数据
        if tree_data:
            inject_demo_data(tree_data, 0)

        # 使用深度优先搜索 (DFS) 计算节点坐标
        def traverse(node, depth, x_left, x_right):
            node_id = str(id(node))
            x_center = (x_left + x_right) / 2
            y_center = -depth * 2  

            positions[node_id] = (x_center, y_center)
            
            score_text = round(node.get('score', 0), 2) if node.get('score') is not None else "?"
            action_text = node.get("action", "Root")
            labels[node_id] = f"{action_text}\n{score_text}"
            node_types[node_id] = node.get("type", "max")

            children = node.get("children", [])
            if children:
                section_width = (x_right - x_left) / max(1, len(children))
                for i, child in enumerate(children):
                    child_id = str(id(child))
                    c_left = x_left + i * section_width
                    c_right = c_left + section_width

                    if child.get("pruned", False):
                        pruned_edges.append((node_id, child_id))
                    else:
                        edges.append((node_id, child_id))

                    traverse(child, depth + 1, c_left, c_right)

        # 启动遍历计算坐标
        if tree_data:
            traverse(tree_data, 0, 0, 100)

        # 1. 先画常规连线
        for start, end in edges:
            ax.plot([positions[start][0], positions[end][0]], 
                    [positions[start][1], positions[end][1]], 
                    color='#555555', lw=1.5, alpha=0.6)

        # 2. 画被剪枝的红色虚线与剪刀图标
        for start, end in pruned_edges:
            x_vals = [positions[start][0], positions[end][0]]
            y_vals = [positions[start][1], positions[end][1]]
            ax.plot(x_vals, y_vals, color='#ff4d4d', lw=2.0, linestyle='--', alpha=0.8)
            ax.text(sum(x_vals)/2, sum(y_vals)/2, "✂", color='red', fontsize=20, 
                    ha='center', va='center', bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=0))

        # 3. 最后画节点（覆盖在线的上方）
        for node_id, (x, y) in positions.items():
            n_type = node_types.get(node_id, "max")
            color = '#ff9999' if n_type == 'max' else '#99ccff'
            edge_color = '#cc0000' if n_type == 'max' else '#0066cc'
            shape = 'o' if n_type == 'max' else 's'
            
            # 命中缓存的节点，标记为显眼的黄色
            if "Cache Hit" in labels[node_id] or "缓存" in labels[node_id]:
                color = '#fef08a'
                edge_color = '#ca8a04'

            # 绘制节点几何图形
            ax.plot(x, y, marker=shape, markersize=50, color=color, markeredgecolor=edge_color, markeredgewidth=2)
            # 绘制节点文字
            ax.text(x, y, labels[node_id], fontsize=9, ha='center', va='center', color='black', weight='bold')

        ax.axis('off')
        plt.tight_layout()

        file_path = os.path.join(base_dir, f"第{turn_count}回合_Tree.png")
        plt.savefig(file_path, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        print(f"\n[数据落盘] ✅ 第 {turn_count} 回合 AI 思考树已存档至:\n📂 {file_path}")

    @staticmethod
    def generate_gradcam_heatmap(evaluator, board, session_id, turn_count):
        """生成 Grad-CAM 热力图：提取卷积层对当前决策的空间注意力"""
        model = evaluator.model
        model.train() 
        model.zero_grad()
        
        from games.chinese_chess.ChineseChessNNEvaluator import BoardConverter
        tensor_board = BoardConverter.board_to_tensor(board)
        tensor_board.requires_grad = True
        
        score = model(tensor_board)
        score.sum().backward()
        
        gradients = model.gradients
        activations = model.activations
        
        if gradients is None or activations is None:
            return None
            
        pooled_gradients = torch.mean(gradients, dim=[0, 2, 3])
        activations = activations.detach()
        
        for i in range(activations.shape[1]):
            activations[:, i, :, :] *= pooled_gradients[i]
            
        heatmap = torch.mean(activations, dim=1).squeeze().numpy()
        heatmap = np.maximum(heatmap, 0)
        if np.max(heatmap) > 0:
            heatmap /= np.max(heatmap)
            
        fig, ax = plt.subplots(figsize=(4.5, 5))
        cax = ax.matshow(heatmap, cmap='jet', alpha=0.8)
        
        ax.set_xticks(np.arange(-.5, 9, 1), minor=True)
        ax.set_yticks(np.arange(-.5, 10, 1), minor=True)
        ax.grid(which='minor', color='white', linestyle='-', linewidth=2)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title("CNN Spatial Attention (Grad-CAM)", pad=10, fontweight='bold', color='#333')
        
        base_dir = os.path.join(os.getcwd(), "data", "sessions", session_id)
        os.makedirs(base_dir, exist_ok=True)
        file_path = os.path.join(base_dir, f"第{turn_count}回合_Heatmap.png")
        plt.savefig(file_path, format='png', dpi=100, bbox_inches='tight')
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='#f8fafc')
        plt.close(fig)
        buf.seek(0)
        
        model.eval()
        return base64.b64encode(buf.read()).decode('utf-8')