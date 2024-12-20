# -*- coding: utf-8 -*-
"""Finite languages and related automata manipulation

Finite languages manipulation

.. *Authors:* Rogério Reis & Nelma Moreira

.. *This is part of FAdo project*   <http://fado.dcc.fc.up.pt

.. *Version:* 1.3.3

.. *Copyright*: 1999-2014 Rogério Reis & Nelma Moreira {rvr,nam}@dcc.fc.up.pt

.. This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 2 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA."""

import fa
from copy import copy
from common import *
import random


class FL(object):
    """Finite Language Class

    :var Words: the elements of the language
    :var Sigma: the alphabet"""
    def __init__(self, wordsList=None, Sigma=None):
        self.Words = set([])
        if Sigma is None:
            self.Sigma = set([])
        else:
            self.Sigma = Sigma
        if wordsList is not None:
            for w in wordsList:
                if type(w) is Word:
                    self.addWord(w)
                else:
                    self.addWord(Word(w))

    def __str__(self):
        l = "({"
        for i in self.Words:
            l += str(i) + ","
        l = l[:-1] + "}, {"
        for i in self.Sigma:
            l += str(i)+","
        l = l[:-1] + "})"
        return l

    def __repr__(self):
        return "FL%s" % self.__str__()

    def __len__(self):
        return len(self.Words)

    def __contains__(self, item):
        return item in self.Words

    def union(self, other):
        """union of FL:   a | b

        :param FL other: right hand operand
        :rtype: FL
        :raises FAdoGeneralError: if both arguments are not FL"""
        return self.__or__(other)

    def __or__(self, other):
        if type(other) != type(self):
            raise FAdoGeneralError("Incompatible objects")
        new = FL()
        new.Sigma = self.Sigma | other.Sigma
        new.Words = self.Words | other.Words
        return new

    def intersection(self, other):
        """Intersection of FL: a & b

        :param FL other: right hand operand
        :raises FAdoGeneralError: if both arguments are not FL"""
        return self.__and__(other)

    def __iter__(self):
        return iter(self.Words)

    def __and__(self, other):
        if type(other) != type(self):
            raise FAdoGeneralError("Incompatible objects")
        new = FL()
        new.Sigma = self.Sigma | other.Sigma
        new.Words = self.Words & other.Words
        return new

    def diff(self, other):
        """Difference of FL: a - b

        :param FL other: right hand operand
        :rtype: FL
        :raises FAdoGeneralError: if both arguments are not FL"""
        return self.__sub__(other)

    def __sub__(self, other):
        if type(other) != type(self):
            raise FAdoGeneralError("Incompatible objects")
        new = FL()
        new.Sigma = self.Sigma | other.Sigma
        new.Words = self.Words - other.Words
        return new

    def setSigma(self, Sigma, Strict=False):
        """Sets the alphabet of a FL

        :param set Sigma: alphabet
        :param bool Strict: behaviour

        .. attention::
           Unless Strict flag is set to True, alphabet can only be enlarged.  The resulting alphabet is  in fact the
           union of the former alphabet with the new one. If flag is set to True, the alphabet is simply replaced."""
        if Strict:
            self.Sigma = Sigma
        else:
            self.Sigma = self.Sigma.union(Sigma)

    def addWords(self, wList):
        """Adds a list of words to a FL

        :param list wList: words to add"""
        self.Words |= set(wList)
        for w in wList:
            if w.epsilonP():
                continue
            for c in w:
                self.Sigma.add(c)

    def addWord(self, word):
        """Adds a word to a FL
        :type word: Word
        :rtype: FL"""
        if word in self:
            return
        self.Words.add(word)
        if not word.epsilonP():
            for c in word:
                self.Sigma.add(c)

    def suffixClosedP(self):
        """Tests if a language is suffix closed

        :rtype: bool"""
        wrds = list(copy(self.Words))
        if Epsilon not in wrds:
            return False
        else:
            wrds.remove(Epsilon)
        wrds.sort(lambda x, y: len(x) - len(y))
        while wrds:
            w = wrds.pop()
            for w1 in suffixes(w):
                if w1 not in self.Words:
                    return False
                else:
                    if w1 in wrds:
                        wrds.remove(w1)
        return True

    def filter(self, automata):
        """Separates a language in two other using a DFA of NFA as a filter

        :param DFA|NFA automata: the automata to be used as a filter
        :returns: the accepted/unaccepted pair of languages
        :rtype: tuple of FL"""
        a, b = (FL(), FL())
        a.setSigma(self.Sigma)
        b.setSigma(self.Sigma)
        for w in self.Words:
            if automata.evalWord(w):
                a.addWords([w])
            else:
                b.addWords([w])
        return a, b

    def MADFA(self):
        """Generates the minimal acyclical DFA using specialized algorithm

        .. versionadded:: 1.3.3

        .. seealso:: Incremental Construction of Minimal Acyclic Finite-State Automata, J.Daciuk, S.Mihov, B.Watson and R.E.Watson

        :rtype: ADFA"""
        aut = ADFA()
        i = aut.addState()
        aut.setInitial(i)
        aut.setSigma(self.Sigma)
        register = set()
        foo = sorted(list(self.Words))
        for w in foo:  # sorted(list(self.Words)):
            (cPrefix, lState) = aut._common_prefix(w)
            cSuffix = w[len(cPrefix):]
            if aut.delta.get(lState, {}):
                aut._replace_or_register(lState, register)
            aut.addSuffix(lState, cSuffix)
        aut._replace_or_register(i, register)
        aut.Minimal = True
        return aut

    def trieFA(self):
        """Generates the trie automaton that recognises this language

        :returns: the trie automaton
        :rtype: ADFA"""
        new = ADFA()
        new.setSigma(copy(self.Sigma))
        i = new.addState()
        new.setInitial(i)
        for w in self.Words:
            if w.epsilonP():
                new.addFinal(i)
            else:
                s = i
                for c in w:
                    if c not in new.delta.get(s, []):
                        sn = new.addState()
                        new.addTransition(s, c, sn)
                        s = sn
                    else:
                        s = new.delta[s][c]
                new.addFinal(s)
        return new

    def toDFA(self):
        """ Generates a DFA recognizing the language

        :rtype: ADFA

        .. versionadded:: 1.2"""
        return self.trieFA()

    def toNFA(self):
        """Generates a NFA recognizing the language

        :rtype: ANFA

        .. versionadded:: 1.2"""
        return self.toDFA().toANFA()

    # noinspection PyUnboundLocalVariable
    def multiLineAutomaton(self):
        """Generates the trivial linear ANFA equivalent to this language
    
        :rtype: ANFA"""
        new = ANFA()
        s1 = None
        new.setSigma(copy(self.Sigma))
        for w in self.Words:
            s = new.addState()
            new.addInitial(s)
            for c in w:
                s1 = new.addState()
                new.addTransition(s, c, s1)
                s = s1
            new.addFinal(s1)
        return new


