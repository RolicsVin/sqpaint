'''
============================================

                 SQPaint
     Автор: Овечин Ратмир Михайлович

  Растровый редактор, основанный на sqlite

============================================

Это главный модуль, запускающий программу.

'''
from core.database import *

database = ProjectDatabase()
project = database.load('D:/Python/sqpaint/test_base.sqlite')

print(project)