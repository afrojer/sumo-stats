#!/usr/bin/env python3

import json
import re
from enum import Enum
from datetime import datetime, date
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, Undefined, config as dcjson_config

def _decode_datetime(datestr):
    """ custom decoder for older python versions that don't like the 'Z' in for iso date format """
    #print(f'INPUT:{datestr}')
    return datetime.fromisoformat(datestr.replace('Z', '+00:00'))


def _decode_date(datestr):
    """ custom decoder for older python versions that only like YYYY-MM-DD """
    #print(f'INPUT:{datestr}')
    while len(datestr) < 8:
        datestr  += '01'
    m = re.match(r'(\d{4})(\d{2})(\d{2})', datestr)
    return date.fromisoformat(f'{m.group(1)}-{m.group(2)}-{m.group(3)}')

def BashoIdStr(bashoId: date):
    return f'{bashoId.year:04}{bashoId.month:02}'

def BashoDate(bashoStr: str):
    while len(bashoStr) < 8:
        bashoStr += '01'
    m = re.match(r'(\d{4})(\d{2})(\d{2})', bashoStr)
    return date.fromisoformat(f'{m.group(1)}-{m.group(2)}-{m.group(3)}')

_RikishiRankValue: dict[str, int] = {
    "Yokozuna 1 East": 101,
    "Yokozuna 1 West": 103,
    "Ozeki 1 East": 202,
    "Ozeki 2 East": 203,
    "Ozeki 1 West": 203,
    "Ozeki 2 West": 204,
    "Sekiwake 1 East": 302,
    "Sekiwake 2 West": 302,
    "Sekiwake 2 East": 303,
    "Sekiwake 1 West": 303,
    "Komusubi 1 East": 402,
    "Komusubi 1 West": 403,
    "Komusubi 2 East": 403,
    "Komusubi 2 West": 404,
    "Maegashira 1 East": 502,
    "Maegashira 2 East": 503,
    "Maegashira 1 West": 503,
    "Maegashira 3 East": 503,
    "Maegashira 4 West": 504,
    "Maegashira 3 West": 505,
    "Maegashira 4 East": 505,
    "Maegashira 5 East": 506,
    "Maegashira 2 West": 506,
    "Maegashira 6 East": 507,
    "Maegashira 5 West": 507,
    "Maegashira 6 West": 508,
    "Maegashira 7 West": 509,
    "Maegashira 8 East": 509,
    "Maegashira 7 East": 509,
    "Maegashira 9 East": 510,
    "Maegashira 8 West": 510,
    "Maegashira 10 East": 511,
    "Maegashira 9 West": 511,
    "Maegashira 10 West": 512,
    "Maegashira 11 East": 512,
    "Maegashira 12 East": 513,
    "Maegashira 11 West": 513,
    "Maegashira 13 East": 514,
    "Maegashira 12 West": 514,
    "Maegashira 14 East": 515,
    "Maegashira 13 West": 515,
    "Maegashira 15 East": 516,
    "Maegashira 14 West": 516,
    "Maegashira 16 East": 517,
    "Maegashira 15 West": 517,
    "Maegashira 17 East": 518,
    "Maegashira 16 West": 518,
    "Maegashira 18 East": 519,
    "Maegashira 17 West": 519,
    "Juryo 1 East": 602,
    "Juryo 2 East": 602,
    "Juryo 1 West": 603,
    "Juryo 3 East": 604,
    "Juryo 2 West": 604,
    "Juryo 3 West": 605,
    "Juryo 4 East": 605,
    "Juryo 5 East": 606,
    "Juryo 4 West": 606,
    "Juryo 5 West": 607,
    "Juryo 6 East": 607,
    "Juryo 6 West": 608,
    "Juryo 7 East": 608,
    "Juryo 8 East": 609,
    "Juryo 7 West": 609,
    "Juryo 9 East": 610,
    "Juryo 8 West": 610,
    "Juryo 9 West": 611,
    "Juryo 10 East": 611,
    "Juryo 11 East": 612,
    "Juryo 10 West": 612,
    "Juryo 11 West": 613,
    "Juryo 12 East": 613,
    "Juryo 13 East": 614,
    "Juryo 12 West": 614,
    "Juryo 13 West": 615,
    "Juryo 14 East": 615,
    "Juryo 14 West": 616,
    "Makushita 1 East": 702,
    "Makushita 1 West": 703,
    "Makushita 2 East": 703,
    "Makushita 2 West": 704,
    "Makushita 3 East": 704,
    "Makushita 4 East": 705,
    "Makushita 3 West": 705,
    "Makushita 5 East": 706,
    "Makushita 4 West": 706,
    "Makushita 6 East": 707,
    "Makushita 5 West": 707,
    "Makushita 7 East": 708,
    "Makushita 6 West": 708,
    "Makushita 7 West": 709,
    "Makushita 8 East": 709,
    "Makushita 9 East": 710,
    "Makushita 8 West": 710,
    "Makushita 10": 710,
    "Makushita 10 East": 711,
    "Makushita 9 West": 711,
    "Makushita 10 West": 712,
    "Makushita 11 East": 712,
    "Makushita 12 East": 713,
    "Makushita 11 West": 713,
    "Makushita 12 West": 714,
    "Makushita 13 East": 714,
    "Makushita 13 West": 715,
    "Makushita 14 East": 715,
    "Makushita 15": 715,
    "Makushita 15 East": 716,
    "Makushita 14 West": 716,
    "Makushita 15 West": 717,
    "Makushita 16 East": 717,
    "Makushita 16 West": 718,
    "Makushita 17 East": 718,
    "Makushita 18 East": 719,
    "Makushita 17 West": 719,
    "Makushita 18 West": 720,
    "Makushita 19 East": 720,
    "Makushita 19 West": 721,
    "Makushita 20 East": 721,
    "Makushita 20 West": 722,
    "Makushita 21 East": 722,
    "Makushita 21 West": 723,
    "Makushita 22 East": 723,
    "Makushita 22 West": 724,
    "Makushita 23 East": 724,
    "Makushita 23 West": 725,
    "Makushita 24 East": 725,
    "Makushita 24 West": 726,
    "Makushita 25 East": 726,
    "Makushita 26 East": 727,
    "Makushita 25 West": 727,
    "Makushita 27 East": 728,
    "Makushita 26 West": 728,
    "Makushita 27 West": 729,
    "Makushita 28 East": 729,
    "Makushita 29 East": 730,
    "Makushita 28 West": 730,
    "Makushita 29 West": 731,
    "Makushita 30 East": 731,
    "Makushita 31 East": 732,
    "Makushita 30 West": 732,
    "Makushita 31 West": 733,
    "Makushita 32 East": 733,
    "Makushita 33 East": 734,
    "Makushita 32 West": 734,
    "Makushita 34 East": 735,
    "Makushita 33 West": 735,
    "Makushita 35 East": 736,
    "Makushita 34 West": 736,
    "Makushita 35 West": 737,
    "Makushita 36 East": 737,
    "Makushita 37 East": 738,
    "Makushita 36 West": 738,
    "Makushita 37 West": 739,
    "Makushita 38 East": 739,
    "Makushita 39 East": 740,
    "Makushita 38 West": 740,
    "Makushita 39 West": 741,
    "Makushita 41 West": 741,
    "Makushita 40 East": 741,
    "Makushita 41 East": 742,
    "Makushita 40 West": 742,
    "Makushita 42 East": 743,
    "Makushita 42 West": 744,
    "Makushita 43 East": 744,
    "Makushita 44 East": 745,
    "Makushita 43 West": 745,
    "Makushita 45 East": 746,
    "Makushita 44 West": 746,
    "Makushita 46 East": 747,
    "Makushita 45 West": 747,
    "Makushita 47 East": 748,
    "Makushita 46 West": 748,
    "Makushita 48 East": 749,
    "Makushita 47 West": 749,
    "Makushita 49 East": 750,
    "Makushita 48 West": 750,
    "Makushita 50 East": 751,
    "Makushita 49 West": 751,
    "Makushita 50 West": 752,
    "Makushita 51 East": 752,
    "Makushita 51 West": 753,
    "Makushita 52 East": 753,
    "Makushita 53 East": 754,
    "Makushita 52 West": 754,
    "Makushita 54 East": 755,
    "Makushita 53 West": 755,
    "Makushita 55 East": 756,
    "Makushita 54 West": 756,
    "Makushita 56 East": 757,
    "Makushita 55 West": 757,
    "Makushita 56 West": 758,
    "Makushita 57 East": 758,
    "Makushita 58 East": 759,
    "Makushita 57 West": 759,
    "Makushita 59 East": 760,
    "Makushita 58 West": 760,
    "Makushita 59 West": 761,
    "Makushita 60 East": 761,
    "Makushita 60 West": 762,
    "Sandanme 1 East": 802,
    "Sandanme 1 West": 803,
    "Sandanme 2 East": 803,
    "Sandanme 3 East": 804,
    "Sandanme 2 West": 804,
    "Sandanme 3 West": 805,
    "Sandanme 4 East": 805,
    "Sandanme 5 East": 806,
    "Sandanme 4 West": 806,
    "Sandanme 5 West": 807,
    "Sandanme 6 East": 807,
    "Sandanme 6 West": 808,
    "Sandanme 7 East": 808,
    "Sandanme 7 West": 809,
    "Sandanme 8 East": 809,
    "Sandanme 8 West": 810,
    "Sandanme 9 East": 810,
    "Sandanme 10 East": 811,
    "Sandanme 9 West": 811,
    "Sandanme 11 East": 812,
    "Sandanme 10 West": 812,
    "Sandanme 11 West": 813,
    "Sandanme 12 East": 813,
    "Sandanme 13 East": 814,
    "Sandanme 12 West": 814,
    "Sandanme 14 East": 815,
    "Sandanme 13 West": 815,
    "Sandanme 15 East": 816,
    "Sandanme 14 West": 816,
    "Sandanme 16 East": 817,
    "Sandanme 15 West": 817,
    "Sandanme 16 West": 818,
    "Sandanme 17 East": 818,
    "Sandanme 18 East": 819,
    "Sandanme 17 West": 819,
    "Sandanme 19 East": 820,
    "Sandanme 18 West": 820,
    "Sandanme 19 West": 821,
    "Sandanme 20 East": 821,
    "Sandanme 20 West": 822,
    "Sandanme 21 East": 822,
    "Sandanme 21 West": 823,
    "Sandanme 22 East": 823,
    "Sandanme 22 West": 824,
    "Sandanme 23 East": 824,
    "Sandanme 23 West": 825,
    "Sandanme 24 East": 825,
    "Sandanme 24 West": 826,
    "Sandanme 25 East": 826,
    "Sandanme 26 East": 827,
    "Sandanme 25 West": 827,
    "Sandanme 26 West": 828,
    "Sandanme 27 East": 828,
    "Sandanme 27 West": 829,
    "Sandanme 28 East": 829,
    "Sandanme 29 East": 830,
    "Sandanme 28 West": 830,
    "Sandanme 29 West": 831,
    "Sandanme 30 East": 831,
    "Sandanme 30 West": 832,
    "Sandanme 31 East": 832,
    "Sandanme 32 East": 833,
    "Sandanme 31 West": 833,
    "Sandanme 33 East": 834,
    "Sandanme 32 West": 834,
    "Sandanme 34 East": 835,
    "Sandanme 33 West": 835,
    "Sandanme 34 West": 836,
    "Sandanme 35 East": 836,
    "Sandanme 36 East": 837,
    "Sandanme 35 West": 837,
    "Sandanme 36 West": 838,
    "Sandanme 37 East": 838,
    "Sandanme 38 East": 839,
    "Sandanme 37 West": 839,
    "Sandanme 39 East": 840,
    "Sandanme 38 West": 840,
    "Sandanme 39 West": 841,
    "Sandanme 40 East": 841,
    "Sandanme 40 West": 842,
    "Sandanme 41 East": 842,
    "Sandanme 42 East": 843,
    "Sandanme 41 West": 843,
    "Sandanme 43 East": 844,
    "Sandanme 42 West": 844,
    "Sandanme 44 East": 845,
    "Sandanme 43 West": 845,
    "Sandanme 45 East": 846,
    "Sandanme 44 West": 846,
    "Sandanme 45 West": 847,
    "Sandanme 46 East": 847,
    "Sandanme 47 East": 848,
    "Sandanme 46 West": 848,
    "Sandanme 48 East": 849,
    "Sandanme 47 West": 849,
    "Sandanme 49 East": 850,
    "Sandanme 48 West": 850,
    "Sandanme 49 West": 851,
    "Sandanme 50 East": 851,
    "Sandanme 50 West": 852,
    "Sandanme 51 East": 852,
    "Sandanme 52 East": 853,
    "Sandanme 51 West": 853,
    "Sandanme 52 West": 854,
    "Sandanme 53 East": 854,
    "Sandanme 53 West": 855,
    "Sandanme 54 East": 855,
    "Sandanme 55 East": 856,
    "Sandanme 54 West": 856,
    "Sandanme 55 West": 857,
    "Sandanme 56 East": 857,
    "Sandanme 56 West": 858,
    "Sandanme 57 East": 858,
    "Sandanme 58 East": 859,
    "Sandanme 57 West": 859,
    "Sandanme 59 East": 860,
    "Sandanme 58 West": 860,
    "Sandanme 59 West": 861,
    "Sandanme 60 East": 861,
    "Sandanme 60 West": 862,
    "Sandanme 61 East": 862,
    "Sandanme 62 East": 863,
    "Sandanme 61 West": 863,
    "Sandanme 63 East": 864,
    "Sandanme 62 West": 864,
    "Sandanme 63 West": 865,
    "Sandanme 64 East": 865,
    "Sandanme 64 West": 866,
    "Sandanme 65 East": 866,
    "Sandanme 66 East": 867,
    "Sandanme 65 West": 867,
    "Sandanme 66 West": 868,
    "Sandanme 67 East": 868,
    "Sandanme 67 West": 869,
    "Sandanme 68 East": 869,
    "Sandanme 69 East": 870,
    "Sandanme 68 West": 870,
    "Sandanme 69 West": 871,
    "Sandanme 70 East": 871,
    "Sandanme 70 West": 872,
    "Sandanme 71 East": 872,
    "Sandanme 72 East": 873,
    "Sandanme 71 West": 873,
    "Sandanme 72 West": 874,
    "Sandanme 73 East": 874,
    "Sandanme 74 East": 875,
    "Sandanme 73 West": 875,
    "Sandanme 74 West": 876,
    "Sandanme 75 East": 876,
    "Sandanme 75 West": 877,
    "Sandanme 76 East": 877,
    "Sandanme 76 West": 878,
    "Sandanme 77 East": 878,
    "Sandanme 77 West": 879,
    "Sandanme 78 East": 879,
    "Sandanme 78 West": 880,
    "Sandanme 79 East": 880,
    "Sandanme 80 East": 881,
    "Sandanme 79 West": 881,
    "Sandanme 80 West": 882,
    "Sandanme 81 East": 882,
    "Sandanme 81 West": 883,
    "Sandanme 82 East": 883,
    "Sandanme 83 East": 884,
    "Sandanme 82 West": 884,
    "Sandanme 84 East": 885,
    "Sandanme 83 West": 885,
    "Sandanme 84 West": 886,
    "Sandanme 85 East": 886,
    "Sandanme 86 East": 887,
    "Sandanme 85 West": 887,
    "Sandanme 87 East": 888,
    "Sandanme 86 West": 888,
    "Sandanme 88 East": 889,
    "Sandanme 87 West": 889,
    "Sandanme 88 West": 890,
    "Sandanme 90": 890,
    "Sandanme 89 East": 890,
    "Sandanme 90 East": 891,
    "Sandanme 89 West": 891,
    "Sandanme 91 East": 892,
    "Sandanme 90 West": 892,
    "Sandanme 91 West": 893,
    "Sandanme 92 East": 893,
    "Sandanme 93 East": 894,
    "Sandanme 92 West": 894,
    "Sandanme 93 West": 895,
    "Sandanme 94 East": 895,
    "Sandanme 94 West": 896,
    "Sandanme 95 East": 896,
    "Sandanme 96 East": 897,
    "Sandanme 95 West": 897,
    "Sandanme 96 West": 898,
    "Sandanme 97 East": 898,
    "Sandanme 98 East": 899,
    "Sandanme 97 West": 899,
    "Sandanme 100": 900,
    "Sandanme 98 West": 900,
    "Sandanme 99 East": 900,
    "Sandanme 100 East": 901,
    "Sandanme 99 West": 901,
    "Sandanme 100 West": 902,
    "Jonidan 1 East": 902,
    "Jonidan 2 East": 903,
    "Jonidan 1 West": 903,
    "Jonidan 3 East": 904,
    "Jonidan 2 West": 904,
    "Jonidan 4 East": 905,
    "Jonidan 3 West": 905,
    "Jonidan 4 West": 906,
    "Jonidan 5 East": 906,
    "Jonidan 5 West": 907,
    "Jonidan 6 East": 907,
    "Jonidan 6 West": 908,
    "Jonidan 7 East": 908,
    "Jonidan 7 West": 909,
    "Jonidan 8 East": 909,
    "Jonidan 9 East": 910,
    "Jonidan 8 West": 910,
    "Jonidan 10 East": 911,
    "Jonidan 9 West": 911,
    "Jonidan 10 West": 912,
    "Jonidan 11 East": 912,
    "Jonidan 11 West": 913,
    "Jonidan 12 East": 913,
    "Jonidan 12 West": 914,
    "Jonidan 13 East": 914,
    "Jonidan 13 West": 915,
    "Jonidan 14 East": 915,
    "Jonidan 15 East": 916,
    "Jonidan 14 West": 916,
    "Jonidan 15 West": 917,
    "Jonidan 16 East": 917,
    "Jonidan 17 East": 918,
    "Jonidan 16 West": 918,
    "Jonidan 18 East": 919,
    "Jonidan 17 West": 919,
    "Jonidan 18 West": 920,
    "Jonidan 19 East": 920,
    "Jonidan 19 West": 921,
    "Jonidan 20 East": 921,
    "Jonidan 21 East": 922,
    "Jonidan 20 West": 922,
    "Jonidan 22 East": 923,
    "Jonidan 21 West": 923,
    "Jonidan 22 West": 924,
    "Jonidan 23 East": 924,
    "Jonidan 24 East": 925,
    "Jonidan 23 West": 925,
    "Jonidan 25 East": 926,
    "Jonidan 24 West": 926,
    "Jonidan 25 West": 927,
    "Jonidan 26 East": 927,
    "Jonidan 26 West": 928,
    "Jonidan 27 East": 928,
    "Jonidan 28 East": 929,
    "Jonidan 27 West": 929,
    "Jonidan 29 East": 930,
    "Jonidan 28 West": 930,
    "Jonidan 30 East": 931,
    "Jonidan 29 West": 931,
    "Jonidan 30 West": 932,
    "Jonidan 31 East": 932,
    "Jonidan 32 East": 933,
    "Jonidan 31 West": 933,
    "Jonidan 33 East": 934,
    "Jonidan 32 West": 934,
    "Jonidan 33 West": 935,
    "Jonidan 34 East": 935,
    "Jonidan 34 West": 936,
    "Jonidan 35 East": 936,
    "Jonidan 36 East": 937,
    "Jonidan 35 West": 937,
    "Jonidan 36 West": 938,
    "Jonidan 37 East": 938,
    "Jonidan 38 East": 939,
    "Jonidan 37 West": 939,
    "Jonidan 39 East": 940,
    "Jonidan 38 West": 940,
    "Jonidan 40 East": 941,
    "Jonidan 39 West": 941,
    "Jonidan 41 East": 942,
    "Jonidan 40 West": 942,
    "Jonidan 41 West": 943,
    "Jonidan 42 East": 943,
    "Jonidan 42 West": 944,
    "Jonidan 43 East": 944,
    "Jonidan 44 East": 945,
    "Jonidan 43 West": 945,
    "Jonidan 44 West": 946,
    "Jonidan 45 East": 946,
    "Jonidan 46 East": 947,
    "Jonidan 45 West": 947,
    "Jonidan 47 East": 948,
    "Jonidan 46 West": 948,
    "Jonidan 48 East": 948,
    "Jonidan 47 West": 949,
    "Jonidan 48 West": 950,
    "Jonidan 49 East": 950,
    "Jonidan 50 East": 951,
    "Jonidan 49 West": 951,
    "Jonidan 50 West": 952,
    "Jonidan 51 East": 952,
    "Jonidan 52 East": 953,
    "Jonidan 51 West": 953,
    "Jonidan 52 West": 954,
    "Jonidan 53 East": 954,
    "Jonidan 54 East": 955,
    "Jonidan 53 West": 955,
    "Jonidan 55 East": 956,
    "Jonidan 54 West": 956,
    "Jonidan 55 West": 957,
    "Jonidan 56 East": 957,
    "Jonidan 56 West": 958,
    "Jonidan 57 East": 958,
    "Jonidan 58 East": 959,
    "Jonidan 57 West": 959,
    "Jonidan 58 West": 960,
    "Jonidan 59 East": 960,
    "Jonidan 59 West": 961,
    "Jonidan 60 East": 961,
    "Jonidan 61 East": 962,
    "Jonidan 60 West": 962,
    "Jonidan 61 West": 963,
    "Jonidan 62 East": 963,
    "Jonidan 62 West": 964,
    "Jonidan 63 East": 964,
    "Jonidan 63 West": 965,
    "Jonidan 64 East": 965,
    "Jonidan 65 East": 966,
    "Jonidan 64 West": 966,
    "Jonidan 65 West": 967,
    "Jonidan 66 East": 967,
    "Jonidan 67 East": 968,
    "Jonidan 66 West": 968,
    "Jonidan 67 West": 969,
    "Jonidan 68 East": 969,
    "Jonidan 69 East": 970,
    "Jonidan 68 West": 970,
    "Jonidan 70 East": 971,
    "Jonidan 69 West": 971,
    "Jonidan 71 East": 972,
    "Jonidan 70 West": 972,
    "Jonidan 72 East": 973,
    "Jonidan 71 West": 973,
    "Jonidan 73 East": 974,
    "Jonidan 72 West": 974,
    "Jonidan 73 West": 975,
    "Jonidan 74 East": 975,
    "Jonidan 74 West": 976,
    "Jonidan 75 East": 976,
    "Jonidan 76 East": 977,
    "Jonidan 75 West": 977,
    "Jonidan 77 East": 978,
    "Jonidan 76 West": 978,
    "Jonidan 77 West": 979,
    "Jonidan 78 East": 979,
    "Jonidan 78 West": 980,
    "Jonidan 79 East": 980,
    "Jonidan 79 West": 981,
    "Jonidan 80 East": 981,
    "Jonidan 81 East": 982,
    "Jonidan 80 West": 982,
    "Jonidan 81 West": 983,
    "Jonidan 82 East": 983,
    "Jonidan 83 East": 984,
    "Jonidan 82 West": 984,
    "Jonidan 83 West": 985,
    "Jonidan 84 East": 985,
    "Jonidan 85 East": 986,
    "Jonidan 84 West": 986,
    "Jonidan 86 East": 987,
    "Jonidan 85 West": 987,
    "Jonidan 86 West": 988,
    "Jonidan 87 East": 988,
    "Jonidan 87 West": 989,
    "Jonidan 88 East": 989,
    "Jonidan 89 East": 990,
    "Jonidan 88 West": 990,
    "Jonidan 90 East": 991,
    "Jonidan 89 West": 991,
    "Jonidan 90 West": 992,
    "Jonidan 91 East": 992,
    "Jonidan 91 West": 993,
    "Jonidan 92 East": 993,
    "Jonidan 92 West": 994,
    "Jonidan 93 East": 994,
    "Jonidan 94 East": 995,
    "Jonidan 93 West": 995,
    "Jonidan 95 East": 996,
    "Jonidan 94 West": 996,
    "Jonidan 95 West": 997,
    "Jonidan 96 East": 997,
    "Jonidan 96 West": 998,
    "Jonidan 97 East": 998,
    "Jonidan 98 East": 999,
    "Jonidan 97 West": 999,
    "Jonidan 98 West": 1000,
    "Jonidan 99 East": 1000,
    "Jonidan 100 East": 1001,
    "Jonidan 99 West": 1001,
    "Jonokuchi 1 East": 1002,
    "Jonidan 100 West": 1002,
    "Jonidan 101 East": 1002,
    "Jonokuchi 1 West": 1003,
    "Jonokuchi 2 East": 1003,
    "Jonidan 102 East": 1003,
    "Jonidan 101 West": 1003,
    "Jonokuchi 3 East": 1004,
    "Jonokuchi 2 West": 1004,
    "Jonidan 102 West": 1004,
    "Jonidan 103 East": 1004,
    "Jonidan 103 West": 1005,
    "Jonidan 104 East": 1005,
    "Jonokuchi 3 West": 1005,
    "Jonokuchi 4 East": 1005,
    "Jonidan 105 East": 1006,
    "Jonokuchi 4 West": 1006,
    "Jonokuchi 5 East": 1006,
    "Jonidan 104 West": 1006,
    "Jonidan 105 West": 1007,
    "Jonokuchi 5 West": 1007,
    "Jonokuchi 6 East": 1007,
    "Jonidan 106 East": 1007,
    "Jonidan 106 West": 1008,
    "Jonokuchi 6 West": 1008,
    "Jonokuchi 7 East": 1008,
    "Jonidan 107 East": 1008,
    "Jonokuchi 7 West": 1009,
    "Jonidan 107 West": 1009,
    "Jonokuchi 8 East": 1009,
    "Jonidan 108 East": 1009,
    "Jonidan 109 East": 1010,
    "Jonokuchi 9 East": 1010,
    "Jonokuchi 8 West": 1010,
    "Jonidan 108 West": 1010,
    "Jonokuchi 9 West": 1011,
    "Jonidan 110 East": 1011,
    "Jonokuchi 10 East": 1011,
    "Jonidan 109 West": 1011,
    "Jonokuchi 10 West": 1012,
    "Jonokuchi 11 East": 1012,
    "Jonidan 111 East": 1012,
    "Jonidan 110 West": 1012,
    "Jonidan 111 West": 1013,
    "Jonokuchi 11 West": 1013,
    "Jonokuchi 12 East": 1013,
    "Jonidan 112 East": 1013,
    "Jonokuchi 12 West": 1014,
    "Jonokuchi 13 East": 1014,
    "Jonidan 113 East": 1014,
    "Jonidan 112 West": 1014,
    "Jonokuchi 14 East": 1015,
    "Jonokuchi 13 West": 1015,
    "Jonidan 114 East": 1015,
    "Jonidan 113 West": 1015,
    "Jonokuchi 15 East": 1016,
    "Jonokuchi 14 West": 1016,
    "Jonidan 114 West": 1016,
    "Jonidan 115 East": 1016,
    "Jonokuchi 15 West": 1017,
    "Jonokuchi 16 East": 1017,
    "Jonidan 116 East": 1017,
    "Jonidan 115 West": 1017,
    "Jonokuchi 17 East": 1018,
    "Jonidan 117 East": 1018,
    "Jonokuchi 16 West": 1018,
    "Jonidan 116 West": 1018,
    "Jonokuchi 18 East": 1019,
    "Jonokuchi 17 West": 1019,
    "Jonidan 117 West": 1019,
    "Jonidan 118 East": 1019,
    "Jonokuchi 18 West": 1020,
    "Jonokuchi 19 East": 1020,
    "Jonidan 119 East": 1020,
    "Jonidan 118 West": 1020,
    "Jonokuchi 19 West": 1021,
    "Jonokuchi 20 East": 1021,
    "Jonidan 120 East": 1021,
    "Jonidan 119 West": 1021,
    "Jonidan 120 West": 1022,
    "Jonokuchi 20 West": 1022,
    "Jonokuchi 21 East": 1022,
    "Jonidan 121 East": 1022,
    "Jonokuchi 22 East": 1023,
    "Jonokuchi 21 West": 1023,
    "Jonidan 121 West": 1023,
    "Jonidan 122 East": 1023,
    "Jonokuchi 23 East": 1024,
    "Jonokuchi 22 West": 1024,
    "Jonidan 122 West": 1024,
    "Jonidan 123 East": 1024,
    "Jonokuchi 24 East": 1025,
    "Jonokuchi 23 West": 1025,
    "Jonidan 123 West": 1025,
    "Jonidan 124 East": 1025,
    "Jonokuchi 25 East": 1026,
    "Jonidan 125 East": 1026,
    "Jonokuchi 24 West": 1026,
    "Jonidan 124 West": 1026,
    "Jonokuchi 25 West": 1027,
    "Jonokuchi 26 East": 1027,
    "Jonidan 125 West": 1027,
    "Jonokuchi 27 East": 1028,
    "Jonidan 127 East": 1028,
    "Jonokuchi 26 West": 1028,
    "Jonidan 126 West": 1028,
    "Jonokuchi 27 West": 1029,
    "Jonokuchi 28 East": 1029,
    "Jonidan 127 West": 1029,
    "Jonidan 128 East": 1029,
    "Jonokuchi 28 West": 1030,
    "Jonokuchi 29 East": 1030,
    "Jonidan 129 East": 1030,
    "Jonidan 128 West": 1030,
    "Jonidan 129 West": 1031,
    "Jonokuchi 29 West": 1031,
    "Jonokuchi 30 East": 1031,
    "Jonidan 130 East": 1031,
    "Jonokuchi 31 East": 1032,
    "Jonokuchi 30 West": 1032,
    "Jonidan 131 East": 1032,
    "Jonidan 130 West": 1032,
    "Jonokuchi 32 East": 1033,
    "Jonokuchi 31 West": 1033,
    "Jonidan 131 West": 1033,
    "Jonidan 132 East": 1033,
    "Jonidan 133 East": 1034,
    "Jonokuchi 32 West": 1034,
    "Jonokuchi 33 East": 1034,
    "Jonidan 132 West": 1034,
    "Jonokuchi 34 East": 1035,
    "Jonidan 134 East": 1035,
    "Jonokuchi 33 West": 1035,
    "Jonidan 134 West": 1036,
    "Jonidan 135 East": 1036,
    "Jonokuchi 35 East": 1036,
    "Jonokuchi 35 West": 1037,
    "Jonokuchi 36 East": 1037,
    "Jonidan 135 West": 1037,
    "Jonokuchi 36 West": 1038,
    "Jonokuchi 37 East": 1038,
    "Jonidan 136 West": 1038,
    "Jonokuchi 38 East": 1039,
    "Jonokuchi 37 West": 1039,
    "Jonidan 137 West": 1039,
    "Jonidan 138 West": 1040,
    "Jonokuchi 38 West": 1040,
    "Jonokuchi 39 East": 1040,
    "Jonidan 139 East": 1040,
    "Jonokuchi 40 East": 1041,
    "Jonokuchi 39 West": 1041,
    "Jonidan 139 West": 1041,
    "Jonokuchi 41 East": 1042,
    "Jonokuchi 40 West": 1042,
    "Jonokuchi 41 West": 1043,
    "Jonidan 143 East": 1044,
    "Jonokuchi 43 East": 1044,
    "Jonokuchi 44 East": 1045,
    "Jonidan 144 East": 1045,
    "Jonidan 144 West": 1046,
    "Jonokuchi 44 West": 1046,
    "Jonidan 146 East": 1047,
    "Jonidan 146 West": 1048,
    "Jonokuchi 46 West": 1048,
    "Jonokuchi 48 East": 1049,
    "Jonokuchi 48 West": 1050,
    "Jonidan 149 East": 1050,
    "Jonokuchi 50 East": 1051,
    "Jonidan 149 West": 1051,
    "Jonidan 150 West": 1052,
    "Jonidan 151 West": 1053,
    "Jonokuchi 51 West": 1053,
    "Jonidan 153 East": 1054,
    "Jonidan 155 East": 1056,
    "Jonokuchi 55 East": 1056,
    "Jonidan 156 East": 1057,
    "Jonidan 157 East": 1058,
    "Jonidan 157 West": 1059,
    "Jonidan 159 East": 1060,
    "Jonidan 159 West": 1061,
    "Jonokuchi 60 East": 1061,
    "Jonidan 161 East": 1062,
    "Jonidan 164 East": 1065,
    "Jonokuchi 65 East": 1066,
    "Jonidan 166 East": 1067,
    "Jonidan 166 West": 1068,
    "Jonidan 167 West": 1069,
    "Jonidan 170 West": 1072,
    "Jonidan 171 East": 1072,
    "Jonidan 172 East": 1073,
    "Jonidan 174 West": 1076,
    "Jonidan 175 West": 1077,
    "Jonidan 177 East": 1078,
    "Jonidan 178 East": 1079,
    "Jonidan 179 East": 1080,
    "Jonidan 178 West": 1080,
    "Jonidan 179 West": 1081,
    "Jonidan 182 West": 1084,
    "Jonidan 185 East": 1086,
    "Jonidan 186 East": 1087,
    "Jonidan 185 West": 1087,
    "Jonidan 197 East": 1098,
    "Mae-zumo": 2000,
    "Banzuke-gai": 3000,
    "": 999999
}

