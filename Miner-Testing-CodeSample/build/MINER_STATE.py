import json
from astar import astar
from pathFinding import findPath

def str_2_json(str):
    return json.loads(str, encoding="utf-8")


# self.D = 3

class Action:
    GO_LEFT = "0"
    GO_RIGHT = "1"
    GO_UP = "2"
    GO_DOWN = "3"
    FREE = "4"
    CRAFT = "5"


class MapInfo:
    def __init__(self):
        self.max_x = 0
        self.max_y = 0
        self.golds = []
        self.obstacles = []
        self.numberOfPlayers = 0
        self.maxStep = 0

    def init_map(self, gameInfo):
        self.max_x = gameInfo["width"] - 1
        self.max_y = gameInfo["height"] - 1
        self.golds = gameInfo["golds"]
        self.obstacles = gameInfo["obstacles"]
        self.maxStep = gameInfo["steps"]
        self.numberOfPlayers = gameInfo["numberOfPlayers"]

    def update(self, golds, changedObstacles):
        self.golds = golds
        for cob in changedObstacles:
            newOb = True
            for ob in self.obstacles:
                if cob["posx"] == ob["posx"] and cob["posy"] == ob["posy"]:
                    newOb = False
                    # print("cell(", cob["posx"], ",", cob["posy"], ") change type from: ", ob["type"], " -> ",
                    #      cob["type"], " / value: ", ob["value"], " -> ", cob["value"])
                    ob["type"] = cob["type"]
                    ob["value"] = cob["value"]
                    break
            if newOb:
                self.obstacles.append(cob)
                # print("new obstacle: ", cob["posx"], ",", cob["posy"], ", type = ", cob["type"], ", value = ",
                #      cob["value"])

    def get_min_x(self):
        return min([cell["posx"] for cell in self.golds])

    def get_max_x(self):
        return max([cell["posx"] for cell in self.golds])

    def get_min_y(self):
        return min([cell["posy"] for cell in self.golds])

    def get_max_y(self):
        return max([cell["posy"] for cell in self.golds])

    def is_row_has_gold(self, y):
        return y in [cell["posy"] for cell in self.golds]

    def is_column_has_gold(self, x):
        return x in [cell["posx"] for cell in self.golds]

    def gold_amount(self, x, y):
        for cell in self.golds:
            if x == cell["posx"] and y == cell["posy"]:
                return cell["amount"]
        return 0

    def get_obstacle(self, x, y):  # Getting the kind of the obstacle at cell(x,y)
        for cell in self.obstacles:
            if x == cell["posx"] and y == cell["posy"]:
                return cell["type"]
        return -1  # No obstacle at the cell (x,y)


