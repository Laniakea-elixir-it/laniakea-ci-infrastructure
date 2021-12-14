#/usr/bin/env python

import os, sys
import argparse
import subprocess
import time
import logging
import re
import yaml 
import requests
import json

#logging.basicConfig(filename='/tmp/indigo_paas_checker.log', format='%(levelname)s %(asctime)s %(message)s', level=logging.DEBUG)
# Create logging facility print to stdout and to log file.
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# Create handler for log file and stdout
logger_outfile_handler = logging.FileHandler('/tmp/indigo_paas_checker.log',mode='w')
logger_stdout_handler = logging.StreamHandler(sys.stdout)
# Set formatter for log file and stdout
logger_formatter = logging.Formatter('%(levelname)s %(asctime)s %(message)s')
logger_outfile_handler.setFormatter(logger_formatter)
logger_stdout_handler.setFormatter(logger_formatter)
# Load configuration for log file and stdout
logger.addHandler(logger_outfile_handler)
logger.addHandler(logger_stdout_handler)


#______________________________________
def cli_options():

  parser = argparse.ArgumentParser(description='INDIGO PaaS checker status')

  parser.add_argument('-l', '--test-list', dest='test_list', help='Deployment test list')
  parser.add_argument('-t', '--polling-timeout', dest='polling_time', default=300, help='Polling timeout') #default to 300
  parser.add_argument('-c', '--healh_check_path', dest='health_check_path', help='Orchestrator health check script path')
  # TODO add here the possibility to dispaly log with new paas

  return parser.parse_args()

#________________________________
def load_list(test_list):
    with open(test_list, 'r') as ilf:
        il = yaml.safe_load(ilf)
        return il

#______________________________________
def run_command(cmd):
  """
  Run subprocess call redirecting stdout, stderr and the command exit code.
  """
  proc = subprocess.Popen( args=cmd, shell=True,  stdout=subprocess.PIPE, stderr=subprocess.PIPE )
  communicateRes = proc.communicate()
  stdout, stderr = communicateRes
  status = proc.wait()
  return stdout, stderr, status

#______________________________________
def check_orchestrator_status(path, url):

  command = '%s -u %s -t 10 -v' % (path, url)

  logger.debug('Check Orchestrator status at: %s' % url)

  stdout, stderr, status = run_command(command)

  logger.debug(stdout)
  logger.debug(stderr)

  return status

#______________________________________
def depcreate(tosca, inputs, url):

  command="/usr/bin/orchent depcreate " + tosca + " '" + inputs + "'" + " -u " + url
  logger.debug(command)
  
  stdout, stderr, status = run_command(command)

  temp = stdout.split(b"Deployment",1)[1]

  dep_uuid = temp.splitlines()[0].strip(b" []:")
  logger.debug('[Deployment] Uuid: %s'% dep_uuid)
  
  dep_status = temp.splitlines()[1].strip(b" status: ")
  logger.debug('[Deployment] Uuid: %s, status: %s' % (dep_uuid, dep_status))

  return dep_uuid.decode("utf-8"), dep_status.decode("utf-8")

#______________________________________
def depshow(uuid):

  command="/usr/bin/orchent depshow " + uuid

  stdout, stderr, status = run_command(command)

  return stdout.decode("utf-8"), stderr.decode("utf-8"), status

#______________________________________
def depdel(uuid):

  command="/usr/bin/orchent depdel " + uuid
  logger.debug(command)
  
  stdout, stderr, status = run_command(command)
 
  return stdout.decode("utf-8"), stderr.decode("utf-8"), status

#______________________________________
def get_deployment_details(dep_uuid):
 
  command="/usr/bin/orchent depshow " + dep_uuid

  stdout, stderr, status = run_command(command)

  # check if the deployment has been deleted
  #pattern = "Error 'Not Found' [404]"
  pattern = "doesn't exist"
  match = re.search(pattern, stdout.decode("utf-8"))
  if (match is not None): 
    logger.debug('Deployment with uuid %s already deleted!' % dep_uuid)
    return 'DELETE_COMPLETE'

  temp = stdout.split(b"Deployment",1)[1]

  return temp

