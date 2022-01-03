#!/bin/bash

targets=(
	'ar5523'
	'mwifiex_usb'
	'rsi_usb'
)
for t in ${targets[@]}; do
	echo $t
	screen -S fuzz -d -m scripts/run_conc_model.sh --usb $t
	sleep 1h
	scripts/kill.sh
	pkill screen
done

for t in ${targets[@]}; do
	echo $t
	tail -n 1 work/work-$t-conc-model/evaluation/data.csv
done

