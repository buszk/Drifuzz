#!/bin/bash

num_trial=10
targets=(
    "ath9k"
    "ath10k_pci"
    "rtwpci"
#    "8139cp"
#    "atlantic"
#    "snic"
#    "stmmac_pci"
)
data_dir=/data/$USER/drifuzz

concolic=1
model=1


for iteration in $(seq $num_trial); do
    for target in ${targets[*]}; do
        resdir=result-${target}-${concolic}-${model}-${iteration}
        if [ -d $data_dir/$resdir ]; then
            continue
        fi
        if [ $concolic -eq 1 ]; then
            echo "Creating snapshot: iter $iteration"
            (cd ../drifuzz-concolic && ./snapshot_helper.py $target &> ~/snapshot_creation.log)
        fi

        echo "Running $target with iteration $iteration"
        echo "concolic: $concolic,  model: $model"

        # Run fuzzing in a deteached screen
        if [ $model -eq 1 ] && [ $concolic -eq 1 ]; then
            screen -S fuzz -d -m scripts/run_conc_model.sh $target
        elif [ $model -eq 1 ] && [ $concolic -eq 0 ]; then
            screen -S fuzz -d -m scripts/run_model.sh  $target
        elif [ $model -eq 0 ] && [ $concolic -eq 1 ]; then
            screen -S fuzz -d -m scripts/run_conc_rand.sh $target
        elif [ $model -eq 0 ] && [ $concolic -eq 0 ]; then
            screen -S fuzz -d -m scripts/run_random.sh $target
        fi

        # Wait for result to be collected
        sleep 1h
        # Teminate
        scripts/kill.sh
        pkill screen

        if [ $model -eq 1 ] && [ $concolic -eq 1 ]; then
            work=work/work-$target-conc-model
        elif [ $model -eq 1 ] && [ $concolic -eq 0 ]; then
            work=work/work-$target-model
        elif [ $model -eq 0 ] && [ $concolic -eq 1 ]; then
            work=work/work-$target-conc
        elif [ $model -eq 0 ] && [ $concolic -eq 0 ]; then
            work=work/work-$target-random
        fi

        mv work $data_dir/$resdir
    done

done
