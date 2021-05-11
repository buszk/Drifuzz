#!/usr/bin/env python3
import os
import sys
import argparse
import pathlib
import pandas
from os.path import join, exists, abspath, dirname

parser = argparse.ArgumentParser()
parser.add_argument('target', type=str)
args = parser.parse_args()

drifuzz_path = dirname(dirname(abspath(__file__)))

model_data_file = join(drifuzz_path, 'work', 'work-' + args.target + '-model', 'evaluation', 'data.csv')
random_data_file = join(drifuzz_path, 'work', 'work-' + args.target + '-random', 'evaluation', 'data.csv')
random_concolic_data_file = join(drifuzz_path, 'work', 'work-' + args.target + '-conc', 'evaluation', 'data.csv')
model_concolic_data_file = join(drifuzz_path, 'work', 'work-' + args.target + '-conc-model', 'evaluation', 'data.csv')

out_file = args.target + '.pdf'
dfs = []
lgs = []
titles = [
    'time',
    'performance',
    'hashes',
    'path_pending',
    'favorites',
    'panics',
    'panics_unique',
    'kasan',
    'kasan_unique',
    'reloads',
    'reloads_unique',
    'level',
    'cycles',
    'fav_pending',
    'blacklisted',
    'total',
    'byte_covered',
]

data_files = [
    random_data_file,
    random_concolic_data_file,
    model_data_file,
    model_concolic_data_file,
]

settings = [
    'random seed',
    'random seed +concolic',
    'generated seed',
    'generated seed +concolic',
]

for i in range(4):
    if exists(data_files[i]):
        df = pandas.read_csv(
                        data_files[i],
                        sep=';',
                        names=titles,
                        index_col=False)
        df['time'] /= 60
        dfs.append(df)
        lgs.append(settings[i])

if len(dfs) == 0:
    sys.exit(0)
ax = dfs[0].plot('time', 'byte_covered', title=args.target)
for df in dfs[1:]:
    ax = df.plot('time', 'byte_covered', title=args.target, ax=ax)

ax.legend(lgs)
fig = ax.get_figure()
fig.savefig(out_file)

