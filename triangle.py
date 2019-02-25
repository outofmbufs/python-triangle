import math


class Triangle:
    #
    # By default...
    #   * The three side lengths of a triangle are attributes: a, b, c
    #   * The three angles, in radians, are: alpha, beta, gamma
    #
    # These two tuples ...
    #
    side_names = ('a', 'b', 'c')
    angle_names = ('alpha', 'beta', 'gamma')
    #
    # ... define that; the code never refers to attribute names directly.
    # Accordingly, they can be overridden in a subclass though that was
    # a secondary consideration. Using this level of indirection helped
    # avoid multiple permutation-specific copies of code in the solvers.
    # For example, SSA requires two sides, but should not require
    # it be specifically given sides "a" and "b".
    #
    # The order in these tuples must correspond, so that:
    #
    #    angle_names[i] is the angle opposing side_names[i]

    # Triangle(**kwargs):
    #
    # Specify a triangle, giving sides and angles via keyword args.
    # The number of sides and angles determines how the solver will
    # determine the full triangle, according to:
    #    SSS  -- all three sides
    #    SSA  -- two sides and a non-included angle
    #    SAS  -- two sides and the included angle
    #    AAS  -- two angles and the non-included side
    #    ASA  -- two angles and the included side
    #
    # Unspecified triangle attributes are calculated from the given values
    # using float/trig operations. Accordingly, they are rarely *exact*.
    #
    # For example:
    #   t1 = Triangle(a=3, b=4, c=5)
    #   t2 = Triangle(alpha=0.6435011087932843, gamma=math.pi/2, a=3)
    #
    # both specify a classic 3/4/5 pythagorean triangle, though it is likely
    # that t1.c != t2.c (they will be close but might not be exactly equal).
    # Note that the __repr__ code chooses to use a representation mimicing
    # the parameters supplied at __init__ for this reason.
    #
    # NOTES:
    # * SSS:   The three sides must satisfy the triangle inequality
    # * SSA:   Raises exception if there are two solutions; use
    #          (classmethod) ssa_to_sss to get both solution forms.
    # * AAAS:  Redundant; not accepted. Instead: omit one A --> AAS/ASA
    #

    def __init__(self, **kwargs):

        # sv: NAMES of sides given, av: NAMES of angles given
        sv, av = self.__kwargshelper(self, kwargs)

        # remember these so __repr__ can specifically reproduce them
        # NOTE they are DELIBERATELY put into canonicalized order
        self.__specifiernames = [
            n for n in self.side_names + self.angle_names if n in sv + av]

        # all valid forms have exactly three elements in aggregate
        total = len(sv) + len(av)
        if total > 3:
            raise ValueError("{} is overspecified".format(self))
        elif total < 3:
            raise ValueError("{} is underspecified".format(self))

        # dispatch according to # of angles ... THIS IS MAYBE TOO CUTE???
        (self._sss, self._ssa_sas, self._aas_asa)[len(av)](sv, av, kwargs)

    #
    # Parses kwargs, collating them into angles and sides (returned)
    # and optionally sets them as attributes if given a target object
    #
    @classmethod
    def __kwargshelper(cls, _targetobject, kwargs):
        """Return two (side names, angle names). Optionally set attrs."""
        sv = []
        av = []
        for k, v in kwargs.items():
            if k in cls.angle_names:
                av.append(k)
            elif k in cls.side_names:
                sv.append(k)
            else:
                raise TypeError(
                    "{}() got unexpected keyword arg '{}'".format(
                        cls.__name__, k))
            if _targetobject:
                setattr(_targetobject, k, v)

        return sv, av

    def __repr__(self):
        # Whatever three attributes were provided to __init__ are the repr
        # (but, of course, with whatever their current values are).
        s = "{}(".format(self.__class__.__name__)
        for a in self.__specifiernames:
            s += "{}={}, ".format(a, getattr(self, a))

        return s.rstrip(", ") + ")"

    def __multiget(self, *attrs):
        """Return a list of the values of given attributes."""
        return [getattr(self, a) for a in attrs]

    @classmethod
    def ssa_to_sss(cls, **kwargs):
        """Return two SSS dictionaries, 1 dict per ssa solution."""

        sv, av = cls.__kwargshelper(None, kwargs)
        if len(sv) != 2 or len(av) != 1:
            raise ValueError("SSA requires exactly 2 sides and 1 angle")

        # let:
        #   alpha be the given angle
        #   a be the opposing side (it can be either side given)
        #   b be the other side (the one that isn't "a")

        alpha = kwargs[av[0]]
        a_name = cls.opposing_name(av[0])
        a = kwargs[a_name]
        b_name = sv[1] if a_name == sv[0] else sv[0]
        b = kwargs[b_name]

        # the c name is whichever side name that wasn't given
        c_name = cls.other_names(a_name, b_name)[0]

        # Law of Sines a/sin(alpha) = b/sin(beta) = c/sin(gamma)
        alpha_sin = math.sin(alpha)

        try:
            beta = math.asin((alpha_sin * b) / a)
        except ValueError:
            raise ValueError("no solution possible")

        # third angle is whatever is left
        gamma = math.pi - (alpha + beta)

        # third side from law of Sines
        c = (math.sin(gamma) * a) / alpha_sin

        d1 = {a_name: a, b_name: b, c_name: c}

        # check for ambiguous case regarding beta:
        #   pi - beta would have the same sin and MIGHT be a solution.
        #   Can rule that out if
        #       alpha + (pi - beta) >= pi
        #   as there would be nothing left for gamma
        #
        # Said another way, another triangle is possible if
        #       alpha + (pi - beta) < pi
        # Simplifying by subtracting pi from both sides:
        #       alpha - beta < 0 is the ambiguous case
        # or    beta > alpha
        if beta > alpha:
            # compute the alternate solution
            beta = math.pi - beta
            gamma = math.pi - (alpha + beta)
            c = (math.sin(gamma) * a) / alpha_sin
            d2 = {a_name: a, b_name: b, c_name: c}
        else:
            d2 = None

        return d1, d2

    def _ssa_sas(self, sv, av, kwargs):
        oppside_name = self.opposing_name(av[0])
        if oppside_name in sv:
            # SSA
            d1, d2 = self.ssa_to_sss(**kwargs)
            if d2 is not None:
                raise ValueError("{} is ambiguous".format(self))

            for k, v in d1.items():
                setattr(self, k, v)
            self._compute_missing_angles()
        else:
            a, c, beta = self.__multiget(*sv, *av)
            b = math.sqrt((a*a) + (c*c) - (2 * a * c * math.cos(beta)))
            setattr(self, self.opposing_name(av[0]), b)
            # now it reduces to SSS
            self._sss(sv, av, kwargs)

    def _aas_asa(self, sv, av, kwargs):
        # gamma name is whichever angle name that wasn't given
        # gamma, the third angle, is whatever is left after the other two
        gamma = math.pi
        for a in self.angle_names:
            if hasattr(self, a):
                gamma -= getattr(self, a)
            else:
                gamma_name = a

        setattr(self, gamma_name, gamma)

        # now that all three angles are known... law of Sines
        s0 = getattr(self, sv[0])
        ratio = s0 / math.sin(getattr(self, self.opposing_name(sv[0])))
        for s in self.side_names:
            if s != sv[0]:
                sx = math.sin(getattr(self, self.opposing_name(s))) * ratio
                setattr(self, s, sx)

    def _sss(self, sv, av, kwargs):
        """compute three angles given three sides."""
        a, b, c = self.__multiget(*self.side_names)
        if a + b <= c or a + c <= b or b + c <= a:
            raise ValueError("{} fails triangle inequality".format(self))
        self._compute_missing_angles()

    def _compute_missing_angles(self):
        """Computes any missing angles. All three sides must be present."""

        snsn = self.side_names + self.side_names   # i.e., double the list
        for angle_name in self.angle_names:
            if not hasattr(self, angle_name):

                # cleverly generates correct sides permutation by sliding
                # a window of three accordingly through snsn list.
                offset = self.angle_names.index(angle_name)
                a, b, c = self.__multiget(*snsn[offset:offset+3])

                angle = math.acos(((b*b) + (c*c) - (a*a)) / (2*b*c))
                setattr(self, angle_name, angle)

    @classmethod
    def opposing_name(cls, name):
        """Return opposing angle name for given side name, or vice versa."""
        if name in cls.side_names:
            return cls.angle_names[cls.side_names.index(name)]
        elif name in cls.angle_names:
            return cls.side_names[cls.angle_names.index(name)]
        else:
            return None

    @classmethod
    def other_names(cls, _name1, *names):
        """Given 1 or more side names or angle names, return the others."""

        # this ONLY returns side names for sides, and angles for angles.
        for x in (cls.side_names, cls.angle_names):
            if _name1 in x:
                for n in names:
                    if n not in x:
                        raise ValueError("mismatching name types given")
                candidates = x
                break
        else:
            raise ValueError("unknown name given")

        return [x for x in candidates if x != _name1 and x not in names]

    def opposing(self, name):
        """Return opposing angle/side VALUE for given side/angle NAME."""
        opp = self.opposing_name(name)
        if opp is not None:
            return getattr(self, opp)
        raise ValueError("{} not found in {}".format(name, self))

    def threesides(self):
        """a, b, c = t.threesides()"""
        return self.__multiget(*self.side_names)

    def threeangles(self):
        """alpha, beta, gamma = t.threeangles()"""
        return self.__multiget(*self.angle_names)

    def canonicaltriangle(self):
        """Return a new triangle with sides in size order low-to-high."""
        abc = self.threesides()
        abc.sort()
        return Triangle(**{k: abc[self.side_names.index(k)]
                           for k in self.side_names})

    def equilateral(self):
        """Return TRUE if triangle is equilateral (uses math.isclose)."""
        a, b, c = self.threesides()
        return math.isclose(a, b) and math.isclose(b, c) and math.isclose(a, c)

    def isoceles(self):
        """Return TRUE if triangle is isoceles (uses math.isclose)."""
        a, b, c = self.threesides()

        # NOTE: "inclusive" definition in which equilateral is also isoceles
        return math.isclose(a, b) or math.isclose(a, c) or math.isclose(b, c)

    def pythagorean(self):
        """Return TRUE if triangle is a right triangle (uses math.isclose)."""
        abc = self.threesides()
        abc.sort()
        a, b, c = abc

        return math.isclose((a * a) + (b * b), (c * c))

    def area(self):
        """Return triangle area. Always uses Heron's formula."""

        a, b, c = self.threesides()
        s = (a + b + c) / 2

        return math.sqrt(s * (s - a) * (s - b) * (s - c))


