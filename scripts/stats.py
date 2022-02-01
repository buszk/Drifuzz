#!/usr/bin/env python3
import os
import sys
import argparse
import psutil
import statistics
from pathlib import Path
import scipy.stats as ss

parser = argparse.ArgumentParser()

parser.add_argument("--result", type=str, default="/data/USER/drifuzz", help="The directory that holds the fuzzing results")
parser.add_argument("--usbresult", type=str, default="/data/USER/drifuzz-usb", help="The directory that holds the fuzzing results")
parser.add_argument("--agamottoresult", type=str, default="/data/USER/agamotto", help="The directory that holds the fuzzing results")
parser.add_argument("--usbagamottoresult", type=str, default="/data/USER/agamotto-usb", help="The directory that holds the fuzzing results")
parser.add_argument("--target", default="all", help="The target(s) to generate graphs")
# parser.add_argument("--out", type=Path, default=Path(__file__).parent.parent/"graphs", help="The output directory")
parser.add_argument("--raw", default=False, action='store_true')
parser.add_argument("--patched", default=False, action='store_true')
parser.add_argument("--agamotto", default=False, action='store_true')
parser.add_argument("--usb", default=False, action='store_true')

args = parser.parse_args()

# if not args.out.exists():
#     os.mkdir(args.out)

def parse_dir(i):
    res = i
    if 'USER' in i:
        res = i.replace('USER', os.environ.get('USER'))
    return Path(res)

resultdir = parse_dir(args.result)
agamotto_resultdir = parse_dir(args.agamottoresult)
drifuzz_usb_resultdir = parse_dir(args.usbresult)
print(f"{drifuzz_usb_resultdir=}")
agamotto_usb_resultdir = parse_dir(args.usbagamottoresult)


settings = [
    'random seed',
    'random seed +concolic',
    'golden seed',
    'golden seed +concolic',
]
# ["Random Fuzzing", "Concolic", "Golden-seed", "Golden-seed Concolic"]
target_means = {}

def statistic_significance(pvalue):
    if pvalue < 0.0001:
        return '****'
    elif pvalue < 0.001:
        return ' ***'
    elif pvalue < 0.01:
        return '  **'
    elif pvalue < 0.05:
        return '   *'
    else:
        return '    '

gstime_min = {
    "ath9k": 138,
    "ath10k_pci": 25,
    "rtwpci": 76,
    "8139cp": 40,
    "atlantic": 16,
    "snic": 14,
    "stmmac_pci": 75,
    "ar5523": 57,
    "mwifiex_usb": 2,
    "rsi_usb": 3,
}

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

    def parse_bitmap_file(x):
        bitmap_file = x / inner_dirname() / "bitmap"
        with open(bitmap_file, 'rb') as f:
            bs = f.read()
            cov= 0
            if args.patched:
                for i in range(int(len(bs)/8)):
                    s = bs[i*8:i*8+8]
                    if s != b'\x00\x00\x00\x00\x00\x00\x00\x00':
                        cov += 1
            else:
                for i in range(len(bs)):
                    if bs[i] != 0:
                        cov += 1
            return cov
    
    def parse_eval_file(x):
        cpu_count = psutil.cpu_count(logical=False)
        eval_file = x / inner_dirname() / "evaluation" / "data.csv"
        with open(eval_file, 'r') as f:
            res = 0
            for line in f:
                res = int(line.split(';')[-1])
                time = float(line.split(';')[0])
                if modeled and time > 3600 - gstime_min[target] * 60 / cpu_count:
                    return res
            return res

    results = []
    for x in resultdir.glob(f"result-{target}-{1 if concolic else 0}-{1 if modeled else 0}-*"):
        bitmap_file = x / inner_dirname() / "bitmap"
        results.append(parse_eval_file(x))
    return results

def usb_result(target):
    def parse_eval_file(x):
        cpu_count = psutil.cpu_count(logical=False)
        eval_file = x / f"work-{target}-conc-model" / "evaluation" / "data.csv"
        with open(eval_file, 'r') as f:
            res = 0
            for line in f:
                res = int(line.split(';')[-1])
                time = float(line.split(';')[0])
                if time > 3600 - gstime_min[target] * 60 / cpu_count:
                    return res
            return int(res)

    results = []
    for x in drifuzz_usb_resultdir.glob(f"{target}-*"):
        cov = parse_eval_file(x)
        if cov:
            results.append(cov)
        else:
            print(x)
    return results
		

