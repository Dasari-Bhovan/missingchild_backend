import os

# Generate a secure secret key
secret_key = os.urandom(24).hex()

print("Generated Secret Key:", secret_key)
