"""
Curtis functions collection for examples and problems.
TODO ***** need to put some vectors into python numpy syntax *****
TODO ***** eliminate global variables *****

    The following is an on-line matlab -> python converter
    https://www.codeconvert.ai/matlab-to-python-converter
Notes:
----------
    The following is an on-line matlab -> python converter
    https://www.codeconvert.ai/matlab-to-python-converter
    
References:
----------
    [1] BMWS; Bate, R. R., Mueller, D. D., White, J. E., & Saylor, W. W. (2020, 2nd ed.).
        Fundamentals of Astrodynamics. Dover Publications Inc.
    [2] Vallado, David A., (2013, 4th ed.).
        Fundamentals of Astrodynamics and Applications, Microcosm Press.
    [3] Curtis, H.W. (2009 2nd ed.).
        Orbital Mechanics for Engineering Students. Elsevier Ltd.
"""

import math

import numpy as np
import scipy.optimize  # used to solve kepler E

from astro_time import julian_date


def lambert(mu: float, R1, R2, tof: float, string: str):
    """
    Lambert solver, Curtis chapter 5.3, pp.263.

    Parameters:
    ----------
        mu     : float, description
        R1     : np.array, description
        R2     : np.array, description
        tof      : float, time of flight
        string : str, "pro" or "retro"; prograde or retrograde

    Returns:
    -------
        v1_vec, v2_vec : description
    """
    # Magnitudes of R1 and R2:
    r1 = np.linalg.norm(R1)
    r2 = np.linalg.norm(R2)

    c12 = np.cross(R1, R2)
    theta = np.arccos(np.dot(R1, R2) / (r1 * r2))

    # Determine whether the orbit is prograde or retrograde:
    if string != "retro" and string != "pro":
        string = "pro"
        print("\n ** Prograde trajectory assumed.\n")

    if string == "pro":
        if c12[2] <= 0:
            theta = 2 * np.pi - theta
    elif string == "retro":
        if c12[2] >= 0:
            theta = 2 * np.pi - theta

    # Equation 5.35:
    A = np.sin(theta) * np.sqrt(r1 * r2 / (1 - np.cos(theta)))

    # Determine approximately where F(z,tof) changes sign, and
    # use that value of z as the starting value for Equation 5.45:
    z = -100
    while F(z, tof) < 0:
        z = z + 0.1

    # Set an error tolerance and a limit on the number of iterations:
    tol = 1e-8
    nmax = 5000

    # Iterate on Equation 5.45 until z is determined to within the
    # error tolerance:
    ratio = 1
    n = 0
    while abs(ratio) > tol and n <= nmax:
        n = n + 1
        ratio = F(z, tof) / dFdz(z)
        z = z - ratio

    # Report if the maximum number of iterations is exceeded:
    if n >= nmax:
        print("\n\n **Number of iterations exceeds #g in " "lambert" " \n\n ")  # nmax

    # Equation 5.46a:
    f = 1 - y(z) / r1

    # Equation 5.46b:
    g = A * np.sqrt(y(z) / mu)

    # Equation 5.46d:
    gdot = 1 - y(z) / r2

    # Equation 5.28:
    V1 = 1 / g * (R2 - f * R1)

    # Equation 5.29:
    V2 = 1 / g * (gdot * R2 - R1)

    return V1, V2


# Equation 5.38:
def y(z):
    return r1 + r2 + A * (z * S(z) - 1) / np.sqrt(C(z))


# Equation 5.40:
def F(z, tof, mu):
    return (y(z) / C(z)) ** 1.5 * S(z) + A * np.sqrt(y(z)) - np.sqrt(mu) * tof


# Equation 5.43:
def dFdz(z):
    if z == 0:
        return np.sqrt(2) / 40 * y(0) ** 1.5 + A / 8 * (
            np.sqrt(y(0)) + A * np.sqrt(1 / (2 * y(0)))
        )
    else:
        return (y(z) / C(z)) ** 1.5 * (
            1 / (2 * z) * (C(z) - 3 * S(z) / (2 * C(z))) + 3 * S(z) ** 2 / (4 * C(z))
        ) + A / 8 * (3 * S(z) / C(z) * np.sqrt(y(z)) + A * np.sqrt(C(z) / y(z)))


"""
    Stumpff functions originated by Karl Stumpff, circa 1947
    Stumpff functions (C(z), S(z)) are part of a universal variable solution,
    which work regardless of eccentricity.
"""