def compare(data, t, c ):
    # print(data[t])
    # print(data[c])
    pvalue = ss.mannwhitneyu(data[t], data[c], alternative="two-sided").pvalue
    print(f"{settings[t]} vs {settings[c]}: significance {statistic_significance(pvalue)} ;p-value {round(pvalue, 4)}")


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
    print(f"mean ratio {statistics.mean(tt)}/{statistics.mean(ff)}={mean_ratio}")
    print(f"{target} & {statistics.mean(ff)} & {statistics.mean(ft)} & {statistics.mean(tf)} & {statistics.mean(tt)} & {round(mean_ratio*100-100, 1)}")

    target_means[target] = mean_ratio

agamotto_alias = {
    '8139cp': 'rtl8139',
    'atlantic': 'aqc100',
    'stmmac_pci': 'quark',
    'mwifiex_usb': 'mwifiex',
    'rsi_usb': 'rsi',
}

def parse_agamotto(target):
    if target in agamotto_alias:
        target = agamotto_alias[target]
    covers = []
    for x in agamotto_resultdir.glob(f"{target}-*"):
        log_file = x / f"{target}.log"
        max_cover = 0
        with open(log_file, encoding='ISO-8859-1') as l:
            for line in l:
                if 'covers' not in line:
                    continue
                sp = line.split(' ')
                if len(sp) != 4:
                    continue
                cover = int(sp[2])
                max_cover = max(cover, max_cover)
        covers.append(max_cover)
    return covers

def parse_agamotto_usb(target):
    if target in agamotto_alias:
        target = agamotto_alias[target]
    covers = []
    for x in agamotto_usb_resultdir.glob(f"{target}-*"):
        log_file = x / f"{x.name}.log"
        max_cover = 0
        with open(log_file, encoding='ISO-8859-1') as l:
            for line in l:
                if 'cover' not in line:
                    continue
                sp = line.split(' ')
                if len(sp) != 12:
                    continue
                cover = int(sp[7][:-1])
                max_cover = max(cover, max_cover)
        covers.append(max_cover)
    return covers

def compare_agamotto(target):
    print(target)
    drifuzz_result = coverage_result(target, True, True)
    agamotto_result = parse_agamotto(target)
    print(f"{drifuzz_result} vs {agamotto_result}")
    if not len(drifuzz_result) or not len(agamotto_result):
        return
    mean_ratio = statistics.mean(drifuzz_result) / statistics.mean(agamotto_result)
    print(f"mean ratio {statistics.mean(drifuzz_result)}/{statistics.mean(agamotto_result)}")
    print(f"Coverage increase {round((mean_ratio-1)*100,1)}%")
    pvalue = ss.mannwhitneyu(drifuzz_result, agamotto_result, alternative="two-sided").pvalue
    print(f"significance {statistic_significance(pvalue)} p-value {round(pvalue, 4)}")

past_res = {
    'ar5523': [
        [62, 68, 62],
        [47] * 2,
    ],
    'mwifiex_usb': [
        [110, 110, 110],
        [66] * 2,
    ],
    'rsi_usb': [
        [271, 260, 260],
        [76] * 2,
    ],
}

def compare_usb(target):
    print(target)
    drifuzz_result = usb_result(target)
    agamotto_result = parse_agamotto_usb(target)
    if not len(drifuzz_result) or not len(agamotto_result):
        return
    if target in past_res:
        drifuzz_result += past_res[target][0]
        agamotto_result += past_res[target][1]
    print(f"{drifuzz_result} vs {agamotto_result}")
    mean_ratio = statistics.mean(drifuzz_result) / statistics.mean(agamotto_result)
    print(f"mean ratio {statistics.mean(drifuzz_result)}/{statistics.mean(agamotto_result)}")
    print(f"Coverage increase {round((mean_ratio-1)*100,1)}%")
    pvalue = ss.mannwhitneyu(drifuzz_result, agamotto_result, alternative="two-sided").pvalue
    print(f"significance {statistic_significance(pvalue)} p-value {round(pvalue, 4)}")

if args.agamotto:
    assert agamotto_resultdir.exists()
    drivers = ["ath9k", "ath10k_pci", "rtwpci"]
    drivers += ["8139cp", "atlantic", "stmmac_pci", "snic"]
    for t in drivers:
        compare_agamotto(t)
    sys.exit()

if args.usb:
    assert drifuzz_usb_resultdir.exists()
    assert agamotto_usb_resultdir.exists()
    drivers = ['ar5523', 'mwifiex_usb', 'rsi_usb']
    for t in drivers:
        compare_usb(t)
    sys.exit()

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
	if args.raw:
		tt= coverage_result(args.target, True, True)
		print(tt)
		print(f"mean {statistics.mean(tt)}")
	else:
		stat_one(args.target)

