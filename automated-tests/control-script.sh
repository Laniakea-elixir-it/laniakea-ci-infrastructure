#!/bin/bash
#
# Usage: ./control-script.sh "prod" for Laniakea prod paas
# Usage: ./control-script.sh "dev" for Laniakea dev paas

if [[ $1 == "prod" ]]; then

  # Laniakea prod
  export ORCHENT_AGENT_ACCOUNT=iam-recas-laniakea-test-jenkins
  export ORCHENT_URL="https://paas-orchestrator.cloud.ba.infn.it"
  export TEST_LIST=./testing/laniakea_at_recas_prod.yaml

  echo "Loading production config"

elif [[ $1 == "dev" ]]; then

  # Lanaieka dev
  export ORCHENT_AGENT_ACCOUNT=iam-recas-laniakea-bot
  export ORCHENT_URL="https://laniakea-dashboard.cloud.ba.infn.it/orchestrator/"
  export TEST_LIST=./automated-tests/laniakea_recas_prod.yaml

  echo "Loading development config"

else

  echo "No configuration available" && exit 1

fi

echo $ORCHENT_AGENT_ACCOUNT
echo $ORCHENT_URL
echo $TEST_LIST

/usr/bin/python --version

# Run check script.
python $PWD/testing/control-script.py -c "$PWD/automated-tests/health-check.sh" -l $TEST_LIST
