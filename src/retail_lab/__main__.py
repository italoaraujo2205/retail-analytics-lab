import argparse
import logging
from pathlib import Path

from .pipeline import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Reproducible retail analytics with synthetic data")
    parser.add_argument("command", choices=["run"])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--orders", type=int, default=24000)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    result = run(args.root, seed=args.seed, n_orders=args.orders)
    print(f"Primary metric effect: BRL {result['difference']:.2f} per randomized customer")
    print(result["decision"])


if __name__ == "__main__":
    main()
