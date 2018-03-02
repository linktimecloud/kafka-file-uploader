#!/bin/bash

set -e

target=$HOME/kafka_file_uploader.zip

git archive -o $target HEAD
echo "Zip file generated successfully at ${target}."
