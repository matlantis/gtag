#!/usr/bin/env python3
import unittest

class Node:
    """
    A Node is either a normal node or a Not-Node, if Not is True.
    It can be a LEAF or an OPERATOR. In the last case is has got
    two children.
    """
    LEAF = 0
    OPERATOR = 1

    def __init__(self, sams, stat):
        self.key = sams
        self.LeafOp = stat
        self.Not = False
        self.leftChild = 0
        self.rightChild = 0

    def __str__(self):
        ans = ""
        if self.Not:
            ans = "!"
        if ( self.LeafOp == self.LEAF ):
            ans += str(self.key)
        else:
            ans += "({} {} {})".format(self.leftChild, self.key, self.rightChild)
        return ans

    def addNot(self):
        self.Not = not self.Not

    def lowerNot(self):
        """Lowers all Not Signs in the subtree down to the leafs."""
        if self.LeafOp == self.LEAF:
            return
        if self.Not == True:
            self.Not = False
            if self.key == "&":
                self.key = "|"
            elif self.key == "|":
                self.key = "&"
            else:
                print("unknown Operator.")
            self.leftChild.addNot()
            self.leftChild.lowerNot()
            self.rightChild.addNot()
            self.rightChild.lowerNot()

    def liftOr(self):
        if self.key == "&":
            if self.leftChild.key == "|" and self.rightChild.key != "|":
                self.key = "|"
                leftNode = self.leftChild
                rightNode = self.rightChild
                self.leftChild = Node("&", self.OPERATOR)
                self.leftChild.leftChild = leftNode.leftChild
                self.leftChild.rightChild = rightNode

                self.rightChild = Node("&", self.OPERATOR)
                self.rightChild.rightChild = rightNode
                self.rightChild.leftChild = leftNode.rightChild
                return True
            elif self.leftChild.key != "|" and self.rightChild.key == "|":
                self.key = "|"
                leftNode = self.leftChild
                rightNode = self.rightChild
                self.leftChild = Node("&", self.OPERATOR)
                self.leftChild.leftChild = leftNode
                self.leftChild.rightChild = rightNode.leftChild

                self.rightChild = Node("&", self.OPERATOR)
                self.rightChild.leftChild = leftNode
                self.rightChild.rightChild = rightNode.rightChild
                return True
            elif self.leftChild.key == "|" and self.rightChild.key == "|":
                self.key = "|"
                leftNode = self.leftChild
                rightNode = self.rightChild
                self.leftChild = Node("|", self.OPERATOR)

                self.leftChild.leftChild = Node("&", self.OPERATOR)
                self.leftChild.leftChild.leftChild = leftNode.leftChild
                self.leftChild.leftChild.rightChild = rightNode.leftChild

                self.leftChild.rightChild = Node("&", self.OPERATOR)
                self.leftChild.rightChild.leftChild = leftNode.rightChild
                self.leftChild.rightChild.rightChild = rightNode.rightChild

                self.rightChild = Node("|", self.OPERATOR)

                self.rightChild.leftChild = Node("&", self.OPERATOR)
                self.rightChild.leftChild.leftChild = leftNode.rightChild
                self.rightChild.leftChild.rightChild = rightNode.leftChild

                self.rightChild.rightChild = Node("&", self.OPERATOR)
                self.rightChild.rightChild.leftChild = leftNode.leftChild
                self.rightChild.rightChild.rightChild = rightNode.rightChild
                return True
            else:
                return ( self.leftChild.liftOr() or self.rightChild.liftOr() )
        elif self.key == "|":
            return ( self.leftChild.liftOr() or self.rightChild.liftOr() )
        else:
            return False

class Tree:
    """Defines a tree representing the feature list."""
    verbose = False

    def __init__(self):
        self.hasFreeAtom = False
        self.atom = 0
        self.NodeStack = []
        self.OpStack = []

    def __str__(self):
        if self.NodeStack == []:
            return "Baum ist leer"
        return str(self.NodeStack[0])

    def clear(self):
        """Deletes the tree"""
        self.atom = None
        self.NodeStack = []
        self.OpStack = []

    # def addOp(self, sams, loc, toks):
    def addOp(self, op):
        """Adds one of & and | to the OpStack."""
        if self.verbose:
            print("Add Op: " + str(op))
        self.OpStack.append(op)

    def addNot(self):
        """Makes the last node on NodeStack a Not-Node"""
        if self.verbose:
            print("add not")
        if len(self.NodeStack) > 0:
            self.NodeStack[-1].Not = True
        else:
            raise Exception("no node on stack to negate")

    def addNode(self):
        """
        Creates a node of either the actual atom or
        the last two nodes on NodeStack and the last op on
        OpStack.
        """
        if self.verbose:
            print("new Node")
        if self.atom:
            newNode = Node(self.atom, Node.LEAF)
            self.NodeStack.append(newNode)
            self.atom = None
        elif ( len(self.OpStack) > 0 and len(self.NodeStack) > 1):
            newNode = Node(self.OpStack.pop(),Node.OPERATOR)
            newNode.rightChild = self.NodeStack.pop()
            newNode.leftChild = self.NodeStack.pop()
            self.NodeStack.append(newNode)
        else:
            raise Exception("no atom present and either no op or no two nodes on stack to create new node")

    def addAtom(self, content):
        """Sets atom to a single atom."""
        self.atom = content
        if self.verbose:
            print("add Atom: {}".format(self.atom))

    def _lowerNot(self):
        """Lowers all Not Signs in the tree down to the leafs."""
        if self.NodeStack != []:
            self.NodeStack[0].lowerNot()

    def _liftOr(self):
        """Lifts all Or-Operators in the tree as highest as possible."""
        if self.NodeStack != []:
            while ( self.NodeStack[0].liftOr() ):
                pass

    def normalize(self):
        self._lowerNot()
        self._liftOr()

class TagSpecTest(unittest.TestCase):
    def setUp(self):
        """
        Create a highly unnormalized tree, normalize and compare output. Lets use:
        "! ( !( Music | Photo ) | Jara )"
        """
        self.tree = Tree()
        self.tree.addAtom("Music")
        self.tree.addNode()
        self.tree.addAtom("Photo")
        self.tree.addNode()
        self.tree.addOp("|")
        self.tree.addNode()
        self.tree.addNot()
        self.tree.addAtom("Jara")
        self.tree.addNode()
        self.tree.addOp("|")
        self.tree.addNode()
        self.tree.addNot()

    def test_output(self):
        """
        Just check the output
        """
        self.assertEqual(str(self.tree), "!(!(Music | Photo) | Jara)")

    def test_normalize(self):
        self.tree.normalize()
        self.assertEqual(str(self.tree), "((Music & !Jara) | (Photo & !Jara))")