class State:
    STATUS_PLAYING = 0
    STATUS_ELIMINATED_WENT_OUT_MAP = 1
    STATUS_ELIMINATED_OUT_OF_ENERGY = 2
    STATUS_ELIMINATED_INVALID_ACTION = 3
    STATUS_STOP_EMPTY_GOLD = 4
    STATUS_STOP_END_STEP = 5

    def __init__(self):
        self.end = False
        self.score = 0
        self.lastAction = None
        self.id = 0
        self.x = 0
        self.y = 0
        self.energy = 0
        self.maxEnergy = 0
        self.mapInfo = MapInfo()
        self.players = []
        self.stepCount = 0
        self.status = State.STATUS_PLAYING
        self.Map = [[]]
        self.maxp = None
        self.freeCount = 0
        self.APath = []
        self.D = 0

    def init_state(self, data):  # parse data from server into object
        game_info = str_2_json(data)
        self.end = False
        self.score = 0
        self.lastAction = None
        self.id = game_info["playerId"]
        self.x = game_info["posx"]
        self.y = game_info["posy"]
        self.energy = game_info["energy"]
        self.maxEnergy = self.energy
        self.mapInfo.init_map(game_info["gameinfo"])
        self.stepCount = 0
        # self.D = self.mapInfo.maxStep // 25
        self.D = 3
        self.status = State.STATUS_PLAYING
        self.players = [{"playerId": 2, "posx": self.x, "posy": self.y},
                        {"playerId": 3, "posx": self.x, "posy": self.y},
                        {"playerId": 4, "posx": self.x, "posy": self.y}]

        self.freeCount = 0
        self.Map = [[-1 for j in range(self.mapInfo.max_x + 1)]
                    for i in range(self.mapInfo.max_y + 1)]

        for obstacle in self.mapInfo.obstacles:
            x = obstacle["posx"]
            y = obstacle["posy"]
            t = obstacle["type"]
            amount = obstacle["value"]
            if t == 1:
                self.Map[y][x] = -20
            else:
                self.Map[y][x] = amount
        for gold in self.mapInfo.golds:
            x = gold["posx"]
            y = gold["posy"]
            amount = gold["amount"]
            self.Map[y][x] = amount

        print(self.Map)

    def update_state(self, data):
        new_state = str_2_json(data)
        for player in new_state["players"]:
            if player["playerId"] == self.id:
                self.x = player["posx"]
                self.y = player["posy"]
                self.energy = player["energy"]
                self.score = player["score"]
                self.lastAction = player["lastAction"]
                self.status = player["status"]

        self.mapInfo.update(new_state["golds"], new_state["changedObstacles"])
        self.Map = [[-1 for j in range(self.mapInfo.max_x + 1)]
                    for i in range(self.mapInfo.max_y + 1)]
        for obstacle in self.mapInfo.obstacles:
            x = obstacle["posx"]
            y = obstacle["posy"]
            amount = obstacle["value"]
            t = obstacle["type"]
            if t == 1:
                self.Map[y][x] = -20
            else:
                self.Map[y][x] = amount
        for gold in self.mapInfo.golds:
            x = gold["posx"]
            y = gold["posy"]
            amount = gold["amount"]
            self.Map[y][x] = amount

        self.players = new_state["players"]
        for i in range(len(self.players) + 1, 5, 1):
            self.players.append(
                {"playerId": i, "posx": self.x, "posy": self.y})
        self.stepCount = self.stepCount + 1
        print("state updated")
        print("POSITION: {}:{}".format(self.y,self.x))
        print("TURN: {}".format(self.stepCount))

    def distance(self, x, y, mx, my):
        d = 9999999
        for ki in range(self.D):
            for kj in range(self.D):
                d = min(d, abs(ki + x - mx) + abs(kj + y - my))
        print("Distance from: [{},{}] -> [{},{}] = {}".format(x, y, mx, my, d))
        return d

    def countPlayerAtPos(self, posx, posy):
        rs = 0
        for player in self.players:
            if player["posx"] == posx and player["posy"] == posy:
                rs += 1
        return rs

    def shouldFree(self):
        if self.energy <= 5:
            self.freeCount += 1
            return True
        if self.mapInfo.maxStep - self.stepCount < 3:
            self.freeCount = 0
            return False
        if self.freeCount == 2 and (self.maxEnergy - self.energy) < (self.maxEnergy // 3):
            self.freeCount = 0
            return False
        if (self.freeCount > 0 and self.energy < self.maxEnergy) and self.freeCount < 3:
            self.freeCount += 1
            return True
        return False


    def nextTarget(self, maxp):
        if (maxp is None):
            return None
        m = 0
        x = -1
        y = -1
        print(self.stepCount, self.D)
        for ki in range(self.D):
            for kj in range(self.D):
                print("{},{}: {}".format(
                    ki + maxp[0], kj + maxp[1], self.Map[ki + maxp[0]][kj + maxp[1]]))
                if m < self.Map[ki + maxp[0]][kj + maxp[1]]:
                    m = self.Map[ki + maxp[0]][kj + maxp[1]]
                    x = ki + maxp[0]
                    y = kj + maxp[1]
                elif m == self.Map[ki + maxp[0]][kj + maxp[1]] and abs(self.y - ki - maxp[0]) + abs(self.y - kj - maxp[1]) < abs(self.y - x) + abs(self.x - y):
                    m = self.Map[ki + maxp[0]][kj + maxp[1]]
                    x = ki + maxp[0]
                    y = kj + maxp[1]
        return None if m == 0 else [x, y]

    def findm(self, x, y, min=0):
        self.maxp = [0]*3
        d = 999999
        # remainStep = self.mapInfo.maxStep - self.stepCount
        print("D", self.D)
        f = [[0 for i in range(len(self.Map[j]))]
             for j in range(len(self.Map))]
        for i in range(len(f)-self.D+1):
            for j in range(len(f[i])-self.D+1):
                for ki in range(self.D):
                    for kj in range(self.D):
                        # f[i][j] += self.Map[i+ki][j+kj]
                        # print(i+ki, j+kj)
                        f[i][j] += max(self.Map[i+ki][j+kj], 0)
                print(i,)
                if self.maxp[2] < f[i][j] and f[i][j] > min:
                    self.maxp[2] = f[i][j]
                    self.maxp[0] = i
                    self.maxp[1] = j
                    d = self.distance(y, x, self.maxp[0], self.maxp[1])
                elif self.maxp[2] == f[i][j]:
                    if d > self.distance(y, x, i, j):
                        self.maxp[2] = f[i][j]
                        self.maxp[0] = i
                        self.maxp[1] = j
                        d = self.distance(y, x, self.maxp[0], self.maxp[1])
        print(f)
        return self.maxp

    # basic algorithm
    def calcNextAction(self):

        x, y = self.x, self.y
        # Rest if energy <= 5

        if self.shouldFree():
            return Action.FREE

        self.freeCount = 0
        if self.Map[y][x] > 0:
            print("Craft at {} {}".format(y, x))
            return Action.CRAFT
        else:
            nextAction = self.nextTarget(self.maxp)
            print("Next: ", nextAction)
            if nextAction is None:
                self.maxp = self.findm(x, y)
                nextAction = self.nextTarget(self.maxp)
                print(self.maxp)
                print(nextAction)
            if nextAction[1] < x:
                return Action.GO_LEFT
            elif (nextAction[1] > x):
                return Action.GO_RIGHT
            elif (nextAction[0] < y):
                return Action.GO_UP
            elif (nextAction[0] > y):
                return Action.GO_DOWN
                
    # basic with some optimize
    def calcNextAction2(self):

        remainTurn = self.mapInfo.maxStep - self.stepCount
        print(remainTurn)
        # self.D = max(1, remainTurn // 50)
        # self.D = 3
        if self.stepCount <= 50:
            self.D = 1
        x,y = self.x, self.y
        if self.shouldFree():
            return Action.FREE

        # Dont craft if too many player here with few gold
        self.freeCount = 0
        numberOfPlayerAtPos = self.countPlayerAtPos(x,y)
        print("No of player at {} {} is {}".format(y,x,numberOfPlayerAtPos))
        print(self.Map[y][x])
        if self.Map[y][x] >= 50:
            print("Craft at {} {} {}".format(y,x, self.Map[y][x]))
            # self.crafted[y][x] = 1
            return Action.CRAFT
        
        nextAction = None
        if self.Map[y][x] == -1:
            nextAction = self.findNearby(x,y)
        if nextAction is None:
            nextAction = self.nextTarget(self.maxp)
            print("Next: ", nextAction)
            if nextAction is None:
                self.maxp = self.findm(x, y)
                nextAction = self.nextTarget(self.maxp)
                print(self.maxp)
            print("Current x,y: {},{}".format(x,y))
            print(nextAction, x, y)
        if nextAction:
            start = (y,x)
            end = tuple(nextAction)
            print("Find path {} {}".format(start, end))
            print(self.Map)
            # self.APath = astar(self.Map, start, end)
            # print(self.APath)
            # if len(self.APath) > 1:
            #     nextAction = self.APath.pop(0)
            #     nextAction = self.APath.pop(0)
            self.APath = findPath(self.Map, start, end)
            print(self.APath)
            if len(self.APath) > 1:
                nextAction = self.APath.pop(0)
            print(nextAction)
            u,v = nextAction
            if self.Map[u][v] + self.energy <= 0:
                return Action.FREE
            if nextAction[1] < x:
                return Action.GO_LEFT
            elif (nextAction[1] > x):
                return Action.GO_RIGHT
            elif (nextAction[0] < y):
                return Action.GO_UP
            elif (nextAction[0] > y):
                return Action.GO_DOWN
            if nextAction[1] == x and nextAction[0] == y and self.Map[y][x] > 0:
                return Action.CRAFT
        
        return Action.FREE

    def findNearby(self, x,y):
        for i,j in [[0, 1], [1, 0], [0,-1], [-1, 0]]:
            if y+i >= 0 and y+i <= self.mapInfo.max_y and x+j >=0 and x+j <= self.mapInfo.max_x:
                numberOfPlayerAtPos = self.countPlayerAtPos(x+j,y+i)
                if self.Map[y+i][x+j] >= 50 and numberOfPlayerAtPos == 0:
                    return (y+i, x+j)

# x = astar([[450, -10, -1, -10, 150, -20, -1, -1, -1, -1, -20, -10, -10, -10, -1, -1, -1, -1, -1, -1, -1], [-10, -10, -10, -10, -20, -1, -20, -20, -20, -20, -5, 50, -10, -10, -10, -10, -20, -5, -1, -10, -20], [-10, -10, 200, -10, -1, -10, -1, -10, -5, -5, -10, -1, -5, -10, -10, -1, -40, -40, -1, -1, -1], [-1, -5, -5, -10, -1, -1, -20, -1, 550, -5, -10, -1, -1, -1, -20, -1, -1, -20, -20, -20, -10], [-10, -1, -1, -1, -20, -1, -20, 50, 300, -5, -10, -1, -5, -1, -1, -1, -20, -5, -5, -1, -20], [-20, -5, -20, -5, -1, -10, -1, -1, -10, -20, 100, -5, -1, -1, -1, -40, -1, -10, -5, -1, -1], [-10, -5, -20, -5, -20, 500, -20, -5, -10, -20, -1, -20, -1, -20, -1, -20, -1, -10, -5, -20, -20], [-1, -5, -20, -5, -1, -10, -5, -5, -1, -1, -1, -1, -10, -1, -10, -5, -20, -20, -20, -1, -20], [1200, -5, -20, -5, -20, -20, -10, -10, -1, -20, 150, -10, -1, -10, -1, -1, -10, -5, -5, -1, 50]], (8, 19), (8, 20))
# y = findPath([[450, -10, -1, -10, 150, -20, -1, -1, -1, -1, -20, -10, -10, -10, -1, -1, -1, -1, -1, -1, -1], [-10, -10, -10, -10, -20, -1, -20, -20, -20, -20, -5, 50, -10, -10, -10, -10, -20, -5, -1, -10, -20], [-10, -10, 200, -10, -1, -10, -1, -10, -5, -5, -10, -1, -5, -10, -10, -1, -40, -40, -1, -1, -1], [-1, -5, -5, -10, -1, -1, -20, -1, 550, -5, -10, -1, -1, -1, -20, -1, -1, -20, -20, -20, -10], [-10, -1, -1, -1, -20, -1, -20, 50, 300, -5, -10, -1, -5, -1, -1, -1, -20, -5, -5, -1, -20], [-20, -5, -20, -5, -1, -10, -1, -1, -10, -20, 100, -5, -1, -1, -1, -40, -1, -10, -5, -1, -1], [-10, -5, -20, -5, -20, 500, -20, -5, -10, -20, -1, -20, -1, -20, -1, -20, -1, -10, -5, -20, -20], [-1, -5, -20, -5, -1, -10, -5, -5, -1, -1, -1, -1, -10, -1, -10, -5, -20, -20, -20, -1, -20], [1200, -5, -20, -5, -20, -20, -10, -10, -1, -20, 150, -10, -1, -10, -1, -1, -10, -5, -5, -1, 50]], (8, 19), (8, 20))
# y = findPath([[-1, -1, -10, 100, -1, -1, -20, -20, -5, -1, -1, -1, -20, -20, -1, -1, -5, -1, -20, -20, -1], [-20, -20, -10, -1, -1, -1, -5, -20, -1, -10, -1, -1, -1, -20, -1, -20, -1, -10, -20, -1, -1], [-1, -1, -20, -1, -1, -1, -1, -20, -20, -20, -1, -1, 100, -1, -1, -1, -1, 50, -10, -1, -1], [-1, -1, -1, -1, -10, -1, -1, -1, -1, -1, -1, -1, -20, 50, -10, -1, -1, -20, -20, -1, -1], [-10, -1, 200, -10, -10, 300, -1, -1, -10, -10, -1, -1, -5, -1, -20, -1, -1, -5, -20, -1, -1], [-1, -20, -1, -1, -1, -1, -1, -5, -1, -1, -20, -20, -1, -1, -1, -1, -1, -1, -10, -1, -1], [-1, -20, -20, -1, -1, -20, -20, -1, -1, 700, -20, -1, -1, -1, -10, -20, -20, -1, -1, -1, 100], [-1, -1, -1, 500, -1, -1, -20, -1, -10, -10, -20, -20, -1, -1, -10, -1, -5, -1, -1, -20, -1], [-20, -20, -1, -10, -1, -20, -10, -1, 400, -10, -20, -20, 500, -1, -10, -1, -5, 100, -1, -1, -1]], (0,1), (6,9))
# print(y)