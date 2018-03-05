#!/usr/bin/env python3
import pyparsing as pp
import unittest

import tree

class ParserTree(tree.Tree):
    def __init__(self):
        tree.Tree.__init__(self)

    def pp_addAtom(self, text, loc, toks):
        print("Atom")
        print("text: {}, loc: {}, toks: {}".format(text, loc, toks))
        super().addAtom(toks[0])

    def pp_addAtomNode(self, text, loc, toks):
        print("AtomNode")
        print("text: {}, loc: {}, toks: {}".format(text, loc, toks))
        super().addAtom(toks[0])
        super().addNode()

    def pp_addOp(self, text, loc, toks):
        print("Op")
        print("text: {}, loc: {}, toks: {}".format(text, loc, toks))
        super().addOp(toks[0])

    def pp_addNode(self, text, loc, toks):
        print("Node")
        print("text: {}, loc: {}, toks: {}".format(text, loc, toks))
        super().addNode()

    def pp_addNot(self, text, loc, toks):
        print("Not")
        print("text: {}, loc: {}, toks: {}".format(text, loc, toks))
        super().addNot()

class Parser:
    """
    Defines the parsing rules. Attention: The parse results will be stored
    in the list trees. Further parsing will append its results
    to the list. So you get the entire list of older results if you look
    into trees.
    """

    def __init__(self):
        [self.rules, self.tree] = self._defineRules()

    def scan(self, text):
        """Scan a given text. Returns a list with the resulting trees."""
        for data, start, end in self.rules.scanString(text):
            pass
        return self.tree

    def parse(self, text):
        """Parses a given text. Returns a list with the resulting trees."""
        print(self.rules.parseString(text))
        return self.tree

    def _defineRules(self):
        """
        Creates the parsing rules and returns the defines ParseElement.
        (see pyparsing.py)
        """
        thetree = ParserTree()

        # # Forwards
        # paren_signed_node = pp.Forward()
        # more_paren_signed_node = paren_signed_node ^ ( "(" + paren_signed_node + ")")

        # atom_node = pp.Word(pp.alphanums).setParseAction(thetree.pp_addAtomNode)
        # op = ( pp.Literal("|") ^ pp.Literal("&") ).setParseAction(thetree.pp_addOp)
        # term_node = ( "(" + more_paren_signed_node + op + more_paren_signed_node + ")").setParseAction(thetree.pp_addNode)
        # node = atom_node ^ term_node
        # signed_node = node ^ ("!" + node).setParseAction(thetree.pp_addNot)
        # paren_signed_node << signed_node ^ ( "(" + signed_node + ")")

        # parens
        lparen = pp.Literal("(").suppress()
        rparen = pp.Literal(")").suppress()

        # Forwards
        paren_signed_node = pp.Forward()

        atom_node = pp.Word(pp.alphanums).setParseAction(thetree.pp_addAtomNode)
        op = ( pp.Literal("|") | pp.Literal("&") ).setParseAction(thetree.pp_addOp)
        term_node = pp.Group(( lparen + paren_signed_node + op + paren_signed_node + rparen ).setParseAction(thetree.pp_addNode))
        node = ( atom_node | term_node )
        signed_node = ( node | pp.Group(("!" + node).setParseAction(thetree.pp_addNot)) )
        paren_signed_node << ( signed_node | ( lparen + paren_signed_node + rparen ) )

        term = paren_signed_node
        return [term, thetree]

    def clear(self):
        self.tree.clear()

class ParserTest(unittest.TestCase):
    # def test_parse_without_parens(self):
    #     parser = Parser()
    #     text = " hund | katz   "
    #     parser.scan(text)
    #     self.assertEqual(str(parser.tree).replace(" ", ""), text.replace(" ", ""))
    def test_parse1(self):
        parser = Parser()
        text = "Music"
        parser.parse(text)
        self.assertEqual(str(parser.tree).replace(" ", ""), "Music")

    def test_parse2(self):
        parser = Parser()
        text = "  Music   "
        parser.parse(text)
        self.assertEqual(str(parser.tree).replace(" ", ""), "Music")

    def test_parse3(self):
        parser = Parser()
        text = "!Music"
        parser.parse(text)
        self.assertEqual(str(parser.tree).replace(" ", ""), "!Music")

    def test_parse4(self):
        parser = Parser()
        text = "(Music)"
        parser.parse(text)
        self.assertEqual(str(parser.tree).replace(" ", ""), "Music")

    def test_parse5(self):
        parser = Parser()
        text = "(!Music)"
        parser.parse(text)
        self.assertEqual(str(parser.tree).replace(" ", ""), "!Music")

    def test_parse6(self):
        parser = Parser()
        text = "((Music))"
        parser.parse(text)
        self.assertEqual(str(parser.tree).replace(" ", ""), "Music")

    def test_parse7(self):
        parser = Parser()
        text = "(!(Music))"
        parser.parse(text)
        self.assertEqual(str(parser.tree).replace(" ", ""), "Music")

    # def test_parse(self):
    #     parser = Parser()
    #     text = "   ! ( ! ( (Music)  | Photo )| Jara  )    "
    #     parser.parse(text)
    #     self.assertEqual(str(parser.tree).replace(" ", ""), text.replace(" ", ""))
