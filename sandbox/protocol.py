class Responses:
    OKAY = b"\x00"
    ERROR = b"\x01"
    RESULTS = b"\x02"


class Commands:
    SETUP = b"\x03"
    PROCESS = b"\x04"
    STOP = b"\xFF"


def Okay():
    return (Responses.OKAY, "")


def Error(msg):
    return (Responses.ERROR, msg)


def Results(results):
    return (Responses.RESULTS, results)


def Setup(config):
    return (Commands.SETUP, config)


def Process(config):
    return (Commands.PROCESS, config)


def Stop():
    return (Commands.STOP, "")
