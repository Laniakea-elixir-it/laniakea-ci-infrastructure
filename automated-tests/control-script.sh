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
  export ORCHENT_AGENT_ACCOUNT=iam-recas-test_laniakea-dev_matangaro_jenkins-test
  #export ORCHENT_URL="https://cloud-90-147-75-119.cloud.ba.infn.it/orchestrator"
  export ORCHENT_URL="https://cloud-90-147-102-77.cloud.ba.infn.it"
  export TEST_LIST=./testing/laniakea_dev.yaml

  echo "Loading development config"

else

  echo "No configuration available" && exit 1

fi

echo $ORCHENT_AGENT_ACCOUNT
echo $ORCHENT_URL
echo $TEST_LIST

/usr/bin/python --version

# Run check script.
python $PWD/testing/control-script.py -c "$PWD/testing/health-check.sh" -l $TEST_LIST
