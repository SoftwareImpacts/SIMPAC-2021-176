from typing import *

import numpy as np
from matplotlib import pyplot as plt

from .interval import Interval
from .copula import Copula
from .core import env

__all__ = [
    # import class
    'Pbox',
    'mixture',
    # import non distribution functions
    'box', 'mmms'
]

class Pbox:

    STEPS = 200

    def __init__(self, left=None, right=None, steps=None, shape=None, mean_left=None, mean_right=None, var_left=None, var_right=None, interpolation='linear'):

        if steps is None: steps = Pbox.STEPS

        if (left is not None) and (right is None):
            right = left

        if left is None and right is None:
            left = np.array((-np.inf))
            right = np.array((np.inf))

        if isinstance(left, Interval):
            left = np.array([left.left]*steps)
        elif not isinstance(left, np.ndarray):
            left = np.array(left)


        if isinstance(right, Interval):
            right = np.array([right.right]*steps)
        elif not isinstance(left, np.ndarray):
            right = np.array(right)
        
        # if len(left) == len(right) and len(left) != steps:
        #     print("WARNING: The left and right arrays have the same length which is inconsistent with steps.")

        if len(left) != steps:
            left = interpolate(left, interpolation=interpolation, left=False, steps=steps)

        if len(right) != steps:
            right = interpolate(right, interpolation=interpolation, left=True, steps=steps)

        self.left = left
        self.right = right

        self.steps = steps
        self.shape = shape
        self.mean_left = -np.inf
        self.mean_right = np.inf
        self.var_left = 0
        self.var_right = np.inf

        self._computemoments()
        if shape is not None: self.shape = shape
        if mean_left is not None: self.mean_left = np.max([mean_left, self.mean_left])
        if mean_right is not None: self.mean_right = np.min([mean_right, self.mean_right])
        if var_left is not None: self.var_left = np.max([var_left, self.var_left])
        if var_right is not None: self.var_right = np.min([var_right, self.var_right])
        self._checkmoments()

    def __repr__(self):
        if self.mean_left == self.mean_right:
            mean_text = f'{round(self.mean_left, 4)}'
        else:
            mean_text = f'[{round(self.mean_left, 4)}, {round(self.mean_right, 4)}]'

        if self.var_left == self.var_right:
            var_text = f'{round(self.var_left, 4)}'
        else:
            var_text = f'[{round(self.var_left, 4)}, {round(self.var_right, 4)}]'

        range_text = f'[{round(np.min([self.left, self.right]), 4), round(np.max([self.left, self.right]), 4)}'

        if self.shape is None:
            shape_text = ' '
        else:
            shape_text = f' {self.shape}' # space to start; see below lacking space

        return f'Pbox: ~{shape_text}(range={range_text}, mean={mean_text}, var={var_text})'

    __str__ = __repr__

    def __iter__(self):
        for val in np.array([self.left,self.right]).flatten():
            yield val


    def __neg__(self):
        if self.shape in ['uniform','normal','cauchy','triangular','skew-normal']:
            s = self.shape
        else:
            s = ''

        return Pbox(
            left = -np.flip(self.right),
            right = -np.flip(self.left),
            shape = s,
            mean_left = -self.mean_right,
            mean_right = -self.mean_left,
            var_left = self.var_left,
            var_right = self.var_right
        )

    def __lt__(self,other):
        return self.lt(other, method = 'f')

    def __rlt__(self,other):
        return self.ge(other, method = 'f')

    def __le__(self,other):
        return self.le(other, method = 'f')

    def __rle__(self,other):
        return self.gt(other, method = 'f')

    def __gt__(self,other):
        return self.gt(other, method = 'f')

    def __rgt__(self,other):
        return self.le(other, method = 'f')

    def __ge__(self,other):
        return self.ge(other, method = 'f')

    def __rge__(self,other):
        return self.lt(other, method = 'f')

    def __and__(self, other):
        return self.logicaland(other, method = 'f')

    def __rand__(self,other):
        return self.logicaland(other, method = 'f')

    def __or__(self, other):
        return self.logicalor(other, method = 'f')

    def __ror__(self,other):
        return self.logicalor(other, method = 'f')

    def __add__(self, other):
        return self.add(other, method = 'f')

    def __radd__(self,other):
        return self.add(other, method = 'f')

    def __sub__(self,other):
        return self.sub(other, method = 'f')

    def __rsub__(self,other):
        self = - self
        return self.add(other, method = 'f')

    def __mul__(self,other):
        return self.mul(other, method = 'f')

    def __rmul__(self,other):
        return self.mul(other, method = 'f')

    def __truediv__(self, other):

        return self.div(other, method = 'f')

    def __rtruediv__(self,other):

        try:
            return other * self.recip()
        except:
            return NotImplemented

    ### Local functions ###
    def _computemoments(self):    # should we compute mean if it is a Cauchy, var if it's a t distribution?
        self.mean_left = np.max([self.mean_left, np.mean(self.left)])
        self.mean_right = np.min([self.mean_right, np.mean(self.right)])

        if not (np.any(np.array(self.left) <= -np.inf) or np.any(np.inf <= np.array(self.right))):
            V, JJ = 0, 0
            j = np.array(range(self.steps))

            for J in np.array(range(self.steps)) - 1:
                ud = [*self.left[j < J], *self.right[J <= j]]
                v = sideVariance(ud)

                if V < v:
                    JJ = J
                    V = v

            self.var_right = V

    def _checkmoments(self):

        a = Interval(self.mean_left, self.mean_right) #mean(x)
        b = dwMean(self)

        self.mean_left = np.max([left(a), left(b)])
        self.mean_right = np.min([right(a), right(b)])

        if self.mean_right < self.mean_left:
            # use the observed mean
            self.mean_left = left(b)
            self.mean_right = right(b)

        a = Interval(self.var_left, self.var_right) #var(x)
        b = dwVariance(self)

        self.var_left = np.max([left(a), left(b)])
        self.var_right = np.min([right(a),right(b)])

        if self.var_right < self.var_left:
            # use the observed variance
            self.var_left = left(b)
            self.var_right = right(b)

    def add(self, other: Union["Pbox",Interval,float,int], method  = 'f') -> "Pbox":
        '''
        Adds to Pbox to other using the defined dependency method
        
        :param other: Pbox, Interval or numeric type
        :param method: 

        :return: Pbox
        :rtype: Pbox
        
        
        '''
        if method not in ['f','p','o','i']:
            raise ArithmeticError("Calculation method unkown")

        if other.__class__.__name__ == 'Interval': 
            other = Pbox(other, steps = self.steps)

        if other.__class__.__name__ == 'Pbox':

            if self.steps != other.steps:
                raise ArithmeticError("Both Pboxes must have the same number of steps")

            if method == 'f':

                nleft  = np.empty(self.steps)
                nright = np.empty(self.steps)

                for i in range(0,self.steps):
                    j = np.array(range(i, self.steps))
                    k = np.array(range(self.steps - 1, i-1, -1))

                    nright[i] = np.min(self.right[j] + other.right[k])

                    jj = np.array(range(0, i + 1))
                    kk = np.array(range(i, -1 , -1))

                    nleft[i] = np.max(self.left[jj] + other.left[kk])

            elif method == 'p':

                nleft  = self.left + other.left
                nright = self.right + other.right

            elif method == 'o':

                nleft  = self.left + np.flip(other.left)
                nright = self.right + np.flip(other.right)

            elif method == 'i':

                nleft  = []
                nright = []
                for i in self.left:
                    for j in other.left:
                        nleft.append(i+j)
                for ii in self.right:
                    for jj in other.right:
                        nright.append(ii+jj)

            nleft.sort()
            nright.sort()

            return Pbox(
                left    = nleft,
                right   = nright,
                steps   = self.steps
            )

        else:
            try:
                # Try adding constant
                if self.shape in ['uniform','normal','cauchy','triangular','skew-normal']:
                    s = self.shape
                else:
                    s = ''

                return Pbox(
                    left       = self.left + other,
                    right      = self.right + other,
                    shape      = s,
                    mean_left  = self.mean_left + other,
                    mean_right = self.mean_right + other,
                    var_left   = self.var_left,
                    var_right  = self.var_right,
                    steps      = self.steps
                )

            except:
                return NotImplemented

    def sub(self, other, method = 'f'):

        if method == 'o':
            method = 'p'
        elif method == 'p':
            method = 'o'

        return self.add(-other, method)

    def mul(self, other, method = 'f'):

        if method not in ['f','p','o','i']:
            raise ArithmeticError("Calculation method unkown")

        if other.__class__.__name__ == 'Interval':
            other = Pbox(other, steps = self.steps)

        if other.__class__.__name__ == 'Pbox':

            if self.steps != other.steps:
                raise ArithmeticError("Both Pboxes must have the same number of steps")

            if method == 'f':

                nleft  = np.empty(self.steps)
                nright = np.empty(self.steps)

                for i in range(0,self.steps):
                    j = np.array(range(i, self.steps))
                    k = np.array(range(self.steps - 1, i-1, -1))

                    nright[i] = np.min(self.right[j] * other.right[k])

                    jj = np.array(range(0, i + 1))
                    kk = np.array(range(i, -1 , -1))

                    nleft[i] = np.max(self.left[jj] * other.left[kk])

            elif method == 'p':

                nleft  = self.left * other.left
                nright = self.right * other.right

            elif method == 'o':

                nleft  = self.left * np.flip(other.left)
                nright = self.right * np.flip(other.right)

            elif method == 'i':

                nleft  = []
                nright = []
                for i in self.left:
                    for j in other.left:
                        nleft.append(i*j)
                for ii in self.right:
                    for jj in other.right:
                        nright.append(ii*jj)

            nleft.sort()
            nright.sort()

            return Pbox(
                left    = nleft,
                right   = nright,
                steps   = self.steps
            )

        else:
            try:
                # Try adding constant
                if self.shape in ['uniform','normal','cauchy','triangular','skew-normal']:
                    s = self.shape
                else:
                    s = ''

                return Pbox(
                    left       = self.left * other,
                    right      = self.right * other,
                    shape      = s,
                    mean_left  = self.mean_left * other,
                    mean_right = self.mean_right * other,
                    var_left   = self.var_left,
                    var_right  = self.var_right,
                    steps      = self.steps
                )

            except:
                return NotImplemented

    def div(self, other, method = 'f'):

        if method == 'o':
            method = 'p'
        elif method == 'p':
            method = 'o'

        return self.mul(1/other, method)

    def recip(self):
        return Pbox(
            left  = 1 / np.flip(self.right),
            right = 1 / np.flip(self.left),
            steps = self.steps
        )


    def lt(self, other, method = 'f'):
        b = self.add(-other, method)
        return(b.get_probability(0))      # return (self.add(-other, method)).get_probability(0)

    def le(self, other, method = 'f'):
        b = self.add(-other, method)
        return(b.get_probability(0))      # how is the "or equal to" affecting the calculation?

    def gt(self, other, method = 'f'):
        self = - self
        b = self.add(other, method)
        return(b.get_probability(0))      # maybe 1-prob ?

    def ge(self, other, method = 'f'):
        self = - self
        b = self.add(other, method)
        return(b.get_probability(0))

    def min(self, other, method = 'f'):

        if method not in ['f','p','o','i']:
            raise ArithmeticError("Calculation method unkown")

        if other.__class__.__name__ == 'Interval':
            other = Pbox(other, steps = self.steps)

        if other.__class__.__name__ == 'Pbox':

            # if self.steps != other.steps:
            #     raise ArithmeticError("Both Pboxes must have the same number of steps")

            if method == 'f':

                nleft  = np.empty(self.steps)
                nright = np.empty(self.steps)

                for i in range(0,self.steps):
                    j = np.array(range(i, self.steps))
                    k = np.array(range(self.steps - 1, i-1, -1))

                    nright[i] = np.minimum(self.right[j],other.right[k])

                    jj = np.array(range(0, i + 1))
                    kk = np.array(range(i, -1 , -1))

                    nleft[i] = np.minimum(self.left[jj],other.left[kk])

            elif method == 'p':

                nleft  = np.minimum(self.left, other.left)
                nright = np.minimum(self.right, other.right)

            elif method == 'o':

                nleft  = np.minimum(self.left, np.flip(other.left))
                nright = np.minimum(self.right, np.flip(other.right))

            elif method == 'i':

                nleft  = []
                nright = []
                for i in self.left:
                    for j in other.left:
                        nleft.append(np.minimum(i,j))
                for ii in self.right:
                    for jj in other.right:
                        nright.append(np.minimum(ii,jj))

            nleft.sort()
            nright.sort()

            return Pbox(
                left    = nleft,
                right   = nright,
                steps   = self.steps
            )

        else:
            try:
                # Try constant
                nleft  = [i if i < other else other for i in self.left]
                nright = [i if i < other else other for i in self.right]

                return Pbox(
                    left       = nleft,
                    right      = nright,
                    steps      = self.steps
                )

            except:
                return NotImplemented

    def max(self, other, method = 'f'):

        if method not in ['f','p','o','i']:
            raise ArithmeticError("Calculation method unkown")

        if other.__class__.__name__ == 'Interval':
            other = Pbox(other, steps = self.steps)

        if other.__class__.__name__ == 'Pbox':

            # if self.steps != other.steps:
            #     raise ArithmeticError("Both Pboxes must have the same number of steps")

            if method == 'f':

                nleft  = np.empty(self.steps)
                nright = np.empty(self.steps)

                for i in range(0,self.steps):
                    j = np.array(range(i, self.steps))
                    k = np.array(range(self.steps - 1, i-1, -1))

                    nright[i] = np.maximum(self.right[j],other.right[k])

                    jj = np.array(range(0, i + 1))
                    kk = np.array(range(i, -1 , -1))

                    nleft[i] = np.maximum(self.left[jj],other.left[kk])

            elif method == 'p':

                nleft  = np.maximum(self.left, other.left)
                nright = np.maximum(self.right, other.right)

            elif method == 'o':

                nleft  = np.maximum(self.left, np.flip(other.left))
                nright = np.maximum(self.right, np.flip(other.right))

            elif method == 'i':

                nleft  = []
                nright = []
                for i in self.left:
                    for j in other.left:
                        nleft.append(np.maximum(i,j))
                for ii in self.right:
                    for jj in other.right:
                        nright.append(np.maximum(ii,jj))

            nleft.sort()
            nright.sort()

            return Pbox(
                left    = nleft,
                right   = nright,
                steps   = self.steps
            )

        else:
            try:
                # Try constant
                nleft  = [i if i > other else other for i in self.left]
                nright = [i if i > other else other for i in self.right]

                return Pbox(
                    left       = nleft,
                    right      = nright,
                    steps      = self.steps
                )

            except:
                return NotImplemented

    def logicaland(self, other, method = 'f'):   # conjunction
        if method=='i': 
            return(self.mul(other,method))  # independence a * b
        # elif method=='p': 
        #     return(self.min(other,method))  # perfect min(a, b)
        # elif method=='o': 
        #     return(max(self.add(other,method)-1, 0))  # opposite max(a + b – 1, 0)
        # elif method=='+': 
        #     return(self.min(other,method))  # positive env(a * b, min(a, b))
        # elif method=='-': 
        #     return(self.min(other,method))  # negative env(max(a + b – 1, 0), a * b)
        else:
            return(env(max(0, self.add(other,method) - 1),  self.min(other,method)))

    def logicalor(self, other, method = 'f'):    # disjunction
        if method=='i':
            return(1 - (1-self) * (1-other))  # independent 1 – (1 – a) * (1 – b)
        # elif method=='p':
        #    return(self.max(other,method))  # perfect max(a, b)
        # elif method=='o':
        #    return(min(self.add(other,method),1)) # opposite min(1, a + b)
        # elif method=='+':
        #    return(env(,min(self.add(other,method),1))  # positive env(max(a, b), 1 – (1 – a) * (1 – b))
        # elif method=='-':
        #    return()  # negative env(1 – (1 – a) * (1 – b), min(1, a + b))
        else:
            return(env(self.max(other,method), min(self.add(other,method),1)))

    def env(self, other):
        if other.__class__.__name__ == 'Interval':
            other = Pbox(other, steps = self.steps)
        if other.__class__.__name__ == 'Pbox':
            if self.steps != other.steps:
                raise ArithmeticError("Both Pboxes must have the same number of steps")

        nleft  = np.minimum(self.left, other.left)
        nright = np.maximum(self.right, other.right)

        return Pbox(
                left    = nleft,
                right   = nright,
                steps   = self.steps
            )

    def show(self,now = True, title = '', **kwargs):

        # now respects discretization
        L = self.left
        R = self.right
        steps = self.steps

        LL = np.concatenate((L, L, np.array([R[-1]])))
        RR = np.concatenate((np.array([L[0]]), R, R))
        ii = np.concatenate((np.arange(steps), np.arange(1, steps + 1), np.array([steps]))) / steps
        jj = np.concatenate((np.array([0]),np.arange(steps + 1), np.arange(1, steps))) / steps

        ii.sort();  jj.sort();  LL.sort();  RR.sort()

        plt.plot(LL,ii,'r-',**kwargs)               # can kwargs overwrite 'r-'?
        plt.plot(RR,jj,'k-',**kwargs)                # can kwargs overwrite 'k-'?
        if title != '' : plt.title(title,**kwargs)   # can kwargs tweak title?

        if now:
            plt.show()
        else:
            return plt

    plot = show

    def get_interval(self, *args) -> Interval:

        if len(args) == 1:

            if args[0] == 1:
                # asking for whole pbox bounds
                return Interval(min(self.left),max(self.right))

            p1 = (1-args[0])/2
            p2 = 1-p1

        elif len(args) == 2:

            p1 = args[0]
            p2 = args[1]

        else:
            raise Exception('Too many inputs')

        y  = np.append(np.insert(np.linspace(0,1,self.steps),0,0),1)

        y1 = 0
        while y[y1] < p1:
            y1 += 1

        y2 = len(y)-1
        while y[y2] > p2:
            y2 -= 1

        x1 = self.left[y1]
        x2 = self.right[y2]
        return Interval(x1,x2)

    def get_probability(self, val) -> Interval:
        p  = np.append(np.insert(np.linspace(0,1,self.steps),0,0),1)

        i = 0
        while i < self.steps and self.left[i] < val:
            i += 1


        ub = p[i]

        j = 0

        while j < self.steps and self.right[j] < val:
            j += 1


        lb = p[j]

        return Interval(lb,ub)

    # def exp(self):
    #     pass

    def mean(self) -> Interval:
        '''
        Returns the mean of the pbox
        '''
        return Interval(self.mean_left,self.mean_right)

    def support(self) -> Interval:
        return Interval(min(self.left),max(self.right))

    def get_x(self):
        '''returns the x values for plotting'''
        left = np.append(np.insert(self.left,0,min(self.left)),max(self.right))
        right = np.append(np.insert(self.right,0,min(self.left)),max(self.right))
        return left, right

    def get_y(self):
        '''returns the y values for plotting'''
        return np.append(np.insert(np.linspace(0,1,self.steps),0,0),1)

    def straddles(self,N, endpoints = True) -> bool:
        """
        Parameters
        ----------
        N : numeric
            Number to check
        endpoints : bool
            Whether to include the endpoints within the check

        Returns
        -------
        True
            If :math:`\\mathrm{left} \\leq N \\leq \mathrm{right}` (Assuming `endpoints=True`)
        False
            Otherwise
        """
        if endpoints:
            if min(self.left) <= N and max(self.right) >= N:
                return True
        else:
            if min(self.left) < N and max(self.right) > N:
                return True

        return False

    def straddles_zero(self,endpoints = True) -> bool:
        """
        Checks whether :math:`0` is within the p-box
        """
        return self.straddles(0,endpoints)

