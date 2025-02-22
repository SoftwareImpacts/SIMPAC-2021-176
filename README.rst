PBA
========

PBA is a probability bound analysis library for Python that allows one to create and calculate with probability distributions, intervals, and probability boxes (p-boxes) within Python.

Probability distributions can be specified using ``pba.distname(**args)`` where *distname* is any of the named distributions that scipy.stats supports.  For instance,   pba.laplace(2,1) specifies a Laplace distribution with mean and variance 2. P-boxes can be created by using interval arguments for these distributions.  Intervals can be created using ``pba.I(lo, hi)`` where *lo* and *hi* are expressions for the lower and upper limits of the interval.

Features
--------

- Interval arithmetic (see https://en.wikipedia.org/wiki/Interval_arithmetic)
- P-box arithmetic (see https://en.wikipedia.org/wiki/Probability_bounds_analysis)

Installation
-------------

Install pba by running

    pip install pba

Contribute & Support
--------------------

If you are having issues or would like to help with development or have intersting use cases, please let us know.
You can email nickgray@liv.ac.uk.

License
--------

The project is licensed under the MIT License.
