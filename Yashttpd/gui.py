""" The easiest way to understand this file is to try it out and have a look at
the html it creates. It creates a very simple page that allows you to spend
money."""
import copy
import tools
import blockchain
import custom
import http
import random
import transactions

def create_jury(pubkey, privkey, dic, DB):
    tx = {'type': 'create_jury', 'vote_id': dic['jury_id']}
    easy_add_transaction(tx, privkey, DB)
    
def spend(pubkey, privkey, dic, DB):
    amount = int(float(dic['amount']) * (10 ** 5))
    tx = {'type': 'spend', 'amount': amount, 'to': dic['to']}
    easy_add_transaction(tx, privkey, DB)

def votecoin_spend(pubkey, privkey, dic, DB):
    amount = int(float(dic['amount']) * (10 ** 5))    
    tx = {'type': 'spend', 'amount': int(amount), 'to': dic['to'], 'vote_id':dic['votecoin_id']}
    easy_add_transaction(tx, privkey, DB)

def ask_decision(pubkey, privkey, dic, DB):
    tx={'type':'propose_decision', 'vote_id':dic['vote_id'], 'decision_id':dic['decision_id'], 'txt':dic['txt']}
    easy_add_transaction(tx, privkey, DB)

def vote_on_decision(pubkey, privkey, dic, DB):
    address=tools.make_address([pubkey], 1)#this might be wrong
    acc=blockchain.db_get(address, DB)
    value=[dic['answer'], str(random.random())+str(random.random())]
    answer_hash=tools.det_hash(value)
    DB['memoized_votes'][answer_hash]=value
    old_vote='unsure'
    if dic['decision_id'] in acc['votes']: #this is always False...
        old_vote=acc['votes'][dic['decision_id']]
    tx={'type':'jury_vote', 'vote_id':dic['vote_id'], 'decision_id':dic['decision_id'], 'old_vote':old_vote, 'new_vote':answer_hash}
    easy_add_transaction(tx, privkey, DB)

def reveal_vote(pubkey, privkey, dic, DB):
    address=tools.make_address([pubkey], 1)#this might be wrong
    acc=blockchain.db_get(address, DB)
    if decision_id in acc['votes']:
        answer_hash=acc['votes'][decision_id]
        a=DB['memoized_votes'][answer_hash]
        tx={'type':'reveal_jury_vote', 'vote_id':dic['vote_id'], 'decision_id':dic['decision_id'], 'old_vote':answer_hash, 'new_vote':a[0], 'secret':a[1]}
        easy_add_transaction(tx, privkey, DB)
def decisions_keepers(jury, DB):
    matrix=transactions.decision_matrix(jury, jury['decisions'], DB)
    #exclude decisions with insufficient participation*certainty
    pc=transactions.part_cert(matrix)
    decisions=[]
    for i in range(len(pc)):
        if pc[i]>0.6:
            decisions.append(jury['decisions'][i])
    return decisions
def SVD_consensus(pubkey, privkey, dic, DB):
    jury=blockchain.db_get(tx['vote_id'], DB)
    tx={'type':'SVD_consensus', 'vote_id':dic['vote_id'], 'decisions':decisions_keepers(jury, DB)}
    easy_add_transaction(tx, privkey, DB)
def make_PM(pubkey, privkey, dic, DB):
    address=tools.make_address([pubkey], 1)
    tx={'type':'prediction_market', 'PM_id':'weather', 'fees':0, 'B':10, 'states':['0 0 0', '1 0 0', '1 1 0', 'default'], 'states_combinatory':[[0,0,0],[1,0,0],[1,1,0]], 'shares_purchased':[0,0,0,0],'decisions':["unique title for decision","unique title for decision2","unique title for decision3"], 'owner':address}
    print('pm in make: ' +str(tx))
    easy_add_transaction(tx, privkey, DB)
def buy_shares(pubkey, privkey, dic, DB):
    tx={'type':'buy_shares', 'buy':[5,4,3,0], 'PM_id':'weather'}
    easy_add_transaction(tx, privkey, DB)
def collect_winnings(pubkey, privkey, div, DB):
    address=tools.make_address([pubkey], 1)
    acc=blockchain.db_get(address, DB)
    tx={'type':'collect_winnings', 'PM_id':'weather', 'shares':acc['shares'][tx['PM_id']], 'address':address}
    easy_add_transaction(tx, privkey, DB)
def easy_add_transaction(tx_orig, privkey, DB):
    tx = copy.deepcopy(tx_orig)
    pubkey = tools.privtopub(privkey)
    address = tools.make_address([pubkey], 1)
    if 'pubkeys' not in tx:
        tx['pubkeys']=[pubkey]
    try:
        tx['count'] = blockchain.count(address, DB)
    except:
        tx['count'] = 1
    tx['signatures'] = [tools.sign(tools.det_hash(tx), privkey)]
    print('CREATED TX: ' + str(tx))
    blockchain.add_tx(tx, DB)

submit_form='''
<form name="first" action="{}" method="{}">
<input type="submit" value="{}">{}
</form> {}
'''
empty_page = '<html><body>{}</body></html>'


def easyForm(link, button_says, more_html='', form_type='post'):
    a = submit_form.format(link, '{}', button_says, more_html, "{}")
    if form_type == 'get':
        return a.format('get', '{}')
    else:
        return a.format('post', '{}')

linkHome = easyForm('/', 'HOME', '', 'get')


def page1(DB, brainwallet=custom.brainwallet):
    out = empty_page
    txt = '<input type="text" name="BrainWallet" value="{}">'
    out = out.format(easyForm('/home', 'Enter BasicCoin wallet passphrase: ', txt.format(brainwallet)))
    return out.format('')


