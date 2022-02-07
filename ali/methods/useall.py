
def usingAll(allAlarms):
    alarms=allAlarms.clip(lower=0)
    targets = ['if', 'nightsignal', 'CuSum']
    for c in targets:
        if c not in allAlarms.columns:
            return

    su = alarms[targets].sum(axis=1)
    alarms['alarm'] = (su >= len(targets))*1+(su >= len(targets)*1.5)*1
    return alarms[['alarm']]

