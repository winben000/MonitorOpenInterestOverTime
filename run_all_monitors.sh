#!/bin/bash

# Run all token monitors in background
echo "Starting monitors for all tokens..."

python3 monitor.py --config milk.json &
python3 monitor.py --config h.json &
python3 monitor.py --config more.json &
python3 monitor.py --config sahara.json &
python3 monitor.py --config dmc.json &
python3 monitor.py --config mav.json &
python3 monitor.py --config cudis.json &

echo "All monitors started in background"
echo "Use 'jobs' to see running processes"
echo "Use 'kill %1 %2 %3 %4 %5 %6 %7' to stop all monitors" 