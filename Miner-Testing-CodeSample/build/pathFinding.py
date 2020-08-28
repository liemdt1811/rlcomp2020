def findPath(Map, start, end):
    h = len(Map)
    w = len(Map[0])
    M = [[min(0, Map[i][j]) for j in range(w)] for i in range(h)]
    D = [[[-99999, i, j] for j in range(w)] for i in range(h)]
    sx, sy = start
    ex, ey = end
    i, j = start
    # D[i][j] = 0
    D[sx][sy][0] = 0
    # print(M, start, end)
    # print(D)

    Dx = 1
    Dy = 1
    if sx > ex:
        Dx = -1
    if sy > ey:
        Dy = -1
    # print(Dx, Dy)

    for i in range(sx+Dx, ex+Dx, Dx):
        D[i][sy] = [D[i-Dx][sy][0] + M[i][sy], i-Dx, sy]
    for j in range(sy+Dy, ey+Dy, Dy):
        D[sx][j] = [D[sx][j-Dy][0] + M[sx][j], sx, j-Dy]

    for i in range(sx+Dx, ex+Dx, Dx):
        for j in range(sy+Dy, ey+Dy, Dy):
            if D[i-Dx][j][0] > D[i][j-Dy][0]:
                D[i][j] = [D[i-Dx][j][0] + M[i][j], i-Dx, j]
            else:
                D[i][j] = [D[i][j-Dy][0] + M[i][j], i, j-Dy]
            # D[i][j] = min(D[i-Dx][j], D[i][j-Dy]) + M[i][j]

    # for row in D:
    #     print(row)
    # path = []
    # Q = [(sx, sy)]
    # Directions = [[0, Dy], [Dx, 0]]
    # while Q:
    #     cx, cy = Q.pop()
    #     for dx, dy in Directions:
    #         if
    # print(D)
    # print(D[ex][ey])
    path = []
    i, j = ex, ey
    while i != sx or j != sy:
        path.append((i, j))
        i, j = D[i][j][1:]

    # print(path[::-1])

    return path[::-1]
