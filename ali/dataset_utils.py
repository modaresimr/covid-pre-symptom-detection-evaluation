import pandas as pd
import os
import json
from . import rhr_utils

dataset_file='COVID-19-Phase2-Wearables.zip'
dataset_meta='41591_2021_1593_MOESM3_ESM.xlsx'

def download():
    from . import utils
    import os
    

    if not os.path.isfile(dataset_file):
        print('downloading dataset....')
        utils.download_file('https://storage.googleapis.com/gbsc-gcp-project-ipop_public/COVID-19-Phase2/COVID-19-Phase2-Wearables.zip',dataset_file)
    if not os.path.isfile(dataset_meta):
        print('downloading meta data....')
        utils.download_file('https://static-content.springer.com/esm/art%3A10.1038%2Fs41591-021-01593-2/MediaObjects/41591_2021_1593_MOESM3_ESM.xlsx',dataset_meta)



def read(device,hr_file,step_file):
    hr = pd.read_csv(hr_file)
    # display( hr.loc[pd.to_datetime(hr['datetime'], errors='coerce').isna()])
    hr['datetime'] = pd.to_datetime(hr['datetime'],errors='coerce')
    error = hr.loc[hr['datetime'].isna()]
    if len(error)>0:
        hr=hr.iloc[0:error.index[0]] #for resolving P678649 
        hr['heartrate'] = hr['heartrate'].astype(int)
    hr=hr.set_index('datetime')
    # if len(error) > 0:
    #     display(hr)
    try:
        step = pd.read_csv(step_file)
    except:
        raise Exception(f"Invalid Format ")
    if device=='Fitbit':
        step['datetime']=pd.to_datetime(step['datetime'])
        step=step.set_index('datetime')
    else: #Apple Watch
        if step.columns[0] == 'BigQuery error in query operation: Error processing job':
            raise Exception(f"Invalid Format {step}")
        if len(step['end_datetime'].unique()) < 2:
            device = 'Fitbit' #step['device'][0]

            step=step.drop(columns=['device']).rename(columns={'start_datetime':'datetime'})
            step['datetime']=pd.to_datetime(step['datetime'])
            step=step.set_index('datetime')
        else:
            error = step.loc[pd.to_datetime(step['start_datetime'], errors='coerce').isna()]
            
            if len(error) > 0:
                step = step.iloc[0:error.index[0]]  # for resolving P678649
                step['steps']=step['steps'].astype(int)
            step['start_datetime']=pd.to_datetime(step['start_datetime']).dt.floor('1T')
            step['end_datetime'] = pd.to_datetime(step['end_datetime']).dt.ceil('1T')
            step=step.loc[step['end_datetime'] > step['start_datetime']]
            step=step.loc[step['end_datetime'] - step['start_datetime']<pd.to_timedelta('10H')]
    return device,hr,step



def load(id):
    hr = pd.read_hdf(f'output/my/{id}/hr.h5', 'hr',mode='r')
    rhr = pd.read_hdf(f'output/my/{id}/rhr.h5', 'rhr',mode='r')
    rhrf = pd.read_hdf(f'output/my/{id}/rhrf.h5', 'rhr',mode='r')
    step = pd.read_hdf(f'output/my/{id}/step.h5', 'step',mode='r')
    with open(f'output/my/{id}/data.json', 'r') as f:
        info = json.load(f)
    info['covid_test_date'] = pd.to_datetime(info['covid_test_date']) if info['covid_test_date'] != 'None' else None
    info['symptom_date'] = pd.to_datetime(info['symptom_date'])if info['symptom_date'] != 'None' else None
    return {
        'hr':hr,
        'step':step,
        'rhr':rhr,
        'rhrf':rhrf,
        'info':info
    }

def convertFromZip(info,force):
    from zipfile import ZipFile
    with ZipFile(dataset_file) as myzip, myzip.open(info['step']) as stepf, myzip.open(info['hr']) as hrf:
        convert(hr_file=hrf, step_file=stepf, info=info, force=force)

def convert(hr_file, step_file, info,force=False):
    id=info['id']
    os.makedirs(f'output/my/{id}', exist_ok=True)
    files = [f'output/my/{id}/hr.h5', f'output/my/{id}/rhr.h5', f'output/my/{id}/rhrf.h5', f'output/my/{id}/step.h5', f'output/my/{id}/data.json']
    exi = [os.path.isfile(f) for f in files]
    if not (force or (False in exi)):
        return
        
    try:
        covid_test_date = pd.to_datetime(info['covid_test_date'])
    except:
        covid_test_date=None    
    try:
        symptom_date = pd.to_datetime(info['symptom_date']) 
    except:
        symptom_date=None    
    device=info['device']
    device,hr, step = read(device, hr_file, step_file)
    rhr = rhr_utils.createRestingHR(device, hr=hr, step=step)
    rhrf = rhr_utils.createRestingHR_new(device, hr=hr, step=step)
    hr.to_hdf(f'output/my/{id}/hr.h5', 'hr', complevel=9, complib='bzip2')
    step.to_hdf(f'output/my/{id}/step.h5', 'step', complevel=9, complib='bzip2')
    rhr.to_hdf(f'output/my/{id}/rhr.h5', 'rhr', complevel=9, complib='bzip2')
    rhrf.to_hdf(f'output/my/{id}/rhrf.h5', 'rhr', complevel=9, complib='bzip2')
    info = {'id': id,'device': device, 'covid_test_date': str(covid_test_date), 'symptom_date': str(symptom_date)}
    with open(f'output/my/{id}/data.json', 'w') as f:
        json.dump(info, f)
    # return load(id)


def getParticipants(args):
    info = pd.read_excel(dataset_meta, 'SourceData_COVID19_Positives', index_col='Participant ID')
    error_files = {}

    from zipfile import ZipFile
    import re
    pattern = re.compile("[^_]*/(P\d+)/(.*\.csv)$")
    
    with ZipFile(dataset_file) as myzip:
        matches = [pattern.match(n) for n in myzip.namelist() if pattern.match(n)]
        ids = {}
        for mm in matches:
            m = mm.groups()

            id = m[0]
            if args.get('only_person',0):
                if id not in args.get('only_person', []):
                    continue
            
            
            if id not in ids:
                ids[id] = {'id': id}
                
            
            file = m[1]
            device = 'AppleWatch' if 'NonFitbit' in file else 'Fitbit'
            typ = "hr" if 'HR' in file else "step"
            ids[id][typ] = mm.string
            ids[id]['device'] = device

            ids[id]['covid_test_date'] = None
            ids[id]['symptom_date'] = None
            if id in info.index:
                user_data = info.loc[id]
                ids[id]['covid_test_date'] = user_data['COVID-19 Test Date']
                ids[id]['symptom_date'] = user_data['COVID-19 Symptom Onset']

            

    if args.get('only_positive', 0):
        ids = {id: ids[id] for id in info.index if id in ids}
    if args.get('only_device', False):
        ids = {id: ids[id] for id in info.index if id in ids and ids[id]['device'] == args.get('only_device')}
    
    # ids = {id: ids[id] for i,id in enumerate(ids) if i>2000}
    return ids;
