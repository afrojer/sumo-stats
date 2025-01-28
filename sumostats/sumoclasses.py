#!/usr/bin/env python3

import json
import re
from enum import Enum
from datetime import datetime, date
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, Undefined, config as dcjson_config
from .sumoclassdata import _RikishiRankValue

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

    def __hash__(self):
        return hash(str(self.value))

    # compare divisions
    def __eq__(self, other):
        try:
            return self.value == other.value
        except:
            pass
        return NotImplemented
    def __ne__(self, other):
        try:
            return self.value != other.value
        except:
            pass
        return NotImplemented
    def __lt__(self, other):
        try:
            o = SumoDivision(str(other.value))
            if o == SumoDivision.Makuuchi:
                if self.value == SumoDivision.Makuuchi:
                    return False
                else:
                    return True
            elif o == SumoDivision.Juryo:
                if self.value == SumoDivision.Makuuchi or \
                        self.value == SumoDivision.Juryo:
                    return False
                elif self.value == SumoDivision.Makushita or \
                     self.value == SumoDivision.Sandanme or \
                     self.value == SumoDivision.Jonidan or \
                     self.value == SumoDivision.Jonokuchi or \
                     self.value == SumoDivision.MaeZumo:
                    return True
                else:
                    return True
            elif o == SumoDivision.Makushita:
                if self.value == SumoDivision.Makuuchi or \
                        self.value == SumoDivision.Juryo or \
                        self.value == SumoDivision.Makushita:
                    return False
                elif self.value == SumoDivision.Sandanme or \
                     self.value == SumoDivision.Jonidan or \
                     self.value == SumoDivision.Jonokuchi or \
                     self.value == SumoDivision.MaeZumo:
                    return True
                else:
                    return True
            elif o == SumoDivision.Sandanme:
                if self.value == SumoDivision.Makuuchi or \
                        self.value == SumoDivision.Juryo or \
                        self.value == SumoDivision.Makushita or \
                        self.value == SumoDivision.Sandanme:
                    return False
                elif self.value == SumoDivision.Jonidan or \
                     self.value == SumoDivision.Jonokuchi or \
                     self.value == SumoDivision.MaeZumo:
                    return True
                else:
                    return True
            elif o == SumoDivision.Jonidan:
                if self.value == SumoDivision.Makuuchi or \
                        self.value == SumoDivision.Juryo or \
                        self.value == SumoDivision.Makushita or \
                        self.value == SumoDivision.Sandanme or \
                        self.value == SumoDivision.Jonidan:
                    return False
                elif self.value == SumoDivision.Jonokuchi or \
                     self.value == SumoDivision.MaeZumo:
                    return True
                else:
                    return True
            elif o == SumoDivision.Jonokuchi:
                if self.value == SumoDivision.Makuuchi or \
                        self.value == SumoDivision.Juryo or \
                        self.value == SumoDivision.Makushita or \
                        self.value == SumoDivision.Sandanme or \
                        self.value == SumoDivision.Jonidan or \
                        self.value == SumoDivision.Jonokuchi:
                    return False
                elif self.value == SumoDivision.MaeZumo:
                    return True
                else:
                    return True
            else:
                return False
        except:
            pass
        return NotImplemented
    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)
    def __gt__(self, other):
        return not self.__lt(other)
    def __ge__(self, other):
        return self.__gt__(other) or self.__eq__(other)

class SumoResult(Enum):
    WIN = 'win'
    LOSS = 'loss'
    ABSENT = 'absent'
    FUSENSHO = 'fusen win'
    FUSENPAI = 'fusen loss'
    FUSEN = 'fusen'

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
    # TODO: this should be a date object I think
    bashoId: int = -1
    rikishiId: int = -1
    height: float = 0.0
    weight: float = 0.0
    bmi: float = 0.0

    def __post_init__(self):
        # BMI = weight (kg) / (height (m))^2
        if self.height > 0.0:
            self.bmi = self.weight / ((self.height/100.0) * (self.height/100.0))

    def __str__(self):
        return f'{self.bashoId}:({self.height},{self.weight})'

    def isValid(self):
        return id != '' and height != 0.0 and weight != 0.0