class DFCA(fa.DFA):
    """Deterministic Cover Automata class

    .. inheritance-diagram:: DFCA"""

    def __init__(self):
        super(DFCA, self).__init__()
        self.length = None

    @property
    def length(self):
        """
        :return: size of the longest word
        :rtype: int"""
        return self.length

    @length.setter
    def length(self, value):
        """Setter
        :param int value: size"""
        self.length = value

    @length.deleter
    def length(self):
        """Length deleter"""
        self.length = None


class AFA(object):
    """Base class for Acyclic Finite Automata

    .. inheritance-diagram:: AFA

    .. note::
       This is just a container for some common methods. **Not to be used directly!!**"""
    def __init__(self):
        self.Dead = None
        self.delta = dict()
        self.Initial = None
        self.States = []
        self.Final = set()

    @abstractmethod
    def addState(self):
        """
        :rtype: int"""
        pass

    @abstractmethod
    def finalP(self):
        pass

    def setDeadState(self, sti):
        """Identifies the dead state

        :param int sti: index of the dead state

        .. attention::
           nothing is done to ensure that the state given is legitimate

        .. note::
           without dead state identified, most of the methods for acyclic automata can not be applied"""
        self.Dead = sti

    def ensureDead(self):
        """Ensures that a state is defined as dead"""
        try:
            _ = self.Dead
        except AttributeError:
            x = self.addState(DeadName)
            self.setDeadState(x)

    def ordered(self):
        """Orders states names in its topological order
    
        :returns: ordered list of state indexes
        :rtype: list of int

        .. note::
           one could use the FA.toposort() method, but special care must be taken with the dead state for the
           algorithms related with cover automata."""

        def _dealS(st1):
            if st1 not in torder:
                torder.append(st1)
                if st1 in self.delta.keys():
                    for k in self.delta[st1]:
                        for dest in forceIterable(self.delta[st1][k]):
                            if dest not in torder and dest != self.Dead:
                                queue.append(dest)

        try:
            dead = self.Dead
        except AttributeError:
            raise FAdoGeneralError("ADFA has not dead state identified")
        torder, queue = [], []
        _dealS(self.Initial)
        while queue:
            st = queue.pop()
            _dealS(st)
        torder.append(dead)
        return torder

    def _getRdelta(self):
        """
        :returns: pair, map of number of sons map, of reverse conectivity
        :rtype: dict"""
        done = set()
        deltaC, rdelta = {}, {}
        notDone = set(forceIterable(self.Initial))
        while notDone:
            sts = uSet(notDone)
            done.add(sts)
            l = set()
            for k in self.delta.get(sts, []):
                for std in forceIterable(self.delta[sts][k]):
                    l.add(std)
                    rdelta.setdefault(std, set([])).add(sts)
                    if std not in done:
                        notDone.add(std)
            deltaC[sts] = len(l)
            notDone.remove(sts)
        for s in forceIterable(self.Initial):
            if s not in rdelta:
                rdelta[s] = set()
        return deltaC, rdelta

    def directRank(self):
        """Compute rank function

        :return: ranf map
        :rtype: dict"""
        r, _ = self.evalRank()
        n = {}
        for x in r:
            for i in r[x]:
                n[i] = x
        return n

    def evalRank(self):
        """Evaluates the rank map of a automaton

        :return: pair of sets of states by rank map, reverse delta accessability map
        :rtype: tuple"""
        (deltaC, rdelta) = self._getRdelta()
        rank, deltai = {}, {}
        for s in xrange(len(self.States)):
            deltai.setdefault(deltaC[s], set([])).add(s)
        i = -1
        notDone = copy(range(len(self.States)))
        deltaC[self.Dead] = 0
        deltai[1].remove(self.Dead)
        deltai[0] = {self.Dead}
        rdelta[self.Dead].remove(self.Dead)
        while notDone:
            rank[i] = deepcopy(deltai[0])
            deltai[0] = set()
            for s in rank[i]:
                for s1 in rdelta[s]:
                    l = deltaC[s1]
                    deltaC[s1] = l - 1
                    deltai[l].remove(s1)
                    deltai.setdefault(l - 1, set()).add(s1)
                notDone.remove(s)
            i += 1
        return rank, rdelta

    def getLeaves(self):
        """The set of leaves, i.e. final states for last symbols of language words

        :return: set of leaves
        :rtype: set"""

        # noinspection PyUnresolvedReferences
        def _last(s1):
            queue, done = {s1}, set()
            while queue:
                q = queue.pop()
                done.add(q)
                for k in self.delta.get(q, {}):
                    for s1 in forceIterable(self.delta[q][k]):
                        if self.finalP(s1):
                            return False
                        elif s1 not in done:
                            queue.add(s1)
            return True

        leaves = set()
        for s in self.Final:
            if _last(s):
                leaves.add(self.States[s])
        return leaves


