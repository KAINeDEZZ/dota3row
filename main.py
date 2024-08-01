import pyautogui
import cv2
import numpy as np
import time

import pyscreeze

BASE_Y = 130
BASE_X = 230

SIZE = 70
OFFSET = 20


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def get_near(self):
        result = []

        if self.x != 0:
            result.append(Point(self.x - 1, self.y))

        if self.x != 7:
            result.append(Point(self.x + 1, self.y))

        if self.y != 0:
            result.append(Point(self.x, self.y - 1))

        if self.y != 7:
            result.append(Point(self.x, self.y + 1))

        return result

    def located_by(self, point):
        if self.x > point.x:
            return 'r'
        elif self.x < point.x:
            return 'l'
        elif self.y > point.y:
            return 'b'
        elif self.y < point.y:
            return 't'

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash(f'{self.x}_{self.y}')

    def __repr__(self):
        return f'<Point {self.x}, {self.y}>'


class Gem(Point):
    def __init__(self, x, y,  name):
        super().__init__(x, y)
        self.name = name

    def __hash__(self):
        return hash(f'{self.x}_{self.y}_{self.name}')

    def __repr__(self):
        return f'<Gem {self.name} {self.x}, {self.y}>'


class Map:
    def __init__(self):
        self.map = []

        for i in range(8):
            row = [None] * 8
            self.map.append(row)

    def insert(self, gems):
        for y in range(8):
            for x in range(8):
                if gems[y][x]:
                    self.map[y][x] = gems[y][x]

    def print(self):
        for y in range(8):
            for x in range(8):
                if self.map[y][x]:
                    print(self.map[y][x]['name'], end=' ')
                else:
                    print('--', end=' ')

            print('')

    def find_near(self, point, name, exclude):
        near_gems = []
        for near_point in point.get_near():
            if near_point in exclude:
                continue

            gem = self[near_point]
            if gem and gem.name == name:
                near_gems.append(gem)

        return near_gems

    def __getitem__(self, item):
        gem = self.map[item.y][item.x]
        return Gem(**gem) if gem else None


def create_map():
    game_map = Map()
    templates = [
        ('DB', ('db.png', 'db2.png', 'db3.png')),
        ('BL', ('bl.png', 'bl2.png', 'bl3.png')),
        ('LB', ('lb.png', 'lb2.png', 'lb3.png')),
        ('PI', ('pi.png', 'pi2.png', 'pi3.png')),
        ('RE', ('re.png', 're2.png', 're3.png')),
        ('YE', ('ye.png', 'ye2.png', 'ye3.png')),
    ]
    for name, i in templates:
        for pic in i:
            try:
                gems = list(pyautogui.locateAllOnScreen(f'images/{pic}', confidence=0.85))
            except pyscreeze.ImageNotFoundException:
                continue

            gems = normalize_gems(name, gems)
            gems = separete_lines(gems)

            game_map.insert(gems)

    return game_map


def map_sum(gems):
    return sum(len(j) for j in (list(filter(bool, i)) for i in gems))


def normalize_gems(name, gems):
    result = []

    for gem in gems:
        result.append({'name': name, 'x': gem.left + gem.width / 2, 'y': gem.top + gem.height / 2})

    return result


def separete_lines(gems):
    result = [[None] * 8 for i in range(8)]
    move = SIZE + OFFSET

    limits = []

    for index in range(8):
        limits.append({
            'x': [BASE_X + index * move, BASE_X + SIZE + index * move],
            'y': [BASE_Y + index * move, BASE_Y + SIZE + index * move]
        })

    for i in gems:
        y = None
        x = None

        for index, limit in enumerate(limits):
            if limit['y'][0] <= i['y'] <= limit['y'][1]:
                y = index

            if limit['x'][0] <= i['x'] <= limit['x'][1]:
                x = index

        if x is not None and y is not None:
            result[y][x] = i
        else:
            if x is not None:
                print(f'Not found x: {i["x"]}')

            if y is not None:
                print(f'Not found y: {i["y"]}')

    return result