#______________________________________
def get_status(uuid):

  deployment = get_deployment_details(uuid)

  if deployment == 'DELETE_COMPLETE':
    return deployment

  dep_status = deployment.splitlines()[1].strip(b" status: ")

  return dep_status.decode("utf-8")

#______________________________________
def get_outputs_json(uuid):

    # Get depployment despshow output
    deployment = get_deployment_details(uuid)

    # Check if deployment is already deleted.
    if deployment == 'DELETE_COMPLETE':
      logger.debug('Deployment already deleted. Returning empty json')
      return {}

    # Decodefrom bytes to string obcject
    decoded_deployment = deployment.decode('utf-8')

    # Remove everything till outputs
    spl_word = 'outputs: '
    res = decoded_deployment.partition(spl_word)[2]

    # Convert string to json
    out_obj = json.loads(res)

    return out_obj

#______________________________________
def get_endpoint(uuid):

    outputs = get_outputs_json(uuid)

    # Check if deployment is already deleted.
    if outputs == {}:
      return 0

    return outputs['endpoint']

#______________________________________
def check_endpoint(uuid):

  endpoint = get_endpoint(uuid)
  if endpoint == "0":
      logger.debug("Deployment already deleted. This should be not happen here! Please check what iss going on")
      return False

  endpoint = endpoint + '/'
  logger.debug('Endpoint check: ' + endpoint)

  try:
    response = requests.get(endpoint, verify=False)
    if response.status_code == 200:
      logger.debug(f"{endpoint}: is reachable")
      return True
    else:
      logger.debug(f"{endpoint}: is Not reachable, status_code: {response.status_code}")
      return False
  #Exception
  except requests.exceptions.RequestException as e:
    # print URL with Errs
    logger.debug(f"{endpoint}: is Not reachable \nErr: {e}")
    return False

#______________________________________
def start():

  logger.debug('======================================')
  logger.debug('Start new check!')
  logger.debug('======================================')

#______________________________________
def end():

  logger.debug('**************************************')
  logger.debug('Check ended!')
  logger.debug('**************************************')

#______________________________________
def run_test_list(test_list, orchestrator_url, polling_time):

  summary_output = {}
  for i in test_list['test']:

    enable_test = test_list['test'][i]['run_test']

    if enable_test:

      name = test_list['test'][i]['name']

      tosca_template_path = test_list['test'][i]['tosca_template_path']
      logger.debug("Downloading tosca template: " + tosca_template_path)

      # Download template
      r = requests.get(test_list['test'][i]['tosca_template'], allow_redirects=True)
      with open(tosca_template_path, 'wb') as tosca_template:
        tosca_template.write(r.content)

      # Get inputs json
      inputs = test_list['test'][i]['inputs']
      if inputs == None:
        inputs = '{}'
      else:
        inputs = json.dumps(inputs)

      # Enable endpoint check
      # This could be further improved with new check.
      enable_endpoint_check = test_list['test'][i]['check_endopint']

      # Run test
      logger.debug('Testing ' + name)
      test_exit_status = run_test(tosca_template_path, orchestrator_url, inputs, polling_time, enable_endpoint_check)
      if test_exit_status:
        summary_output[name] = "SUCCESS"
      elif not test_exit_status:
        summary_output[name] = "ERROR"

  logger.debug("Output summary")
  logger.debug(summary_output)
  return summary_output

