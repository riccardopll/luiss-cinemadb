import sys

import bcrypt

print(bcrypt.hashpw(sys.argv[1].encode(), bcrypt.gensalt()).decode())
