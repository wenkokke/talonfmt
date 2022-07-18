from talon_fmt.prettyprinter.doc import *


def test_Text_intern_Empty():
    assert Empty is Text("")


def test_Text_intern_Space():
    assert Space is Text(" ")


def test_Text_intern_Line():
    assert Line is Text("\n")


def test_Empty_repr():
    assert repr(Empty) == "Empty"


def test_Space_repr():
    assert repr(Space) == "Space"


def test_Line_repr():
    assert repr(Line) == "Line"


def test_DocLike_Line():
    assert cat("hello\nworld") == cat("hello", Line, "world")

def test_DocLike_Space():
    assert cat("hello world") == cat("hello", Space, "world")
