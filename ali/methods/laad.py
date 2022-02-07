import pandas as pd
import pandasql as ps


def laad(dataset, params):
    import sys
    info=dataset['info']
    hr=dataset['hr'].copy()
    step=dataset['step'].copy()
    # sys.path.append("..")
    from .LAAD_orig.scripts import laad_covid19 as laad_covid19


    
    if info["device"] == 'AppleWatch':
        import pandasql as ps
        sqlcode = '''
                select hr.datetime,step.steps
                from hr,step
                where hr.datetime >= step.start_datetime and hr.datetime <= step.end_datetime
            '''
        step2 = ps.sqldf(sqlcode, locals())
        step2['datetime'] = pd.to_datetime(step2['datetime'])
        step2 = step2.set_index('datetime')
        step=step2['steps']
    
    dataset={'hr':hr, 'step':step, 'info':info}
    alarms= laad_covid19.run(dataset, params)
    alarms.loc[alarms['alarm']<=4,'alarm']=1
    alarms.loc[alarms['alarm']>4,'alarm']=2
    return alarms