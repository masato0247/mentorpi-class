#!/usr/bin/env python3
"""保存した地図（.pgm と .yaml）から、指定した場所の寸法を測るプログラム.
 
使い方:
  python3 measure_map.py 地図.yaml 測定箇所.yaml [--csv 結果.csv]
"""
import argparse
import csv
import math
import os
 
import numpy as np
import yaml
 
OCCUPIED_MAX = 100   # これより暗い画素は「壁」とみなす（地図では黒＝0）
FREE_MIN = 230       # これより明るい画素は「何もない場所」とみなす（白＝254）
 
 
def read_pgm(path):
    """P5形式（バイナリ）のPGM画像を読み込む."""
    with open(path, 'rb') as f:
        data = f.read()
    tokens = []
    pos = 0
    while len(tokens) < 4:
        while data[pos:pos + 1].isspace():
            pos += 1
        if data[pos:pos + 1] == b'#':
            while data[pos:pos + 1] not in (b'\n', b''):
                pos += 1
            continue
        start = pos
        while not data[pos:pos + 1].isspace():
            pos += 1
        tokens.append(data[start:pos])
    pos += 1
    if tokens[0] != b'P5':
        raise ValueError('P5形式のPGMではありません: ' + path)
    width, height, maxval = int(tokens[1]), int(tokens[2]), int(tokens[3])
    if maxval > 255:
        raise ValueError('16ビットのPGMには対応していません')
    img = np.frombuffer(data, dtype=np.uint8, count=width * height, offset=pos)
    return img.reshape((height, width))
 
 
class OccupancyMap:
    """地図の画像と、画像のマスと実際の座標（m）の対応."""
 
    def __init__(self, yaml_path):
        with open(yaml_path) as f:
            info = yaml.safe_load(f)
        image_path = info['image']
        if not os.path.isabs(image_path):
            base = os.path.dirname(os.path.abspath(yaml_path))
            image_path = os.path.join(base, image_path)
        self.img = read_pgm(image_path)
        if info.get('negate', 0):
            self.img = 255 - self.img
        self.res = float(info['resolution'])
        self.ox = float(info['origin'][0])
        self.oy = float(info['origin'][1])
        if abs(float(info['origin'][2])) > 1e-6:
            raise ValueError('回転した地図には対応していません')
        self.h, self.w = self.img.shape
 
    def value(self, x, y):
        """座標(x, y)のマスの明るさ。地図の外なら None."""
        col = math.floor((x - self.ox) / self.res)
        row = self.h - 1 - math.floor((y - self.oy) / self.res)
        if 0 <= col < self.w and 0 <= row < self.h:
            return int(self.img[row, col])
        return None
 
 
def find_wall(m, x, y, dx, dy, max_dist=50.0):
    """(x, y) から (dx, dy) の向きに進み、最初の壁までの距離を返す."""
    step = m.res / 10
    d = 0.0
    while d <= max_dist:
        v = m.value(x + dx * d, y + dy * d)
        if v is None:
            return None
        if v < OCCUPIED_MAX:
            return d
        d += step
    return None
 
 
def measure(m, item):
    """1カ所の寸法（両側の壁の間の距離）を測る."""
    x, y = float(item['point'][0]), float(item['point'][1])
    direction = item['direction']
    if direction == 'x':
        dx, dy = 1.0, 0.0
    elif direction == 'y':
        dx, dy = 0.0, 1.0
    else:
        angle = math.radians(float(direction))
        dx, dy = math.cos(angle), math.sin(angle)
 
    start = m.value(x, y)
    if start is None or start < FREE_MIN:
        return None, '測り始める点が「何もない場所」になっていません'
    d_plus = find_wall(m, x, y, dx, dy)
    d_minus = find_wall(m, x, y, -dx, -dy)
    if d_plus is None or d_minus is None:
        return None, '壁が見つかりませんでした'
    return d_plus + d_minus, ''
 
 
def main():
    parser = argparse.ArgumentParser(description='地図の寸法を測る')
    parser.add_argument('map_yaml', help='地図の .yaml ファイル')
    parser.add_argument('points_yaml', help='測定箇所を書いた .yaml ファイル')
    parser.add_argument('--csv', help='結果を追記する CSV ファイル')
    args = parser.parse_args()
 
    m = OccupancyMap(args.map_yaml)
    with open(args.points_yaml) as f:
        items = yaml.safe_load(f)['measurements']
 
    map_name = os.path.splitext(os.path.basename(args.map_yaml))[0]
    print(f'地図: {map_name}（1マス {m.res * 100:.1f} cm）')
    print(f'{"箇所":<14}{"地図の寸法[m]":>14}{"正解[m]":>10}{"誤差[mm]":>10}')
 
    rows = []
    errors = []
    for item in items:
        name = item['name']
        truth = item.get('truth')
        value, note = measure(m, item)
        if value is None:
            print(f'{name:<14}{"---":>14}  {note}')
            rows.append([map_name, name, '', truth, '', note])
            continue
        if truth is None:
            print(f'{name:<14}{value:>14.3f}')
            rows.append([map_name, name, f'{value:.4f}', '', '', ''])
            continue
        error = value - float(truth)
        errors.append(error)
        print(f'{name:<14}{value:>14.3f}{float(truth):>10.3f}{error * 1000:>10.0f}')
        rows.append([map_name, name, f'{value:.4f}', truth, f'{error:.4f}', ''])
 
    if errors:
        rmse = math.sqrt(sum(e * e for e in errors) / len(errors))
        print(f'RMSE（誤差の大きさの平均）: {rmse * 1000:.0f} mm（{len(errors)}カ所）')
 
    if args.csv:
        new_file = not os.path.exists(args.csv)
        with open(args.csv, 'a', newline='') as f:
            writer = csv.writer(f)
            if new_file:
                writer.writerow(['map', 'name', 'measured_m', 'truth_m',
                                 'error_m', 'note'])
            writer.writerows(rows)
        print(f'結果を {args.csv} に追記しました')
 
 
if __name__ == '__main__':
    main()