class ADFA(fa.DFA, AFA):
    """Acyclic Deterministic Finite Automata class

    .. inheritance-diagram:: ADFA

    .. versionchanged:: 1.3.3
    """
    def __init__(self):
        fa.DFA.__init__(self)
        AFA.__init__(self)
        self.Minimal = False

    def __repr__(self):
        return 'ADFA({0:s})'.format(self.__str__())

    def complete(self, dead=None):
        """Make the ADFA complete

        :param int dead: a state to be identified as dead state if one was not identified yet
        :rtype: ADFA

        .. attention::
           The object is modified in place

        .. versionchanged:: 1.3.3"""
        if dead is not None:
            self.Dead = dead
        else:
            try:
                if self.Dead is None:
                    raise AttributeError
                else:
                    _ = self.Dead
            except AttributeError:
                foo = self.addState(DeadName)
                self.Dead = foo
        for st in range(len(self.States)):
            for k in self.Sigma:
                if k not in self.delta.get(st, {}).keys():
                    self.addTransition(st, k, self.Dead)
        self.Minimal = False
        return self

    def dup(self):
        """Duplicate the basic structure into a new ADFA. Basically a copy.deep.

        :rtype: ADFA"""
        return deepcopy(self)

    def __invert__(self):
        """ Complement of a ADFA is a DFA

        :return:DFA
        """
        aut = self.forceToDFA()
        return ~aut

    def minimalP(self, method=None):
        """Tests if the DFA is minimal

        :param method: minimization algorithm (here void)
        :rtype: bool

        .. versionchanged:: 1.3.3"""
        if self.Minimal:
            return True
        foo = self.minimal()
        if self.completeP():
            foo.complete()
        answ = len(foo) == len(self)
        if answ:
            self.Minimal = True
        return answ

    def forceToDFA(self):
        """ Conversion to DFA

        :rtype: DFA"""
        new = fa.DFA()
        new.States = deepcopy(self.States)
        new.Sigma = deepcopy(self.Sigma)
        new.Initial = self.Initial
        new.Final = copy(self.Final)
        for s in self.delta:
            for c in self.delta[s]:
                new.addTransition(s, c, self.delta[s][c])
        return new

    def forceToDFCA(self):
        """ Conversion to DFCA

        :rtype: DFA"""
        new = fa.DFA()
        new.States = deepcopy(self.States)
        new.Sigma = deepcopy(self.Sigma)
        new.Initial = self.Initial
        new.Final = copy(self.Final)
        for s in self.delta:
            for c in self.delta[s]:
                new.addTransition(s, c, self.delta[s][c])
        return new

    def wordGenerator(self):
        """Creates a random word generator

        :return: the random word generator
        :rtype: RndWGen

        .. versionadded:: 1.2"""
        return RndWGen(self)

    def possibleToReverse(self):
        """Tests if language is reversible

        .. versionadded:: 1.3.3"""
        return True

    def minimal(self):
        """Finds the minimal equivalent ADFA

        .. seealso:: [TCS 92 pp 181-189] Minimisation of acyclic deterministic automata in linear time, Dominique Revuz

        .. versionchanged:: 1.3.3

        :returns: the minimal equivalent ADFA
        :rtype: ADFA"""

        def _getListDelta(ss):
            """returns [([sons,final?],s) for s in ss].sort"""
            l = []
            for s in ss:
                dl = [new.delta[s][k] for k in new.Sigma]
                dl.append(s in new.Final)
                l.append((dl, s))
            l.sort()
            return l

        def _collapse(r1, r2):
            """redirects all transitions going to r2 to r1 and adds r2 to toBeDeleted"""
            for s in rdelta[r2]:
                for k in new.delta[s]:
                    if new.delta[s][k] == r2:
                        new.delta[s][k] = r1
            toBeDeleted.append(r2)

        if len(self.States) == 1:
            return self
        new = deepcopy(self)
        new.trim()
        new.complete()
        if new.Dead is None:
            deadName = None
        else:
            deadName = new.States[new.Dead]
        rank, rdelta = new.evalRank()
        toBeDeleted = []
        maxr = len(rank) - 2
        for r in xrange(maxr + 1):
            ls = _getListDelta(rank[r])
            (d0, s0) = ls[0]
            j = 1
            while j < len(ls):
                (d1, s1) = ls[j]
                if d0 == d1:
                    _collapse(s0, s1)
                else:
                    (d0, s0) = (d1, s1)
                j += 1
        new.deleteStates(toBeDeleted)
        if deadName is not None:
            new.Dead = new.stateIndex(deadName)
        new.Minimal = True
        return new

    def minReversible(self):
        """Returns the minimal reversible equivalent automaton

        :rtype: ADFA"""
        new = self.dup()
        rank, rdelta = new.evalRank()



    def statePairEquiv(self, s1, s2):
        """Tests if two states of a ADFA are equivalent

        :param int s1: state1
        :param int s2: state2
        :rtype: bool

        .. versionadded:: 1.3.3"""
        if not self.same_nullability(s1, s2):
            return False
        else:
            return self.delta.get(s1, {}) == self.delta.get(s2, {})

    def addSuffix(self, st, w):
        """Adds a suffix starting in st

        :param int st: state
        :param Word w: suffix

        .. versionadded:: 1.3.3

        .. attention:: in place transformation"""
        s1 = st
        for c in w:
            s2 = self.addState()
            self.addTransition(s1, c, s2)
            s1 = s2
        self.addFinal(s1)

    def _last_child(self, s):
        """to be used by xxx of FL.MADFA

        :param int s: state index
        :returns: pair state index / symbol

        .. versionadded:: 1.3.3"""
        for c in sorted(list(self.Sigma)).__reversed__():
            if c in self.delta.get(s, {}):
                return self.delta[s][c], c
        raise FAdoGeneralError("Something unexpected in _last_child({:d})".format(s))

    def _replace_or_register(self, s, r):
        """to be used by xxx of FL.MADFA

        :param int s: state
        :param Set r: register (inherited from context)

        .. versionadded:: 1.3.3"""
        (child, c) = self._last_child(s)
        if self.delta.get(child, {}):
            self._replace_or_register(child, r)
        for q in r:
            if self.statePairEquiv(q, child):
                self.delta[s][c] = q
                self.deleteState(child)
                return
        r.add(child)

    def _common_prefix(self, wrd):
        """The longest prefix of w that can be read in the ADFA and the correspondent state

        :param Word wrd: word"""
        pref = Word()
        q = self.Initial
        for s in wrd:
            if s in self.delta.get(q, {}):
                pref.append(s)
                q = self.delta[q][s]
            else:
                break
        return pref, q

    def _addWordToMinimal(self, w):
        """Incremental minimization algorithm

        :param Word w: word

        .. attention:: in place transformation

        .. versionadded:: 1.3.3

        .. seealso:: Incremental Construction of Minimal Acyclic Finite-State Automata, J.Daciuk, S.Mihov,
                     B.Watson and R.E.Watson"""

        def _transverseNonConfluence(wrd):
            inCount = dict()
            for s in range(len(self.States)):
                for c in self.delta.get(s, {}):
                    for s1 in self.delta[s][c]:
                        inCount[s1] = inCount.get(s1, 0) + 1
            q = self.Initial
            visited = [q]
            for i, sym in enumerate(wrd):
                if sym not in self.delta.get(s, {}) or inCount[self.delta[q][sym]] > 1:
                    return q, i
                q = self.delta[q][sym]
                visited.append(q)

        def _cloneConfluence(st, wrd, ind):
            q = st
            for i, sym in enumerate(wrd[ind:]):
                if sym not in self.delta.get(q, {}):
                    return q, i + ind
                qn = self.delta[q][sym]
                sn = self.addState()
                for c1 in self.delta.get(qn, {}):
                    self.delta.setdefault(sn, {})[c1] = self.delta[qn][c1]
                    if self.finalP(qn):
                        self.addFinal(sn)
                self.addTransition(q, sym, sn)
                q = sn
                visited.append(q)

        def _replOrReg(st, wrd):
            if len(w) != 0:
                self.addTransition(q,wrd[0],_replOrReg(self.delta[st][wrd[0]], wrd[1:]))
            else:
                for c in register:
                    if self.statePairEquiv(c, q):
                        self.deleteState(q)
                        return c
                register.add(q)

        def _addSuffix(st, wrd):
            s = st
            for c in wrd:
                sn = self.addState()
                self.addTransition(s, c, sn)
                s = sn
            self.addFinal(s)

        register = set()
        visited = []
        q, i = _transverseNonConfluence(w)
        f = q
        register.remove(q)
        j = i
        q, i = _cloneConfluence(q, w, i)
        _addSuffix(q, w[i:])
        if j < len(w):
            self.delta[f][w[j]] = _replOrReg(self.delta[f][w[j]], w[j+1:])



    def dissMin(self, witnesses=None):
        """Evaluates the minimal dissimilarity language
        :param dict witnesses: optional witness dictionay
        :rtype: FL

        .. versionadded:: 1.2.1"""
        new = self.minimal()
        sz = len(new.States)
        todo = [(i, j) for i in range(sz) for j in range(i)]
        mD = FL(Sigma=new.Sigma)
        lvl = new.level()
        rnk = new.directRank()
        l = max([rnk[x] for x in rnk])
        Li = []
        for (i, j) in todo:
            if self.finalP(i) ^ self.finalP(j):
                if witnesses is not None:
                    witnesses[(i, j)] = Word(Epsilon)
                Li.append((i, j))
                mD.addWord(Word(Epsilon))
        delFromList(todo, Li)
        words = self.words()
        for w in words:
            if len(w) >= l or not todo:
                break
            Li = []
            for (i, j) in todo:
                if (lvl[i] + len(w) > l) or (lvl[j] + len(w) > l):
                    Li.append((i, j))
                elif self.evalWordP(w, i) ^ self.evalWordP(w, j):
                    mD.addWord(w)
                    if witnesses is not None:
                        witnesses[(i, j)] = w
                    Li.append((i, j))
            delFromList(todo, Li)
        return mD

    def diss(self):
        """ Evaluates the dissimilarity language

        :rtype: FL

        .. versionadded:: 1.2.1"""
        new = self.minimal()
        n = len(new.States)
        mD = FL(Sigma=new.Sigma)
        lvl = new.level()
        rnk = new.directRank()
        l = max([rnk[x] for x in rnk])
        if len(new.Final) != n:
            mD.addWord(Word(Epsilon))
        words = self.words()
        for w in words:
            lw = len(w)
            if lw >= l:
                break
            skip = False
            for i in range(n):
                if skip:
                    break
                for j in range(i):
                    if (lvl[i] + lw <= l) and (lvl[j] + lw <= l) and (self.evalWordP(w, i) ^ self.evalWordP(w, j)):
                        mD.addWord(w)
                        skip = True
                        break
        return mD

    def level(self):
        """Computes the level  for each state

        :returns: levels of states
        :rtype: dict

        .. versionadded:: 0.9.8"""
        lvl = {}
        done, alvl = set(), [self.Initial]
        l = 0
        while alvl:
            nlvl = set()
            for i in alvl:
                lvl[i] = l
                done.add(i)
                for c in self.delta[i]:
                    j = self.delta[i][c]
                    if j not in done and j not in alvl:
                        nlvl.add(j)
            l += 1
            alvl = copy(nlvl)
        return lvl

    def _gap(self, l, lvl):
        """Computes the gap value for each pair of states.

        The automata is supposed to have its states named numerically in such way that the initial is zero

        :param int l: length of the longest word
        :param dict lvl: level of each state
        :returns: gap function
        :rtype: dict"""
        def _range(r, s):
            return l - max(lvl[r], lvl[s])
        gp = {}
        n = len(self.States) - 1
        for i in range(n):
            gp[(self.stateIndex(i), self.stateIndex(n))] = l
        if lvl[self.stateIndex(n)] <= l:
            for i in self.Final:
                gp[(i, self.stateIndex(n))] = 0
        for i in range(n):
            for j in range(i + 1, n):
                if not self.same_nullability(self.stateIndex(i), self.stateIndex(j)):
                    gp[(self.stateIndex(i), self.stateIndex(j))] = 0
                else:
                    gp[(self.stateIndex(i), self.stateIndex(j))] = l
        for i in range(n - 2, -1, -1):
            for j in range(n, i, -1):
                for c in self.Sigma:
                    i1, j1 = self.delta[self.stateIndex(i)][c], self.delta[self.stateIndex(j)][c]
                    if i1 != j1:
                        if int(self.States[i1]) < int(self.States[j1]):
                            g = gp[(i1, j1)]
                        else:
                            g = gp[(j1, i1)]
                        if g + 1 <= _range(self.stateIndex(i), self.stateIndex(j)):
                            gp[(self.stateIndex(i), self.stateIndex(j))] = min(gp[(self.stateIndex(i),
                                                                                   self.stateIndex(j))], g + 1)
        return gp

    def minDFCA(self):
        """Generates a minimal deterministic cover automata from a DFA

        :rtype: DFCA

        .. versionadded:: 0.9.8

        .. seealso::
            Cezar Campeanu, Andrei Päun, and Sheng Yu, An efficient algorithm for constructing minimal cover
            automata for finite languages, IJFCS"""
        new = self.dup().minimal()
        if not self.completeP():
            new.complete()
        rank = new.directRank()
        irank = dict((v, [k for (k, xx) in filter(lambda key, value: value == v, rank.items())])
                     for v in set(rank.values()))
        l = rank[new.Initial]
        lvl = new.level()
        foo = [x for x in irank]
        foo.sort(reverse=True)
        lnames = [None for _ in new.States]
        newname = 0
        for i in foo:
            for j in irank[i]:
                lnames[j] = newname
                newname += 1
        new.States = lnames
        g = new._gap(l, lvl)
        P = [False for _ in new.States]
        toMerge = []
        for i in range(len(new.States) - 1):
            if not P[i]:
                for j in range(i + 1, len(new.States)):
                    if not P[j] and g[(new.stateIndex(i), new.stateIndex(j))] == l:
                        toMerge.append((i, j))
                        P[j] = True
        for (a, b) in toMerge:
            new.mergeStates(new.stateIndex(b), new.stateIndex(a))
        new.trim()
        new = new.forceToDFCA()
        new.length = l
        return new

    def trim(self):
        """Remove states that do not lead to a final state, or, inclusively, that can't be reached from the initial
        state. Only useful states remain.

        .. attention:: in place transformation"""
        fa.OFA.trim(self)
        try:
            del self.Dead
        except AttributeError:
            pass
        return self

    def toANFA(self):
        """Converts the ADFA in a equivalent ANFA

        :rtype: ANFA"""
        new = ANFA()
        new.setSigma(copy(self.Sigma))
        new.States = copy(self.States)
        for s in xrange(len(self.States)):
            for k in self.delta.get(s, {}):
                new.addTransition(s, k, self.delta[s][k])
        new.addInitial(self.Initial)
        for s in self.Final:
            new.addFinal(s)
        return new

    def toNFA(self):
        """Converts the ADFA in a equivalent NFA

        :rtype: ANFA

        .. versionadded:: 1.2"""
        return self.toANFA()


