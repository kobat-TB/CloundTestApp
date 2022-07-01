
import json
import os
from time import sleep
from gaputils.iointerface.LoggerProcess import LoggerProcess
from lib.MainProcess import MainProcess

__version__ = '0.1.0'

class main:
    # define default parameter
    __PARAM_DEFAULT = {
        'ver':__version__,
        'logger':{},
        'mainprocess':{},
        }

    def __init__(self):
        ### initialize logger process ###
        lp = LoggerProcess()
        lp.start()
        sleep(4)
        logger = lp.getLogger(__name__)

        ### read config.ini ###
        logger.info('read config.ini')
        config_path = 'config.ini'
        if os.path.exists(config_path):
            # open config.ini if exists it
            with open(config_path, 'r') as file:
                param = json.load(file)
            for key in self.__PARAM_DEFAULT:
                if key not in param:
                    param[key] = self.__PARAM_DEFAULT[key]
        else:
            # create new param using default value
            param = dict()
            for key in self.__PARAM_DEFAULT:
                param[key] = self.__PARAM_DEFAULT[key]

        # save current version information
        param['ver'] = __version__

        mp = MainProcess(param['mainprocess'], lp.queue)
        mp.start()
        sleep(600)
        mp.stop()

        ### save config.ini ###
        logger.info('save config.ini')
        param_out = {}
        param_out['ver'] = param['ver']
        param_out['logger'] = lp.param
        param_out['mainprocess'] = mp.param

        with open(config_path, 'w') as file:
            json.dump(param_out, file, indent=2)

        ### stop logger ###
        lp.stop()

if __name__ == "__main__":
    main()
