from time import sleep
from multiprocessing import Process, Queue, Value

from gaputils.iointerface.RRIProcess import RRIProcess
from gaputils.iointerface.SCUProcess import SCUProcess
from gaputils.iointerface.ModeCloudProcess import ModeCloudProcess
from gaputils.iointerface.CsvOutProcess import CsvOutProcess

# for debug
import logging
logger = logging.getLogger(__name__)

class MainProcess():
    # define default parameter
    __PARAM_DEFAULT = {
        'rri_flg':True,
        'rri':{},
        'scu_flg':True,
        'scu':{},
        'mode_flg':True,
        'mode':{},
        'csvout_flg':True,
        'csvout':{},
        'sleep_sec':0.001,
        }

    def __init__(self, param={}, lq=None):
        # set param to member of Class
        self.__param = param

        # check key and set default parameter if key doesn't exist
        for key in self.__PARAM_DEFAULT:
            if key not in self.__param:
                self.__param[key] = self.__PARAM_DEFAULT[key]
                # logger.info(f'Parameter "{key}" is set as default value "{self.__PARAM_DEFAULT[key]}".')

        # initialize input devices process
        self.__indevs = list()
        if self.__param['rri_flg']:
            self.__indevs.append(RRIProcess(self.__param['rri'], lq))
        if self.__param['scu_flg']:
            self.__indevs.append(SCUProcess(self.__param['scu'], lq))

        # initialize output devices process
        self.__outdevs = list()
        if self.__param['mode_flg']:
            self.__outdevs.append(ModeCloudProcess(self.__param['mode'], lq))
        if self.__param['csvout_flg']:
            self.__outdevs.append(CsvOutProcess(self.__param['csvout'], lq))

        # initialize members
        self.__queue = Queue()
        self.__run_flg = Value('i', 0)
        self.__lq = lq
        self.__p = None

    def _work(self, indevs, outdevs, queue, run_flg, lq):
        # set up logging for multiprocessing
        if lq is not None:
            h = logging.handlers.QueueHandler(lq)
            root = logging.getLogger()
            root.addHandler(h)
            root.setLevel(logging.NOTSET)
        
        # start devices
        for outdev in outdevs:
            outdev.start()
        for indev in indevs:
            indev.start()
        
        # set start flag as True
        run_flg.value = True

        # get data from indevs while run_flg is True
        logger.info('Start main process.')
        while True:
            if not run_flg.value and queue.empty():
                break

            for indev in indevs:
                if indev.data_get_size:
                    # get data
                    data = indev.data_get

                    # send data
                    for outdev in outdevs:
                        outdev.data_send = data

            sleep(self.__param['sleep_sec'])

        logger.info('Stop main process.')

        # stop devices
        for indev in indevs:
            indev.stop()
        for outdev in outdevs:
            outdev.stop()

    def start(self):
        if self.__p is None:
            # initialize serial process
            self.__p = Process(target=self._work, args=(self.__indevs, self.__outdevs, 
            self.__queue, self.__run_flg, self.__lq))

            # start process
            self.__p.start()

            # wait for __work process setup  is completed
            while not self.__run_flg.value:
                sleep(0.001)
            
            logger.info(f'Run {self.__class__.__name__} is completed.')
        else:
            logger.warning(f'{self.__class__.__name__} has already started.')

    def stop(self):
        rem = []
        if self.__p is not None:
            # turn run flag to off
            self.__run_flg.value = 0

            # workの処理が終わるようにとりあえず1msec待機
            sleep(0.001)

            # wait for process end
            if self.__p is not None:

                self.__p.join()
                logger.info(f'Join {self.__class__.__name__} is completed.')
                self.__p = None
        else:
            logger.warning(f'{self.__class__.__name__} has already stoped.')

        # queueのデータの残りを返す
        return rem
    
    @property
    def param(self):
        """
        getter of "param"
        """
        # get param from input devices
        for indev in self.__indevs:
            if isinstance(indev, RRIProcess):
               self.__param['rri'] = indev.param
            elif isinstance(indev, SCUProcess):
               self.__param['scu'] = indev.param
            else:
                msg = f'"{type(indev)}" is unknown class instance.'
                logger.error(msg)
                raise ValueError(msg)

        # get param from output devices
        for outdev in self.__outdevs:
            if isinstance(outdev, ModeCloudProcess):
                self.__param['mode'] = outdev.param
            elif isinstance(outdev, CsvOutProcess):
                self.__param['csvout'] = outdev.param
            else:
                msg = f'"{type(outdev)}" is unknown class instance.'
                logger.error(msg)
                raise ValueError(msg)

        return self.__param
