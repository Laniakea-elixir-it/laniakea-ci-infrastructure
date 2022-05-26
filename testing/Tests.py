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
def run_galaxy_tools(endpoint, api_key, wf_file, input_file):
    import bioblend_test.install_tools_from_wf
    import bioblend_test.run_workflow
    test_name = wf_file[wf_file.rfind('/')+1:] 
    logger.debug(f"BASIC TEST RUNNING  {test_name}")
    logger.debug(endpoint)
    logger.debug(api_key)
    logger.debug('INSTALL WF TOOLS')
    endpoint = endpoint + '/'
    bioblend_test.install_tools_from_wf.install_tools(endpoint,api_key,wf_file) 
    logger.debug('RUN TOOLS')
    bioblend_test.run_workflow.run_galaxy_tools(endpoint,api_key,test_name,wf_file,input_file)




