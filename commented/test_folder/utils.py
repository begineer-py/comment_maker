import math
import random
from datetime import datetime

def calculate_distance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def generate_random_points(n, min_val=-100, max_val=100):
    points = []
    for _ in range(n):
        x = random.uniform(min_val, max_val)
        y = random.uniform(min_val, max_val)
        points.append((x, y))
    return points

def get_current_timestamp():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

def format_number(num, decimal_places=2):
    return f"{num:.{decimal_places}f}"

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def distance_to_origin(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)
    
    def __str__(self):
        return f"Point({self.x}, {self.y})" 