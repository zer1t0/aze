import sys
from uuid import UUID

def add_b64_padding(data):
    padding_len = (4 - (len(data) % 4)) % 4
    return data + "=" * padding_len

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# from https://stackoverflow.com/questions/53847404/how-to-check-uuid-validity-in-python#answer-33245493
def is_valid_uuid(uuid_to_test, version=4):
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test
