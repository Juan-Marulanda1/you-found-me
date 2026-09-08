from enum import StrEnum


class AnnouncementType(StrEnum):
    LOST = "LOST"
    FOUND = "FOUND"


class AnnouncementStatus(StrEnum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
