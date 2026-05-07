import React, { useState, useEffect } from 'react';

// ==========================================
// 1. 初始化棋盘数据
// ==========================================
const INITIAL_BOARD = {
  '0,0': { type: '車', color: 'black' }, '1,0': { type: '馬', color: 'black' }, '2,0': { type: '象', color: 'black' }, '3,0': { type: '士', color: 'black' }, '4,0': { type: '將', color: 'black' }, '5,0': { type: '士', color: 'black' }, '6,0': { type: '象', color: 'black' }, '7,0': { type: '馬', color: 'black' }, '8,0': { type: '車', color: 'black' },
  '1,2': { type: '砲', color: 'black' }, '7,2': { type: '砲', color: 'black' },
  '0,3': { type: '卒', color: 'black' }, '2,3': { type: '卒', color: 'black' }, '4,3': { type: '卒', color: 'black' }, '6,3': { type: '卒', color: 'black' }, '8,3': { type: '卒', color: 'black' },
  
  '0,9': { type: '車', color: 'red' }, '1,9': { type: '馬', color: 'red' }, '2,9': { type: '相', color: 'red' }, '3,9': { type: '仕', color: 'red' }, '4,9': { type: '帥', color: 'red' }, '5,9': { type: '仕', color: 'red' }, '6,9': { type: '相', color: 'red' }, '7,9': { type: '馬', color: 'red' }, '8,9': { type: '車', color: 'red' },
  '1,7': { type: '炮', color: 'red' }, '7,7': { type: '炮', color: 'red' },
  '0,6': { type: '兵', color: 'red' }, '2,6': { type: '兵', color: 'red' }, '4,6': { type: '兵', color: 'red' }, '6,6': { type: '兵', color: 'red' }, '8,6': { type: '兵', color: 'red' },
};

