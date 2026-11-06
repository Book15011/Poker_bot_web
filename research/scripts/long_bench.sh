#!/bin/bash
# Benchmarks for the longer deep-stack training (deep_long.sh): new blueprints against the first ones.
# Waits for training to finish, then runs every job at low priority, PAR at a time, one JSON file per job.
#
#   new vs old, real game, blueprint only:   bp_compare.js blueprint at 50, 100 and 200bb
#   new vs old, real game, the site's Expert: bp_compare.js expert at 100bb (80 turn / 400 river iterations)
#   Local Best Response, old and new with the same seeds and 10x the hands of the first run
#
# Usage: long_bench.sh [parallel]
set -u
PAR=${1:-8}
R=/home/ubuntu/test/poker-ai
OLD=$R/exports; NEW=$R/exports/long; DATA=$R/data_deep; OUT=$R/results/long_bench
cd "$R"
until grep -q "ALL DONE" logs/deep_long.log; do sleep 120; done
mkdir -p "$OUT"
source ~/.nvm/nvm.sh > /dev/null
cd repo/research/bench
{
  for d in 50 100 200; do echo "bp_d$d node bp_compare.js $NEW $OLD $DATA blueprint $d 100000 $d"; done
  for s in 1 2 3 4; do echo "expert_d100_s$s node bp_compare.js $NEW $OLD $DATA expert 100 150 $((10 + s)) 80 400"; done
  for v in new old; do
    dir=$NEW; [ $v = old ] && dir=$OLD
    echo "lbr_${v}_d100_f2 node lbr.js blueprint $dir $DATA 100 100 200000 0 0 16 2"
    echo "lbr_${v}_d100_f0 node lbr.js blueprint $dir $DATA 100 100 200000 0 0 15 0"
    echo "lbr_${v}_d200_f2 node lbr.js blueprint $dir $DATA 200 200 200000 0 0 19 2"
  done
} > "$OUT/jobs.txt"
export OUT
xargs -P "$PAR" -L 1 bash -c 'name=$0; nice -n 10 "$@" > "$OUT/$name.json" 2> "$OUT/$name.err"' < "$OUT/jobs.txt"
echo "$(date -u +%FT%TZ) long bench finished" >> "$R/logs/deep_long.log"
