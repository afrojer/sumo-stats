#!/usr/bin/env python3

import os
import sys

cdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cdir+'/../')
from sumostats.sumoapi import *
from sumostats.sumotable import *

def PrintRikishi(rinput):
    # print(rinput)
    if hasattr(rinput, '__len__'):
        for r in rinput:
            print(r)
    else:
        print(rinput)

def TestTable():
    sumotable = SumoTable()
    sumotable.TEST_IT()
    sumotable.save_table('./sumo_data.pickle')
    return

TestTable()
