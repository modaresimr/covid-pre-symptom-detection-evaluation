import pandas as pd
def rhrad(dataset,params):
    info=dataset['info']
    hr=dataset['hr']
    step=dataset['step']
    
    import sys
    # sys.path.append("..")
    
    if info["device"] == 'AppleWatch':
        # step_n = pd.DataFrame(columns=['steps'])
    #         print(step)
        all=[]
        for k,row in step.iterrows():
            newRange=pd.date_range(row['start_datetime'].floor('1T'),row['end_datetime'].floor('1T'),freq='1T')
            a=pd.DataFrame(index=newRange)
            a['steps']=row['steps']/len(newRange)
            all.append(a)

        step=pd.concat(all)
    
    if params['mode'] == 'v6':
        from .rhrad_orig.scripts import rhrad_online_24hr_alerts_v6 as rhrad
    else:
        from .rhrad_orig.scripts import rhrad_online_24hr_alerts_v7 as rhrad

    res = rhrad.run(hr, step, info, outliers_rate=params['outliers_fraction'])
    res = res.set_index('datetime')

    res.loc[res['alert_type'] == 'YELLOW'] = 1
    res.loc[res['alert_type'] == 'RED'] = 2
    res.loc[res['alert_type'] == 'GREEN'] = 0

    res = res.rename(columns={"alert_type": "alarm"})
    if res.shape[0]:
        res.index = res.index.floor('1D')

    return res

    
