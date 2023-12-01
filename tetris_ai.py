
# Import necessary modules
from random import randrange as rand
import pygame, sys
import csv
import time
import os
import glob
# The configuration
cell_size = 18
cols =      10
rows =      22
maxfps =    10

# Define colors and shapes
colors = [
(0,   0,   0  ),
(255, 85,  85),
(100, 200, 115),
(120, 108, 245),
(255, 140, 50 ),
(50,  120, 52 ),
(146, 202, 73 ),
(150, 161, 218 ),
(35,  35,  35) # Helper color for background grid
]

# Define the shapes of the single parts
tetris_shapes = [
    [[1, 1, 1],
     [0, 1, 0]],

    [[0, 2, 2],
     [2, 2, 0]],

    [[3, 3, 0],
     [0, 3, 3]],

    [[4, 0, 0],
     [4, 4, 4]],

    [[0, 0, 5],
     [5, 5, 5]],

    [[6, 6, 6, 6]],

    [[7, 7],
     [7, 7]]
]

def rotate_clockwise(shape):
    return [
        [ shape[y][x] for y in range(len(shape)) ]
        for x in range(len(shape[0]) - 1, -1, -1)
    ]

def check_collision(board, shape, offset):
    off_x, off_y = offset
    for cy, row in enumerate(shape):
        for cx, cell in enumerate(row):
            try:
                if cell and board[ cy + off_y ][ cx + off_x ]:
                    return True
            except IndexError:
                return True
    return False

def remove_row(board, row):
    del board[row]
    return [[0 for i in range(cols)]] + board

def join_matrixes(mat1, mat2, mat2_off):
    off_x, off_y = mat2_off
    for cy, row in enumerate(mat2):
        for cx, val in enumerate(row):
            mat1[cy+off_y-1 ][cx+off_x] += val
    return mat1

def new_board():
    board = [
        [ 0 for x in range(cols) ]
        for y in range(rows)
    ]
    board += [[ 1 for x in range(cols)]]
    return board