class SumoDivision(Enum):
    Makuuchi = 'Makuuchi'
    Juryo = 'Juryo'
    Makushita = 'Makushita'
    Sandanme = 'Sandanme'
    Jonidan = 'Jonidan'
    Jonokuchi = 'Jonokuchi'
    MaeZumo = 'Mae-zumo'

    UNKNOWN = ''

    def __repr__(self):
        return self.value

    def __str__(self):
        return str(self.value)

    def __contains__(self, val):
        try:
            SumoDivision(val)
        except ValueError:
            return False
        return True

class SumoResult(Enum):
    WIN = 'win'
    LOSS = 'loss'
    ABSENT = 'absent'
    FUSENSHO = 'fusen win'
    FUSENPAI = 'fusen loss'
    UNKNOWN = ''

    def __repr__(self):
        return self.value

    def __str__(self):
        return str(self.value)

    def __contains__(self, val):
        try:
            SumoResult(val)
        except ValueError:
            return False
        return True

@dataclass_json(undefined=Undefined.RAISE)
@dataclass()
class RikishiMeasurement:
    id: str = ''
    bashoId: int = -1
    rikishiId: int = -1
    height: float = 0.0
    weight: float = 0.0

    def __str__(self):
        return f'{self.bashoId}:({self.height},{self.weight})'

    def isValid(self):
        return id != '' and height != 0.0 and weight != 0.0

