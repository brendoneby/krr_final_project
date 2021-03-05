import unittest
import read, copy
from logical_classes import *
from knowledgebase import KnowledgeBase

class KBTest(unittest.TestCase):

    def setUp(self):
        self.KB = KnowledgeBase([], [], 'statements_kb4.txt')

    def test1(self):
        ask1 = read.parse_input("fact: (motherof ada ?X)")
        print(' Asking if', ask1)
        answer = self.KB.kb_ask(ask1)
        self.assertEqual(str(answer[0]), "?X : bing")

    def test2(self):
        ask1 = read.parse_input("fact: (grandmotherof ada ?X)")
        print(' Asking if', ask1)
        answer = self.KB.kb_ask(ask1)
        self.assertEqual(str(answer[0]), "?X : felix")
        self.assertEqual(str(answer[1]), "?X : chen")

    def test3(self):
        r1 = read.parse_input("fact: (motherof ada bing)")
        print(' Retracting', r1)
        self.KB.kb_retract(r1)
        ask1 = read.parse_input("fact: (grandmotherof ada ?X)")
        print(' Asking if', ask1)
        answer = self.KB.kb_ask(ask1)
        self.assertEqual(str(answer[0]), "?X : felix")

    def test4(self):
        r1 = read.parse_input("fact: (grandmotherof ada chen)")
        print(' Retracting', r1)
        self.KB.kb_retract(r1)
        ask1 = read.parse_input("fact: (grandmotherof ada ?X)")
        print(' Asking if', ask1)
        answer = self.KB.kb_ask(ask1)
        self.assertEqual(str(answer[0]), "?X : felix")
        self.assertEqual(str(answer[1]), "?X : chen")

    def test5(self):
        r1 = read.parse_input("rule: ((motherof ?x ?y)) -> (parentof ?x ?y)")
        print(' Retracting', r1)
        self.KB.kb_retract(r1)
        ask1 = read.parse_input("fact: (parentof ada ?X)")
        print(' Asking if', ask1)
        answer = self.KB.kb_ask(ask1)
        self.assertEqual(str(answer[0]), "?X : bing")

    def test6(self):
        fact1 = read.parse_input("fact: (motherof ada greta)")
        self.KB.kb_add(fact1)
        fact2 = read.parse_input("fact: (motherof greta hansel)")
        self.KB.kb_add(fact2)
        ask1 = read.parse_input("fact: (grandmotherof ada ?X)")
        print(' Asking if', ask1)
        answer = self.KB.kb_ask(ask1)
        self.assertEqual(str(answer[2]), "?X : hansel")

    def test7(self):
        fact1 = read.parse_input("fact: (motherof greta hansel)")
        self.KB.kb_add(fact1)
        ask1 = read.parse_input("fact: (grandmotherof ada hansel)")
        print(' Asking if', ask1)
        answer = self.KB.kb_ask(ask1)
        self.assertTrue(str(answer))

    def test8(self):
        fact1 = read.parse_input("fact: (grandmotherof stephanie chen)")
        self.KB.kb_add(fact1)
        fact2 = read.parse_input("fact: (auntof may chen)")
        self.KB.kb_add(fact2)
        fact3 = read.parse_input("fact: (motherof bing chen)")
        print(' Retracting', fact3)
        self.KB.kb_retract(fact3)
        ask1 = read.parse_input("fact: (grandmotherof ?X chen)")
        print(' Asking if', ask1)
        answer = self.KB.kb_ask(ask1)
        self.assertEqual(str(answer[0]), "?X : stephanie")
        ask2 = read.parse_input("fact: (auntof ?X chen)")
        print(' Asking if', ask2)
        answer2 = self.KB.kb_ask(ask2)
        self.assertEqual(str(answer2[0]), "?X : may")

    def test9(self):
        fact1 = read.parse_input("fact: (motherof stephanie bing)")
        self.KB.kb_add(fact1)
        fact2 = read.parse_input("fact: (sisterof may bing)")
        self.KB.kb_add(fact2)
        fact3 = read.parse_input("fact: (motherof bing chen)")
        print(' Retracting', fact3)
        self.KB.kb_retract(fact3)
        ask1 = read.parse_input("fact: (grandmotherof ?X chen)")
        print(' Asking if', ask1)
        answer = self.KB.kb_ask(ask1)
        print(" answer",answer)
        self.assertTrue(len(answer) == 0)
        ask2 = read.parse_input("fact: (auntof ?X chen)")
        print(' Asking if', ask2)
        answer2 = self.KB.kb_ask(ask2)
        self.assertTrue(len(answer2) == 0)

    def test10(self):
        r1 = read.parse_input("fact: (motherof ada bing)")
        print(' Retracting', r1)
        self.KB.kb_retract(r1)
        ask1 = read.parse_input("fact: (grandmotherof ada ?X)")
        print(' Asking if', ask1)
        answer = self.KB.kb_ask(ask1)
        self.assertEqual(str(answer[0]), "?X : felix")
        self.assertEqual(1, (len(answer)))

    def test11(self):
        r1 = read.parse_input("fact: (motherof ada bing)")
        print(' Retracting', r1)
        self.KB.kb_retract(r1)
        ask1 = read.parse_input("fact: (parent ada ?X)")
        print(' Asking if', ask1)
        answer = self.KB.kb_ask(ask1)
        self.assertEqual(0, len(answer))

def pprint_justification(answer):
    """Pretty prints (hence pprint) justifications for the answer.
    """
    if not answer: print('Answer is False, no justification')
    else:
        print('\nJustification:')
        for i in range(0,len(answer.list_of_bindings)):
            # print bindings
            print(answer.list_of_bindings[i][0])
            # print justifications
            for fact_rule in answer.list_of_bindings[i][1]:
                pprint_support(fact_rule,0)
        print

def pprint_support(fact_rule, indent):
    """Recursive pretty printer helper to nicely indent
    """
    if fact_rule:
        print(' '*indent, "Support for")

        if isinstance(fact_rule, Fact):
            print(fact_rule.statement)
        else:
            print(fact_rule.lhs, "->", fact_rule.rhs)

        if fact_rule.supported_by:
            for pair in fact_rule.supported_by:
                print(' '*(indent+1), "support option")
                for next in pair:
                    pprint_support(next, indent+2)



if __name__ == '__main__':
    unittest.main()
