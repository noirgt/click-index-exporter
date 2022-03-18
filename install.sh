#!/bin/bash
SCRIPT_PATH=$(dirname "$0")
CREDENTIALS=$SCRIPT_PATH/.credentials

docker build -t click-index-exporter:latest .

if test -f "$CREDENTIALS"; then
    docker run -d --name click-index-exporter \
        -v $(pwd)/config.yml:/click-index-exporter/config.yml \
        -v $(pwd)/.credentials:/click-index-exporter/\.credentials \
        -p 9091:9091 click-index-exporter
else
    echo "File '.credentials' does not exists."
fi
