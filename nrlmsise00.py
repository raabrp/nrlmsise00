ENABLE_SPACE_WEATHER = False

from ctypes import *
import datetime

c_nrlmsise = CDLL('libnrlmsise00.so')

###############################################################################
# Type and signature declarations

class C_Flags(Structure):
    '''
    Switches: to turn on and off particular variations use these switches.
    0 is off, 1 is on, and 2 is main effects off but cross terms on.

    Standard values are 1 for all switches.

    switches[i]:
     i - explanation
    -----------------
     0 - output in meters and kilograms instead of centimeters and grams
     1 - F10.7 effect on mean
     2 - time independent
     3 - symmetrical annual
     4 - symmetrical semiannual
     5 - asymmetrical annual
     6 - asymmetrical semiannual
     7 - diurnal
     8 - semidiurnal
     9 - daily ap [when this is set to -1 (!) the pointer
                  ap_a in struct nrlmsise_input must
                  point to a struct ap_array]
    10 - all UT/long effects
    11 - longitudinal
    12 - UT and mixed UT/long
    13 - mixed AP/UT/LONG
    14 - terdiurnal
    15 - departures from diffusive equilibrium
    16 - all TINF var
    17 - all TLB var
    18 - all TN1 var
    19 - all S var
    20 - all TN2 var
    21 - all NLB var
    22 - all TN3 var
    23 - turbo scale height var
    '''
    _fields_ = [
        ("switches", c_int * 24),
        ("sw", c_double * 24),
        ("swc", c_double * 24)
    ]

class C_AParray(Structure):
    _fields_ = [
        ("a", c_double * 7)
    ]

class C_Input(Structure):
    _fields_ = [
        ("year", c_int),
        ("doy", c_int),
        ("sec", c_double),
        ("alt", c_double),
        ("g_lat", c_double),
        ("g_long", c_double),
        ("lst", c_double),
        ("f107A", c_double),
        ("f107", c_double),
        ("ap", c_double),
        ("ap_array", POINTER(C_AParray)) # see above
    ]

class C_Output(Structure):
    _fields_ = [
        ("d", c_double * 9), # densities
        ("t", c_double * 2)  # temperatures
    ]

# neutral atmospheric model - anomalous oxygen
c_nrlmsise.gtd7.restype = None
c_nrlmsise.gtd7.argtypes = (C_Input, C_Flags, POINTER(C_Output))

# neutral atmospheric model + anomalous oxygen
c_nrlmsise.gtd7d.restype = None
c_nrlmsise.gtd7d.argtypes = (C_Input, C_Flags, POINTER(C_Output))

###############################################################################
# Wrapping Function
#

