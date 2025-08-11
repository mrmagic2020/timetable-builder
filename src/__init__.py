from dataclasses import dataclass

@dataclass
class Timetable:
    id : str
    classes : list[list[list[str]]]
    #days #periods #list of classes by classid