def find_move_2(game_map):
    for count in range(5, 2, -1):
        for y in reversed(range(8)):
            for x in reversed(range(8)):
                point = Point(x, y)

                gems_x, gems_y, points_x, points_y = get_lines(game_map, point, count)
                for pos, stack, points in zip(('x', 'y'), (gems_x, gems_y), (points_x, points_y)):
                    if len(points) < count:
                        continue

                    for name in stack:
                        if stack[name] == count - 1:
                            different_point = find_different(game_map, points, name)
                            for next_gem in game_map.find_near(different_point, name, points):
                                return [next_gem, game_map[different_point]]


def get_lines(game_map, point, count):
    gems_x = {}
    points_x = set()
    gems_y = {}
    points_y = set()

    for i in range(count):
        if point.y - i >= 0:
            y_point = Point(point.x, point.y - i)
            gem_y = game_map[y_point]
            if gem_y:
                if not gems_y.get(gem_y.name):
                    gems_y[gem_y.name] = 0

                points_y.add(Point(point.x, point.y - i))
                gems_y[gem_y.name] += 1

        if point.x - i >= 0:
            x_point = Point(point.x - i, point.y)

            gem_x = game_map[x_point]
            if gem_x:
                if not gems_x.get(gem_x.name):
                    gems_x[gem_x.name] = 0

                points_x.add(Point(point.x - i, point.y))
                gems_x[gem_x.name] += 1

    return gems_x, gems_y, points_x, points_y


def find_different(game_map, points, name):
    for point in points:
        gem = game_map[point]
        if not gem or gem.name != name:
            return point


def find_near(game_map, x, y, name):
    if y != 0 and game_map[y - 1][x] and game_map[y - 1][x]['name'] == name:
        yield {'x': x, 'y': y - 1, 'p': 't'}

    if y != 7 and game_map[y + 1][x] and game_map[y + 1][x]['name'] == name:
        yield {'x': x, 'y': y + 1, 'p': 'b'}

    if x != 0 and game_map[y][x - 1] and game_map[y][x - 1]['name'] == name:
        yield {'x': x - 1, 'y': y, 'p': 'l'}

    if x != 7 and game_map[y][x + 1] and game_map[y][x + 1]['name'] == name:
        yield {'x': x + 1, 'y': y, 'p': 'r'}


def make_move2(move):
    delta_x = move[1].x - move[0].x
    delta_y = move[1].y - move[0].y

    result_x = move[1].x
    result_y = move[1].y

    if abs(delta_x) > 10:
        if delta_x > 0:
            result_x += 20
        else:
            result_x -= 20
    else:
        if delta_y > 0:
            result_y += 20
        else:
            result_y -= 20

    print(delta_x, delta_y)
    pyautogui.moveTo(move[0].x, move[0].y)
    pyautogui.dragTo(result_x, result_y, 0.3, button='left')


def main():
    game_map = create_map()
    game_map.print()
    print()
    move = find_move_2(game_map)
    if move:
        print(move)
        make_move2(move)
        return True


def try_restart():
    try:
        end_but = pyautogui.locateCenterOnScreen('images/end.png', confidence=0.9)
        pyautogui.click(end_but.x, end_but.y)
        time.sleep(1)
        pyautogui.click(end_but.x, end_but.y)
    except pyautogui.ImageNotFoundException:
        pass

    time.sleep(3)

    try:
        start_but = pyautogui.locateCenterOnScreen('images/start.png', confidence=0.9)
        pyautogui.click(start_but.x, start_but.y)
        time.sleep(1)
        pyautogui.click(start_but.x, start_but.y)
    except pyautogui.ImageNotFoundException:
        pass


if __name__ == "__main__":
    pyautogui.FAILSAFE = True
    while True:
        try_restart()
        for i in range(20):
            main()