class RndWGen(object):
    """Word random generator class

    .. versionadded:: 1.2"""
    def __init__(self, aut):
        """
        :param aut: automata recognizing the language
        :type aut: ADFA """
        self.Sigma = list(aut.Sigma)
        self.table = dict()
        self.aut = aut.minimal()
        rank, _ = self.aut.evalRank()
        self.aut._compute_delta_inv()
        deltai = self.aut.delta_inv
        mrank = max(rank)
        for i in range(0, mrank + 1):
            for s in rank[i]:
                self.table.setdefault(s, {})
                if self.aut.finalP(s):
                    final = 1
                else:
                    final = 0
                self.table[s][None] = sum([self.table[s].get(c, 0) for c in self.Sigma])
                for c in self.Sigma:
                    rs = deltai[s].get(c, [])
                    for r in rs:
                        self.table.setdefault(r, {})
                        self.table[r][c] = self.table[s][None] + final

    @staticmethod
    def _rndChoose(l):
        sm = sum(l)
        r = random.randint(1, sm)
        for i, j in enumerate(l):
            if r <= j:
                return i
            else:
                r -= j

    def next(self):
        """Next word

        :return: a new random word"""
        word = Word()
        s = self.aut.Initial
        while True:
            if self.aut.finalP(s) and random.randint(1, self.table[s][None] + 1) == 1:
                return word
            i = self._rndChoose([self.table[s].get(c, 0) for c in self.Sigma])
            word.append(self.Sigma[i])
            s = self.aut.delta[s][self.Sigma[i]]


