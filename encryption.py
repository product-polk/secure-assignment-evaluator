import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import json
import hashlib

# Generate a stable encryption key based on the assignment ID
def generate_key_from_id(assignment_id):
    """Generate a stable encryption key based on the assignment ID"""
    # Use a fixed salt for deterministic keys based on ID
    salt = os.environ.get('ENCRYPTION_SALT', 'secure-evaluator-salt').encode()
    
    # Generate a key using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    # Use assignment_id as the password for key derivation
    key = base64.urlsafe_b64encode(kdf.derive(assignment_id.encode()))
    return key

def encrypt_file(file_data, assignment_id):
    """Encrypt file data using the assignment ID"""
    key = generate_key_from_id(assignment_id)
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(file_data)
    return encrypted_data

def decrypt_file(encrypted_data, assignment_id):
    """Decrypt file data using the assignment ID"""
    key = generate_key_from_id(assignment_id)
    fernet = Fernet(key)
    decrypted_data = fernet.decrypt(encrypted_data)
    return decrypted_data

def encrypt_data(data, assignment_id):
    """Encrypt any JSON-serializable data"""
    # Convert data to JSON string
    json_data = json.dumps(data).encode()
    return encrypt_file(json_data, assignment_id)

def decrypt_data(encrypted_data, assignment_id):
    """Decrypt data back to its original form"""
    json_data = decrypt_file(encrypted_data, assignment_id)
    return json.loads(json_data)

def secure_file_path(assignment_id):
    """Create a secure file path based on assignment ID"""
    # Create a hash of the assignment ID to obscure the actual file name
    hashed_id = hashlib.sha256(assignment_id.encode()).hexdigest()
    return os.path.join('data', f"{hashed_id}.enc")