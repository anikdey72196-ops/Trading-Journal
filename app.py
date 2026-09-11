import runpy
import sys
import os

if __name__ == '__main__':
    target_path = os.path.join(os.path.dirname(__file__), 'app', 'routes', 'app.py')
    routes_dir = os.path.dirname(target_path)
    if routes_dir not in sys.path:
        sys.path.insert(0, routes_dir)
    runpy.run_path(target_path, run_name='__main__')