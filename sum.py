from supertracer import SuperTracer

log = open("error_log.txt", "a")
tracer = SuperTracer(files=[log]) # type: ignore
    
def cause_exception():
    return 1 / 0  # This will raise a ZeroDivisionError

cause_exception()