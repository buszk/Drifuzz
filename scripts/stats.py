#!/usr/bin/env python3

import os
import argparse
import statistics
from pathlib import Path
import scipy.stats as ss

parser = argparse.ArgumentParser()

parser.add_argument("--result", type=str, default="/data/USER/drifuzz", help="The directory that holds the fuzzing results")
parser.add_argument("--target", default="all", help="The target(s) to generate graphs")
# parser.add_argument("--out", type=Path, default=Path(__file__).parent.parent/"graphs", help="The output directory")

args = parser.parse_args()

# if not args.out.exists():
#     os.mkdir(args.out)

resultdir = args.result
if 'USER' in resultdir:
    resultdir = resultdir.replace('USER', os.environ.get('USER'))
resultdir = Path(resultdir)
assert resultdir.exists()


settings = [
    'random seed',
    'random seed +concolic',
    'golden seed',
    'golden seed +concolic',
]
# ["Random Fuzzing", "Concolic", "Golden-seed", "Golden-seed Concolic"]
target_means = {}

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
    for x in resultdir.glob(f"result-{target}-{1 if concolic else 0}-{1 if modeled else 0}-*"):
        bitmap_file = x / inner_dirname() / "bitmap"
        with open(bitmap_file, 'rb') as f:
            bs = f.read()
            cov= 0
            for i in range(int(len(bs)/8)):
                s = bs[i*8:i*8+8]
                if s != b'\x00\x00\x00\x00\x00\x00\x00\x00':
                    cov += 1
            results.append(cov)
    return results

def compare(data, t, c ):
    # print(data[t])
    # print(data[c])
    pvalue = ss.mannwhitneyu(data[t], data[c], alternative="greater").pvalue
    print(f"{settings[t]} vs {settings[c]}: p-value {round(pvalue, 4)}")

    # print(ss.mannwhitneyu(data[t], data[c], alternative="greater").pvalue)

def stat_one(target):
    global target_means
    ff = coverage_result(target, False, False)
    ft = coverage_result(target, False, True)
    tf = coverage_result(target, True, False)
    tt = coverage_result(target, True, True)
    data = [ff, ft, tf, tt]
    print("=" *10 + target + "="*10)
    compare(data, 1, 0)
    compare(data, 2, 0)
    compare(data, 3, 1)
    compare(data, 3, 0)
    mean_ratio = statistics.mean(tt) / statistics.mean(ff)
    print(f"mean ratio {mean_ratio}")
    print(f"{target} & {statistics.mean(ff)} & {statistics.mean(ft)} & {statistics.mean(tf)} & {statistics.mean(tt)} & {round(mean_ratio*100-100, 1)}")

    target_means[target] = mean_ratio

targets = ["ath9k", "ath10k_pci", "rtwpci", "8139cp", "atlantic", "stmmac_pci", "snic"]
if args.target == "all":
    for t in targets:
        stat_one(t)
    drivers = ["ath9k", "ath10k_pci", "rtwpci"]
    geo_mean = statistics.geometric_mean([target_means[t] for t in drivers])
    print(f"WiFi drivers coverage increase geo-mean: {geo_mean}")
    drivers = ["8139cp", "atlantic", "stmmac_pci", "snic"]
    geo_mean = statistics.geometric_mean([target_means[t] for t in drivers])
    print(f"Ethernet drivers coverage increase geo-mean: {geo_mean}")
else:
    stat_one(args.target)

