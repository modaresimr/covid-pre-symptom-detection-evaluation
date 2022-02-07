import pandas as pd
import subprocess
import os
import shutil
def CuSum(dataset,params):
    info=dataset['info']
    hr=dataset['hr']
    step = dataset['step']
    thereshold=float(params['thereshold'])
    
    id = info["id"]
    root = f'/tmp/cusum/{info["id"]}'
    subprocess.check_output(f'rm -rf {root}; mkdir -p {root}', shell=True)
    # import os
    # os.makedirs(root)
    hrf = f'{root}/hr.csv'
    stepf = f'{root}/step.csv'
    stepf2 = f'{root}/step2.csv'
    hr.to_csv(hrf)
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
        step2.to_csv(stepf)
    else:
        step.to_csv(stepf)
    # step.to_csv(stepf2)
    # display(step2)
    pos_date = info["covid_test_date"] if info["symptom_date"] == None else info["symptom_date"]
    # dev = 'apple' if device == 'AppleWatch' else 'fitbit'

    dev = 'fitbit'
    try:
        import os
        dir_path = os.path.dirname(os.path.realpath(__file__))
        # print(f'{id} {hrf} {stepf} {dev} {pos_date}')
        out = subprocess.check_output(f"/usr/bin/Rscript --vanilla {dir_path}/cusum_orig/online_cusum_alarm_fn.R {id} {hrf} {stepf} {dev} {pos_date.date()} {thereshold}", shell=True, stderr=subprocess.STDOUT)
        # print(out)

        if os.path.isdir(f'output/figure/{id}_figure_under_par{thereshold}/'):
            for f in os.listdir(f'output/figure/{id}_figure_under_par{thereshold}/'):
                shutil.copyfile(f'output/figure/{id}_figure_under_par{thereshold}/{f}', f'output/my/{id}/CuSum-{f}')

    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
    subprocess.check_output(f'rm -rf {root}', shell=True)
    if os.path.isfile(f'output/table/{id}_table_under_par_{thereshold}/{id}_eval_under{thereshold}.csv'):
        eval_under = pd.read_csv(f'output/table/{id}_table_under_par_{thereshold}/{id}_eval_under{thereshold}.csv')
        offline = pd.read_csv(f'output/table/{id}_table_under_par_{thereshold}/{id}_offline_result_under_par{thereshold}.csv')
        online = pd.read_csv(f'output/table/{id}_table_under_par_{thereshold}/{id}_online_result_under_par{thereshold}.csv')
        eval_under = eval_under.rename(columns={'evaluation time': 'datetime', 'alarm for previous 24 hours': 'alarm'})
        eval_under['datetime'] = pd.to_datetime(eval_under['datetime']).dt.floor('1D')
        eval_under = eval_under.set_index('datetime')
        eval_under['alarm'] = eval_under['alarm'].replace({'Green': 0, 'Yellow': 1, 'Red': 2, 'N/A': -1, 'Baseline': -2})
    else:
        if 'Error' in f'{out}':
            print(f"error for {thereshold}")
            print(out)
        eval_under = pd.DataFrame(columns=['alarm'])
    # display(eval_under)
    # display(offline)
    # display(online)
    return eval_under
