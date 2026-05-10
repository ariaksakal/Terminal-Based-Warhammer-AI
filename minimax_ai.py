from constants import *
from heuristics import evaluate_state
import random
import time  # <--- Zamanlayıcı için bunu ekledik

def get_best_move(game_state):
    """
    Minimax algoritmasını başlatır ve en iyi hamleyi döndürür.
    """
    best_score = -INFINITY
    best_move = None
    
    # Hero'nun yapabileceği tüm hamleleri al
    legal_moves = game_state.get_legal_moves(game_state.hero)
    
    # Eğer hiç hamle yoksa (sıkıştıysa) bekle
    if not legal_moves:
        return ('wait', game_state.hero.pos)
    
    # --- KRİTİK DÜZELTME ---
    # Eğer AI tüm senaryolarda öleceğini görürse best_move None kalıyordu ve oyun çöküyordu.
    # Varsayılan olarak listedeki ilk hamleyi seçiyoruz. 
    # Böylece "kötünün iyisi" olmasa bile en azından geçerli bir hamle yapmış olur.
    best_move = legal_moves[0] 
    # -----------------------

    # Alpha-Beta Başlangıç Değerleri
    alpha = -INFINITY
    beta = INFINITY

    print(f"🧠 AI Düşünüyor... (Olasılıklar: {len(legal_moves)})")
    
    # --- BURAYA 5 SANİYE BEKLEME EKLEDİK ---
    # Tabloları rahat takip edebilmek için yapay zeka hamle yapmadan önce bekler.
    time.sleep(5) 
    # ---------------------------------------

    # Kök Düğüm (Root Node) - İlk Hamleler
    for move in legal_moves:
        # 1. Sanal bir evren oluştur (Kopyala)
        simulated_state = game_state.clone()
        
        # 2. Bu sanal evrende hamleyi yap (Bizim sıramız)
        # Not: clone() sonrası hero referansı değiştiği için yeni state'teki hero'yu bulmalıyız
        sim_hero = simulated_state.hero 
        simulated_state.apply_move(sim_hero, move)
        
        # 3. Minimax'i çağır (Sıra Düşmanda - MIN layer)
        # Depth - 1 yaptık çünkü bir hamle harcadık
        score = minimax(simulated_state, AI_DEPTH - 1, alpha, beta, False)
        
        # 4. En iyi skoru tut
        if score > best_score:
            best_score = score
            best_move = move
            
        # Alpha güncelle (Max oyuncusu için alt sınır)
        alpha = max(alpha, best_score)
        
    return best_move

def minimax(state, depth, alpha, beta, is_maximizing):
    """
    Özyinelemeli (Recursive) Minimax Fonksiyonu + Alpha-Beta Pruning.
    """
    
    # 1. DURMA KOŞULLARI (Base Cases)
    # Derinlik bitti veya oyun bitti (Hero öldü)
    if depth == 0 or not state.hero.is_alive():
        return evaluate_state(state)

    # 2. MAX PLAYER (HERO - BİZİM TURUMUZ)
    if is_maximizing:
        max_eval = -INFINITY
        moves = state.get_legal_moves(state.hero)
        
        if not moves: return evaluate_state(state)

        for move in moves:
            sim_state = state.clone()
            sim_state.apply_move(sim_state.hero, move)
            
            eval_score = minimax(sim_state, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            
            # Pruning (Budama)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break # Beta Cut-off
        return max_eval

    # 3. MIN PLAYER (DÜŞMANLAR - DÜNYANIN TURU)
    else:
        # Düşmanlar için tek tek ağaç oluşturmak yerine,
        # onların "Basit Mantıklı" (Scripted) oynayacağını varsayıyoruz.
        
        min_eval = INFINITY
        
        # Düşman turunu simüle et
        sim_state = state.clone()
        simulate_enemy_turn(sim_state)
        
        # Düşmanlar oynadıktan sonra sıra tekrar Hero'da (Max)
        eval_score = minimax(sim_state, depth - 1, alpha, beta, True)
        min_eval = min(min_eval, eval_score)
        
        # Pruning
        beta = min(beta, eval_score)
        if beta <= alpha:
             pass # Normalde break olur ama burada loop yok
            
        return min_eval

def simulate_enemy_turn(state):
    """
    Minimax içinde düşmanların ne yapacağını tahmin eder.
    Agresif oynarlar: Vurabiliyorsan vur, yoksa yaklaş.
    """
    enemies = [u for u in state.units if u.uid == ENEMY_ID]
    hero = state.hero
    
    if not hero.is_alive(): return

    for enemy in enemies:
        # Basit AI Mantığı: Vurabiliyorsan Vur, Yoksa Yaklaş
        dist = abs(enemy.pos[0] - hero.pos[0]) + abs(enemy.pos[1] - hero.pos[1])
        
        if dist <= enemy.attack_range:
            # Saldır
            state.apply_move(enemy, ('attack', hero))
        else:
            # Yaklaş (Basit Pathfinding: Hero'ya doğru 1 adım)
            move_candidates = state.get_legal_moves(enemy)
            # Sadece hareket hamlelerini al
            move_candidates = [m for m in move_candidates if m[0] == 'move']
            
            if move_candidates:
                # Hero'ya mesafeyi en aza indiren hamleyi seç
                best_move = min(move_candidates, key=lambda m: abs(m[1][0] - hero.pos[0]) + abs(m[1][1] - hero.pos[1]))
                state.apply_move(enemy, best_move)