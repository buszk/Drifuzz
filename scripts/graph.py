#!/usr/bin/env python3

import os
import argparse
import statistics
from pathlib import Path
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser()

parser.add_argument("--result", type=Path, default="/data/zekun/drifuzz", help="The directory that holds the fuzzing results")
parser.add_argument("--target", default="all", help="The target(s) to generate graphs")
parser.add_argument("--out", type=Path, default=Path(__file__).parent.parent/"graphs", help="The output directory")

args = parser.parse_args()

if not args.out.exists():
    os.mkdir(args.out)

assert args.result.exists()


def coverage_result(target, modeled, concolic):
    def inner_dirname():
        if not modeled and not concolic:
            return f"work-{target}-random"
        elif not modeled and concolic:
            return f"work-{target}-conc"
        elif modeled and not concolic:
            return f"work-{target}-model"
        else:
            return f"work-{target}-conc-model"
    
    results = []
    for x in args.result.glob(f"result-{target}-{1 if concolic else 0}-{1 if modeled else 0}-*"):
        data_file = x / inner_dirname() / "evaluation" / "data.csv"
        assert data_file.exists()
        with open(data_file, 'r') as f:
            last_line = f.readlines()[-1]
            cov = int(last_line.split(';')[-1])
            results.append(cov)
    print(statistics.median(results))
    return results

def plot_one(target):
    bp = plt.boxplot([
                    coverage_result(target, False, False),  
                    coverage_result(target, False, True), 
                    coverage_result(target, True, False), 
                    coverage_result(target, True, True), 
                    ],labels=["Random Fuzzing", "Concolic", "Golden-seed", "Golden-seed Concolic"])
    plt.title(target)
    plt.ylabel("Coverage(bytes)")
    plt.savefig(args.out / target)
    plt.clf()

targets = ["ath9k", "ath10k_pci", "rtwpci", "8139cp", "atlantic", "stmmac_pci", "snic"]
if args.target == "all":
    for t in targets:
        plot_one(t)
else:
    plot_one(args.target)
