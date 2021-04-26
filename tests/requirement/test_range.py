import pytest

from brakeman.requirement.vrange import VRange


@pytest.fixture
def in_range_data():
    return {
        VRange().ge(0): {
            -1: False,
            0: True,
            1: True
        },
        VRange().gt(0): {
            -1: False,
            0: False,
            1: True
        },
        VRange().le(0): {
            -1: True,
            0: True,
            1: False
        },
        VRange().lt(0): {
            -1: True,
            0: False,
            1: False
        }
    }


def test_in_range(in_range_data):
    for vr, d in in_range_data.items():
        for v, exp in d.items():
            assert vr.in_range(v) == exp


@pytest.fixture
def overlap_data():
    vrs = [VRange().close(0, 1), VRange().open(0, 1), VRange().lt(0), VRange().le(0), VRange().ge(1), VRange().gt(1)]
    res = [
        [True, True, False, True, True, False],
        [True, True, False, False, False, False],
        [False, False, True, True, False, False],
        [True, False, True, True, False, False],
        [True, False, False, False, True, True],
        [False, False, False, False, True, True]
    ]

    return vrs, res


def test_overlap(overlap_data):
    vrs, res = overlap_data

    for i, vi in enumerate(vrs):
        for j, vj in enumerate(vrs):
            assert vi.is_intersected(vj) == res[i][j]


def test_overlap2():
    vr1 = VRange().open(1, 2)
    vr2 = VRange().open(0, 5)
    assert vr1.is_intersected(vr2)
    assert vr2.is_intersected(vr1)

def test_intersect():
    vr1 = VRange().open(1, 2)
    vr2 = VRange().open(0, 5)
    inter = vr1.intersection(vr2)
    assert str(inter) == '(1, 2)'
