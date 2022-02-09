#!/bin/bash

targets=(
	'ar5523'
	'mwifiex_usb'
	'rsi_usb'
)

for i in `seq 7`; do
for t in ${targets[@]}; do
	if [ -d /data/$USER/drifuzz-usb/$t-$i ]; then
		continue
	fi
	date
	echo $t $i
	screen -S fuzz -d -m scripts/run_conc_model.sh --usb $t
	sleep 1h
	scripts/kill.sh
	pkill screen
	echo -n "coverage: "
	tail -n 1 work/work-$t-conc-model/evaluation/data.csv |awk -F';' '{print $17}'
	mkdir -p /data/$USER/drifuzz-usb/$t-$i
	mv work/work-$t-conc-model/ /data/$USER/drifuzz-usb/$t-$i
done
done