class TetrisApp(object):
    def __init__(self):
        pygame.init()
        pygame.key.set_repeat(250, 25)
        self.width = cell_size * (cols + 6)
        self.height = cell_size * rows
        self.rlim = cell_size * cols
        self.bground_grid = [[8 if x % 2 == y % 2 else 0 for x in range(cols)] for y in range(rows)]

        self.default_font = pygame.font.Font(pygame.font.get_default_font(), 12)
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.event.set_blocked(pygame.MOUSEMOTION)

        self.next_stone = tetris_shapes[rand(len(tetris_shapes))]
        
        self.log_file = self.get_next_log_file()
        self.start_time = time.time()
        self.last_logged_time = self.start_time
        
        self.gameover = False
        self.paused = False
        self.init_game()
        
    def get_next_log_file(self):
            existing_files = glob.glob('tetris_data_*.csv')
            existing_numbers = [int(f.split('_')[-1].split('.')[0]) for f in existing_files if f.split('_')[-1].split('.')[0].isdigit()]
            next_number = max(existing_numbers, default=0) + 1
            return f'tetris_data_{next_number}.csv'
    
    def log_game_data(self):
        current_time = time.time() - self.start_time
        with open(self.log_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([current_time, self.score])

    def new_stone(self):
        self.stone = self.next_stone[:]
        self.next_stone = tetris_shapes[rand(len(tetris_shapes))]
        self.stone_x = int(cols / 2 - len(self.stone[0])/2)
        self.stone_y = 0

        if check_collision(self.board,
                           self.stone,
                           (self.stone_x, self.stone_y)):
            self.gameover = True

    def init_game(self):
        self.board = new_board()
        self.new_stone()
        self.level = 1
        self.score = 0
        self.lines = 0
        pygame.time.set_timer(pygame.USEREVENT+1, 1000)

    def disp_msg(self, msg, topleft):
        x,y = topleft
        for line in msg.splitlines():
            self.screen.blit(
                self.default_font.render(
                    line,
                    False,
                    (255,255,255),
                    (0,0,0)),
                (x,y))
            y+=14

    def center_msg(self, msg):
        for i, line in enumerate(msg.splitlines()):
            msg_image =  self.default_font.render(line, False,
                (255,255,255), (0,0,0))

            msgim_center_x, msgim_center_y = msg_image.get_size()
            msgim_center_x //= 2
            msgim_center_y //= 2

            self.screen.blit(msg_image, (
              self.width // 2-msgim_center_x,
              self.height // 2-msgim_center_y+i*22))

    def draw_matrix(self, matrix, offset):
        off_x, off_y = offset
        for y, row in enumerate(matrix):
            for x, val in enumerate(row):
                if val >= len(colors):
                    print(f"Warning: Color index out of range for value {val} at position ({x}, {y})")
                    val = 0  # Default to the first color
                if val:
                    pygame.draw.rect(
                        self.screen,
                        colors[val],
                        pygame.Rect(
                            (off_x + x) * cell_size,
                            (off_y + y) * cell_size,
                            cell_size,
                            cell_size), 0)

    def add_cl_lines(self, n):
        linescores = [0, 40, 100, 300, 1200]
        self.lines += n
        self.score += linescores[n] * self.level
        if self.lines >= self.level*6:
            self.level += 1
            newdelay = 1000-50*(self.level-1)
            newdelay = 100 if newdelay < 100 else newdelay
            pygame.time.set_timer(pygame.USEREVENT+1, newdelay)

    def move(self, delta_x):
        if not self.gameover and not self.paused:
            new_x = self.stone_x + delta_x
            if new_x < 0:
                new_x = 0
            if new_x > cols - len(self.stone[0]):
                new_x = cols - len(self.stone[0])
            if not check_collision(self.board,
                                   self.stone,
                                   (new_x, self.stone_y)):
                self.stone_x = new_x
    def quit(self):
        self.center_msg("Exiting...")
        pygame.display.update()
        sys.exit()

    def drop(self, manual):
        if not self.gameover and not self.paused:
            self.score += 1 if manual else 0
            self.stone_y += 1
            if check_collision(self.board, self.stone, (self.stone_x, self.stone_y)):
                self.board = join_matrixes(self.board, self.stone, (self.stone_x, self.stone_y))
                self.new_stone()
                cleared_rows = 0
                for i, row in enumerate(self.board[:-1]):  # Exclude the bottom boundary row
                    if 0 not in row:  # Check if the row is completely filled
                        self.board = remove_row(self.board, i)
                        cleared_rows += 1
                        break
                self.add_cl_lines(cleared_rows)
                return True
        return False


    def insta_drop(self):
        if not self.gameover and not self.paused:
            while(not self.drop(True)):
                pass

    def rotate_stone(self):
        if not self.gameover and not self.paused:
            new_stone = rotate_clockwise(self.stone)
            if not check_collision(self.board,
                                   new_stone,
                                   (self.stone_x, self.stone_y)):
                self.stone = new_stone

    def toggle_pause(self):
        self.paused = not self.paused

    def start_game(self):
        if self.gameover:
            self.init_game()
            self.gameover = False

    
    def score_board(self, board):
        # Optimal parameters
        a = -0.510066
        b = 0.760666
        c = -0.45663
        d = -0.284483

        aggregate_height = 0
        complete_lines = 0
        holes = 0
        bumpiness = 0

        column_heights = [0] * cols

        # Calculate column heights, complete lines, and holes
        for col in range(cols):
            column_filled = False
            for row in range(rows - 1):  # Exclude the bottom row
                if board[row][col] > 0:
                    column_filled = True
                    column_heights[col] = rows - row - 1  # Adjust for bottom row
                    break

        # Count holes
        for col in range(cols):
            found_block = False
            for row in range(rows):
                if board[row][col] > 0:
                    found_block = True
                elif board[row][col] == 0 and found_block:
                    holes += 1

        # Calculate aggregate height and bumpiness
        for i in range(cols):
            aggregate_height += column_heights[i]
            if i < cols - 1:
                bumpiness += abs(column_heights[i] - column_heights[i + 1])

        # Count complete lines
        complete_lines = sum(1 for row in board[:-1] if 0 not in row)
        # Score calculation
        score = (a * aggregate_height) + (b * complete_lines) + (c * holes) + (d * bumpiness)
        #print(f"Aggregate_height: {a * aggregate_height}")
        #print(f"complete_lines: {b * complete_lines}")
        #print(f"Holes: {c * holes}")
        #print(f"bumpiness: {d * bumpiness}")
        
        return score



    def run(self):
        key_actions = {
            'ESCAPE':   self.quit,
            'LEFT':     lambda: self.move(-1),
            'RIGHT':    lambda: self.move(+1),
            'DOWN':     lambda: self.drop(True),
            'UP':       self.rotate_stone,
            'p':        self.toggle_pause,
            'SPACE':    self.start_game,
            'RETURN':   self.insta_drop
        }
        
        self.gameover = False
        self.paused = False

        dont_burn_my_cpu = pygame.time.Clock()
        while True:
            current_time = time.time()
            if current_time - self.last_logged_time >= 1:  # Log data every second
                self.log_game_data()
                self.last_logged_time = current_time
            self.screen.fill((0,0,0))
            if self.gameover:
                self.log_game_data()
                self.center_msg("""Game Over!\nYour score: %d
Press space to continue""" % self.score)
            
            else:
                if self.paused:
                    self.center_msg("Paused")
                else:
                    self.execute_move()  # AI makes a move here
                    pygame.draw.line(self.screen,
                        (255,255,255),
                        (self.rlim+1, 0),
                        (self.rlim+1, self.height-1))
                    self.disp_msg("Next:", (
                        self.rlim+cell_size,
                        2))
                    self.disp_msg("Score: %d\n\nLevel: %d\
\nLines: %d" % (self.score, self.level, self.lines),
                        (self.rlim+cell_size, cell_size*5))
                    self.draw_matrix(self.bground_grid, (0,0))
                    self.draw_matrix(self.board, (0,0))
                    self.draw_matrix(self.stone,
                        (self.stone_x, self.stone_y))
                    self.draw_matrix(self.next_stone,
                        (cols+1,2))
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.USEREVENT+1:
                    self.drop(False)
                elif event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.KEYDOWN:
                    for key in key_actions:
                        if event.key == eval("pygame.K_"
                        +key):
                            key_actions[key]()

            dont_burn_my_cpu.tick(maxfps)


    def remove_complete_lines(self, board):
        # Remove complete lines from the board and return the new board
        new_board = [row for row in board if any(cell == 0 for cell in row)]
        complete_lines = len(board) - len(new_board)
        for _ in range(complete_lines):
            new_board.insert(0, [0 for _ in range(cols)])
        return new_board
    
    def evaluate_move(self, board, piece, rotation, position):
        x_position, y_position = position
        # Rotate the piece
        rotated_piece = piece
        for _ in range(rotation):
            rotated_piece = rotate_clockwise(rotated_piece)

        # Check if the move is valid (no collision)
        if check_collision(board, rotated_piece, (x_position, y_position)):
            return -1000000  # Return a very low score for invalid moves

        # Simulate placing the piece on the board
        temp_board = [row[:] for row in board]  # Create a copy of the board
        temp_board = join_matrixes(temp_board, rotated_piece, (x_position, y_position))

        # Remove any complete lines
        #temp_board = self.remove_complete_lines(temp_board)

        # Score the board state
        score = self.score_board(temp_board)

        return score
    
    def find_lowest_position(self, board, piece, x_position):
        """Finds the lowest possible Y-position for the piece at the given X-position."""
        for y_position in range(rows):
            if check_collision(board, piece, (x_position, y_position)):
                # Return the position just above the collision point
                return y_position - 1
        return rows - 1

    
    def ai_decision(self):
        best_score = None
        best_move = None
        original_stone = self.stone[:]  # Make a copy of the original stone

        for rotation in range(self.get_unique_rotations(self.stone)):
            # Apply rotation
            rotated_stone = original_stone[:]
            for _ in range(rotation):
                rotated_stone = rotate_clockwise(rotated_stone)

            for x_position in range(cols - len(rotated_stone[0]) + 1):
                # Find the lowest y position for the current x position
                y_position = self.find_lowest_position(self.board, rotated_stone, x_position)
                
                # Temporarily place the stone on the board to evaluate the move
                temp_board = self.place_stone(self.board, rotated_stone, x_position, y_position)
                
                # Evaluate the board state after placing the stone
                score = self.score_board(temp_board)
                
                if best_score is None or score > best_score:
                    best_score = score
                    best_move = (rotation, x_position, y_position)

        self.stone = original_stone  # Reset the stone to its original orientation
        return best_move

    def place_stone(self, board, stone, x, y):
        """
        Place the stone on the board at the specified x, y position
        and return the new board state without altering the original board.
        """
        temp_board = [row[:] for row in board]  # Create a copy of the board
        for dy, row in enumerate(stone):
            for dx, cell in enumerate(row):
                if cell:
                    temp_board[y + dy][x + dx] = cell
        return temp_board



    def get_unique_rotations(self, piece):
        # Identifying the piece by its shape and returning the number of unique rotations
        if piece == tetris_shapes[0]:  # Shape 1 (e.g., I)
            return 2
        elif piece == tetris_shapes[1]:  # Shape 2 (e.g., O)
            return 1
        elif piece in [tetris_shapes[2], tetris_shapes[3], tetris_shapes[4], tetris_shapes[5], tetris_shapes[6]]:  # T, L, J, S, Z
            return 4
        else:
            # Default case if no match is found
            return 4

    def execute_move(self):
        rotation, position_x, position_y = self.ai_decision()
        #print(f"Executing move: Rotating {rotation} times")
        #print(f"Moving to {position_x},{position_y}")
        while rotation > 0:
            self.rotate_stone()
            rotation -= 1
        # Move horizontally
        while position_x != self.stone_x:
            self.move(-1 if position_x < self.stone_x else 1)
        
        if position_y != self.stone_y:
            self.drop(True)
        
if __name__ == '__main__':
    App = TetrisApp()
    App.run()
