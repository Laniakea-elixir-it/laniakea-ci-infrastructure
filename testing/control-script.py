#/usr/bin/env python

import os, sys
import argparse
import subprocess
import time
import logging
import re

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

  parser.add_argument('-m', '--mail-address', dest='mail_address', help='Mail to send output')
  parser.add_argument('-t', '--polling-timeout', dest='polling_time', default=30, help='Polling timeout') #default to 300
  parser.add_argument('-r', '--tosca-template', dest='tosca_template', help='TOSCA tempalte to be used')
  parser.add_argument('-c', '--healh_check_path', dest='health_check_path', help='Orchestrator health check script path')
  parser.add_argument('-u', '--orchestrator-url', dest='orchestrator_url', help='Orchestrator URL')

  return parser.parse_args()

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
def depcreate(tosca, url):

  command="/usr/bin/orchent depcreate " + tosca + " '{}' -u " + url
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
  
  stdout, stderr, status = run_command(command)
 
  return stdout.decode("utf-8"), stderr.decode("utf-8"), status

#______________________________________
def get_status(dep_uuid):
 
# qui c'è un problema. anche se il deploy non viene cancellato viene mostrato come "already" deleted.

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

  dep_status = temp.splitlines()[1].strip(b" status: ")

  return dep_status.decode("utf-8")

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
def indigo_paas_checker():

  start()

  options = cli_options()

  #depls='/usr/bin/orchent depls -c me'
  #depls_out, depls_err, depls_status = run_command(depls)
  #print depls_out

  # Check orchestrator status.
  orchestrator_status = check_orchestrator_status(options.health_check_path, options.orchestrator_url)
  if(orchestrator_status is not 0):
    logger.debug('Unable to contact the orchestrator at %s.' % options.orchestrator_url)
    end()
    sys.exit(1)

  # Start PaaS test deployment
  dep_uuid, dep_status = depcreate(options.tosca_template, options.orchestrator_url)
 
  # Update deployment status
  time.sleep(float(options.polling_time))
  dep_status = get_status(dep_uuid)

  count = 0
  while(dep_status == 'CREATE_IN_PROGRESS'):
    time.sleep(float(options.polling_time))
    dep_status = get_status(dep_uuid)
    count = count + 1
    logger.debug('[Deployment] Update n. %s, uuid: %s, status: %s.' % (count, dep_uuid, dep_status))
  logger.debug('Deployment uuid %s finished with status: %s' % (dep_uuid, dep_status))

  # wait some secs.
  #time.sleep(10)

  # Print output if failed
  if(dep_status == 'CREATE_FAILED'):
    final_out, final_err, final_status = depshow(dep_uuid)
    logger.debug('Deployments details - stdout: ' + final_out)
    logger.debug('Deployments details - stderr: ' + final_err)

  ## Always delete deployment
  final_out, final_err, final_status = depdel(dep_uuid)  

  ## Ensure deletion
  ## This should get rid also of concurrency.
  del_count = 1 # delete already triggered 1 time
  pattern='successfully triggered'
  match = re.search(pattern, str(final_out))
  while(match is None): 
    logger.debug('Deployment uuid %s delete failed. Wait for 2 minutes and retry.' % dep_uuid)
    time.sleep(120)
    del_count = del_count + 1
    logger.debug('Delete uuid %s retry n. %s.' % (dep_uuid, del_count))
    final_out, final_err, final_status = depdel(dep_uuid)
    match = re.search(pattern, final_out)
  logger.debug('Deployment uuid %s delete: %s' % (dep_uuid, final_out))

  ## Notify delete failed.
  ## Check deployment status during delete in progress
  #dep_status = get_status(dep_uuid)
  #logger.debug('[Deletion] Deployment uuid %s status: %s' % (dep_uuid, dep_status))

  # reset counter
  count = 0
  while(dep_status == 'DELETE_IN_PROGRESS'):
    time.sleep(60)
    dep_status = get_status(dep_uuid)
    count = count + 1
    logger.debug('[Deletion] Update n. %s, uuid %s, status: %s.' % (count, dep_uuid, dep_status))
  logger.debug('Delete finished.')

  ## Send report if create failed
  ## Update deployment status
  #dep_status = get_status(dep_uuid)
  #if(dep_status == 'DELETE_FAILED'):
  #  final_out, final_err, final_status = depshow(dep_uuid)
  #  sendmail = 'echo "Deployment delete failed uuid: %s \n  %s" | /usr/bin/mail -s "[INDIGO PaaS] check at: $(date)" %s' % (dep_uuid, final_out, options.mail_address)
  #  run_command(sendmail)
  #  logger.debug('Report sent to: %s' % options.mail_address)

  end()

#______________________________________
if __name__ == '__main__':
  indigo_paas_checker()
