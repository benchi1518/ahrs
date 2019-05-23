# -*- coding: utf-8 -*-
"""
Madgwick Algorithm

References
----------
.. [1] http://www.x-io.co.uk/open-source-imu-and-ahrs-algorithms/
.. [2] Nonlinear Complementary Filters on the Special Orthogonal Group; R.
   Mahony et al. 2010. (https://hal.archives-ouvertes.fr/hal-00488376/document)
.. [3] http://www.olliw.eu/2013/imu-data-fusing/
.. [4] https://motsai.com/omid-vs-madgwick-low-power-orientation-filters/

"""

import numpy as np
from ahrs.common.orientation import *

class Madgwick:
    """
    Class of Madgwick algorithm
    """
    __dict__ = {
        "beta": 0.1,
        "samplePeriod": 1.0/256.0
    }
    def __init__(self, *args, **kwargs):
        self.__dict__.update(kwargs)

    def updateIMU(self, g, a, q, **kwargs):
        """
        Madgwick's AHRS algorithm with an IMU architecture.

        Adapted to Python from original implementation by Sebastian Madgwick.

        Parameters
        ----------
        g : array
            Sample of tri-axial Gyroscope in radians.
        a : array
            Sample of tri-axial Accelerometer.
        q : array
            A-priori quaternion.
        beta : float
            Filter gain of a quaternion derivative.
        samplePeriod : float
            Sampling rate in seconds. Inverse of sampling frequency.

        Returns
        -------
        q : array
            Estimated quaternion.

        """
        # Read input parameters
        beta = kwargs['beta'] if 'beta' in kwargs.keys() else self.__dict__['beta']
        samplePeriod = kwargs['samplePeriod'] if 'samplePeriod' in kwargs.keys() else self.__dict__['samplePeriod']
        a_norm = np.linalg.norm(a)
        if a_norm == 0:     # handle NaN
            return q
        a /= a_norm
        # Assert values
        q /= np.linalg.norm(q)
        qw, qx, qy, qz = q[0], q[1], q[2], q[3]
        # Gradient decent algorithm corrective step
        F = np.array([2.0*(qx*qz - qw*qy)   - a[0],
                      2.0*(qw*qx + qy*qz)   - a[1],
                      2.0*(0.5-qx**2-qy**2) - a[2]])
        J = np.array([[-2.0*qy, 2.0*qz, -2.0*qw, 2.0*qx],
                      [ 2.0*qx, 2.0*qw,  2.0*qz, 2.0*qy],
                      [ 0.0,   -4.0*qx, -4.0*qy, 0.0   ]])
        step = J.T@F
        step /= np.linalg.norm(step)
        # Compute rate of change of quaternion
        qDot = 0.5 * q_prod(q, [0, g[0], g[1], g[2]]) - beta * step.T
        # Integrate to yield Quaternion
        q += qDot*samplePeriod
        q /= np.linalg.norm(q)
        return q

    def updateMARG(self, g, a, m, q, **kwargs):
        """
        Madgwick's AHRS algorithm with a MARG architecture.

        Adapted to Python from original implementation by Sebastian Madgwick.

        Parameters
        ----------
        g : array
            Sample of tri-axial Gyroscope in radians.
        a : array
            Sample of tri-axial Accelerometer.
        m : array
            Sample of tri-axial Magnetometer.
        q : array
            A-priori quaternion.
        beta : float
            Filter gain of a quaternion derivative.
        samplePeriod : float
            Sampling rate in seconds. Inverse of sampling frequency.

        Returns
        -------
        q : array
            Estimated quaternion.

        """
        # Read input parameters
        beta = kwargs['beta'] if 'beta' in kwargs.keys() else self.__dict__['beta']
        samplePeriod = kwargs['samplePeriod'] if 'samplePeriod' in kwargs.keys() else self.__dict__['samplePeriod']
        # Normalise accelerometer measurement
        a_norm = np.linalg.norm(a)
        if a_norm == 0:     # handle NaN
            return q
        a /= a_norm
        # Normalise magnetometer measurement
        m_norm = np.linalg.norm(m)
        if m_norm == 0:     # handle NaN
            return q
        m /= m_norm
        # Assert values
        q /= np.linalg.norm(q)
        qw, qx, qy, qz = q[0], q[1], q[2], q[3]
        # Reference direction of Earth's magnetic field
        h = q_prod(q, q_prod([0, m[0], m[1], m[2]], q_conj(q)))
        b = [0.0, np.linalg.norm([h[1], h[2]]), 0.0, h[3]]
        # Gradient decent algorithm corrective step
        F = np.array([2.0*(qx * qz - qw * qy) - a[0],
                    2.0*(qw * qx + qy * qz)   - a[1],
                    2.0*(0.5 - qx**2 - qy**2) - a[2],
                    2.0*b[1]*(0.5 - qy**2 - qz**2) + 2.0*b[3]*(qx*qz - qw*qy)       - m[0],
                    2.0*b[1]*(qx*qy - qw*qz)       + 2.0*b[3]*(qw*qx + qy*qz)       - m[1],
                    2.0*b[1]*(qw*qy + qx*qz)       + 2.0*b[3]*(0.5 - qx**2 - qy**2) - m[2]])
        J = np.array([[-2.0*qy,               2.0*qz,                  -2.0*qw,                    2.0*qx],
                    [ 2.0*qx,                 2.0*qw,                   2.0*qz,                    2.0*qy],
                    [ 0.0,                   -4.0*qx,                  -4.0*qy,                    0.0],
                    [-2.0*b[3]*qy,            2.0*b[3]*qz,             -4.0*b[1]*qy-2.0*b[3]*qw,  -4.0*b[1]*qz+2.0*b[3]*qx],
                    [-2.0*b[1]*qz+2*b[3]*qx,  2.0*b[1]*qy+2.0*b[3]*qw,  2.0*b[1]*qx+2.0*b[3]*qz,  -2.0*b[1]*qw+2.0*b[3]*qy],
                    [ 2.0*b[1]*qy,            2.0*b[1]*qz-4.0*b[3]*qx,  2.0*b[1]*qw-4.0*b[3]*qy,   2.0*b[1]*qx]])
        step = J.T@F
        step /= np.linalg.norm(step)    # normalise step magnitude
        # Compute rate of change of quaternion
        qDot = 0.5 * q_prod(q, [0, g[0], g[1], g[2]]) - beta * step.T
        # Integrate to yield quaternion
        q += qDot*samplePeriod
        q /= np.linalg.norm(q) # normalise quaternion
        return q
