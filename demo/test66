import subprocess
import hashlib

def run_cmd(user_input):
    subprocess.run(user_input, shell=True) # Command Injection!

def hash_pass(pwd):
    return hashlib.md5(pwd.encode()).hexdigest() # Weak MD5 Hash!
