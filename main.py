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
database.create('D:/Python/sqpaint/test_base.sqlite', 'my_project', 100, 100)