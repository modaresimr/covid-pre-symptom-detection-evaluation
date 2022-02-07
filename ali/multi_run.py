import multiprocessing
import concurrent.futures
import traceback
import os
import functools
import pandas as pd
from . import main
from . import dataset_utils
from zipfile import ZipFile
from IPython.display import display, Image
import matplotlib.pylab as plt
from . import ui,utils

import ipyumbrella as uw
from tqdm.notebook import tqdm




def run(args):
    print(f'runing... args={args}')
    ids=dataset_utils.getParticipants(args)
    eval_plot = ui.eval_ploter(args=args)
    
    
    total = None
    
    
    
    parallel= args.get('parallel',0)

    uw.Accordion().D.append(eval_plot.out, title='Evaluation')
    if parallel:
        # display(eval_plot.out)
        runner = functools.partial(parrun, args=args)
    else:
        runner = functools.partial(parrun, args=args, acc=uw.Accordion().D)

    result=utils.parallelRunner(parallel, runner, ids.values())

    for i,res in enumerate(result):
        (id, out, data)=res
        if 'eval' in out:
            res = out['eval']
            if(total is None):
                total = res
            else:
                total = total.add(res, fill_value=0)
            # eval_plot.plot_evals(total)
            if args.get('show_final_graph', 0):
                display(Image(f'output/my/{id}/all.png'))
            if(i % 19 == 0):
                print(f'{(i/len(ids)*100):0.0f}%    {"*"*int(i/len(ids)*50)}')
            if(i % 1 == 0):
                eval_plot.plot_evals(total)
            # printEvals(total)

    print(f'result============')

    eval_plot.plot_evals(total,True)
    # printEvals(total)
    # eval_plot.close()

    return total





def run2(args):
    print(f'runing... args={args}')
    ids=getFileInfo(args)
    eval_plot = ui.eval_ploter(args=args)
    pbar = tqdm(total=len(ids))
    
    
    total = None
    
    if args.get('parallel'):
        display(eval_plot.out)
        runner = functools.partial(parrun, args=args)
        from contextlib import closing

        pool = multiprocessing.Pool(8,maxtasksperchild=8)
        try:
            result = pool.imap(runner, ids.values())
            
            # pool= concurrent.futures.ProcessPoolExecutor(8)
            # result = pool.map(runner, ids.values())

            for i,(id, out, data) in enumerate(result):
            # for i, id in enumerate(ids):
            #     (id, out, data) = result.next()
                pbar.update(1)
                if 'eval' in out:
                    res = out['eval']
                    if(total is None):
                        total = res
                    else:
                        total = total.add(res, fill_value=0)
                    # eval_plot.plot_evals(total)
                    if args.get('show_final_graph', 0):
                        display(Image(f'output/my/{id}/all.png'))
                    if(i % 19 == 0):
                        print(f'{(i/len(ids)*100):0.0f}%    {"*"*int(i/len(ids)*50)}')
                    if(i % 1 == 0):
                        eval_plot.plot_evals(total)
                    # printEvals(total)
        except KeyboardInterrupt:
            pool.terminate()
            pool.join()
            pool.close()

    else:
        uw.Accordion().D.append(eval_plot.out, title='Evaluation')
        acc = uw.Accordion().D
        runner = functools.partial(parrun, args=args,acc=acc)
        for i, data in enumerate(ids.values()):
            (id, out, data) = runner(data)
            pbar.update(1)
            if 'eval' in out:
                res = out['eval']
                if(total is None):
                    total = res
                else:
                    total = total.add(res, fill_value=0)
                # if(total == None):
                #     total = res
                # else:
                #     total = {k: {cm: total[k][cm]+res[k][cm] for cm in res[k]} for k in res}
            if args.get('show_final_graph', 0):
                display(Image(f'output/my/{id}/all.png'))
            if(i % 10 == 0 and not(total is None)):
                print(f'{(i/len(ids)*100):0.0f}%    {"*"*int(i/len(ids)*50)}')

            if(i % 1 == 0 and not(total is None)):
                eval_plot.plot_evals(total)
                # printEvals(total)
                # ui.plot_evals(total,fig)

    print(f'result============')

    eval_plot.plot_evals(total,True)
    # printEvals(total)
    # eval_plot.close()

    return total




def parrun(data, args,acc=None):
    
    id = data['id']

    
    
    print(' ', end='', flush=True)
    if acc is None:
        return parrun2(data,args)
    with acc.item(f'{id}'):
        return parrun2(data,args)

def parrun2(info, args):
        id = info['id']
        print(' ', end='', flush=True)
        # print (id)
        try:
            # run_methods = args['methods']
            # print(f'{id}, run_methods={run_methods}')
            
            # print(f'{id}, run_methods={run_methods}')        
            # run_methods=[]
            dataset_utils.convertFromZip(info,force=False)
            # data=pd.DataFrame()
            # data[id,info['device']]=1
            
            return (id, {'eval': main.run(id=id, args=args)}, info)

        #             print(f'res={res} total={total_res}')
                # if total_res==None:total_res=res
                # else:
                #     total_res={k:{cm:total_res[k][cm]+res[k][cm] for cm in res[k]} for k in res}

            # if args.get('debug') and ('nightsignal_orig' in methods):
            #     from IPython.display import IFrame
            #     display(Image("./NightSignalResult.png"))

        except Exception as e:
            print(f'{id} ignored because of exception {e}')
            if args.get('show_exception'):
                print(f'id={id} {e}'[0:200])
                traceback.print_exc()

            return (id, {'exception': e}, info)
        return (id, {'finish': 'yes'}, info)
