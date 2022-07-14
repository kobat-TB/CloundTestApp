
from copy import deepcopy
import json
from inputimeout import inputimeout, TimeoutOccurred
import os
import sys
from time import sleep, time
from gaputils.iointerface.LoggerProcess import LoggerProcess
from pyparsing import Opt
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

        # recognize args
        args = deepcopy(sys.argv[1:])
        fname = None
        mtime = None
        while args:
            opt = args.pop(0)
            if opt == '-n':
                if not args:
                    raise ValueError(f'Opt "-r" require the output file name.')
                fname = args.pop(0)
            elif opt == '-t':
                if not args:
                    raise ValueError(f'Opt "-t" needs the measurement time in integer.')
                mtime = args.pop(0)
                if not mtime.isdigit():
                    raise ValueError(f'Opt "-t" needs the measurement time in integer.')
                mtime = int(mtime)
            else:
                raise ValueError(f'Opt "{opt}" is unknown.')
        if mtime is None:
            mtime = sys.maxsize
        
        # start main process
        mp = MainProcess(param['mainprocess'], lp.queue)
        mp.start()

        logger.info('Start measurement.')
        t_start = time()
        while True:
            input_str = ''
            try:
                input_str = inputimeout(prompt='>>', timeout=1)
            except TimeoutOccurred:
                print(f'time out')

            if input_str.upper() == 'STOP':
                print(f'get stop command')
            else:
                print(f'"{input_str} is unknown.')
                
            t_now = time()
            if (t_now - t_start) > mtime:
                break
            sleep(0.1)

        # stop main process
        mp.stop()
        logger.info('Start measurement.')

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