@dataclass_json(undefined=Undefined.RAISE)
@dataclass()
class RikishiRank:
    id: str = ''
    bashoId: int = -1
    rikishiId: int = -1
    rankValue: int = -1
    rank: str = ''

    def __post_init__(self):
        # Make sure this is always set
        if self.rankValue < 0:
            self.rankValue = _RikishiRankValue[self.rank]
        return

    def __str__(self):
        return f'{self.bashoId}:{self.rank}({self.rankValue})'

    def isValid(self):
        return rankValue > 0


@dataclass_json(undefined=Undefined.RAISE)
@dataclass()
class RikishiShikona:
    id: str = ''
    bashoId: int = -1
    rikishiId: int = -1
    shikonaEn: str = ''
    shikonaJp: str = ''

    def __str__(self):
        return f'{self.bashoId}:{self.shikonaEn}'


@dataclass_json(undefined=Undefined.RAISE)
@dataclass()
class RikishiStats:
    absenceByDivision: dict[SumoDivision, int] = field(default_factory=dict)
    totalBasho: int = field(default=0, metadata=dcjson_config(field_name="basho"))
    bashoByDivision: dict[SumoDivision, int] = field(default_factory=dict)
    lossByDivision: dict[SumoDivision, int] = field(default_factory=dict)
    totalAbsences: int = 0
    totalByDivision: dict[SumoDivision, int] = field(default_factory=dict)
    totalMatches: int = 0
    totalLosses: int = 0
    totalWins: int = 0
    winsByDivision: dict[SumoDivision, int] = field(default_factory=dict)
    yusho: int = 0
    yushoByDivision: dict[SumoDivision, int] = field(default_factory=dict)
    specialPrizes: dict[str, int] = field(default_factory=dict, metadata=dcjson_config(field_name="sansho"))

