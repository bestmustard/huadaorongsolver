import copy
from copy import deepcopy
from heapq import heappush, heappop
import heapq
import math
import time
import argparse
import sys

#====================================================================================

char_goal = '1'
char_single = '2'

class Piece:
    """
    This represents a piece on the Hua Rong Dao puzzle.
    """

    def __init__(self, is_goal, is_single, coord_x, coord_y, orientation):
        """
        :param is_goal: True if the piece is the goal piece and False otherwise.
        :type is_goal: bool
        :param is_single: True if this piece is a 1x1 piece and False otherwise.
        :type is_single: bool
        :param coord_x: The x coordinate of the top left corner of the piece.
        :type coord_x: int
        :param coord_y: The y coordinate of the top left corner of the piece.
        :type coord_y: int
        :param orientation: The orientation of the piece (one of 'h' or 'v') 
            if the piece is a 1x2 piece. Otherwise, this is None
        :type orientation: str
        """

        self.is_goal = is_goal
        self.is_single = is_single
        self.coord_x = coord_x
        self.coord_y = coord_y
        self.orientation = orientation

    def __repr__(self):
        return '{} {} {} {} {}'.format(self.is_goal, self.is_single, \
            self.coord_x, self.coord_y, self.orientation)

class Board:
    """
    Board class for setting up the playing board.
    """

    def __init__(self, pieces):
        """
        :param pieces: The list of Pieces
        :type pieces: List[Piece]
        """

        self.width = 4
        self.height = 5

        self.pieces = pieces

        # self.grid is a 2-d (size * size) array automatically generated
        # using the information on the pieces when a board is being created.
        # A grid contains the symbol for representing the pieces on the board.
        self.grid = []
        self.__construct_grid()


    def __construct_grid(self):
        """
        Called in __init__ to set up a 2-d grid based on the piece location information.

        """

        for i in range(self.height):
            line = []
            for j in range(self.width):
                line.append('.')
            self.grid.append(line)

        for piece in self.pieces:
            if piece.is_goal:
                self.grid[piece.coord_y][piece.coord_x] = char_goal
                self.grid[piece.coord_y][piece.coord_x + 1] = char_goal
                self.grid[piece.coord_y + 1][piece.coord_x] = char_goal
                self.grid[piece.coord_y + 1][piece.coord_x + 1] = char_goal
            elif piece.is_single:
                self.grid[piece.coord_y][piece.coord_x] = char_single
            else:
                if piece.orientation == 'h':
                    self.grid[piece.coord_y][piece.coord_x] = '<'
                    self.grid[piece.coord_y][piece.coord_x + 1] = '>'
                elif piece.orientation == 'v':
                    self.grid[piece.coord_y][piece.coord_x] = '^'
                    self.grid[piece.coord_y + 1][piece.coord_x] = 'v'

    def display(self):
        """
        Print out the current board.

        """
        for i, line in enumerate(self.grid):
            for ch in line:
                print(ch, end='')
            print()

    def empty_spaces(self):
        """
        Return the indices of empty spaces.
        Return type: list

        """

        indices = []
        for i in range (5):
            for j in range (4):
                if self.grid[i][j] == '.':
                    indices.append([i, j])
        return indices

    def is_empty(self, x, y):
        """
        Return if a coordinate is empty
        
        """
        if x < 0 or x > 3 or y < 0 or y > 4:
            return False
        empty_spaces = self.empty_spaces()
        return [y, x] in empty_spaces

    def get_goal(self):
        """
        Return the coordinates of the goal for this board

        """
        for piece in self.pieces:
            if piece.is_goal:
                return [piece.coord_x, piece.coord_y]

    def __str__(self) -> str:
        return ''.join(''.join(str(i) for i in x) for x in self.grid)

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self.grid))

    
        
class State:
    """
    State class wrapping a Board with some extra current state information.
    Note that State and Board are different. Board has the locations of the pieces. 
    State has a Board and some extra information that is relevant to the search: 
    heuristic function, f value, current depth and parent.
    """

    def __init__(self, board, f, depth, parent=None):
        """
        :param board: The board of the state.
        :type board:  array
        :param f: The f value of current state.
        :type f: int
        :param depth: The depth of current state in the search tree.
        :type depth: int
        :param parent: The parent of current state.
        :type parent: Optional[State]
        """
        self.board = board
        self.f = f
        self.depth = depth
        self.parent = parent
        # self.id = hash(board)  # The id for breaking ties.

    

    def __lt__(self, other):
        return self.f < other.f