if __name__ == '__main__':
    def triangle_tests():

        t345 = Triangle(a=3, b=4, c=5)
        abg345 = (('alpha', 0.6435011087932843),
                  ('beta', 0.9272952180016123),
                  ('gamma', math.pi/2))

        for a, aval in abg345:
            if not math.isclose(getattr(t345, a), aval):
                raise ValueError("cannot establish measurement standards")
        test345s = [{'a': 3, 'b': 4, 'c': 5},                          # SSS
                    {'a': 3, 'b': 4, 'gamma': math.pi/2},              # SAS
                    {'a': 3, 'beta': t345.beta, 'b': 4},               # SSA
                    {'alpha': t345.alpha, 'beta': t345.beta, 'c': 5},  # ASA
                    {'alpha': t345.alpha, 'beta': t345.beta, 'a': 3},  # AAS
                    ]

        for v in test345s:
            tx = Triangle(**v)
            for a in tx.side_names + tx.angle_names:
                if not math.isclose(getattr(tx, a), getattr(t345, a)):
                    raise ValueError(v)
            # tolerance is generous but this is "just a check"
            if not math.isclose(tx.area(), t345.area(), rel_tol=0.000001):
                raise ValueError(tx, tx.area())

        # some that should fail, all w/value error
        vxxx = [{'a': 3, 'b': 4, 'c': 555},              # inequality
                {'a': 3, 'alpha': t345.alpha, 'b': 4},   # ambiguous
                {'a': 3},                                # underspecified
                {'a': 3, 'b': 4, 'c': 5, 'alpha': 1},    # overspecified
                ]
        for v in vxxx:
            try:
                tx = Triangle(**v)
                raise TypeError(v)
            except ValueError:
                pass

        return True

    triangle_tests()
