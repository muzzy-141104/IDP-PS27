import os
import sys

# Add project root to path
sys.path.append(os.path.abspath('.'))

from drishti.backend.supabase_client import upload_to_storage

# create a dummy file
with open('dummy.jpg', 'wb') as f:
    f.write(b'dummy content')

url = upload_to_storage('dummy.jpg')
print(f"Upload URL: {url}")
