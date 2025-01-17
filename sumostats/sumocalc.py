#!/usr/bin/env python3

from .sumoapi import *

from datetime import date
from dateutil.relativedelta import *
import sys

class BoutCompare():
    def __init__(self, data:SumoData):
        self._data = data

    # Override this method
    #
    # Return:
    #   [-1, 0) to favor opponent
    #   (0, 1] to favor rikishi
    #   [0] to pass-through with no opinion about this matchup
    def compare(self, matchup:SumoMatchup):
        pass

    def __call__(self, matchup:SumoMatchup):
        return self.compare(matchup)

#
# Compare Rikishi based on BMI
#
class CompareBMI(BoutCompare):
    def compare(self, matchup):
        return 1.0 - matchup.rikishi.bmi() / matchup.opponent.bmi()