def C(z):  # temporary, until I change calling routines
    return stumpff_C(z)


def S(z):  # temporary, until I change calling routines
    return stumpff_S(z)


def stumpff_S(z):
    if z > 0:
        x = np.sqrt(z)
        return (x - np.sin(x)) / (x) ** 3
    elif z < 0:
        y = np.sqrt(-z)
        return (np.sinh(y) - y) / (y) ** 3
    else:
        return 1 / 6


def stumpff_C(z):
    if z > 0:
        return (1 - np.cos(np.sqrt(z))) / z
    elif z < 0:
        return (np.cosh(np.sqrt(-z)) - 1) / (-z)
    else:
        return 1 / 2


def sphere_of_influence(sma: float, mass1: float, mass2: float):
    """
    Radius of the SOI (sphere of influence)

    Input Parameters:
    ----------
    sma : float, semi-major axis of mass1 orbiting mass2
    mass1 : float, generally the smaller of the 2 mass's (i.e. planet)
    mass2 : float, generally the larger of the 2 mass's (i.e. sun)

    Returns:
    -------
    r_SOI : float, radius of the SOI (sphere of influence)
    """
    r_SOI = sma * (mass1 / mass2) ** (2 / 5)
    return r_SOI


def E_zerosolver(E, args):
    Me = args[0]
    ecc = args[1]
    return E - ecc * np.sin(E) - Me


def solve_for_E(Me: float, ecc: float):
    """
    Solve Keplers equation.
    Note, Curtis, p.163, algorithm 3.1

    Parameters:
    ----------
        Me : float, mean angle/anomaly [rad]
        ecc : float, eccentricity

    Return:
    -------
        sols : float, E [rad]
    """
    # iterative solution process
    sols = scipy.optimize.fsolve(E_zerosolver, x0=Me, args=[Me, ecc])[0]
    return sols


def planet_elements_and_sv(planet_id, year, month, day, hour, minute, second, mu):
    """
    Curtis pp.470, section 8.10; p.471-472, algorithm 8.1.; pp.473, example 8.7

    Parameters:
    ----------
        planet_id : _type_
        year      : _type_
        month     : _type_
        day       : _type_
        hour      : _type_
        minute    : _type_
        second    : _type_
        mu        : _type_

    Return:
    -------
       names... : _type_
    """
    deg = math.pi / 180  # conversion [rad]->[deg]

    # Vallado equivilent of Curtis p.276, eqn 5.48:
    # parameters of julian_date(yr, mo, d, hr, minute, sec, leap_sec=False)
    jd = julian_date(yr=year, mo=month, d=day, hr=hour, minute=minute, sec=second)

    # commented code, below, obsolete; delete later
    # j0 = j1(year, month, day)
    # ut = (hour + minute / 60 + second / 3600) / 24
    # Curtis p.276 eqn 5.47
    # jd = j0 + ut

    # Planetary ephemeris pp.470, section 8.10; data, p.472, tbl 8.1.
    J2000_coe, rates = planetary_elements(planet_id)

    # Curtis p.471, eqn 8.93a
    t0 = (jd - 2451545) / 36525
    # Curtis p.471, eqn 8.93b
    elements = J2000_coe + rates * t0

    a = elements[0]
    e = elements[1]

    # Curtis p.89, eqn 2.71
    h = math.sqrt(mu * a * (1 - e**2))

    # Reduce the angular elements to range 0 - 360 [deg]
    incl = elements[2]
    RA = elements[3]  # [deg]
    w_hat = elements[4]  # [deg]
    L = elements[5]  # [deg]
    w = w_hat - RA  # [deg]
    M = L - w_hat  # [deg]

    # Curtis, p.163, algorithm 3.1 (M [rad]) in example 3.1
    # E = kepler_E(e, M * deg)  # [rad]
    E = solve_for_E(ecc=e, Me=M * deg)  # [rad]

    # Curtis, p.160, eqn 3.13
    TA = 2 * math.atan(math.sqrt((1 + e) / (1 - e)) * math.tan(E / 2))  # [rad]

    coe = [h, e, RA * deg, incl * deg, w * deg, TA * deg]

    # Curtis, p.231, algorithm 4.5; see p. 232, example 4.7
    r, v = sv_from_coe(coe, mu)

    return coe, r, v, jd


