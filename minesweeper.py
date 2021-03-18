"""A command line version of Minesweeper"""
import random
import re
import time
from string import ascii_lowercase

from knowledgebase import KnowledgeBase
import read


def setupgrid(gridsize, start, numberofmines):
    emptygrid = [['0' for i in range(gridsize)] for i in range(gridsize)]

    mines = getmines(emptygrid, start, numberofmines)

    for i, j in mines:
        emptygrid[i][j] = 'X'

    grid = getnumbers(emptygrid)

    return (grid, mines)


def showgrid(grid):
    gridsize = len(grid)

    horizontal = '   ' + (4 * gridsize * '-') + '-'

    # Print top column letters
    toplabel = '     '

    for i in ascii_lowercase[:gridsize]:
        toplabel = toplabel + i + '   '

    print(toplabel + '\n' + horizontal)

    # Print left row numbers
    for idx, i in enumerate(grid):
        row = '{0:2} |'.format(idx + 1)

        for j in i:
            row = row + ' ' + j + ' |'

        print(row + '\n' + horizontal)

    print('')


def getrandomcell(grid):
    gridsize = len(grid)

    a = random.randint(0, gridsize - 1)
    b = random.randint(0, gridsize - 1)

    return (a, b)


def getneighbors(grid, rowno, colno):
    gridsize = len(grid)
    neighbors = []

    for i in range(-1, 2):
        for j in range(-1, 2):
            if i == 0 and j == 0:
                continue
            elif -1 < (rowno + i) < gridsize and -1 < (colno + j) < gridsize:
                neighbors.append((rowno + i, colno + j))

    return neighbors


def getmines(grid, start, numberofmines):
    mines = []
    # return [(4, 6), (3, 7), (6, 4), (2, 0), (3, 5), (3, 3), (6, 2), (7, 2), (0, 2), (2, 3)]     #Winnable
    neighbors = getneighbors(grid, *start)

    for i in range(numberofmines):
        cell = getrandomcell(grid)
        while cell == start or cell in mines or cell in neighbors:
            cell = getrandomcell(grid)
        mines.append(cell)
    print("mines",mines)
    return mines


def getnumbers(grid):
    for rowno, row in enumerate(grid):
        for colno, cell in enumerate(row):
            if cell != 'X':
                # Gets the values of the neighbors
                values = [grid[r][c] for r, c in getneighbors(grid,
                                                              rowno, colno)]

                # Counts how many are mines
                grid[rowno][colno] = str(values.count('X'))

    return grid


def showcells(grid, currgrid, rowno, colno):
    # Exit function if the cell was already shown
    if currgrid[rowno][colno] != ' ':
        return

    # Show current cell
    currgrid[rowno][colno] = grid[rowno][colno]

    # Get the neighbors if the cell is empty
    if grid[rowno][colno] == '0':
        for r, c in getneighbors(grid, rowno, colno):
            # Repeat function for each neighbor that doesn't have a flag
            if currgrid[r][c] != 'F':
                showcells(grid, currgrid, r, c)


def playagain():
    choice = input('Play again? (y/n): ')

    return choice.lower() == 'y'


def parseinput(inputstring, gridsize, helpmessage):
    cell = ()
    flag = False
    message = "Invalid cell. " + helpmessage

    pattern = r'([a-{}])([0-9]+)(f?)'.format(ascii_lowercase[gridsize - 1])
    validinput = re.match(pattern, inputstring)

    if inputstring == 'help':
        message = helpmessage

    elif validinput:
        rowno = int(validinput.group(2)) - 1
        colno = ascii_lowercase.index(validinput.group(1))
        flag = bool(validinput.group(3))

        if -1 < rowno < gridsize:
            cell = (rowno, colno)
            message = ''

    return {'cell': cell, 'flag': flag, 'message': message}

def neighbors_equal(grid, i, j, equal_to):
    if isinstance(equal_to, str): equal_to = {equal_to}
    return [grid[a][b] in equal_to for a, b in getneighbors(grid, i, j)]

def init_kb(gridsize):
    # Using rules from 
    KB = KnowledgeBase([], [], 'minesweeper_kb.txt')
    print("Initializing KB")
    start, end = -1, gridsize+1
    # print(start,end)
    for i in range(start,end):
        for j in range(start,end):
            if i==start or i==end-1 or j==start or j==end-1:
                KB.kb_add_parse(f'fact: (safe c{i}{j})')
            for k in range(max(i-1,start),min(i+2,end)):
                for l in range(max(j-1, start), min(j+2, end)):
                    if i==k and j==l: continue
                    KB.kb_add_parse(f'fact: (nextTo c{i}{j} c{k}{l})')
                    KB.kb_add_parse(f'fact: (nextTo c{k}{l} c{i}{j})')
    return KB


