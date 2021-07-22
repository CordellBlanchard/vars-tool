import numpy as np
from math import factorial

'''
This code was originally published by the following individuals for use with
Scilab:
    Copyright (C) 2012 - 2013 - Michael Baudin
    Copyright (C) 2012 - Maria Christopoulou
    Copyright (C) 2010 - 2011 - INRIA - Michael Baudin
    Copyright (C) 2009 - Yann Collette
    Copyright (C) 2009 - CEA - Jean-Marc Martinez

    website: forge.scilab.org/index.php/p/scidoe/sourcetree/master/macros
    Much thanks goes to these individuals. It has been converted to Python by
    Abraham Lee.

The code below included in vars-tool is taken from the
pyDOE project: https://github.com/tisimst/pyDOE
'''


def lhs(sp=None, params=1, seed=None, criterion=None, iterations=None):
    """
    Generate a latin-hypercube design.

    Parameters
    ----------
    n : int
        the number of factors to generate samples for
    samples : int
        the number of samples to generate for each factor,
        defaults to ``n``
    criterion : str
        allowable values are ``center`` or ``c``, ``maximin`` or ``m``,
        ``centermaximin`` or ``cm``, and ``correlation`` or ``corr``.
        If no value given, the design is simply randomized.
    iterations : int
        The number of iterations in the `maximin` and
        correlations algorithms, default to 5

    Returns
    -------
    H : array_like 
        An n-by-samples design matrix that has
        been normalized so factor values
        are uniformly spaced between zero and one.

    Example
    -------
    A 3-factor design (defaults to 3 samples)::

        >>> lhs(3)
        array([[ 0.40069325,  0.08118402,  0.69763298],
               [ 0.19524568,  0.41383587,  0.29947106],
               [ 0.85341601,  0.75460699,  0.360024  ]])

    A 4-factor design with 6 samples::

        >>> lhs(4, samples=6)
        array([[ 0.27226812,  0.02811327,  0.62792445,  0.91988196],
               [ 0.76945538,  0.43501682,  0.01107457,  0.09583358],
               [ 0.45702981,  0.76073773,  0.90245401,  0.18773015],
               [ 0.99342115,  0.85814198,  0.16996665,  0.65069309],
               [ 0.63092013,  0.22148567,  0.33616859,  0.36332478],
               [ 0.05276917,  0.5819198 ,  0.67194243,  0.78703262]])

    A 2-factor design with 5 centered samples::

        >>> lhs(2, samples=5, criterion='center')
        array([[ 0.3,  0.5],
               [ 0.7,  0.9],
               [ 0.1,  0.3],
               [ 0.9,  0.1],
               [ 0.5,  0.7]])

    A 3-factor design with 4 samples where the minimum distance between
    all samples has been maximized::

        >>> lhs(3, samples=4, criterion='maximin')
        array([[ 0.02642564,  0.55576963,  0.50261649],
               [ 0.51606589,  0.88933259,  0.34040838],
               [ 0.98431735,  0.0380364 ,  0.01621717],
               [ 0.40414671,  0.33339132,  0.84845707]])

    A 4-factor design with 5 samples where the samples are as uncorrelated
    as possible (within 10 iterations)::

        >>> lhs(4, samples=5, criterion='correlate', iterations=10)
    """
    H = None

    # check the seed number
    if seed:
        np.random.seed(int(seed))

    if sp is None:
        sp = params

    if criterion is not None:
        assert criterion.lower() in ('center', 'c', 'maximin', 'm',
                                     'centermaximin', 'cm', 'correlation',
                                     'corr'), 'Invalid value for "criterion": {}'.format(criterion)
    else:
        H = _lhsclassic(params, sp)

    if criterion is None:
        criterion = 'center'

    if iterations is None:
        iterations = 5

    if H is None:
        if criterion.lower() in ('center', 'c'):
            H = _lhscentered(params, sp)
        elif criterion.lower() in ('maximin', 'm'):
            H = _lhsmaximin(params, sp, iterations, 'maximin')
        elif criterion.lower() in ('centermaximin', 'cm'):
            H = _lhsmaximin(params, sp, iterations, 'centermaximin')
        elif criterion.lower() in ('correlate', 'corr'):
            H = _lhscorrelate(params, sp, iterations)

    return H