@dataclass_json(undefined=Undefined.RAISE)
@dataclass()
class Rikishi:
    id: int
    sumodbId: int = -1
    nskId: int = -1
    shikonaEn: str = ''
    shikonaJp: str = ''
    currentRank: str = ''
    currentRankValue: int = -1
    heya: str = ''
    birthDate: datetime = field(default='0001-01-01T00:00:00+00:00', metadata=dcjson_config(decoder=_decode_datetime))
    shusshin: str = ''
    height: float = 0.0
    weight: float = 0.0
    debut: date = field(default='0001-01-01T00:00:00+00:00', metadata=dcjson_config(decoder=_decode_date))
    updatedAt: datetime = field(default='0001-01-01T00:00:00+00:00', metadata=dcjson_config(decoder=_decode_datetime))
    createdAt: datetime = field(default='0001-01-01T00:00:00+00:00', metadata=dcjson_config(decoder=_decode_datetime))
    intai: datetime = field(default='0001-01-01T00:00:00+00:00', metadata=dcjson_config(decoder=_decode_datetime))
    measurementHistory: list[RikishiMeasurement] = field(default_factory=list)
    rankHistory: list[RikishiRank]  = field(default_factory=list)
    shikonaHistory: list[RikishiShikona] = field(default_factory=list)

    def __post_init__(self):
        # always make sure currentRankValue is set
        if self.currentRankValue < 0:
            self.currentRankValue = _RikishiRankValue[self.currentRank]
        return

    def __str__(self):
        s = f'{self.id}: {self.shikonaEn} [{self.heya}]'
        if self.retired():
            s += f' (retired since {self.intai})'
        else:
            s += f', {str(self.currentRank)}'
        s += f', height:{self.height}, weight:{self.weight}'
        if len(self.rankHistory) > 0:
            s += f'\n{self.id}: RankHistory={list(map(str, self.rankHistory))}' 
        if len(self.measurementHistory) > 0:
            s += f'\n{self.id}: MeasurementHistory={list(map(str, self.measurementHistory))}'
        if len(self.shikonaHistory) > 0:
            s += f'\n{self.id}: ShikonaHistory={list(map(str, self.shikonaHistory))}'
        return s

    def name(self):
        return self.shikonaEn

    def retired(self):
        return True if self.intai.timestamp() > 0 else False

    def isValid(self):
        return self.id > 0

