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

    # function called to determine when floats are "close" (can be overridden)
    isclose = math.isclose

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
    #          (classmethod) sss_solutions to get both solution forms.
    # * AAAS:  Redundant; not accepted. Instead: omit one A --> AAS/ASA
    #

    def __init__(self, **kwargs):
        """Create a Triangle given three params (SSS/SSA/SAS/AAS/ASA).

        Examples:
           t = Triangle(a=3, b=4, c=5)
           t = Triangle(a=8, alpha=math.pi/3, beta=math.pi/3)
        """

        # sv: NAMES of sides given, av: NAMES of angles given
        sv, av = self.__kwargshelper(self, kwargs)

        # remember the original parameters, mostly for __repr__
        # NOTE that this puts them into a canonical order (deliberately).
        # Therefore it is a list of tuples rather than a dict, although
        # the newest python dict semantics are now order-preserving as well.
        self.__origparams = [
            (n, kwargs[n])
            for n in self.side_names + self.angle_names if n in sv + av]

        # all valid forms have exactly three elements in aggregate
        total = len(sv) + len(av)
        if total > 3:
            raise ValueError(f"{self} is overspecified")
        elif total < 3:
            raise ValueError(f"{self} is underspecified")

        # dispatch according to # of angles ... THIS IS MAYBE TOO CUTE???
        (self._sss, self._ssa_sas, self._aas_asa)[len(av)](sv, av, kwargs)

    #
    # Parses kwargs, collating them into angles and sides (returned)
    # and optionally sets them as attributes if given a target object
    # Raises ValueError for various sanity check errors (sides < 0, etc)
    #
    @classmethod
    def __kwargshelper(cls, _targetobject, kwargs):
        """Return 2 lists: (side names, angle names). Optionally set attrs."""
        sv = []
        av = []
        for k, v in kwargs.items():
            # negative/zero is illegal for both angles and sides
            if v <= 0:
                raise ValueError(f"{k!r} (={v}) must be > 0")
            if k in cls.angle_names:
                if v >= math.pi:
                    raise ValueError(f"angle {k!r} (={v}) >= π")
                av.append(k)
            elif k in cls.side_names:
                sv.append(k)
            else:
                raise TypeError(f"{cls} got unexpected keyword arg {k!r}")
            if _targetobject:
                setattr(_targetobject, k, v)

        return sv, av

    def __repr__(self):
        # Whatever three attributes were provided to __init__ are the repr
        # (but, of course, with whatever their current values are).
        s = f"{self.__class__.__name__}("
        for attr, origv in self.__origparams:
            s += f"{attr}={getattr(self, attr)}, "

        return s.rstrip(", ") + ")"

    def __multiget(self, *attrs):
        """Return a list of the values of given attributes."""
        return [getattr(self, a) for a in attrs]

    @classmethod
    def sss_solutions(cls, **kwargs):
        """Return two SSS dicts, (1 per solution). 2nd dict might be None.

        Primarily useful for ambiguous SSA cases, to get both solutions, e.g.:
          sss_1, sss_2 = Triangle.sss_solutions(a=3, b=4, alpha=math.pi/4)
          t = Triangle(**sss_1)
        """

        sv, av = cls.__kwargshelper(None, kwargs)

        # If this is NOT the (potentially) ambiguous SSA case, just
        # make a Triangle and report the sole SSS solution.
        # NOTE (FRAGILE!) --
        #    Triangle() calls this method for the SSA case so this
        #    code has to carefully weed out that infinite recursion

        # note: don't have to test len(av) > 0 before opposing_name because
        #       len(av) != 1 would already short-circuit that case
        if len(sv) != 2 or len(av) != 1 or cls.opposing_name(av[0]) not in sv:
            t = cls(**kwargs)
            return {n: getattr(t, n) for n in t.side_names}, None

        # SSA case falls through to here.
        # (Note that SAS was weeded out in the opposing_name test)
        # Let:
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
            raise ValueError("no angle solution for {}".format(
                    cls.opposing_name(b_name)))

        # third angle is whatever is left
        gamma = math.pi - (alpha + beta)
        if gamma <= 0:
            raise ValueError("no angle solution for {}".format(
                    cls.opposing_name(c_name)))

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
            d1, d2 = self.sss_solutions(**kwargs)
            if d2 is not None:
                raise ValueError(f"{self} is ambiguous")

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
        if gamma <= 0:
            raise ValueError(f"{self}: no solution for third angle")

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
            raise ValueError(f"{self} fails triangle inequality tests")
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
        raise ValueError(f"{name!r} not found in {self}")

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
        """Return TRUE if triangle is equilateral (uses isclose)."""
        a, b, c = self.threesides()
        return self.isclose(a, b) and self.isclose(b, c) and self.isclose(a, c)

    def isoceles(self):
        """Return TRUE if triangle is isoceles (uses isclose)."""
        a, b, c = self.threesides()

        # NOTE: "inclusive" definition in which equilateral is also isoceles
        return self.isclose(a, b) or self.isclose(a, c) or self.isclose(b, c)

    def pythagorean(self):
        """Return TRUE if triangle is a right triangle (uses isclose)."""
        abc = self.threesides()
        abc.sort()
        a, b, c = abc

        return self.isclose((a * a) + (b * b), (c * c))

    def area(self):
        """Return triangle area. Always uses Heron's formula."""

        a, b, c = self.threesides()
        s = (a + b + c) / 2

        return math.sqrt(s * (s - a) * (s - b) * (s - c))

    def altitude(self, basename):
        """Return the geometric 'altitude' (height) from the given base."""

        if basename not in self.side_names:
            raise ValueError(f"{basename} is not a side name in {self}")
        return (2 * self.area()) / getattr(self, basename)

    def similar(self, t):
        """Return True if triangle t is geometrically similar to this one.

        Uses isclose(). Two triangles are similar if one can be converted
        to the other by any combination of linearly scaling (all) the sides
        and performing rotation reflection.
        """

        # sorting the angles is essentially rotation/reflection as needed
        return all(map(self.isclose,
                       sorted(self.threeangles()),
                       sorted(t.threeangles())))

    # obviously this is just a convenience function as all it does
    # is multiply each side by the given factor.
    def scale(self, factor):
        """Scale a triangle by the given factor."""
        if factor <= 0:
            raise ValueError(f"{self} illegal scale factor {factor}")
        for n in self.side_names:
            setattr(self, n, getattr(self, n) * factor)


