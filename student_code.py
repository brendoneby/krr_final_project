import itertools

import read, copy
from util import *
from logical_classes import *

verbose = 0

class KnowledgeBase(object):
    def __init__(self, facts=[], rules=[]):
        self.facts = facts
        self.rules = rules
        self.ie = InferenceEngine()

    def __repr__(self):
        return 'KnowledgeBase({!r}, {!r})'.format(self.facts, self.rules)

    def __str__(self):
        string = "Knowledge Base: \n"
        string += "\n".join((str(fact) for fact in self.facts)) + "\n"
        string += "\n".join((str(rule) for rule in self.rules))
        return string

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

    def kb_add(self, fact_rule):
        """Add a fact or rule to the KB"""
        printv("Adding {!r}", 1, verbose, [fact_rule])
        print("\nAdding",fact_rule,"to KB")
        if isinstance(fact_rule, Fact):
            self._kb_add_fact(fact_rule)
        elif isinstance(fact_rule, Rule):
            self._kb_add_rule(fact_rule)

    def _kb_add_fact(self, fact):
        if fact not in self.facts:
            self.facts.append(fact)
            for rule in self.rules:
                self.ie.fc_infer(fact, rule, self)
        else:
            if fact.supported_by:
                ind = self.facts.index(fact)
                for f in fact.supported_by:
                    self.facts[ind].supported_by.append(f)
            else:
                ind = self.facts.index(fact)
                self.facts[ind].asserted = True

    def _kb_add_rule(self, rule):
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

    def kb_is_violation(self, cell, safe_or_bomb):
        """Returns if adding a fact to the knowledgebase causes a logical inconsistancy"""
        fact = read.parse_input("fact: ("+safe_or_bomb+" "+cell+")")
        printv("Asserting {!r}", 0, verbose, [fact])
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
        print("Asking {!r}".format(f))
        if factq(f):
            bindings_lst = ListOfBindings()
            # ask matched facts
            for fact in self.facts:
                binding = match(f.statement, fact.statement)
                if binding:
                    bindings_lst.add_bindings(binding, [fact])

            return bindings_lst if bindings_lst.list_of_bindings else []

        else:
            print("Invalid ask:", f.statement)
            return []

    def kb_retract(self, fact):
        """Retract a fact from the KB"""
        printv("Retracting {!r}", 0, verbose, [fact])
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
    def fc_infer(self, fact, rule, kb):
        """Forward-chaining to infer new facts and rules

        Args:
            fact (Fact) - A fact from the KnowledgeBase
            rule (Rule) - A rule from the KnowledgeBase
            kb (KnowledgeBase) - A KnowledgeBase

        Returns:
            Nothing
        """
        printv('Attempting to infer from {!r} and {!r} => {!r}', 1, verbose,
            [fact.statement, rule.lhs, rule.rhs])

        if bindings := self._get_rule_bindings(fact, rule):
            new_lhs = [ns for stmt in rule.lhs
                       if (ns := instantiate(stmt,bindings)) != fact.statement]
            new_rhs = instantiate(rule.rhs, bindings)
            new_fact_rule = Fact(new_rhs, [(fact,rule)]) if not new_lhs \
                else Rule([new_lhs,new_rhs], [(fact,rule)])

            fact.supports_rules.append(new_fact_rule)
            rule.supports_rules.append(new_fact_rule)
            kb.kb_add(new_fact_rule)

    def _get_rule_bindings(self, fact, rule):
        bindings = None
        for stmt in rule.lhs: bindings = match(stmt, fact.statement, bindings)
        return bindings