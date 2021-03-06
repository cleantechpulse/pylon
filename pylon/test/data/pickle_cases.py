#!/usr/bin/python

import sys
import os.path
import logging

from pylon.util import pickle_matpower_cases

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
    format="%(levelname)s: %(message)s")

def pickle_cases():
    data_dir = os.path.dirname(__file__)
    case_paths = [os.path.join(data_dir, 'case30pwl.m'),
                  os.path.join(data_dir, 'case6ww.m'),
                  os.path.join(data_dir, 'case24_ieee_rts.m'),
                  os.path.join(data_dir, 'case_ieee30.m')]

    pickle_matpower_cases(case_paths)
    pickle_matpower_cases(os.path.join(data_dir, 'case3bus_P6_6.m'), 1)


if __name__ == '__main__':
    pickle_cases()
