from io import StringIO
import os
import sys


TESTS_DIR = os.path.dirname(os.path.realpath(__file__))
SAMPLES_DIR = os.path.join(TESTS_DIR, "samples")


class StandardOutputCapture(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio
        sys.stdout = self._stdout