def get_transfer_angle(r1, r2, prograde=True):
    """
    Find transfer angle, given r1, r2, sense of rotation (long or short)
    2024-08-13 Copied from LambertHub angles.py

    Parameters
    ----------
    r1: np.array
        Initial position vector.
    r2: np.array
        Final position vector.
    prograde: bool
        If True, prograde motion, otherwise retrograde motion.

    Return
    -------
    dtheta: float, angle between vectors [rad]
    """
    import numpy as np

    # Verify position vectors are collinear. If so, verify the transfer
    # angle is 0 or pi.
    if np.all(np.cross(r1, r2) == 0):
        return 0 if np.all(np.sign(r1) == np.sign(r2)) else np.pi

    # Solve for a unitary vector normal to the vector plane. Its direction and
    # sense the one given by the cross product (right-hand) from r1 to r2.
    h = np.cross(r1, r2) / norm(np.cross(r1, r2))

    # Compute the projection of the normal vector onto the reference plane.
    alpha = dot(np.array([0, 0, 1]), h)

    # Get the minimum angle (0 <= dtheta <= pi) between r1 and r2.
    r1_norm, r2_norm = [norm(vec) for vec in [r1, r2]]
    theta0 = np.arccos(dot(r1, r2) / (r1_norm * r2_norm))

    # Fix theta as needed
    if prograde is True:
        dtheta = theta0 if alpha > 0 else 2 * np.pi - theta0
    else:
        dtheta = theta0 if alpha < 0 else 2 * np.pi - theta0

    return dtheta


