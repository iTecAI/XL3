def parse(body):
    tostr = body.decode('utf-8')
    parts = tostr.split('&')
    ret = {}
    for p in parts:
        ret[p.split('=',1)[0]] = p.split('=',1)[1]
    return ret