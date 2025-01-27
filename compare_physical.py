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

class CompareBMI(SumoBoutCompare):
    """
    Compare rikishi based on BMI

    Since 2000:
        Tallest Sumo wrestler: 1.96m
        Shorest Sumo wrestler: 1.60m
        Heaviest Sumo wrestler: 252kg
        Lighest Sumo wrestler: 61.8kg

    This gives us a possible BMI range of:
        largest: 252 / (1.6*1.6) = 98
        smallest: 61.8 / (1.96*1.96) = 16

    Overweight is 30+
    A value of 98 is crazy, but looking at the top 10 heaviest Sumo
    wrestlers of all-time, the largest BMI is actually around 85.

    Normal, healthy BMI is 18.5 - 24.9, so we will cap the lower range
    to 18.5, and allow a BMI up to a crazy value of 85. We use this to
    normalize the BMI value between 0 and 1

    """
    def compare(self, matchup, basho, day):
        _minBMI = 18.5
        _maxBMI = 85
        _bmiRange = _maxBMI - _minBMI

        # produce positive numbers for a rikishi with higher BMI than
        # his opponent, and negative numbers for an opponent with
        # higher BMI than the rikishi
        _bmiDiff = matchup.rikishi.bmi() - matchup.opponent.bmi()
        _pct = _bmiDiff / _bmiRange

        self.debug('BMIDiff:@bmi, PCT:@pct', bmi=_bmiDiff, pct=_pct)
        return _pct

class CompareHeight(SumoBoutCompare):
    """
    Compare rikishi based on height

    The tallest recorded Sumo wrestler is 2.27m (Ikuzuki Geitazaemon)
    The shortest recorded Sumo wrestler is 1.58m (Tamatsubaki Kentarō)

    """
    def compare(self, matchup, basho, day):
        _maxHeight = 227.0 # cm
        _minHeight = 158.0 # cm
        _heightDiffRange = _maxHeight - _minHeight

        # using rikishi as the numerator will produce positive numbers for a
        # rikishi taller than his opponent, and negative numbers for an
        # opponent taller than the rikishi
        _diff = matchup.rikishi.height() - matchup.opponent.height()
        _pct = _diff / _heightDiffRange

        self.debug('HeightDiff:@height, PCT:@pct', height=_diff, pct=_pct)
        return _pct

class CompareWeight(SumoBoutCompare):
    """
    Compare rikishi based on weight

    The heaviest recorded Sumo wrestler is 292.6kg (Ōrora Satoshi)
    The lightest recorded Sumo wrestler is 73kg (Tamatsubaki Kentarō)

    """
    def compare(self, matchup, basho, day):
        _maxWeight = 292.6 # kg
        _minWeight = 73.0 # kg
        _weightDiffRange = _maxWeight - _minWeight

        # using rikishi as the numerator will produce positive numbers for a
        # rikishi heavier than his opponent, and negative numbers for an
        # opponent heavier than the rikishi
        _diff = matchup.rikishi.weight() - matchup.opponent.weight()
        _pct = _diff / _weightDiffRange

        self.debug('WeightDiff:@weight, PCT:@pct', weight=_diff, pct=_pct)
        return _pct

