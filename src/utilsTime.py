def formatDuration(seconds):
    if not seconds:
        return 0

    h = seconds // 3600
    s = seconds % 3600
    m = s // 60
    s = s % 60

    if s >= 30:
        if m == 59:
            h += 1
            m = 0
        else:
            m += 1

    if h > 0:
        dur = f"{h}\N{DEGREE SIGN} {m}'"
    else:
        dur = f"{m}'"

    return dur