def nrlmsise00(doy, sec, alt, g_lat, g_long, lst, f107A=150, f107=150, ap=4,
               ap_array=None, off_switches=None, cross_switches=None,
               anomalous_oxygen=False):
    '''

    ARGUMENTS:

        doy: day of year 
        sec: seconds in day (UT)
        alt: altitude (ambiguous?) [km]
        g_lat: geodetic latitude [deg]
        g_long: geodetic longitude [deg]
        lst: local apparent solar time (hours), see note below
        f107A: 81 day average of F10.7 flux (centered on doy) [stu]
        f107: daily F10.7 flux for previous day [stu]
        ap: magnetic index (daily)
        ap_array: array containing the following magnetic values:
            0: daily AP
            1: 3 hr AP index for current time
            2: 3 hr AP index for 3 hrs before current time
            3: 3 hr AP index for 6 hrs before current time
            4: 3 hr AP index for 9 hrs before current time
            5: Average of eight 3 hr AP indicies from 12 to 33 hrs
               prior to current time
            6: Average of eight 3 hr AP indicies from 36 to 57 hrs
               prior to current time
        off_switches: optional overide of switches (see docstring for
                      C_Flags) as a list of indecies for switches to set to 0
        cross_switches: optional overide of switches (see docstring for
                        C_Flags) as a list of indecies for switches to set to 2
        anomalous_oxygen: whether to include anomalous oxygen in mass density

    UT, Local Time, and Longitude are used independently in the
    model and are not of equal importance for every situation.
    For the most physically realistic calculation these three
    variables should be consistent (lst=sec/3600 + g_long/15).
    The Equation of Time departures from the above formula
    for apparent local time can be included if available but
    are of minor importance.

    f107 and f107A values used to generate the model correspond
    to the 10.7 cm radio flux at the actual distance of the Earth
    from the Sun rather than the radio flux at 1 AU. The following
    site provides both classes of values:

    (link down) ftp://ftp.ngdc.noaa.gov/stp/solar_data/solar_radio/flux/
    (using https://spawx.nwra.com/spawx/env_latest.html instead)

    f107, f107A, and ap effects are neither large nor well
    established below 80 km.

    RETURNS:
        [d, t]

    where
        d[0] - HE number density(m-3)
        d[1] - O number density(m-3)
        d[2] - N2 number density(m-3)
        d[3] - O2 number density(m-3)
        d[4] - AR number density(m-3)
        d[5] - Total mass density(kg m-3) [includes d[8] in td7d]
        d[6] - H Number density(m-3)
        d[7] - N Number density(m-3)
        d[8] - Anomalous oxygen number density(m-3)
        t[0] - Exospheric temperature(K)
        t[1] - Temperature at alt(K)

    O, H, and N are set to zero below 72.5 km

    t[0], Exospheric temperature, is set to global average for
    altitudes below 120 km. The 120 km gradient is left at global
    average value for altitudes below 72 km.

    If `anomalous_oxygen` is False, d[5] is the sum of the mass densities of
    the species labeled by indices 0-4 and 6-7 in output variable d.
    This includes He, O, N2, O2, Ar, H, and N but does NOT include
    anomalous oxygen (species index 8).

    If `anomalous_oxygen` is True, d[5] is the "effective total mass density
    for drag" and is the sum of the mass densities of all species
    in this model, INCLUDING anomalous oxygen.

    '''

    switches = [1] * 24

    if (off_switches == None):
        off_switches = []

    if (cross_switches == None):
        cross_switches = []

    for indx in off_switches:
        switches[indx] = 0
    for ind in cross_switches:
        switches[indx] = 2

    if (ap_array == None):
        ap_array = [0] * 7
    else:
        switches[9] = -1

    #### do C subroutine

    c_ap_array = C_AParray((c_double * 7)(*ap_array))

    c_input = C_Input(
        0, doy, sec, alt, g_lat, g_long, lst, f107A, f107, ap,
        pointer(c_ap_array)
    )

    c_flags = C_Flags()
    c_flags.switches = (c_int * 24)(*switches)

    c_out = C_Output()

    if anomalous_oxygen:
        c_nrlmsise.gtd7d(c_input, c_flags, c_out)
    else:
        c_nrlmsise.gtd7(c_input, c_flags, c_out)

    #### end C subroutine

    return (list(c_out.d), list(c_out.t))

###############################################################################
# SPACE WEATHER

if ENABLE_SPACE_WEATHER:
    import urllib.request
    from bs4 import BeautifulSoup as Soup

    def get_latest_valid(x):
        while (x[-1] == -999.0):
            x.pop()
        return x[-1]

    def get_latest_space_weather():
        with urllib.request.urlopen(
                'https://spawx.nwra.com/spawx/env_latest.html'
        ) as resp:
            src = Soup(resp.read()).find('pre').text

            lines = src.split('\n')

            fgps = list(map(float, lines[16].split()[1:]))
            fbar = list(map(float, lines[17].split()[1:]))
            swpc_ap = list(map(float, lines[20].split()[2:]))
            ap24 = list(map(float, lines[31].split()[3:]))

            f107 = get_latest_valid(fgps)
            f107a = get_latest_valid(fbar)
            ap = get_latest_valid(swpc_ap)
            ap_array = [
                swpc_ap[-1],
                ap24[-1], ap24[-2], ap24[-3], ap24[-4],
                swpc_ap[-2], swpc_ap[-3]
            ]

            return f107, f107a, ap, ap_array

###############################################################################

