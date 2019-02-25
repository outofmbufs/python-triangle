# python-triangle

A python class implementing triangle objects.

A Triangle has three sides: `a`, `b`, and `c`. It also has three angles: `alpha`, `beta`, `gamma`.

To create a Triangle, specify three parameters in any one of these combinations:

* Three sides (SSS)
* Two sides and an adjacent angle (SSA)
* Two sides and the included angle (SAS)
* Two angles and the included side (ASA)
* Two angles and an adjacent side (AAS)

Examples:

    # create a classic pythagorean 3/4/5 triangle:
    t = Triangle(a=3, b=4, c=5)

    # create an equilateral triangle:
    t = Triangle(a=8, b=8, c=8)

    # create "the same" triangle, within math tolerances:
    t = Triangle(a=8, beta=math.pi/3, gamma=math.pi/3)

Regardless of how it is created, the resulting `Triangle` object will have all six attributes present: sides `a`, `b`, `c` and respectively-opposing angles `alpha`, `beta`, `gamma`.

When specifying a `Triangle` in `SSS` form, all three sides must obey the *Triangle Inequality* permutations:

    a + b > c
    a + c > b
    b + c > a

When specifying in `SSA` form, some combinations of values may have two triangle solutions. A `ValueError` exception is raised in this case; applications must convert this form into a different, unambiguous, specification (and choose one of the two solutions to do so). A classmethod, `ssa_to_sss`, is available for this purpose (see description).

As an example of an ambiguous case, note these two triangles:

    t1 = Triangle(a=3, b=4, c=1.8284271)
    t2 = Triangle(a=3, b=4, c=3.8284271)

both have `alpha` of 45 degrees; therefore this raises ValueError:

    t = Triangle(a=3, b=4, alpha=math.pi/4)

as there is no way to know which solution is intended. Use `ssa_to_sss` and select the desired solution from the two it will return.

## REPR

The `__repr__` of a `Triangle` has this form:

    Triangle(p1=v1, p2=v2, p3=v3)

where `p1`, `p2`, and `p3` are the three parameter names that were supplied when the object was created. The order they appear in the string is canonical, i.e., will be the same no matter which order they were provided at creation time. The values associated are, of course, the current values which could potentially have been changed since the object was created (although altering those attributes could cause a `Triangle` to not be a triangle!).


## METHODS

* `Triangle(**kwargs)`: Constructor. As already described above.

* `threesides()`: Return all three sides of the Triangle, as a tuple `(a, b, c)`.

* `threeangles()`: Return all three angles of the Triangle, as a tuple.

* `area()`: Compute Triangle's area (uses Heron's formula).

* `opposing(name)`: CLASSMETHOD. Given any attribute name return the name of the attribute opposing it. For example, opposing('a') --> 'alpha'; opposing('alpha') --> 'a'.

* `other_names(*args)`: CLASSMETHOD. Given one or more names, all either side names or angle names, return a list of the unspecified names. For example, other_names('a', 'b') --> 'c'.

* `canonicaltriangle()`: Factory function. Creates a NEW Triangle with the same parameters but with the sides ordered from smallest to largest such that `a <= b <= c`.

* `equilateral()`: Returns True if the `Triangle` is equilateral. Uses `math.isclose()` as the definition of equality (with default `rel_tol`).

* `isoceles()`: Returns True if an equilateral triangle, using `math.isclose()` for comparisons. An equilateral triangle will also be an isoceles triangle.

* `pythagorean()`: Returns True if a Pythagorean (i.e., Right) triangle.

* `ssa_to_sss(**kwargs)`: CLASSMETHOD. Returns a tuple of two dictionaries, the second of which may be None. Each dictionary contains an SSS specification (i.e., an `a`, `b`, and `c`) suitable for use in a `Triangle()` call.

An example of how to use `ssa_to_sss`:

    solution_1, solution_2 = Triangle.ssa_to_sss(a=3, b=4, alpha=math.pi/4)
    t = Triangle(*solution_1)

produces the same `Triangle` that:

    t1 = Triangle(a=3, b=4, c=1.8284271)

produces.

