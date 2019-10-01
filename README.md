# python-triangle

A python class implementing a triangle solver and triangle objects.

A Triangle has three sides: `a`, `b`, and `c`. It also has three angles: `alpha`, `beta`, `gamma`.

To solve (create) a Triangle, specify any one of these combinations of parameters:

* Three sides (SSS)
* Two sides and an adjacent angle (SSA)
* Two sides and the included angle (SAS)
* Two angles and the included side (ASA)
* Two angles and an adjacent side (AAS)

The class invokes the appropriate triangle solution algorithm and computes the remaining parameters from the parameters given.

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

When specifying in `SSA` form, some combinations of values may have two triangle solutions. By default, a `ValueError` exception is raised when this happens. 

As an example of an ambiguous case, note these two triangles:

    t1 = Triangle(a=3, b=4, c=1.8284271)
    t2 = Triangle(a=3, b=4, c=3.8284271)

both have `alpha` of 45 degrees; therefore this raises ValueError:

    t = Triangle(a=3, b=4, alpha=math.pi/4)

as there is no way to know which solution is intended. There are two ways to handle this case:

1.  Use `sss_solutions` and select the desired solution from the two it will return.

2. Specify a `triangle_filter`.

If the optional `triangle_filter` parameter is specified to `Triangle`, it will be invoked at `__init__` time like this:

    ok = triangle_filter(t)

where `t` is a candidate `Triangle` object. The filter should return True or False according to whether the triangle is "acceptable" or not.

The call signature is compatible with using `Triangle.acute`, `Triangle.obtuse`, etc as filters. After filtering,  there must be exactly one solution or a `ValueError` is raised.

So, for example:

    t = Triangle(a=3, b=4, alpha=math.pi/4,
                 triangle_filter=Triangle.obtuse)

will return the same triangle shown as `t1` above. Similarly:

    t = Triangle(a=3, b=4, alpha=math.pi/4,
                 triangle_filter=Triangle.acute)

will return `t2`.

CAUTION: A triangle can be "not acute" and "not obtuse" ... it can be pythagorean. Floating point fuzziness must be understood with care when using filters especially if any of the implied angles are very close to `pi/2`.

As a convenience, a classmethod `coordinates_to_sss` converts an iterable of three vertex coordinates (each coordinate an (x, y) tuple) into a dict of three side lengths using `d = sqrt(dx^2 + dy^2)`. So, for example:

    coords = ((45, 42), (42, 42), (45, 46))
    t = Triangle(**Triangle.coordinates_to_sss(coords))

is yet another way to make a 3/4/5 triangle.


## REPR

The `__repr__` of a `Triangle` has this form:

    Triangle(p1=v1, p2=v2, p3=v3)

where `p1`, `p2`, and `p3` are the three parameter names that were supplied when the object was created. The order they appear in the string is canonical, i.e., will be the same no matter which order they were provided at creation time. The values associated are, of course, the current values which could potentially have been changed since the object was created (although altering those attributes could cause a `Triangle` to not be a triangle!).


## METHODS

* t = `Triangle(**kwargs)`: Constructor. As already described above.

* t.`threesides()`: Return all three sides of `t`, as a tuple `(a, b, c)`.

* t.`threeangles()`: Return all three angles of `t`, as a tuple.

* t.`area()`: Return area of `t`.

* t.`altitude(basename)`: Return altitude (height) relative to the named base.

* Triangle.`opposing_name(name)`: Given any attribute name return the name of the attribute opposing it. For example, opposing('a') --> 'alpha'; opposing('alpha') --> 'a'.

* t.`opposing(name)`: Given any attribute name return the VALUE of the attribute opposing it. For example, t.opposing('a') will return t.alpha.

* Triangle.`other_names(*args)`: Given one or more names, all either side names or angle names, return a list of the unspecified names. For example, other_names('a', 'b') --> 'c'.

* t2 = t.`canonicaltriangle()`: Factory function. Creates a NEW Triangle with the same parameters but with the sides ordered from smallest to largest such that `a <= b <= c`.

* t.`scale(factor)`: Adjusts (multiplies) all three sides by `factor`.

* t.`equilateral()`: Returns True if the `t` is equilateral. Uses `math.isclose()` as the definition of equality (with default `rel_tol`).

* t.`isoceles()`: Returns True if `t` is an equilateral triangle, using `math.isclose()` for comparisons. An equilateral triangle will also be an isoceles triangle.

* t.`pythagorean()`: Returns True if `t` is a Pythagorean (i.e., Right) triangle. Can be used as a `triangle_filter`. Angles are compared to pi/2 using `isclose`.

* t.`acute()`: Returns True if `t` is an acute triangle, that is, all angles are less than pi/2. If `t` is `pythagorean` it will not be `acute`. Can be used as a `triangle_filter`.

* t.`obtuse()`: Returns True if `t` is an obtuse triangle, that is, there is an angle greater than pi/2. If `t` is `pythagorean` it will not be `obtuse`. Can be used as a `triangle_filter`.

* t.`not_acute()`: Returns True if `t` is `obtuse` or `pythagorean`. Can be used as a `triangle_filter`.

* t.`not_obtuse()`: Returns True if `t` is `acute` or `pythagorean`. Can be used as a `triangle_filter`.

* Triangle.`sss_solutions(**kwargs)`: Given three parameters (e.g., two sides and one angle), returns a tuple of two dictionaries, the second of which may be None. Each dictionary contains an SSS specification (i.e., an `a`, `b`, and `c`) suitable for use in a `Triangle()` call. This is primarily useful in ambiguous SSA cases where there are two possible solutions (as otherwise the parameters could also just be given to Triangle() directly).

* Triangle.`coordinates_to_sss(coordinates)`: Given an iterable of length three, each element being itself an (x, y) tuple, return a dictionary of side lengths suitable for use to create a Triangle.

* t.`similar(t2)`: Returns True if `t` and `t2` are "similar". Two triangles are similar if one can be converted to the other by any combination of linearly scaling (all) the sides and performing rotation/reflection. Uses isclose()

### More about `sss_solutions`

An example of how to use `sss_solutions`:

    solution_1, solution_2 = Triangle.sss_solutions(a=3, b=4, alpha=math.pi/4)
    t = Triangle(**solution_1)

produces the same `Triangle` that:

    t1 = Triangle(a=3, b=4, c=3.828427124746191)

produces.

## Subclassing
Three class attributes can be overridden by subclasses if desired for customizing Triangles:

* `side_names`: tuple of three names (each a string) of each respective side of a Triangle. Default is `('a', 'b', 'c')`.

* `angle_names`: tuple of three of each respective angle of a Triangle. Default is `('alpha', 'beta', 'gamma')`.

    NOTE: The order of entries in `side_names` and `angle_names` defines an opposition relationship; i.e., `angle_names[i]` is the angle in opposition to `side_names[i]`.

* `isclose`: method for comparing two floating-point values to see if they are "approximately equal". Override the default of `math.isclose` if a different tolerance or methodology is required.



EXAMPLES:

This subclass renames the angles as A1, A2, and A3:

    class TriangleX(Triangle):
        angle_names = ('A1', 'A2', 'A3')

    right_triangle = TriangleX(A1=0.6435011087932843,
                               A3=math.pi/2,
                               a=3)


This subclass changes the comparison method to be EXACT. Note that this could have surprising results for some methods (e.g., the isoceles and equilateral predicates), due to floating point inexactness:

    class TriangleQ(Triangle):
        @staticmethod
        def isclose(a, b):
            return a == b


