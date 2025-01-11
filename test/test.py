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


def TestAPI():
    sumo = SumoAPI()

    print("rikishi = sumo.rikishis(limit=2, skip=23)")
    try:
        rikishi = sumo.rikishis(limit=2, skip=23)
        PrintRikishi(rikishi)
    except Exception as e:
        print(e)
    print('\n')


    print("rikishi = sumo.rikishis(limit=5, shikonaEn='Onosho')")
    try:
        rikishi = sumo.rikishis(limit=5, shikonaEn='Onosho')
        PrintRikishi(rikishi)
    except Exception as e:
        print(e)
    print('\n')

    print("rikishi = sumo.rikishis(limit=2, skip=1111, retired=True)")
    rikishi = sumo.rikishis(limit=2, skip=1111, retired=True)
    PrintRikishi(rikishi)
    print('\n')

    print("rikishi = sumo.rikishis(limit=2, shikonaEn='Terunofuji')")
    rikishi = sumo.rikishis(limit=2, shikonaEn='Terunofuji')
    PrintRikishi(rikishi)
    print('\n')

    print("rikishi = sumo.rikishis(limit=2, shikonaEn='Shishi', shikonas='true', measurements='true', ranks='true')")
    rikishi = sumo.rikishis(limit=2, shikonaEn='Shishi', shikonas='true', measurements='true', ranks='true')
    PrintRikishi(rikishi)
    print('\n')

    print("rikishi = sumo.rikishi(86)")
    rikishi = sumo.rikishi(86)
    PrintRikishi(rikishi)
    print('\n')

    print("rikishi= sumo.rikishi(86, measurements=True)")
    rikishi= sumo.rikishi(86, measurements=True)
    PrintRikishi(rikishi)
    print('\n')

    print("rikishi= sumo.rikishi(86, ranks=True)")
    rikishi= sumo.rikishi(86, ranks=True)
    PrintRikishi(rikishi)
    print('\n')

    print("rikishi= sumo.rikishi(86, shikonas=True)")
    rikishi= sumo.rikishi(86, shikonas=True)
    PrintRikishi(rikishi)
    print('\n')

    print("stats = sumo.rikishi_stats(45)")
    stats = sumo.rikishi_stats(45)
    print(stats)
    print('\n')

    print("matches = sumo.rikishi_matches(45, limit=3)")
    matches = sumo.rikishi_matches(45, limit=3)
    print(matches)
    print('\n')

    print("basho = sumo.basho(202412)")
    basho = sumo.basho(202412)
    print(basho)
    print('\n')

    print("basho = sumo.basho(202411)")
    basho = sumo.basho(202411)
    print(basho)
    print('\n')

    print("banzuke = sumo.basho_banzuke(202409, SumoDivision.Makuuchi)")
    banzuke = sumo.basho_banzuke(202409, SumoDivision.Makuuchi)
    print(banzuke)
    print('\n')

    print("torikumi = sumo.basho_torikiumi(202409, SumoDivision.Juryo, 6)")
    torikumi = sumo.basho_torikumi(202409, SumoDivision.Juryo, 6)
    print(torikumi)
    print('\n')

    return

def TestTable():
    sumotable = SumoTable()
    sumotable.TEST_IT()
    sumotable.save_table('./sumo_data.pickle')
    return

TestTable()
#TestAPI()
