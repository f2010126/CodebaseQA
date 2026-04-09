#!/usr/bin/env bash
# initialize conda in this shell
source "$(conda info --base)/etc/profile.d/conda.sh"

conda activate agent_env

python -m main