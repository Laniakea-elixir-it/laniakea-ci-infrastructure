import logging
import sys

class LogFacility:

    def __init__(self):

        self.log_file = '/tmp/indigo_paas_checker.log' 

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

        # Create handler for log file and stdout
        logger_outfile_handler = logging.FileHandler(self.log_file,mode='w')
        logger_stdout_handler = logging.StreamHandler(sys.stdout)
        # Set formatter for log file and stdout
        logger_formatter = logging.Formatter('%(levelname)s %(asctime)s %(message)s')
        logger_outfile_handler.setFormatter(logger_formatter)
        logger_stdout_handler.setFormatter(logger_formatter)
        # Load configuration for log file and stdout
        self.logger.addHandler(logger_outfile_handler)
        self.logger.addHandler(logger_stdout_handler)

    def get_logger(self):
        return self.logger


log_facility = LogFacility()
logger = log_facility.get_logger()
logger.info('test')
