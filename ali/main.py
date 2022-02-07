import pandas as pd
import os
from IPython.display import display
import subprocess
from . import ui
from . import evals
from . import timeseries_anomaly_detection
from . import dataset_utils
import os
import shutil
import traceback
import json

from . import methods

def run(id, args={}):
    dataset = dataset_utils.load(id)
    info = dataset['info']
    if args['debug']:
        print(info)
    os.makedirs(f'output/my/{id}', exist_ok=True)
    
    try:
        allAlarms = pd.read_csv(f'output/my/{id}/alarm.csv', parse_dates=['datetime'], index_col='datetime')
        allAlarms = allAlarms[[c for c in allAlarms.columns if 'alisignal' not in c]]
    except:
        allAlarms = dataset['rhrf'].resample('1d').count()[[]]

    run_methods = args['methods']
    for method in run_methods:
        if not args['rerun'] and method in allAlarms.columns:
            continue

        args['current_method'] = method
        print(f'{id} {method}')
        inline_params = method.split('_')
        try:
            if 'ns_my' in method :
                out = methods.nightsignal.nightsignal(dataset=dataset, params={
                    'red_threshold': int(inline_params[1]),
                    'yellow_threshold': int(inline_params[1])-1
                })
            elif 'nightsignal' in method:
                out = methods.nightsignal.nightsignal_orig(dataset=dataset, params={
                    'red_threshold': int(inline_params[1]),
                    'yellow_threshold': int(inline_params[1])-1
                })
            elif 'alisignal' in method:
                seg = int(method.split('_')[1])
                out = methods.mysignal.alisignal(dataset=dataset, params={'seg':seg})
            elif 'random' in method:
                out = methods.random.randomSignal(dataset=dataset, params={
                    'rate':float(inline_params[1])
                })
            elif 'CuSum' in method :
                out = methods.cusum.CuSum(dataset=dataset,params={
                    'thereshold':inline_params[1]
                })
            elif 'isolationforest' in method:
                out = methods.isolationforest.IsolationForest(dataset=dataset,params={
                    'contamination_rate':float(inline_params[1])
                })
            elif 'isolationforest2' in method:
                out = methods.isolationforest.IsolationForest2(dataset=dataset)
            elif 'laad' in method :
                out = methods.laad.laad(dataset=dataset,params={
                    'threshold%':float(inline_params[1])
                })
            elif 'rhrad' in method:
                out = methods.rhrad.rhrad(dataset=dataset, params={
                    'mode': 'v7',
                    'outliers_fraction': inline_params[1]})
            elif 'ad_' in method:
                # flags> a: avg feature
                # flags> b: avg of previous avg feature
                # flags> d: day feature
                # flags> f: time segment
                # flags> l: transfer learning
                # flags> m: median feature
                # flags> n: avg of previous median feature
                # flags> o: only over night
                # flags> t: time feature

                params = {'flags': inline_params[1],
                          'seg': pd.to_timedelta(inline_params[2]),
                          'overlap': pd.to_timedelta(inline_params[3]),
                          'resolution': inline_params[4],
                          'model': 'auto-encoder',
                          # 'model':'lstm',
                          # 'use_time_feature':0,
                          # 'use_time_feature':1,
                          'test_days': 2,
                          'min_train_days': 7,
                          'max_train_days': 50,
                          # 'future_data_if_not_enough_data':14,
                          'future_data_if_not_enough_data': 0,
                          'only_new_points': 1,
                          # 'use_median':1,
                          **args
                          }
                # print(params)
                out = methods.autoencoder.anomaly_detection(dataset=dataset, params=params)
            elif method=='use-all':
                continue
            else:
                print(f'method not found  {method}')

            allAlarms[method] = out['alarm']
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f'{id} {method} ignored because of exception {e}')
            if args.get('show_exception', 0):
                print(f'id={id} {e}'[0:200])
                traceback.print_exc()

            continue

    if 'use-all' in run_methods:
        out = methods.useall.usingAll(allAlarms)
        if out is not None:
            allAlarms['use-all'] = out['alarm']


    allAlarms = allAlarms.fillna(-3)
    allAlarms.to_csv(f'output/my/{id}/alarm.csv')

    

    ev = {}
    # display(rhrf)
    for method in allAlarms.columns:
        alarm = allAlarms[[method]].rename(columns={method: 'alarm'})
        res = evals.eval_both(dataset, alerts=alarm)
        ev[method] = pd.DataFrame(res).T.stack()

    df = pd.concat(ev, axis=1).T
    # df = df.round(2)#.sort_index(axis=1)
    # print(df)

    result=evals.CalcMetrics(df)
    df.round(2).to_csv(f'output/my/{id}/eval.csv')

    if args.get('save_plots_for_user', 0):
        ui.plotAll(dataset, all_alarms=allAlarms,
                   file=f'output/my/{id}/all.png', args=args, evals=result)

    if args.get('draw_eval', 0):
        # display(df.round(2))
        ui.plot_evals(df)

    return df


if __name__ == '__main__':
    import glob
    import os
    import getopt
    import sys
    full_cmd_arguments = sys.argv
    argument_list = full_cmd_arguments[1:]

    short_options = "h"
    long_options = ["heartrate=", "step=", "device=", "restinghr=", "method="]

    try:
        arguments, values = getopt.getopt(argument_list, short_options, long_options)
    except getopt.error as err:
        print(str(err))
        sys.exit(2)
    covid_test_date = None
    symthom_date = None
    import random

    id = -1
    for current_argument, current_value in arguments:
        if current_argument in ("-h", "--help"):
            print("Please use: python3 ali.py --method=nightsignal --device=Fitbit --restinghr=<RHR_FILE> || python3 --method=isolationforest ali.py --device=AppleWatch  --heartrate=<HR_FILE> --step=<STEP_FILE> ")
        elif current_argument in ("--heartrate"):
            hr_file = current_value
        elif current_argument in ("--step"):
            step_file = current_value
        elif current_argument in ("--device"):
            device = current_value
        # elif current_argument in ("--restinghr"):
        #     restinghr_file = current_value
        elif current_argument in ("--method"):
            method = current_value
        elif current_argument in ("--covid-test-date"):
            covid_test_date = current_value
        elif current_argument in ("--symthom-date"):
            symthom_date = current_value
        elif current_argument in ("--id"):
            id = current_value

    if id == -1:
        id = hash(step_file+hr_file)

    dataset_utils.convert(hr_file=hr_file, step_file=step_file, info={
        'id': id,
        'device': device,
        'covid_test_date': covid_test_date, 'symptom_date': symthom_date
    }, force=True)
    out = run(id=id, args={'methods':[method]})
    # display(out)
