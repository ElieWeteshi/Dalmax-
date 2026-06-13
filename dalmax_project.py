
import pygame  # Importe la bibliothèque Pygame pour gérer l'affichage graphique, les entrées et le temps
import random  # Importe le module natif Random pour simuler les erreurs sur les bas niveaux
import time    # Importe le module Time pour mesurer précisément le temps de réflexion de l'IA

# ==============================================================================
# CONFIGURATION DE LA DIFFICULTÉ INTÉGRÉE (DALMAX BLITZ ENGINE)
# 100 = Niveau Grand Maître Hybride (Calcul ultra-profond mais bridé à 1.5s max)
# ==============================================================================

AI_DIFFICULTY = 100

pygame.init()  

# --- CONSTANTES ---
WIDTH, HEIGHT = 600, 600  
screen = pygame.display.set_mode((WIDTH, HEIGHT))  
clock = pygame.time.Clock()  

BG = pygame.Color("darkslategray")            
BOARD_LIGHT = pygame.Color("antiquewhite")    
BOARD_DARK = pygame.Color("sienna")           
RED_PIECE = pygame.Color("red")               
BLACK_PIECE = pygame.Color("black")           
HIGHLIGHT = pygame.Color("green")             
VALID_MOVE = pygame.Color("limegreen")         
WHITE = pygame.Color("white")                 
GRAY = pygame.Color("gray")                   
GOLD = pygame.Color("gold")                   
SEL_COLOR = pygame.Color("yellow")       

# Nouvelle couleur harmonieuse pour retracer le dernier coup (Ambre/Or doux)
LAST_MOVE_COLOR = pygame.Color(230, 160, 30)