# Functions
def env_int(*args):
    left = min([min(i) if hasattr(i,"__iter__") else i for i in args])
    right = max([max(i) if hasattr(i,"__iter__") else i for i in args])
    return Interval(left, right)

def left(imp):
    if isinstance(imp, Interval) or isinstance(imp, Pbox):  # neither "pba.pbox.Pbox" nor "pbox.Pbox" works (with or without quotemarks), even though type(b) is <class 'pba.pbox.Pbox' and isinstance(pba.norm(5,1),pba.pbox.Pbox) is True
        return imp.left
    elif hasattr(imp,"__iter__"):
        return min(imp)
    else:
        return imp

def right(imp):
    if isinstance(imp, Interval) or isinstance(imp, Pbox):
        return imp.right
    elif hasattr(imp,"__iter__"):
        return max(imp)
    else:
        return imp

def left_list(implist, verbose=False):
    if not hasattr(implist,"__iter__"):
        return np.array(implist)

    return np.array([left(imp) for imp in implist])

def right_list(implist, verbose=False):
    if not hasattr(implist,"__iter__"):
        return np.array(implist)

    return np.array([right(imp) for imp in implist])

def qleftquantiles(pp, x, p): # if first p is not zero, the left tail will be -Inf
    return [max(left_list(x)[right_list(p) <= P]) for P in pp]

