import itertools
import time

import read, copy
from util import *
from logical_classes import *

verbose = 0

class KnowledgeBase(object):
    def __init__(self, facts=[], rules=[], file = 'minesweeper_kb.txt'):
        self.facts = facts
        self.rules = rules
        self.ie = InferenceEngine()
        self.setUp(file)

    def __repr__(self):
        return 'KnowledgeBase({!r}, {!r})'.format(self.facts, self.rules)

    def __str__(self):
        string = "Knowledge Base: \n"
        string += "\n".join((str(fact) for fact in self.facts)) + "\n"
        string += "\n".join((str(rule) for rule in self.rules))
        return string

    def setUp(self, file):
        # Assert starter facts
        self.data = read.read_tokenize(file)
        data = read.read_tokenize(file)
        for item in data:
            if isinstance(item, Fact) or isinstance(item, Rule):
                self.kb_add(item)

    def _get_fact(self, fact):
        """ Args: fact (Fact): Fact we're searching for
            Returns: Fact: matching fact
        """
        for kbfact in self.facts:
            if fact == kbfact:
                return kbfact

    def _get_rule(self, rule):
        """ Args: rule (Rule): Rule we're searching for
            Returns: Rule: matching rule
        """
        for kbrule in self.rules:
            if rule == kbrule:
                return kbrule

    def kb_add_parse(self, text):
        parsed = read.parse_input(text)
        self.kb_add(parsed)

    def kb_add(self, fact_rule):
        """Add a fact or rule to the KB"""
        #printv("Adding {!r}", 1, verbose, [fact_rule])
        # print("\nAdding",fact_rule,"to KB")
        if isinstance(fact_rule, Fact):
            self._kb_add_fact(fact_rule)
        elif isinstance(fact_rule, Rule):
            self._kb_add_rule(fact_rule)

    def _kb_add_fact(self, fact):
        # t0 = time.time()
        if fact not in self.facts:
            self.facts.append(fact)
            # for rule in self.rules:
            #     self.ie.fc_infer(fact, rule, self)
        else:
            if fact.supported_by:
                ind = self.facts.index(fact)
                for f in fact.supported_by:
                    self.facts[ind].supported_by.append(f)
            else:
                ind = self.facts.index(fact)
                self.facts[ind].asserted = True
        # t1 = time.time()
        # print("adding fact took: " + str(t1-t0))

    def _kb_add_rule(self, rule):
        # t0 = time.time()
        # print("adding rule")
        # print(rule)
        if rule not in self.rules:
            self.rules.append(rule)
            for fact in self.facts:
                self.ie.fc_infer(fact, rule, self)
        else:
            if rule.supported_by:
                ind = self.rules.index(rule)
                for f in rule.supported_by:
                    self.rules[ind].supported_by.append(f)
            else:
                ind = self.rules.index(rule)
                self.rules[ind].asserted = True
        # t1 = time.time()
        # print("adding rule took: " + str(t1-t0))

    def is_violation(self, cell, safe_or_bomb):
        """Returns if adding a fact to the knowledgebase causes a logical inconsistancy"""
        fact = read.parse_input("fact: ("+safe_or_bomb+" "+cell+")")
        #printv("Asserting {!r}", 0, verbose, [fact])
        self.kb_add(fact)
        isViolation = read.parse_input("fact: (violation "+cell+")")
        self.kb_ask(isViolation)
        self.kb_retract(fact)
        return isViolation

    def kb_ask(self, f):
        """Ask if a fact is in the KB
        Args: fact (Fact) - Statement to be asked (will be converted into a Fact)
        Returns: listof Bindings|False - list of Bindings if result found, False otherwise
        """
        #print("Asking {!r}".format(f))
        if factq(f):
            # ask matched facts
            if bindings := self.check_facts(f): return bindings

            # check rules if no facts found
            backward_result = self.backward_chain(f)

            return backward_result

        else:
            #print("Invalid ask:", f.statement)
            return []

    def check_facts(self, f):
        if isinstance(f,Fact): stmt = f.statement
        elif isinstance(f,Statement): stmt = f
        else: return False
        # print("checking",stmt)
        for fact in self.facts:
            binding = match(stmt, fact.statement)
            if binding:
                # print("returning true")
                return binding
        # print("returning false")
        return False

    def backward_chain(self, f):
        for rule in self.rules:
            binding = match(f.statement, rule.rhs)
            if binding and binding.bindings:
                # print("bindings")
                # print(binding)
                is_entailed = self.ie.bc_infer(binding, f, rule, self)
                if is_entailed: return True
        return False

    def kb_retract(self, fact):
        """Retract a fact from the KB"""
        #printv("Retracting {!r}", 0, verbose, [fact])
        if isinstance(fact, Rule): return

        kb_fact = self.facts[self.facts.index(fact)]
        if kb_fact.supported_by: kb_fact.asserted = False
        else: self._kb_retract_recursive(kb_fact)

    def _kb_retract_recursive(self, fact_rule):
        for supported in itertools.chain(fact_rule.supports_facts, fact_rule.supports_rules):
            self._clean_up_supported_by(supported, fact_rule)
            if not supported.asserted and not supported.supported_by:
                self._kb_retract_recursive(supported)
        self.facts.remove(fact_rule) if isinstance(fact_rule, Fact) else self.rules.remove(fact_rule)

    def _clean_up_supported_by(self, fact_rule, item):
        for i,pair in enumerate(fact_rule.supported_by):
            if item in pair: fact_rule.supported_by.pop(i)



