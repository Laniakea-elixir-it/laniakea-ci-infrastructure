#!/usr/bin/env python

import time
import yaml
import jinja2
from jinja2 import Environment, FileSystemLoader
import tempfile
import subprocess
import logging
import requests
import sys

# Load Jinja2 templates
template_dir = './templates'
env = Environment( loader=FileSystemLoader(template_dir) )

# Packer executable
packer_exe='/usr/bin/packer'

# Create logging facility print to stdout and to log file.
report_file="./report/build_report_"+ str(time.strftime("%Y%m%d-%H%M%S"))+'.log'
build_init_datetime=str(time.strftime("Date: %Y-%m-%d - Time: %H:%M:%S"))

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# Create handler for log file and stdout
logger_outfile_handler = logging.FileHandler('./report/test.log',mode='w')
logger_stdout_handler = logging.StreamHandler(sys.stdout)
# Set formatter for log file and stdout
logger_formatter = logging.Formatter('%(levelname)s %(asctime)s %(message)s')
logger_outfile_handler.setFormatter(logger_formatter)
logger_stdout_handler.setFormatter(logger_formatter)
# Load configuration for log file and stdout
logger.addHandler(logger_outfile_handler)
logger.addHandler(logger_stdout_handler)

#________________________________
def create_report(report):
    """
    Start build report for github upload.
    Write header file
    """
    with open(report, 'w') as logfile:
        logger.debug('*** Laniakea Image build Report ***\n')
        logger.debug(build_init_datetime+"\n")
        logger.debug('Report file: ' + str(report) + '\n')
        logger.debug('\n')

#________________________________
def run_command(cmd):
    """
    Run subprocess call redirecting stdout, stderr and the command exit code.
    """
    proc = subprocess.Popen( args=cmd, shell=True,  stdout=subprocess.PIPE, stderr=subprocess.PIPE )
    communicateRes = proc.communicate()
    stdout, stderr = communicateRes
    status = proc.wait()
    return stdout, stderr, status

#________________________________
def upload_report_to_github(report):
    logger.debug(report)
    add_cmd = 'git add '+report
    add_stdout, add_stderr, add_status = run_command(add_cmd)
    logger.debug('[Git add] ' + str(add_stdout))
    logger.debug('[Git add] ' + str(add_stderr))

    if add_status == 0:
        commit_cmd = 'git commit -m "Add automated report - ' + build_init_datetime +'"'
        logger.debug(commit_cmd)
        commit_stdout, commit_stderr, commit_status = run_command(commit_cmd)
        logger.debug('[Git commit] ' + str(commit_stdout))
        logger.debug('[Git commit] ' + str(commit_stderr))

        if commit_status == 0:
            push_cmd = 'git push origin HEAD:master'
            push_stdout, push_stderr, push_status = run_command(push_cmd)
            logger.debug('[Git push] ' + str(push_stdout))
            logger.debug('[Git push] ' + str(push_stderr))

#________________________________
def load_list():
    with open('images_list.yaml', 'r') as ilf:
        il = yaml.safe_load(ilf)
        return il

#________________________________
def parse_list(info_list, outpath):
    """
    Create Packer json files, from jinja2 templates
    This returns images list to be built
    """

    images_db_url = info_list['images_db_url']

    r = requests.get(images_db_url)
    current_images_list = r.json()
    for k in range(len(current_images_list['rows'])):
        current_image_name = current_images_list['rows'][k]['doc']['data']['image_name']
        if 'version' not in current_images_list['rows'][k]['doc']['data']:
            logger.debug('There is no version to compare with.')
        else:
            current_image_version = current_images_list['rows'][k]['doc']['data']['version']

    images_to_build = []
    for i in info_list['images']:

        image = info_list['images'][i]
        name = image['name']
        version = image['version']
        build = image['build']

        logger.debug("Building image: "+str(name)+" Version: "+str(version))
        # Grant an image with the same name and version does not exist
        for k in range(len(current_images_list['rows'])):
            if name == current_images_list['rows'][k]['doc']['data']['image_name'] and version == current_images_list['rows'][k]['doc']['data']['version']:
                logger.debug("The image: " +str(name)+" Version: "+str(version)+ " is already available on CMDB. Skipping.")
                build = False

        if not build:
            continue

        else:

            # Load template
            template = env.get_template('packer.json.j2')

            # Check if ansible galaxy file is there
            ansible_galaxy_file = None
            if 'ansible_galaxy_file' in image['packer']:
              ansible_galaxy_file = image['packer']['ansible_galaxy_file']

            # Render template
            rendered_template = template.render(
                                                name = name,
                                                version = version,
                                                ssh_username = image['packer']['ssh_username'],
                                                source_image = image['packer']['source_image'],
                                                flavor = image['packer']['flavor'],
                                                volume_size = image['packer']['volume_size'],
                                                network_id = image['packer']['network_id'],
                                                ansible_galaxy_file = ansible_galaxy_file,
                                                playbook_file = image['packer']['playbook_file']
                                               )

            # Write packer json to file
            fout_name = outpath+'/'+name+'.json'
            with open(fout_name, "w") as fout:
                fout.write(rendered_template)

            images_to_build.append(fout_name)

            logger.debug('[Image to Build] '+name)
            logger.debug('[Packer template] '+rendered_template)

    return images_to_build

#________________________________
def build_images_with_packer(path_list):

    for template_path in path_list:
        logger.debug('Start Build')
        build_image(template_path)

#________________________________
def build_image(path):
    """
    Run subprocess call redirecting stdout, stderr and the command exit code.
    """
    cmd = packer_exe + ' build ' + path + '-debug'
    logger.debug(cmd)

    proc = subprocess.Popen( args=cmd, shell=True,  stdout=subprocess.PIPE, stderr=subprocess.STDOUT )

    while proc.poll() is None:
        line = proc.stdout.readline()
        sl = line.strip()
        dsl = sl.decode('utf-8')
        logger.debug('[Packer] '+dsl)

    status = proc.wait()

    return status

#________________________________
def build_images():

    create_report(report_file)

    images_info = load_list()

    # Create a temporary directory
    tempdir = tempfile.mkdtemp(dir='./')
    logger.debug('The created temporary directory is %s' % tempdir) # move to log

    # Create packer json
    images_to_build = parse_list(images_info, tempdir)
    logger.debug(images_to_build)

    # Build Packer images
    build_images_with_packer(images_to_build)

    # Upload report to github
    #upload_report_to_github(report_file)

#______________________________________
if __name__ == "__main__":
   build_images()
