from enum import Enum

class AnnouncementType(str, Enum):
    LOST = "LOST"
    FOUND = "FOUND"
    
class AnnouncementStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"