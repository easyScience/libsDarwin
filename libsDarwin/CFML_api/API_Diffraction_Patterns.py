# **************************************************************************
#
# CrysFML API Diffraction Patters
#
# @file      Src/API_Diffraction_Patterns.py
# @brief     Diffraction Patterns utilities based on CrysFML
#
# @homepage  https://code.ill.fr/scientific-software/crysfml
# @license   GNU LGPL (see LICENSE)
# @copyright Institut Laue Langevin 2020-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import CFML_api.crysfml_api
import CFML_api.FortranBindedClass

class DiffractionPattern(CFML_api.FortranBindedClass):
    def __init__(self, simulation_conditions, reflection_list, scale_f):
        self._set_fortran_address(CFML_api.crysfml_api.diffraction_patterns_compute_powder_pattern(
            simulation_conditions.to_dict(), reflection_list.get_fortran_address(), scale_f)["address"])
        
    def get_x(self):
        return CFML_api.crysfml_api.diffraction_patterns_get_x(self.get_fortran_address())["x"]
        
    def get_y(self):
        return CFML_api.crysfml_api.diffraction_patterns_get_y(self.get_fortran_address())["y"]
        
    x = property(get_x)
    y = property(get_y)


class PseudoVoigt():
    def __init__(self):
        self.fwhm = None
        self.eta  = None

        
    # Vp(x,f) = eta * L(x,f) + (1-eta)*G(x,f)
    def pseudovoigt_param(self, fwhm_G, fwhm_L):
    
        o1 = 2.69269
        o2 = 2.42843
        o3 = 4.47163
        o4 = 0.07842

        e1 = 1.36603
        e2 = 0.47719
        e3 = 0.11116

        # f=[f_{G}^{5}+2.69269f_{G}^{4}f_{L}+2.42843f_{G}^{3}f_{L}^{2}
        #       + 4.47163f_{G}^{2}f_{L}^{3}+0.07842f_{G}f_{L}^{4}+f_{L}^{5}]^{1/5

        self.fwhm = (fwhm_G**5.0 + o1*fwhm_G**4.0*fwhm_L + o2*fwhm_G**3.0*fwhm_L**2.0
                + o3*fwhm_G**2.0*fwhm_L**3.0+ o4*fwhm_G*fwhm_L**4.0+fwhm_L**5.0)**0.2

        #\eta =1.36603(f_{L}/f)-0.47719(f_{L}/f)^{2}+0.11116(f_{L}/f)^{3}
        ratio = fwhm_L/fwhm
        self.eta = max(1.0e-06, e1 * ratio - e2 * ratio**2 + e3 * ratio**3)

    def value(self,x):
        x2=x*x
        ag= 0.93943727869965133377234032841018/self.fwhm
        bg= 2.7725887222397812376689284858327/(self.fwhm**2)
        al= 0.63661977236758134307553505349006/self.fwhm
        bl= 4.0/self.fwhm**2
        gauss = ag* exp(-bg*x2)
        lor   = al/(1.0+bl*x2)
        pv_val = self.eta*lor + (1.0 - self.eta)*gauss

        return pv_val
