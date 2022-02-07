import pandas as pd
def alisignal(dataset,params):
    rhr=dataset['rhr']
    seg=params['seg']
    # display(rhr)
    rhr24 = rhr.resample('1D').mean()
    # display(rhr24)
    rhr24median = rhr24.expanding().median().astype(int)

    rhr1 = rhr.resample(f'{seg}T').mean()
    rhr1 = rhr1.loc[rhr1.index.hour<=6]
    

    missings = rhr24.index[rhr24['heartrate'].isnull()]
    rhr24 = rhr24.interpolate(limit=1)
    # rhr1 = rhr1.interpolate(limit=1)
    rhr1['date']=rhr1.index.floor('1D')
    newJoin = rhr1.join(rhr24median.rename(columns={'heartrate': 'hr_median'}),on='date').sort_index()
    n = pd.DataFrame(index=newJoin.index[newJoin['heartrate'] >= newJoin['hr_median']])
    n['alarm'] = 1
    n = n.resample('1D').sum()
    # red_and_yellow_alert_dates = rhr24[rhr24['heartrate'] >= rhr24median['heartrate']+3].index
    # display(rhr24['heartrate'])
    # display(rhr24median['heartrate'])
    total = rhr1[['heartrate']].rename(columns={'heartrate': 'count'}).resample('1D').count().join(n).fillna(0)
    total=total.loc[total['count']>(7*60/seg)/5]
    # red_alert_dates = n.index[n['alarm']>total['heartrate']/1.5]
    # yellow_alert_dates = n.index[n['alarm'] > total['heartrate']/2]
    red_alert_dates = total.index[total['alarm']/total['count']>0.75]
    yellow_alert_dates = total.index[total['alarm']/total['count']>0.5]

    # red_alert_dates = newJoin[newJoin['heartrate'] > newJoin['hr_median']+4].index
    # yellow_alert_dates = newJoin[(newJoin['heartrate'] > newJoin['hr_median']+3)].index

    allalarms = rhr24.copy()
    allalarms['red_alarm'] = 0
    allalarms['yellow_alarm'] = 0
    allalarms.loc[red_alert_dates, 'red_alarm'] = 1
    allalarms.loc[yellow_alert_dates, 'yellow_alarm'] = 1
    allalarms = allalarms.rolling(2).sum()
    allalarms.loc[allalarms['red_alarm'] >= 2,'red'] = 1
    allalarms.loc[allalarms['yellow_alarm'] >= 2, 'yellow'] = 1
    allalarms=allalarms.fillna(0)
    allalarms['alarm'] = allalarms['red']+allalarms['yellow']
    # print('doing original one')
    # nightsignal2(device,hr_file,step_file)
    return allalarms[['alarm']]