# noinspection PyUnresolvedReferences
class ANFA(fa.NFA, AFA):
    """Acyclic Nondeterministic Finite Automata class

    .. inheritance-diagram:: ANFA"""

    def moveFinal(self, st, stf):
        """Unsets a set as final transfering transition to another final
        :param int st: the state to be 'moved'
        :param int stf: the destination final state

        .. note::
           stf must be a 'last' final state, i.e., must have no out transitions to anywhere but to a possible dead
           state

        .. attention:: the object is modified in place"""
        (rdelta, _) = self._getRdelta()
        for s in rdelta[st]:
            l = []
            for k in self.delta[s]:
                if st in self.delta[s][k]:
                    l.append(k)
            for k in l:
                self.addTransition(s, k, stf)
            self.delFinal(s)

    def mergeStates(self, s1, s2):
        """Merge state s2 into state s1

        :param int s1: state
        :param int s2: state

        .. note::
           no attempt is made to check if the merging preserves the language of teh automaton

        .. attention:: the object is modified in place"""
        (_, rdelta) = self._getRdelta()
        for s in rdelta[s2]:
            l = []
            for k in self.delta[s]:
                if s2 in self.delta[s][k]:
                    l.append(k)
            for k in l:
                self.delta[s][k].remove(s2)
                self.addTransition(s, k, s1)
        for k in self.delta.get(s2, {}):
            for ss in self.delta[s2][k]:
                self.delta.setdefault(s1, {}).setdefault(k, set()).add(ss)
        self.deleteState(s2)

    def mergeLeaves(self):
        """Merge leaves

        .. attention:: object is modified in place"""
        l = self.getLeaves()
        if len(l):
            s0n = l.pop()
            while l:
                s0 = self.stateIndex(s0n)
                s = self.stateIndex(l.pop())
                self.mergeStates(s0, s)

    def mergeInitial(self):
        """Merge initial states

        .. attention:: object is modified in place"""
        l = copy(self.Initial)
        s0 = self.stateIndex(l.pop())
        while l:
            s = self.stateIndex(l.pop())
            self.mergeStates(s0, s)


