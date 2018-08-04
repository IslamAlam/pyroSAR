# -*- coding: utf-8 -*-
import ConfigParser
import os
import warnings

from os.path import expanduser

__LOCAL__ = ['sensor', 'projection', 'orbit', 'polarizations', 'acquisition_mode',
             'start', 'stop', 'product', 'spacing', 'samples', 'lines']


class Storage(dict):
    """
    Dict class with point access to store the lookups, pattern and URLs

    Attributes
    ----------
    STORAGE.LOOKUP : Storage
        All lookup table merged in a Storage class instance:
            * snap : SNAP process.
            * attributes : Attributes for different sensors.
    STORAGE.URL : dict (with point access)
        All URLs for DEMs, orbit files etc.:
            * dem : URL to download specific DEMs:
                * strm3
                * ace2
                * strm3_FTP
                * strm1HGT
                * ace
            * orbit : URL to download the orbit files:
                * ers1
                * ers2
                * s1_poe
                * s1_pres
                * doris
            * auxcal : URL to download the auxcal data:
                * s1
                * envisat
                * ers

    Note
    ----
    There may be additional attributes not listed above depending of the
    specific solver. Since this class is essentially a subclass of dict
    with attribute accessors, one can see which attributes are available
    using the `keys()` method.
    """

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __repr__(self):
        if self.keys():
            m = max(map(len, list(self.keys()))) + 1
            return '\n'.join([k.rjust(m) + ': ' + repr(v)
                              for k, v in sorted(self.items())])
        else:
            return self.__class__.__name__ + "()"

    def __dir__(self):
        return list(self.keys())


# ==============================================================================
# LOOKUP
# ==============================================================================
snap_suffix = {'Apply-Orbit-File': 'Orb',
               'Calibration': 'Cal',
               'Cross-Correlation': '',
               'LinearToFromdB': 'dB',
               'Remove-GRD-Border-Noise': 'bnr',
               'SAR-Simulation': 'Sim',
               'SARSim-Terrain-Correction': 'TC',
               'Subset': '',
               'Terrain-Correction': 'TC',
               'Terrain-Flattening': 'TF',
               'Read': '',
               'Write': ''}

snap = Storage(suffix=snap_suffix)

LOOKUP = Storage(snap=snap,

                 attributes={'sensor': 'TEXT',
                             'orbit': 'TEXT',
                             'acquisition_mode': 'TEXT',
                             'start': 'TEXT',
                             'stop': 'TEXT',
                             'product': 'TEXT',
                             'samples': 'INTEGER',
                             'lines': 'INTEGER',
                             'outname_base': 'TEXT PRIMARY KEY',
                             'scene': 'TEXT',
                             'hh': 'INTEGER',
                             'vv': 'INTEGER',
                             'hv': 'INTEGER',
                             'vh': 'INTEGER'})

# ==============================================================================
# URL
# ==============================================================================
dem = Storage(ace2='http://step.esa.int/auxdata/dem/ACE2/5M/',
              ace='http://step.esa.int/auxdata/dem/ACE30/',
              srtm3_FTP='xftp.jrc.it',
              srtm3='http://srtm.csi.cgiar.org/SRT-ZIP/SRTM_V41/SRTM_Data_GeoTiff/',
              srtm1Hgt='http://step.esa.int/auxdata/dem/SRTMGL1/', )

orbit = Storage(doris='http://step.esa.int/auxdata/orbits/Doris/vor',
                ers1='http://step.esa.int/auxdata/orbits/ers_precise_orb/ERS1',
                ers2='http://step.esa.int/auxdata/orbits/ers_precise_orb/ERS2',
                s1_poe='http://step.esa.int/auxdata/orbits/Sentinel-1/POEORB/',
                s1_res='http://step.esa.int/auxdata/orbits/Sentinel-1/RESORB/')

