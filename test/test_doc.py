from talonfmt.prettyprinter.doc import *


def test_Text_intern_Empty():
    assert Empty is Text("")
    assert Empty is Text.intern_Empty()
    assert Empty.is_Empty()
    assert repr(Empty) == "Empty"


def test_Text_intern_Space():
    assert Space is Text(" ")
    assert Space is Text.intern_Space()
    assert Space.is_Space()
    assert repr(Space) == "Space"


def test_Text_intern_Line():
    assert Line is Text("\n")
    assert Line is Text.intern_Line()
    assert Line.is_Line()
    assert repr(Line) == "Line"


def test_Alt_intern_Fail():
    assert Fail is Alt(alts=())
    assert Fail is Alt.intern_Fail()
    assert Fail.is_Fail()
    assert repr(Fail) == "Fail"


def test_Alt_intern_SoftLine():
    assert SoftLine is Alt(alts=(Line, Empty))
    assert SoftLine is Alt.intern_SoftLine()
    assert SoftLine.is_SoftLine()
    assert repr(SoftLine) == "SoftLine"


def test_DocLike_Line():
    assert cat("hello\nworld") == cat("hello", Line, "world")


def test_DocLike_Space():
    assert cat("hello world") == cat("hello", Space, "world")


def test_DocLike_Line_and_Space():
    cat1 = cat("hello world\nwello horld")
    cat2 = cat("hello", Space, "world", Line, "wello", Space, "horld")
    assert cat1 == cat2