BOARD_SIZE = 10  
CELL = min((WIDTH - 20) // BOARD_SIZE, (HEIGHT - 160) // BOARD_SIZE)
BOARD_X = (WIDTH - BOARD_SIZE * CELL) // 2
BOARD_Y = 70       
PIECE_R = CELL // 2 - 4  

board = [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]
TRANSPOSITION_TABLE = {}
# Variable pour mémoriser le dernier coup : (r1, c1, r2, c2)
last_move = None 

def init_board():
    global board, TRANSPOSITION_TABLE, last_move
    board = [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    TRANSPOSITION_TABLE.clear()
    last_move = None
    for r in range(BOARD_SIZE):        
        for c in range(BOARD_SIZE):    
            if (r + c) % 2 == 1:       
                if r < 4:              
                    board[r][c] = 'b'
                elif r > 5:            
                    board[r][c] = 'r'

init_board()  

turn = 'r'  
selected = None  
valid_moves = []  
game_over = False  
winner = None  
message = "Your turn (Red)"  

def board_to_tuple(brd):
    return tuple(tuple(row) for row in brd)

def get_moves(r, c, brd):
    piece = brd[r][c]  
    if piece is None:
        return [], []  

    moves = []   
    jumps = []   
    is_king = piece in ('R', 'B')  
    color = piece.lower()  
    dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    if is_king:
        for dr, dc in dirs:
            step = 1
            enemy_found = None
            while True:
                nr, nc = r + dr * step, c + dc * step
                if not (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE):
                    break
                current_target = brd[nr][nc]
                if enemy_found is None:
                    if current_target is None:
                        moves.append((nr, nc))
                    elif current_target.lower() == color:
                        break
                    else:
                        enemy_found = (nr, nc)
                else:
                    if current_target is None:
                        jumps.append((nr, nc, enemy_found[0], enemy_found[1]))
                    else:
                        break
                step += 1
    else:
        move_dirs = [(-1, -1), (-1, 1)] if color == 'r' else [(1, -1), (1, 1)]
        for dr, dc in move_dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and brd[nr][nc] is None:
                moves.append((nr, nc))

        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                if brd[nr][nc] is not None and brd[nr][nc].lower() != color:
                    jr, jc = nr + dr, nc + dc
                    if 0 <= jr < BOARD_SIZE and 0 <= jc < BOARD_SIZE and brd[jr][jc] is None:
                        jumps.append((jr, jc, nr, nc))

    return moves, jumps  

def has_any_jumps(color, brd):
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if brd[r][c] and brd[r][c].lower() == color:
                _, jumps = get_moves(r, c, brd)
                if jumps:
                    return True  
    return False

def simulate_max_jumps(r, c, brd):
    _, jumps = get_moves(r, c, brd)
    if not jumps:
        return 0
    max_child = 0
    for jr, jc, cr, cc in jumps:
        temp_brd = [row[:] for row in brd]
        temp_brd[jr][jc] = temp_brd[r][c]
        temp_brd[r][c] = None
        temp_brd[cr][cc] = None
        max_child = max(max_child, 1 + simulate_max_jumps(jr, jc, temp_brd))
    return max_child

def get_all_legal_moves(color, brd):
    all_jumps = []
    all_moves = []
    force_jump = has_any_jumps(color, brd)

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if brd[r][c] and brd[r][c].lower() == color:
                moves, jumps = get_moves(r, c, brd)
                if force_jump:
                    for jr, jc, cr, cc in jumps:
                        temp_brd = [row[:] for row in brd]
                        temp_brd[jr][jc] = temp_brd[r][c]
                        temp_brd[r][c] = None
                        temp_brd[cr][cc] = None
                        total_caps = 1 + simulate_max_jumps(jr, jc, temp_brd)
                        all_jumps.append((total_caps, (r, c, jr, jc, cr, cc)))
                else:
                    for mr, mc in moves:
                        all_moves.append((r, c, mr, mc, None, None))

    if force_jump:
        max_cap_value = max(item[0] for item in all_jumps)
        result = [item[1] for item in all_jumps if item[0] == max_cap_value]
        result.sort(key=lambda m: (m[2] == (BOARD_SIZE-1 if color == 'b' else 0)), reverse=True)
        return result

    all_moves.sort(key=lambda m: (3 <= m[3] <= 6) + (m[2] * (1 if color == 'b' else -1)), reverse=True)
    return all_moves

def simulate_move(r1, c1, r2, c2, cr, cc, brd):
    next_brd = [row[:] for row in brd]
    next_brd[r2][c2] = next_brd[r1][c1]
    next_brd[r1][c1] = None
    if cr is not None:
        next_brd[cr][cc] = None

    if next_brd[r2][c2] == 'r' and r2 == 0:
        next_brd[r2][c2] = 'R'
    elif next_brd[r2][c2] == 'b' and r2 == BOARD_SIZE - 1:
        next_brd[r2][c2] = 'B'

    if cr is not None:
        _, jumps = get_moves(r2, c2, next_brd)
        if jumps:
            jr, jc, cr2, cc2 = jumps[0]
            return simulate_move(r2, c2, jr, jc, cr2, cc2, next_brd)

    return next_brd

def evaluate_board(brd):
    score = 0
    VAL_PION = 1000
    VAL_REINE = 3750  

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            p = brd[r][c]
            if p is None:
                continue

            if p == 'b':
                score += VAL_PION
                score += r * 35  
                if 3 <= c <= 6 and 3 <= r <= 6: score += 40  
                if r == 0: score += 75  
                if c == 0 or c == BOARD_SIZE - 1: score += 20  
            elif p == 'B':
                score += VAL_REINE
                if abs(r - c) == 0 or abs(r + c) == BOARD_SIZE - 1: score += 50 
            elif p == 'r':
                score -= VAL_PION
                score -= (BOARD_SIZE - 1 - r) * 35
                if 3 <= c <= 6 and 3 <= r <= 6: score -= 40
                if r == BOARD_SIZE - 1: score -= 75
                if c == 0 or c == BOARD_SIZE - 1: score -= 20
            elif p == 'R':
                score -= VAL_REINE
                if abs(r - c) == 0 or abs(r + c) == BOARD_SIZE - 1: score -= 50

    return score

start_time = 0
time_limit = 1.4  
abort_search = False

def minimax(brd, depth, alpha, beta, maximizing_player):
    global abort_search
    if depth > 1 and (time.time() - start_time) > time_limit:
        abort_search = True
        return evaluate_board(brd), None

    board_state = board_to_tuple(brd)
    if board_state in TRANSPOSITION_TABLE:
        stored_depth, stored_eval, stored_move = TRANSPOSITION_TABLE[board_state]
        if stored_depth >= depth:
            return stored_eval, stored_move

    if depth <= 0:
        if has_any_jumps('b' if maximizing_player else 'r', brd):
            depth += 1 
        else:
            return evaluate_board(brd), None

    if maximizing_player:
        moves = get_all_legal_moves('b', brd)
        if not moves:
            return -5000000, None
        max_eval = -99999999
        best_move = None
        for m in moves:
            next_brd = simulate_move(m[0], m[1], m[2], m[3], m[4], m[5], brd)
            ev, _ = minimax(next_brd, depth - 1, alpha, beta, False)
            if abort_search: 
                break
            if ev > max_eval:
                max_eval = ev
                best_move = m
            alpha = max(alpha, ev)
            if beta <= alpha:
                break
        if not abort_search:
            TRANSPOSITION_TABLE[board_state] = (depth, max_eval, best_move)
        return max_eval, best_move
    else:
        moves = get_all_legal_moves('r', brd)
        if not moves:
            return 5000000, None
        min_eval = 99999999
        best_move = None
        for m in moves:
            next_brd = simulate_move(m[0], m[1], m[2], m[3], m[4], m[5], brd)
            ev, _ = minimax(next_brd, depth - 1, alpha, beta, True)
            if abort_search: 
                break
            if ev < min_eval:
                min_eval = ev
                best_move = m
            beta = min(beta, ev)
            if beta <= alpha:
                break
        if not abort_search:
            TRANSPOSITION_TABLE[board_state] = (depth, min_eval, best_move)
        return min_eval, best_move

def count_pieces(color):
    count = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] and board[r][c].lower() == color:
                count += 1
    return count

def make_actual_move(r1, c1, r2, c2, captured=None):
    global last_move
    board[r2][c2] = board[r1][c1]  
    board[r1][c1] = None           
    if captured:
        board[captured[0]][captured[1]] = None  

    if board[r2][c2] == 'r' and r2 == 0:
        board[r2][c2] = 'R'  
    elif board[r2][c2] == 'b' and r2 == BOARD_SIZE - 1:
        board[r2][c2] = 'B'  

    # Enregistre le mouvement pour l'affichage des traces sur l'interface
    last_move = (r1, c1, r2, c2)

def ai_move():
    global turn, message, start_time, abort_search
    legal_moves = get_all_legal_moves('b', board)

    if not legal_moves:
        turn = 'r'
        check_game_over()
        return

    chosen_move = legal_moves[0]

    if random.randint(1, 100) <= AI_DIFFICULTY:
        start_time = time.time()
        abort_search = False

        for depth in range(1, 11):
            _, current_best = minimax(board, depth, -99999999, 99999999, True)
            if not abort_search and current_best is not None:
                chosen_move = current_best
            if abort_search:
                break
    else:
        chosen_move = random.choice(legal_moves)  

    r1, c1, r2, c2, cr, cc = chosen_move
    make_actual_move(r1, c1, r2, c2, (cr, cc) if cr is not None else None)  

    if cr is not None:
        while True:
            _, jumps = get_moves(r2, c2, board)
            if not jumps:
                break  
            jr, jc, cr2, cc2 = jumps[0]
            make_actual_move(r2, c2, jr, jc, (cr2, cc2))
            r2, c2 = jr, jc  

    turn = 'r'  
    message = "Your turn (Red)"  
    check_game_over()  

def get_valid_for_selected(sr, sc):
    moves_list = []
    moves, jumps = get_moves(sr, sc, board)
    legal = get_all_legal_moves('r', board)

    force_jump = has_any_jumps('r', board)
    if force_jump:
        for lm in legal:
            if lm[0] == sr and lm[1] == sc:
                moves_list.append((lm[2], lm[3], lm[4], lm[5]))
    else:
        for mr, mc in moves:
            moves_list.append((mr, mc, None, None))
    return moves_list

def draw_board():
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            x = BOARD_X + c * CELL
            y = BOARD_Y + r * CELL
            color = BOARD_LIGHT if (r + c) % 2 == 0 else BOARD_DARK
            pygame.draw.rect(screen, color, (x, y, CELL, CELL))

    # Trace le dernier mouvement effectué sur le plateau si présent
    if last_move:
        r1, c1, r2, c2 = last_move
        for r, c in [(r1, c1), (r2, c2)]:
            lx = BOARD_X + c * CELL
            ly = BOARD_Y + r * CELL
            # Dessine un indicateur de bordure épais pour bien cerner l'origine/destination
            pygame.draw.rect(screen, LAST_MOVE_COLOR, (lx, ly, CELL, CELL), 4)

    if selected:
        sr, sc = selected
        x = BOARD_X + sc * CELL
        y = BOARD_Y + sr * CELL
        pygame.draw.rect(screen, SEL_COLOR, (x, y, CELL, CELL), 3)  

    for vm in valid_moves:
        vr, vc = vm[0], vm[1]
        cx = BOARD_X + vc * CELL + CELL // 2
        cy = BOARD_Y + vr * CELL + CELL // 2
        pygame.draw.circle(screen, VALID_MOVE, (cx, cy), 8)  

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            piece = board[r][c]
            if piece:
                cx = BOARD_X + c * CELL + CELL // 2  
                cy = BOARD_Y + r * CELL + CELL // 2  
                is_king = piece in ('R', 'B')
                if piece.lower() == 'r':
                    pygame.draw.circle(screen, pygame.Color("maroon"), (cx + 2, cy + 2), PIECE_R)  
                    pygame.draw.circle(screen, RED_PIECE, (cx, cy), PIECE_R)                      
                    pygame.draw.circle(screen, pygame.Color("tomato"), (cx - 3, cy - 3), PIECE_R // 3) 
                    pygame.draw.circle(screen, pygame.Color("darkred"), (cx, cy), PIECE_R, 2)       
                else:
                    pygame.draw.circle(screen, pygame.Color("gray10"), (cx + 2, cy + 2), PIECE_R)   
                    pygame.draw.circle(screen, BLACK_PIECE, (cx, cy), PIECE_R)                     
                    pygame.draw.circle(screen, pygame.Color("gray30"), (cx - 3, cy - 3), PIECE_R // 3) 
                    pygame.draw.circle(screen, pygame.Color("gray20"), (cx, cy), PIECE_R, 2)        
                if is_king:
                    kf = pygame.font.Font(None, CELL // 2)  
                    kt = kf.render('K', True, GOLD)        
                    kr = kt.get_rect(center=(cx, cy))      
                    screen.blit(kt, kr)                    

def check_game_over():
    global game_over, winner, message
    red_count = count_pieces('r')
    black_count = count_pieces('b')

    if red_count == 0:  
        game_over = True
        winner = 'b'
        message = "Black wins!"
    elif black_count == 0:  
        game_over = True
        winner = 'r'
        message = "Red wins!"
    elif not get_all_legal_moves(turn, board):  
        game_over = True
        winner = 'r' if turn == 'b' else 'b'
        message = f"{'Red' if winner == 'r' else 'Black'} wins!"

running = True  
ai_timer = 0    

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:  
            running = False            
        elif event.type == pygame.MOUSEBUTTONDOWN:  
            tx, ty = event.pos  
            if game_over:  
                init_board()
                turn = 'r'
                selected = None
                valid_moves = []
                game_over = False
                winner = None
                message = "Your turn (Red)"
                continue  

            if turn != 'r':  
                continue

            bc = (tx - BOARD_X) // CELL
            br = (ty - BOARD_Y) // CELL

            if 0 <= br < BOARD_SIZE and 0 <= bc < BOARD_SIZE:  
                if board[br][bc] and board[br][bc].lower() == 'r':
                    if message == "Continue jumping!":
                        continue
                    selected = (br, bc)  
                    valid_moves = get_valid_for_selected(br, bc)  
                elif selected:
                    moved = False
                    for vm in valid_moves:
                        if vm[0] == br and vm[1] == bc:  
                            sr, sc = selected
                            captured = (vm[2], vm[3]) if vm[2] is not None else None
                            make_actual_move(sr, sc, br, bc, captured)  
                            moved = True

                            if captured:
                                _, more_jumps = get_moves(br, bc, board)
                                if more_jumps:  
                                    selected = (br, bc)  
                                    valid_moves = []
                                    legal_suite = get_all_legal_moves('r', board)
                                    for lm in legal_suite:
                                        if lm[0] == br and lm[1] == bc:
                                            valid_moves.append((lm[2], lm[3], lm[4], lm[5]))
                                    if valid_moves:
                                        message = "Continue jumping!"
                                        break  

                            selected = None
                            valid_moves = []
                            check_game_over()  
                            if not game_over:
                                turn = 'b'                     
                                message = "Black thinking..."  
                                ai_timer = 2                
                            break
                    if not moved and message != "Continue jumping!":
                        selected = None  
                        valid_moves = []

    if turn == 'b' and not game_over:
        ai_timer -= 1  
        if ai_timer <= 0:
            ai_move()  

    # --- INTERFACE ---
    screen.fill(BG)  

    font = pygame.font.Font(None, 28)
    msg_color = WHITE
    if "Red" in message or "jumping" in message:
        msg_color = pygame.Color("lightcoral")  
    elif "Black" in message:
        msg_color = pygame.Color("lightgray")
    mt = font.render(message, True, msg_color)
    mr = mt.get_rect(center=(WIDTH // 2, 25))
    screen.blit(mt, mr)

    red_count = count_pieces('r')
    black_count = count_pieces('b')
    sf = pygame.font.Font(None, 24)
    rt = sf.render(f'Red: {red_count}', True, pygame.Color("lightcoral"))
    screen.blit(rt, (10, 47))  
    bt = sf.render(f'Black: {black_count}', True, pygame.Color("lightgray"))
    screen.blit(bt, (WIDTH - 90, 47))  

    draw_board()

    pygame.draw.rect(screen, pygame.Color("saddlebrown"),
        (BOARD_X - 2, BOARD_Y - 2, BOARD_SIZE * CELL + 4, BOARD_SIZE * CELL + 4), 3)

    if not game_over:
        inf = pygame.font.Font(None, 22)
        force = has_any_jumps('r', board) if turn == 'r' else False
        if (force or message == "Continue jumping!") and turn == 'r':
            it = inf.render('You must jump (Max Rafle)!', True, pygame.Color("orange"))  
        else:
            it = inf.render(f'DALMAX ENGINE ({AI_DIFFICULTY}%) | Highlight Moves Active', True, GRAY)  
        ir = it.get_rect(center=(WIDTH // 2, BOARD_Y + BOARD_SIZE * CELL + 30))
        screen.blit(it, ir)

    if game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(140)  
        screen.blit(overlay, (0, 0))

        bf = pygame.font.Font(None, 52)
        if winner == 'r':
            wt = bf.render('You Win!', True, pygame.Color("green"))
        else:
            wt = bf.render('You Lose!', True, pygame.Color("crimson"))
        wr = wt.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
        screen.blit(wt, wr)

        sf2 = pygame.font.Font(None, 30)
        wn = 'Red' if winner == 'r' else 'Black'
        st = sf2.render(f'{wn} wins the game', True, WHITE)
        sr = st.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 15))
        screen.blit(st, sr)

        hf = pygame.font.Font(None, 26)
        ht = hf.render('Tap to play again', True, GRAY)
        hr = ht.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 55))
        screen.blit(ht, hr)

    pygame.display.flip()  
    clock.tick(30)  

pygame.quit()


# In[ ]:




