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


CASES = [
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
        [
            "-f",
            K8S_SAMPLE_PATH,
            "unit.public-address",
            "@machine.hostname=juju-36490e-1",
            "workload-status.current~block",
            "name%container",
        ],
        "10.118.249.130",
        0,
    ),
    Case(
        [
            "-f",
            K8S_SAMPLE_PATH,
            "machine.hardware",
        ],
        """
        arch=amd64 cores=2 mem=8192M virt-type=container
        None
        arch=amd64 cores=2 mem=8192M virt-type=container
        """,
        0,
    ),
    Case(
        ["-f", K8S_SAMPLE_PATH, "app,base", "charm=kubernetes-control-plane"],
        """
        {'name': 'ubuntu', 'channel': '22.04'}
        """,
        0,
    ),
    Case(
        ["-f", K8S_SAMPLE_PATH, "app.name,base", "charm=kubernetes-control-plane"],
        """
        ['kubernetes-control-plane', {'name': 'ubuntu', 'channel': '22.04'}]
        """,
        0,
    ),
]


@pytest.mark.parametrize("case", CASES)
def test_cli(case: Case):
    (argv, want_output, want_code) = case

    with StandardOutputCapture() as got_output_lines:
        got_code = main(argv)

    assert want_code == got_code
    assert dedent(want_output).strip() == "\n".join(got_output_lines).strip()
