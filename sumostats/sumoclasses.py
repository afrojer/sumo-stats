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
    if len(datestr) < 8:
        datestr = datestr + '01'
    m = re.match(r'(\d{4})(\d{2})(\d{2})', datestr)
    return date.fromisoformat(f'{m.group(1)}-{m.group(2)}-{m.group(3)}')


class SumoDivision(Enum):
    Makuuchi = 'Makuuchi'
    Juryo = 'Juryo'
    Makushita = 'Makushita'
    Sandanme = 'Sandanme'
    Jonidan = 'Jonidan'
    Jonokuchi = 'Jonokuchi'

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
@dataclass()
class RikishiStats:
    absenceByDivision: dict[SumoDivision, int] = field(default_factory=dict)
    basho: int = -1
    bashoByDivision: dict[SumoDivision, int] = field(default_factory=dict)
    lossByDivision: dict[SumoDivision, int] = field(default_factory=dict)
    totalAbsences: int = -1
    totalByDivision: dict[SumoDivision, int] = field(default_factory=dict)
    totalMatches: int = -1
    totalLosses: int = -1
    totalWins: int = -1
    winsByDivision: dict[SumoDivision, int] = field(default_factory=dict)
    yusho: int = -1
    yushoByDivision: dict[SumoDivision, int] = field(default_factory=dict)
    specialPrizes: dict[str, int] = field(default_factory=dict, metadata=dcjson_config(field_name="sansho"))

@dataclass_json(undefined=Undefined.RAISE)
@dataclass()
class Rikishi:
    id: int
    sumodbId: int
    nskId: int
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

    stats: RikishiStats = RikishiStats()

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
    division: SumoDivision = field(metadata=dcjson_config(field_name="type"))
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
class BashoMatch:
    bashoId: date = field(metadata=dcjson_config(decoder=_decode_date))
    division: SumoDivision
    day: int
    matchNo: int
    eastId: int
    eastShikona: str
    westId: int
    westShikona: str
    winnerId: int
    winnerEn: str
    winnerJp: str
    matchId: str = field(default='', metadata=dcjson_config(field_name="id"))
    eastRank: str = ''
    westRank: str = ''
    kimarite: str = ''

@dataclass_json(undefined=Undefined.RAISE)
@dataclass(frozen=True)
class Basho:
    bashoDate: date = field(metadata=dcjson_config(field_name="date", decoder=_decode_date))
    startDate: datetime = field(default='0001-01-01T00:00:00+00:00', metadata=dcjson_config(decoder=_decode_datetime))
    endDate: datetime = field(default='0001-01-01T00:00:00+00:00', metadata=dcjson_config(decoder=_decode_datetime))
    yusho: list[Yusho] = field(default_factory=list)
    specialPrizes: list[SpecialPrize] = field(default_factory=list)

@dataclass_json(undefined=Undefined.RAISE)
@dataclass(frozen=True)
class BashoTorikumi(Basho):
    torikumi: list[BashoMatch] = field(default_factory=list)

@dataclass_json(undefined=Undefined.RAISE)
@dataclass(frozen=True)
class BanzukeMatchRecord:
    opponentID: int
    opponentShikonaEn: str
    opponentShikonaJp: str
    result: SumoResult
    kimarite: str

@dataclass_json(undefined=Undefined.RAISE)
@dataclass(frozen=True)
class BanzukeRikishi:
    rikishiId: int = field(metadata=dcjson_config(field_name="rikishiID"))
    shikonaEn: str
    shikonaJp: str
    side: str
    rankValue: int
    rank: str
    wins: int
    losses: int
    absences: int
    record: list[BanzukeMatchRecord]

@dataclass_json(undefined=Undefined.RAISE)
@dataclass(frozen=True)
class Banzuke:
    bashoId: date = field(metadata=dcjson_config(decoder=_decode_date))
    division: SumoDivision
    east: list[BanzukeRikishi]
    west: list[BanzukeRikishi]

