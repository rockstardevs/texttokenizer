from pathlib import Path

import pytest

from texttokenizer.util import (
    expand_page_list,
    flag_composer,
    flags_decomposer,
    suffix_path,
)


def test_suffix_path():
    src_path = Path("/root/test.pdf")
    assert suffix_path(src_path, "foo") == Path("/root/test-foo.pdf")
    assert suffix_path(src_path, "bar", ext=".json") == Path("/root/test-bar.json")


def test_expand_page_list():
    assert expand_page_list("", 0) == [0]
    assert expand_page_list("0", 0) == [0]
    assert expand_page_list("", 3) == [0, 1, 2, 3]
    assert expand_page_list("1,3-4", 5) == [1, 3, 4]
    assert expand_page_list("3-4,1", 5) == [1, 3, 4]
    assert expand_page_list("1,3-4", 3) == [1, 3]
    assert expand_page_list("3-4", 4) == [3, 4]
    with pytest.raises(ValueError):
        expand_page_list("-", 4)


def test_flag_composer():
    assert flag_composer({}) == 0
    assert flag_composer({"superscript": True}) == 1
    assert flag_composer({"superscript": False}) == 0
    assert flag_composer({"serif": True, "bold": False}) == 4
    assert flag_composer({"serif": False, "bold": True}) == 16
    assert flag_composer({"serif": True, "bold": True}) == 20


def test_flag_decomposer():
    assert flags_decomposer(0) == {
        "bold": False,
        "italic": False,
        "mono": False,
        "proportional": True,
        "sans": True,
        "serif": False,
        "superscript": False,
    }
    assert flags_decomposer(1) == {
        "bold": False,
        "italic": False,
        "mono": False,
        "proportional": True,
        "sans": True,
        "serif": False,
        "superscript": True,
    }
    assert flags_decomposer(4) == {
        "bold": False,
        "italic": False,
        "mono": False,
        "proportional": True,
        "sans": False,
        "serif": True,
        "superscript": False,
    }
    assert flags_decomposer(16) == {
        "bold": True,
        "italic": False,
        "mono": False,
        "proportional": True,
        "sans": True,
        "serif": False,
        "superscript": False,
    }
    assert flags_decomposer(20) == {
        "bold": True,
        "italic": False,
        "mono": False,
        "proportional": True,
        "sans": False,
        "serif": True,
        "superscript": False,
    }