def planetary_elements(planet_id: int):
    """
    Planetary Elements including Pluto.

    Input Parameters:
    ----------
        planet_id : int, 1->p; Mercury->Pluto

    Returns (for planet_id input):
    -------
        J2000_coe   : python list, J2000 clasic orbital elements (Kepler).
        J2000_rates : python list, coe rate change (x/century) from 2000-01-01.
    Notes:
    ----------
        Element list output:
            sma   = semi-major axis (aka a) [km]
            ecc   = eccentricity
            incl  = inclination angle; to the ecliptic [deg]
            RAAN  = right ascension of ascending node (aka capital W) [deg]
                    longitude node
            w_bar = longitude of periapsis [deg]
            L     = mean longitude [deg]

        References: see list at file beginning.
    """
    planets = [
        "Mercury",
        "Venus",
        "Earth",
        "Mars",
        "Jupiter",
        "Saturn",
        "Uranus",
        "Neptune",
        "Pluto",
    ]
    # Keplerian Elements and Rates, JPL, Table 1; EXCLUDING Pluto.
    #   https://ssd.jpl.nasa.gov/planets/approx_pos.html
    #   Mean ecliptic and equinox of J2000; time-interval 1800 AD - 2050 AD.
    #   JPL Table 1 order of the elements is different then the other list below.
    #   Also note, Table 1 list earth-moon barycenter, not just earth.
    #           sma   |    ecc      |     inc     | long.node   | long.peri   |  mean.long (L)
    #       au, au/cy | ecc, ecc/cy | deg, deg/cy | deg, deg/cy | deg, deg/cy | deg, deg/cy
    # J2000_elements = [
    #     [0.38709927, 0.20563593, 7.00497902, 48.33076593, 77.45779628, 252.25032350],
    #     [0.72333566, 0.00677672, 3.39467605, 76.67984255, 131.60246718, 181.97909950],
    #     [1.00000261, 0.01671123, -0.00001531, 0.0, 102.93768193, 100.46457166],
    #     [1.52371034, 0.09339410, 1.84969142, 49.55953891, -23.94362959, -4.55343205],
    #     [5.20288700, 0.04838624, 1.30439695, 100.47390909, 14.72847983, 34.39644501],
    #     [9.53667594, 0.05386179, 2.48599187, 113.66242448, 92.59887831, 49.95424423],
    #     [19.18916464, 0.04725744, 0.77263783, 74.01692503, 170.95427630, 313.23810451],
    #     [30.06992276, 0.00859048, 1.77004347, 131.78422574, 44.96476227, -55.12002969],
    #     [
    #         39.48211675,
    #         0.24882730,
    #         17.14001206,
    #         110.30393684,
    #         224.06891629,
    #         238.92903833,
    #     ],
    # ]
    # J2000_rates = [] I accidentally erased, 2024-August

    # Data below, copied Curtis tbl 8.1, Standish et.al. 1992
    # Elements, python list:
    # (semi-major axis)|             |             |(RAAN, Omega)| (omega_bar) |
    #            sma   |    ecc      |     incl    | long.node   | long.peri   |  mean.long (L)
    #        au, au/cy | ecc, ecc/cy | deg, deg/cy | deg, deg/cy | deg, deg/cy | deg, deg/cy
    J2000_elements = [
        [0.38709893, 0.20563069, 7.00487, 48.33167, 77.4545, 252.25084],
        [0.72333199, 0.00677323, 3.39471, 76.68069, 131.53298, 181.97973],
        [1.00000011, 0.01671022, 0.00005, -11.26064, 102.94719, 100.46435],
        [1.52366231, 0.09341233, 1.845061, 49.57854, 336.04084, 355.45332],
        [5.20336301, 0.04839266, 1.30530, 100.55615, 14.75385, 34.40438],
        [9.53707032, 0.05415060, 2.48446, 113.71504, 92.43194, 49.94432],
        [19.19126393, 0.04716771, 0.76986, 74.22988, 170.96424, 313.23218],
        [30.06896348, 0.00858587, 1.76917, 131.72169, 44.97135, 304.88003],
        [
            39.48168677,
            0.24880766,
            17.14175,
            110.30347,
            224.06676,
            238.92881,
        ],
    ]
    # century [cy] rates, python list:
    # Data below, copied Curtis tbl 8.1, Standish et.al. 1992
    # Units of rates table:
    # "au/cy", "1/cy", "arc-sec/cy", "arc-sec/cy", "arc-sec/cy", "arc-sec/cy"
    cent_rates = [
        [0.00000066, 0.00002527, -23.51, -446.30, 573.57, 538101628.29],
        [0.00000092, -0.00004938, -2.86, -996.89, -108.80, 210664136.06],
        [-0.0000005, -0.00003804, -46.94, -18228.25, 1198.28, 129597740.63],
        [-0.00007221, 0.00011902, -25.47, -1020.19, 1560.78, 68905103.78],
        [0.00060737, -0.00012880, -4.15, 1217.17, 839.93, 10925078.35],
        [-0.00301530, -0.00036762, 6.11, -1591.05, -1948.89, 4401052.95],
        [0.00152025, -0.00019150, -2.09, -1681.4, 1312.56, 1542547.79],
        [-0.00125196, 0.00002514, -3.64, -151.25, -844.43, 786449.21],
        [-0.00076912, 0.00006465, 11.07, -37.33, -132.25, 522747.90],
    ]
    # extract user requested planet coe data & rates;
    #   reminder, coe=classic orbital elements (Kepler)
    J2000_coe = J2000_elements[planet_id - 1]
    J2000_rates = cent_rates[planet_id - 1]
    # note, some constants from Vallado, NOT Curtis
    au = 149597870.7  # [km/au] Vallado p.1043, tbl.D-5

    # elements & rates conversions
    J2000_coe[0] = J2000_coe[0] * au  # [km] sma (semi-major axis, aka a) convert
    J2000_rates[0] = J2000_rates[0] * au
    # convert sec/cy to deg/cy; yes,
    #   I know there is a better way for this conversion; this gets the job done
    J2000_rates[2] = J2000_rates[2] / 3600.0
    J2000_rates[3] = J2000_rates[3] / 3600.0
    J2000_rates[4] = J2000_rates[4] / 3600.0
    J2000_rates[5] = J2000_rates[5] / 3600.0

    return J2000_coe, J2000_rates


