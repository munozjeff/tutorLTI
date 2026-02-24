from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import os

def generate_keys(key_dir="."):
    """Generate RSA private and public keys for LTI signing"""
    print(f"Generating keys in {os.path.abspath(key_dir)}...")
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    # Serialize private key
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Serialize public key
    public_key = private_key.public_key()
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Write private key
    with open(os.path.join(key_dir, "private.pem"), "wb") as f:
        f.write(pem_private)
    
    # Write public key
    with open(os.path.join(key_dir, "public.pem"), "wb") as f:
        f.write(pem_public)
        
    print("Keys generated successfully!")

if __name__ == "__main__":
    # If running as script, put in parent dir or specified location
    output_dir = os.environ.get('KEY_DIR', '..')
    generate_keys(output_dir)
