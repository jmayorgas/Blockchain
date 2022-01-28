from crypt import methods
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse


# CREACIÓN DE UNA CADENA DE BLOQUES
class Blockchain:
    def __init__(self) -> None:
        self.chain = []
        self.transactions = []
        self.create_block(proof=1, previous_hash='0')
        # El listado de nodos donde va a operar nuestra blockchain, no va a existir un
        # orden. Por eso se usa el set en lugar de una lista
        self.nodes = set()
    
    def create_block(self, proof: int, previous_hash: str):
        block = {
            'index': len(self.chain)+1,
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'previous_hash': previous_hash,
            'transactions': self.transactions
        }
        self.transactions = []
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
    
    def add_transaction(self, sender, receiver, amount):
        """
        sender: Emisor de la transacción
        receive: Receptor de la transacción
        amount: Cantidad de la transacción

        Va a devolver el identificador el bloque para el que se están
        recogiendo las transacciones
        """
        self.transactions.append({
            'sender': sender,
            'receiver': receiver,
            'amount': amount
        })

        return self.get_previous_block()['index'] + 1

    def add_node (self, address):
        """
        Añadirá un nodo dada una dirección a la lista de nodos

        address: dirección del nuevo nodo
        """
        # Se crea un objeto de tipo URL Parse que tiene varios atributos 
        # sobre la URL
        parsed_url = urlparse(address)
        # Nos quedamo solamente con la dirección. Se suprime el http o argumentos
        # que pueda tener la URL
        self.nodes.add(parsed_url.netloc)
    
    def replace_chain(self):
        """
        Función que se usará cuando un minero haya minado un bloque, y por lo tanto
        la cadena actual será más larga que la anterior. Por lo tanto, todos los
        demás mineros deberá actualizar la cadena por la nueva resultante
        """
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        # Recorremos toda la red y le vamos consultando a los mineros las 
        # longitudes de sus cadenas
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                # Si la longitud de una caden sobrepasa el valor actual máximo
                # y el bloque es válido, se actualiza
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        
        # Si al finalizar el bucle se ha encontrado alguna cadena mayor a la 
        # actualla reemplazamos y devolvemos True ya que se ha reemplazado la
        # cadena 
        if longest_chain:
            self.chain = longest_chain
            return True
        
        # En caso contrario devolvemos False ya que no se habría reemplazado
        # la cadena
        return False


# MINADO DE BLOQUES DE LA CADENA

# Creación de aplicación web
app = Flask(__name__)

# Crear la dirección del nodo en el puerto 5000
node_address = str(uuid4()).replace('-','')

# Creamos una instancia de la clase Blockchain
blockchain = Blockchain()

# Minado de un nuevo bloque
@app.route('/mine_block', methods=['GET'])

def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block.get('proof')
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender=node_address,
                               receiver='Michael Jordan',
                               amount=23)
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': 'Congrats. You have mine a new block',
                'index': block.get('index'),
                'timestamp': block.get('timestamp'),
                'proof': block.get('proof'),
                'previous_hash': block.get('previous_hash'),
                'transactions': block.get('transactions')
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

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all(key in json for key in transaction_keys):
        return 'Transacción incompleta. Faltan elementos', 400
    index = blockchain.add_transaction(sender=json['sender'],
                                       receiver=json['receiver'],
                                       amount=json['amount']
                                       )

    response = {'message': f'La transacción será añadida al bloque {index}'}
    return jsonify(response), 201


# DESCENTRALIZAR LA CADENA DE BLOQUES
# Para convertir la Cadena de Bloques en Criptomoneda se tiene que añadir:
#   - Añadir campo para las transacciones
#   - Añadir campo para el consenso

# Conectar nuevos nodos
@app.route('/connect_node', methods=['POST'])
def connect_node():
    """
    Por POST se va a pasar una lista de uno o varios nodos a dar de alta
    """
    json = request.get_json()
    nodes = json.get('nodes')
    if len(nodes) is None:
        return 'No se ha añadido ningún nodo', 400
    
    # En caso de que haya bloques que añadir, se van dando de alta
    for node in nodes:
        blockchain.add_node(address=node)

    response = {'message': 'Nodes connected successfully',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response, 201)

# Reemplazo de cadenas en caso de que haya una nueva cadena más larga
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()

    if is_chain_replaced:
        message = 'The chain has been updated'
    else:
        message = 'The chain is okay, it is not neccesary to be updated'
    response = {'message': message,
                'chain': blockchain.chain}
    return jsonify(response), 200        


# Ejecutar la app
app.run(host='0.0.0.0', port=5004)