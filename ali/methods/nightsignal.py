import os
import pandas as pd

def nightsignal_orig(dataset,params):
    hr = dataset['hr']
    step = dataset['step']
    info=dataset['info']
    device = dataset['info']['device']
    import sys
    # sys.path.append("..")
    from .ns_orig import nightsignal
    
    if device == 'Fitbit':
        nighthr = hr[hr.index.hour <= 6][['heartrate']]

        rhr = nighthr.resample("1T").mean().dropna().round().join(step).fillna(0)[['heartrate', 'steps']].astype(int)

        # df.drop(['row_num','start_date','end_date','symbol'], axis=1, errors='ignore').astype(int)
        # display(rhr.loc[rhr['end_datetime'] == ' '])
        rhr.to_csv(f'/tmp/rhr{info["id"]}.csv')
        out = nightsignal.run(heartrate_file=None,
                              step_file=None,
                              device=device,
                              restinghr_file=f'/tmp/rhr{info["id"]}.csv',
                              id=info['id'],
                              red_threshold=params['red_threshold'],
                              yellow_threshold=params['yellow_threshold'])
    else:
        out = nightsignal.run(heartrate_file=hr,
                              step_file=step,
                              device=device,
                              id=info['id'],
                              red_threshold=params['red_threshold'],
                              yellow_threshold=params['yellow_threshold'])
        # out.index=out.index.rename('datetime')
    # print(out)
    os.system(f'rm /tmp/rhr{info["id"]}.csv')
    if out.columns.shape[0] == 0:
        allalarms = hr.resample('1D').max()
        allalarms['alarm'] = 0
        return allalarms[['alarm']]
    out = out.rename(columns={'date': 'datetime', 'val': 'alarm'})
    out['datetime'] = pd.to_datetime(out['datetime'])
    out = out.set_index('datetime').astype(int)
    # print(out)
    # out=out.loc[out['alarm']>0]
    out.index = out.index.floor('1D')
    out=out.loc[out.alarm>0]
    return out


# My implementation
def nightsignal(dataset,params):
    rhr = dataset['rhr']
    red_threshold = params['red_threshold'],
    yellow_threshold = params['yellow_threshold']
    
    rhr24 = rhr.resample('24H').mean()
    rhr24median = rhr24.expanding().median().astype(int)

    missings = rhr24.index[rhr24['heartrate'].isnull()]
    rhr24 = rhr24.interpolate(limit=1)

    # newJoin = rhr24.join(rhr24median.rename(columns={'heartrate': 'hr_median'})).sort_index()
    # red_and_yellow_alert_dates = rhr24[rhr24['heartrate'] >= rhr24median['heartrate']+3].index
    # display(rhr24['heartrate'])
    # display(rhr24median['heartrate'])
    red_alert_dates = rhr24.index[rhr24['heartrate'] >= rhr24median['heartrate']+red_threshold]
    yellow_alert_dates = rhr24.index[rhr24['heartrate'] >= rhr24median['heartrate']+yellow_threshold]
    # red_alert_dates = newJoin[newJoin['heartrate'] > newJoin['hr_median']+4].index
    # yellow_alert_dates = newJoin[(newJoin['heartrate'] > newJoin['hr_median']+3)].index

    allalarms = rhr24.copy()
    allalarms['red_alarm'] = 0
    allalarms['yellow_alarm'] = 0
    allalarms.loc[red_alert_dates, 'red_alarm'] = 1
    allalarms.loc[yellow_alert_dates, 'yellow_alarm'] = 1
    allalarms = allalarms.rolling(2).sum()
    allalarms.loc[allalarms['red_alarm'] >= 2, 'red'] = 1
    allalarms.loc[allalarms['yellow_alarm'] >= 2, 'yellow'] = 1
    allalarms = allalarms.fillna(0)
    allalarms['alarm'] = allalarms['red']+allalarms['yellow']
    # print('doing original one')
    # nightsignal2(device,hr_file,step_file)
    return allalarms[['alarm']]


