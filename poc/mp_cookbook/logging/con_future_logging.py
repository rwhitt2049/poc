from multiprocessing import Manager
from concurrent.futures import ProcessPoolExecutor
import logging.handlers
import logging


class GeneralHandler:
    """
    A simple handler for logging events.
    """

    def handle(self, record):
        logger = logging.getLogger(record.name)
        logger.handle(record)


def double(arg):
    q = arg[1]
    x = arg[0]
    qlog = logging.handlers.QueueHandler(q)
    root = logging.getLogger()
    root.addHandler(qlog)
    root.setLevel(logging.DEBUG)
    wrk = logging.getLogger('worker')
    try:
        1/x
    except ZeroDivisionError as e:
        wrk.exception(e)

    return 2*x


def main():
    q = Manager().Queue()
    wrk = logging.getLogger('worker')
    wrk.setLevel(logging.DEBUG)
    sh = logging.StreamHandler()
    wrk.addHandler(sh)

    lp = logging.handlers.QueueListener(q, GeneralHandler(), respect_handler_level=False)
    lp.start()

    numbs = ((x, q) for x in range(10))
    executor = ProcessPoolExecutor(max_workers=2)
    vals = executor.map(double, numbs)

    '''
    workers = []
    for i in range(10):

        wp = Process(target=double, args=([i, q],))
        workers.append(wp)
        wp.start()

    for wp in workers:
        wp.join()

    '''
    print(list(vals))
    lp.stop()

if __name__ == '__main__':
    main()