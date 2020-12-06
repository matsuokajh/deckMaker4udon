from dataclasses import dataclass
import pathlib 

@dataclass
class CardImg:
    path: pathlib.Path
    f_hash: str
    def __str__(self):
        s = str(self.path)
        return s


# class Card:
#     def __init__(self, face, back = None, num = 1):
#         self.face = face
#         self.back = back
#         self.num = num

@dataclass
class Card:
    id:int
    face:CardImg
    back:CardImg

class dCard:
    def __init__(self,id:int, cb, face, back, num):
        self.id = id
        self.cb = cb
        self.face = face
        self.back = back
        self.num = num