#!/bin/bash

export ORCHENT_AGENT_ACCOUNT=iam-recas-laniakea-test-jenkins
export ORCHENT_URL="https://paas-orchestrator.cloud.ba.infn.it"

/usr/bin/python --version
echo $PWD
# Run check script.
python ./control-script.py -m laniakea.testuser@gmail.com -c "./health-check.sh" -u "https://paas-orchestrator.cloud.ba.infn.it" -r ./node_with_image.yaml
