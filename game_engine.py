import numpy as np
import random
import copy
from constants import *

class Unit:
    def __init__(self, uid, u_type, hp, dmg, move_range, attack_range, pos):
        self.uid = uid
        self.type = u_type  # "Hero", "Orc", "Archer", "Healer", "BOSS"
        self.hp = hp
        self.max_hp = hp
        self.dmg = dmg
        self.move_range = move_range
        self.attack_range = attack_range
        self.pos = pos # (row, col)
        self.is_raged = False # Boss için

    def is_alive(self):
        return self.hp > 0

class GameState:
    def __init__(self):
        # --- KATMANLI HARİTA SİSTEMİ ---
        self.board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
        
        # High Ground Haritası (Şeytan Üçgeni)
        self.height_map = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
        self.height_map[1, 1] = 1; self.height_map[1, 3] = 1; self.height_map[3, 2] = 1

        # Çalı Haritası
        self.bush_map = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
        self.bush_map[2, 2] = 1; self.bush_map[0, 2] = 1

        self.units = []
        self.turn_count = 0
        self.kill_count = 0
        self.game_over = False
        self.log_message = "" 
        self.wave_count = 1 # Dalga sayacı burada dursun

        # Hero'yu Başlat
        self.hero = Unit(HERO_ID, "Hero", HERO_MAX_HP, HERO_DMG, HERO_MOVE, HERO_RANGE, (1, 1))
        self.units.append(self.hero)
        self.update_board()

    def update_board(self):
        """Birimlerin konumunu matrise işler."""
        self.board.fill(0)
        for unit in self.units:
            if unit.is_alive():
                self.board[unit.pos] = unit.uid
            else:
                self.units.remove(unit) 

    def clone(self):
        """AI Simülasyonu için kopya."""
        new_state = copy.deepcopy(self)
        return new_state

    def get_legal_moves(self, unit):
        """Tüm yasal hamleleri listele."""
        moves = []
        if not unit.is_alive(): return moves

        r, c = unit.pos

        # 1. HAREKET (Move)
        for dr in range(-unit.move_range, unit.move_range + 1):
            for dc in range(-unit.move_range, unit.move_range + 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    dist = abs(nr - r) + abs(nc - c)
                    if dist <= unit.move_range and dist > 0:
                        if self.board[nr, nc] == EMPTY:
                            moves.append(('move', (nr, nc)))

        # 2. SALDIRI (Attack)
        for target in self.units:
            if target.uid != unit.uid and target.is_alive():
                dist = abs(target.pos[0] - r) + abs(target.pos[1] - c)
                if dist <= unit.attack_range:
                    moves.append(('attack', target))
        
        # 3. BEKLE (Wait)
        moves.append(('wait', unit.pos))

        return moves

    def apply_move(self, unit, move_action):
        """Hamleyi uygula."""
        action_type, data = move_action

        if action_type == 'move':
            unit.pos = data
        
        elif action_type == 'attack':
            target = data
            damage = unit.dmg
            
            # --- MEKANİKLER ---
            if self.height_map[unit.pos] == 1 and self.height_map[target.pos] == 0:
                damage += HIGH_GROUND_DMG_BONUS
            
            if self.bush_map[target.pos] == 1:
                damage = int(damage * BUSH_DEFENSE_BONUS) 

            if unit.type == "BOSS" and unit.is_raged:
                damage += 2

            target.hp -= damage
            
            # Sparta Tekmesi (Sadece High Ground'dan vurulursa)
            if self.height_map[unit.pos] == 1 and self.height_map[target.pos] == 0:
                self.apply_knockback(unit, target)

            if not target.is_alive():
                if target.uid == ENEMY_ID: self.kill_count += 1
                if target.uid == HERO_ID: self.game_over = True

        self.update_board()

    def apply_knockback(self, attacker, victim):
        """Düşmanı 1 kare geri it."""
        ar, ac = attacker.pos
        vr, vc = victim.pos
        dr, dc = vr - ar, vc - ac
        push_r, push_c = vr + dr, vc + dc
        
        if 0 <= push_r < BOARD_SIZE and 0 <= push_c < BOARD_SIZE:
            if self.board[push_r, push_c] == EMPTY:
                victim.pos = (push_r, push_c) 
            else:
                victim.hp -= 3 # Duvar hasarı
        else:
             victim.hp -= 3 

    def spawn_enemy(self, is_boss=False):
        """
        ZORLAŞTIRILMIŞ SPAWN SİSTEMİ
        Dalga arttıkça düşmanlar güçlenir.
        """
        multiplier = 1.0 + (self.wave_count * 0.2) # Her wave %20 güçlenirler
        
        if is_boss:
            hp = int(BOSS_HP * multiplier)
            dmg = int(BOSS_DMG + (self.wave_count // 2)) # Her 2 wave'de +1 Hasar
            boss = Unit(ENEMY_ID, "BOSS", hp, dmg, 2, 1, (4, 4))
            self.units.append(boss)
        else:
            empty_spots = []
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if self.board[r,c] == 0: empty_spots.append((r,c))
            
            if empty_spots:
                pos = random.choice(empty_spots)
                roll = random.random()
                
                # İSTATİSTİKLER (SCALING)
                # Wave 1: Orc HP 10
                # Wave 5: Orc HP 20
                # Wave 10: Orc HP 30
                base_hp_add = self.wave_count * 2 
                base_dmg_add = self.wave_count // 3 # Her 3 wave'de +1 hasar

                if roll < 0.2: # Healer
                     self.units.append(Unit(ENEMY_ID, "Healer", HEALER_HP + base_hp_add, 0, 2, 1, pos))
                elif roll < 0.5: # Archer
                     self.units.append(Unit(ENEMY_ID, "Archer", ARCHER_HP + base_hp_add, ARCHER_DMG + base_dmg_add, 2, ARCHER_RANGE, pos))
                else: # Orc
                     self.units.append(Unit(ENEMY_ID, "Orc", ORC_HP + base_hp_add, ORC_DMG + base_dmg_add, 2, 1, pos))
                
                self.update_board()