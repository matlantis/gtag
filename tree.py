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
            ans = ans + "!"
        ans = ans + "("
        if ( self.LeafOp == self.LEAF ):
            ans = ans + str(self.key)
        else:
            ans = ans + str(self.leftChild) + " " + str(self.key) + " " + str(self.rightChild)
        ans = ans + ")"
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

#    def fusionateKeyNot(self):
#        """appends a '!' to each feature which is in a not-leaf"""
#        if self.LeafOp == self.LEAF:
#            if self.Not:
#                self.key = "!" + self.key
#            return
#        self.leftChild.fusionateKeyNot()
#        self.rightChild.fusionateKeyNot()

class Tree:
    """Defines a tree representing the feature list."""
    verbose = False

    def __init__(self):
        self.hasFreeAtom = False
        self.actAtom = 0
        self.NodeStack = []
        self.OpStack = []

    def __str__(self):
        if self.NodeStack == []:
            return "Baum ist leer"
        return str(self.NodeStack[0])

    def clear(self):
        """Deletes the tree"""
        self.hasFreeAtom = False
        self.actAtom = 0
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
        if self.hasFreeAtom:
            newNode = Node(self.actAtom, Node.LEAF)
            self.NodeStack.append(newNode)
            self.hasFreeAtom = False
        elif ( len(self.OpStack) > 0 and len(self.NodeStack) > 1):
            newNode = Node(self.OpStack.pop(),Node.OPERATOR)
            newNode.rightChild = self.NodeStack.pop()
            newNode.leftChild = self.NodeStack.pop()
            self.NodeStack.append(newNode)
        else:
            raise Exception("no atom present and either no op or no two nodes on stack to create new node")

    def addAtom(self, content):
        """Sets actAtom to a single atom."""
        self.actAtom = content
        if self.verbose:
            print("add Atom: {}".format(self.actAtom))
        self.hasFreeAtom = True

    def lowerNot(self):
        """Lowers all Not Signs in the tree down to the leafs."""
        if self.NodeStack != []:
            self.NodeStack[0].lowerNot()

    def liftOr(self):
        """Lifts all Or-Operators in the tree as highest as possible."""
        if self.NodeStack != []:
            while ( self.NodeStack[0].liftOr() ):
                pass

    def liftOrlowerNot(self):
        self.lowerNot()
        self.liftOr()

class TagSpecTest(unittest.TestCase):
    def test_addsomenodesandops(self):
        """
        Create a Tree and put this one on: "Music | (!Photo & Jara)"
        """ 
        tree = Tree()
        tree.addAtom("Music")
        tree.addNode()
        tree.addAtom("Photo")
        tree.addNode()
        tree.addNot()
        tree.addAtom("Jara")
        tree.addNode()
        tree.addOp("&")
        tree.addNode()
        tree.addOp("|")
        tree.addNode()
        self.assertEqual(str(tree), "((Music) | (!(Photo) & (Jara)))")

if __name__ == "__main__":
    example()
