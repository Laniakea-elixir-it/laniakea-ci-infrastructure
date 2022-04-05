import re
import yaml
import requests
import json

import Utils

from LogFacility import logger
logger.info('Deployment class')

#______________________________________
class Deployment:

    def __init__(self, tosca, inputs, url):

        command="/usr/bin/orchent depcreate -g elixir-italy " + tosca + " '" + inputs + "'" + " -u " + url
        logger.debug(command)

        stdout, stderr, status = Utils.run_command(command)

        temp = stdout.split(b"Deployment",1)[1]

        dep_uuid = temp.splitlines()[0].strip(b" []:")
        logger.debug('[Deployment] Uuid: %s'% dep_uuid)

        dep_status = temp.splitlines()[1].strip(b" status: ")
        logger.debug('[Deployment] Uuid: %s, status: %s' % (dep_uuid, dep_status))

        self.dep_uuid = dep_uuid.decode("utf-8")


    def get_uuid(self): return self.dep_uuid


    def __get_details(self):

        command="/usr/bin/orchent depshow " + self.dep_uuid

        stdout, stderr, status = Utils.run_command(command)

        # check if the deployment has been deleted
        #pattern = "Error 'Not Found' [404]"
        pattern = "doesn't exist"
        match = re.search(pattern, stdout.decode("utf-8"))
        if (match is not None):
            logger.debug('Deployment with uuid %s already deleted!' % self.dep_uuid)
            self.dep_status = 'DELETE_COMPLETE'

        temp = stdout.split(b"Deployment",1)[1]
        return temp


    def get_status(self):
    
        deployment = self.__get_details()
    
        if deployment == 'DELETE_COMPLETE':
          return deployment
    
        dep_status = deployment.splitlines()[1].strip(b" status: ")
    
        self.dep_status = dep_status.decode("utf-8")

        return self.dep_status


    def __get_outputs_json(self):
    
        # Get depployment despshow output
        deployment = self.__get_details()
    
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


    def get_endpoint(self):

        outputs = self.__get_outputs_json()

        # Check if deployment is already deleted.
        if outputs == {}:
            return 0

        self.dep_endpoint = outputs['endpoint']

        return self.dep_endpoint


    def depshow(self):
    
        command="/usr/bin/orchent depshow " + self.dep_uuid
    
        stdout, stderr, status = Utils.run_command(command)
    
        return stdout.decode("utf-8"), stderr.decode("utf-8"), status


    def depdel(self):

        command="/usr/bin/orchent depdel " + self.dep_uuid
        logger.debug(command)

        stdout, stderr, status = Utils.run_command(command)

        return stdout.decode("utf-8"), stderr.decode("utf-8"), status
