#!/usr/bin/env python3

import httpx
import json
import re
from datetime import datetime, date
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, Undefined, config as dcjson_config

def decode_datetime(datestr):
    """ custom decoder for older python versions that don't like the 'Z' in for iso date format """
    #print(f'INPUT:{datestr}')
    return datetime.fromisoformat(datestr.replace('Z', '+00:00'))


def decode_date(datestr):
    """ custom decoder for older python versions that only like YYYY-MM-DD """
    #print(f'INPUT:{datestr}')
    if len(datestr) < 8:
        datestr = datestr + '01'
    m = re.match(r'(\d{4})(\d{2})(\d{2})', datestr)
    return date.fromisoformat(f'{m.group(1)}-{m.group(2)}-{m.group(3)}')



@dataclass_json(undefined=Undefined.RAISE)
@dataclass(frozen=True)
class RikishiMeasurement:
    id: str
    bashoId: int
    rikishiId: int
    height: int
    weight: int

    def __str__(self):
        return f'{self.bashoId}:({self.height},{self.weight})'


@dataclass_json(undefined=Undefined.RAISE)
@dataclass(frozen=True)
class RikishiRank:
    id: str
    bashoId: int
    rikishiId: int
    rankValue: int
    rank: str

    def __str__(self):
        return f'{self.bashoId}:{self.rank}({self.rankValue})'


@dataclass_json(undefined=Undefined.RAISE)
@dataclass(frozen=True)
class RikishiShikona:
    id: str
    bashoId: int
    rikishiId: int
    shikonaEn: str
    shikonaJp: str

    def __str__(self):
        return f'{self.bashoId}:{self.shikonaEn}'


@dataclass_json(undefined=Undefined.RAISE)
@dataclass(frozen=True)
class RikishiStats:
    absenceByDivision: dict[str, int]
    basho: int
    bashoByDivision: dict[str, int]
    lossByDivision: dict[str, int]
    totalAbsences: int
    totalByDivision: dict[str, int]
    totalMatches: int
    totalLosses: int
    totalWins: int
    winsByDivision: dict[str, int]
    yusho: int
    yushoByDivision: dict[str, int]
    specialPrizes: dict[str, int] = field(metadata=dcjson_config(field_name="sansho"))


@dataclass_json(undefined=Undefined.RAISE)
@dataclass(frozen=True)
class Rikishi:
    id: int
    sumodbId: int
    nskId: int
    shikonaEn: str = ''
    shikonaJp: str = ''
    currentRank: str = ''
    heya: str = ''
    birthDate: datetime = field(default='0001-01-01T00:00:00+00:00', metadata=dcjson_config(decoder=decode_datetime))
    shusshin: str = ''
    height: float = 0.0
    weight: float = 0.0
    debut: date = field(default='0001-01-01T00:00:00+00:00', metadata=dcjson_config(decoder=decode_date))
    updatedAt: datetime = field(default='0001-01-01T00:00:00+00:00', metadata=dcjson_config(decoder=decode_datetime))
    createdAt: datetime = field(default='0001-01-01T00:00:00+00:00', metadata=dcjson_config(decoder=decode_datetime))
    intai: datetime = field(default='0001-01-01T00:00:00+00:00', metadata=dcjson_config(decoder=decode_datetime))
    measurementHistory: list[RikishiMeasurement] = field(default_factory=list)
    rankHistory: list[RikishiRank]  = field(default_factory=list)
    shikonaHistory: list[RikishiShikona] = field(default_factory=list)

    # need to make a default constructor, and a custom set() function
    #stats: RikishiStats = RikishiStats()

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

@dataclass_json(undefined=Undefined.RAISE)
@dataclass(frozen=True)
class Yusho:
    division: str = field(metadata=dcjson_config(field_name="type"))
    rikishiId: int
    shikonaEn: str
    shikonaJp: str

@dataclass_json(undefined=Undefined.RAISE)
@dataclass(frozen=True)
class SpecialPrize:
    name: str = field(metadata=dcjson_config(field_name="type"))
    rikishiId: int
    shikonaEn: str
    shikonaJp: str

@dataclass_json(undefined=Undefined.RAISE)
@dataclass(frozen=True)
class Basho:
    bashoDate: date = field(metadata=dcjson_config(field_name="date", decoder=decode_date))
    startDate: datetime = field(default='0001-01-01T00:00:00+00:00', metadata=dcjson_config(decoder=decode_datetime))
    endDate: datetime = field(default='0001-01-01T00:00:00+00:00', metadata=dcjson_config(decoder=decode_datetime))
    yusho: list[Yusho] = field(default_factory=list)
    specialPrizes: list[SpecialPrize] = field(default_factory=list)

@dataclass_json(undefined=Undefined.RAISE)
@dataclass(frozen=True)
class BashoMatch:
    bashoId: date = field(metadata=dcjson_config(decoder=decode_date))
    division: str
    day: int
    matchNo: int
    eastId: int
    eastShikona: str
    westId: int
    westShikona: str
    winnerId: int
    winnerEn: str
    winnerJp: str
    eastRank: str = ''
    westRank: str = ''
    kimarite: str = ''

