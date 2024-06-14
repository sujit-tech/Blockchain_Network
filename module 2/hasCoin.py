#creating crypto currency
import datetime
import hashlib
import json
from flask import Flask, jsonify,request
import requests
from uuid import uuid4
from urllib.parse import urlparse

#part 1
# Create blockchain
class Blockchain:
    def __init__(self):
        self.chain = []
        self.transactions=[]
        self.create_block(proof=1, prev_hash='0')
        self.node=set()

    def create_block(self, proof, prev_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'prev_hash': prev_hash,
            'transaction':self.transactions
        }
        self.transactions=[]
        self.chain.append(block)
        return block

    def get_prev_block(self):
        return self.chain[-1]

    def proof_of_work(self, prev_proof):
        new_proof = 1
        check_proof = False
        while not check_proof:
            hash_op = hashlib.sha256(str(new_proof**2 - prev_proof**2).encode()).hexdigest()
            if hash_op[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self,chain):
        prev_block = self.chain[0]
        block_index = 1
        while block_index < len(self.chain):
            block = self.chain[block_index]
            if block['prev_hash'] != self.hash(prev_block):
                return False
            prev_proof = prev_block['proof']
            proof = block['proof']
            hash_op = hashlib.sha256(str(proof**2 - prev_proof**2).encode()).hexdigest()
            if hash_op[:4] != '0000':
                return False
            prev_block = block
            block_index += 1
        return True
    def add_transaction(self,sender,receiver,amount):
        self.transactions.append({'sender':sender,
                           'receiver': receiver,
                           'amount':amount})
        prev_block=self.get_prev_block()
        return prev_block['index']+1
    def add_node(self,address):
        parse_url = urlparse(address)
        self.node.add(parse_url.netloc)
    def replace_chain(self):
        network =self.node
        longest_chain=None
        max_length=len(self.chain)
        for node in network:
            response=requests.get(f'http://{node}/get_chain')
            if response.status_code==200:
                length =response.json()['length']
                chain=response.json()['chain']
                if length>max_length and self.is_chain_valid(chain):
                    max_length=length
                    longest_chain=chain
        if longest_chain:
            self.chain=longest_chain
            return True
        return False
# Create web App
app = Flask(__name__)
node_address = str(uuid4()).replace('-', '')
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
blockchain = Blockchain()

#part 2 mining the blockchain

# Mine a block
@app.route('/mine_block', methods=['GET'])
def mine_block():
    prev_block = blockchain.get_prev_block()
    prev_proof = prev_block['proof']
    proof = blockchain.proof_of_work(prev_proof)
    prev_hash = blockchain.hash(prev_block)
    blockchain.add_transaction(sender=node_address, receiver='hadalin', amount=1)
    block = blockchain.create_block(proof, prev_hash)
    response = {
        'message': 'Congratulations, you just mined a block!',
        'index': block['index'],
        'timestamp': block['timestamp'],
        'proof': block['proof'],
        'prev_hash': block['prev_hash'],
        'transaction':block['transaction']
    }
    return jsonify(response), 200

# Retrieve the full Blockchain
@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200
#check validity
@app.route('/is_valid', methods=['GET'])
def is_valid():
    valid = blockchain.is_chain_valid(blockchain.chain)
    if valid:
        response={'message':'valid'}
    else:
        response={'message':'invalid'}
    return jsonify(response),200
#add transaction inside block
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json=request.get_json()
    transaction_key=['sender','receiver','amount']
    if not all(key in json for key in transaction_key):
        return 'some elements are missing',400
    index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
    response = {'message':f'this transact will be added to block {index}'}
    return jsonify(response),201
#connecting the nodes
@app.route('/connect_node', methods=['POST'])
def connect_node():
    nodes=request.get_json().get('nodes')
    if nodes is None:
        return "no node",400
    for node in nodes:
        blockchain.add_node(node)
    response={'message':'All nodes are connected',
              'total node':list(blockchain.node)}
    return jsonify(response),201

@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response={'message': 'all node in chains are changed',
                 'new chain':blockchain.chain}
    else:
        response={'message':'every chain are valid',
                'actual chain':blockchain.chain}
    return jsonify(response),200

# Run app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