def qrightquantiles(pp, x, p):  # if last p is not one, the right tail will be Inf
    return [min(right_list(x)[P <= left_list(p)]) for P in pp]

def quantiles(x, p, steps=200):
    left = qleftquantiles(ii(steps=steps), x, p)
    right = qrightquantiles(jj(steps=steps), x, p)
    return Pbox(left=left, right=right)  # quantiles are in x and the associated cumulative probabilities are in p

def interp_step(u, steps=200):
    u = np.sort(u)

    seq = np.linspace(start=0, stop=len(u) - 0.00001, num=steps, endpoint=True)
    seq = np.array([trunc(seq_val) for seq_val in seq])
    return u[seq]

def interp_cubicspline(vals, steps=200):
    vals = np.sort(vals) # sort
    vals_steps = np.array(range(len(vals))) + 1
    vals_steps = vals_steps / len(vals_steps)

    steps = np.array(range(steps)) + 1
    steps = steps / len(steps)

    interped = interp.CubicSpline(vals_steps, vals)
    return interped(steps)

def interp_left(u, steps=200):
    p = np.array(range(len(u))) / (len(u) - 1)
    pp, x = ii(steps=steps), u
    return qleftquantiles(pp, x, p)

def interp_right(d, steps=200):
    p = np.array(range(len(d))) / (len(d) - 1)
    pp, x = jj(steps=steps), d
    return qrightquantiles(pp, x, p)

