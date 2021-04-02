#!/bin/bash

modprobe $1
sleep 1
cat /proc/modules
