import os
from textwrap import dedent
from typing import NamedTuple, Sequence

import pytest

from jockey.__main__ import main
from tests.test_util import SAMPLES_DIR, StandardOutputCapture


K8S_SAMPLE_PATH = os.path.join(SAMPLES_DIR, "k8s-core-juju-status.json")


class Case(NamedTuple):
    argv: Sequence[str]
    want_output: str
    want_code: int

    def __str__(self):
        return " ".join(self.argv)


SUPPORTED_CASES = [
    Case(
        ["-f", K8S_SAMPLE_PATH, "u"],
        """
        easyrsa/0
        etcd/0
        kubernetes-control-plane/0
        calico/1
        containerd/1
        kubernetes-worker/0
        calico/0
        containerd/0
        """,
        0,
    ),
    Case(
        ["-f", K8S_SAMPLE_PATH, "m"],
        """
        0
        0/lxd/0
        1
        """,
        0,
    ),
]


UNSUPPORTED_CASES = []


@pytest.mark.parametrize("case", SUPPORTED_CASES)
def test_cli(case: Case):
    (argv, want_output, want_code) = case

    with StandardOutputCapture() as got_output_lines:
        got_code = main(argv)

    assert want_code == got_code
    assert dedent(want_output).strip() == "\n".join(got_output_lines).strip()