if __name__ == '__main__':
    import unittest

    class TriangleTestMethods(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            cls.t345 = Triangle(a=3, b=4, c=5)
            cls.abg345 = (('alpha', 0.6435011087932843),
                          ('beta', 0.9272952180016123),
                          ('gamma', math.pi/2))
            for a, v in cls.abg345:
                if not cls.fuzzy_equal(getattr(cls.t345, a), v):
                    raise ValueError("cannot establish baseline angles")

        @staticmethod
        def fuzzy_equal(a, b):
            return abs(a - b) < .000001

        def test_triangle_solutions(self):
            t345 = self.t345
            alpha, beta, gamma = t345.threeangles()
            test345s = [
                {'a': 3, 'b': 4, 'c': 5},                   # SSS
                {'a': 3, 'b': 4, 'gamma': math.pi/2},       # SAS
                {'a': 3, 'b': 4, 'gamma': gamma},           # SAS (same)
                {'a': 3, 'beta': beta, 'b': 4},             # SSA
                {'alpha': alpha, 'beta': beta, 'c': 5},     # ASA
                {'alpha': alpha, 'beta': beta, 'a': 3},     # AAS
                ]

            for v in test345s:
                tx = Triangle(**v)
                for a in tx.side_names + tx.angle_names:
                    self.assertTrue(
                        self.fuzzy_equal(getattr(tx, a), getattr(t345, a)))

                self.assertTrue(t345.similar(tx))
                self.assertTrue(self.fuzzy_equal(tx.area(), t345.area()))

        def test_nonsolutions(self):
            alpha, beta, gamma = self.t345.threeangles()

            # these should fail, all w/value error
            vxxx = [
                {'a': 3, 'b': 4, 'c': 555},              # inequality
                {'a': 3, 'alpha': alpha, 'b': 4},        # ambiguous
                {'a': 3},                                # underspecified
                {'a': 3, 'b': 4, 'c': 5, 'alpha': 1},    # overspecified
                {'a': 0, 'b': 4, 'c': 5},                # <= 0
                {'a': 3, 'beta': 4, 'c': 5},             # beta too big
                {'a': 4, 'b': 4.1, 'alpha': math.pi/2},  # no beta works
                                                         # angles too big
                {'a': 4, 'beta': 0.75*math.pi, 'gamma': 0.75*math.pi},
                ]
            for v in vxxx:
                self.assertRaises(ValueError, Triangle, **v)

        def test_ssssolutions(self):
            # Should generate two solutions
            d1, d2 = Triangle.sss_solutions(a=3, b=4, alpha=self.t345.alpha)

            self.assertIsNotNone(d1)
            self.assertIsNotNone(d2)

            # one or the other should have come up with t345.
            self.assertTrue(self.t345.similar(Triangle(**d1)) or
                            self.t345.similar(Triangle(**d2)))

    unittest.main()
