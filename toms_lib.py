def get_date(): # return current date and time
        from datetime import datetime
        time = datetime.now()
        return "%02d-%02d-%04d_%02d%02d%02d" % (time.day, time.month, time.year, time.hour, time.minute, time.second)

def update_file(message,filename): # append filename with message
    with open(filename,'a') as f:
        f.write(message)


# decorator function
# parameter list (in order):
# trace_level = the level of debug information to be logged (0 = none)
# log_file = the filename (including path) to where log entries get written

def logging_decorator (trace_level,log_file):
    def real_decorator(f):

        from functools import wraps
        from datetime import datetime

        @wraps(f)
        def wrapped(*args, **kwargs):

            if trace_level > 0:
                datestr = get_date()
                update_file ("INFO: trace_level = %s, log entry made before function %s was called at: %s\n" % (str(trace_level),f.__name__,datestr),log_file)

            if trace_level > 1:
                t1 = datetime.now()

            r = f(*args, **kwargs)      # call the original function

            if trace_level > 1:
                t2 = datetime.now()
                elapsed_time = str((t2 - t1).total_seconds())
                update_file ("INFO: trace_level = %s, the time taken to execute function %s was %s seconds\n" % (str(trace_level),f.__name__,elapsed_time),log_file)

		arg_string = ""
		for arg in args:
			arg_string = arg_string + arg + " "

                update_file ("INFO: %d arguments were passed to function %s: %s \n" % (len(args),f.__name__,arg_string),log_file)

            if trace_level > 0:
                datestr = get_date()
                update_file ("INFO: trace_level = %s, log entry made after function %s was called at: %s\n" % (str(trace_level),f.__name__,datestr),log_file)

            return r
        return wrapped
    return real_decorator