def read_from_file(filename):
    """
    Load initial board from a given file.

    :param filename: The name of the given file.
    :type filename: str
    :return: A loaded board
    :rtype: Board
    """

    puzzle_file = open(filename, "r")

    line_index = 0
    pieces = []
    g_found = False

    for line in puzzle_file:

        for x, ch in enumerate(line):

            if ch == '^': # found vertical piece
                pieces.append(Piece(False, False, x, line_index, 'v'))
            elif ch == '<': # found horizontal piece
                pieces.append(Piece(False, False, x, line_index, 'h'))
            elif ch == char_single:
                pieces.append(Piece(False, True, x, line_index, None))
            elif ch == char_goal:
                if g_found == False:
                    pieces.append(Piece(True, False, x, line_index, None))
                    g_found = True
        line_index += 1

    puzzle_file.close()

    board = Board(pieces)
    
    return board

def goal_test(state):
    if (state.board.grid[3][1] == char_goal) and (state.board.grid[4][2] == char_goal):
        return True
    else:
        return False

def new_board(old_pieces, new_piece, former_piece):
    """
    Helper function to get a new set of pieces
    :return: A new board
    :rtype: Board
    """
    new_pieces = [new_piece]
    for old_piece in old_pieces:
        if old_piece is not former_piece:
            new_pieces.append(old_piece)
    return Board(new_pieces)

def generate_successors(state):
    
    successors = []
    board = state.board
    pieces = board.pieces

    for p in pieces:
        if p.is_goal:

            # move right

            if board.is_empty(p.coord_x + 2, p.coord_y) and board.is_empty(p.coord_x + 2, p.coord_y + 1):
                new_p = Piece(True, False, p.coord_x + 1, p.coord_y, None)
                new_b = new_board (pieces, new_p, p)
                successors.append(State(new_b, manhattan(new_b) + state.depth + 1, state.depth + 1, state))

            # move left

            elif board.is_empty(p.coord_x - 1, p.coord_y) and board.is_empty(p.coord_x - 1, p.coord_y + 1):
                new_p = Piece(True, False, p.coord_x - 1, p.coord_y, None)
                new_b = new_board (pieces, new_p, p)
                successors.append(State(new_b, manhattan(new_b) + state.depth + 1, state.depth + 1, state))

            # move down

            elif board.is_empty(p.coord_x, p.coord_y + 2) and board.is_empty(p.coord_x + 1, p.coord_y + 2):
                new_p = Piece(True, False, p.coord_x, p.coord_y + 1, None)
                new_b = new_board (pieces, new_p, p)
                successors.append(State(new_b, manhattan(new_b) + state.depth + 1, state.depth + 1, state))

            # move up

            elif board.is_empty(p.coord_x, p.coord_y - 1) and board.is_empty(p.coord_x + 1, p.coord_y - 1):
                new_p = Piece(True, False, p.coord_x, p.coord_y - 1, None)
                new_b = new_board (pieces, new_p, p)
                successors.append(State(new_b, manhattan(new_b) + state.depth + 1, state.depth + 1, state))

        elif p.is_single:

            # move right

            if board.is_empty(p.coord_x + 1, p.coord_y):
                new_p = Piece(False, True, p.coord_x + 1, p.coord_y, None)
                new_b = new_board (pieces, new_p, p)
                successors.append(State(new_b, manhattan(new_b) + state.depth + 1, state.depth + 1, state))

            # move left

            if board.is_empty(p.coord_x - 1, p.coord_y):
                new_p = Piece(False, True, p.coord_x - 1, p.coord_y, None)
                new_b = new_board (pieces, new_p, p)
                successors.append(State(new_b, manhattan(new_b) + state.depth + 1, state.depth + 1, state))

            # move down

            if board.is_empty(p.coord_x, p.coord_y + 1):
                new_p = Piece(False, True, p.coord_x, p.coord_y + 1, None)
                new_b = new_board (pieces, new_p, p)
                successors.append(State(new_b, manhattan(new_b) + state.depth + 1, state.depth + 1, state))

            # move up

            if board.is_empty(p.coord_x, p.coord_y - 1):
                new_p = Piece(False, True, p.coord_x, p.coord_y - 1, None)
                new_b = new_board (pieces, new_p, p)
                successors.append(State(new_b, manhattan(new_b) + state.depth + 1, state.depth + 1, state))

        elif p.orientation is not None:

            if p.orientation == 'h':


                # move right

                if board.is_empty(p.coord_x + 2, p.coord_y):
                    new_p = Piece(False, False, p.coord_x + 1, p.coord_y, 'h')
                    new_b = new_board (pieces, new_p, p)
                    successors.append(State(new_b, manhattan(new_b) + state.depth + 1, state.depth + 1, state))

                # move left

                if board.is_empty(p.coord_x - 1, p.coord_y):
                    new_p = Piece(False, False, p.coord_x - 1, p.coord_y, 'h')
                    new_b = new_board (pieces, new_p, p)
                    successors.append(State(new_b, manhattan(new_b) + state.depth + 1, state.depth + 1, state))

                # move down

                if board.is_empty(p.coord_x, p.coord_y + 1) and board.is_empty(p.coord_x + 1, p.coord_y + 1):
                    new_p = Piece(False, False, p.coord_x, p.coord_y + 1, 'h')
                    new_b = new_board (pieces, new_p, p)
                    successors.append(State(new_b, manhattan(new_b) + state.depth + 1, state.depth + 1, state))

                # move up

                elif board.is_empty(p.coord_x, p.coord_y - 1) and board.is_empty(p.coord_x + 1, p.coord_y - 1):
                    new_p = Piece(False, False, p.coord_x, p.coord_y - 1, 'h')
                    new_b = new_board (pieces, new_p, p)
                    successors.append(State(new_b, manhattan(new_b) + state.depth + 1, state.depth + 1, state))
                    
            elif p.orientation == 'v':


                # move right

                if board.is_empty(p.coord_x + 1, p.coord_y) and board.is_empty(p.coord_x + 1, p.coord_y + 1):
                    new_p = Piece(False, False, p.coord_x + 1, p.coord_y, 'v')
                    new_b = new_board (pieces, new_p, p)
                    successors.append(State(new_b, manhattan(new_b) + state.depth + 1, state.depth + 1, state))

                # move left

                elif board.is_empty(p.coord_x - 1, p.coord_y) and board.is_empty(p.coord_x - 1, p.coord_y + 1):
                    new_p = Piece(False, False, p.coord_x - 1, p.coord_y, 'v')
                    new_b = new_board (pieces, new_p, p)
                    successors.append(State(new_b, manhattan(new_b) + state.depth + 1, state.depth + 1, state))

                # move down

                if board.is_empty(p.coord_x, p.coord_y + 2):
                    new_p = Piece(False, False, p.coord_x, p.coord_y + 1, 'v')
                    new_b = new_board (pieces, new_p, p)
                    successors.append(State(new_b, manhattan(new_b) + state.depth + 1, state.depth + 1, state))

                # move up

                if board.is_empty(p.coord_x, p.coord_y - 1):
                    new_p = Piece(False, False, p.coord_x, p.coord_y - 1, 'v')
                    new_b = new_board (pieces, new_p, p)
                    successors.append(State(new_b, manhattan(new_b) + state.depth + 1, state.depth + 1, state))
    return successors