def interp_outer(x, left, steps=200):
    if (left) :
        return interp_left(x, steps=steps)
    else:
        return interp_right(x, steps=steps)

def interp_linear(V, steps=200):
    m = len(V) - 1

    if m == 0: return np.repeat(V, steps)
    if steps == 1: return np.array([min(V), max(V)])

    d = 1 / m
    n = round(d * steps * 200)

    if n == 0:
        c = V
    else:
        c = []
        for i in range(m):
            v = V[i]
            w = V[i + 1]
            c.extend(np.linspace(start=v, stop=w, num=n))

    u = [c[round((len(c) - 1) * (k + 0) / (steps - 1))] for k in range(steps)]

    return np.array(u)

def interpolate(u, interpolation='linear', left=True, steps=200):
    if interpolation == 'outer':
        return interp_outer(u, left, steps=steps)
    elif interpolation == 'spline':
        return interp_cubicspline(u, steps=steps)
    elif interpolation == 'step':
        return interp_step(u, steps=steps)
    else:
        return interp_linear(u, steps=steps)

def sideVariance(w, mu=None):
    if not isinstance(w, np.ndarray): w = np.array(w)
    if mu is None: mu = np.mean(w)
    return max(0, np.mean((w - mu) ** 2))

def dwMean(pbox):
    return Interval(np.mean(pbox.right), np.mean(pbox.left))

