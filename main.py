import miner
import message_handler
import time
import threading
import custom
import leveldb
import networking
import command_prompt_advanced
import sys
import truthcoin_api
import tools
import blockchain
import peers_check
import multiprocessing
import Queue

i_queue=multiprocessing.Queue()
o_queue=multiprocessing.Queue()
heart_queue=multiprocessing.Queue()
try:
    script=file(sys.argv[1],'r').read()
except: script=''
db = leveldb.LevelDB(custom.database_name)
DB = {'stop':False,
      'db': db,
      'txs': [],
      'suggested_blocks': Queue.Queue(),
      'suggested_txs': Queue.Queue(),
      'heart_queue': heart_queue,
      'memoized_votes':{},
      'peers_ranked':[],
      'diffLength': '0'}
def len_f(i, DB):
    if not blockchain.db_existence(str(i), DB): return i-1
    return len_f(i+1, DB)
DB['length']=len_f(0, DB)
DB['diffLength']='0'
if DB['length']>-1:
    DB['diffLength']=blockchain.db_get(str(DB['length']), DB)['diffLength']

worker_tasks = [
    # Keeps track of blockchain database, checks on peers for new blocks and
    # transactions.
    #all these workers share memory DB
    #if any one gets blocked, then they are all blocked.
    {'target': truthcoin_api.main,
     'args': (DB, i_queue, o_queue),
     'daemon':True},
    {'target': miner.main,
     'args': (custom.pubkey, custom.hashes_per_check, DB),
     'daemon': False},#it makes more threads, so it can't be a daemon.
    {'target': blockchain.suggestion_txs,
     'args': (DB,),
     'daemon': True},
    {'target': blockchain.suggestion_blocks,
     'args': (DB,),
     'daemon': True},
    {'target': peers_check.main,
     'args': (custom.peers, DB),
     'daemon': True},
    {'target': networking.serve_forever,
     'args': (custom.port, lambda d: message_handler.main(d, DB), heart_queue),
     'daemon': True}
]
processes= [#these do NOT share memory with the rest.
    {'target':command_prompt_advanced.main, 
     'args':(i_queue, o_queue, script)},
    {'target':tools.heart_monitor,
     'args':(heart_queue, )}
]
cmds=[]
for process in processes:
    cmd=multiprocessing.Process(target=process['target'], args=process['args'])
    cmd.start()
    cmds.append(cmd)
def start_worker_proc(**kwargs):
    #print("Making worker thread.")
    daemon=kwargs.pop('daemon', True)
    proc = threading.Thread(**kwargs)
    proc.daemon = daemon
    proc.start()
    return proc

#print('tasks: ' + str(worker_tasks))
workers = [start_worker_proc(**task_info) for task_info in worker_tasks]
while not DB['stop']:
    #print('in loop')
    time.sleep(0.5)
tools.log('stopping all threads...')
for cmd in cmds:
    cmd.join()
time.sleep(5)
sys.exit(1)
