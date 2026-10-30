"""Keep release packages written by tests out of the real content/releases folder."""
import os
import tempfile

os.environ.setdefault("RELEASE_STORAGE_PATH", tempfile.mkdtemp(prefix="sarmaan-test-releases-"))