def dwVariance(pbox):
    if np.any(np.isinf(pbox.left)) or np.any(np.isinf(pbox.right)):
        return Interval(0, np.inf)

    if np.all(pbox.right[0] == pbox.right) and np.all(pbox.left[0] == pbox.left):
        return Interval(0, (pbox.right[0] - pbox.left[0]) ** (2 / 4))

    vr = sideVariance(pbox.left, np.mean(pbox.left))
    w = np.copy(pbox.left)
    n = len(pbox.left)

    for i in reversed(range(n)):
        w[i] = pbox.right[i]
        v = sideVariance(w, np.mean(w))

        if np.isnan(vr) or np.isnan(v):
            vr = np.inf
        elif vr < v:
            vr = v

    if pbox.left[n - 1] <= pbox.right[0]:
        vl = 0.0
    else:
        x = pbox.right
        vl = sideVariance(w, np.mean(w))

        for i in reversed(range(n)):
            w[i] = pbox.left[i]
            here = w[i]

            if 1 < i:
                for j in reversed(range(i-1)):
                    if w[i] < w[j]:
                        w[j] = here

            v = sideVariance(w, np.mean(w))

            if np.isnan(vl) or np.isnan(v):
                vl = 0
            elif v < vl:
                vl = v

    return Interval(vl, vr)