class Atmosphere:
    def __init__(self, now=None, get_space_weather=False, **kwargs):
        '''

        Arguments:
            now: datetime.datetime object (leave blank to use current time)

            get_space_weather: whether to query NWRA Space Weather Service
                               for current space weather.

            kwargs may be passed to nrlmsise00:
               f107A=150,
               f107=150,
               ap=4,
               ap_array=None,
               off_switches=None,
               cross_switches=None,
               anomalous_oxygen=False

        Below 80 km, effects of space weather are "neither large nor well
        established" and may be ignored (default values are used instead)

        '''

        if (now == None):
            now = datetime.datetime.utcnow()

        self.doy = now.timetuple().tm_yday
        self.sec = (now.hour * 60 + now.minute) * 60 + now.second

        if 'lst' in kwargs:
            del kwargs['lst']

        if (get_space_weather and ENABLE_SPACE_WEATHER):
            a, b, c, d = get_latest_space_weather()
            kwargs['f107'] = a
            kwargs['f107A'] = b
            kwargs['ap'] = c
            kwargs['ap_array'] = d

        self.kwargs = kwargs

    def _full_output(self, g_lat, g_long, alt, lst=None):
        '''

        Arguments:

        lat: geodetic latitude [deg]
        lon: geodetic longitude [deg]
        alt: altitude (ambiguous?) [km]
        lst: for test purposes only [hours]

        Returns: [d, t]

        where

        d[0] - HE number density(m-3)
        d[1] - O number density(m-3)
        d[2] - N2 number density(m-3)
        d[3] - O2 number density(m-3)
        d[4] - AR number density(m-3)
        d[5] - Total mass density(kg m-3) # with or without anomalous oxygen
        d[6] - H Number density(m-3)
        d[7] - N Number density(m-3)
        d[8] - Anomalous oxygen number density(m-3)
        t[0] - Exospheric temperature(K)
        t[1] - Temperature at alt(K)
        '''

        if (lst is None):
            lst = self.sec / 3600 + g_long/15

        return nrlmsise00(
            self.doy, self.sec, alt, g_lat, g_long, lst, **self.kwargs
        )

        return d, t

    def local_conditions(self, g_lat, g_long, alt):
        '''

        Arguments:

        lat: geodetic latitude [deg]
        lon: geodetic longitude [deg]
        alt: altitude (ambiguous?) [km]

        Returns:

        Total mass density(kg m-3), # with or without anomalous oxygen
        Temperature at alt(K)
        '''

        d, t = local_conditions(self, g_lat, g_long, alt)

        rho = d[5] * 1000 # total_mass_density [kg m^-3]
        temp = t[1] # temperature [Kelvin]

        return(rho, temp)

# Test output
if __name__ == "__main__":

    def flatten(nested_list):
        return [y for x in nested_list for y in x]

    def as_relative_error(x, y):
        out = []
        for i in range(len(x)):
            if not x[i] == 0:
                out.append((y[i] - x[i]) / x[i])
            else:
                out.append(y[i])

        return out

    def to_datetime(doy, sec):
        x = datetime.datetime(2018, 1, 1, 0, 0, 0)
        y = datetime.timedelta(days=(doy)-1, seconds=sec)
        return x + y

    def run_test(
            doy=172, sec=29000, alt=400, g_lat=60, g_long=-70, lst=16,
            f107A=150, f107=150, ap=4, use_ap_array=False
    ):

        kwargs = {
            'lst': lst,
        }
        if use_ap_array:
            kwargs['ap_array'] = [100] * 7
        if f107A != 150:
            kwargs['f107A'] = f107A
        if f107 != 150:
            kwargs['f107'] = f107
        if ap != 4:
            kwargs['ap'] = ap

        atmo = Atmosphere(to_datetime(doy, sec), off_switches=[0], **kwargs)
        return flatten(atmo._full_output(g_lat, g_long, alt, lst))

        
    # read nominal values
    with open('ref_output.txt') as f:
        ref_lines = f.read().split('\n')

    nominal = []
    for i in range(17):
        nominal.append(list(map(float, ref_lines[i * 2].split())))

    def evaluate_test(index, **kwargs):

        # prtint percentage error
        # print(as_relative_error(nominal[index], run_test(**kwargs)))

        # print returned values
        print(run_test(**kwargs))

    evaluate_test(0)
    evaluate_test(1, doy=81)
    evaluate_test(2, sec=75000, alt=1000)
    evaluate_test(3, alt=100)
    evaluate_test(4, g_lat=0)
    evaluate_test(5, g_long=0)
    evaluate_test(6, lst=4)
    evaluate_test(7, f107A=70)
    evaluate_test(8, f107=180)
    evaluate_test(9, ap=40)
    evaluate_test(10, alt=0)
    evaluate_test(11, alt=10)
    evaluate_test(12, alt=30)
    evaluate_test(13, alt=50)
    evaluate_test(14, alt=70)
    evaluate_test(15, use_ap_array=True)
    # evaluate_test(16, use_ap_array=True)
    print("Test 16 not run. Referencing nrlmsise-00_test.c, I don't see how" +
           " tests 15 and 16 differ in input...")