// ==========================================
// 2. 主应用程序 (紧凑大屏 + 离线日志生成)
// ==========================================
export default function ChineseChessApp() {
  // === 玩家身份与对局 Session 状态 ===
  const [hasStarted, setHasStarted] = useState(false);
  const [playerId, setPlayerId] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [turnCount, setTurnCount] = useState(1);

  const [history, setHistory] = useState([{
    board: INITIAL_BOARD,
    turn: 'red',
    lastMove: null,
    actionMessage: "系统就绪，等待红方初次指令",
    heatmapImg: null,
  }]);
  const [stepNumber, setStepNumber] = useState(0);
  
  const [searchDepth, setSearchDepth] = useState(3);
  const [branchLimit, setBranchLimit] = useState(4);

  const currentState = history[stepNumber];
  const board = currentState.board;
  const turn = currentState.turn;
  const lastMove = currentState.lastMove;
  const actionMessage = currentState.actionMessage;
  const heatmapImg = currentState.heatmapImg;

  const [selectedPos, setSelectedPos] = useState(null);
  const [validMoves, setValidMoves] = useState([]);
  const [isAiThinking, setIsAiThinking] = useState(false);
  const [winner, setWinner] = useState(null);

  const isViewingHistory = stepNumber < history.length - 1;

  // 启动对局，生成唯一文件夹名称
  const handleStartGame = () => {
    if (!playerId.trim()) {
      alert("请输入玩家 ID！");
      return;
    }
    const date = new Date();
    const yyyy = date.getFullYear();
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const dd = String(date.getDate()).padStart(2, '0');
    const hh = String(date.getHours()).padStart(2, '0');
    const min = String(date.getMinutes()).padStart(2, '0');
    const ss = String(date.getSeconds()).padStart(2, '0');
    
    // 生成格式: PlayerID_YYYYMMDD_HHMMSS
    const sid = `${playerId.trim()}_${yyyy}${mm}${dd}_${hh}${min}${ss}`;
    setSessionId(sid);
    setHasStarted(true);
  };

  const inBoard = (x, y) => x >= 0 && x <= 8 && y >= 0 && y <= 9;
  const inPalace = (x, y, color) => {
    if (x < 3 || x > 5) return false;
    return color === 'red' ? (y >= 7 && y <= 9) : (y >= 0 && y <= 2);
  };

  const calculateValidMoves = (x, y, piece, currentBoard) => {
    const moves = [];
    const addIfValid = (targetX, targetY) => {
      if (!inBoard(targetX, targetY)) return false;
      const targetPiece = currentBoard[`${targetX},${targetY}`];
      if (targetPiece?.color === piece.color) return false; 
      moves.push({ x: targetX, y: targetY });
      return true;
    };

    if (piece.type === '車') {
      const dirs = [[0, 1], [0, -1], [1, 0], [-1, 0]];
      dirs.forEach(([dx, dy]) => {
        let cx = x + dx, cy = y + dy;
        while (inBoard(cx, cy)) {
          const targetPiece = currentBoard[`${cx},${cy}`];
          if (!targetPiece) { moves.push({ x: cx, y: cy }); } 
          else { if (targetPiece.color !== piece.color) moves.push({ x: cx, y: cy }); break; }
          cx += dx; cy += dy;
        }
      });
    } 
    else if (piece.type === '馬') {
      const jumps = [{ dx: 1, dy: 2, bx: x, by: y + 1 }, { dx: 2, dy: 1, bx: x + 1, by: y }, { dx: 2, dy: -1, bx: x + 1, by: y }, { dx: 1, dy: -2, bx: x, by: y - 1 }, { dx: -1, dy: -2, bx: x, by: y - 1 }, { dx: -2, dy: -1, bx: x - 1, by: y }, { dx: -2, dy: 1, bx: x - 1, by: y }, { dx: -1, dy: 2, bx: x, by: y + 1 }];
      jumps.forEach(j => { if (!currentBoard[`${j.bx},${j.by}`]) addIfValid(x + j.dx, y + j.dy); });
    }
    else if (piece.type === '相' || piece.type === '象') {
      const jumps = [{ dx: 2, dy: 2, bx: x + 1, by: y + 1 }, { dx: 2, dy: -2, bx: x + 1, by: y - 1 }, { dx: -2, dy: 2, bx: x - 1, by: y + 1 }, { dx: -2, dy: -2, bx: x - 1, by: y - 1 }];
      jumps.forEach(j => {
        const ty = y + j.dy;
        if ((piece.color === 'red' && ty < 5) || (piece.color === 'black' && ty > 4)) return;
        if (!currentBoard[`${j.bx},${j.by}`]) addIfValid(x + j.dx, ty); 
      });
    }
    else if (piece.type === '仕' || piece.type === '士') {
      const dirs = [[1, 1], [1, -1], [-1, 1], [-1, -1]];
      dirs.forEach(([dx, dy]) => { const tx = x + dx, ty = y + dy; if (inPalace(tx, ty, piece.color)) addIfValid(tx, ty); });
    }
    else if (piece.type === '帥' || piece.type === '將') {
      const dirs = [[0, 1], [0, -1], [1, 0], [-1, 0]];
      dirs.forEach(([dx, dy]) => { const tx = x + dx, ty = y + dy; if (inPalace(tx, ty, piece.color)) addIfValid(tx, ty); });
    }
    else if (piece.type === '炮' || piece.type === '砲') {
      const dirs = [[0, 1], [0, -1], [1, 0], [-1, 0]];
      dirs.forEach(([dx, dy]) => {
        let cx = x + dx, cy = y + dy; let overPiece = false;
        while (inBoard(cx, cy)) {
          const targetPiece = currentBoard[`${cx},${cy}`];
          if (!targetPiece) { if (!overPiece) moves.push({ x: cx, y: cy }); } 
          else { if (!overPiece) { overPiece = true; } else { if (targetPiece.color !== piece.color) moves.push({ x: cx, y: cy }); break; } }
          cx += dx; cy += dy;
        }
      });
    }
    else if (piece.type === '兵' || piece.type === '卒') {
      const dirY = piece.color === 'red' ? -1 : 1;
      addIfValid(x, y + dirY); 
      if (piece.color === 'red' ? y < 5 : y > 4) { addIfValid(x - 1, y); addIfValid(x + 1, y); }
    }
    return moves;
  };

  const handleSquareClick = async (x, y) => {
    if (winner || isAiThinking) return; 
    if (isViewingHistory) {
      alert("⚠️ 处于历史审查模式，请点击底部的『推进』至最新帧继续。"); return;
    }

    const posKey = `${x},${y}`;
    const clickedPiece = board[posKey];

    if (clickedPiece && clickedPiece.color === turn && turn === 'red') {
      setSelectedPos({ x, y });
      setValidMoves(calculateValidMoves(x, y, clickedPiece, board));
      return;
    }

    if (selectedPos && validMoves.some(m => m.x === x && m.y === y)) {
      const newBoard = { ...board };
      const movingPiece = newBoard[`${selectedPos.x},${selectedPos.y}`];
      const targetPiece = newBoard[posKey]; 
      
      delete newBoard[`${selectedPos.x},${selectedPos.y}`];
      newBoard[posKey] = movingPiece;

      const playerState = {
        board: newBoard,
        turn: 'black',
        lastMove: { from: { x: selectedPos.x, y: selectedPos.y }, to: { x, y } },
        actionMessage: `[玩家指令] 红 ${movingPiece.type} (${selectedPos.x},${selectedPos.y}) -> (${x},${y})`,
        heatmapImg: null,
      };
      
      const newHistory = [...history, playerState];
      setHistory(newHistory);
      setStepNumber(newHistory.length - 1);

      setSelectedPos(null);
      setValidMoves([]);

      if (targetPiece && targetPiece.type === '將') {
        setWinner('red'); return; 
      }

      setIsAiThinking(true);

      try {
        const response = await fetch('http://127.0.0.1:8000/api/move', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          // 传递核心元数据：加上 session_id 和 turn_count
          body: JSON.stringify({ 
            from_x: selectedPos.x, from_y: selectedPos.y, to_x: x, to_y: y, 
            depth: searchDepth, branch_limit: branchLimit,
            session_id: sessionId, turn_count: turnCount 
          })
        });

        const data = await response.json();
        
        if (data.status === 'success') {
          const aiMove = data.ai_move;
          const afterAiBoard = { ...newBoard }; 
          const fromKey = `${aiMove.from_x},${aiMove.from_y}`;
          const toKey = `${aiMove.to_x},${aiMove.to_y}`;
          const aiPiece = afterAiBoard[fromKey];
          
          if (!aiPiece) {
            alert(`严重异常：数据不同步。请重启后端。`);
            setIsAiThinking(false); return;
          }

          const aiTargetPiece = afterAiBoard[toKey]; 
          delete afterAiBoard[fromKey];
          afterAiBoard[toKey] = aiPiece;

          const aiState = {
            board: afterAiBoard,
            turn: 'red',
            lastMove: { from: { x: aiMove.from_x, y: aiMove.from_y }, to: { x: aiMove.to_x, y: aiMove.to_y } },
            actionMessage: `[系统响应] 黑 ${aiMove.piece} (${aiMove.from_x},${aiMove.from_y}) -> (${aiMove.to_x},${aiMove.to_y}) | 决策树已归档`,
            heatmapImg: data.visualizations?.heatmap || null,
          };

          const finalHistory = [...newHistory, aiState];
          setHistory(finalHistory);
          setStepNumber(finalHistory.length - 1);
          setTurnCount(prev => prev + 1); // 成功后回合数+1

          if (aiTargetPiece && aiTargetPiece.type === '帥') {
            setWinner('black');
          }
          
        } else if (data.status === 'game_over') {
          setWinner('red'); 
          const checkmateState = {
            ...playerState,
            actionMessage: `[系统判定] CHECKMATE 绝杀！AI 算力耗尽，已无合法走步。`,
          };
          const finalHistory = [...history.slice(0, -1), checkmateState];
          setHistory(finalHistory);
          setStepNumber(finalHistory.length - 1);
        } else {
          alert(`后端报错: ${data.error || data.message}`);
          setHistory(history);
          setStepNumber(history.length - 1);
        }
      } catch (error) {
        alert("无法连接到AI服务器！");
      } finally {
        setIsAiThinking(false);
      }
    }
  };

  const renderGridLines = () => {
    const colStep = 100 / 9; const rowStep = 100 / 10;
    const offsetX = colStep / 2; const offsetY = rowStep / 2;
    const renderMark = (xIdx, yIdx) => {
      const px = offsetX + xIdx * colStep; const py = offsetY + yIdx * rowStep;
      const size = 3; const gap = 1; 
      const strokeColor = "#2C1608"; const marks = [];
      if (xIdx > 0) marks.push(<path key={`tl-${xIdx}-${yIdx}`} d={`M ${px-gap} ${py-gap-size} L ${px-gap} ${py-gap} L ${px-gap-size} ${py-gap}`} stroke={strokeColor} strokeWidth="1.5" fill="none" />);
      if (xIdx < 8) marks.push(<path key={`tr-${xIdx}-${yIdx}`} d={`M ${px+gap} ${py-gap-size} L ${px+gap} ${py-gap} L ${px+gap+size} ${py-gap}`} stroke={strokeColor} strokeWidth="1.5" fill="none" />);
      if (xIdx > 0) marks.push(<path key={`bl-${xIdx}-${yIdx}`} d={`M ${px-gap} ${py+gap+size} L ${px-gap} ${py+gap} L ${px-gap-size} ${py+gap}`} stroke={strokeColor} strokeWidth="1.5" fill="none" />);
      if (xIdx < 8) marks.push(<path key={`br-${xIdx}-${yIdx}`} d={`M ${px+gap} ${py+gap+size} L ${px+gap} ${py+gap} L ${px+gap+size} ${py+gap}`} stroke={strokeColor} strokeWidth="1.5" fill="none" />);
      return marks;
    };
    return (
      <svg style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none', zIndex: 0 }}>
        <rect x={`${offsetX}%`} y={`${offsetY}%`} width={`${colStep * 8}%`} height={`${rowStep * 9}%`} fill="none" stroke="#2C1608" strokeWidth="2" />
        {Array.from({ length: 10 }).map((_, i) => (<line key={`h${i}`} x1={`${offsetX}%`} y1={`${offsetY + i * rowStep}%`} x2={`${offsetX + 8 * colStep}%`} y2={`${offsetY + i * rowStep}%`} stroke="#2C1608" strokeWidth="1.5" />))}
        {Array.from({ length: 9 }).map((_, i) => {
          const lineX = `${offsetX + i * colStep}%`;
          if (i === 0 || i === 8) return <line key={`v${i}`} x1={lineX} y1={`${offsetY}%`} x2={lineX} y2={`${offsetY + 9 * rowStep}%`} stroke="#2C1608" strokeWidth="1.5" />;
          return ( <React.Fragment key={`v${i}`}> <line x1={lineX} y1={`${offsetY}%`} x2={lineX} y2={`${offsetY + 4 * rowStep}%`} stroke="#2C1608" strokeWidth="1.5" /> <line x1={lineX} y1={`${offsetY + 5 * rowStep}%`} x2={lineX} y2={`${offsetY + 9 * rowStep}%`} stroke="#2C1608" strokeWidth="1.5" /> </React.Fragment> );
        })}
        <line x1={`${offsetX + 3 * colStep}%`} y1={`${offsetY}%`} x2={`${offsetX + 5 * colStep}%`} y2={`${offsetY + 2 * rowStep}%`} stroke="#2C1608" strokeWidth="1.5" />
        <line x1={`${offsetX + 5 * colStep}%`} y1={`${offsetY}%`} x2={`${offsetX + 3 * colStep}%`} y2={`${offsetY + 2 * rowStep}%`} stroke="#2C1608" strokeWidth="1.5" />
        <line x1={`${offsetX + 3 * colStep}%`} y1={`${offsetY + 7 * rowStep}%`} x2={`${offsetX + 5 * colStep}%`} y2={`${offsetY + 9 * rowStep}%`} stroke="#2C1608" strokeWidth="1.5" />
        <line x1={`${offsetX + 5 * colStep}%`} y1={`${offsetY + 7 * rowStep}%`} x2={`${offsetX + 3 * colStep}%`} y2={`${offsetY + 9 * rowStep}%`} stroke="#2C1608" strokeWidth="1.5" />
        {[ [1,2], [7,2], [0,3], [2,3], [4,3], [6,3], [8,3], [1,7], [7,7], [0,6], [2,6], [4,6], [6,6], [8,6] ].map(([x, y]) => renderMark(x, y))}
        <text x="25%" y="51.5%" fontSize="24" fill="#2C1608" textAnchor="middle" dominantBaseline="middle" style={{fontFamily: 'STKaiti, serif', letterSpacing: '8px', opacity: 0.8}}>楚 河</text>
        <text x="75%" y="51.5%" fontSize="24" fill="#2C1608" textAnchor="middle" dominantBaseline="middle" style={{fontFamily: 'STKaiti, serif', letterSpacing: '8px', opacity: 0.8}}>汉 界</text>
      </svg>
    );
  };

  // 渲染登录拦截界面
  if (!hasStarted) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', width: '100%', backgroundColor: '#0f172a', alignItems: 'center', justifyContent: 'center', fontFamily: 'sans-serif' }}>
        <div style={{ padding: '40px', backgroundColor: '#fff', border: '4px solid #333', boxShadow: '12px 12px 0 rgba(255,255,255,0.1)', textAlign: 'center' }}>
          {/* 将名字修改为简洁大气的 中国象棋 AI (Phase 3) */}
          <h2 style={{ margin: '0 0 20px 0', color: '#0f172a', fontWeight: '900', fontSize: '24px' }}>中国象棋 AI (Phase 3)</h2>
          <p style={{ margin: '0 0 20px 0', color: '#64748b', fontSize: '14px' }}>请输入实验干预者身份标识 (Player ID)</p>
          <input 
            type="text" 
            placeholder="如: WangTianyi"
            value={playerId}
            onChange={(e) => setPlayerId(e.target.value)}
            style={{ width: '100%', padding: '12px', marginBottom: '20px', border: '2px solid #cbd5e1', fontSize: '16px', outline: 'none', boxSizing: 'border-box' }}
            onKeyDown={(e) => { if (e.key === 'Enter') handleStartGame(); }}
          />
          <button 
            onClick={handleStartGame}
            style={{ width: '100%', padding: '12px', backgroundColor: '#ef4444', color: '#fff', border: '2px solid #b91c1c', cursor: 'pointer', fontWeight: 'bold', fontSize: '16px', textTransform: 'uppercase' }}
          >初始化对局并建立离线日志</button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', width: '100%', backgroundColor: '#e2e8f0', fontFamily: 'sans-serif', alignItems: 'center', padding: '40px 20px' }}>
      
      <div style={{ marginBottom: '20px', width: '100%', maxWidth: '640px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '2px solid #333', paddingBottom: '10px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 'bold', color: '#0f172a', margin: 0 }}>
          {playerId.toUpperCase()} <span style={{color: '#ef4444'}}>VS</span> AI
        </h1>
        
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <div style={{ padding: '4px 8px', border: '2px solid #0f172a', display: 'flex', alignItems: 'center', gap: '5px', backgroundColor: '#fff' }}>
            <span style={{ fontSize: '11px', fontWeight: 'bold', color: '#475569' }}>深度:</span>
            <select value={searchDepth} onChange={(e) => setSearchDepth(Number(e.target.value))} style={{ border: 'none', outline: 'none', fontWeight: 'bold', backgroundColor: 'transparent', cursor: 'pointer', color: '#0f172a' }}>
              <option value={2}>2层</option>
              <option value={3}>3层</option>
              <option value={4}>4层</option>
              <option value={5}>5层 (极深)</option>
            </select>
          </div>
          
          <div style={{ padding: '4px 8px', border: '2px solid #0f172a', display: 'flex', alignItems: 'center', gap: '5px', backgroundColor: '#fff' }}>
            <span style={{ fontSize: '11px', fontWeight: 'bold', color: '#475569' }}>宽度:</span>
            <select value={branchLimit} onChange={(e) => setBranchLimit(Number(e.target.value))} style={{ border: 'none', outline: 'none', fontWeight: 'bold', backgroundColor: 'transparent', cursor: 'pointer', color: '#0f172a' }}>
              <option value={3}>3</option>
              <option value={4}>4</option>
              <option value={6}>6</option>
              <option value={8}>8 (慢)</option>
            </select>
          </div>
        </div>
      </div>

      {/* 核心棋盘 */}
      <div style={{ 
        position: 'relative', width: '100%', maxWidth: '560px', aspectRatio: '9 / 10', 
        backgroundColor: '#5C3A21', 
        borderRadius: '0', border: '8px solid #2C1608', 
        boxSizing: 'content-box', opacity: (isAiThinking || isViewingHistory) ? 0.85 : 1, 
        boxShadow: 'inset 0 0 20px rgba(0,0,0,0.5), 12px 12px 0 rgba(0,0,0,0.15)' 
      }}>
        {renderGridLines()}
        
        {winner && (
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(15, 23, 42, 0.85)', zIndex: 100, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '20px', textAlign: 'center' }}>
            <div style={{ border: `4px solid ${winner === 'red' ? '#ef4444' : '#38bdf8'}`, padding: '30px', backgroundColor: '#0f172a', boxShadow: '8px 8px 0 rgba(0,0,0,0.5)' }}>
              <h2 style={{ color: winner === 'red' ? '#ef4444' : '#38bdf8', fontSize: '28px', margin: '0 0 15px 0', fontWeight: '900', letterSpacing: '2px' }}>
                {winner === 'red' ? 'CHECKMATE: 玩家胜利' : 'FATAL ERROR: 电脑胜利'}
              </h2>
              <button onClick={() => window.location.reload()} style={{ padding: '10px 24px', fontSize: '14px', cursor: 'pointer', backgroundColor: '#fff', border: 'none', fontWeight: 'bold', color: '#0f172a', textTransform: 'uppercase' }}>
                重新初始化
              </button>
            </div>
          </div>
        )}

        {isViewingHistory && !winner && (
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.4)', zIndex: 50, display: 'flex', alignItems: 'flex-start', justifyContent: 'center', paddingTop: '40px' }}>
            <div style={{ backgroundColor: '#fff', padding: '8px 16px', border: '2px solid #3b82f6', color: '#1d4ed8', fontWeight: 'bold', boxShadow: '4px 4px 0 rgba(59,130,246,0.5)' }}>
              [回溯模式] 正在审查历史记录
            </div>
          </div>
        )}

        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'grid', gridTemplateColumns: 'repeat(9, minmax(0, 1fr))', gridTemplateRows: 'repeat(10, minmax(0, 1fr))' }}>
          {Array.from({ length: 10 }).map((_, y) => 
            Array.from({ length: 9 }).map((_, x) => {
              const posKey = `${x},${y}`;
              const piece = board[posKey];
              const isSelected = selectedPos?.x === x && selectedPos?.y === y;
              const isValidMove = validMoves.some(m => m.x === x && m.y === y);
              const isLastMovePoint = lastMove && ((lastMove.from.x === x && lastMove.from.y === y) || (lastMove.to.x === x && lastMove.to.y === y));

              return (
                <div key={posKey} style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: (isAiThinking || winner || isViewingHistory) ? 'default' : 'pointer', backgroundColor: isLastMovePoint ? 'rgba(255, 255, 255, 0.15)' : 'transparent', borderRadius: '0' }} onClick={() => handleSquareClick(x, y)}>
                  {isValidMove && (<div style={{ position: 'absolute', width: '12px', height: '12px', backgroundColor: '#4ade80', borderRadius: '0', zIndex: 10, boxShadow: '0 0 5px rgba(0,0,0,0.5)' }} />)}
                  {piece && (
                    <div style={{ 
                      width: '80%', aspectRatio: '1 / 1', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', 
                      fontWeight: 'bold', fontSize: 'clamp(16px, 4vw, 26px)', 
                      boxShadow: isSelected ? '0 8px 20px rgba(0,0,0,0.8)' : '2px 3px 5px rgba(0,0,0,0.5)', 
                      backgroundColor: '#FDF5E6', 
                      color: piece.color === 'red' ? '#B71C1C' : '#0F172A', 
                      border: `2px solid ${piece.color === 'red' ? '#B71C1C' : '#0F172A'}`, 
                      fontFamily: 'STKaiti, serif', zIndex: 20, 
                      transform: isSelected ? 'scale(1.1) translateY(-3px)' : 'scale(1)', 
                      outline: isSelected ? '3px solid #60a5fa' : 'none', outlineOffset: '2px'
                    }}>
                      <div style={{ width: '82%', height: '82%', borderRadius: '50%', border: '1px solid currentColor', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{piece.type}</div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
      
      {/* 控制面板横向排列 */}
      <div style={{ marginTop: '24px', width: '100%', maxWidth: '560px', display: 'flex', gap: '16px' }}>
        {/* 时间线控制器 */}
        <div style={{ flex: 1, backgroundColor: '#fff', border: '2px solid #cbd5e1', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 15px' }}>
          <button disabled={stepNumber === 0} onClick={() => setStepNumber(prev => Math.max(0, prev - 1))} style={{ padding: '8px 12px', border: '2px solid #333', backgroundColor: stepNumber === 0 ? '#e2e8f0' : '#fff', color: stepNumber === 0 ? '#94a3b8' : '#333', cursor: stepNumber === 0 ? 'not-allowed' : 'pointer', fontWeight: 'bold' }}>◀ 溯源</button>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <span style={{ fontSize: '14px', fontWeight: 'bold', color: '#333' }}>帧: {stepNumber} / {history.length - 1}</span>
            {isViewingHistory && (<span onClick={() => setStepNumber(history.length - 1)} style={{ fontSize: '12px', color: '#2563eb', textDecoration: 'underline', cursor: 'pointer', marginTop: '2px' }}>同步至最新</span>)}
          </div>
          <button disabled={stepNumber === history.length - 1} onClick={() => setStepNumber(prev => Math.min(history.length - 1, prev + 1))} style={{ padding: '8px 12px', border: '2px solid #333', backgroundColor: stepNumber === history.length - 1 ? '#e2e8f0' : '#fff', color: stepNumber === history.length - 1 ? '#94a3b8' : '#333', cursor: stepNumber === history.length - 1 ? 'not-allowed' : 'pointer', fontWeight: 'bold' }}>推进 ▶</button>
        </div>
        
        {/* 状态播报板 */}
        <div style={{ flex: 1, backgroundColor: '#1e293b', color: winner ? '#ef4444' : '#10b981', padding: '12px 16px', border: '2px solid #333', display: 'flex', alignItems: 'center', gap: '10px', fontFamily: 'monospace' }}>
          <span style={{ fontSize: '18px' }}>{isAiThinking ? '...' : '>_'}</span>
          <span style={{ fontSize: '13px', fontWeight: 'bold', letterSpacing: '0.5px' }}>{actionMessage}</span>
        </div>
      </div>

      {/* 热力图监控 (可选保留) */}
      {heatmapImg && (
        <div style={{ marginTop: '24px', width: '100%', maxWidth: '560px', backgroundColor: '#fff', padding: '20px', border: '2px solid #cbd5e1' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 'bold', color: '#0f172a', borderBottom: '2px solid #0f172a', paddingBottom: '8px', margin: '0 0 12px 0' }}>CNN 视网膜特征捕获</h3>
          <img src={`data:image/png;base64,${heatmapImg}`} alt="CNN Heatmap" style={{ width: '100%', border: '2px solid #333', backgroundColor: '#f8fafc' }} />
        </div>
      )}

    </div>
  );
}