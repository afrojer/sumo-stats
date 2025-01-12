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

class SumoDivision(Enum):
    Makuuchi = 'Makuuchi'
    Juryo = 'Juryo'
    Makushita = 'Makushita'
    Sandanme = 'Sandanme'
    Jonidan = 'Jonidan'
    Jonokuchi = 'Jonokuchi'
    MaeZumo = 'Mae-zumo'

    UNKNOWN = 'Unknown'

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


@dataclass_json(undefined=Undefined.RAISE)
@dataclass()
class RikishiRank:
    id: str = ''
    bashoId: int = -1
    rikishiId: int = -1
    rankValue: int = -1
    rank: str = ''

    def __str__(self):
        return f'{self.bashoId}:{self.rank}({self.rankValue})'


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
    division: SumoDivision
    east: list[BanzukeRikishi]
    west: list[BanzukeRikishi]

    def __str__(self):
        return f'{BashoIdStr(self.bashoId)}:{self.division}'