def sigmaInitialSegment(Sigma, l, exact=False):
    """Generates the ADFA recognizing Sigma^i for i<=l
    :param set Sigma: the alphabet
    :param int l: length
    :param bool exact: only the words with exactly that length?
    :returns: the automaton
    :rtype: ADFA"""
    new = ADFA()
    new.setSigma(Sigma)
    s = new.addState()
    if not exact:
        new.addFinal(s)
    new.setInitial(s)
    for i in range(l):
        s1 = new.addState()
        if not exact or i == l - 1:
            new.addFinal(s1)
        for k in Sigma:
            new.addTransition(s, k, s1)
        s = s1
    return new


# noinspection PyUnboundLocalVariable
def genRndTrieBalanced(maxL, Sigma, safe=True):
    """Generates a random trie automaton for a binary language of balanced words of a given leght for max word
    :param int maxL: length of the max word
    :param set Sigma: alphabet to be used
    :param bool safe: should a word of size maxl be present in every language?
    :return: the generated trie automaton
    :rtype: ADFA"""

    def _genEnsurance(m, alphabet):
        l = len(alphabet)
        fair = m / l
        if m % l == 0:
            odd = 0
        else:
            odd = 1
        pool = copy(alphabet)
        c = {}
        sl = []
        while len(sl) < m:
            s1 = random.choice(pool)
            c[s1] = c.get(s1, 0) + 1
            if c[s1] == fair + odd:
                pool.remove(s1)
            sl.append(s1)
        return sl

    def _legal(cont):
        l = [cont[k1] for k1 in cont]
        return max(l) - min(l) <= 1

    def _descend(s1, ens, safe1, m, cont):
        sons = 0
        if not safe1:
            if _legal(cont):
                final = random.randint(0, 1)
            else:
                final = 0
        # noinspection PyUnboundLocalVariable
        if safe1:
            trie.addFinal(s1)
            final = 1
        elif final == 1:
            trie.addFinal(s1)
        if m != 0:
            if safe1:
                ks = ens.pop()
            else:
                ks = None
            for k1 in trie.Sigma:
                ss = trie.addState()
                trie.addTransition(s1, k1, ss)
                cont[k1] = cont.get(k1, 0) + 1
                if _descend(ss, ens, k1 == ks, m - 1, cont):
                    sons += 1
                cont[k1] -= 1
        if sons == 0 and final == 0:
            trie.deleteState(s1)
            return False
        else:
            return True

    if safe:
        ensurance = _genEnsurance(maxL, Sigma)
    else:
        ensurance = None
    trie = ADFA()
    trie.setSigma(Sigma)
    s = trie.addState()
    trie.setInitial(s)
    contab = {}
    for k in Sigma:
        contab[k] = 0
    _descend(s, ensurance, safe, maxL, contab)
    if random.randint(0, 1) == 1:
        trie.delFinal(s)
    return trie


