# MIT License
#
# Copyright (c) 2019 Neil Webber
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from collections import ChainMap
from itertools import combinations
import math


class Triangle:
    """Class implementing geometric triangles."""
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
    # ... define those names. The solver algorithm uses a level of indirection
    # when accessing attributes, to allow full generality of specifications.
    # For example, an SSA specification could be
    #                       side a, side b, angle beta
    # but also could be:    side b, side c, angle gamma
    # Consequently, the solver doesn't access attributes directly by name.
    # Instead it accesses them indirectly/algorithmically, to allow full
    # flexibility for SSA/SAS/AAS/ASA specifications. All other methods also
    # use that indirection.
    #
    # A side benefit, preserved through careful coding throughout to never
    # reference attributes by name directly, is that subclasses can redefine
    # the attribute names themselves by overriding the above tuples. Not clear
    # how useful it is, but once the solver was written that way... why not.
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
    #    AAS  -- two angles and a non-included side
    #    ASA  -- two angles and the included side
    #
    # Unspecified triangle attributes are calculated from the given values
    # using float/trig operations. Accordingly, they are rarely *exact*.
    #
    # EXAMPLES:
    #
    #   # SSS example
    #   t1 = Triangle(a=3, b=4, c=5)
    #
    #   # AAS example
    #   t2 = Triangle(a=3, alpha=0.6435011087932843, gamma=math.pi/2)
    #
    # Note that the distinction between AAS vs ASA, or SSA vs SAS, is
    # entirely about *which* angles or sides are given, not (obviously?)
    # the order of the arguments.
    #
    # In the above examples, t1 and t2 both specify the same classic 3/4/5
    # pythagorean triangle, but it is unlikely that t1.c == t2.c because of
    # floating point and trig function precision.
    #
    # NOTES:
    # * SSS:   The three sides must satisfy the triangle inequality
    # * SSA:   Raises exception (by default) if there are two solutions;
    #          use (classmethod) sss_solutions to get both solution forms.
    #          Alternatively, specify a triangle_filter (see below)
    # * AAAS:  Redundant; not accepted. Instead: omit one A --> AAS/ASA
    #
    # Optional parameter triangle_filter can be used to constrain solutions.
    # The filter is invoked at __init__ time like this:
    #
    #       ok = triangle_filter(t)
    #
    # where 't' is a Triangle object. It should return True or False
    # according to whether the triangle is "acceptable" or not.
    #
    # The call signature is compatible with using Triangle.acute,
    # Triangle.obtuse, etc as filters. After filtering solutions there
    # must be EXACTLY ONE solution or a ValueError is raised.
    # The expected use case for a triangle_filter is disambiguating
    # SSA solutions, so for example if an acute triangle is desired:
    #
    #    t = Triangle(a=3, b=4, alpha=0.65, triangle_filter=Triangle.acute)
    #
    # will work, whereas without the filter it raises ValueError because
    # there are two solutions to this set of SSA parameters.
    #
    # CAUTION: Triangle classification is a three-way function, any given
    # triangle will be either acute, obtuse, OR pythagorean. It may be
    # the case that Triangle.not_acute (or Triangle.not_obtuse) is a
    # better filter than the positive (acute/obtuse) predicate, especially
    # if any angles are within floating point tolerance of pi/2.
    #
    def __init__(self, triangle_filter=None, **kwargs):
        """Create a Triangle given three params (SSS/SSA/SAS/AAS/ASA).

        Examples:
           t = Triangle(a=3, b=4, c=5)
           t = Triangle(a=8, alpha=math.pi/3, beta=math.pi/3)

        Argument triangle_filter can be used to choose when SSA is ambiguous.
        See documentation for details.
        """

        # The __repr__ is the original parameters, in a canonical order.
        self.__origparams = [
            n for n in self.side_names + self.angle_names if n in kwargs]

        # Use the solver, turn all into SSS (possibly two solutions), filter
        # NOTE: There is a (subtle) recursion here if a triangle_filter
        #       was specified -- construct a trial triangle from SSS
        #       (and no filter) and pass it to the given filter to test it.
        solns = [s for s in self.sss_solutions(**kwargs)
                 if s is not None and (triangle_filter is None or
                                       triangle_filter(self.__class__(**s)))]

        if len(solns) != 1:
            raise ValueError(f"{kwargs} has {len(solns)} solutions")

        # set all the attrs, use kwargs in favor of computed sides or angles
        for k, v in ChainMap(kwargs, self.compute_angles(*solns)).items():
            setattr(self, k, v)

    #
    # Checks legality of kwargs
    # Raises ValueError for various sanity check errors (sides < 0, etc)
    #
    @classmethod
    def __check_kwargs(cls, kwargs):
        for k, v in kwargs.items():
            if v <= 0:
                raise ValueError(f"{k!r} (={v}) must be > 0")
            if k in cls.angle_names:
                if v >= math.pi:
                    raise ValueError(f"angle {k!r} (={v}) >= π")
            elif k not in cls.side_names:
                raise TypeError(f"{cls} got unexpected keyword arg {k!r}")

    def __repr__(self):
        s = f"{self.__class__.__name__}("
        for attr in self.__origparams:
            s += f"{attr}={getattr(self, attr)}, "

        return s.rstrip(", ") + ")"

    @classmethod
    def sss_solutions(cls, **kwargs):
        """Return two SSS dicts, (1 per solution), 2nd of which might be None.

        This is the heart of the triangle solver and is used by __init__().
        It can also be useful to invoke directly for ambiguous SSA cases,
        to get both solutions, e.g.:
          sss_1, sss_2 = Triangle.sss_solutions(a=3, b=4, alpha=math.pi/4)
          t = Triangle(**sss_1)
        """

        cls.__check_kwargs(kwargs)
        sv = [k for k in cls.side_names if k in kwargs]
        av = [k for k in cls.angle_names if k in kwargs]

        # all valid forms have exactly three elements in aggregate
        if len(kwargs) != 3:
            raise ValueError(f"{kwargs} over/under specified")

        # 0, 1, 2, or 3 sides given:
        if len(sv) == 1:
            return cls.__aas_asa(sv, av, kwargs)
        elif len(sv) == 2:
            return cls.__sas_ssa(sv, av, kwargs)
        elif len(sv) == 3:
            # SSS case; solution is as given but verify triangle rules
            a, b, c = kwargs.values()
            if a + b <= c or a + c <= b or b + c <= a:
                raise ValueError(f"{kwargs} fails triangle inequality tests")
            return kwargs, None

        # reaching here implies 0 sides given
        raise ValueError(f"{kwargs} must specify at least one side")

    @classmethod
    def compute_angles(cls, sss):
        """Return a complete (angles and sides) triangle dict, given SSS."""
        ax = sss.copy()
        for angle_name in cls.angle_names:
            oppsidename = cls.opposing_name(angle_name)
            bname, cname = cls.other_names(oppsidename)
            a = sss[oppsidename]
            b = sss[bname]
            c = sss[cname]
            angle = math.acos(((b*b) + (c*c) - (a*a)) / (2*b*c))
            ax[angle_name] = angle
        return ax

    @classmethod
    def coordinates_to_sss(cls, coordinates):
        """Return SSS dict given ((x0, y0), (x1, y1), (x2, y2))"""
        if len(coordinates) != 3:
            raise ValueError(f"{coordinates} must be three (x,y) tuples")
        sss = {}
        for twopts, k in zip(combinations(coordinates, 2), cls.side_names):
            v0, v1 = twopts
            dx = v1[0]-v0[0]
            dy = v1[1]-v0[1]
            sss[k] = math.sqrt((dx * dx) + (dy * dy))
        return sss

    @classmethod
    def __sas_ssa(cls, sv, av, pm):
        """Return two SSS dicts given an SSA or SAS set of parameters.

        The second dict will be None unless there are two solutions.
        """
        oppside_name = cls.opposing_name(av[0])
        if oppside_name in sv:
            # SSA
            # Let:
            #   c be the side that WASN'T given
            #   alpha be the given angle
            #   a be the opposing side (it can be either side given)
            #   b be the other side (the one that isn't "a")
            # NOTE: confusingly, these variable name choices have no relation
            #       to the particular parameter/attributes being used/set.
            #       Not merely because those names can be overridden, but
            #       more importantly because any two sides could be a and b
            #       in these calculations (and any angle could be alpha).
            #       This is either obvious, or it's not. :)
            c_name = cls.other_names(*sv)[0]
            oc_name = cls.opposing_name(c_name)
            alpha = pm[av[0]]
            a_name = cls.opposing_name(av[0])
            a = pm[a_name]
            b_name = cls.other_names(a_name, c_name)[0]
            ob_name = cls.opposing_name(b_name)
            b = pm[b_name]

            # Law of Sines a/sin(alpha) = b/sin(beta) = c/sin(gamma)
            alpha_sin = math.sin(alpha)
            try:
                beta = math.asin((alpha_sin * b) / a)
            except ValueError:
                raise ValueError(f"no angle solution for {ob_name}")

            # third angle is whatever is left
            gamma = math.pi - (alpha + beta)
            if gamma <= 0:
                raise ValueError(f"no angle solution for {oc_name}")

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
        else:
            # SAS - much simpler
            a = pm[sv[0]]
            c = pm[sv[1]]
            beta = pm[av[0]]
            b = math.sqrt((a*a) + (c*c) - (2 * a * c * math.cos(beta)))
            pm[cls.opposing_name(av[0])] = b
            d1 = {s: pm[s] for s in cls.side_names}
            d2 = None

        return d1, d2

    @classmethod
    def __aas_asa(cls, sv, av, pm):
        """Return two SSS dicts given an AAS or ASA set of parameters.

        The second dict will ALWAYS be None, but is returned to be
        consistent with __sas_ssa and sss_solutions expectations.
        """

        # gamma name is whichever angle name that wasn't given
        # gamma, the third angle, is whatever is left after the other two
        gamma = math.pi
        for a in cls.angle_names:
            if a in pm:
                gamma -= pm[a]
            else:
                gamma_name = a
        if gamma <= 0:
            raise ValueError(f"{pm}: no solution for third angle")

        pm[gamma_name] = gamma

        # now that all three angles are known... law of Sines
        s0 = pm[sv[0]]
        ratio = s0 / math.sin(pm[cls.opposing_name(sv[0])])
        for s in cls.side_names:
            if s != sv[0]:
                sx = math.sin(pm[cls.opposing_name(s)]) * ratio
                pm[s] = sx
        return {s: pm[s] for s in cls.side_names}, None

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
    def other_names(cls, _name, *more):
        """Given 1 or more side names or angle names, return the others."""

        # The explicit "_name" in def forces python to enforce "at least
        # one argument required" ... then this puts all the args back
        # into one tuple for convenience
        names = (_name, *more)

        if names[0] in cls.side_names:
            candidates = cls.side_names
        else:
            candidates = cls.angle_names

        for n in names:
            if n not in candidates:
                raise ValueError(f"mismatching or unknown name '{n}'")

        return [x for x in candidates if x not in names]

    def opposing(self, name):
        """Return opposing angle/side VALUE for given side/angle NAME."""
        opp = self.opposing_name(name)
        if opp is not None:
            return getattr(self, opp)
        raise ValueError(f"{name!r} not found in {self}")

    def threesides(self):
        """a, b, c = t.threesides()"""
        return [getattr(self, s) for s in self.side_names]

    def threeangles(self):
        """alpha, beta, gamma = t.threeangles()"""
        return [getattr(self, a) for a in self.angle_names]

    def canonicaltriangle(self):
        """Return a new triangle with sides in size order low-to-high."""
        sides = self.threesides()
        return Triangle(**dict(zip(self.side_names, sorted(sides))))

    def copy(self):
        """Return new copy of a Triangle."""
        t = self.__class__(**{k: getattr(self, k) for k in self.__origparams})
        # because there's no guarantee attrs haven't bashed inconsistently...
        for k in self.side_names + self.angle_names:
            setattr(t, k, getattr(self, k))
        return t

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
        a, b, c = sorted(self.threesides())

        return self.isclose((a * a) + (b * b), (c * c))

    def acute(self):
        """Return TRUE if not pythagorean and all three angles are < 90."""
        # To handle floating point (im)precision, if the triangle is
        # "close enough" to being pythagorean (right triangle), it is
        # not acute. If it is not close enough, then there is no further
        # concern about floating point fuzziness.
        if self.pythagorean():
            return False
        return all(a < math.pi/2 for a in self.threeangles())

    def not_acute(self):
        """Convenience for ssa_filter use; allows pythagorean or obtuse."""
        return self.pythagorean() or self.obtuse()

    def obtuse(self):
        """Return TRUE if not pythagorean and all three angles are > 90."""
        return not self.pythagorean() and not self.acute()

    def not_obtuse(self):
        """Convenience for ssa_filter use; allows pythagorean or acute."""
        return self.pythagorean() or self.acute()

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

    # Factory to make a Triangle subclass from a string specification.
    # Handy for simple geometry problems where the angles are given
    # explicit names and the sides are named from their adjacent angles.
    #
    #   TX = fromnames("ABC")
    #
    # is equivalent to:
    #    class TX(Triangle):
    #       angle_names = ('A', 'B', 'C')
    #       side_names = ('BC', 'AC', 'AB')   # note order; opposing sides
    #
    @classmethod
    def fromnames(cls, s, /, *, name=None):
        if len(s) != 3:
            raise ValueError(f"names string ({s!r}) must be length 3")
        angles = tuple(s)
        sides = (angles[1] + angles[2],
                 angles[0] + angles[2],
                 angles[0] + angles[1])
        return type(name or f"fromnames.{s}",
                    (Triangle,),
                    dict(angle_names=angles, side_names=sides))


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

        def test_345triangle_solutions(self):
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

        def test_pyth(self):
            self.assertTrue(Triangle.pythagorean(self.t345))
            a, b, c = self.t345.threesides()
            t543 = Triangle(a=c, b=b, c=a)
            self.assertTrue(t543.pythagorean())

        def test_triangle_solutions(self):
            # these test vectors have been worked out by hand
            tests = [
                ({'a': 3, 'b': 4, 'alpha': 0.6724600056836807,
                  'triangle_filter': Triangle.acute},
                 {'c': 4.8}),
                ({'a': 3, 'b': 4, 'alpha': 0.6724600056836807,
                  'triangle_filter': Triangle.obtuse},
                 {'c': 1.4583333333}),
                ({'alpha': 0.907922503, 'beta': 1.19862779, 'c': 1.2},
                 {'a': 1.1, 'b': 1.3, 'gamma': 1.03504236059}),
                ({'a': 1.1, 'beta': 1.19862779, 'c': 1.2},
                 {'alpha': 0.907922503, 'b': 1.3, 'gamma': 1.03504236059}),
                ]

            for v, rslts in tests:
                tx = Triangle(**v)
                for a in rslts:
                    self.assertTrue(
                        self.fuzzy_equal(getattr(tx, a), rslts[a]))

        def test_similar(self):
            self.assertTrue(self.t345.similar(Triangle(a=5, b=3, c=4)))
            self.assertTrue(self.t345.similar(self.t345))
            for f in (0.1, 1.01, 2, 44, .00000001, 1e23):
                for a, b, c in ((3, 4, 5), (3, 5, 4),
                                (4, 3, 5), (4, 5, 3),
                                (5, 3, 4), (5, 4, 3)):
                    tx = Triangle(a=a, b=b, c=c)
                    tx.scale(f)
                    self.assertTrue(self.t345.similar(tx))

            self.assertFalse(self.t345.similar(Triangle(a=5, b=5, c=4)))

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

        def test_altitude(self):
            # compute the altitudes relative to all three sides of
            # a precomputed result in various permutations. Overkill.
            tv = (((30, 40, 50), (40, 30, 24)),
                  ((40, 30, 50), (30, 40, 24)),
                  ((50, 30, 40), (24, 40, 30)),
                  ((50, 40, 30), (24, 30, 40)))
            for sv, hv in tv:
                t = Triangle(**dict(zip(Triangle.side_names, sv)))
                for sn, av in zip(Triangle.side_names, hv):
                    self.assertEqual(t.altitude(sn), av)

        def test_othernames(self):
            tv = ((('a',), ('b', 'c')),
                  (('a', 'b'), ('c')),
                  (('a', 'alpha'), None),
                  (('alpha', 'gamma', 'beta'), ()),
                  (('c',), ('a', 'b')))
            for names, expected in tv:
                if expected is None:
                    self.assertRaises(ValueError, Triangle.other_names, *names)
                else:
                    r = sorted(list(Triangle.other_names(*names)))
                    x = sorted(list(expected))
                    self.assertEqual(r, x)

        def test_canon(self):
            t = Triangle(a=5, b=4, c=3)
            a, b, c = t.canonicaltriangle().threesides()
            self.assertTrue(a <= b)
            self.assertTrue(b <= c)

        def test_opposingname(self):
            for a, s in zip(Triangle.angle_names, Triangle.side_names):
                self.assertEqual(Triangle.opposing_name(a), s)
                self.assertEqual(Triangle.opposing_name(s), a)

            self.assertEqual(Triangle.opposing_name('rumplestiltskin'), None)

        def test_coordinates(self):
            # various forms of a 3,4,5 triangle specified as coordinates
            tv = (((0, 0), (3, 0), (3, 4)),
                  ((100, 100), (103, 100), (103, 104)),
                  ((100, 200), (103, 200), (103, 204)),
                  ((100, -200), (103, -200), (103, -204)),
                  ((-100, -200), (-103, -200), (-103, -204)),
                  ((-200, -100), (-203, -100), (-203, -104)))
            for coords in tv:
                sss = Triangle.coordinates_to_sss(coords)
                self.assertTrue(self.t345.similar(Triangle(**sss)))

        def test_subclass_renaming(self):
            class PQRTriangle(Triangle):
                side_names = ('p', 'q', 'r')
                angle_names = ('huey', 'dewey', 'louie')

            pqr345 = PQRTriangle(p=3, q=4, r=5)
            pcopy = pqr345.copy()
            for t in (pqr345, pcopy):
                self.assertTrue(self.t345.similar(t))
                self.assertTrue(t.similar(self.t345))
                self.assertTrue(math.isclose(t.louie, math.pi/2))

        def test_fromnames(self):
            # similar to subclass but create class via fromnames
            PQRTriangle = Triangle.fromnames('PQR')
            pqr345 = PQRTriangle(PQ=3, QR=4, PR=5)
            self.assertTrue(pqr345.similar(self.t345))
            self.assertTrue(math.isclose(pqr345.Q, math.pi/2))

    unittest.main()
