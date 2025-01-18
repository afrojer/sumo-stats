#!/usr/bin/env python3
#
# compare_physical.py
#
# Define physical trait comparators
#
# Each class should have a compare() function that takes a single SumoMatchup parameter.
# This function should return:
#     [-1, 0) to favor "opponent"
#     (0, 1] to favor "rikishi"
#     0 to pass through with no opinion
#

import os
import sys
cdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cdir)

from sumostats.sumodata import *
from sumostats.sumocalc import *

#
# Compare Rikishi based on BMI
#
class CompareBMI(SumoBoutCompare):
    def compare(self, matchup):
        #
        # Since 2000:
        #     Tallest Sumo wrestler: 1.96m
        #     Shorest Sumo wrestler: 1.60m
        #     Heaviest Sumo wrestler: 252kg
        #     Lighest Sumo wrestler: 61.8kg
        #
        # This gives us a possible BMI range of:
        #     largest: 252 / (1.6*1.6) = 98
        #     smallest: 61.8 / (1.96*1.96) = 16
        #
        # Overweight is 30+
        # A value of 98 is crazy, but looking at the top 10 heaviest Sumo
        # wrestlers of all-time, the largest BMI is actually around 85.
        #
        # Normal, healthy BMI is 18.5 - 24.9, so we will cap the lower range
        # to 18.5, and allow a BMI up to a crazy value of 85. We use this to
        # normalize the BMI value between 0 and 1
        #
        _minBMI = 18.5
        _maxBMI = 85
        _bmiRange = _maxBMI - _minBMI

        _rikishiBMI = (matchup.rikishi.bmi() - _minBMI) / _bmiRange
        _opponentBMI = (matchup.opponent.bmi() - _minBMI) / _bmiRange

        if _rikishiBMI > _opponentBMI:
            return _rikishiBMI
        else:
            return -_opponentBMI

#
# Compare Rikishi based on height
#
class CompareHeight(SumoBoutCompare):
    def compare(self, matchup):
        #
        # The tallest recorded Sumo wrestler is 2.27m (Ikuzuki Geitazaemon)
        # The shortest recorded Sumo wrestler is 1.58m (Tamatsubaki Kentarō)
        #
        _maxHeight = 227.0 # cm
        _minHeight = 158.0 # cm
        _heightDiffRange = _maxHeight - _minHeight

        # using rikishi as the numerator will produce positive numbers for a
        # rikishi taller than his opponent, and negative numbers for an
        # opponent taller than the rikishi
        _diff = matchup.rikishi.height() - matchup.opponent.height()
        return _diff / _heightDiffRange

#
# Compare Rikishi based on weight
#
class CompareWeight(SumoBoutCompare):
    def compare(self, matchup):
        #
        # The heaviest recorded Sumo wrestler is 292.6kg (Ōrora Satoshi)
        # The lightest recorded Sumo wrestler is 73kg (Tamatsubaki Kentarō)
        #
        _maxWeight = 292.6 # kg
        _minWeight = 73.0 # kg
        _weightDiffRange = _maxWeight - _minWeight

        # using rikishi as the numerator will produce positive numbers for a
        # rikishi heavier than his opponent, and negative numbers for an
        # opponent heavier than the rikishi
        _diff = matchup.rikishi.weight() - matchup.opponent.weight()
        return _diff / _weightDiffRange