#______________________________________
def run_test(tosca_template, orchestrator_url, inputs, polling_time, enable_endpoint_check=False):
  # Start PaaS test deployment
  dep_uuid, dep_status = depcreate(tosca_template, inputs, orchestrator_url)

  # Update deployment status
  time.sleep(polling_time)
  dep_status = get_status(dep_uuid)

  count = 0
  while(dep_status == 'CREATE_IN_PROGRESS'):
    time.sleep(polling_time)
    dep_status = get_status(dep_uuid)
    count = count + 1
    logger.debug('[Deployment] Update n. %s, uuid: %s, status: %s.' % (count, dep_uuid, dep_status))
  logger.debug('Deployment uuid %s finished with status: %s' % (dep_uuid, dep_status))

  # Record Create status. If CREATE_FAILED the job will file at the end.
  create_status_record = dep_status

  # wait some secs.
  #time.sleep(10)

  # Print output
  create_out, create_err, create_status = depshow(dep_uuid)
  logger.debug('Deployment details - stdout: ' + create_out)
  logger.debug('Deployment details - stderr: ' + create_err)

  ## Check if endpoint is available.
  if create_status_record == "CREATE_COMPLETE" and enable_endpoint_check:
    endpoint_status = check_endpoint(dep_uuid)
    if not endpoint_status:
      logger.debug('The deployment is in CREATE_COMPLETE, but it is not reachable. Please check Orchestrator logs.')
      create_status_record = 'CREATE_FAILED'
      logger.debug('The create_status_record is set to ' + create_status_record)

  ## Always delete deployment
  delete_out, delete_err, delete_status = depdel(dep_uuid)
  dep_status = get_status(dep_uuid)
  logger.debug('Deployment delete - stdout: ' + delete_out)
  logger.debug('Deployment delete - stderr: ' + delete_err)
  logger.debug('Deployment delete - status: ' + dep_status)

  ## Ensure deletion
  ## This should get rid also of concurrency.
  del_count = 1 # delete already triggered 1 time
  pattern='successfully triggered'
  match = re.search(pattern, str(delete_out))
  while(match is None):
    logger.debug('Deployment uuid %s delete failed. Wait for 2 minutes and retry.' % dep_uuid)
    time.sleep(120)
    del_count = del_count + 1
    logger.debug('Delete uuid %s retry n. %s.' % (dep_uuid, del_count))
    delete_out, delete_err, delete_status = depdel(dep_uuid)
    match = re.search(pattern, str(delete_out))
  logger.debug('Deployment uuid %s delete: %s' % (dep_uuid, delete_out))

  # reset counter
  count = 0
  while(dep_status == 'DELETE_IN_PROGRESS'):
    time.sleep(60)
    dep_status = get_status(dep_uuid)
    logger.debug(dep_status)
    count = count + 1
    logger.debug('[Deletion] Update n. %s, uuid %s, status: %s.' % (count, dep_uuid, dep_status))
  logger.debug('Delete finished.')

  # Record Delete status. If DELETE_FAILED the job will file at the end.
  logger.debug(dep_status)
  delete_status_record = dep_status

  # Notify delete failed.
  if(create_status_record == 'CREATE_FAILED'):
    logger.debug('Deployment ' + dep_uuid + ' creation failed.')
    current_status = get_status(dep_uuid)
    logger.debug('Current status ' + current_status)
    return False
  if(delete_status_record == 'DELETE_FAILED'):
    logger.debug('Deployment ' + dep_uuid + ' delete failed.')
    current_status = get_status(dep_uuid)
    logger.debug('Current status ' + current_status)
    return False
  else:
    logger.debug('Deployment correctly performed. Check logs for further details.')
    return True

#______________________________________
def indigo_paas_checker():

  start()

  options = cli_options()

  # Load test list
  test_list = load_list(options.test_list)

  # Check orchestrator status.
  orchestrator_url = test_list['orchestrator_url']
  orchestrator_status = check_orchestrator_status(options.health_check_path, orchestrator_url)
  if(orchestrator_status is not 0):
    logger.debug('Unable to contact the orchestrator at %s.' % options.orchestrator_url)
    end()
    sys.exit(1)

  # Run PaaS orchestrator tests
  summary_json = run_test_list(test_list, orchestrator_url, float(options.polling_time))

  errors = "ERROR" in summary_json.values()
  if errors:
    sys.exit(1)

  end()

#______________________________________
if __name__ == '__main__':
  indigo_paas_checker()
