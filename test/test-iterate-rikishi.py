#!/usr/bin/env python3

import os
import sys

cdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cdir+'/../')
from sumostats.sumoapi import *
from sumostats.sumodata import *


def TestIterateOverAllRikishi(picklefile = './sumodata_200001_202411.pickle'):
    sumodata = None
    try:
        sumodata = SumoData.load_data(picklefile)
    except:
        pass

    if not sumodata:
        sumodata = SumoData()
    sumodata.print_table_stats()

    max_height = 0.0
    tallest_rikishi = None
    min_height = 9999999.0
    shortest_rikishi = None
    max_weight = 0.0
    heaviest_rikishi = None
    min_weight = 9999999.0
    lightest_rikishi = None

    for rikishi in sumodata.each_rikishi():
        h = rikishi.height()
        w = rikishi.weight()
        if h > max_height:
            max_height = h
            tallest_rikishi = rikishi
        if h < min_height and h > 0.0:
            min_height = h
            shortest_rikishi = rikishi
        if w > max_weight:
            max_weight = w
            heaviest_rikishi = rikishi
        if w < min_weight and w > 0.0:
            min_weight = w
            lightest_rikishi = rikishi

    print(f'Found {sumodata.total_rikishi()} rikishi')
    print(f'Tallest: {tallest_rikishi} : {tallest_rikishi.height()}cm ({max_height}cm)')
    print(f'Shortest: {shortest_rikishi} : {shortest_rikishi.height()}cm ({min_height}cm)')
    print(f'Heaviest: {heaviest_rikishi} : {heaviest_rikishi.weight()}kg ({max_weight}kg)')
    print(f'Lightest: {lightest_rikishi} : {lightest_rikishi.weight()}kg ({min_weight}kg)')

    # BMI = weight (kg) / (height (m))^2
    largest_bmi = heaviest_rikishi.weight() / ((shortest_rikishi.height()/100.0) * (shortest_rikishi.height()/100.0))
    smallest_bmi = lightest_rikishi.weight() / ((tallest_rikishi.height()/100.0) * (tallest_rikishi.height()/100.0))
    print(f'largest possible BMI: {largest_bmi}')
    print(f'smallest possible BMI: {smallest_bmi}')

    return


TestIterateOverAllRikishi()
