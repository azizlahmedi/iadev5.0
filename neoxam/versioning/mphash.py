#-*- coding: utf-8 -*-

def mphash(*args):
    """returns the vms six letter hashcode for any suite of names.

    >>> mphash('portefeuille', 'menu.general.unix')
    'k4qsbp'

    >>> mphash(['portefeuille', 'menu.general.unix'])
    'k4qsbp'
    """
    try:
        head,tail=args[0],args[1:]
    except Exception as e:
        print(e)
        raise ValueError
    if not tail:
        if isinstance(head,list):
            head,tail = head[0],head[1:]
    seed = 0
    while 1:
        if not tail:
            return magnum_short_name(head, seed)
        else:
            old_seed = seed
            seed = magnum_short_id(head, seed)
            head,tail = tail[0],tail[1:]

def magnum_short_id(longname,  seed):
    return cname(chash(longname, seed))

def magnum_short_name(longname, seed):
    id_ = magnum_short_id(longname, seed)
    return rad2asc(id_, "______").lower()

def cname(wd):
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    val = abs(wd)
    s = [' ' for i in range(6)]
    for j in range(5, -1, -1):
        s[j] = chars[val % 36]
        val = abs(chash(chars, val))
    return asc2rad("".join(s))

def chash(s, startval):
    num = startval
    for j in range(len(s), 0, -1):
        c = ord(s[-j].upper())
        num = (((num >> 29) & 7) + num * 8 + c + j) & 0xffffffff
        if num & (1 << 31):
            num = num - (1 << 32)
        else:
            num = num & (0xffffffff >> 1)
    return num

rad50 = " ABCDEFGHIJKLMNOPQRSTUVWXYZ$.%0123456789"
rad50lower = " ABCDEFGHIJKLMNOPQRSTUVWXYZ$.%0123456789"

def rad2asc(rad, s):
    tmp = 0
    s = list(s)
    for i in range(len(s)):
        if not i % 3:
            tmp = rad & 0xffff
            rad >>= 16
    
        if i % 3 == 0:
            s[i] = rad50[(tmp // (40 * 40)) % 40]
        elif i % 3 == 1:
            s[i] = rad50[(tmp // 40) % 40]
        elif i % 3 == 2:
            s[i] = rad50[tmp % 40]
    return "".join(s)

def asc2rad(s):
    res = 0
    tmp = 0
    s = s[:6]
    s += '      '[len(s):6]
    s = list(s.upper())
    for i in range(0, 6):
        p = rad50.find(s[i])
        if p == -1:
            s[i] = 29
        else:
            s[i] = p

        tmp = (tmp * 40 + s[i]) & 0xffffffff
        if (i % 3) == 2:
            res |= (tmp << (i // 3) * 16) & 0xffffffff
            tmp = 0
    return res