class SumoAPI:
    """ Object wrapper around sumo-api.com API calls """

    def __init__(self):
        self.apiurl = "https://sumo-api.com/api"

    def rikishis(self, limit = 1000, skip = 0, retired = False, **query):
        """ GET /rikishis """
        url = self.apiurl + "/rikishis"
        # shikonaEn: search for a rikishi by English shikona
        # heya: search by heya, full name in English, e.g. Isegahama
        # sumodbId: search by sumoDB ID, e.g. 11927 = Terunofuji
        # nskId: search by official NSK ID, e.g. 3321 = Terunofuji
        # intai: (retirement date) if missing, only active rikishi are searched. If true, retired rikishi are also searched.
        # measurements: if true, the changes in a rikishi's measurements over time will be included in the response
        # ranks: if true, the changes in a rikishi's ranks over time will be included in the response
        # shikonas: if true, the changes in a rikishi's shikonas over time will be included in the response
        # limit: how many results to return, 1000 hard limit
        # skip: skip over the number of results specified
        validparams = ['shikonaEn', 'heya', 'sumodbId', 'nskId', 'measurements', 'ranks', 'shikonas']
        params = { 'limit': limit, 'skip': skip, 'intai': 'true' if retired else 'false' }
        for name, val in query.items():
            if name in validparams:
                params[name] = val
            else:
                raise Exception('invalid parameter:', name)
        r = httpx.get(url, params=params)
        j = r.json()
        if j["total"] < 1:
            raise Execption("can't find Rikishi with given query parameters")
        # print(j["records"])
        return list(map(Rikishi.from_dict, j["records"]))

    def rikishi(self, rikishiId, measurements = False, ranks = False, shikonas = False):
        """ GET /api/rikishi/:rikishiId """
        url = self.apiurl + f'/rikishi/{rikishiId}'
        # measurements: if true, the changes in a rikishi's measurements over time will be included in the response
        # ranks: if true, the changes in a rikishi's ranks over time will be included in the response
        # shikonas: if true, the changes in a rikishi's shikonas over time will be included in the response
        params = {}
        if measurements:
            params['measurements']='true'
        if ranks:
            params['ranks']='true'
        if shikonas:
            params['shikonas']='true'
        r = httpx.get(url, params=params)
        j = r.json()
        # print(j)
        return Rikishi.from_dict(j)

    def rikishi_stats(self, rikishiId):
        """ GET /api/rikishi/:rikishiId/stats """
        url = self.apiurl + f'/rikishi/{rikishiId}/stats'
        r = httpx.get(url)
        j = r.json()
        # print(j)
        return RikishiStats.from_dict(j)

    def rikishi_matches(self, rikishiId, bashoId = None, limit = 0, skip = 0):
        """ GET /api/rikishi/:rikishiId/matches """
        url = self.apiurl + f'/rikishi/{rikishiId}/matches'
        params={ 'limit': limit, 'skip': skip }
        if bashoId:
            params["bashoId"] = bashoId
        r = httpx.get(url, params=params)
        j = r.json()
        # print(j)
        if j["total"] < 1:
            return []
        return list(map(BashoMatch.from_dict, j["records"]))

    def basho(self, bashoId):
        """ GET /api/basho/:bashoId """
        url = self.apiurl + f'/basho/{bashoId}'
        r = httpx.get(url)
        j = r.json()
        # print(j)
        return Basho.from_dict(j)

#GET /api/rikishi/:rikishiId/matches
#GET /api/rikishi/:rikishiId/matches/:opponentId

#GET /api/basho/:bashoId/banzuke/:division
#GET /api/basho/:bashoId/torikumi/:division/:day

#GET /api/kimarite
#GET /api/kimarite/:kimarite

#GET /api/measurements
#GET /api/ranks
#GET /api/shikonas



def PrintRikishi(rinput):
    # print(rinput)
    if hasattr(rinput, '__len__'):
        for r in rinput:
            print(r)
    else:
        print(rinput)


sumo = SumoAPI()

rikishi = sumo.rikishis(limit=2, skip=23)
PrintRikishi(rikishi)
print('\n')

rikishi = sumo.rikishis(limit=2, skip=1111, retired=True)
PrintRikishi(rikishi)
print('\n')

rikishi = sumo.rikishis(limit=2, shikonaEn='Terunofuji')
PrintRikishi(rikishi)
print('\n')

rikishi = sumo.rikishis(limit=2, shikonaEn='Shishi', shikonas='true', measurements='true', ranks='true')
PrintRikishi(rikishi)
print('\n')

rikishi = sumo.rikishi(86)
PrintRikishi(rikishi)
print('\n')

rikishi= sumo.rikishi(86, measurements=True)
PrintRikishi(rikishi)
print('\n')

rikishi= sumo.rikishi(86, ranks=True)
PrintRikishi(rikishi)
print('\n')

rikishi= sumo.rikishi(86, shikonas=True)
PrintRikishi(rikishi)
print('\n')

stats = sumo.rikishi_stats(45)
print(stats)
print('\n')

matches = sumo.rikishi_matches(45, limit=3)
print(matches)
print('\n')

basho = sumo.basho(202411)
print(basho)
print('\n')
