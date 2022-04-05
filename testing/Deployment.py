import subprocess

from LogFacility import logger
logger.info('Deployment class')


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
class Deployment:

    def __init__(self, tosca, inputs, url):

        command="/usr/bin/orchent depcreate -g elixir-italy " + tosca + " '" + inputs + "'" + " -u " + url
        logger.debug(command)

        stdout, stderr, status = run_command(command)

        temp = stdout.split(b"Deployment",1)[1]

        dep_uuid = temp.splitlines()[0].strip(b" []:")
        logger.debug('[Deployment] Uuid: %s'% dep_uuid)

        dep_status = temp.splitlines()[1].strip(b" status: ")
        logger.debug('[Deployment] Uuid: %s, status: %s' % (dep_uuid, dep_status))

        self.dep_uuid = dep_uuid.decode("utf-8")
        self.dep_status = dep_status.decode("utf-8")

    def get_uuid(self): return self.dep_uuid
    def get_status(self): return self.dep_status