def mixture(
    *args: Union[Pbox,Interval,float,int],
    weights: List[Union[float,int]] = [], 
    steps: int = Pbox.STEPS
    ) -> Pbox:
    '''
    Returns Box interval
    Parameters
    ----------
    *args :
        Number of p-boxes or objects that can be tran
    weights:
        Right side of box
    
    Returns
    ----------
    Pbox
    '''
    #TODO: IMPROVE READBILITY

    x = []
    for pbox in args:
        if pbox.__class__.__name__ != 'Pbox':
            try:
                try:
                    pbox = box(pbox)
                except:
                    pbox = Pbox(pbox)
            except:
                raise TypeError("Unable to convert %s object (%s) to Pbox" %(type(pbox),pbox))
        x.append(pbox)

    k = len(x)
    if weights == []:
        weights = [1] * k


    # temporary hack
    # k = 2
    # x = [self, x]
    # w = [1,1]


    if k != len(weights):
        return('Need same number of weights as arguments for mixture')
    weights = [i/sum(weights) for i in weights]               # w = w / sum(w)
    u = []
    d = []
    n = []
    ml = []
    mh = []
    m = []
    vl = []
    vh = []
    v = []
    for i in range(k) :
        u = u + list(x[i].left)
        d = np.append(d,x[i].right)
        n = n + [weights[i] / x[i].steps] * x[i].steps    # w[i]*rep(1/x[i].steps,x[i].steps))

        # mu = mean(x[i])
        # ml = ml + [mu.left()]
        # mh = mh + [mu.right()]
        # m = m + [mu]               # don't need?
        # sigma2 = var(x[[i]])  ### !!!! shouldn't be the sample variance, but the population variance
        # vl = vl + [sigma2.left()]
        # vh = vh + [sigma2.right()]
        # v = v + [sigma2]

        ML = x[i].mean_left
        MR = x[i].mean_right
        VL = x[i].var_left
        VR = x[i].var_right
        m = m + [Interval(ML,MR)]
        v = v + [Interval(VL,VR)]
        ml = ml + [ML]
        mh = mh + [MR]
        vl = vl + [VL]
        vh = vh + [VR]

    n = [_/sum(n) for _ in n]                     # n = n / sum(n)
    su = sorted(u)
    su = [su[0]] + su
    pu = [0] + list(np.cumsum([n[i] for i in np.argsort(u)]))  #  pu = c(0,cumsum(n[order(u)]))
    sd = sorted(d); sd = sd + [sd[-1]]
    pd = list(np.cumsum([n[i] for i in np.argsort(d)])) + [1]  #  pd = c(cumsum(n[order(d)]),1)
    u = [];  d = []
    j = len(pu) - 1
    for p in reversed(np.arange(steps)/steps) :   # ii = np.arange(steps))/steps  #    ii = 0: (Pbox$steps-1) / Pbox$steps
        while p < pu[j] : j = j - 1                 # repeat {if (pu[j] <= p) break; j = j - 1}
        u = [su[j]] + u
    j = 0
    for p in (np.arange(steps)+1)/steps :         # jj = (np.arange(steps)+1)/steps #  jj =  1: Pbox$steps / Pbox$steps
        while pd[j] < p : j = j + 1                 # repeat {if (p <= pu[j]) break; j = j + 1}
        d = d + [sd[j]]
    mu = Interval(np.sum([W * M for M,W in zip(weights,ml)]), np.sum([W * M for M,W in zip(weights,mh)]))
    s2 = 0
    for i in range(k) : s2  = s2 + weights[i] * (v[i] + m[i]**2)
    s2 = s2 - mu**2

    return Pbox(np.array(u),np.array(d), mean_left=mu.left, mean_right=mu.right, var_left=s2.left, var_right=s2.right, steps = steps)

