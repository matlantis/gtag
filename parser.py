#!/usr/bin/env python3
import pyparsing as pp
import unittest

import tree

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
        self.rules.parseString(text)
        return self.tree

    def _defineRules(self):
        """
        Creates the parsing rules and returns the defines ParseElement.
        (see pyparsing.py)
        """
        thetree = tree.Tree()
        # define custom actions
        thetree.pp_addAtom = lambda toks: thetree.addAtom(toks[0])
        thetree.pp_addOp = lambda toks: thetree.addOp(toks[0])

        atom = pp.Word(pp.alphanums)
        op = ( pp.Literal("|") ^ pp.Literal("&") )
        node = pp.Forward()
        signed_node = node ^ ("!" + node).setParseAction(thetree.addNot)
        node << ( atom.setParseAction(thetree.pp_addAtom)
            ^ ( "(" + ( signed_node + op.setParseAction(thetree.pp_addOp) + signed_node )
            + ")" ) ).setParseAction(thetree.addNode)

        return [signed_node, thetree]

class ParserTest(unittest.TestCase):
    def test_parse(self):
        parser = Parser()
        text = "   ! ( ! (Music  | Photo )| Jara  )    "
        parser.scan(text)
        self.assertEqual(str(parser.tree).replace(" ", ""), text.replace(" ", ""))
