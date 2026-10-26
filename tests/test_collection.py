""" RDF-: the Collection shape expression, ((shapeExpr))[min, max].

A sequence term `(1 2 3)` is one RDF node; a Collection says how many elements it has and what each
must conform to.  `[m]` is exactly m elements, `[m, n]` from m to n, `[m, *]` or `[m,]` at least m,
no bounds any length.  `((x))` is always a Collection; `(x)` is still a parenthesised shape expression.
"""
import json

from ShExJSG import ShExJ

from pyshexc.ShExC import ShExC
from pyshexc.parser_impl.generate_shexj import parse

BASE = "http://a.example/"


def shape_expr_of(text: str):
    """ the first shape's expression: in this ShExJ, a declaration is the expression itself with an id """
    schema = parse(text, BASE)
    assert schema is not None, text
    return schema.shapes[0]


def collection(shape_expr, **bounds):
    return ShExJ.Collection(id=ShExJ.IRIREF(BASE + "S"), shapeExpr=shape_expr, **bounds)


def as_dict(obj):
    return json.loads(obj._as_json)


def test_each_form_of_bounds():
    dt = ShExJ.NodeConstraint(datatype=ShExJ.IRIREF(BASE + "T"))
    assert as_dict(shape_expr_of("<S> ((<T>))")) == as_dict(collection(dt))
    assert as_dict(shape_expr_of("<S> ((<T>))[2]")) == as_dict(collection(dt, min=2, max=2))
    assert as_dict(shape_expr_of("<S> ((<T>))[2, 3]")) == as_dict(collection(dt, min=2, max=3))
    assert as_dict(shape_expr_of("<S> ((<T>))[1, *]")) == as_dict(collection(dt, min=1, max=-1))
    assert as_dict(shape_expr_of("<S> ((<T>))[1,]")) == as_dict(collection(dt, min=1, max=-1))
    assert as_dict(shape_expr_of("<S> (( <T> )) [ 0 , 1 ]")) == as_dict(collection(dt, min=0, max=1))


def test_any_shape_expression_and_nesting():
    se = shape_expr_of("<S> ((@<T> OR IRI))[0, 1]")
    assert isinstance(se, ShExJ.Collection) and isinstance(se.shapeExpr, ShExJ.ShapeOr)
    assert (se.min, se.max) == (0, 1)
    se = shape_expr_of("<S> ((((<T>))[2]))[1, *]")
    assert isinstance(se, ShExJ.Collection) and isinstance(se.shapeExpr, ShExJ.Collection)
    assert (se.shapeExpr.min, se.shapeExpr.max, se.min, se.max) == (2, 2, 1, -1)
    assert isinstance(shape_expr_of("<S> ((@<T>))").shapeExpr, str)
    assert isinstance(shape_expr_of("<S> (({ <p> . }))").shapeExpr, ShExJ.Shape)


def test_is_a_shape_atom():
    se = shape_expr_of("<S> NOT ((<T>))")
    assert isinstance(se, ShExJ.ShapeNot) and isinstance(se.shapeExpr, ShExJ.Collection)
    se = shape_expr_of("<S> ((<T>))[2] OR IRI")
    assert isinstance(se, ShExJ.ShapeOr) and isinstance(se.shapeExprs[0], ShExJ.Collection)
    se = shape_expr_of("<S> { <p> ((<T>))[3] ; <q> NOT ((@<T>)) {2} }")
    tcs = se.expression.expressions
    assert isinstance(tcs[0].valueExpr, ShExJ.Collection) and (tcs[0].valueExpr.min, tcs[0].valueExpr.max) == (3, 3)
    assert isinstance(tcs[1].valueExpr, ShExJ.ShapeNot) and isinstance(tcs[1].valueExpr.shapeExpr, ShExJ.Collection)


def test_parentheses_stay_parentheses():
    # (a parenthesised expression at the top of a declaration, `<S> (<T>)`, yields no schema in
    # PyShExC before and after this change; the inline forms below are what schemas write)
    tc = shape_expr_of("<S> { <p> (<T>) }").expression
    assert isinstance(tc.valueExpr, ShExJ.NodeConstraint)
    tc = shape_expr_of("<S> { <p> ((<T>) OR BNODE) }").expression
    assert isinstance(tc.valueExpr, ShExJ.ShapeOr) and "Collection" not in tc.valueExpr._as_json
    tc = shape_expr_of("<S> { <p> (((<T>))) }").expression
    assert isinstance(tc.valueExpr, ShExJ.Collection), "parentheses around a Collection"
    se = shape_expr_of("<S> ((<T>))[2] AND (<T>)")
    assert isinstance(se, ShExJ.ShapeAnd) and isinstance(se.shapeExprs[0], ShExJ.Collection) \
        and isinstance(se.shapeExprs[1], ShExJ.NodeConstraint)


def test_malformed_bounds_are_rejected():
    for text in ["<S> ((<T>))[*]", "<S> ((<T>))[1 2]", "<S> ((<T>))[,1]", "<S> ((<T>))[1, 2, 3]", "<S> ((<T>))[]"]:
        assert parse(text, BASE) is None, text


def test_round_trips_through_the_writer():
    for text in ["<S> ((<T>))[2, 3]", "<S> ((@<T> OR IRI))[1, *]", "<S> ((((LITERAL))[2]))",
                 "<S> NOT ((<T>)) AND ((BNODE))[0, 1]", "<S> { <p> ((<T>))[3] ; <p> ((@<S>)) {2} }",
                 "<S> NOT (<T> AND IRI)"]:
        once = parse(text, BASE)
        written = str(ShExC(once))
        again = parse(written, BASE)
        assert again is not None, f"{text}\n  -> {written}"
        assert as_dict(again) == as_dict(once), f"{text}\n  -> {written}"


def test_dot_is_the_empty_shape():
    """ `((.))`: as in ShExJ, `.` is {"type": "Shape"}, so any element conforms """
    assert as_dict(shape_expr_of("<S> ((.))")) == as_dict(collection(ShExJ.Shape()))
    assert as_dict(shape_expr_of("<S> ((.))[0, *]")) == as_dict(collection(ShExJ.Shape(), min=0, max=-1))