@dataclass_json(undefined=Undefined.RAISE)
@dataclass()
class Yusho:
    division: SumoDivision = field(metadata=dcjson_config(field_name="type"))
    rikishiId: int = -1
    shikonaEn: str = ''
    shikonaJp: str = ''

@dataclass_json(undefined=Undefined.RAISE)
@dataclass()
class SpecialPrize:
    name: str = field(metadata=dcjson_config(field_name="type"))
    rikishiId: int = -1
    shikonaEn: str = ''
    shikonaJp: str = ''

@dataclass_json(undefined=Undefined.RAISE)
@dataclass()
class BashoMatch:
    bashoId: date = field(metadata=dcjson_config(decoder=_decode_date))
    division: SumoDivision = SumoDivision.UNKNOWN
    day: int = -1
    matchNo: int = -1
    eastId: int = -1
    eastShikona: str = ''
    westId: int = -1
    westShikona: str = ''
    winnerId: int = -1
    winnerEn: str = ''
    winnerJp: str = ''
    matchId: str = field(default='', metadata=dcjson_config(field_name="id"))
    eastRank: str = ''
    westRank: str = ''
    kimarite: str = ''

    def __post_init__(self):
        if self.matchId == '':
            # matchId format is:
            #   [bashoId (YYYYMM)]-[day]-[matchNo - 1]-[eastId]-[westId]
            self.matchId = f'{BashoIdStr(self.bashoId)}-{self.day}-{self.matchNo - 1}-{self.eastId}-{self.westId}'
        return

    def isValid(self):
        return self.bashoId.year > 1000

    def upcoming(self):
        if self.winnerId <= 0:
            return True
        return False