# noinspection PyUnboundLocalVariable
def genRndTrieUnbalanced(maxL, Sigma, ratio, safe=True):
    """Generates a random trie automaton for a binary language of balanced words of a given length for max word

    :param int maxL: length of the max word
    :param set Sigma: alphabet to be used
    :param int ratio: the ratio of the unbalance
    :param bool safe: should a word of size maxl be present in every language?
    :return: the generated trie automaton
    :rtype: ADFA"""

    def _genEnsurance(m, alphabet):
        chief = uSet(alphabet)
        fair = m / (ratio + 1)
        pool = list(copy(alphabet))
        c = {}
        sl = []
        while len(sl) < m:
            s1 = random.choice(pool)
            c[s1] = c.get(s1, 0) + 1
            if len(sl) - c.get(chief, 0) == fair:
                pool = [chief]
            sl.append(s1)
        return sl

    def _legal(cont):
        l = [cont[k1] for k1 in cont]
        return (ratio + 1) * cont[uSet(Sigma)] >= sum(l)

    # noinspection PyUnboundLocalVariable
    def _descend(s1, ens, safe1, m, cont):
        sons = 0
        if not safe1:
            if _legal(cont):
                final = random.randint(0, 1)
            else:
                final = 0
        if safe1:
            trie.addFinal(s1)
            final = 1
        elif final == 1:
            trie.addFinal(s1)
        if m:
            if safe1:
                ks = ens.pop()
            else:
                ks = None
            for k1 in trie.Sigma:
                ss = trie.addState()
                trie.addTransition(s1, k1, ss)
                cont[k1] = cont.get(k1, 0) + 1
                if _descend(ss, ens, k1 == ks, m - 1, cont):
                    sons += 1
                cont[k1] -= 1
        if sons == 0 and final == 0:
            trie.deleteState(s1)
            return False
        else:
            return True

    if safe:
        ensurance = _genEnsurance(maxL, Sigma)
    else:
        ensurance = None
    trie = ADFA()
    trie.setSigma(Sigma)
    s = trie.addState()
    trie.setInitial(s)
    contab = {}
    for k in Sigma:
        contab[k] = 0
    _descend(s, ensurance, safe, maxL, contab)
    if random.randint(0, 1) == 1:
        trie.delFinal(s)
    return trie