class InferenceEngine(object):
    def bc_infer(self, bindings, fact, rule, kb):
        """Forward-chaining to infer new facts and rules

        Args:
            fact (Fact) - A fact from the KnowledgeBase
            rule (Rule) - A rule from the KnowledgeBase
            kb (KnowledgeBase) - A KnowledgeBase

        Returns:
            Nothing
        """
        #printv('Attempting to infer from {!r} and {!r} => {!r}', 1, verbose,
            # [fact.statement, rule.lhs, rule.rhs])

        if not bindings or len(bindings.bindings) ==  0: return False

        # if bindings := self._get_rule_bindings(fact, rule):
        lhs = [instantiate(stmt,bindings) for stmt in rule.lhs]
        # lhs = [ns for stmt in rule.lhs
        #            if (ns := instantiate(stmt,bindings)) != fact.statement]
        rhs = instantiate(rule.rhs, bindings)
        test_rule = Rule([lhs, rhs], [])
        # print("test rule:",test_rule)
        entailed_rule = self.bc_infer_step(test_rule, kb, [])
        # print("entailed",is_entailed)
        if entailed_rule:
            kb.kb_add(Fact(rhs, [entailed_rule]))
        return entailed_rule

    def bc_infer_step(self, rule, kb, used_terms = []):
        # print()
        # print("step",rule)
        for kb_fact in kb.facts:
            # if str(kb_fact.statement).startswith("(near1Bomb"): print(kb_fact.statement, used_terms)
            if fact_bindings := self._get_rule_bindings(kb_fact, rule, used_terms):
                # if str(kb_fact.statement).startswith("(near1Bomb"): print(fact_bindings)
                # print("Final Bindings",fact_bindings)
                if len(fact_bindings.bindings) == 0: continue
                new_rule = self.get_new_rule(rule, kb_fact, fact_bindings, kb)
                new_rule = self.get_new_rule(rule, kb_fact, fact_bindings, kb)
                if not new_rule: continue
                next_used_terms = used_terms.copy()
                next_used_terms.extend(fact_bindings.bindings_dict.values())
                # print("used terms",next_used_terms)
                # print("has unknown",  rule_has_unknown(new_rule))
                if rule_has_unknown(new_rule):
                    entailed_rule = self.bc_infer_step(new_rule, kb, next_used_terms)
                    if entailed_rule:
                        # add suppported by kb_fact, entailed_rule
                        new_rule.supported_by.append((kb_fact, entailed_rule))
                        return new_rule
                    else: continue
                else:
                    return new_rule
        return False

    def get_new_rule(self, rule, fact, bindings, kb):
        new_lhs = [instantiate(stmt,bindings) for stmt in rule.lhs]
        # new_lhs = [ns for stmt in rule.lhs
        #            if (ns := instantiate(stmt,bindings)) != fact.statement]
        new_rhs = instantiate(rule.rhs, bindings)
        new_rule = Rule([new_lhs,new_rhs], [])
        # print()
        # print("bindings found",bindings)
        # print(new_rule)
        for stmt in new_lhs:
            if not is_variable(stmt) and not kb.check_facts(stmt): return False
        return new_rule


    def fc_infer(self, fact, rule, kb):
        """Forward-chaining to infer new facts and rules

        Args:
            fact (Fact) - A fact from the KnowledgeBase
            rule (Rule) - A rule from the KnowledgeBase
            kb (KnowledgeBase) - A KnowledgeBase

        Returns:
            Nothing
        """
        #printv('Attempting to infer from {!r} and {!r} => {!r}', 1, verbose,
            # [fact.statement, rule.lhs, rule.rhs])

        if bindings := self._get_rule_bindings(fact, rule):
            new_lhs = [ns for stmt in rule.lhs
                       if (ns := instantiate(stmt,bindings)) != fact.statement]
            new_rhs = instantiate(rule.rhs, bindings)
            new_fact_rule = Fact(new_rhs, [(fact,rule)]) if not new_lhs \
                else Rule([new_lhs,new_rhs], [(fact,rule)])

            fact.supports_rules.append(new_fact_rule)
            rule.supports_rules.append(new_fact_rule)
            kb.kb_add(new_fact_rule)

    def _get_rule_bindings(self, fact, rule, used_terms = []):
        bindings = None
        # print()
        # rhsst = str(rule.rhs)
        for stmt in rule.lhs:
            if not is_variable(stmt): continue
            bindings = match(stmt, fact.statement, bindings, used_terms)
            # if rhsst == "(bomb c03)" and bindings and len(bindings.bindings)>0:
            #     print("matching",stmt,fact.statement, ", bindings:",bindings)
        # if(bindings and len(bindings.bindings)>0): print("bindings:",bindings)
        return bindings