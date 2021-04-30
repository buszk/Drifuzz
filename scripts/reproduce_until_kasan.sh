if [ $# -lt 3 ]; then
    echo "$0 <target> <work> <input>"
    exit 1
fi
target=$1
work=$2
input=$3
i=0
while [[ $i -lt 1000 ]]; do
    ((i++))
    python3 -u fuzzer/reproduce.py seed/seed-random  $work $target --reproduce $input  2>&1 |tee reproduce.log
    if grep handle_kasan reproduce.log; then
        echo "Found! After $i tries"
        break
    fi
done
