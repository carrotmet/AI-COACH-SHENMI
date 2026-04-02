# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'D:/github.com/carrotmet/SMAICOACH/shenmi4/backend')
from main import app

print("All routes in the application:")
for route in app.routes:
    if hasattr(route, 'path'):
        print(f'Route: {route.path}')