# noinspection PyUnboundLocalVariable
def genRandomTrie(maxL, Sigma, safe=True):
    """Generates a random trie automaton for a finite language with a given length for max word
    :param int maxL: length of the max word
    :param set Sigma: alphabet to be used
    :param bool safe: should a word of size maxl be present in every language?
    :return: the generated trie automaton
    :rtype: ADFA"""

    def _genEnsurance(m, alphabet):
        l = len(alphabet)
        sl = list(alphabet)
        return [sl[random.randint(0, l - 1)] for _ in xrange(m)]

    # noinspection PyUnboundLocalVariable
    def _descend(s1, ens, safe1, m):
        sons = 0
        final = None
        if not safe1:
            final = random.randint(0, 1)
        if safe1:
            trie.addFinal(s1)
            final = 1
        elif final == 1:
            trie.addFinal(s1)
        if m:
            if safe1:
                ks = ens.pop()
            else:
                ks = None
            for k in trie.Sigma:
                ss = trie.addState()
                trie.addTransition(s1, k, ss)
                if _descend(ss, ens, k == ks, m - 1):
                    sons += 1
        if sons == 0 and final == 0:
            trie.deleteState(s1)
            return False
        else:
            return True

    if safe:
        ensurance = _genEnsurance(maxL, Sigma)
    else:
        ensurance = None
    trie = ADFA()
    trie.setSigma(Sigma)
    s = trie.addState()
    trie.setInitial(s)
    _descend(s, ensurance, safe, maxL)
    if random.randint(0, 1) == 1:
        trie.delFinal(s)
    return trie


# noinspection PyUnboundLocalVariable
def genRndTriePrefix(maxL, Sigma, ClosedP=False, safe=True):
    """Generates a random trie automaton for a finite (either prefix free or prefix closed) language with a given
    length for max word
    :param int maxL: length of the max word
    :param set Sigma: alphabet to be used
    :param bool ClosedP: should it be a prefix closed language?
    :param bool safe: should a word of size maxl be present in every language?
    :return: the generated trie automaton
    :rtype: ADFA"""

    def _genEnsurance(m, alphabet):
        l = len(alphabet)
        sl = list(alphabet)
        return [sl[random.randint(0, l - 1)] for _ in xrange(m)]

    def _descend(s1, ens, saf, m):
        sons = ClosedP
        if m is 0:
            final = random.randint(0, 1)
            if saf or final == 1:
                trie.addFinal(s1)
                return True
            else:
                return False
        else:
            if saf is True:
                ks = ens.pop()
            else:
                ks = None
            for k in trie.Sigma:
                ss = trie.addState()
                trie.addTransition(s1, k, ss)
                r = _descend(ss, ens, k == ks, m - 1)
                if not ClosedP:
                    sons |= r
                else:
                    sons &= 1
            if not ClosedP:
                if not sons:
                    final = random.randint(0, 1)
                    if final == 1:
                        trie.addFinal(s1)
                        return True
                    else:
                        return False
                else:
                    return True
            else:
                if not sons:
                    final = random.randint(0, 1)
                    if final == 1:
                        trie.addFinal(s1)
                        return True
                    else:
                        return False
                else:
                    trie.addFinal(s1)
                    return True

    ensurance = None
    if safe:
        ensurance = _genEnsurance(maxL, Sigma)
    trie = ADFA()
    trie.setSigma(Sigma)
    s = trie.addState()
    trie.setInitial(s)
    _descend(s, ensurance, safe, maxL)
    return trie


def DFAtoADFA(aut):
    """Transforms an acyclic DFA into a ADFA

    :param DFA aut: the automaton to be transformed
    :raises notAcyclic: if the DFA is not acyclic
    :returns: the converted automaton
    :rtype: ADFA"""
    new = deepcopy(aut)
    new.trim()
    if not new.acyclicP(True):
        raise notAcyclic()
    afa = ADFA()
    afa.States = copy(new.States)
    afa.Sigma = copy(new.Sigma)
    afa.Initial = new.Initial
    afa.delta = copy(new.delta)
    afa.Final = copy(new.Final)
    afa.complete()
    return afa


def stringToADFA(s):
    """Convert a canonical string representation of a ADFA to a ADFA
    :param list s: the string in its canonical order
    :returns: the ADFA
    :rtype: ADFA

    .. seealso::
        Marco Almeida, Nelma Moreira, and Rogério Reis. Exact generation of minimal acyclic deterministic finite
        automata. International Journal of Foundations of Computer Science, 19(4):751-765, August 2008.
    """
    k = len(s[0]) - 1
    new = ADFA()
    new.setSigma([str(c) for c in range(k)])
    for st, sts in enumerate(s):
        new.addState(str(st))
        for c, s1 in enumerate(sts[:-1]):
            new.addTransition(st, str(c), s1)
        if sts[-1]:
            new.addFinal(st)
    new.setInitial(len(s) - 1)
    return new

