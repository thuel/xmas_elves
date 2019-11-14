import argparse
import functools
import logging
import logging.handlers as handlers

from pathlib import Path

logformat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.DEBUG, format=logformat)

logger=logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = handlers.RotatingFileHandler(Path(__file__).name + '.log', maxBytes=1000, backupCount=2)
handler.setLevel(logging.INFO)

formatter = logging.Formatter(logformat)
handler.setFormatter(formatter)

logger.addHandler(handler)



def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('arg1', type=str, help='help for arg1 comes here')
    return parser.parse_args()


def main():
    """ Executes the main application when called from cmdline.
    """
    args = parse_args()
    logger.debug(args)

if __name__ == "__main__":
    main()