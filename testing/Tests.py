import requests

from LogFacility import logger
from Deployments import Deployment
import Utils


#______________________________________
def check_orchestrator_status(path, url):

    command = '%s -u %s -t 10 -v' % (path, url)

    logger.debug('Check Orchestrator status at: %s' % url)

    stdout, stderr, status = Utils.run_command(command)

    logger.debug(stdout)
    logger.debug(stderr)

    return status


#______________________________________
def check_endpoint(uuid):

    dep = Deployment(dep_uuid=uuid)
    endpoint = dep.get_endpoint()
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
def run_galaxy_tools(endpoint, api_key):
    import bioblend_test.run_workflow 
    logger.debug('Run Galaxy Tools Placeholder')
    logger.debug(endpoint)
    logger.debug(api_key)
    bioblend_test.run_workflow.run_galaxy_tools(endpoint,api_key,"bowtie_test","bioblend-test/workflows/bowtie2_mapping.ga","bioblend-test/inputs/input_files.json")




