# src/borg/testsuite/archiver/conftest.py
import pytest
from borg.archiver.transfer_cmd import BRANCHES_TAKEN

ALL_TRANSFER_BRANCHES = {
    "1_true",
    "1_false",
    "2_true",
    "2_false",
    "3_true",
    "3_false",
    "4_true",
    "4_false",
    "5_true",
    "5_false",
    "6_true",
    "6_false",
    "7_true",
    "7_false",
    "8_true",
    "8_false",
    "9_true",
    "9_false",
    "10_true",
    "10_false",
    "11_true",
    "12_true",
    "13_true",
    "14_true",
    "14_false",
    "15_true",
    "15_false",
    "16_true",
    "16_elif",
    "16_false",
    "17_true",
    "17_false",
    "18_true",
    "18_false",
    "19_true",
    "19_false",
    "20_true",
    "20_false",
    "21_true",
    "21_false",
}


@pytest.fixture(autouse=True, scope="module")
def transfer_branch_tracker(request):
    if "transfer_cmd_test" not in request.fspath.basename:
        yield
        return

    BRANCHES_TAKEN.clear()
    yield


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if not BRANCHES_TAKEN:
        return

    covered = BRANCHES_TAKEN & ALL_TRANSFER_BRANCHES
    missing = ALL_TRANSFER_BRANCHES - covered
    total = len(ALL_TRANSFER_BRANCHES)
    pct = 100 * len(covered) / total

    terminalreporter.write_sep("-", "Transfer branch coverage")
    terminalreporter.write_line(f"Covered:  {sorted(covered)}")
    terminalreporter.write_line(f"Missing:  {sorted(missing)}")
    terminalreporter.write_line(f"Coverage: {len(covered)}/{total} ({pct:.1f}%)")
