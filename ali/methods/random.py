
def randomSignal(dataset,params):
    rhr=dataset['rhr']
    rate = params['rate']

    rhr24 = rhr.resample('1D').max().dropna()
    # rhr24median = rhr24.expanding().median().astype(int)
    red_alert_dates = rhr24.sample(frac=rate, replace=False, random_state=1).index

    # red_alert_dates = rhr24.sample(frac=0.13, replace=True, random_state=1).index
    # red_alert_dates=rhr24.dropna().iloc[::int(1/rate),:].index
    
    # rhr24 = rhr24.interpolate(limit=1)
    # yellow_alert_dates = red_alert_dates

    # red_alert_dates = newJoin[newJoin['heartrate'] > newJoin['hr_median']+4].index
    # yellow_alert_dates = newJoin[(newJoin['heartrate'] > newJoin['hr_median']+3)].index

    allalarms = rhr24.copy()
    allalarms['red_alarm'] = 0
    allalarms['yellow_alarm'] = 0
    allalarms.loc[red_alert_dates, 'alarm'] = 2 
    allalarms = allalarms.fillna(0)
    # print('doing original one')
    # nightsignal2(device,hr_file,step_file)
    return allalarms[['alarm']]
