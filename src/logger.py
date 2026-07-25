import logging

from typing import Optional

class Logger():
    # Default configuration: 
    #   - logging_file: None, by default logs are not saved in the filesystem
    #   - logging_level: INFO

    log_filepath: Optional[str] = None
    logging_level: int = logging.INFO

    @staticmethod
    def set_logging_config(log_filepath: Optional[str], logging_level: int):
        if log_filepath is not None:
            logging.basicConfig(filename=log_filepath, level=logging_level)
        else:
            logging.basicConfig(level=logging_level)

    @staticmethod
    def get_logger(classname: str) ->logging.Logger:
        return logging.getLogger(classname)    