#!/bin/bash

export ORCHENT_AGENT_ACCOUNT=iam-recas-laniakea-test-jenkins
export ORCHENT_URL="https://paas-orchestrator.cloud.ba.infn.it"

/usr/bin/python --version

# Run check script.
echo "$PWD"
python $PWD/testing/control-script.py -m laniakea.testuser@gmail.com -c "$PWD/testing/health-check.sh" -u "https://paas-orchestrator.cloud.ba.infn.it" -r $PWD/testing/node_with_image.yaml
