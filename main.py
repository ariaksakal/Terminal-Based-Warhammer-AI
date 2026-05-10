import time
import os
import random
# Import Unit class and constants from game_engine
from game_engine import GameState, Unit, ENEMY_ID, BOSS_HP, BOSS_DMG 
from minimax_ai import get_best_move
from constants import *

def clear_screen():
    # Clear screen for Windows and Mac/Linux
    os.system('cls' if os.name == 'nt' else 'clear')

def print_game_state(state):
    """
    Renders the current game state to the console in a 'Cinematic' way.
    """
    clear_screen()
    
    # 1. TOP INFO PANEL
    wave_num = state.wave_count if hasattr(state, 'wave_count') else 1
    
    print(f"⚔️  TACTICAL AI SURVIVAL | 🌊 WAVE: {wave_num} ⚔️")
    print("-" * 40)
    print(f"💀 KILLS: {state.kill_count} | ❤️ HERO HP: {state.hero.hp}/{state.hero.max_hp} | 💪 DMG: {state.hero.dmg}")
    
    # Boss Warning
    boss_alive = any(u.type == "BOSS" for u in state.units)
    if boss_alive:
        boss = next(u for u in state.units if u.type == "BOSS")
        status = "RAGED 🔥" if boss.is_raged else "ACTIVE"
        print(f"👹 BOSS: {boss.hp} HP [{status}]")
    print("-" * 40)

    # 2. MAP RENDERING
    display_map = [['.' for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    # Terrain Layer
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if state.height_map[r, c] == 1: display_map[r][c] = '^' # High Ground
            if state.bush_map[r, c] == 1: display_map[r][c] = '&'   # Bush

    # Unit Layer
    for unit in state.units:
        symbol = '?'
        if unit.type == "Hero": symbol = 'H'
        elif unit.type == "Orc": symbol = 'o'
        elif unit.type == "Archer": symbol = 'A'
        elif unit.type == "Healer": symbol = '+'
        elif unit.type == "BOSS": symbol = 'Ω' if not unit.is_raged else 'X' 
        
        try: display_map[unit.pos[0]][unit.pos[1]] = symbol
        except: pass

    # Draw Map
    print("   0 1 2 3 4")
    for i, row in enumerate(display_map):
        print(f"{i}  {' '.join(row)}")
    
    print("-" * 40)
    print("LEGEND: [^] High Ground | [&] Bush | [H] Hero | [o] Orc | [+] Healer | [Ω] Boss")
    
    # 3. LOG MESSAGES (UI)
    if hasattr(state, 'log_message') and state.log_message:
        print(f"\n📢 {state.log_message}")

def play_game():
    game = GameState()
    
    print("🚀 GAME STARTING... DIFFICULTY: HARDCORE")
    time.sleep(2)

    # --- INITIAL WAVE START ---
    game.spawn_enemy()
    game.spawn_enemy()

    while not game.game_over:
        game.turn_count += 1
        
        # ==========================================
        # 1. HERO TURN (AI AGENT - MINIMAX)
        # ==========================================
        print_game_state(game)
        
        action = get_best_move(game)
        
        action_type, data = action
        if action_type == 'move':
            game.log_message = f"Hero moved to: {data}"
        elif action_type == 'attack':
            target = data
            game.log_message = f"Hero attacked -> {target.type} (HP: {target.hp})"
        elif action_type == 'wait':
            game.log_message = "Hero is waiting..."
            
        game.apply_move(game.hero, action)
        print_game_state(game)
        
        if not game.hero.is_alive(): break

        # ==========================================
        # 2. ENEMY TURN (SMART PATHFINDING UPDATE)
        # ==========================================
        enemies = [u for u in game.units if u.uid == ENEMY_ID]
        
        if not enemies:
            pass 
        else:
            for enemy in enemies:
                if not enemy.is_alive(): continue
                
                # Boss Rage Control
                if enemy.type == "BOSS" and enemy.hp < (BOSS_HP * BOSS_RAGE_THRESHOLD):
                    if not enemy.is_raged:
                        enemy.is_raged = True
                        enemy.dmg += 2
                        enemy.move_range += 1
                        game.log_message = "⚠️ BOSS ENRAGED! (RAGE MODE ACTIVATED)"
                        print_game_state(game)
                        time.sleep(1)

                # --- SMART MOVEMENT ---
                dist_to_hero = abs(enemy.pos[0] - game.hero.pos[0]) + abs(enemy.pos[1] - game.hero.pos[1])
                
                # 1. Attack if in range (Priority)
                if dist_to_hero <= enemy.attack_range:
                    game.apply_move(enemy, ('attack', game.hero))
                    game.log_message = f"{enemy.type} hit Hero! (-{enemy.dmg} HP)"
                
                # 2. Move if cannot attack
                else:
                    legal_moves = game.get_legal_moves(enemy)
                    move_moves = [m for m in legal_moves if m[0] == 'move']
                    
                    if move_moves:
                        # --- NEW LOGIC: FLANKING ---
                        # Sort all possible moves by distance to Hero (Ascending)
                        move_moves.sort(key=lambda m: abs(m[1][0] - game.hero.pos[0]) + abs(m[1][1] - game.hero.pos[1]))
                        
                        # Best move (Shortest distance)
                        best_move = move_moves[0]
                        
                        # --- LOOP BREAKER: FLANKING (FOR ALL ENEMIES) ---
                        # If stuck behind another unit, try to flank (move sideways)
                        if len(move_moves) > 1:
                            # 30% chance to pick the 2nd best move (Flanking/Shortcut)
                            if random.random() < 0.3:
                                best_move = move_moves[1]

                        game.apply_move(enemy, best_move)
                        game.log_message = f"{enemy.type} is repositioning..."
                
                print_game_state(game)
                time.sleep(0.3) 
                
                if not game.hero.is_alive():
                    game.game_over = True
                    break
        
        if game.game_over: break

        # ==========================================
        # 3. WAVE CONTROL
        # ==========================================
        enemies = [u for u in game.units if u.uid == ENEMY_ID]
        
        if not enemies: # Wave Cleared
            print("\n" + "="*40)
            print(f"🎉 WAVE {game.wave_count} CLEARED! 🎉")
            
            heal_amount = max(5, 15 - game.wave_count) 
            max_hp_bonus = 5 if game.wave_count < 5 else 2
            
            print(f"💪 UPGRADE: +{heal_amount} HP, +{max_hp_bonus} MAX HP")
            print("="*40)
            
            game.hero.max_hp += max_hp_bonus
            game.hero.hp += heal_amount
            if game.hero.hp > game.hero.max_hp:
                game.hero.hp = game.hero.max_hp
            
            time.sleep(3)
            game.wave_count += 1
            
            if game.wave_count % 5 == 0:
                game.log_message = "👹 BOSS WAVE INCOMING!"
                game.spawn_enemy(is_boss=True)
            else:
                game.log_message = f"🌊 WAVE {game.wave_count} - ENEMIES INCOMING!"
                enemy_num = min(2 + (game.wave_count // 2), 8)
                for _ in range(enemy_num):
                    game.spawn_enemy()

    # --- GAME OVER SCREEN ---
    clear_screen()
    print("\n" * 3)
    print("💀💀 GAME OVER 💀💀")
    print(f"🏆 SCORE (KILLS): {game.kill_count}")
    print(f"🌊 WAVES SURVIVED: {game.wave_count}")
    print("\n")

if __name__ == "__main__":
    play_game()