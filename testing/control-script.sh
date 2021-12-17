#!/bin/bash
#
# Usage: ./control-script.sh test-list.yml

export ORCHENT_AGENT_ACCOUNT=iam-recas-laniakea-test-jenkins
export ORCHENT_URL="https://paas-orchestrator.cloud.ba.infn.it"

/usr/bin/python --version

# Run check script.
python $PWD/testing/control-script.py -c "$PWD/testing/health-check.sh" -l $1
