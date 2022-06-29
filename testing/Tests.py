import requests

from LogFacility import logger
from Deployments import Deployment
import Utils
from ftplib import FTP
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By


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
    endpoint = endpoint + '/'
    logger.debug(f"Testing {test_name} on {endpoint} with api key {api_key}")
    logger.debug(f"Installing tools for workflow {test_name}")
    bioblend_test.install_tools_from_wf.install_tools(endpoint,api_key,wf_file) 
    logger.debug(f"Running workflow {test_name}")
    bioblend_test.run_workflow.run_galaxy_tools(endpoint,api_key,test_name,wf_file,input_file)


#______________________________________
def ftp_login(host, user, passwd):
    test = FTP(host=host, user=user, passwd=passwd )
    return test

def ftp_upload(test, file_path):
    with open(file_path,'rb') as f:
      fname = os.path.basename(file_path)
      test.storbinary(f'STOR {fname}', f)

def test_ftp(host, file_path, user, password):
    logger.debug(f"Testing FTP on {host} with upload of {file_path}")
    test = ftp_login(host=host, user=user, passwd=password)
    logger.debug(f"FTP connection with {host} established")
    ftp_upload(test=test, file_path=file_path)
    logger.debug(f"File successfully uploaded with FTP")


#______________________________________
def start_firefox_driver(geckodriver_path):
    firefox_options = webdriver.firefox.options.Options()
    firefox_options.headless = True
    driver = webdriver.Firefox(options=firefox_options, executable_path=geckodriver_path)
    return driver

def find_website_element(driver, class_name, name):
    return list(set(driver.find_elements(By.CLASS_NAME, class_name)) & set(driver.find_elements(By.NAME, name)))[0]

def galaxy_login(driver, endpoint, username, password):
    # Connect to endpoint
    driver.get(endpoint)
    logger.debug(f'Connection established with {endpoint}')

    # Get login and password textbox
    time.sleep(5)
    login = find_website_element(driver=driver, class_name='form-control', name='login')
    password = find_website_element(driver=driver, class_name='form-control', name='password')
    # Get login button
    login_button = find_website_element(driver=driver, class_name='btn', name='login')

    # Insert credentials
    login.send_keys(username)
    password.send_keys(password)
    login_button.click()
    logger.debug('Logged into galaxy')

def screenshot_galaxy(geckodriver_path, endpoint, username, password, output_path):
    driver = start_firefox_driver(geckodriver_path)
    galaxy_login(driver, endpoint, username, password)
    time.sleep(5)
    driver.get_screenshot_as_file(output_path)
    driver.close()