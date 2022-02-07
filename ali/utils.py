from tqdm.notebook import tqdm
import multiprocessing


def parallelRunner(parallel, runner, items):
    pbar = tqdm(total=len(items))
    if parallel:
        pool = multiprocessing.Pool(8,maxtasksperchild=4)
        result = pool.imap(runner, items)
        try:
            for _ in items:
                res = result.next()
                pbar.update(1)
                yield res
        except KeyboardInterrupt:
            pool.terminate()
            pool.join()
            pool.close()
            raise
    else:
        for item in items:
            res = runner(item)
            pbar.update(1)
            yield res


def download_file(url, filename):
    """
    Helper method handling downloading large files from `url` to `filename`. Returns a pointer to `filename`.
    """
    import urllib, os
    
    response = getattr(urllib, 'request', urllib).urlopen(url)
    with tqdm.wrapattr(open(filename+".tmp", "wb"), "write",
                    miniters=1, desc=url.split('/')[-1],
                    total=getattr(response, 'length', None)) as fout:
        for chunk in response:
            fout.write(chunk)

    os.rename(filename+".tmp",filename)