
def formatDuration(seconds):
    h = seconds // 3600
    s = seconds - h * 3600
    m = s // 60
    s = s - m * 60

    if s > 30:
        m += 1

    if h > 0:
        dur = f"{h}\N{DEGREE SIGN}{m}'"
    else:
        dur = f"{m}'"

    return dur
