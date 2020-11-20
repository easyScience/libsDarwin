# **************************************************************************
#
# CrysFML API Reflection Utilities
#
# @file      Src/API_Reflections_Utilities.py
# @brief     Reflections utilities based on CrysFML
#
# @homepage  https://code.ill.fr/scientific-software/crysfml
# @license   GNU LGPL (see LICENSE)
# @copyright Institut Laue Langevin 2020-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import CFML_api.crysfml_api
import CFML_api.FortranBindedClass

class ReflectionList(CFML_api.FortranBindedClass):
    def __init__(self, cell, spg, lfriedel, value1, value2):
        CFML_api.FortranBindedClass.__init__(self)
        self._set_fortran_address(
            CFML_api.crysfml_api.reflections_utilities_hkl_uni_reflist(
                cell.get_fortran_address(), spg.get_fortran_address(),
                lfriedel, value1, value2)["address"])
        
    def __del__(self):
        CFML_api.crysfml_api.reflections_utilities_del_reflection_list(self.get_fortran_address())
    
    def compute_structure_factors(self, space_group, atom_list):
        CFML_api.crysfml_api.structure_factors_structure_factors(
            atom_list.get_fortran_address(), space_group.get_fortran_address(),
            self.get_fortran_address())