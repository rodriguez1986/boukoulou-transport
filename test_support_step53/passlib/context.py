"""TEST ONLY: only permits importing JWT code; password methods unavailable."""
class CryptContext:
    def __init__(self, *args, **kwargs): pass
    def hash(self, *args, **kwargs):
        raise RuntimeError('Test shim: no password hashing support')
    def verify(self, *args, **kwargs):
        raise RuntimeError('Test shim: no password verification support')