def dfs(initial):

    frontier = [initial]

    explored = []

    while frontier != []:

        curr = frontier.pop()

        if goal_test(curr):
            return curr
        else:
            for successor in generate_successors(curr):
                if successor.board.grid not in explored:
                    frontier.append(successor)
                    explored.append(successor.board.grid)

    return None

def manhattan(board):

    goal = board.get_goal()

    return abs(goal[0] - 1) + abs(goal[1] - 3)

def astar(initial):

    frontier = [initial]
    heapq.heapify(frontier)

    explored = {initial.board: initial}

    while frontier != []:

        curr = heapq.heappop(frontier)

        if goal_test(curr):
            return curr
        else:
            for successor in generate_successors(curr):
                if successor.board not in explored or successor < explored[successor.board]:
                    heapq.heappush(frontier, successor)
                    explored[successor.board] = successor
    
    return None

def get_solution(state, outputfile):

    path = []

    state_count = 0

    while state is not None:
        path.append(state.board)
        state = state.parent

    file = open(outputfile, "w")
    
    while path != []:
        board = path.pop()

        state_count += 1

        file = open(outputfile, "a")
        for i, line in enumerate(board.grid):
            for ch in line:
                file.write(ch)
            file.write("\n")
        file.write("\n")

    print(state_count)


    

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputfile",
        type=str,
        required=True,
        help="The input file that contains the puzzle."
    )
    parser.add_argument(
        "--outputfile",
        type=str,
        required=True,
        help="The output file that contains the solution."
    )
    parser.add_argument(
        "--algo",
        type=str,
        required=True,
        choices=['astar', 'dfs'],
        help="The searching algorithm."
    )
    args = parser.parse_args()

    # read the board from the file

    board = read_from_file(args.inputfile)    
    initial = State(board, manhattan(board), 0)

    if args.algo == 'astar':
        get_solution(astar(initial), args.outputfile)
    elif args.algo == 'dfs':
        get_solution(dfs(initial), args.outputfile)

