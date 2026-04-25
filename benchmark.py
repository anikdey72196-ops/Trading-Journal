import time
import sys
sys.path.append('app/routes')
from main_routes import get_inr_per_usd

def run_benchmark():
    start = time.time()
    for _ in range(5):
        get_inr_per_usd()
    end = time.time()
    print(f"Time for 5 calls: {end - start:.4f} seconds")

if __name__ == "__main__":
    run_benchmark()
