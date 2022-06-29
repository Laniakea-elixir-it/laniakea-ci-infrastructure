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

from LogFacility import logger
logger.info('Start Test')

from Deployments import Deployment
import Utils
import Tests

#______________________________________
def cli_options():

  parser = argparse.ArgumentParser(description='INDIGO PaaS checker status')

  parser.add_argument('-l', '--test-list', dest='test_list', help='Deployment test list')
  parser.add_argument('-t', '--polling-timeout', dest='polling_time', default=300, help='Polling timeout') #default to 300
  parser.add_argument('-c', '--healh_check_path', dest='health_check_path', help='Orchestrator health check script path')
  #parser.add_argument('-g', '--user-group', dest='user_group', help='Specify user group on IAM.')
  # TODO add here the possibility to dispaly log with new paas

  return parser.parse_args()

#______________________________________
def load_list(test_list):
    with open(test_list, 'r') as ilf:
        il = yaml.safe_load(ilf)
        return il

#______________________________________
def load_test_mapper(test_mapper):
  with open(test_mapper, 'r') as tmf:
    tm = yaml.safe_load(tmf)
    return tm

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

    enable_test = test_list['test'][i]['enabled']

    if enable_test:

      name = test_list['test'][i]['name']

      tosca_template_path = test_list['test'][i]['tosca_template_path']
      logger.debug("Downloading tosca template: " + tosca_template_path)

      # Download template
      r = requests.get(test_list['test'][i]['tosca_template'], allow_redirects=True)
      with open(tosca_template_path, 'wb') as tosca_template:
        tosca_template.write(r.content)

      # Get test user
      user = test_list['test_user']

      # Get inputs json
      inputs = test_list['test'][i]['inputs']
      if inputs == None:
        inputs = '{}'
      else:
        # add the ssh user to inputs
        if 'users' in inputs:
          inputs['users'].append(user)

        inputs = json.dumps(inputs)

      # Enable endpoint tests.
      run_more = test_list['test'][i]['run_more']
      logger.debug('Additional tests: ' + str(run_more))

      # Run test
      logger.debug('Testing ' + name)
      test_exit_status = run_test(tosca_template_path, orchestrator_url, inputs, polling_time, run_more)
      if test_exit_status:
        summary_output[name] = "SUCCESS"
      elif not test_exit_status:
        summary_output[name] = "ERROR"

  logger.debug("Output summary")
  logger.debug(summary_output)
  return summary_output

#______________________________________
def run_test(tosca_template, orchestrator_url, inputs, polling_time, additional_tests=False):
  # Start PaaS test deployment
  dep = Deployment(tosca_template, inputs, orchestrator_url, None)
  
  try:
    dep_uuid = dep.get_uuid()
    dep_status = dep.get_status()

    # Update deployment status
    time.sleep(polling_time)
    dep_status = dep.get_status()

    count = 0
    while(dep_status == 'CREATE_IN_PROGRESS'):
      time.sleep(polling_time)
      dep_status = dep.get_status()
      count = count + 1
      logger.debug('[Deployment] Update n. %s, uuid: %s, status: %s.' % (count, dep_uuid, dep_status))
    logger.debug('Deployment uuid %s finished with status: %s' % (dep_uuid, dep_status))

    # Record Create status. If CREATE_FAILED the job will file at the end.
    create_status_record = dep_status

    # wait some secs.
    #time.sleep(10)

    # Print output
    create_out, create_err, create_status = dep.depshow()
    logger.debug('Deployment details - stdout: ' + create_out)
    logger.debug('Deployment details - stderr: ' + create_err)

    # Get tests mapper, mapping tests to input files
    test_mapper = load_test_mapper('./testing/laniakea_dev_test_mapper.yaml')


    #####################################################################################
    ## Run tests.
    ## Implement all tests here.
    #####################################################################################

    if create_status_record == "CREATE_COMPLETE" and type(additional_tests) is list:
    
      for test in additional_tests:
        if test=='endpoint':
          endpoint_status = Tests.check_endpoint(dep.get_uuid())
          if not endpoint_status:
            logger.debug('The deployment is in CREATE_COMPLETE, but it is not reachable. Please check Orchestrator logs.')
            create_status_record = 'CREATE_FAILED'
            logger.debug('The create_status_record is set to ' + create_status_record)
        
        elif test=='ftp':
          logger.debug(f'Running {test} test...')
          ftp_file_path = test_mapper['test'][test]['file_path']
          ftp_user = test_mapper['test'][test]['user']
          ftp_password = test_mapper['test'][test]['password']
          host = dep.get_endpoint().rstrip('/').rstrip('/galaxy').lstrip('http://')
          Tests.test_ftp(host=host, file_path=ftp_file_path, user=ftp_user, password=ftp_password)

        elif test in test_mapper['test'].keys():
          logger.debug(f'Running {test} test...')
          Tests.run_galaxy_tools(dep.get_endpoint(),api_key='not_very_secret_api_key',wf_file=test_mapper['test'][test]['wf_file'],input_file=test_mapper['test'][test]['input_file'])

        else:
          logger.debug(f'Test {test} is missing in laniakea_dev_test_mapper.yaml')


    #####################################################################################
    ## End tests.
    #####################################################################################

    ## Take screenshot of galaxy instance
    Tests.screenshot_galaxy(geckodriver_path='./geckodriver', endpoint=dep.get_endpoint(), username='admin@admin.com', password='galaxy_admin_password', output_path='/tmp/galaxy_screenshot.png')

  finally:
    ## Always delete deployment
    delete_out, delete_err, delete_status = dep.depdel()
    dep_status = dep.get_status()
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
      delete_out, delete_err, delete_status = dep.depdel()
      match = re.search(pattern, str(delete_out))
    logger.debug('Deployment uuid %s delete: %s' % (dep_uuid, delete_out))

    # reset counter
    count = 0
    while(dep_status == 'DELETE_IN_PROGRESS'):
      time.sleep(60)
      dep_status = dep.get_status()
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
      current_status = dep.get_status()
      logger.debug('Current status ' + current_status)
      return False
    if(delete_status_record == 'DELETE_FAILED'):
      logger.debug('Deployment ' + dep_uuid + ' delete failed.')
      current_status = dep.get_status()
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
  orchestrator_status = Tests.check_orchestrator_status(options.health_check_path, orchestrator_url)
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
