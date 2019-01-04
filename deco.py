#!/usr/bin/python
# name: deco.py

from toms_lib import get_date
from toms_lib import update_file
from toms_lib import logging_decorator
logfile = "testlog.txt"
tracelevel = 2


@logging_decorator(tracelevel,logfile)
def myfunc(myarg1, myarg2):

    datestr = get_date()
    update_file ("INFO: log entry made during function myfunc execution at: %s\n" % (datestr),logfile)

    return "return values %s %s" % (myarg1, myarg2)

r = myfunc('asdf','qweqwr')
print (r)
