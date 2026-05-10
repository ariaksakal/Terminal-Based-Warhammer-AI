from constants import *
import math

def evaluate_state(state):
   
    
 
    if not state.hero.is_alive():
        return -INFINITY 
    
    
    hero_hp_ratio = state.hero.hp / state.hero.max_hp
    score = (state.hero.hp * W_HERO_HP) * (1 + (1 - hero_hp_ratio)) 
    
 
    score += state.kill_count * W_KILL_COUNT

   
    r, c = state.hero.pos

    if state.height_map[r, c] == 1:
        score += W_HIGH_GROUND

    
    if state.bush_map[r, c] == 1:
        score += W_BUSH_CONTROL

    
    enemies = [u for u in state.units if u.uid == ENEMY_ID]
    total_enemy_hp = sum(u.hp for u in enemies)
    
  
    score -= total_enemy_hp * 10.0 

    for enemy in enemies:
        dist = abs(enemy.pos[0] - r) + abs(enemy.pos[1] - c)
        

        score += (10 - dist) * 5

       
        if enemy.type == "Healer":
            score += (10 - dist) * 10 
        
      
        if enemy.type in ["Orc", "Archer", "BOSS"]:
            if dist <= 1:
                
                if hero_hp_ratio < 0.2: 
                    score -= 50 
                else: 
                    
                    score += 50 
            
            
            if enemy.type == "BOSS" and enemy.is_raged and dist <= 2:
                score -= W_BOSS_THREAT * 3

    return score