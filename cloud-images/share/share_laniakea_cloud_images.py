#!/usr/bin/env python
"""
Source documentation: https://userguide.cloudveneto.it/en/latest/ManagingImages.html
"""
import yaml
import subprocess
import logging
import requests
import sys
import argparse

#tenant_list_yaml_path = './laniakea_tanant_list.yaml'


#______________________________________
def cli_options():

  parser = argparse.ArgumentParser(description='Share cloud images among tanants.')

  parser.add_argument('-i', '--image-id', dest='image_id', help='Image to share by ID.')
  parser.add_argument('-l', '--tenant-list', dest='tenant_list', default='./laniakea_tenant_list.yml', help='Laniakea tenant list.')
  parser.add_argument('-s', '--source-tenant', dest='source_tenant', default='usegalaxy-it', help='Source tenant hosting the image to share.')
  parser.add_argument('-d', '--destinantion-tenants', dest='destination_tenants', default='elixir-italy-services,ELIXIR-PAAS', help='Destination tenants list to share the image with.')
  parser.add_argument('-t', '--token', dest='token', help='The IAM Access Token.')
  parser.add_argument('-a', '--tag', dest='tag', default='recas-paas',  help='Set tag to image allowing cip to import them on cmdb.')

  return parser.parse_args()

#______________________________________
def parse_yaml(yaml_file):
    with open(yaml_file, 'r') as fin:
        tli = yaml.safe_load(fin)
        return tli

#______________________________________
def build_openstack_cmd(os_access_token=None, os_auth_type='v3oidcaccesstoken', os_auth_url='https://keystone.recas.ba.infn.it/v3', os_protocol='openid', os_identity_provider='recas-bari', os_idendtity_api_version='3'):
    """
    Example
    openstack --os-auth-type v3oidcaccesstoken --os-access-token ${IAM_ACCESS_TOKEN} --os-auth-url https://keystone.recas.ba.infn.it/v3 --os-protocol openid --os-identity-provider recas-bari --os-identity-api-version 3 --os-project-id de43ed139278425c981263c90e39f18e ...
    We can't use the project id as base command since it is going to change with respect to the src or dest tenant.
    """

    cmd = 'openstack --os-auth-type ' + os_auth_type + ' --os-access-token ' + os_access_token + ' --os-auth-url ' + os_auth_url + ' --os-protocol ' + os_protocol + ' --os-identity-provider ' + os_identity_provider + ' --os-identity-api-version ' + os_idendtity_api_version

    return cmd

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
def change_image_visibility(base_cmd, source_project_id, image_id, visibility):

    cmd = base_cmd + ' --os-project-id ' + source_project_id + ' image set --property visibility=' + visibility + ' ' + image_id

    print(f'Change visibility of the image { image_id }: { cmd }')
    
    stdout, stderr, status = run_command(cmd)

    return stdout, stderr, status

#______________________________________
def add_image_tag(base_cmd, source_project_id, tag, image_id):
    """
    Add image tag allowing cip to retrieve the image
    Command: openstack image set --tag recas-paas 5537b6be-b606-4a26-a205-e1f2fe9d1c67
    """

    cmd = base_cmd + ' --os-project-id ' + source_project_id + ' image set --tag ' + tag + ' ' + image_id

    print(f'Add { tag } to image { image_id }: { cmd }')

    stdout, stderr, status = run_command(cmd)

    return stdout, stderr, status

#______________________________________
def add_image_to_project(base_cmd, source_project_id, image_id, dest_project_id):

    cmd = base_cmd + ' --os-project-id ' + source_project_id + ' image add project ' + image_id + ' ' + dest_project_id

    print(f'Add { image_id } from { source_project_id } to project { dest_project_id }: { cmd }')

    stdout, stderr, status = run_command(cmd)

    return stdout, stderr, status

#______________________________________
def accept_image(base_cmd, dest_project_id, image_id):

    cmd = base_cmd + ' --os-project-id ' + dest_project_id + ' image set --accept ' + image_id

    print(f'Accept { image_id } to project { dest_project_id }: { cmd }')

    stdout, stderr, status = run_command(cmd)

    return stdout, stderr, status

#______________________________________
def share_images():

    options = cli_options()
    tenant_list = parse_yaml(options.tenant_list)

    src = options.source_tenant
    source_project_id = tenant_list['tenants'][src]['id']

    tenant_dest_li = (options.destination_tenants).split(",")

    # Build base openstack command.
    base_openstack_cmd = build_openstack_cmd(os_access_token=options.token)

    # Operations performed on Source tenant
    #if options.image_id is None:
    #    raise error(ValueError, "image id not found")

    # Change image visibility to shared
    print('1. Change image visibility')
    civ_stdout, civ_stderr, civ_status = change_image_visibility(base_openstack_cmd, source_project_id, options.image_id, 'shared')
    print(civ_stdout)
    print(civ_stderr)
    print(civ_status)
    print('-----------------------')

    # Set image tag for cip import
    print('2. Add image tag.')
    it_stdout, it_stderr, it_status = add_image_tag(base_openstack_cmd, source_project_id, options.tag, options.image_id)
    print(it_stdout)
    print(it_stderr)
    print(it_status)
    print('-----------------------')

    # Add image to dest tenants
    print('3. Add image to project.')
    for tenant in tenant_dest_li:
        dest_tenant_id = tenant_list['tenants'][tenant]['id']

        adi_stdout, adi_stderr, adi_status = add_image_to_project(base_openstack_cmd, source_project_id, options.image_id, dest_tenant_id)
        print(adi_stdout)
        print(adi_stderr)
        print(adi_status)
        print('-----------------------')

        aci_stdout, aci_stderr, aci_status = accept_image(base_openstack_cmd, dest_tenant_id, options.image_id)
        print(aci_stdout)
        print(aci_stderr)
        print(aci_status)
        print('-----------------------')

#______________________________________
if __name__ == "__main__":
   share_images()
