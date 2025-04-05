import pygame
import chess
import speech_recognition as sr
import pyttsx3
import random

USER_COLOR = chess.WHITE  

pygame.init()
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

WIDTH, HEIGHT = 480, 480
SQUARE_SIZE = WIDTH // 8
WHITE = (245, 245, 220)
BLACK = (139, 69, 19)
TEXT_COLOR = (0, 0, 0)

win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Voice Chess")

piece_images = {}
piece_name_map = {
    'P': 'white_pawn', 'N': 'white_knight', 'B': 'white_bishop',
    'R': 'white_rook', 'Q': 'white_queen', 'K': 'white_king',
    'p': 'black_pawn', 'n': 'black_knight', 'b': 'black_bishop',
    'r': 'black_rook', 'q': 'black_queen', 'k': 'black_king'
}
for piece, name in piece_name_map.items():
    path = f"assets/{name}.png"
    piece_images[piece] = pygame.transform.scale(
        pygame.image.load(path), (SQUARE_SIZE, SQUARE_SIZE)
    )

board = chess.Board()
font = pygame.font.SysFont("Arial", 16)
last_opponent_move = None

def draw_board():
    colors = [WHITE, BLACK]
    for row in range(8):
        for col in range(8):
            color = colors[(row + col) % 2]
            pygame.draw.rect(win, color, pygame.Rect(
                col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    for i in range(8):
        rank_label = font.render(str(8 - i), True, TEXT_COLOR)
        win.blit(rank_label, (2, i * SQUARE_SIZE + 2))
        file_label = font.render(chr(ord('A') + i), True, TEXT_COLOR)
        win.blit(file_label, (i * SQUARE_SIZE + SQUARE_SIZE - 14, HEIGHT - 18))

def draw_pieces():
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            row = 7 - (square // 8)
            col = square % 8
            win.blit(piece_images[str(piece)], (col * SQUARE_SIZE, row * SQUARE_SIZE))

def recognize_voice():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        speak("Please say your move.")
        print("🎙️ Listening...")
        audio = r.listen(source)

    try:
        text = r.recognize_google(audio)
        print(f"🗣️ Recognized: {text}")
        return text
    except sr.UnknownValueError:
        print("❌ Speech not understood.")
        speak("I could not understand. Please try again.")
        return None
    except sr.RequestError:
        print("❌ Recognition service error.")
        speak("There was an error with the speech service.")
        return None

def extract_uci_from_speech(spoken_text):
    if "what pieces do i have" in spoken_text or "my pieces left" in spoken_text or "remaining pieces" in spoken_text:
        return "query_my_pieces"

    if "where are my" in spoken_text:
        for piece in ["pawns", "knights","nights","night","lights","light","elephant", "route","horse" ,"bishops", "rooks", "queens", "king"]:
            if piece in spoken_text:
                if piece.startswith("knight") or piece in ["night", "nights","lights","light","horses"]:
                    return "query_my_knights"
                if piece.startswith("rook") or piece in ["brooke", "books","elephant", "route"]:
                    return "query_my_rooks"
                return f"query_my_{piece}"

    if "where are black" in spoken_text:
        for piece in ["pawns", "knights","nights","night","lights","light","elephant", "route","horse" ,"bishops", "rooks", "queens", "king"]:
            if piece in spoken_text:
                if piece.startswith("knight") or piece in ["night", "nights","lights","light","horses"]:
                    return "query_my_knights"
                if piece.startswith("rook") or piece in ["brooke", "books","elephant", "route"]:
                    return "query_my_rooks"
                return f"query_black_{piece}"

    if "where are white" in spoken_text:
        for piece in ["pawns", "knights","nights","night","lights","light","elephant", "route","horse" ,"bishops", "rooks", "queens", "king"]:
            if piece in spoken_text:
                if piece.startswith("knight") or piece in ["night", "nights","lights","light","horses"]:
                    return "query_my_knights"
                if piece.startswith("rook") or piece in ["brooke", "books","elephant", "route"]:
                    return "query_my_rooks"
                return f"query_white_{piece}"

    if not spoken_text:
        return None

    spoken_text = spoken_text.lower()

    if any(phrase in spoken_text for phrase in [
        "last three moves", "what were the last three moves", 
        "say last three moves", "previous three moves"
    ]):
        return "last_3_moves_request"


    if any(phrase in spoken_text for phrase in ["last move", "what was the last move", "opponent move", "previous move", "say last"]):
        return "last_move_request"

    for square in chess.SQUARE_NAMES:
        if f"what is on {square}" in spoken_text or f"what's on {square}" in spoken_text or f"which piece is on {square}" in spoken_text or f"what is at {square}" in spoken_text:
            return f"query_{square}"

    for word in ["move", "moves", "to", "square", "step", "steps", "from", "capture", "takes", "and", "by"]:
        spoken_text = spoken_text.replace(word, " ")

    num_words = {
        "one": "1", "two": "2", "three": "3", "four": "4",
        "five": "5", "six": "6", "seven": "7", "eight": "8"
    }
    for word, digit in num_words.items():
        spoken_text = spoken_text.replace(word, digit)

    words = spoken_text.strip().split()
    print(f"🔍 Processed words: {words}")

    files = {'a','b','c','d','e','f','g','h'}
    ranks = {'1','2','3','4','5','6','7','8'}
    coords = []

    for word in words:
        if len(word) == 2 and word[0] in files and word[1] in ranks:
            coords.append(word)

    if len(coords) >= 2:
        uci = coords[0] + coords[1]
        print(f"✅ Extracted UCI: {uci}")
        return uci

    fallback_clean = ''.join([c for c in spoken_text if c in 'abcdefgh12345678'])
    print(f"🧼 Cleaned fallback UCI: {fallback_clean}")
    return fallback_clean if len(fallback_clean) == 4 else None

def describe_move(move):
    temp_board = board.copy()
    temp_board.pop()
    moving_piece = temp_board.piece_at(move.from_square)
    if not moving_piece:
        return "Unable to describe the move."

    piece_name = piece_name_map[str(moving_piece)].split('_')[1].capitalize()
    from_sq = move.uci()[:2].upper()
    to_sq = move.uci()[2:].upper()

    if move.promotion:
        promo_piece = chess.piece_symbol(move.promotion).upper()
        return f"{piece_name} moves from {from_sq} to {to_sq} and promotes to {promo_piece}"

    if temp_board.is_capture(move):
        return f"{piece_name} captures at {to_sq}"
    else:
        return f"{piece_name} moves from {from_sq} to {to_sq}"
    
def speak_last_n_moves(n=3):
    move_stack = list(board.move_stack)
    if not move_stack:
        speak("No moves have been made yet.")
        return

    total = len(move_stack)
    start = max(0, total - n * 2)
    relevant_moves = move_stack[start:]
    temp_board = chess.Board()

    spoken_moves = []
    for i, move in enumerate(relevant_moves):
        color = "White" if (start + i) % 2 == 0 else "Black"
        desc = describe_move_with_board(temp_board, move)
        spoken_moves.append(f"{color}: {desc}")
        temp_board.push(move)

    for line in spoken_moves:
        speak(line)

def describe_move_with_board(temp_board, move):
    moving_piece = temp_board.piece_at(move.from_square)
    piece_name = piece_name_map[str(moving_piece)].split('_')[1].capitalize() if moving_piece else "Piece"
    from_sq = move.uci()[:2].upper()
    to_sq = move.uci()[2:].upper()
    is_capture = temp_board.is_capture(move)

    if move.promotion:
        promo_piece = chess.piece_symbol(move.promotion).upper()
        return f"{piece_name} from {from_sq} to {to_sq}, promoting to {promo_piece}"

    return f"{piece_name} {'captures at' if is_capture else 'moves from'} {from_sq} to {to_sq}"


import time  

def make_random_opponent_move():
    global last_opponent_move
    time.sleep(random.uniform(1, 2))  
    legal_moves = list(board.legal_moves)
    if legal_moves:
        move = random.choice(legal_moves)
        last_opponent_move = move
        board.push(move)
        print(f"🤖 Opponent moved: {move}")
        speak(f"My move is {describe_move(move)}")
        if board.is_check():
            speak("Check.")
        if board.is_game_over():
            handle_game_over()
def handle_game_over():
    if board.is_checkmate():
        speak("Checkmate! Game over.")
        print("🏁 Checkmate! Game over.")
    elif board.is_stalemate():
        speak("Stalemate! It's a draw.")
        print("🏁 Stalemate! It's a draw.")
    elif board.is_insufficient_material():
        speak("Draw due to insufficient material.")
        print("🏁 Draw: Insufficient material.")
    elif board.is_seventyfive_moves():
        speak("Draw due to seventy-five move rule.")
        print("🏁 Draw: 75-move rule.")
    elif board.is_fivefold_repetition():
        speak("Draw due to fivefold repetition.")
        print("🏁 Draw: Fivefold repetition.")
    else:
        speak("Game over.")
        print("🏁 Game over.")

def find_piece(board, piece_symbol, color):
    squares = []
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.symbol().lower() == piece_symbol.lower() and piece.color == color:
            squares.append(chess.square_name(square).upper())
    return squares

def main():
    global last_opponent_move
    run = True
    clock = pygame.time.Clock()

    while run:
        clock.tick(30)
        draw_board()
        draw_pieces()
        pygame.display.flip()
        if board.turn == USER_COLOR:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False

            spoken = recognize_voice()
            if spoken:
                spoken = spoken.lower()
                spoken = spoken.replace("night", "knight")
                spoken = spoken.replace("rock", "rook")
                spoken = spoken.replace("brook", "rook")
                spoken = spoken.replace("horse", "knight")
                spoken = spoken.replace("elephant", "rook")

                # ✅ Handle "Where is my [piece]?" voice queries
                if any(word in spoken for word in ["where", "my", "king", "queen", "bishop", "rook", "knight", "pawn"]):
                    piece = None
                    if "king" in spoken:
                        piece = 'K'
                    elif "queen" in spoken:
                        piece = 'Q'
                    elif "rook" in spoken:
                        piece = 'R'
                    elif "bishop" in spoken:
                        piece = 'B'
                    elif "knight" in spoken:
                        piece = 'N'
                    elif "pawn" in spoken:
                        piece = 'P'

                    if piece:
                        color = board.turn
                        locations = find_piece(board, piece, color)
                        if locations:
                            piece_name = piece_name_map[piece].split("_")[1]
                            speak(f"Your {piece_name} is on " + ", ".join(locations))
                        else:
                            speak(f"I could not find your {piece_name} on the board.")
                    continue

                move_str = extract_uci_from_speech(spoken)

                if move_str == "last_move_request":
                    if last_opponent_move:
                        move_desc = describe_move(last_opponent_move)
                        speak("Opponent's last move was: " + move_desc)
                    else:
                        speak("No move made by opponent yet.")
                    continue

                if move_str == "last_3_moves_request":
                    speak_last_n_moves()
                    continue

                if move_str and move_str.startswith("query_"):
                    square_str = move_str.split("_")[1]
                    square = chess.parse_square(square_str)
                    piece = board.piece_at(square)
                    if piece:
                        color = "White" if piece.color == chess.WHITE else "Black"
                        piece_type = piece_name_map[str(piece)].split('_')[1]
                        speak(f"There is a {color} {piece_type} on {square_str.upper()}")
                    else:
                        speak(f"There is no piece on {square_str.upper()}")
                    continue

                elif move_str == "query_my_pieces":
                    my_color = chess.WHITE if board.turn == chess.WHITE else chess.BLACK
                    my_pieces = [board.piece_at(sq) for sq in chess.SQUARES if board.piece_at(sq) and board.piece_at(sq).color == my_color]
                    types = {}
                    for p in my_pieces:
                        name = piece_name_map[str(p)].split("_")[1]
                        types[name] = types.get(name, 0) + 1
                    if types:
                        summary = ", ".join(f"{v} {k}" for k, v in types.items())
                        speak(f"You have: {summary}")
                    else:
                        speak("You have no pieces left.")

                elif move_str and (move_str.startswith("query_my_") or move_str.startswith("query_white_") or move_str.startswith("query_black_")):
                    parts = move_str.split("_")
                    color_str = parts[1]
                    piece_name = parts[2]
                    color = chess.WHITE if color_str in ["my", "white"] else chess.BLACK

                    matching_squares = []
                    for sq in chess.SQUARES:
                        piece = board.piece_at(sq)
                        if piece and piece.color == color:
                            p_name = piece_name_map[str(piece)].split("_")[1]
                            if p_name == piece_name:
                                matching_squares.append(chess.square_name(sq).upper())

                    if matching_squares:
                        speak(f"{color_str.capitalize()} {piece_name}s are on: {', '.join(matching_squares)}")
                    else:
                        speak(f"There are no {color_str} {piece_name}s on the board.")
                    continue

                if move_str:
                    try:
                        move = chess.Move.from_uci(move_str)
                        if move in board.legal_moves:
                            is_capture = board.is_capture(move)
                            moving_piece = board.piece_at(move.from_square)
                            piece_name = piece_name_map[str(moving_piece)].split('_')[1].capitalize() if moving_piece else "Piece"
                            board.push(move)
                            if board.is_check():
                                speak("Check.")
                            if board.is_game_over():
                                handle_game_over()
                                continue

                            draw_board()
                            draw_pieces()
                            pygame.display.flip()

                            from_sq = move_str[:2].upper()
                            to_sq = move_str[2:].upper()

                            if is_capture:
                                speak(f"{piece_name} captures at {to_sq}")
                            else:
                                speak(f"{piece_name} moves from {from_sq} to {to_sq}")

                            print(f"✅ You moved: {move_str}")

                            time.sleep(0.5)

                            if not board.is_game_over():
                                speak("Now my move...")
                                time.sleep(0.5)
                                make_random_opponent_move()

                                draw_board()
                                draw_pieces()
                                pygame.display.flip()
                        else:
                            speak("That's not a legal move.")
                            print("❌ Illegal move.")
                    except Exception as e:
                        speak("Invalid move format.")
                        print(f"❌ Error interpreting move: {e}")
                else:
                    speak("Couldn't extract move. Say like 'E2 to E4' or 'B1 to C3'.")

    pygame.quit()

if __name__ == "__main__":
    main()