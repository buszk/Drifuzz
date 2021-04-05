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

model_data_file = join(drifuzz_path, 'work-' + args.target + '-model', 'evaluation', 'data.csv')
random_data_file = join(drifuzz_path, 'work-' + args.target + '-random', 'evaluation', 'data.csv')
out_file = args.target + '.pdf'
if not exists(model_data_file):
    print(f'File {model_data_file} does not exists')
    sys.exit(0)
if not exists(random_data_file):
    print(f'File {random_data_file} does not exists')
    sys.exit(0)
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
    'byte_covered',
]
df1 = pandas.read_csv(
                    model_data_file,
                    sep=';',
                    names=titles,
                    index_col=False)

df2 = pandas.read_csv(
                    random_data_file,
                    sep=';',
                    names=titles,
                    index_col=False)

# print(df['time'])
# print(df['byte_covered'])
# print(df.loc[17243])
ax = df1.plot('time', 'byte_covered', title=args.target)
ax = df2.plot('time', 'byte_covered', ax=ax)
ax.legend(['generated seed', 'random seed'])
fig = ax.get_figure()
fig.savefig(out_file)

