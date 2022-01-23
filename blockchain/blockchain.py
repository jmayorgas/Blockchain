from crypt import methods
import datetime
from email import message
import hashlib
import json
from flask import Flask, jsonify


# CREACIÓN DE CADENA DE BLOQUES (BLOCKCHAIN)
class Blockchain:
    def __init__(self) -> None:
        self.chain = []
        self.create_block(proof=1, previous_hash='0')
    
    def create_block(self, proof: int, previous_hash: str):
        block = {
            'index': len(self.chain)+1,
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'previous_hash': previous_hash
        }
        self.chain.append(block)
        return block
    
    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**3-previous_proof**2+(new_proof**(1/2)-previous_proof**(1/2))).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        
        return new_proof
    
    def hash(self, block):
        """
        Dado un bloque, devuelve el hash correspondiente al mismo
        """
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        """
        Se va a ir comprobando desde el bloque 0 (Génesis)
        que todos los bloques siguientes están correctos
        """
        previous_block = chain[0]
        block_index = 1

        # Bucle while para ir iterando desde el primer hasta el último bloque
        while block_index < len(chain):
            block = chain[block_index]
            # Comparamos si el hash_previo del bloque actual es igual al hash
            # del bloque previo
            if block.get('previous_hash') != self.hash(previous_block):
                return False
            previous_proof = previous_block.get('proof')
            proof = block.get('proof')
            hash_operation = hashlib.sha256(str(proof**3-previous_proof**2+(proof**(1/2)-previous_proof**(1/2))).encode()).hexdigest()
            # Comprobamos si el hash es correcto entre el bloque actual y 
            # el previo
            if hash_operation[:4] != '0000':
                return False
            # Actualizamos el bloque previo por el actual y aumentamos el 
            # índice en 1 posición para comprobar el siguiente bloque
            previous_block = block
            block_index += 1
        
        return True

# MINADO DE BLOQUES DE LA CADENA

# Creación de aplicación web
app = Flask(__name__)

# Creamos una instancia de la clase Blockchain
blockchain = Blockchain()

# Minado de un nuevo bloque
@app.route('/mine_block', methods=['GET'])

def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block.get('proof')
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': 'Congrats. You have mine a new block',
                'index': block.get('index'),
                'timestamp': block.get('timestamp'),
                'proof': block.get('proof'),
                'previous_hash': block.get('previous_hash')
                }
    return jsonify(response), 200

# Obtener la cadena de bloques
@app.route('/get_chain', methods=['GET'])

def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)
               }
    return jsonify(response), 200

# Comprueba si la cadena de bloques es válida
@app.route('/is_valid', methods=['GET'])

def is_valid():
    valid = blockchain.is_chain_valid(blockchain.chain)
    if valid:
        message = 'The blockchain is valid'
    else:
        message = 'Ups. This blockchain is not valid'
    response = {'message': message}
    return jsonify(response), 200


# Ejecutar la app
app.run(host='0.0.0.0', port=5000)