auxcal = Storage(s1='http://step.esa.int/auxdata/auxcal/S1/',
                 envisat='http://step.esa.int/auxdata/auxcal/ENVISAT/',
                 ers='http://step.esa.int/auxdata/auxcal/ERS/')

URL = Storage(dem=dem,
              orbit=orbit,
              auxcal=auxcal)

# ==============================================================================
# Merge
# ==============================================================================
STORAGE = Storage(URL=URL,
                  LOOKUP=LOOKUP)


class ConfigHandler(object):
    """
    ConfigHandler is a configuration handler for pyroSAR. It is intended to be called by a class's "__init__" and 
    set or get the configuration parameters throughout an entire package.
    The primary goal with ConfigHandler is to load a single, consistent configuration environment to be passed 
    amongst ALL objects within a package.
        
    ConfigHandler is a SINGLETON, meaning once instantiated, THE SAME OBJECT
    will be returned to every class object calling it.

    Parameters
    ----------
    path : str or None
        A path where the .pyrosar directory will be created. If None (default) it will be created in the user home
        directory.
    config_fname : str
        Name of the config file. Default is 'config.ini'.
    
    Methods
    -------
    make_dir : Create a .pyrosar directory in home directory.
    create_config : Create a config.ini file in .pyrosar directory.
    open : Open the config.ini file.
    add_section : Create a new section in the configuration.
    set : Set an option in the configuration.
    remove_option : Remove an option in the configuration.

    Notes
    -----
    The syntax is the same as in ConfigParser. Here, keys are called options.

    Examples
    --------
    >>> from pyroSAR import ConfigHandler
    >>> config = ConfigHandler()
    >>> config.add_section('SNAP')
    >>> config.set('SNAP', 'etc', 'C:\Users\user\dir_1')
    >>> config.set('SNAP', 'auxdata', 'C:\Users\user\dir_2')
    >>> print config
        'Class    : Config
         Path     : C:\Users\ibari\.pyrosar\ConfigHandler.ini
         Sections : 1

         Contents:
           Section: SNAP
	            x etc :: C:\Users\user\dir_1 :: <type 'str'>
	            x auxdata :: C:\Users\user\dir_2 :: <type 'str'>'

    >>> config.SNAP
        {'auxdata': 'C:\\Users\\user\\dir_2', 'etc': 'C:\\Users\\user\\dir_1'}
    >>> config.SNAP['etc']
        'C:\\Users\\user\\dir_1'
    >>> config.SNAP['auxdata']
        'C:\\Users\\user\\dir_2'
    """

    # ---- Define Global Variables ----

    __SNAP_KEYS = {
        "etc": "etc",
        "exe": "executable",
        "aux": "auxdata",
        "pro": "properties"
    }

    __SECTIONS = {
        "snap": "SNAP"
    }

    # Define __setter to control changeable keys (optional)
    # __setter = ["etc", "auxdata"]

    def __init__(self, path=None, config_fname='config.ini'):

        path = os.path.join(expanduser("~"), '.pyrosar') if path is None else os.path.join(path, '.pyrosar')

        self.__GLOBAL = {
            "path": path,
            "config_fname": config_fname,
            "config": os.path.join(os.path.join(path, config_fname)),
        }

        if os.path.isfile(self.__GLOBAL['config']):
            self.parser = ConfigParser.RawConfigParser()
            self.parser.read(self.__GLOBAL['config'])

        else:
            self.create_config()
            self.parser = ConfigParser.RawConfigParser()
            self.parser.read(self.__GLOBAL['config'])

    def make_dir(self):
        """
        Create a .pyrosar directory in home directory.

        Returns
        -------
        None
        """

        if not os.path.exists(self.__GLOBAL['path']):
            os.makedirs(self.__GLOBAL['path'])

        else:
            pass

    def create_config(self):
        """
        Create a config.ini file in .pyrosar directory.

        Returns
        -------
        None
        """

        self.make_dir()

        if not os.path.isfile(self.__GLOBAL['config']):
            with open(self.__GLOBAL['config'], 'w'):
                pass
        else:
            pass

    def __str__(self):

        string_literal = 'Class    : Config\n' \
                         'Path     : {0}\n' \
                         'Sections : {1}\n'.format(self.__GLOBAL['config'], len(self.parser.sections()))

        print (string_literal)
        print("Contents:")

        for section in self.parser.sections():
            print("\n Section: {0}".format(section))

            for options in self.parser.options(section):
                print("\t x {0} :: {1} :: {2}".format(options, self.parser.get(section, options), str(type(options))))

        return ''

    def __getattr__(self, section):
        try:
            return dict(self.parser.items(section))
        except ConfigParser.NoSectionError:
            raise AttributeError

    @property
    def sections(self):
        return self.parser.sections()

    def keys(self, section):
        """
        Get all keys (options) of a section.

        Parameters
        ----------
        section : str
            Section name.

        Returns
        -------
        list : options (keys) of a section.

        """
        return self.parser.options(section)

    def open(self):
        """
        Open the config.ini file. This method will open the config.ini file in a external standard app (text editor).

        Returns
        -------
        os.startfile

        """

        os.startfile(self.__GLOBAL['config'])

    def add_section(self, section='SNAP'):
        """
        Create a new section in the configuration.

        Parameters
        ----------
        section : str
            Section name

        Returns
        -------
        None

        """
        if self.parser.has_section(section):
            pass

        elif section not in ConfigHandler.__SECTIONS.values():
            raise AttributeError(
                "Only the following sections are allowed: {0}.".format(str(ConfigHandler.__SECTIONS.values())))

        else:
            self.parser.add_section(section)
            with open(self.__GLOBAL['config'], 'wb') as item:
                self.parser.write(item)

    def set(self, section, key, value, overwrite=False):
        """
        Set an option.

        Parameters
        ----------
        section : str
            Section name.
        key : str
            Key value.
        value :
            Value of the key.
        overwrite : bool
            If True and the defined key exists the value will be overwritten.

        Returns
        -------
        None
        """
        if not self.parser.has_section(section):
            raise AttributeError("Section {0} does not exist.".format(str(section)))

        elif key not in ConfigHandler.__SNAP_KEYS.values():
            raise AttributeError(
                "Only the following keys are allowed: {0}.".format(str(ConfigHandler.__SNAP_KEYS.values())))

        else:
            if key in self.parser.options(section):

                if overwrite:
                    self.parser.set(section, key, value)
                    with open(self.__GLOBAL['config'], 'wb') as item:
                        self.parser.write(item)

                else:
                    warnings.warn("Value already exists.")

            else:
                self.parser.set(section, key, value)
                with open(self.__GLOBAL['config'], 'wb') as item:
                    self.parser.write(item)

    def remove_option(self, section, key):
        """
        Remove an option and key.

        Parameters
        ----------
        section : str
            Section name.
        key : str
            Key value.

        Returns
        -------
        None
        """
        if not self.parser.has_section(section):
            raise AttributeError("Section {0} does not exist.".format(str(section)))

        elif key not in self.parser.options(section):
            raise AttributeError("Key {0} does not exist.".format(str(key)))

        else:
            self.parser.remove_option(section, key)

            # write changes back to the config file
            with open(self.__GLOBAL['config'], "wb") as config_file:
                self.parser.write(config_file)

    def get(self, section, key=None):
        """
        Get all options (keys) and values of a section.

        Parameters
        ----------
        section : str
            Section name.

        key : str or None
            If not None it returns the specific value of the desired key. Else (default) it will return all
            keys and values.

        Returns
        -------
        dict : keys and values of a section.

        """
        if not self.parser.has_section(section):
            raise AttributeError("Section {0} does not exist.".format(str(section)))
        else:
            if key is None:
                return dict(self.parser.items(section))

            else:
                items = dict(self.parser.items(section))
                return items[key]
