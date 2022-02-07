
def createRestingHR_new(device,hr,step):
    
    if device=='Fitbit':
        # Cacluating Resting HR
        step_n=step.resample('1T').mean()
    #     hr['datetime_m'] = hr.index.floor('1T')
    #     hr_step = hr.join(step, on='datetime_m', how='outer')
    else: #Apple Watch
        step_n=pd.DataFrame(columns=['steps'])
    #         print(step)
        all=[]
        for k,row in step.iterrows():
            newRange=pd.date_range(row['start_datetime'].floor('1T'),row['end_datetime'].floor('1T'),freq='1T')
            a=pd.DataFrame(index=newRange)
            a['steps']=row['steps']/len(newRange)
            all.append(a)

        step_n=pd.concat(all)

    hr = hr.resample('1T').mean()
    hr_step = hr.join(step_n, how='outer')

    rhr_hint=hr_step.rolling('12T',min_periods=0).count().loc[hr.index].dropna()
    rhr=hr.loc[rhr_hint[(rhr_hint['heartrate']>0) &(rhr_hint['steps']==0)].index].dropna()
    return rhr
    

def createRestingHR(device,hr,step):
    nighthr = hr[(hr.index.hour >= 0) & (hr.index.hour <= 6)].copy()
    
    if device=='Fitbit':
        # Cacluating Resting HR
        nighthr['datetime_m'] = nighthr.index.floor('T')
        hr_step = nighthr.join(step, on='datetime_m', how='left')
        rhr = hr_step[hr_step['steps'] != hr_step['steps']][['heartrate']]
    else: #Apple Watch
        import pandasql as ps
        sqlcode = '''
        select datetime,heartrate from nighthr where datetime not in (
            select nighthr.datetime
            from nighthr,step
            where nighthr.datetime >= step.start_datetime and nighthr.datetime <= step.end_datetime
            )
        '''
        rhr = ps.sqldf(sqlcode, locals())
        rhr['datetime'] = pd.to_datetime(rhr['datetime'])
        rhr = rhr.set_index('datetime')
    return rhr