def _lhsclassic(n, samples):
    # Generate the intervals
    cut = np.linspace(0, 1, samples + 1)

    # Fill points uniformly in each interval
    u = np.random.rand(samples, n)
    a = cut[:samples]
    b = cut[1:samples + 1]
    rdpoints = np.zeros_like(u)
    for j in range(n):
        rdpoints[:, j] = u[:, j] * (b - a) + a

    # Make the random pairings
    H = np.zeros_like(rdpoints)
    for j in range(n):
        order = np.random.permutation(range(samples))
        H[:, j] = rdpoints[order, j]

    return H


def _lhscentered(n, samples):
    # Generate the intervals
    cut = np.linspace(0, 1, samples + 1)

    # Fill points uniformly in each interval
    u = np.random.rand(samples, n)
    a = cut[:samples]
    b = cut[1:samples + 1]
    _center = (a + b) / 2

    # Make the random pairings
    H = np.zeros_like(u)
    for j in range(n):
        H[:, j] = np.random.permutation(_center)

    return H


def _lhsmaximin(n, samples, iterations, lhstype):
    maxdist = 0

    # Maximize the minimum distance between points
    for i in range(iterations):
        if lhstype == 'maximin':
            Hcandidate = _lhsclassic(n, samples)
        else:
            Hcandidate = _lhscentered(n, samples)

        d = _pdist(Hcandidate)
        if maxdist < np.min(d):
            maxdist = np.min(d)
            H = Hcandidate.copy()

    return H


def _lhscorrelate(n, samples, iterations):
    mincorr = np.inf

    # Minimize the components correlation coefficients
    for i in range(iterations):
        # Generate a random LHS
        Hcandidate = _lhsclassic(n, samples)
        R = np.corrcoef(Hcandidate)
        if np.max(np.abs(R[R != 1])) < mincorr:
            mincorr = np.max(np.abs(R - np.eye(R.shape[0])))
            print(
                'new candidate solution found with max,abs corrcoef = {}'.format(mincorr))
            H = Hcandidate.copy()

    return H


def _pdist(x):
    '''
    Description:
    ------------
    This function calculates the pair-wise point distances of a matrix.


    Arguments:
    ----------
    :param x: an m-by-n array of scalars, where there are m points in n dimensions.
    :type x: np.ndarray


    Returns:
    --------
    :param d: A 1-by-b array of scalars, where b = m*(m - 1)/2.
              This array contains all the pair-wise point distances,
              arranged in the order (1, 0), (2, 0), ..., (m-1, 0),
              (2, 1), ..., (m-1, 1), ..., (m-1, m-2).
    :rtype d: np.ndarray


    Example:
    --------
    >>> x = np.array([[0.1629447, 0.8616334],
    ...               [0.5811584, 0.3826752],
    ...               [0.2270954, 0.4442068],
    ...               [0.7670017, 0.7264718],
    ...               [0.8253975, 0.1937736]])
    >>> _pdist(x)
    array([ 0.6358488,  0.4223272,  0.6189940,  0.9406808,  0.3593699,
            0.3908118,  0.3087661,  0.6092392,  0.6486001,  0.5358894])


    Credit:
    -------
    PyDOE (tisimst@gmail.com)


    License:
    --------
    The *BSD License* (3-clause)
    '''

    x = np.atleast_2d(x)
    assert len(x.shape) == 2, 'Input array must be 2d-dimensional'

    m, n = x.shape
    if m < 2:
        return []

    d = []
    for i in range(m - 1):
        for j in range(i + 1, m):
            d.append((sum((x[j, :] - x[i, :])**2))**0.5)

    return np.array(d)