def coe_from_date(planet_id: int, date_UT):
    """
    Compute planetary coe (clasic orbital elements), given earth date [ut].
    Keep in mind, outputs are in [km] & [rad]

    Input Parameters:
    ----------
        planet_id : int, Mercury->Pluto
        date_UT   : python date/time list;
            yr, mo, d, hr, minute, sec

    Returns:
    ----------
        t0_coe    : python list, coe at t0.
            See details and variable list in planetary_elements():
            sma [km], ecc [-], incl [rad], RAAN [rad], w_hat [rad], L [rad]
        jd_t0     : float, julian date of planet coe

    Notes:
    ----------
        Steps 1, 2, 3, of Curtis p.471-472, part of algorithm 8.1.
    """
    yr, mo, d, hr, minute, sec = date_UT
    jd_t0 = julian_date(
        yr=yr, mo=mo, d=d, hr=hr, minute=minute, sec=sec, leap_sec=False
    )
    # print(f"t0, given date/time, {yr}-{mo}-{d} {hr}:{minute}:{sec:.4g} UT")
    # print(f"Julian date, jd_t0= {jd_t0}")

    # Julian centuries at J2000
    yr, mo, d, hr, minute, sec = 2000, 1, 1, 12, 0, 0  # UT
    jd_j2000 = julian_date(
        yr=yr, mo=mo, d=d, hr=hr, minute=minute, sec=sec, leap_sec=False
    )

    # Curtis p.472, eqn 8.93a
    t0_j_cent = (jd_t0 - jd_j2000) / 36525  # julian centuries since t0

    # Curtis p.472, eqn 8.93a
    t0_j_cent = (jd_t0 - jd_j2000) / 36525  # julian centuries since t0
    # print(f"centuries since J2000, t0_j_cent= {t0_j_cent:.8g} [centuries]")

    # orbital elements tables kept in functionCollection.py
    # Curtis, p.473, step 3
    j2000_coe, j2000_rates = planetary_elements(planet_id=planet_id)

    # apply century rates to J2000 coe rates
    #   python list multiply
    t0_rates = [j2000_rates[x] * t0_j_cent for x in range(len(j2000_rates))]
    # python list add
    t0_coe = [j2000_coe[x] + t0_rates[x] for x in range(len(j2000_coe))]

    # [deg] values need to be 0-360; better method must exist for below
    # angular output values converted to [rad]
    t0_coe[2] = (t0_coe[2] % 360) * math.pi / 180  # note modulo arithmetic, %
    t0_coe[3] = (t0_coe[3] % 360) * math.pi / 180  # note modulo arithmetic, %
    t0_coe[4] = (t0_coe[4] % 360) * math.pi / 180  # note modulo arithmetic, %
    t0_coe[5] = (t0_coe[5] % 360) * math.pi / 180  # note modulo arithmetic, %

    # coe orbital elements list; see variable list in planetary_elements():
    # coe_elements_names= ["sma", "ecc", "incl", "RAAN", "w_hat", "L"]
    return t0_coe, jd_t0


def sv_from_coe(h, ecc, RA, incl, w, TA, mu):
    """
    Compute state vector (r,v) from classic orbital elements (coe).
    2024-August, many edits from MatLab translation!
    TODO consider using quaternions to avoid the gimbal lock of euler angles.

    Input Parameters:
        mu   - gravitational parameter [km^3 / s^2]
        coe  - orbital elements (h ecc RA incl w TA)
            h    = magnitude, angular momentum [km^2/s]
            ecc  = eccentricity [-]
            RA   = right ascension of the ascending node [rad];
                    aka capital W
            incl = inclination of the orbit [rad]
            w    = argument of perigee [rad]
            TA   = true angle/anomaly [rad]
        R3_w - Rotation matrix about the z-axis through the angle w
        R1_i - Rotation matrix about the x-axis through the angle i
        R3_RA- Rotation matrix about the z-axis through the angle RA
        Q_pX - Matrix of the transformation from perifocal to geocentric
                equatorial frame
        rp   - position vector in the perifocal frame [km]
        vp   - velocity vector in the perifocal frame [km/s]
        r    - position vector in the geocentric equatorial frame [km]
        v    - velocity vector in the geocentric equatorial frame [km/s]
    """
    # RA = RA * math.pi / 180  # [rad] right ascension of the ascending node
    # incl = incl * math.pi / 180  # [rad] inclination
    # w = w * math.pi / 180  # [rad] argument of periapsis
    # TA = TA * math.pi / 180  # [rad] true angle/anomaly

    # Curtis eqns 4.45 and 4.46 (rp and vp are column vectors):
    rp = (
        (h**2 / mu)
        * (1 / (1 + ecc * math.cos(TA)))
        * (math.cos(TA) * np.array([1, 0, 0]) + math.sin(TA) * np.array([0, 1, 0]))
    )
    rp = rp.reshape(-1, 1)  # convert to column vector
    vp = (mu / h) * (
        -math.sin(TA) * np.array([1, 0, 0]) + (ecc + math.cos(TA)) * np.array([0, 1, 0])
    )
    vp = vp.reshape(-1, 1)  # convert to column vector

    # Create rotation matrices/arrays
    # rotate z-axis thru angle RA, Curtis, eqn 4.34
    # R3_RA = [ math.cos(RA)  math.sin(RA)  0
    #         -math.sin(RA)  math.cos(RA)  0
    #             0        0     1]
    c_RA, s_RA = math.cos(RA), math.sin(RA)  #
    R3_RA = np.array([[c_RA, s_RA, 0], [-s_RA, c_RA, 0], [0, 0, 1]])

    # rotation about x-axis, inclination, Curtis, eqn 4.32
    # R1_i = [1       0          0
    #         0   cos(incl)  sin(incl)
    #         0  -sin(incl)  cos(incl)]
    c_in, s_in = np.cos(incl), np.sin(incl)
    R1_i = np.array([[1, 0, 0], [0, c_in, s_in], [0, -s_in, c_in]])
    # print(f"incl= {incl*180/np.pi}")
    # print(f"R1_i= {R1_i}")

    # rotation about z-axis, Curtis, eqn 4.34
    # R3_w = [ cos(w)  sin(w)  0
    #         -sin(w)  cos(w)  0
    #         0       0     1]
    c_w, s_w = np.cos(w), np.sin(w)
    R3_w = np.array([[c_w, s_w, 0], [-s_w, c_w, 0], [0, 0, 1]])
    # print(f"R3_w= {R3_w}")

    # Curtis, eqn 4.49
    Q_pX = R3_w @ R1_i @ R3_RA  # matrix multiply
    # print(f"Q_px= {Q_pX}")
    Q_Xp = np.transpose(Q_pX)

    # Curtis, eqn 4.51 (r and v are column vectors):
    r = Q_Xp @ rp
    v = Q_Xp @ vp

    # Convert r and v into row vectors:
    r = np.ravel(r)  # flatten the array
    v = np.ravel(v)  # flatten the array
    return r, v


