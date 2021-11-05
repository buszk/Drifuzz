#!/usr/bin/env python3
import sys

s = 0.0
for line in sys.stdin:
    s += float(line)

print(f"total {s}")