@dataclass_json(undefined=Undefined.RAISE)
@dataclass()
class RikishiMatchup:
    total: int = 0
    rikishiWins: int = 0
    opponentWins: int = 0
    kimariteLosses: dict[str,int] = field(default_factory=dict)
    kimariteWins: dict[str,int] = field(default_factory=dict)
    matches: list[BashoMatch] = field(default_factory=list)

@dataclass_json(undefined=Undefined.RAISE)
@dataclass()
class Basho:
    bashoDate: date = field(metadata=dcjson_config(field_name="date", decoder=_decode_date))
    startDate: datetime = field(default='0001-01-01T00:00:00+00:00', metadata=dcjson_config(decoder=_decode_datetime))
    endDate: datetime = field(default='0001-01-01T00:00:00+00:00', metadata=dcjson_config(decoder=_decode_datetime))
    yusho: list[Yusho] = field(default_factory=list)
    specialPrizes: list[SpecialPrize] = field(default_factory=list)
    location: str = ''

    def id(self):
        return BashoIdStr(self.bashoDate)

    def isValid(self):
        return self.bashoDate.year > 1000

@dataclass_json(undefined=Undefined.RAISE)
@dataclass()
class BashoTorikumi(Basho):
    torikumi: list[BashoMatch] = field(default_factory=list)
    division: SumoDivision = field(default=SumoDivision.UNKNOWN)
    day: int = field(default=-1)