def home(DB, dic):
    if 'BrainWallet' in dic:
        dic['privkey'] = tools.det_hash(dic['BrainWallet'])
    elif 'privkey' not in dic:
        return "<p>You didn't type in your brain wallet.</p>"
    privkey = dic['privkey']
    pubkey = tools.privtopub(dic['privkey'])
    address = tools.make_address([pubkey], 1)
    Do={'SVD_consensus':SVD_consensus, 'reveal_vote':reveal_vote, 'vote_on_decision':vote_on_decision, 'ask_decision':ask_decision, 'create_jury':create_jury, 'spend':spend, 'votecoin_spend':votecoin_spend, 'make_PM':make_PM, 'buy_shares':buy_shares, 'collect_winnings':collect_winnings}
    if 'do' in dic and dic['do'] in Do:
        Do[dic['do']](pubkey, privkey, dic, DB)
    out = empty_page
    out = out.format('<p>your address: ' + str(address) + '</p>{}')
    out = out.format('<p>current block: ' + str(DB['length']) + '</p>{}')
    acc = blockchain.db_get(address, DB)
    balance = acc['amount']
    for tx in DB['txs']:
        if tx['type'] == 'spend' and tx['to'] == address and 'vote_id' not in tx:
            balance += tx['amount']
        if tx['type'] == 'spend' and tx['pubkeys'][0] == pubkey:
            if 'vote_id' not in tx:
                balance -= tx['amount']                
            balance -= custom.fee
    out = out.format('<p>current balance is: ' + str(balance/100000.0) + '</p>{}')
    if balance > 0:
        out = out.format(easyForm('/home', 'spend money', '''
        <input type="hidden" name="do" value="spend">
        <input type="text" name="to" value="address to give to">
        <input type="text" name="amount" value="amount to spend">
        <input type="hidden" name="privkey" value="{}">'''.format(privkey)))
        out = out.format(easyForm('/home', 'ask decision', '''
        <input type="hidden" name="do" value="ask_decision">
        <input type="text" name="vote_id" value="name of jury">
        <input type="text" name="decision_id" value="unique title for decision">
        <input type="text" name="txt" value="decision txt">
        <input type="hidden" name="privkey" value="{}">'''.format(privkey)))
    if balance > custom.create_jury_fee:
        out = out.format(easyForm('/home', 'create jury', '''
        <input type="hidden" name="do" value="create_jury">
        <input type="text" name="jury_id" value="name of jury">
        <input type="hidden" name="privkey" value="{}">'''.format(privkey)))
    out = out.format(easyForm('/home', 'make PM', '''
    <input type="hidden" name="do" value="make_PM">
    <input type="hidden" name="privkey" value="{}">'''.format(privkey)))
    for pool in acc['votecoin']:
        out = out.format('amount: {} {}'.format(acc['votecoin'][pool], '{}'))
        out = out.format(easyForm('/home', 'spend votecoins: '+str(pool), '''
        <input type="hidden" name="do" value="votecoin_spend">
        <input type="text" name="to" value="address to give to">
        <input type="text" name="amount" value="amount to spend">
        <input type="hidden" name="votecoin_id" value="{}">
        <input type="hidden" name="privkey" value="{}">'''.format(pool, privkey)))
        votecoin_pool=blockchain.db_get(pool, DB)
        if tools.reveal_time_p(DB, 5):
            out = out.format(easyForm('/home', 'SVD consensus', '''
            <input type="hidden" name="do" value="SVD_consensus">
            <input type="hidden" name="vote_id" value="{}">
            <input type="hidden" name="privkey" value="{}">'''.format(pool, privkey)))
        for decision in votecoin_pool['decisions']:
            dec=blockchain.db_get(decision, DB)
            if not tools.reveal_time_p(DB):
                out = out.format(easyForm('/home', 'vote on decision: '+str(decision)+' : '+(dec['txt']), '''
                <input type="hidden" name="do" value="vote_on_decision">
                <input type="text" name="answer" value="yes/no/unsure">
                <input type="hidden" name="vote_id" value="{}">
                <input type="hidden" name="decision_id" value="{}">
                <input type="hidden" name="privkey" value="{}">'''.format(pool, decision, privkey)))
            acc=blockchain.db_get(address, DB)
            if tools.reveal_time_p(DB) and decision in acc['votes'] and len(acc['votes'][decision])>8:#and I have participated in a vote
                out = out.format(easyForm('/home', 'reveal vote: '+str(decision)+' : '+(dec['txt']), '''
                <input type="hidden" name="do" value="reveal_vote">
                <input type="hidden" name="vote_id" value="{}">
                <input type="hidden" name="decision_id" value="{}">
                <input type="hidden" name="privkey" value="{}">'''.format(pool, decision, privkey)))
    if blockchain.db_existence('weather', DB):
        out = out.format(easyForm('/home', 'buy_shares: ', '''
        <input type="hidden" name="do" value="buy_shares">
        <input type="hidden" name="privkey" value="{}">'''.format(privkey)))
        out = out.format(easyForm('/home', 'collect winnings: ', '''
        <input type="hidden" name="do" value="collect_winnings">
        <input type="hidden" name="privkey" value="{}">'''.format(privkey)))
    txt='''    <input type="hidden" name="privkey" value="{}">'''
    s = easyForm('/home', 'Refresh', txt.format(privkey))
    return out.format(s)


def hex2htmlPicture(string, size):
    txt = '<img height="{}" src="data:image/png;base64,{}">{}'
    return txt.format(str(size), string, '{}')

def main(port, brain_wallet, db):
    global DB
    DB = db
    http.server(DB, port, page1, home)