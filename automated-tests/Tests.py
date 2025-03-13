"""
This module contains functions that execute tests on deployments. When you want to add a test, add it under the
test section of laniakea_dev_test_mapper.yaml with the variables needed by the test.
The test function must then be added with the same name here, with two arguments: deployment and test_vars.
The var deployment will correspond to the Deployment object instantiated by control-script.py and can be used
to retrieve information on the deployment, such as its endpoint.
The var test_vars will correspond to a dictionary containing the test variables specified in the laniakea_dev_test_mapper.yaml
"""

import requests

from LogFacility import logger
from Deployments import Deployment
import Utils
from ftplib import FTP
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import urlparse
from datetime import datetime

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

def endpoint(deployment, test_vars=None):
    endpoint_status = check_endpoint(deployment.get_uuid())
    if not endpoint_status:
      logger.debug('The deployment is in CREATE_COMPLETE, but it is not reachable. Please check Orchestrator logs.')
      create_status_record = 'CREATE_FAILED'
      logger.debug('The create_status_record is set to ' + create_status_record)

#______________________________________
def galaxy_tools(deployment, test_vars, api_key='not_very_secret_api_key'):
    import bioblend_test.install_tools_from_wf
    import bioblend_test.run_workflow
    wf_file = test_vars['wf_file']
    input_file = test_vars['input_file']
    test_name = wf_file[wf_file.rfind('/')+1:]
    endpoint = deployment.get_endpoint() + '/'
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

def ftp(deployment, test_vars):
    logger.debug(f'Running ftp test...')
    ftp_file_path = test_vars['file_path']
    ftp_user = test_vars['user']
    ftp_password = test_vars['password']
    host = urlparse(deployment.get_endpoint()).netloc
    test_ftp(host=host, file_path=ftp_file_path, user=ftp_user, password=ftp_password)

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
    login_textbox = find_website_element(driver=driver, class_name='form-control', name='login')
    password_textbox = find_website_element(driver=driver, class_name='form-control', name='password')
    # Get login button
    login_button = find_website_element(driver=driver, class_name='btn', name='login')

    # Insert credentials
    login_textbox.send_keys(username)
    password_textbox.send_keys(password)
    login_button.click()
    logger.debug('Logged into galaxy')

def find_unique_path(path):
    filename, extension = os.path.splitext(path)
    counter = 1

    while os.path.exists(path):
        path = filename + str(counter) + extension
        counter += 1

    return path

def screenshot_galaxy(geckodriver_path, endpoint, username, password, output_path):
    driver = start_firefox_driver(geckodriver_path)
    galaxy_login(driver, endpoint, username, password)
    time.sleep(5)
    output_path = find_unique_path(output_path)
    driver.get_screenshot_as_file(output_path)
    driver.close()
    current_date = datetime.now().strftime("%y%m%d_%H%M%S")
    output_path_renamed = 'galaxy_screenshot' + current_date + '.png'
    os.rename(output_path, output_path_renamed)

def screenshot(deployment, test_vars):
    logger.debug(f'Running screenshot test...')
    geckodriver_path = test_vars['geckodriver_path']
    username = test_vars['username']
    password = test_vars['password']
    screenshot_output_path = test_vars['output_path']
    screenshot_galaxy(geckodriver_path, deployment.get_endpoint(), username, password, screenshot_output_path)
