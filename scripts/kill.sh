#!/bin/bash
# pkill -9 bash || true
ps aux|grep python|grep drifuzz |awk '{print $2}'|xargs -I '{}' kill -9 '{}' || true
pkill -9 gdb || true
pkill -9 panda || true
