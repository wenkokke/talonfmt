from talon_fmt.prettyprinter.doc import *


def test_Empty_singleton():
    assert Empty is EmptyType()


def test_Empty_repr():
    assert repr(Empty) == "Empty"


def test_Line_singleton():
    assert Line is LineType()


def test_Line_repr():
    assert repr(Line) == "Line"


def test_SoftLine_singleton():
    assert SoftLine is (Empty | Line)


def test_SoftLine_repr():
    assert repr(SoftLine) == "SoftLine"


def test_Alt_repr():
    assert repr(Line | Empty) == "Line | Empty"


def test_Text_Empty():
    assert Empty is Text("")


def test_Text_intern_Space():
    assert Space is Text(" ")


def test_to_doc():
    assert to_doc("hello\nworld") == Cat((Text(text="hello"), Line, Text(text="world")))