### None-Distribution Pboxes 

def box(
    a: Union[Interval,float,int] ,
    b = None, 
    steps = Pbox.STEPS
    ) -> Pbox:
    '''
    Returns Box interval
    
    
    Parameters
    ----------
        a :
            Left side of box
        b:
            Right side of box
    
    Returns
    ----------
        Pbox:
            p-box
        
    '''
    if b == None:
        b = a
    i = Interval(a,b)
    return Pbox(
        left = a,
        right = b,
        mean_left = i.left,
        mean_right= i.right,
        var_left = 0,
        var_right=((i.right-i.left)**2)/4,
        steps = steps
    )
    
def mmms(
    minimum: Union[Interval,float,int], 
    maximum: Union[Interval,float,int], 
    mean: Union[Interval,float,int], 
    stddev: Union[Interval,float,int], 
    steps: int = Pbox.STEPS
    ) -> Pbox:
    '''
    Generates a distribution-free p-box based upon the minimum, maximum, mean and standard deviation of the variable
 
    Parameters
    ----------
    minimum : 
        minimum value of the variable
    maximum : 
        maximum value of the variable
    mean : 
        mean value of the variable
    stddev :
        standard deviation of the variable 
    
    Returns
    ----------
    Pbox

    '''
    if minimum == maximum:
        return box(minimum, maximum)
    def _left(x): 
        if type(x) in [int,float]:
            return x
        if x.__class__.__name__ == "Interval":
            return x.left
        if x.__class__.__name__ == "Pbox":
            return min(x.left)
        
    def _right(x): 
        if type(x) in [int,float]:
            return x
        if x.__class__.__name__ == "Interval":
            return x.right
        if x.__class__.__name__ == "Pbox":
            return max(x.right)           
           
    def _imp(a,b) : 
        return Interval(max(_left(a),_left(b)),min(_right(a),_right(b)))
    def _env(a,b) : 
        return Interval(min(_left(a),_left(b)),max(_right(a),_right(b)))    
    
    def _constrain(a, b, msg) :
        if ((right(a) < left(b)) or (right(b) < left(a))) : 
            print("Math Problem: impossible constraint", msg)
        return _imp(a,b)
    
    zero = 0.0                          
    one = 1.0
    ran = maximum - minimum;
    m = _constrain(mean, Interval(minimum,maximum), "(mean)");
    s = _constrain(stddev, _env(Interval(0.0),(abs(ran*ran/4.0 - (maximum-mean-ran/2.0)**2))**0.5)," (dispersion)")
    ml = (m.left-minimum)/ran
    sl = s.left/ran
    mr = (m.right-minimum)/ran
    sr = s.right/ran
    z = box(minimum, maximum)
    n  = len(z.left)
    L = [0.0] * n
    R = [1.0] * n
    for i in range(n) :
        p = i / n
        if (p <= zero) : 
            x2 = zero
        else : x2 = ml - sr * (one / p - one)**0.5
        if (ml + p <= one) :
            x3 = zero
        else : 
            x5 = p*p + sl*sl - p
            if (x5 >= zero) :                  
                      x4 = one - p + x5**0.5
                      if (x4 < ml) : x4 = ml
            else : x4 = ml
            x3 = (p + sl*sl + x4*x4 - one) / (x4 + p - one)
        if ((p <= zero) or (p <= (one - ml))) : x6 = zero
        else : x6 = (ml - one) / p + one
        L[i] = max(max(max(x2,x3),x6),zero) * ran + minimum;
    
        p = (i+1)/n
        if (p >= one) : x2 = one
        else : x2 = mr + sr * (one/(one/p - one))**0.5
        if (mr + p >= one) : x3 = one
        else :
               x5 = p*p + sl*sl - p
               if (x5 >= zero) :                  
                      x4 = one - p - x5**0.5
                      if (x4 > mr) : x4 = mr                  
               else : x4 = mr 
               x3 = (p + sl*sl + x4*x4 - one) / (x4 + p - one) - one
             
        if (((one - mr) <= p) or (one <= p)) : x6 = one
        else : x6 = mr / (one - p)
        R[i] = min(min(min(x2,x3),x6),one) * ran + minimum
  
    v = s**2
    return Pbox(np.array(L),np.array(R),mean_left=left(m),mean_right=right(m),var_left=left(v),var_right=right(v),steps = steps)
