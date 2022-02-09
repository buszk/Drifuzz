#!/bin/bash

targets=(
    'ath9k'
    'ath10k_pci'
     'rtwpci'
     '8139cp'
     'atlantic'
     'stmmac_pci'
     'snic'
)

N=100
echo N = $N

for t in ${targets[@]}; do
    date
	echo $t
    scripts/reproduce.sh --n $N $t ../drifuzz-model-result/$t/ ../drifuzz-model-result/$t/out/0 2>&1|grep "bitmap cover\|trace hash" > $t.cover
    cat $t.cover |sort | uniq -c
	echo

    scripts/reproduce_naive.sh --flat --n 0 $t ../drifuzz-model-result/$t/ ../drifuzz-model-result/$t/out/0 2>&1|grep "bitmap cover"
    echo

    scripts/reproduce_naive.sh --n $N $t ../drifuzz-model-result/$t/ ../drifuzz-model-result/$t/out/0 2>&1|grep "bitmap cover\|trace hash" > $t.naive.cover
    cat $t.naive.cover |sort |uniq -c
done