def test_planetary_elements():
    """
    Curtis tbl 8.1 test
    """
    planet_id = 3  # earth
    J2000_coe, rates = planetary_elements(planet_id)

    np.set_printoptions(precision=4)  # numpy, set vector printing size
    # print(f"planetary elements, J2000_coe= {J2000_coe}")
    # print(f"elements rates, rates= {rates} [deg/cy]")
    # format print results
    coe_list = [f"{num:.6g}" for num in J2000_coe]  # just a print list
    print(f"planetary elements, J2000_coe= {coe_list} [km] & [deg]")
    rates_list = [f"{num:.6g}" for num in rates]  # just a print list
    print(f"elements rates, rates= {rates_list} [km] & [deg/cy]")

    # get date for planetary elements

    return None


def test_coe_from_date():
    """
    Code began with Curtis example 8.7.
    Note, coe_from_date() returns in units [km] & [rad]
    """
    planet_id = 3  # earth
    date_UT = [2003, 8, 27, 12, 0, 0]  # [UT]
    coe_t0, jd_t0 = coe_from_date(planet_id, date_UT)
    # coe_elements_names= ["sma", "ecc", "incl", "RAAN", "w_hat", "L"]
    sma, ecc, incl, RAAN, w_hat, L = coe_t0
    incl_deg = incl * 180 / math.pi
    RAAN_deg = RAAN * 180 / math.pi
    w_hat_deg = w_hat * 180 / math.pi
    L_deg = L * 180 / math.pi

    print(f"Julian date, jd_t0= {jd_t0}")
    print(
        f"sma= {sma:.8g} [km], "
        f"ecc= {ecc:.8g}, "
        f"\nincl_deg= {incl_deg:.8g} [deg], "
        f"RAAN_deg= {RAAN_deg:.6g} [deg], "
        f"w_hat_deg= {w_hat_deg:.6g} [deg], "
        f"L_deg= {L_deg:.6g} [deg]"
    )
    return None


def test_sv_from_coe():
    """
    Curtis example 4.7.
    h, ecc, RA, incl, w, TA
    """
    print(f"\nTest Curtis function, sv_from_coe():")
    mu_earth_km = 398600  # [km^3/s^2]
    h = 80000  # [km^2/s]
    ecc = 1.4
    # RA, incl, w, TA = [40, 30, 60, 30]  # [deg]
    RA, incl, w, TA = [
        40 * math.pi / 180,
        30 * math.pi / 180,
        60 * math.pi / 180,
        30 * math.pi / 180,
    ]  # [rad]
    r1_vec, v1_vec = sv_from_coe(
        h=h, ecc=ecc, RA=RA, incl=incl, w=w, TA=TA, mu=mu_earth_km
    )
    print(f"position, r1= {r1_vec}")
    print(f"velocity, v1= {v1_vec}")

    return None


def main():
    # just a placeholder to help with editor navigation:--)
    return


# use the following to test/examine functions
if __name__ == "__main__":

    # test_planetary_elements()  # verify tbl 8.1
    # test_coe_from_date()  # part of Curtis, algorithm 8.1
    test_sv_from_coe()  #