def updateKB(grid, KB):
    # Pass facts to the KB
    for i, row in enumerate(grid):
        for j, ele in enumerate(row):
            if ele != ' ' and ele != 'F':
                KB.kb_add_parse(f'fact: (safe c{i}{j})')
                if ele != '0':
                    near_n_bombs = sum(neighbors_equal(grid, i, j, "F"))
                    near_n_safe = 8 - sum(neighbors_equal(grid, i, j, {"F"," "}))
                    KB.kb_add_parse(f'fact: (near{ele}bomb c{i}{j})')
                    KB.kb_add_parse(f'fact: (known{near_n_bombs}bomb c{i}{j})')
                    KB.kb_add_parse(f'fact: (known{near_n_safe}safe c{i}{j})')
    return KB


def findFrontier(grid):
    # Get all the positions which are next to a known quantity
    # These will be the things we theorize about
    frontier = set()
    for i, row in enumerate(grid):
        for j, ele in enumerate(row):
            if ' ' == grid[i][j] and not all(neighbors_equal(grid, i, j, {" ","F"})):
            # if ' ' == grid[i][j] and not all([' ' == grid[a][b] for a, b in getneighbors(grid, i, j)]):
                frontier.add((i, j))
    return frontier

#Deduces a safe cell from frontier cells, if possible
#If no safe cell found, returns null
def deduceSafeCell(kb, grid):
    frontierCells = findFrontier(grid)

    # print(frontierCells)
    print("thinking...")
    if frontierCells:
        for cell in frontierCells:
            cellid = "c"+str(cell[0])+str(cell[1])

            ask = read.parse_input("fact: (bomb "+cellid+")")
            # print("asking " + str(ask))
            is_entailed = kb.kb_ask(ask)
            # print("entailed:", is_entailed)
            if is_entailed: return cell,True

            ask = read.parse_input("fact: (safe "+cellid+")")
            # print("asking " + str(ask))
            is_entailed = kb.kb_ask(ask)
            # print("entailed:", is_entailed)
            if is_entailed: return cell,False
    return None,False

def playgame():
    gridsize = 10
    numberofmines = 10

    kb = init_kb(gridsize)

    currgrid = [[' ' for i in range(gridsize)] for i in range(gridsize)]

    grid = []
    flags = []
    starttime = 0

    helpmessage = ("Type the column followed by the row (eg. a5). "
                   "To put or remove a flag, add 'f' to the cell (eg. a5f).")

    showgrid(currgrid)
    print(helpmessage + " Type 'help' to show this message again.\n")

    while True:
        print("finding safe cell")
        predCell, isBomb = deduceSafeCell(kb, currgrid)
        print("done finding safe cell")

        if predCell:
            predRow, predCol = predCell
            predRow += 1
            predCol = ascii_lowercase[predCol]
            pred = predCol+str(predRow)+("f" if isBomb else "")
            print("The KB suggests the following cell: {0}".format(pred))
            minesleft = numberofmines - len(flags)
            prompt = input('Enter the cell ({0} mines left):[{1}] '.format(minesleft,pred)) or pred
        else:
            print("Pick a random cell. The KB cannot determine a safe cell.")
            minesleft = numberofmines - len(flags)
            prompt = input('Enter the cell ({0} mines left): '.format(minesleft))
        result = parseinput(prompt, gridsize, helpmessage + '\n')

        message = result['message']
        cell = result['cell']

        if cell:
            print('\n\n')
            rowno, colno = cell
            currcell = currgrid[rowno][colno]
            flag = result['flag']

            if not grid:
                grid, mines = setupgrid(gridsize, cell, numberofmines)
            if not starttime:
                starttime = time.time()

            if flag:
                # Add a flag if the cell is empty
                if currcell == ' ':
                    currgrid[rowno][colno] = 'F'
                    flags.append(cell)
                # Remove the flag if there is one
                elif currcell == 'F':
                    currgrid[rowno][colno] = ' '
                    flags.remove(cell)
                else:
                    message = 'Cannot put a flag there'

            # If there is a flag there, show a message
            elif cell in flags:
                message = 'There is a flag there'

            elif grid[rowno][colno] == 'X':
                print('Game Over\n')
                showgrid(grid)
                if playagain():
                    playgame()
                return

            elif currcell == ' ':
                showcells(grid, currgrid, rowno, colno)

            else:
                message = "That cell is already shown"

            if set(flags) == set(mines):
                minutes, seconds = divmod(int(time.time() - starttime), 60)
                print(
                    'You Win. '
                    'It took you {} minutes and {} seconds.\n'.format(minutes,
                                                                      seconds))
                showgrid(grid)
                if playagain():
                    playgame()
                return
        print("updating....")
        updateKB(currgrid, kb)
        print("updating done")
        showgrid(currgrid)
        print(message)

playgame()
