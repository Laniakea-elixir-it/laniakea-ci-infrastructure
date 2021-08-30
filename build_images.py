#!/usr/bin/env python

import time
import yaml
import jinja2
from jinja2 import Environment, FileSystemLoader
import tempfile
import subprocess
import logging

# Load Jinja2 templates
template_dir = './templates'
env = Environment( loader=FileSystemLoader(template_dir) )

# Packer executable
packer_exe='/usr/bin/packer'

# Create Log facility
report_file="./report/build_report_"+ str(time.strftime("%Y%m%d-%H%M%S"))+'.log'
build_init_datetime=str(time.strftime("Date: %Y-%m-%d - Time: %H:%M:%S"))
#report_file='example.log'

logging.basicConfig(filename=report_file, format='%(levelname)s %(asctime)s: %(message)s', level=logging.DEBUG)


#________________________________
def create_report(report):
    """
    Start build report for github upload.
    Write header file
    """
    with open(report, 'w') as logfile:
        logfile.write('*** Laniakea Image build Report ***\n')
        logfile.write(build_init_datetime+"\n")
        logfile.write('Report file: ' + str(report) + '\n')
        logfile.write('\n')


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
    print(report)
    add_cmd = 'git add '+report
    add_stdout, add_stderr, add_status = run_command(add_cmd)
    print('[Git add] '+str(add_stdout))
    print('[Git add] '+str(add_stderr))

    if add_status == 0:
        commit_cmd = 'git commit -m "Add automated report - ' + build_init_datetime +'"'
        print(commit_cmd)
        commit_stdout, commit_stderr, commit_status = run_command(commit_cmd)
        print('[Git commit] '+str(commit_stdout))
        print('[Git commit] '+str(commit_stderr))

        if commit_status == 0:
            push_cmd = 'git push'
            push_stdout, push_stderr, push_status = run_command(push_cmd)
            print('[Git push] '+str(push_stdout))
            print('[Git push] '+str(push_stderr))

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

    images_to_build = []
    for i in info_list['images']:

        image = info_list['images'][i]

        name = image['name']
        version = image['version']
        build = image['build']

        # Load template
        template = env.get_template('packer.json.j2')

        if build:

            # Render template
            rendered_template = template.render(
                                                name = name,
                                                version = version,
                                                ssh_username = image['packer']['ssh_username'],
                                                source_image = image['packer']['source_image'],
                                                flavor = image['packer']['flavor'],
                                                volume_size = image['packer']['volume_size'],
                                                network_id = image['packer']['network_id'],
                                                playbook_file = image['packer']['playbook_file']
                                               )

            # Write packer json to file
            fout_name = outpath+'/'+name+'.json'
            with open(fout_name, "w") as fout:
                fout.write(rendered_template)

            images_to_build.append(fout_name)

            logging.info('[Image to Build] '+name)
            logging.debug('[Packer template] '+rendered_template)

    return images_to_build

#________________________________
def build_images_with_packer(path_list):

    for template_path in path_list:
        logging.info('Start Build')
        build_image(template_path)

#________________________________
def build_image(path):
    """
    Run subprocess call redirecting stdout, stderr and the command exit code.
    """
    cmd = packer_exe + ' build ' + path
    print(cmd)

    proc = subprocess.Popen( args=cmd, shell=True,  stdout=subprocess.PIPE, stderr=subprocess.STDOUT )

    while proc.poll() is None:
        line = proc.stdout.readline()
        sl = line.strip()
        dsl = sl.decode('utf-8')
        print(dsl)
        logging.info('[Packer] '+dsl)

    status = proc.wait()

    return status

#________________________________
def build_images():

    create_report(report_file)

    images_info = load_list()

    # Create a temporary directory
    tempdir = tempfile.mkdtemp(dir='./')
    print('The created temporary directory is %s' % tempdir) # move to log

    # Create packer json
    images_to_build = parse_list(images_info, tempdir)
    print(images_to_build)

    # Build Packer images
    build_images_with_packer(images_to_build)

    # Upload report to github
    upload_report_to_github(report_file)

#______________________________________
if __name__ == "__main__":
   build_images()
