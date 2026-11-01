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
# project = database.create('D:/Python/sqpaint/test_base.sqlite', 'my_project', 100, 100)
project = database.load('D:/Python/sqpaint/test_base.sqlite')
database.save(project)

print(project)