@dataclass_json(undefined=Undefined.RAISE)
@dataclass()
class RikishiRank:
    id: str = ''
    bashoId: date = field(default=date(1,1,1), metadata=dcjson_config(decoder=_decode_date))
    rikishiId: int = -1
    rankValue: int = -1
    rank: str = ''

    def RankValue(rankStr):
        if rankStr in _RikishiRankValue:
            return _RikishiRankValue[rankStr]
        return _RikishiRankValue['']

    def __post_init__(self):
        # Make sure this is always set
        if self.rankValue < 0:
            self.rankValue = RankValue(self.rank)
        return

    def __str__(self):
        return f'{BashoIdStr(self.bashoId)}:{self.rank}({self.rankValue})'

    def isValid(self):
        return rankValue > 0

    def __eq__(self, other):
        return self.rankValue == other.rankValue
    def __ne__(self, other):
        return self.rankValue != other.rankValue
    def __lt__(self, other):
        return self.rankValue < other.rankValue
    def __le__(self, other):
        return self.rankValue <= other.rankValue
    def __gt__(self, other):
        return self.rankValue > other.rankValue
    def __ge__(self, other):
        return self.rankValue >= other.rankValue


@dataclass_json(undefined=Undefined.RAISE)
@dataclass()
class RikishiShikona:
    id: str = ''
    bashoId: date = field(default=date(1,1,1), metadata=dcjson_config(decoder=_decode_date))
    rikishiId: int = -1
    shikonaEn: str = ''
    shikonaJp: str = ''

    def __str__(self):
        return f'{BashoIdStr(self.bashoId)}:{self.shikonaEn}'


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
    birthDate: datetime = field(default=datetime(1,1,1), metadata=dcjson_config(decoder=_decode_datetime))
    shusshin: str = ''
    height: float = 0.0
    weight: float = 0.0
    bmi: float = 0.0
    debut: date = field(default=date(1,1,1), metadata=dcjson_config(decoder=_decode_date))
    updatedAt: datetime = field(default=datetime(1,1,1), metadata=dcjson_config(decoder=_decode_datetime))
    createdAt: datetime = field(default=datetime(1,1,1), metadata=dcjson_config(decoder=_decode_datetime))
    intai: datetime = field(default=datetime(1,1,1), metadata=dcjson_config(decoder=_decode_datetime))
    measurementHistory: list[RikishiMeasurement] = field(default_factory=list)
    rankHistory: list[RikishiRank]  = field(default_factory=list)
    shikonaHistory: list[RikishiShikona] = field(default_factory=list)

    def __post_init__(self):
        # always make sure currentRankValue is set
        if self.currentRankValue < 0:
            if self.currentRank in _RikishiRankValue:
                self.currentRankValue = _RikishiRankValue[self.currentRank]
        if self.bmi == 0.0 and self.height > 0.0:
            self.bmi = self.weight / ((self.height/100.0) * (self.height/100.0))
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

    def age(self, inBasho:date = None) -> int:
        """
        return rikishi age in days
        """
        if self.birthDate == datetime(1,1,1):
            return 0
        # valid birthday
        _bday = self.birthDate.date()
        if inBasho:
            return (inBasho - _bday).days
        return (date.today() - _bday).days

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
    bashoId: date = field(default=date(1,1,1), metadata=dcjson_config(decoder=_decode_date))
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
    bashoDate: date = field(default=date(1,1,1), metadata=dcjson_config(field_name="date", decoder=_decode_date))
    startDate: datetime = field(default=datetime(1,1,1), metadata=dcjson_config(decoder=_decode_datetime))
    endDate: datetime = field(default=datetime(1,1,1), metadata=dcjson_config(decoder=_decode_datetime))
    yusho: list[Yusho] = field(default_factory=list)
    specialPrizes: list[SpecialPrize] = field(default_factory=list)
    location: str = ''

    def id_str(self):
        return BashoIdStr(self.bashoDate)

    def date(self):
        return self.bashoDate

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
    opponentID: int = -1
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
    bashoId: date = field(default=date(1,1,1), metadata=dcjson_config(decoder=_decode_date))
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
