from enum import Enum



class PageType(str, Enum):
    CERTIFICATION = "certification"
    LEARNING_PATH = "learning_path"
    MODULE = "module"
    UNIT = "unit"