@dataclass_json(undefined=Undefined.RAISE)
@dataclass()
class BanzukeMatchRecord:
    opponentID: int
    result: SumoResult = SumoResult.UNKNOWN
    kimarite: str = ''
    opponentShikonaEn: str = ''
    opponentShikonaJp: str = ''

@dataclass_json(undefined=Undefined.RAISE)
@dataclass()
class BanzukeRikishi:
    rikishiId: int = field(metadata=dcjson_config(field_name="rikishiID"))
    side: str = ''
    rankValue: int = -1
    rank: str = ''
    wins: int = -1
    losses: int = -1
    absences: int = -1
    record: list[BanzukeMatchRecord] = field(default_factory=list)
    shikonaEn: str = ''
    shikonaJp: str = ''

    def desc(self):
        return f'{self.shikonaEn}({self.rikishiId})'

@dataclass_json(undefined=Undefined.RAISE)
@dataclass()
class Banzuke:
    bashoId: date = field(metadata=dcjson_config(decoder=_decode_date))
    division: SumoDivision = SumoDivision.UNKNOWN
    east: list[BanzukeRikishi] = field(default_factory=list)
    west: list[BanzukeRikishi] = field(default_factory=list)

    def __post_init__(self):
        if not self.east:
            self.east = []
        if not self.west:
            self.west = []

    def __str__(self):
        return f'{BashoIdStr(self.bashoId)}:{self.division}'

    def isValid(self):
        return self.bashoId.year > 1000
