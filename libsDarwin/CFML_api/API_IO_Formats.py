# **************************************************************************
#
# CrysFML API IO Format
#
# @file      Src/API_IO_Formats.py
# @brief     IO Formats based on CrysFML
#
# @homepage  https://code.ill.fr/scientific-software/crysfml
# @license   GNU LGPL (see LICENSE)
# @copyright Institut Laue Langevin 2020-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import CFML_api.crysfml_api
import CFML_api.API_Crystal_Metrics
import CFML_api.API_Crystallographic_Symmetry
import CFML_api.API_Atom_TypeDef

class CIFFile():
    """ A class used to handle CIF Files

    ...
    Attributes
    ----------
    filename : string

    Methods
    -------
    get_as_string_array

    """
    def __init__(self, filename):
        """
        Parameters
        ----------
        filename : str
           Name of the CIF File
        """
        self.__load_cif_file(filename)
    
    @property
    def filename(self):
        """
        Name of the CIF File (str)
        """
        return self.__filename
    
    @property
    def cell(self):
        """
        Cell (CFML_api.Cell type)
        """
        return self.__cell
    
    @property
    def space_group(self):
        """
        Space Group (CFML_api.SpaceGroup type)
        """
        return self.__space_group
    
    @property
    def atom_list(self):
        """
        List of atoms (CFML_api.AtomList type)
        """
        return self.__atom_list
    
    @filename.setter
    def filename(self, filename):
        """
        Setter for the name of the cif file
        The setter reloads the cell, space group and atom list
        """
        self.__load_cif_file(filename)    

    def get_as_string_array(self):
        """
        Returns the CIF File as an array of string
        """
        ret = []
        with open(self.__filename, 'r') as file:
            for line in file.readlines():
                ret.append(line[:-1])
        return ret

    def __load_cif_file(self, filename):
        """
        Internal method
        Loads the CIF File
        """
        self.__filename = filename
        dict = CFML_api.crysfml_api.IO_formats_readn_set_xtal_structure(self.__filename)
        self.__cell = CFML_api.API_Crystal_Metrics.Cell.from_fortran_address(dict["Cell"])
        self.__space_group = CFML_api.API_Crystallographic_Symmetry.SpaceGroup.from_fortran_address(dict["SpG"])
        self.__atom_list = CFML_api.API_Atom_TypeDef.AtomList.from_fortran_address(dict["A"])