# -*- coding: utf-8 -*-
#GSASIIpwdGUI - powder data display routines
########### SVN repository information ###################
# $Date: 2020-10-14 21:56:09 +0200 (Wed, 14 Oct 2020) $
# $Author: vondreele $
# $Revision: 4594 $
# $URL: https://subversion.xray.aps.anl.gov/pyGSAS/trunk/GSASIIpwdGUI.py $
# $Id: GSASIIpwdGUI.py 4594 2020-10-14 19:56:09Z vondreele $
########### SVN repository information ###################
'''
*GSASIIpwdGUI: Powder Pattern GUI routines*
-------------------------------------------

Used to define GUI controls for the routines that interact
with the powder histogram (PWDR) data tree items.

'''
from __future__ import division, print_function
import platform
import sys
import os.path
# Don't depend on graphics for scriptable
try:
    import wx
    import wx.grid as wg
except ImportError:
    pass
import numpy as np
import numpy.linalg as nl
import numpy.ma as ma
import math
import copy
import random as ran
if '2' in platform.python_version_tuple()[0]:
    import cPickle
else:
    import pickle as cPickle
import scipy.interpolate as si
import GSASIIpath
GSASIIpath.SetVersionNumber("$Revision: 4594 $")
import GSASIImath as G2mth
import GSASIIpwd as G2pwd
import GSASIIfiles as G2fil
import GSASIIobj as G2obj
import GSASIIlattice as G2lat
import GSASIIspc as G2spc
import GSASIIindex as G2indx
import GSASIIplot as G2plt
import GSASIIdataGUI as G2gd
import GSASIIphsGUI as G2phsG
import GSASIIctrlGUI as G2G
import GSASIIElemGUI as G2elemGUI
import GSASIIElem as G2elem
import GSASIIsasd as G2sasd
import G2shapes
VERY_LIGHT_GREY = wx.Colour(235,235,235)
WACV = wx.ALIGN_CENTER_VERTICAL
if '2' in platform.python_version_tuple()[0]:
    GkDelta = unichr(0x0394)
    Pwr10 = unichr(0x0b9)+unichr(0x2070)
    Pwr20 = unichr(0x0b2)+unichr(0x2070)
    Pwrm1 = unichr(0x207b)+unichr(0x0b9)
    Pwrm2 = unichr(0x207b)+unichr(0x0b2)
    Pwrm6 = unichr(0x207b)+unichr(0x2076)
    Pwrm4 = unichr(0x207b)+unichr(0x2074)
    Angstr = unichr(0x00c5)
else:
    GkDelta = chr(0x0394)
    Pwr10 = chr(0x0b9)+chr(0x2070)
    Pwr20 = chr(0x0b2)+chr(0x2070)
    Pwrm1 = chr(0x207b)+chr(0x0b9)
    Pwrm2 = chr(0x207b)+chr(0x0b2)
    Pwrm6 = chr(0x207b)+chr(0x2076)
    Pwrm4 = chr(0x207b)+chr(0x2074)
    Angstr = chr(0x00c5)   
# trig functions in degrees
sind = lambda x: math.sin(x*math.pi/180.)
tand = lambda x: math.tan(x*math.pi/180.)
cosd = lambda x: math.cos(x*math.pi/180.)
asind = lambda x: 180.*math.asin(x)/math.pi
    
################################################################################
###### class definitions
################################################################################

class SubCellsDialog(wx.Dialog):
    def __init__(self,parent,title,controls,SGData,items,phaseDict):
        wx.Dialog.__init__(self,parent,-1,title,
            pos=wx.DefaultPosition,style=wx.DEFAULT_DIALOG_STYLE)
        self.panel = None
        self.controls = controls
        self.SGData = SGData         #for parent phase
        self.items = items
        self.phaseDict = phaseDict
        
        self.Draw()
    
    def Draw(self):
        
        def RefreshGrid(event):
            r,c =  event.GetRow(),event.GetCol()
            br = self.items[r]
            phase = self.phaseDict[br]
            rLab = magDisplay.GetRowLabelValue(r)
            pname = '(%s) %s'%(rLab,phase['Name'])
            if c == 0:
                mSGData = phase['SGData']
                text,table = G2spc.SGPrint(mSGData,AddInv=True)
                if 'magAtms' in phase:
                    msg = 'Magnetic space group information'
                    text[0] = ' Magnetic Space Group: '+mSGData['MagSpGrp']
                    text[3] = ' The magnetic lattice point group is '+mSGData['MagPtGp']
                    OprNames,SpnFlp = G2spc.GenMagOps(mSGData)
                    G2G.SGMagSpinBox(self.panel,msg,text,table,mSGData['SGCen'],OprNames,
                        mSGData['SpnFlp'],False).Show()
                else:
                    msg = 'Space Group Information'
                    G2G.SGMessageBox(self.panel,msg,text,table).Show()
            elif c == 1:
                maxequiv = phase['maxequiv']
                mSGData = phase['SGData']
                Uvec = phase['Uvec']
                Trans = phase['Trans']
                ifMag = False
                if 'magAtms' in phase:
                    ifMag = True
                    allmom = phase.get('allmom',False)
                    magAtms = phase.get('magAtms','')
                    mAtoms = TestMagAtoms(phase,magAtms,self.SGData,Uvec,Trans,allmom,maxequiv)
                else:
                    mAtoms = TestAtoms(phase,self.controls[15],self.SGData,Uvec,Trans,maxequiv)
                Atms = []
                AtCods = []
                atMxyz = []
                for ia,atom in enumerate(mAtoms):
                    atom[0] += '_%d'%ia
                    SytSym,Mul,Nop,dupDir = G2spc.SytSym(atom[2:5],mSGData)
                    Atms.append(atom[:2]+['',]+atom[2:5])
                    AtCods.append('1')
                    if 'magAtms' in phase:
                        MagSytSym = G2spc.MagSytSym(SytSym,dupDir,mSGData)
                        CSI = G2spc.GetCSpqinel(mSGData['SpnFlp'],dupDir)
                        atMxyz.append([MagSytSym,CSI[0]])
                    else:
                        CSI = G2spc.GetCSxinel(SytSym)
                        atMxyz.append([SytSym,CSI[0]])
                G2phsG.UseMagAtomDialog(self.panel,pname,Atms,AtCods,atMxyz,ifMag=ifMag,ifOK=True).Show()
            elif c in [2,3]:
                if c == 2:
                    title = 'Conjugacy list for '+pname
                    items = phase['altList']
                    
                elif c == 3:
                    title = 'Super groups list list for '+pname
                    items = phase['supList']
                    if not items[0]:
                        wx.MessageBox(pname+' is a maximal subgroup',caption='Super group is parent',style=wx.ICON_INFORMATION)
                        return
                SubCellsDialog(self.panel,title,self.controls,self.SGData,items,self.phaseDict).Show()
        
        if self.panel: self.panel.Destroy()
        self.panel = wx.Panel(self)
        rowLabels = [str(i+1) for i in range(len(self.items))]
        colLabels = ['Space Gp','Uniq','nConj','nSup','Trans','Vec','a','b','c','alpha','beta','gamma','Volume']
        Types = [wg.GRID_VALUE_STRING,]+3*[wg.GRID_VALUE_LONG,]+2*[wg.GRID_VALUE_STRING,]+ \
            3*[wg.GRID_VALUE_FLOAT+':10,5',]+3*[wg.GRID_VALUE_FLOAT+':10,3',]+[wg.GRID_VALUE_FLOAT+':10,2']
        table = []
        for ip in self.items:
            phase = self.phaseDict[ip]
            natms = phase.get('nAtoms',1)
            try:
                nConj = len(phase['altList'])
                nSup = len(phase['supList'])
            except KeyError:
                nConj = 0
                nSup = 0
            cell  = list(phase['Cell'])
            trans = G2spc.Trans2Text(phase['Trans'])
            vec = G2spc.Latt2text([phase['Uvec'],])
            row = [phase['Name'],natms,nConj,nSup,trans,vec]+cell
            table.append(row)
        CellsTable = G2G.Table(table,rowLabels=rowLabels,colLabels=colLabels,types=Types)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        magDisplay = G2G.GSGrid(self.panel)
        magDisplay.SetTable(CellsTable, True)
        magDisplay.Bind(wg.EVT_GRID_CELL_LEFT_CLICK,RefreshGrid)
        magDisplay.AutoSizeColumns(False)
        mainSizer.Add(magDisplay,0)
        
        OkBtn = wx.Button(self.panel,-1,"Ok")
        OkBtn.Bind(wx.EVT_BUTTON, self.OnOk)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((20,20),1)
        btnSizer.Add(OkBtn)
        btnSizer.Add((20,20),1)
        
        mainSizer.Add(btnSizer,0,wx.EXPAND|wx.BOTTOM|wx.TOP, 10)
        self.panel.SetSizer(mainSizer)
        self.panel.Fit()
        self.Fit()

                
    def OnOk(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.Destroy()
#        self.EndModal(wx.ID_OK)

class RDFDialog(wx.Dialog):
    def __init__(self,parent):
        wx.Dialog.__init__(self,parent,-1,'Background radial distribution function',
            pos=wx.DefaultPosition,style=wx.DEFAULT_DIALOG_STYLE)
        self.panel = None
        self.result = {'UseObsCalc':'obs-calc','maxR':20.0,'Smooth':'linear'}
        
        self.Draw()
        
    def Draw(self):
        
        def OnUseOC(event):
            self.result['UseObsCalc'] = useOC.GetValue()
            
        def OnSmCombo(event):
            self.result['Smooth'] = smCombo.GetValue()
                    
        if self.panel: self.panel.Destroy()
        self.panel = wx.Panel(self)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(wx.StaticText(self.panel,label='Background RDF controls:'),0)
        plotType = wx.BoxSizer(wx.HORIZONTAL)
        plotType.Add(wx.StaticText(self.panel,label=' Select plot type:'),0,WACV)
        Choices = ['obs-back','calc-back','obs-calc']
        useOC = wx.ComboBox(self.panel,value=Choices[2],choices=Choices,
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
        useOC.SetValue(self.result['UseObsCalc'])
        useOC.Bind(wx.EVT_COMBOBOX,OnUseOC)
        plotType.Add(useOC,0,WACV)
        mainSizer.Add(plotType,0)
        dataSizer = wx.BoxSizer(wx.HORIZONTAL)
        dataSizer.Add(wx.StaticText(self.panel,label=' Smoothing type: '),0,WACV)
        smChoice = ['linear','nearest',]
        smCombo = wx.ComboBox(self.panel,value=self.result['Smooth'],choices=smChoice,
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        smCombo.Bind(wx.EVT_COMBOBOX, OnSmCombo)
        dataSizer.Add(smCombo,0,WACV)
        dataSizer.Add(wx.StaticText(self.panel,label=' Maximum radial dist.: '),0,WACV)
        maxR = G2G.ValidatedTxtCtrl(self.panel,self.result,'maxR',nDig=(10,1),xmin=10.,xmax=50.,
            typeHint=float)
        dataSizer.Add(maxR,0,WACV)
        mainSizer.Add(dataSizer,0)

        OkBtn = wx.Button(self.panel,-1,"Ok")
        OkBtn.Bind(wx.EVT_BUTTON, self.OnOk)
        cancelBtn = wx.Button(self.panel,-1,"Cancel")
        cancelBtn.Bind(wx.EVT_BUTTON, self.OnCancel)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((20,20),1)
        btnSizer.Add(OkBtn)
        btnSizer.Add((20,20),1)
        btnSizer.Add(cancelBtn)
        btnSizer.Add((20,20),1)
        
        mainSizer.Add(btnSizer,0,wx.EXPAND|wx.BOTTOM|wx.TOP, 10)
        self.panel.SetSizer(mainSizer)
        self.panel.Fit()
        self.Fit()
        
    def GetSelection(self):
        return self.result

    def OnOk(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_OK)

    def OnCancel(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_CANCEL)
        
    
################################################################################
##### Setup routines
################################################################################

def GetFileBackground(G2frame,xye,Pattern):
    bxye = np.zeros(len(xye[1]))
    if 'BackFile' in Pattern[0]:
        backfile,mult = Pattern[0]['BackFile'][:2]
        if backfile:
            bId = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,backfile)
            if bId:
                bxye = mult*G2frame.GPXtree.GetItemPyData(bId)[1][1]
            else:
                print('Error: background PWDR {} not found'.format(backfile))
                Pattern[0]['BackFile'][0] = ''
    return bxye
    
def IsHistogramInAnyPhase(G2frame,histoName):
    '''Tests a Histogram to see if it is linked to any phases.
    Returns the name of the first phase where the histogram is used.
    '''
    phases = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,'Phases')
    if phases:
        item, cookie = G2frame.GPXtree.GetFirstChild(phases)
        while item:
            data = G2frame.GPXtree.GetItemPyData(item)
            histoList = data['Histograms'].keys()
            if histoName in histoList:
                return G2frame.GPXtree.GetItemText(item)
            item, cookie = G2frame.GPXtree.GetNextChild(phases, cookie)
        return False
    else:
        return False

def SetupSampleLabels(histName,dataType,histType):
    '''Setup a list of labels and number formatting for use in
    labeling sample parameters.
    :param str histName: Name of histogram, ("PWDR ...")
    :param str dataType: 
    '''
    parms = []
    parms.append(['Scale','Histogram scale factor: ',[10,7]])
    if 'C' in histType:
        parms.append(['Gonio. radius','Goniometer radius (mm): ',[10,3]])
    if 'PWDR' in histName:
        if dataType == 'Debye-Scherrer':
            if 'T' in histType:
                parms += [['Absorption',u'Sample absorption (\xb5\xb7r/l): ',[10,4]],]
            else:
                parms += [['DisplaceX',u'Sample X displ. perp. to beam (\xb5m): ',[10,3]],
                    ['DisplaceY',u'Sample Y displ. || to beam (\xb5m): ',[10,3]],
                    ['Absorption',u'Sample absorption (\xb5\xb7r): ',[10,4]],]
        elif dataType == 'Bragg-Brentano':
            parms += [['Shift',u'Sample displacement(\xb5m): ',[10,4]],
                ['Transparency',u'Sample transparency(1/\xb5eff, cm): ',[10,3]],
                ['SurfRoughA','Surface roughness A: ',[10,4]],
                ['SurfRoughB','Surface roughness B: ',[10,4]]]
    elif 'SASD' in histName:
        parms.append(['Thick','Sample thickness (mm)',[10,3]])
        parms.append(['Trans','Transmission (meas)',[10,3]])
        parms.append(['SlitLen',u'Slit length (Q,\xc5'+Pwrm1+')',[10,3]])
    parms.append(['Omega','Goniometer omega:',[10,3]])
    parms.append(['Chi','Goniometer chi:',[10,3]])
    parms.append(['Phi','Goniometer phi:',[10,3]])
    parms.append(['Azimuth','Detector azimuth:',[10,3]])
    parms.append(['Time','Clock time (s):',[12,3]])
    parms.append(['Temperature','Sample temperature (K): ',[10,3]])
    parms.append(['Pressure','Sample pressure (MPa): ',[10,3]])
    return parms

def SetDefaultSASDModel():
    'Fills in default items for the SASD Models dictionary'    
    return {'Back':[0.0,False],
        'Size':{'MinDiam':50,'MaxDiam':10000,'Nbins':100,'logBins':True,'Method':'MaxEnt',
                'Distribution':[],'Shape':['Spheroid',1.0],
                'MaxEnt':{'Niter':100,'Precision':0.01,'Sky':-3},
                'IPG':{'Niter':100,'Approach':0.8,'Power':-1},'Reg':{},},
        'Pair':{'Method':'Moore','MaxRadius':100.,'NBins':100,'Errors':'User',
                'Percent error':2.5,'Background':[0,False],'Distribution':[],
                'Moore':10,'Dist G':100.,'Result':[],},            
        'Particle':{'Matrix':{'Name':'vacuum','VolFrac':[0.0,False]},'Levels':[],},
        'Shapes':{'outName':'run','NumAA':100,'Niter':1,'AAscale':1.0,'Symm':1,'bias-z':0.0,
                 'inflateV':1.0,'AAglue':0.0,'pdbOut':False,'boxStep':4.0},
        'Current':'Size dist.','BackFile':'',
        }
        
def SetDefaultREFDModel():
    '''Fills in default items for the REFD Models dictionary which are 
    defined as follows for each layer:
    
    * Name: name of substance
    * Thick: thickness of layer in Angstroms (not present for top & bottom layers)
    * Rough: upper surface roughness for layer (not present for toplayer)
    * Penetration: mixing of layer substance into layer above-is this needed?
    * DenMul: multiplier for layer scattering density (default = 1.0)
        
    Top layer defaults to vacuum (or air/any gas); can be substituted for some other substance.
    
    Bottom layer default: infinitely thisck Silicon; can be substituted for some other substance.
    '''
    return {'Layers':[{'Name':'vacuum','DenMul':[1.0,False],},                                  #top layer
        {'Name':'vacuum','Rough':[0.,False],'Penetration':[0.,False],'DenMul':[1.0,False],}],   #bottom layer
        'Scale':[1.0,False],'FltBack':[0.0,False],'Zero':'Top','dQ type':'None','Layer Seq':[],               #globals
        'Minimizer':'LMLS','Resolution':[0.,'Const dq/q'],'Recomb':0.5,'Toler':0.5,             #minimizer controls
        'DualFitFiles':['',],'DualFltBacks':[[0.0,False],],'DualScales':[[1.0,False],]}         #optional stuff for multidat fits?
        
def SetDefaultSubstances():
    'Fills in default items for the SASD Substances dictionary'
    return {'Substances':{'vacuum':{'Elements':{},'Volume':1.0,'Density':0.0,'Scatt density':0.0,'XImag density':0.0},
        'unit scatter':{'Elements':None,'Volume':None,'Density':None,'Scatt density':1.0,'XImag density':1.0}}}

def GetFileList(G2frame,fileType):
    fileList = []
    Id, cookie = G2frame.GPXtree.GetFirstChild(G2frame.root)
    while Id:
        name = G2frame.GPXtree.GetItemText(Id)
        if fileType in name.split()[0]:
            fileList.append(name)
        Id, cookie = G2frame.GPXtree.GetNextChild(G2frame.root, cookie)
    return fileList
        
def GetHistsLikeSelected(G2frame):
    '''Get the histograms that match the current selected one:
    The histogram prefix and data type (PXC etc.), the number of
    wavelengths and the instrument geometry (Debye-Scherrer etc.) 
    must all match. The current histogram is not included in the list. 

    :param wx.Frame G2frame: pointer to main GSAS-II data tree
    '''
    histList = []
    inst,inst2 = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Instrument Parameters'))
    hType = inst['Type'][0]
    if 'Lam1' in inst:
        hLam = 2
    elif 'Lam' in inst:
        hLam = 1
    else:
        hLam = 0
    sample = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId,'Sample Parameters'))
#    hGeom = sample.get('Type')
    hstName = G2frame.GPXtree.GetItemText(G2frame.PatternId)
    hPrefix = hstName.split()[0]+' '
    # cycle through tree looking for items that match the above
    item, cookie = G2frame.GPXtree.GetFirstChild(G2frame.root)        
    while item:
        name = G2frame.GPXtree.GetItemText(item)
        if name.startswith(hPrefix) and name != hstName:
            cGeom,cType,cLam, = '?','?',-1
            subitem, subcookie = G2frame.GPXtree.GetFirstChild(item)
            while subitem:
                subname = G2frame.GPXtree.GetItemText(subitem)
                if subname == 'Sample Parameters':
                    sample = G2frame.GPXtree.GetItemPyData(subitem)
#                    cGeom = sample.get('Type')
                elif subname == 'Instrument Parameters':
                    inst,inst2 = G2frame.GPXtree.GetItemPyData(subitem)
                    cType = inst['Type'][0]
                    if 'Lam1' in inst:
                        cLam = 2
                    elif 'Lam' in inst:
                        cLam = 1
                    else:
                        cLam = 0
                subitem, subcookie = G2frame.GPXtree.GetNextChild(item, subcookie)
            if cLam == hLam and cType == hType: # and cGeom == hGeom:
                if name not in histList: histList.append(name)
        item, cookie = G2frame.GPXtree.GetNextChild(G2frame.root, cookie)
    return histList

def SetCopyNames(histName,dataType,addNames=[]):
    '''Determine the items in the sample parameters that should be copied,
    depending on the histogram type and the instrument type.
    '''
    copyNames = ['Scale',]
    histType = 'HKLF'
    if 'PWDR' in histName:
        histType = 'PWDR'
        if 'Debye' in dataType:
            copyNames += ['DisplaceX','DisplaceY','Absorption']
        else:       #Bragg-Brentano
            copyNames += ['Shift','Transparency','SurfRoughA','SurfRoughB']
    elif 'SASD' in histName:
        histType = 'SASD'
        copyNames += ['Materials','Thick',]
    if len(addNames):
        copyNames += addNames
    return histType,copyNames
    
def CopyPlotCtrls(G2frame):
    '''Global copy: Copy plot controls from current histogram to others.
    '''
    hst = G2frame.GPXtree.GetItemText(G2frame.PatternId)
    histList = GetHistsLikeSelected(G2frame)
    if not histList:
        G2frame.ErrorDialog('No match','No other histograms match '+hst,G2frame)
        return
    sourceData = G2frame.GPXtree.GetItemPyData(G2frame.PatternId)
    
    if 'Offset' not in sourceData[0]:    #patch for old data
        sourceData[0].update({'Offset':[0.0,0.0],'delOffset':0.02,'refOffset':-1.0,
            'refDelt':0.01,})
        G2frame.GPXtree.SetItemPyData(G2frame.PatternId,sourceData)
        
    dlg = G2G.G2MultiChoiceDialog(G2frame,'Copy plot controls from\n'+str(hst[5:])+' to...',
        'Copy plot controls', histList)
    results = []
    try:
        if dlg.ShowModal() == wx.ID_OK:
            results = dlg.GetSelections()
    finally:
        dlg.Destroy()
    copyList = []
    for i in results: 
        copyList.append(histList[i])

    keys = ['Offset','delOffset','refOffset','refDelt']
    source = dict(zip(keys,[sourceData[0][item] for item in keys]))
    for hist in copyList:
        Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,hist)
        data = G2frame.GPXtree.GetItemPyData(Id)
        data[0].update(source)
        G2frame.GPXtree.SetItemPyData(Id,data)
    print ('Copy of plot controls successful')

def CopySelectedHistItems(G2frame):
    '''Global copy: Copy items from current histogram to others.
    '''
    hst = G2frame.GPXtree.GetItemText(G2frame.PatternId)
    histList = GetHistsLikeSelected(G2frame)
    if not histList:
        G2frame.ErrorDialog('No match','No other histograms match '+hst,G2frame)
        return
    choices = ['Limits','Background','Instrument Parameters','Sample Parameters']
    dlg = G2G.G2MultiChoiceDialog(G2frame,'Copy which histogram sections from\n'+str(hst[5:]),
        'Select copy sections', choices, filterBox=False)
    dlg.SetSelections(range(len(choices)))
    choiceList = []
    if dlg.ShowModal() == wx.ID_OK:
        choiceList = [choices[i] for i in dlg.GetSelections()]
    if not choiceList: return
    
    dlg = G2G.G2MultiChoiceDialog(G2frame,'Copy parameters from\n'+str(hst[5:])+' to...',
        'Copy parameters', histList)
    results = []
    try:
        if dlg.ShowModal() == wx.ID_OK:
            results = dlg.GetSelections()
    finally:
        dlg.Destroy()
    copyList = []
    for i in results: 
        copyList.append(histList[i])

    if 'Limits' in choiceList: # Limits
        data = G2frame.GPXtree.GetItemPyData(
            G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId,'Limits'))
        for item in copyList:
            Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,item)
            G2frame.GPXtree.SetItemPyData(
                G2gd.GetGPXtreeItemId(G2frame,Id,'Limits'),
                copy.deepcopy(data))
    if 'Background' in choiceList:  # Background
        data = G2frame.GPXtree.GetItemPyData(
            G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId,'Background'))
        for item in copyList:
            Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,item)
            G2frame.GPXtree.SetItemPyData(
                G2gd.GetGPXtreeItemId(G2frame,Id,'Background'),
                copy.deepcopy(data))
    if 'Instrument Parameters' in choiceList:  # Instrument Parameters
        # for now all items in Inst. parms are copied
        data,data1 = G2frame.GPXtree.GetItemPyData(
            G2gd.GetGPXtreeItemId(
                G2frame,G2frame.PatternId,'Instrument Parameters'))
        for item in copyList:
            Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,item)
            G2frame.GPXtree.GetItemPyData(
                G2gd.GetGPXtreeItemId(G2frame,Id,'Instrument Parameters')
                )[0].update(copy.deepcopy(data))
            G2frame.GPXtree.GetItemPyData(
                G2gd.GetGPXtreeItemId(G2frame,Id,'Instrument Parameters')
                )[1].update(copy.deepcopy(data1))
    if 'Sample Parameters' in choiceList:  # Sample Parameters
        data = G2frame.GPXtree.GetItemPyData(
            G2gd.GetGPXtreeItemId(
                G2frame,G2frame.PatternId,'Sample Parameters'))
        # selects items to be copied
        histType,copyNames = SetCopyNames(hst,data['Type'],
            addNames = ['Omega','Chi','Phi','Gonio. radius','InstrName'])
        copyDict = {parm:data[parm] for parm in copyNames}
        for item in copyList:
            Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,item)
            G2frame.GPXtree.GetItemPyData(
                G2gd.GetGPXtreeItemId(G2frame,Id,'Sample Parameters')
                ).update(copy.deepcopy(copyDict))
                         
def TestMagAtoms(phase,magAtms,SGData,Uvec,Trans,allmom,maxequiv=100,maximal=False):
    found = False
    anymom = False
    phase['Keep'] = False
    if not magAtms:
        phase['Keep'] = True
        return []
    invTrans = nl.inv(Trans)
    atCodes = []
    Phase = {'General':{'AtomPtrs':[2,1],'SGData':copy.deepcopy(phase['SGData'])},'Atoms':[]}
    for matm in magAtms:
        XYZ = G2spc.GenAtom(matm[3:6],SGData,False,Move=True)
        xyzs = [xyz[0] for xyz in XYZ]
        atCodes += len(xyzs)*['1',]
        xyzs,atCodes = G2lat.ExpandCell(xyzs,atCodes,0,Trans)
        for ix,x in enumerate(xyzs):
            xyz = G2lat.TransformXYZ(x-Uvec,invTrans.T,np.zeros(3))%1.
            Phase['Atoms'].append(matm[:2]+list(xyz))
            SytSym,Mul,Nop,dupDir = G2spc.SytSym(xyz,phase['SGData'])
            CSI = G2spc.GetCSpqinel(phase['SGData']['SpnFlp'],dupDir)
            if any(CSI[0]):     
                anymom = True
            if allmom:
                if not any(CSI[0]):
                    phase['Keep'] = False
                    found = True
    uAtms = G2lat.GetUnique(Phase,atCodes)[0]
    natm = len(uAtms)
    if anymom and natm <= maxequiv and not found:
        phase['Keep'] = True
        if maximal and phase['supList'][0]:
            phase['Keep'] = False
    return uAtms

def TestAtoms(phase,magAtms,SGData,Uvec,Trans,maxequiv=100,maximal=False):
    phase['Keep'] = True
    invTrans = nl.inv(Trans)
    atCodes = []
    Phase = {'General':{'AtomPtrs':[2,1],'SGData':copy.deepcopy(phase['SGData'])},'Atoms':[]}
    for matm in magAtms:
        XYZ = G2spc.GenAtom(matm[3:6],SGData,False,Move=True)
        xyzs = [xyz[0] for xyz in XYZ]
        atCodes += len(xyzs)*['1',]
        xyzs,atCodes = G2lat.ExpandCell(xyzs,atCodes,0,Trans)
        for ix,x in enumerate(xyzs):
            xyz = G2lat.TransformXYZ(x-Uvec,invTrans.T,np.zeros(3))%1.
            Phase['Atoms'].append(matm[:2]+list(xyz))
    uAtms = G2lat.GetUnique(Phase,atCodes)[0]
    natm = len(uAtms)
    if natm > maxequiv: #too many allowed atoms found
        phase['Keep'] = False
    if maximal and phase['supList'][0]:
        phase['Keep'] = False
    return uAtms

################################################################################
#####  Powder Peaks
################################################################################           
       
def UpdatePeakGrid(G2frame, data):
    '''respond to selection of PWDR powder peaks data tree item.
    '''
    def OnAutoSearch(event):
        PatternId = G2frame.PatternId
        limits = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Limits'))[1]
        inst,inst2 = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Instrument Parameters'))
        Pattern = G2frame.GPXtree.GetItemPyData(PatternId)
        profile = Pattern[1]
        bxye = GetFileBackground(G2frame,profile,Pattern)
        x0 = profile[0]
        iBeg = np.searchsorted(x0,limits[0])
        iFin = np.searchsorted(x0,limits[1])
        x = x0[iBeg:iFin]
        y0 = (profile[1]+bxye)[iBeg:iFin]
        ysig = 1.0*np.std(y0)
        offset = [-1,1]
        ymask = ma.array(y0,mask=(y0<ysig))
        for off in offset:
            ymask = ma.array(ymask,mask=(ymask-np.roll(y0,off)<=0.))
        indx = ymask.nonzero()
        mags = ymask[indx]
        poss = x[indx]
        refs = list(zip(poss,mags))
        if 'T' in Inst['Type'][0]:    
            refs = G2mth.sortArray(refs,0,reverse=True)     #big TOFs first
        else:   #'c' or 'B'
            refs = G2mth.sortArray(refs,0,reverse=False)    #small 2-Thetas first
        for i,ref1 in enumerate(refs):      #reject picks closer than 1 FWHM
            for ref2 in refs[i+1:]:
                if abs(ref2[0]-ref1[0]) < 2.*G2pwd.getFWHM(ref1[0],inst):
                    del(refs[i])
        if 'T' in Inst['Type'][0]:    
            refs = G2mth.sortArray(refs,1,reverse=False)
        else:   #'C' or 'B'
            refs = G2mth.sortArray(refs,1,reverse=True)
        for pos,mag in refs:
            data['peaks'].append(G2mth.setPeakparms(inst,inst2,pos,mag))
        UpdatePeakGrid(G2frame,data)
        G2plt.PlotPatterns(G2frame,plotType='PWDR')
        
    def OnCopyPeaks(event):
        hst = G2frame.GPXtree.GetItemText(G2frame.PatternId)
        histList = GetHistsLikeSelected(G2frame)
        if not histList:
            G2frame.ErrorDialog('No match','No histograms match '+hst,G2frame)
            return
        copyList = []
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Copy peak list from\n'+str(hst[5:])+' to...',
            'Copy peaks', histList)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                for i in dlg.GetSelections():
                    copyList.append(histList[i])
        finally:
            dlg.Destroy()
        for item in copyList:
            Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,item)
            G2frame.GPXtree.SetItemPyData(
                G2gd.GetGPXtreeItemId(G2frame,Id,'Peak List'),copy.deepcopy(data))
            
    def OnLoadPeaks(event):
        pth = G2G.GetExportPath(G2frame)
        dlg = wx.FileDialog(G2frame, 'Choose GSAS-II PWDR peaks list file', pth, '', 
            'PWDR peak list files (*.pkslst)|*.pkslst',wx.FD_OPEN)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                peaks = []
                filename = dlg.GetPath()
                File = open(filename,'r')
                S = File.readline()
                while S:
                    if '#' in S:
                        S = File.readline()
                        continue
                    try:
                        peaks.append(eval(S))
                    except:
                        break
                    S = File.readline()
                File.close()
        finally:
            dlg.Destroy()
        data = {'peaks':peaks,'sigDict':{}}
        UpdatePeakGrid(G2frame,data)
        G2plt.PlotPatterns(G2frame,plotType='PWDR')
        
    def OnSavePeaks(event):
        pth = G2G.GetExportPath(G2frame)
        dlg = wx.FileDialog(G2frame, 'Choose GSAS-II PWDR peaks list file', pth, '', 
            'PWDR peak list files (*.pkslst)|*.pkslst',wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                # make sure extension is .pkslst
                filename = os.path.splitext(filename)[0]+'.pkslst'
                File = open(filename,'w')
                File.write("#GSAS-II PWDR peaks list file; do not add/delete items!\n")
                for item in data:
                    if item == 'peaks':
                        for pk in data[item]:
                            File.write(str(pk)+'\n')
                File.close()
                print ('PWDR peaks list saved to: '+filename)
        finally:
            dlg.Destroy()
    
    def OnUnDo(event):
        DoUnDo()
        G2frame.dataWindow.UnDo.Enable(False)
        
    def DoUnDo():
        print ('Undo last refinement')
        file = open(G2frame.undofile,'rb')
        PatternId = G2frame.PatternId
        for item in ['Background','Instrument Parameters','Peak List']:
            G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, item),cPickle.load(file))
            if G2frame.dataWindow.GetName() == item:
                if item == 'Background':
                    UpdateBackground(G2frame,G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, item)))
                elif item == 'Instrument Parameters':
                    UpdateInstrumentGrid(G2frame,G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, item)))
                elif item == 'Peak List':
                    UpdatePeakGrid(G2frame,G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, item)))
            print (item+' recovered')
        file.close()
        
    def SaveState():
        G2frame.undofile = os.path.join(G2frame.dirname,'GSASII.save')
        file = open(G2frame.undofile,'wb')
        PatternId = G2frame.PatternId
        for item in ['Background','Instrument Parameters','Peak List']:
            cPickle.dump(G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId,item)),file,1)
        file.close()
        G2frame.dataWindow.UnDo.Enable(True)
        
    def OnLSQPeakFit(event):
        if reflGrid.IsCellEditControlEnabled(): # complete any grid edits in progress
            reflGrid.HideCellEditControl()
            reflGrid.DisableCellEditControl()
        if not G2frame.GSASprojectfile:            #force a save of the gpx file so SaveState can write in the same directory
            G2frame.OnFileSaveas(event)
        wx.CallAfter(OnPeakFit,'LSQ')
        
    def OnOneCycle(event):
        if reflGrid.IsCellEditControlEnabled(): # complete any grid edits in progress
            reflGrid.HideCellEditControl()
            reflGrid.DisableCellEditControl()
        wx.CallAfter(OnPeakFit,'LSQ',oneCycle=True)
        
    def OnSeqPeakFit(event):
        histList = G2gd.GetGPXtreeDataNames(G2frame,['PWDR',])
        od = {'label_1':'Copy to next','value_1':False,'label_2':'Reverse order','value_2':False}
        dlg = G2G.G2MultiChoiceDialog(G2frame, 'Sequential peak fits',
             'Select dataset to include',histList,extraOpts=od)
        names = []
        if dlg.ShowModal() == wx.ID_OK:
            for sel in dlg.GetSelections():
                names.append(histList[sel])
        dlg.Destroy()
        if not names:
            return
        Id =  G2gd.GetGPXtreeItemId(G2frame,G2frame.root,'Sequential peak fit results')
        if Id:
            SeqResult = G2frame.GPXtree.GetItemPyData(Id)
        else:
            SeqResult = {}
            Id = G2frame.GPXtree.AppendItem(parent=G2frame.root,text='Sequential peak fit results')
        SeqResult = {'SeqPseudoVars':{},'SeqParFitEqList':[]}
        SeqResult['histNames'] = names
        dlg = wx.ProgressDialog('Sequential peak fit','Data set name = '+names[0],len(names), 
            style = wx.PD_ELAPSED_TIME|wx.PD_AUTO_HIDE|wx.PD_REMAINING_TIME|wx.PD_CAN_ABORT)
        controls = {'deriv type':'analytic','min dM/M':0.001,}
        print ('Peak Fitting with '+controls['deriv type']+' derivatives:')
        oneCycle = False
        FitPgm = 'LSQ'
        prevVaryList = []
        peaks = None
        varyList = None
        if od['value_2']:
            names.reverse()
        try:
            for i,name in enumerate(names):
                print (' Sequential fit for '+name)
                dlg.Raise()
                GoOn = dlg.Update(i,newmsg='Data set name = '+name)[0]
                if not GoOn:
                    dlg.Destroy()
                    break
                PatternId =  G2gd.GetGPXtreeItemId(G2frame,G2frame.root,name)
                if i and od['value_1']:
                    G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Peak List'),copy.deepcopy(peaks))
                    prevVaryList = varyList[:]
                peaks = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Peak List'))
                background = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Background'))
                limits = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Limits'))[1]
                inst,inst2 = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Instrument Parameters'))
                Pattern = G2frame.GPXtree.GetItemPyData(PatternId)
                data = Pattern[1]
                fixback = GetFileBackground(G2frame,data,Pattern)
                peaks['sigDict'],result,sig,Rvals,varyList,parmDict,fullvaryList,badVary = G2pwd.DoPeakFit(FitPgm,peaks['peaks'],
                    background,limits,inst,inst2,data,fixback,prevVaryList,oneCycle,controls)   #needs wtFactor after controls?
                if len(result[0]) != len(fullvaryList):
                    dlg.Destroy()
                    print (' ***** Sequential peak fit stopped at '+name+' *****')
                    break
                else:
                    G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Peak List'),copy.deepcopy(peaks))
                    SeqResult[name] = {'variables':result[0],'varyList':varyList,'sig':sig,'Rvals':Rvals,
                        'covMatrix':np.eye(len(result[0])),'title':name,'parmDict':parmDict,
                        'fullVary':fullvaryList,'badVary':badVary}
            print (' ***** Sequential peak fit successful *****')
        finally:
            dlg.Destroy()
        SeqResult['histNames'] = histList
        G2frame.GPXtree.SetItemPyData(Id,SeqResult)
        G2frame.G2plotNB.Delete('Sequential refinement')    #clear away probably invalid plot
        G2frame.GPXtree.SelectItem(Id)
        
    def OnClearPeaks(event):
        dlg = wx.MessageDialog(G2frame,'Delete all peaks?','Clear peak list',wx.OK|wx.CANCEL)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                peaks = {'peaks':[],'sigDict':{}}
        finally:
            dlg.Destroy()
        UpdatePeakGrid(G2frame,peaks)
        G2plt.PlotPatterns(G2frame,plotType='PWDR')
        
    def OnPeakFit(FitPgm,oneCycle=False):
        SaveState()
        controls = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.root, 'Controls'))
        if not controls:
            controls = {'deriv type':'analytic','min dM/M':0.001,}     #fill in defaults if needed
        print ('Peak Fitting with '+controls['deriv type']+' derivatives:')
        PatternId = G2frame.PatternId
        peaks = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Peak List'))
        if not peaks:
            G2frame.ErrorDialog('No peaks!','Nothing to fit!')
            return
        background = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Background'))
        limits = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Limits'))[1]
        inst,inst2 = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Instrument Parameters'))
        Pattern = G2frame.GPXtree.GetItemPyData(PatternId)
        data = Pattern[1]
        wtFactor = Pattern[0]['wtFactor']
        bxye = GetFileBackground(G2frame,data,Pattern)
        dlg = wx.ProgressDialog('Residual','Peak fit Rwp = ',101.0, 
            style = wx.PD_ELAPSED_TIME|wx.PD_AUTO_HIDE|wx.PD_REMAINING_TIME|wx.PD_CAN_ABORT)
        screenSize = wx.ClientDisplayRect()
        Size = dlg.GetSize()
        if 50 < Size[0] < 500: # sanity check on size, since this fails w/Win & wx3.0
            dlg.SetSize((int(Size[0]*1.2),Size[1])) # increase size a bit along x
            dlg.SetPosition(wx.Point(screenSize[2]-Size[0]-305,screenSize[1]+5))
        try:
            results = G2pwd.DoPeakFit(FitPgm,peaks['peaks'],background,limits,inst,inst2,data,bxye,[],oneCycle,controls,wtFactor,dlg)
            peaks['sigDict'] = results[0]
            text = 'Peak fit: Rwp=%.2f%% Nobs= %d Nparm= %d Npeaks= %d'%(results[3]['Rwp'],results[1][2]['fjac'].shape[1],len(results[0]),len(peaks['peaks']))
        finally:
#            dlg.Destroy()
            print ('finished')
        newpeaks = copy.copy(peaks)
        G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Peak List'),newpeaks)
        G2frame.AddToNotebook(text)
        G2plt.PlotPatterns(G2frame,plotType='PWDR')
        wx.CallAfter(UpdatePeakGrid,G2frame,newpeaks)
        
    def OnResetSigGam(event):
        PatternId = G2frame.PatternId
        Inst,Inst2 = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Instrument Parameters'))
        peaks = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Peak List'))
        if not peaks['peaks']:
            G2frame.ErrorDialog('No peaks!','Nothing to do!')
            return
        newpeaks = {'peaks':[],'sigDict':{}}
        for peak in peaks['peaks']:
            newpeaks['peaks'].append(G2mth.setPeakparms(Inst,Inst2,peak[0],peak[2]))
        G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Peak List'),newpeaks)
        UpdatePeakGrid(G2frame,newpeaks)
                
    def setBackgroundColors():
       for r in range(reflGrid.GetNumberRows()):
           for c in range(reflGrid.GetNumberCols()):
               if reflGrid.GetColLabelValue(c) in ['position','intensity','alpha','beta','sigma','gamma']:
                   if float(reflGrid.GetCellValue(r,c)) < 0.:
                       reflGrid.SetCellBackgroundColour(r,c,wx.RED)
                   else:
                       reflGrid.SetCellBackgroundColour(r,c,wx.WHITE)
                                                  
    def KeyEditPeakGrid(event):
        '''Respond to pressing a key to act on selection of a row, column or cell
        in the Peak List table
        '''
        rowList = reflGrid.GetSelectedRows()
        colList = reflGrid.GetSelectedCols()
        selectList = reflGrid.GetSelectedCells()
        data = G2frame.GPXtree.GetItemPyData(G2frame.PickId)
        if event.GetKeyCode() == wx.WXK_RETURN:
            event.Skip(True)
        elif event.GetKeyCode() == wx.WXK_CONTROL:
            event.Skip(True)
        elif event.GetKeyCode() == wx.WXK_SHIFT:
            event.Skip(True)
        elif rowList and (event.GetKeyCode() == wx.WXK_DELETE or event.GetKeyCode() == 8):
            # pressing the delete key or backspace deletes selected peak(s)
            reflGrid.ClearSelection()
            reflGrid.ClearGrid()
            rowList.sort()
            rowList.reverse()
            nDel = 0
            for row in rowList:
                G2frame.PeakTable.DeleteRow(row)
                nDel += 1
            if nDel:
                msg = wg.GridTableMessage(G2frame.PeakTable, 
                    wg.GRIDTABLE_NOTIFY_ROWS_DELETED,0,nDel)
                reflGrid.ProcessTableMessage(msg)
            data['peaks'] = G2frame.PeakTable.GetData()[:-nDel]
            G2frame.GPXtree.SetItemPyData(G2frame.PickId,data)
            setBackgroundColors()
        elif colList and (event.GetKeyCode() == 89 or event.GetKeyCode() == 78):
            reflGrid.ClearSelection()
            key = event.GetKeyCode()
            for col in colList:
                if G2frame.PeakTable.GetTypeName(0,col) == wg.GRID_VALUE_BOOL:
                    if key == 89: #'Y'
                        for row in range(G2frame.PeakTable.GetNumberRows()): data['peaks'][row][col]=True
                    elif key == 78:  #'N'
                        for row in range(G2frame.PeakTable.GetNumberRows()): data['peaks'][row][col]=False
        elif selectList and (event.GetKeyCode() == 89 or event.GetKeyCode() == 78):
            reflGrid.ClearSelection()
            key = event.GetKeyCode()
            for row,col in selectList:
                if G2frame.PeakTable.GetTypeName(row,col) == wg.GRID_VALUE_BOOL:
                    if key == 89: #'Y'
                        data['peaks'][row][col]=True
                    elif key == 78:  #'N'
                        data['peaks'][row][col]=False
        else:
            event.Skip()
            return
        G2plt.PlotPatterns(G2frame,plotType='PWDR')
        wx.CallAfter(UpdatePeakGrid,G2frame,data)
            
    def SelectVars(rows):
        '''Set or clear peak refinement variables for peaks listed in rows
        '''
        refOpts = {reflGrid.GetColLabelValue(i):i+1 for i in range(reflGrid.GetNumberCols()) if reflGrid.GetColLabelValue(i) != "refine"}
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Select columns to refine',
            'Refinement Selection', sorted(refOpts.keys()),
            filterBox=False,toggle=False)
        sels = []
        try:
            if dlg.ShowModal() == wx.ID_OK:
                sels = [sorted(refOpts.keys())[i] for i in dlg.GetSelections()]
            else:
                return
        finally:
            dlg.Destroy()
        for r in rows:
            for lbl,c in refOpts.items():
                data['peaks'][r][c] = lbl in sels
        UpdatePeakGrid(G2frame,data)
        
    def OnRefineSelected(event):
        '''set refinement flags for the selected peaks
        '''
        rows = list(set([row for row,col in reflGrid.GetSelectedCells()] +
                        reflGrid.GetSelectedRows()))
        if not rows:
            wx.MessageBox('No selected rows. You must select rows or cells before using this command',
                          caption='No selected peaks')
            return
        SelectVars(rows)

    def OnRefineAll(event):
        '''set refinement flags for all peaks
        '''
        SelectVars(range(reflGrid.GetNumberRows()))

#    def onCellListSClick(event):
#        '''Called when a peak is selected so that it can be highlighted in the plot
#        '''
#        event.Skip()
#        c =  event.GetRow(),event.GetCol()
#        if c < 0: # replot except whan a column is selected
#            wx.CallAfter(G2plt.PlotPatterns,G2frame,plotType='PWDR')
#        
    def onCellListDClick(event):
        '''Called after a double-click on a cell label'''
        r,c =  event.GetRow(),event.GetCol()
        if r < 0 and c < 0:
            for row in range(reflGrid.GetNumberRows()):
                reflGrid.SelectRow(row,True)                    
            for col in range(reflGrid.GetNumberCols()):
                reflGrid.SelectCol(col,True)                    
        elif r > 0:     #row label: select it and replot!
            reflGrid.ClearSelection()
            reflGrid.SelectRow(r,True)
            wx.CallAfter(G2frame.reflGrid.ForceRefresh)
            wx.CallAfter(G2plt.PlotPatterns,G2frame,plotType='PWDR')
        elif c > 0:     #column label: just select it (& redisplay)
            reflGrid.ClearSelection()
            reflGrid.SelectCol(c,True)
            if reflGrid.GetColLabelValue(c) != 'refine': return
            choice = ['Y - vary all','N - vary none',]
            dlg = wx.SingleChoiceDialog(G2frame,'Select refinement option for '+reflGrid.GetColLabelValue(c-1),
                'Refinement controls',choice)
            dlg.CenterOnParent()
            if dlg.ShowModal() == wx.ID_OK:
                sel = dlg.GetSelection()
                if sel == 0:
                    for row in range(reflGrid.GetNumberRows()): data['peaks'][row][c]=True
                else:
                    for row in range(reflGrid.GetNumberRows()): data['peaks'][row][c]=False
            wx.CallAfter(UpdatePeakGrid,G2frame,data)
                 
    #======================================================================
    # beginning of UpdatePeakGrid init
    #======================================================================
    G2frame.GetStatusBar().SetStatusText('Global refine: select refine column & press Y or N',1)
    G2gd.SetDataMenuBar(G2frame,G2frame.dataWindow.PeakMenu)
    G2frame.Bind(wx.EVT_MENU, OnAutoSearch, id=G2G.wxID_AUTOSEARCH)
    G2frame.Bind(wx.EVT_MENU, OnCopyPeaks, id=G2G.wxID_PEAKSCOPY)
    G2frame.Bind(wx.EVT_MENU, OnSavePeaks, id=G2G.wxID_PEAKSAVE)
    G2frame.Bind(wx.EVT_MENU, OnLoadPeaks, id=G2G.wxID_PEAKLOAD)
    G2frame.Bind(wx.EVT_MENU, OnUnDo, id=G2G.wxID_UNDO)
    G2frame.Bind(wx.EVT_MENU, OnRefineSelected, id=G2frame.dataWindow.peaksSel.GetId())
    G2frame.Bind(wx.EVT_MENU, OnRefineAll, id=G2frame.dataWindow.peaksAll.GetId())
    G2frame.Bind(wx.EVT_MENU, OnLSQPeakFit, id=G2G.wxID_LSQPEAKFIT)
    G2frame.Bind(wx.EVT_MENU, OnOneCycle, id=G2G.wxID_LSQONECYCLE)
    G2frame.Bind(wx.EVT_MENU, OnSeqPeakFit, id=G2G.wxID_SEQPEAKFIT)
    G2frame.Bind(wx.EVT_MENU, OnClearPeaks, id=G2G.wxID_CLEARPEAKS)
    G2frame.Bind(wx.EVT_MENU, OnResetSigGam, id=G2G.wxID_RESETSIGGAM)
    if data['peaks']:
        G2frame.dataWindow.AutoSearch.Enable(False)
        G2frame.dataWindow.PeakCopy.Enable(True)
        G2frame.dataWindow.PeakFit.Enable(True)
        G2frame.dataWindow.PFOneCycle.Enable(True)
        G2frame.dataWindow.SeqPeakFit.Enable(True)
    else:
        G2frame.dataWindow.PeakFit.Enable(False)
        G2frame.dataWindow.PeakCopy.Enable(False)
        G2frame.dataWindow.PFOneCycle.Enable(False)
        G2frame.dataWindow.AutoSearch.Enable(True)
        G2frame.dataWindow.SeqPeakFit.Enable(False)
    G2frame.PickTable = []
    rowLabels = []
    PatternId = G2frame.PatternId
    Inst = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Instrument Parameters'))[0]
    for i in range(len(data['peaks'])): rowLabels.append(str(i+1))
    if 'C' in Inst['Type'][0]:
        colLabels = ['position','refine','intensity','refine','sigma','refine','gamma','refine']
        Types = [wg.GRID_VALUE_FLOAT+':10,4',wg.GRID_VALUE_BOOL,
            wg.GRID_VALUE_FLOAT+':10,1',wg.GRID_VALUE_BOOL,
            wg.GRID_VALUE_FLOAT+':10,5',wg.GRID_VALUE_BOOL,
            wg.GRID_VALUE_FLOAT+':10,5',wg.GRID_VALUE_BOOL]
    else:
        colLabels = ['position','refine','intensity','refine','alpha','refine',
            'beta','refine','sigma','refine','gamma','refine']
        if 'T' in Inst['Type'][0]:
            Types = [wg.GRID_VALUE_FLOAT+':10,1',wg.GRID_VALUE_BOOL,
                wg.GRID_VALUE_FLOAT+':10,4',wg.GRID_VALUE_BOOL,
                wg.GRID_VALUE_FLOAT+':10,4',wg.GRID_VALUE_BOOL,
                wg.GRID_VALUE_FLOAT+':10,5',wg.GRID_VALUE_BOOL,
                wg.GRID_VALUE_FLOAT+':10,5',wg.GRID_VALUE_BOOL,
                wg.GRID_VALUE_FLOAT+':10,5',wg.GRID_VALUE_BOOL]
        else:  #'B'
            Types = [wg.GRID_VALUE_FLOAT+':10,4',wg.GRID_VALUE_BOOL,
                wg.GRID_VALUE_FLOAT+':10,1',wg.GRID_VALUE_BOOL,
                wg.GRID_VALUE_FLOAT+':10,5',wg.GRID_VALUE_BOOL,
                wg.GRID_VALUE_FLOAT+':10,5',wg.GRID_VALUE_BOOL,
                wg.GRID_VALUE_FLOAT+':10,5',wg.GRID_VALUE_BOOL,
                wg.GRID_VALUE_FLOAT+':10,5',wg.GRID_VALUE_BOOL]
    T = []
    for peak in data['peaks']:
        T.append(peak[0])
    D = dict(zip(T,data['peaks']))
    T.sort()
    if 'T' in Inst['Type'][0]:  #want big TOF's first
        T.reverse()
    X = []
    for key in T: X.append(D[key])
    data['peaks'] = X
    G2frame.dataWindow.ClearData()
    mainSizer = G2frame.dataWindow.GetSizer()
    G2frame.GPXtree.SetItemPyData(G2frame.PickId,data)
    G2frame.PeakTable = G2G.Table(data['peaks'],rowLabels=rowLabels,colLabels=colLabels,types=Types)
    #G2frame.SetLabel(G2frame.GetLabel().split('||')[0]+' || '+'Peak List')
    G2frame.dataWindow.currentGrids = []
    reflGrid = G2G.GSGrid(parent=G2frame.dataWindow)
    reflGrid.SetTable(G2frame.PeakTable, True)
    setBackgroundColors()                         
#    reflGrid.Bind(wg.EVT_GRID_CELL_CHANGE, RefreshPeakGrid)
    reflGrid.Bind(wx.EVT_KEY_DOWN, KeyEditPeakGrid)
#    reflGrid.Bind(wg.EVT_GRID_LABEL_LEFT_CLICK, onCellListSClick)
#    G2frame.dataWindow.Bind(wg.EVT_GRID_CELL_LEFT_CLICK, onCellListSClick)
    reflGrid.Bind(wg.EVT_GRID_LABEL_LEFT_DCLICK, onCellListDClick)
#    G2frame.dataWindow.Bind(wg.EVT_GRID_CELL_LEFT_DCLICK, onCellListDClick)
    reflGrid.AutoSizeColumns(False)
    reflGrid.SetScrollRate(10,10)
    G2frame.reflGrid = reflGrid
    mainSizer.Add(reflGrid,1,wx.ALL|wx.EXPAND,1)
    G2frame.dataWindow.SetDataSize()

################################################################################
#####  Background
################################################################################           
       
def UpdateBackground(G2frame,data):
    '''respond to selection of PWDR background data tree item.
    '''
    def OnBackFlagCopy(event):
        flag = data[0][1]
        backDict = data[-1]
        if backDict['nDebye']:
            DBflags = []
            for term in backDict['debyeTerms']:
                DBflags.append(term[1::2])
        if backDict['nPeaks']:
            PKflags = []
            for term in backDict['peaksList']:
                PKflags.append(term[1::2])            
        hst = G2frame.GPXtree.GetItemText(G2frame.PatternId)
        histList = GetHistsLikeSelected(G2frame)
        if not histList:
            G2frame.ErrorDialog('No match','No histograms match '+hst,G2frame)
            return
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Copy bkg ref. flags from\n'+str(hst[5:])+' to...',
            'Copy bkg flags', histList)
        copyList = []
        try:
            if dlg.ShowModal() == wx.ID_OK:
                for i in dlg.GetSelections(): 
                    copyList.append(histList[i])
        finally:
            dlg.Destroy()
        for item in copyList:
            Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,item)
            backData = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,Id,'Background'))
            backData[0][1] = copy.copy(flag)
            bkDict = backData[-1]
            if bkDict['nDebye'] == backDict['nDebye']:
                for i,term in enumerate(bkDict['debyeTerms']):
                    term[1::2] = copy.copy(DBflags[i])
            if bkDict['nPeaks'] == backDict['nPeaks']:
                for i,term in enumerate(bkDict['peaksList']):
                    term[1::2] = copy.copy(PKflags[i])                    
            
    def OnBackCopy(event):
        hst = G2frame.GPXtree.GetItemText(G2frame.PatternId)
        histList = GetHistsLikeSelected(G2frame)
        if not histList:
            G2frame.ErrorDialog('No match','No histograms match '+hst,G2frame)
            return
        copyList = []
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Copy bkg params from\n'+str(hst[5:])+' to...',
            'Copy parameters', histList)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                for i in dlg.GetSelections():
                    copyList.append(histList[i])
        finally:
            dlg.Destroy()
        for item in copyList:
            Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,item)
            G2frame.GPXtree.SetItemPyData(
                G2gd.GetGPXtreeItemId(G2frame,Id,'Background'),copy.deepcopy(data))
            CalcBack(Id)
            
    def OnBackSave(event):
        pth = G2G.GetExportPath(G2frame)
        dlg = wx.FileDialog(G2frame, 'Set name to save GSAS-II background parameters file', pth, '', 
            'background parameter files (*.pwdrbck)|*.pwdrbck',wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                # make sure extension is .pwdrbck
                filename = os.path.splitext(filename)[0]+'.pwdrbck'
                File = open(filename,'w')
                File.write("#GSAS-II background parameter file; do not add/delete items!\n")
                File.write(str(data[0])+'\n')
                for item in data[1]:
                    if item in ['nPeaks','background PWDR','nDebye'] or not len(data[1][item]):
                        File.write(item+':'+str(data[1][item])+'\n')
                    else:
                        File.write(item+':\n')
                        for term in data[1][item]:
                            File.write(str(term)+'\n')
                File.close()
                print ('Background parameters saved to: '+filename)
        finally:
            dlg.Destroy()
        
    def OnBackLoad(event):
        pth = G2G.GetImportPath(G2frame)
        if not pth: pth = '.'
        dlg = wx.FileDialog(G2frame, 'Choose GSAS-II background parameters file', pth, '', 
            'background parameter files (*.pwdrbck)|*.pwdrbck',wx.FD_OPEN)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                newback = [[],{}]
                filename = dlg.GetPath()
                File = open(filename,'r')
                S = File.readline()
                if S[0] == '#':    #skip the heading
                    S = File.readline()     #should contain the std. bck fxn
                newback[0] = eval(S.strip())
                S = File.readline()                
                while S and ':' in S:
                    item,vals = S.strip().split(':')
                    if item in ['nPeaks','nDebye']:
                        newback[1][item] = int(vals)
                    elif 'PWDR' in item:
                        newback[1][item] = eval(vals)
                    elif item in ['FixedPoints','debyeTerms','peaksList']:
                        newback[1][item] = []
                        S = File.readline()
                        while S and ':' not in S:
                            newback[1][item].append(eval(S.strip()))
                            S = File.readline()
                        else:
                            continue
                    S = File.readline()                
                File.close()
                G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId,'Background'),newback)
        finally:
            dlg.Destroy()
        CalcBack(G2frame.PatternId)
        G2plt.PlotPatterns(G2frame,plotType='PWDR')
        wx.CallLater(100,UpdateBackground,G2frame,newback)

    def OnBkgFit(event):
        
        def SetInstParms(Inst):
            dataType = Inst['Type'][0]
            insVary = []
            insNames = []
            insVals = []
            for parm in Inst:
                insNames.append(parm)
                insVals.append(Inst[parm][1])
                if parm in ['U','V','W','X','Y','Z','SH/L','I(L2)/I(L1)','alpha',
                    'beta-0','beta-1','beta-q','sig-0','sig-1','sig-2','sig-q',] and Inst[parm][2]:
                        Inst[parm][2] = False
#                        insVary.append(parm)
            instDict = dict(zip(insNames,insVals))
            instDict['X'] = max(instDict['X'],0.01)
            instDict['Y'] = max(instDict['Y'],0.01)
            if 'SH/L' in instDict:
                instDict['SH/L'] = max(instDict['SH/L'],0.002)
            return dataType,instDict,insVary
    
        PatternId = G2frame.PatternId        
        controls = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.root, 'Controls'))
        background = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Background'))
        limits = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Limits'))[1]
        inst,inst2 = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Instrument Parameters'))
        # sort the points for convenience and then separate them; extend the range if needed
        if 'FixedPoints' not in background[1]:
            msg = ("You have not defined any fixed background points. "+
                    "Use the Fixed Points/Add menu item to define points that will be fit."+
                    '\n\nSee the "Fitting the Starting Background using Fixed Points" tutorial for more details.')
            print (msg)
            G2frame.ErrorDialog('No points',msg)
            return
        background[1]['FixedPoints'] = sorted(background[1]['FixedPoints'],key=lambda pair:pair[0])        
        X = [x for x,y in background[1]['FixedPoints']]
        Y = [y for x,y in background[1]['FixedPoints']]
        if X[0] > limits[0]:
            X = [limits[0]] + X
            Y = [Y[0]] + Y
        if X[-1] < limits[1]:
            X += [limits[1]]
            Y += [Y[-1]]
        # interpolate the fixed points onto the grid of data points within limits
        pwddata = G2frame.GPXtree.GetItemPyData(PatternId)[1]
        xBeg = np.searchsorted(pwddata[0],limits[0])
        xFin = np.searchsorted(pwddata[0],limits[1])
        xdata = pwddata[0][xBeg:xFin]
        ydata = si.interp1d(X,Y)(ma.getdata(xdata))
        W = [1]*len(xdata)
        Z = [0]*len(xdata)

        # load instrument and background params
        print (' NB: Any instrument parameter refinement flags will be cleared')
        dataType,insDict,insVary = SetInstParms(inst)
        bakType,bakDict,bakVary = G2pwd.SetBackgroundParms(background)
        # how many background parameters are refined?
        if len(bakVary)*1.5 > len(X):
            msg = ("You are attempting to vary "+str(len(bakVary))+
                   " background terms with only "+str(len(X))+" background points"+
                    "\nAdd more points or reduce the number of terms")
            print (msg)
            G2frame.ErrorDialog('Too few points',msg)
            return
        
        wx.BeginBusyCursor()
        try:
            G2pwd.DoPeakFit('LSQ',[],background,limits,inst,inst2,
                np.array((xdata,ydata,W,Z,Z,Z)),Z,prevVaryList=bakVary,controls=controls)
        finally:
            wx.EndBusyCursor()
        # compute the background values and plot them
        parmDict = {}
        bakType,bakDict,bakVary = G2pwd.SetBackgroundParms(background)
        parmDict.update(bakDict)
        parmDict.update(insDict)
        # Note that this generates a MaskedArrayFutureWarning, but these items are not always masked
        pwddata[3][xBeg:xFin] *= 0.
        pwddata[5][xBeg:xFin] *= 0.
        pwddata[4][xBeg:xFin] = G2pwd.getBackground('',parmDict,bakType,dataType,xdata)[0]
        G2plt.PlotPatterns(G2frame,plotType='PWDR')
        # show the updated background values
        wx.CallLater(100,UpdateBackground,G2frame,data)
        
    def OnBkgClear(event):
        if 'FixedPoints' not in data[1]:
            return
        else:
            data[1]['FixedPoints'] = []
            G2plt.PlotPatterns(G2frame,plotType='PWDR')
    
    def OnPeaksMove(event):
        if not data[1]['nPeaks']:
            G2frame.ErrorDialog('Error','No peaks to move')
            return
        Peaks = {'peaks':[],'sigDict':{}}
        for peak in data[1]['peaksList']:
            Peaks['peaks'].append([peak[0],0,peak[2],0,peak[4],0,peak[6],0])
        G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Peak List'),Peaks)
        
    def OnMakeRDF(event):
        dlg = RDFDialog(G2frame)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                RDFcontrols = dlg.GetSelection()
            else:
                return
        finally:
            dlg.Destroy()
        PatternId = G2frame.PatternId        
        background = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Background'))
        inst,inst2 = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Instrument Parameters'))
        pwddata = G2frame.GPXtree.GetItemPyData(PatternId)[1]
        auxPlot = G2pwd.MakeRDF(RDFcontrols,background,inst,pwddata)
        if '2' in platform.python_version_tuple()[0]:
            superMinusOne = unichr(0xaf)+unichr(0xb9)
        else:
            superMinusOne = chr(0xaf)+chr(0xb9)
        for plot in auxPlot:
            XY = np.array(plot[:2])
            if 'D(R)' in plot[2]:
                xlabel = r'$R, \AA$'
                ylabel = r'$D(R), arb. units$'
            else:
                xlabel = r'$Q,\AA$'+superMinusOne
                ylabel = r'$I(Q)$'
            G2plt.PlotXY(G2frame,[XY,],Title=plot[2],labelX=xlabel,labelY=ylabel,lines=True)      
        
    def BackSizer():
        
        def OnNewType(event):
            data[0][0] = bakType.GetValue()
            
        def OnBakRef(event):
            data[0][1] = bakRef.GetValue()
            
        def OnBakTerms(event):
            data[0][2] = int(bakTerms.GetValue())
            M = len(data[0])
            N = data[0][2]+3
            item = data[0]
            if N > M:       #add terms
                for i in range(M,N): 
                    item.append(0.0)
            elif N < M:     #delete terms
                for i in range(N,M):
                    del(item[-1])
            G2frame.GPXtree.SetItemPyData(BackId,data)
            wx.CallLater(100,UpdateBackground,G2frame,data)
            
        def AfterChange(invalid,value,tc):
            if invalid: return
            CalcBack(G2frame.PatternId)
            G2plt.PlotPatterns(G2frame,plotType='PWDR')
            
        backSizer = wx.BoxSizer(wx.VERTICAL)
        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        topSizer.Add(wx.StaticText(G2frame.dataWindow,-1,' Background function: '),0,WACV)
        bakType = wx.ComboBox(G2frame.dataWindow,value=data[0][0],
                choices=Choices,style=wx.CB_READONLY|wx.CB_DROPDOWN)
        bakType.Bind(wx.EVT_COMBOBOX, OnNewType)
        topSizer.Add(bakType)
        topSizer.Add((5,0),0)
        bakRef = wx.CheckBox(G2frame.dataWindow,label=' Refine?')
        bakRef.SetValue(bool(data[0][1]))
        bakRef.Bind(wx.EVT_CHECKBOX, OnBakRef)
        topSizer.Add(bakRef,0,WACV)
        backSizer.Add(topSizer)
        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        topSizer.Add(wx.StaticText(G2frame.dataWindow,-1,' Number of coeff.: '),0,WACV)
        bakTerms = wx.ComboBox(G2frame.dataWindow,-1,value=str(data[0][2]),choices=[str(i+1) for i in range(36)],
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        bakTerms.Bind(wx.EVT_COMBOBOX,OnBakTerms)
        topSizer.Add(bakTerms,0,WACV)
        topSizer.Add((5,0),0)
        backSizer.Add(topSizer)
        backSizer.Add(wx.StaticText(G2frame.dataWindow,-1,' Background coefficients:'),0)
        bakSizer = wx.FlexGridSizer(0,5,5,5)
        for i,value in enumerate(data[0][3:]):
            bakVal = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data[0],i+3,nDig=(10,4),OnLeave=AfterChange)
            bakSizer.Add(bakVal,0,WACV)
        backSizer.Add(bakSizer)
        return backSizer
        
    def DebyeSizer():
        
        def OnDebTerms(event):
            data[1]['nDebye'] = int(debTerms.GetValue())
            M = len(data[1]['debyeTerms'])
            N = data[1]['nDebye']
            if N > M:       #add terms
                for i in range(M,N): 
                    data[1]['debyeTerms'].append([1.0,False,1.0,False,0.010,False])
            elif N < M:     #delete terms
                for i in range(N,M):
                    del(data[1]['debyeTerms'][-1])
            if N == 0:
                CalcBack(G2frame.PatternId)
                G2plt.PlotPatterns(G2frame,plotType='PWDR')                
            wx.CallAfter(UpdateBackground,G2frame,data)

        def KeyEditPeakGrid(event):
            colList = debyeGrid.GetSelectedCols()
            if event.GetKeyCode() == wx.WXK_RETURN:
                event.Skip(True)
            elif event.GetKeyCode() == wx.WXK_CONTROL:
                event.Skip(True)
            elif event.GetKeyCode() == wx.WXK_SHIFT:
                event.Skip(True)
            elif colList:
                debyeGrid.ClearSelection()
                key = event.GetKeyCode()
                for col in colList:
                    if debyeTable.GetTypeName(0,col) == wg.GRID_VALUE_BOOL:
                        if key == 89: #'Y'
                            for row in range(debyeGrid.GetNumberRows()): data[1]['debyeTerms'][row][col]=True
                        elif key == 78:  #'N'
                            for row in range(debyeGrid.GetNumberRows()): data[1]['debyeTerms'][row][col]=False
        
        def OnCellChange(event):
            CalcBack(G2frame.PatternId)
            G2plt.PlotPatterns(G2frame,plotType='PWDR')                

        debSizer = wx.BoxSizer(wx.VERTICAL)
        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        topSizer.Add(wx.StaticText(G2frame.dataWindow,-1,' Debye scattering: '),0,WACV)
        topSizer.Add(wx.StaticText(G2frame.dataWindow,-1,' Number of terms: '),0,WACV)
        debTerms = wx.ComboBox(G2frame.dataWindow,-1,value=str(data[1]['nDebye']),choices=[str(i) for i in range(21)],
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        debTerms.Bind(wx.EVT_COMBOBOX,OnDebTerms)
        topSizer.Add(debTerms,0,WACV)
        topSizer.Add((5,0),0)
        debSizer.Add(topSizer)
        if data[1]['nDebye']:
            debSizer.Add(wx.StaticText(G2frame.dataWindow,-1,' Debye diffuse terms:'),0)       
            rowLabels = []
            for i in range(len(data[1]['debyeTerms'])): rowLabels.append(str(i))
            colLabels = ['A','refine','R','refine','U','refine']
            Types = [wg.GRID_VALUE_FLOAT+':10,2',wg.GRID_VALUE_BOOL,
            wg.GRID_VALUE_FLOAT+':10,3',wg.GRID_VALUE_BOOL,
            wg.GRID_VALUE_FLOAT+':10,5',wg.GRID_VALUE_BOOL]
            debyeTable = G2G.Table(data[1]['debyeTerms'],rowLabels=rowLabels,colLabels=colLabels,types=Types)
            debyeGrid = G2G.GSGrid(parent=G2frame.dataWindow)
            debyeGrid.SetTable(debyeTable, True)
            debyeGrid.Bind(wx.EVT_KEY_DOWN, KeyEditPeakGrid)
            debyeGrid.Bind(wg.EVT_GRID_CELL_CHANGED,OnCellChange)
            debyeGrid.AutoSizeColumns(False)
            debSizer.Add(debyeGrid)        
        return debSizer
      
    def PeaksSizer():

        def OnPeaks(event):
            'Respond to a change in the number of background peaks'
            data[1]['nPeaks'] = int(peaks.GetValue())
            M = len(data[1]['peaksList'])
            N = data[1]['nPeaks']
            if N > M:       #add terms
                for i in range(M,N): 
                    data[1]['peaksList'].append([1.0,False,1.0,False,0.10,False,0.10,False])
            elif N < M:     #delete terms
                for i in range(N,M):
                    del(data[1]['peaksList'][-1])
            if N == 0:
                CalcBack(G2frame.PatternId)
                G2plt.PlotPatterns(G2frame,plotType='PWDR')
            # this callback is crashing wx when there is an open
            # peaksGrid cell editor, at least on Mac. Code below
            # should fix this, but it does not.
            # https://stackoverflow.com/questions/64082199/wxpython-grid-destroy-with-open-celleditor-crashes-python-even-with-disablece
            if peaksGrid and peaksGrid.IsCellEditControlEnabled():
                # complete any grid edits in progress
                #print('closing')
                peaksGrid.HideCellEditControl()
                peaksGrid.DisableCellEditControl()
                #wx.CallLater(100,peaksGrid.Destroy) # crashes python
            wx.CallAfter(UpdateBackground,G2frame,data)
            
        def KeyEditPeakGrid(event):
            colList = peaksGrid.GetSelectedCols()
            if event.GetKeyCode() == wx.WXK_RETURN:
                event.Skip(True)
            elif event.GetKeyCode() == wx.WXK_CONTROL:
                event.Skip(True)
            elif event.GetKeyCode() == wx.WXK_SHIFT:
                event.Skip(True)
            elif colList:
                peaksGrid.ClearSelection()
                key = event.GetKeyCode()
                for col in colList:
                    if peaksTable.GetTypeName(0,col) == wg.GRID_VALUE_BOOL:
                        if key == 89: #'Y'
                            for row in range(peaksGrid.GetNumberRows()): data[1]['peaksList'][row][col]=True
                        elif key == 78:  #'N'
                            for row in range(peaksGrid.GetNumberRows()): data[1]['peaksList'][row][col]=False
                            
        def OnCellChange(event):
            CalcBack(G2frame.PatternId)
            G2plt.PlotPatterns(G2frame,plotType='PWDR')                

        peaksSizer = wx.BoxSizer(wx.VERTICAL)
        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        topSizer.Add(wx.StaticText(G2frame.dataWindow,-1,' Peaks in background: '),0,WACV)
        topSizer.Add(wx.StaticText(G2frame.dataWindow,-1,' Number of peaks: '),0,WACV)
        peaks = wx.ComboBox(G2frame.dataWindow,-1,value=str(data[1]['nPeaks']),choices=[str(i) for i in range(30)],
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        peaks.Bind(wx.EVT_COMBOBOX,OnPeaks)
        topSizer.Add(peaks,0,WACV)
        topSizer.Add((5,0),0)
        peaksSizer.Add(topSizer)
        G2frame.dataWindow.currentGrids = []
        peaksGrid = None
        if data[1]['nPeaks']:
            peaksSizer.Add(wx.StaticText(G2frame.dataWindow,-1,' Peak list:'),0)       
            rowLabels = []
            for i in range(len(data[1]['peaksList'])): rowLabels.append(str(i))
            colLabels = ['pos','refine','int','refine','sig','refine','gam','refine']
            Types = [wg.GRID_VALUE_FLOAT+':10,2',wg.GRID_VALUE_BOOL,
            wg.GRID_VALUE_FLOAT+':10,3',wg.GRID_VALUE_BOOL,
            wg.GRID_VALUE_FLOAT+':10,3',wg.GRID_VALUE_BOOL,
            wg.GRID_VALUE_FLOAT+':10,5',wg.GRID_VALUE_BOOL]
            peaksTable = G2G.Table(data[1]['peaksList'],rowLabels=rowLabels,colLabels=colLabels,types=Types)
            peaksGrid = G2G.GSGrid(parent=G2frame.dataWindow)
            peaksGrid.SetTable(peaksTable, True)
            peaksGrid.Bind(wx.EVT_KEY_DOWN, KeyEditPeakGrid)
            peaksGrid.Bind(wg.EVT_GRID_CELL_CHANGED,OnCellChange)
            peaksGrid.AutoSizeColumns(False)
            peaksSizer.Add(peaksGrid)        
        return peaksSizer
    
    def BackFileSizer():
        
        def OnBackPWDR(event):
            data[1]['background PWDR'][0] = back.GetValue()
            if  data[1]['background PWDR'][0]:
                curHist = G2frame.GPXtree.GetItemPyData(G2frame.PatternId)
                Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,data[1]['background PWDR'][0])
                if not Id:
                    G2G.G2MessageBox(G2frame,'Histogram not found -- how did this happen?','Missing histogram')
                    back.SetValue('')
                    data[1]['background PWDR'][0] = back.GetValue()
                    return
                bkgHist = G2frame.GPXtree.GetItemPyData(Id)
                if len(bkgHist[1][0]) != len(curHist[1][0]):
                    G2G.G2MessageBox(G2frame,'Histogram have different lengths','Mismatched histograms')
                    back.SetValue('')
                    data[1]['background PWDR'][0] = back.GetValue()
                    return
            CalcBack()
            G2plt.PlotPatterns(G2frame,plotType='PWDR')
        
        def AfterChange(invalid,value,tc):
            if invalid: return
            CalcBack()
            G2plt.PlotPatterns(G2frame,plotType='PWDR')

        fileSizer = wx.BoxSizer(wx.VERTICAL)
        fileSizer.Add(wx.StaticText(G2frame.dataWindow,-1,' Fixed background file:'),0)
        if 'background PWDR' not in data[1]:
            data[1]['background PWDR'] = ['',-1.,False]
        backSizer = wx.BoxSizer(wx.HORIZONTAL)
        Choices = ['',]+G2gd.GetGPXtreeDataNames(G2frame,['PWDR',])
        Source = G2frame.GPXtree.GetItemText(G2frame.PatternId)
        Choices.pop(Choices.index(Source))
        back = wx.ComboBox(parent=G2frame.dataWindow,value=data[1]['background PWDR'][0],choices=Choices,
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        back.Bind(wx.EVT_COMBOBOX,OnBackPWDR)
        backSizer.Add(back)
        backSizer.Add(wx.StaticText(G2frame.dataWindow,-1,' multiplier'),0,WACV)
        backMult = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data[1]['background PWDR'],1,nDig=(10,3),OnLeave=AfterChange)
        backSizer.Add(backMult,0,WACV)
        fileSizer.Add(backSizer)
        return fileSizer
    
    def CalcBack(PatternId=G2frame.PatternId):
            limits = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Limits'))[1]
            inst,inst2 = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Instrument Parameters'))
            backData = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Background'))
            dataType = inst['Type'][0]
            insDict = {inskey:inst[inskey][1] for inskey in inst}
            parmDict = {}
            bakType,bakDict,bakVary = G2pwd.SetBackgroundParms(data)
            parmDict.update(bakDict)
            parmDict.update(insDict)
            pwddata = G2frame.GPXtree.GetItemPyData(PatternId)
            xBeg = np.searchsorted(pwddata[1][0],limits[0])
            xFin = np.searchsorted(pwddata[1][0],limits[1])
            fixBack = backData[1]['background PWDR']
            try:    #typically bad grid value or no fixed bkg file
                Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,fixBack[0])
                fixData = G2frame.GPXtree.GetItemPyData(Id)
                fixedBkg = {'_fixedVary':False,'_fixedMult':fixBack[1],'_fixedValues':fixData[1][1][xBeg:xFin]} 
                pwddata[1][4][xBeg:xFin] = G2pwd.getBackground('',parmDict,bakType,dataType,pwddata[1][0][xBeg:xFin],fixedBkg)[0]
            except:
                pass

    # UpdateBackground execution starts here    
    if len(data) < 2:       #add Debye diffuse & peaks scattering here
        data.append({'nDebye':0,'debyeTerms':[],'nPeaks':0,'peaksList':[]})
    if 'nPeaks' not in data[1]:
        data[1].update({'nPeaks':0,'peaksList':[]})
    G2frame.dataWindow.currentGrids = []
    G2gd.SetDataMenuBar(G2frame,G2frame.dataWindow.BackMenu)
    G2frame.Bind(wx.EVT_MENU,OnBackCopy,id=G2G.wxID_BACKCOPY)
    G2frame.Bind(wx.EVT_MENU,OnBackFlagCopy,id=G2G.wxID_BACKFLAGCOPY)
    G2frame.Bind(wx.EVT_MENU,OnBackSave,id=G2G.wxID_BACKSAVE)
    G2frame.Bind(wx.EVT_MENU,OnBackLoad,id=G2G.wxID_BACKLOAD)
    G2frame.Bind(wx.EVT_MENU,OnPeaksMove,id=G2G.wxID_BACKPEAKSMOVE)
    G2frame.Bind(wx.EVT_MENU,OnMakeRDF,id=G2G.wxID_MAKEBACKRDF)
    G2frame.Bind(wx.EVT_MENU,OnBkgFit,id=G2frame.dataWindow.wxID_BackPts['Fit'])
    G2frame.Bind(wx.EVT_MENU,OnBkgClear,id=G2frame.dataWindow.wxID_BackPts['Clear'])    
    BackId = G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Background')
    Choices = ['chebyschev','chebyschev-1','cosine','Q^2 power series','Q^-2 power series','lin interpolate','inv interpolate','log interpolate']
    G2frame.dataWindow.ClearData()
    mainSizer = G2frame.dataWindow.GetSizer()
    mainSizer.Add(BackSizer())
    mainSizer.Add((0,5),0)
    mainSizer.Add(DebyeSizer())
    mainSizer.Add((0,5),0)
    mainSizer.Add(PeaksSizer())
    mainSizer.Add((0,5),0)
    mainSizer.Add(BackFileSizer())
    G2frame.dataWindow.SetDataSize()
        
################################################################################
#####  Limits
################################################################################           
       
def UpdateLimitsGrid(G2frame, data,plottype):
    '''respond to selection of PWDR Limits data tree item.
    '''
    def AfterChange(invalid,value,tc):
        if invalid: return
        plottype = G2frame.GPXtree.GetItemText(G2frame.PatternId)[:4]
        wx.CallAfter(G2plt.PlotPatterns,G2frame,newPlot=False,plotType=plottype)  #unfortunately this resets the plot width

    def LimitSizer():
        limits = wx.FlexGridSizer(0,3,0,5)
        labels = ['Tmin','Tmax']
        for i in [0,1]:
            limits.Add(wx.StaticText(G2frame.dataWindow,
                label=' Original {} {:.4f}'.format(labels[i],data[0][i])),0,WACV)
            limits.Add(wx.StaticText(G2frame.dataWindow,label=' New: '),0,WACV)
            limits.Add(G2G.ValidatedTxtCtrl(G2frame.dataWindow,data[1],i,  \
                xmin=data[0][0],xmax=data[0][1],nDig=(10,4),typeHint=float,OnLeave=AfterChange))
        return limits
        
    def ExclSizer():
        
        def OnDelExcl(event):
            Obj = event.GetEventObject()
            item = Indx[Obj.GetId()]
            del(data[item+2])
            G2plt.PlotPatterns(G2frame,newPlot=False,plotType=plottype)
            wx.CallAfter(UpdateLimitsGrid,G2frame,data,plottype)
        
        Indx = {}
        excl = wx.FlexGridSizer(0,3,0,5)
        excl.Add(wx.StaticText(G2frame.dataWindow,label=' From: '),0,WACV)
        excl.Add(wx.StaticText(G2frame.dataWindow,label=' To: '),0,WACV)
        excl.Add(wx.StaticText(G2frame.dataWindow,label=' Delete?: '),0,WACV)
        for Id,item in enumerate(data[2:]):
            for i in [0,1]:
                excl.Add(G2G.ValidatedTxtCtrl(G2frame.dataWindow,item,i,  \
                    xmin=data[0][0],xmax=data[0][1],nDig=(10,4),typeHint=float,OnLeave=AfterChange))
            delExcl = wx.CheckBox(G2frame.dataWindow,label='')
            Indx[delExcl.GetId()] = Id
            delExcl.Bind(wx.EVT_CHECKBOX,OnDelExcl)
            excl.Add(delExcl,0,WACV)
        return excl
               
    def OnAddExcl(event):
        G2frame.ifGetExclude = True
        G2frame.plotFrame.Raise()
        G2G.G2MessageBox(G2frame.plotFrame,'Click on a point in the pattern to be excluded, then drag or edit limits to adjust range','Creating excluded region')
        
    def OnLimitCopy(event):
        hst = G2frame.GPXtree.GetItemText(G2frame.PatternId)
        histList = GetHistsLikeSelected(G2frame)
        if not histList:
            G2frame.ErrorDialog('No match','No histograms match '+hst,G2frame)
            return
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Copy limits from\n'+str(hst[5:])+' to...',
            'Copy limits', histList)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                for i in dlg.GetSelections(): 
                    item = histList[i]
                    Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,item)
                    G2frame.GPXtree.SetItemPyData(
                        G2gd.GetGPXtreeItemId(G2frame,Id,'Limits'),copy.deepcopy(data))
        finally:
            dlg.Destroy()
            
    def Draw():
        G2frame.dataWindow.ClearData()
        mainSizer = G2frame.dataWindow.GetSizer()
        mainSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Data used in refinement'),0,WACV)
        mainSizer.Add((5,5))
        mainSizer.Add(LimitSizer())
        if len(data)>2:
            mainSizer.Add((0,5),0)
            mainSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Excluded regions:'),0,WACV)
            mainSizer.Add(ExclSizer())
        G2frame.dataWindow.SetDataSize()

    G2frame.ifGetExclude = False
    G2gd.SetDataMenuBar(G2frame,G2frame.dataWindow.LimitMenu)
    #G2frame.SetLabel(G2frame.GetLabel().split('||')[0]+' || '+'Limits')
    G2frame.Bind(wx.EVT_MENU,OnLimitCopy,id=G2G.wxID_LIMITCOPY)
    G2frame.Bind(wx.EVT_MENU,OnAddExcl,id=G2G.wxID_ADDEXCLREGION)
    Draw() 
    
################################################################################
#####  Instrument parameters
################################################################################           
       
def UpdateInstrumentGrid(G2frame,data):
    '''respond to selection of PWDR/SASD/REFD Instrument Parameters
    data tree item.
    '''
    if 'Bank' not in data:  #get it from name; absent for default parms selection 
        hst = G2frame.GPXtree.GetItemText(G2frame.PatternId)
        if 'Bank' in hst:
            bank = int(hst.split('Bank')[1].split('_')[0])
            data['Bank'] = [bank,bank,0]
        else:
            data['Bank'] = [1,1,0]

    def keycheck(keys):
        good = []
        for key in keys:
            if key in ['Type','Bank','U','V','W','X','Y','Z','SH/L','I(L2)/I(L1)','alpha',
                'beta-0','beta-1','beta-q','sig-0','sig-1','sig-2','sig-q','Polariz.','alpha-0','alpha-1',
                'Lam','Azimuth','2-theta','fltPath','difC','difA','difB','Zero','Lam1','Lam2']:
                good.append(key)
        return good
        
    def updateData(inst,ref):
        data = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,
            G2frame.PatternId,'Instrument Parameters'))[0]
        for item in data:
            try:
                data[item] = [data[item][0],inst[item],ref[item]]
            except KeyError:
                try:
                    data[item] = [data[item][0],inst[item]]
                except KeyError:
                    pass        #skip 'Polariz.' for N-data
    
    def RefreshInstrumentGrid(event,doAnyway=False):
        if doAnyway or event.GetRow() == 1:
            peaks = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Peak List'))
            newpeaks = []
            for peak in peaks['peaks']:
                newpeaks.append(G2mth.setPeakparms(data,Inst2,peak[0],peak[2]))
            peaks['peaks'] = newpeaks
            G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Peak List'),peaks)
            
    def OnCalibrate(event):
        Pattern = G2frame.GPXtree.GetItemPyData(G2frame.PatternId)
        xye = ma.array(ma.getdata(Pattern[1]))
        cw = np.diff(xye[0])
        IndexPeaks = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Index Peak List'))
        if not len(IndexPeaks[0]):
            G2frame.ErrorDialog('Can not calibrate','Index Peak List empty')
            return
        if not np.any(IndexPeaks[1]):
            G2frame.ErrorDialog('Can not calibrate','Peak positions not refined')
            return False
        Ok = False
        for peak in IndexPeaks[0]:
            if peak[2] and peak[3]:
                Ok = True
        if not Ok:
            G2frame.ErrorDialog('Can not calibrate','Index Peak List not indexed')
            return            
        if G2pwd.DoCalibInst(IndexPeaks,data):
            UpdateInstrumentGrid(G2frame,data)
            XY = []
            Sigs = []
            for ip,peak in enumerate(IndexPeaks[0]):
                if peak[2] and peak[3]:
                    binwid = cw[np.searchsorted(xye[0],peak[0])]
                    XY.append([peak[-1],peak[0],binwid])
                    Sigs.append(IndexPeaks[1][ip])
            if len(XY):
                XY = np.array(XY)
                G2plt.PlotCalib(G2frame,data,XY,Sigs,newPlot=True)
        else:
            G2frame.ErrorDialog('Can not calibrate','Nothing selected for refinement')

    def OnLoad(event):
        '''Loads instrument parameters from a G2 .instprm file
        in response to the Instrument Parameters-Operations/Load Profile menu
        If instprm file has multiple banks each with header #Bank n: ..., this 
        finds matching bank no. to load - rejects nonmatches.
        
        Note that similar code is found in ReadPowderInstprm (GSASIIdataGUI.py)
        '''
        
        def GetDefaultParms(rd):
            '''Solicits from user a default set of parameters & returns Inst parm dict
            param: self: refers to the GSASII main class
            param: rd: importer data structure
            returns: dict: Instrument parameter dictionary
            '''       
            import defaultIparms as dI
            sind = lambda x: math.sin(x*math.pi/180.)
            tand = lambda x: math.tan(x*math.pi/180.)
            while True: # loop until we get a choice
                choices = []
                head = 'Select from default instrument parameters'
    
                for l in dI.defaultIparm_lbl:
                    choices.append('Defaults for '+l)
                res = G2G.BlockSelector(choices,ParentFrame=G2frame,title=head,
                    header='Select default inst parms',useCancel=True)
                if res is None: return None
                if 'Generic' in choices[res]:
                    dlg = G2G.MultiDataDialog(G2frame,title='Generic TOF detector bank',
                        prompts=['Total FP','2-theta',],values=[25.0,150.,],
                            limits=[[6.,200.],[5.,175.],],formats=['%6.2f','%6.1f',])
                    if dlg.ShowModal() == wx.ID_OK: #strictly empirical approx.
                        FP,tth = dlg.GetValues()
                        difC = 505.632*FP*sind(tth/2.)
                        sig1 = 50.+2.5e-6*(difC/tand(tth/2.))**2
                        bet1 = .00226+7.76e+11/difC**4
                        Inst = G2frame.ReadPowderInstprm(dI.defaultIparms[res],bank,1,rd)
                        Inst[0]['difC'] = [difC,difC,0]
                        Inst[0]['sig-1'] = [sig1,sig1,0]
                        Inst[0]['beta-1'] = [bet1,bet1,0]
                        return Inst    #this is [Inst1,Inst2] a pair of dicts
                    dlg.Destroy()
                else:
                    inst1,inst2 = G2frame.ReadPowderInstprm(dI.defaultIparms[res],bank,1,rd)
                    return [inst1,inst2]
                if 'lab data' in choices[res]:
                    rd.Sample.update({'Type':'Bragg-Brentano','Shift':[0.,False],'Transparency':[0.,False],
                        'SurfRoughA':[0.,False],'SurfRoughB':[0.,False]})
                else:
                    rd.Sample.update({'Type':'Debye-Scherrer','Absorption':[0.,False],'DisplaceX':[0.,False],
                        'DisplaceY':[0.,False]})
        
        data = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,
            G2frame.PatternId,'Instrument Parameters'))[0]
        bank = data['Bank'][0]
        pth = G2G.GetImportPath(G2frame)
        if not pth: pth = '.'
        dlg = wx.FileDialog(G2frame, 'Choose GSAS-II instrument parameters file', pth, '', 
            'instrument parameter files (*.instprm)|*.instprm',wx.FD_OPEN)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                File = open(filename,'r')
                S = File.readline()
                newItems = []
                newVals = []
                Found = False
                while S:
                    if S[0] == '#':
                        if Found:
                            break
                        if 'Bank' in S:
                            if bank == int(S.split(':')[0].split()[1]):
                                S = File.readline()
                                continue
                            else:
                                S = File.readline()
                                while S and '#Bank' not in S:
                                    S = File.readline()
                                continue
                        else:   #a non #Bank file
                            S = File.readline()
                            continue
                    Found = True
                    [item,val] = S[:-1].split(':')
                    newItems.append(item)
                    try:
                        newVals.append(float(val))
                    except ValueError:
                        newVals.append(val)                        
                    S = File.readline()                
                File.close()
                if Found:
                    Inst,Inst2 = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId,'Instrument Parameters'))
                    if 'Bank' not in Inst:  #patch for old .instprm files - may cause faults for TOF data
                        Inst['Bank'] = [1,1,0]
                    data = G2fil.makeInstDict(newItems,newVals,len(newVals)*[False,])
                    G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId,'Instrument Parameters'),[data,Inst2])
                    RefreshInstrumentGrid(event,doAnyway=True)          #to get peaks updated
                    UpdateInstrumentGrid(G2frame,data)
                else:
                    G2frame.ErrorDialog('No match','Bank %d not in %s'%(bank,filename),G2frame)
            else:
                rd = G2obj.ImportPowderData('Dummy')
                rd.Sample = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId,'Sample Parameters'))
                try:
                    data = GetDefaultParms(rd)[0]
                except TypeError:   #Cancel - got None 
                    pass
                UpdateInstrumentGrid(G2frame,data)
            G2plt.PlotPeakWidths(G2frame)
        finally:
            dlg.Destroy()
        
    def OnSave(event):
        '''Respond to the Instrument Parameters Operations/Save Profile menu
        item: writes current parameters to a .instprm file
        It does not write Bank n: on # line & thus can be used any time w/o clash of bank nos.
        '''
        pth = G2G.GetExportPath(G2frame)
        dlg = wx.FileDialog(G2frame, 'Set name to save GSAS-II instrument parameters file', pth, '', 
            'instrument parameter files (*.instprm)|*.instprm',wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                # make sure extension is .instprm
                filename = os.path.splitext(filename)[0]+'.instprm'
                File = open(filename,'w')
                File.write("#GSAS-II instrument parameter file; do not add/delete items!\n")
                for item in data:
                    File.write(item+':'+str(data[item][1])+'\n')
                File.close()
                print ('Instrument parameters saved to: '+filename)
        finally:
            dlg.Destroy()
            
    def OnSaveAll(event):
        '''Respond to the Instrument Parameters Operations/Save all Profile menu & writes 
        selected inst parms. across multiple banks into a single file
        Each block starts with #Bank n: GSAS-II instrument... where n is bank no.
        item: writes parameters from selected PWDR entries to a .instprm file
        '''
        hst = G2frame.GPXtree.GetItemText(G2frame.PatternId)
        histList = GetHistsLikeSelected(G2frame)
        histList.insert(0,hst)
        saveList = []
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Save instrument parameters from',
            'Save instrument parameters', histList)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                for i in dlg.GetSelections():
                    saveList.append(histList[i])
        finally:
            dlg.Destroy()
        pth = G2G.GetExportPath(G2frame)
        dlg = wx.FileDialog(G2frame, 'Choose GSAS-II instrument parameters file', pth, '', 
            'instrument parameter files (*.instprm)|*.instprm',wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                # make sure extension is .instprm
                filename = os.path.splitext(filename)[0]+'.instprm'
                File = open(filename,'w')
                for hist in saveList:
                    Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,hist)
                    inst = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,Id,'Instrument Parameters'))[0]
                    if 'Bank' not in inst:  #patch
                        bank = 1
                        if 'Bank' in hist:
                            bank = int(hist.split('Bank')[1])
                        inst['Bank'] = [bank,bank,0]
                    bank = inst['Bank'][0]                
                    File.write("#Bank %d: GSAS-II instrument parameter file; do not add/delete items!\n"%(bank))
                    for item in inst:
                        File.write(item+':'+str(inst[item][1])+'\n')                                    
                File.close()
        finally:
            dlg.Destroy()
                                                
    def OnReset(event):
        insVal.update(insDef)
        updateData(insVal,insRef)
        RefreshInstrumentGrid(event,doAnyway=True)          #to get peaks updated
        UpdateInstrumentGrid(G2frame,data)
        G2plt.PlotPeakWidths(G2frame)
        
    def OnInstFlagCopy(event):
        hst = G2frame.GPXtree.GetItemText(G2frame.PatternId)
        histList = GetHistsLikeSelected(G2frame)
        if not histList:
            G2frame.ErrorDialog('No match','No histograms match '+hst,G2frame)
            return
        keys = list(data.keys())
        try:
            keys.remove('Source')
        except ValueError:
            pass
        flags = dict(zip(keys,[data[key][2] for key in keys]))
        instType = data['Type'][0]
        copyList = []
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Copy inst ref. flags from\n'+hst[5:],
            'Copy refinement flags', histList)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                for i in dlg.GetSelections():
                    copyList.append(histList[i])
        finally:
            dlg.Destroy()
        for item in copyList:
            Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,item)
            instData = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,Id,'Instrument Parameters'))[0]
            if 'Bank' not in instData:
                instData['Bank'] = [1,1,0]
            if len(data) == len(instData) and instType == instData['Type'][0]:   #don't mix data types or lam & lam1/lam2 parms!
                for item in instData:
                    if item not in ['Source',]:
                        instData[item][2] = copy.copy(flags[item])
            else:
                print (item+' not copied - instrument parameters not commensurate')
        
    def OnInstCopy(event):
        #need fix for dictionary
        hst = G2frame.GPXtree.GetItemText(G2frame.PatternId)
        histList = GetHistsLikeSelected(G2frame)
        if not histList:
            G2frame.ErrorDialog('No match','No histograms match '+hst,G2frame)
            return
        copyList = []
        copyData = copy.deepcopy(data)
        del copyData['Azimuth'] #not to be copied!
        instType = data['Type'][0]
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Copy inst params from\n'+hst,
            'Copy parameters', histList)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                for i in dlg.GetSelections(): 
                    copyList.append(histList[i])
        finally:
            dlg.Destroy()
        for item in copyList:
            Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,item)
            instData = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,Id,'Instrument Parameters'))[0]
            if 'Bank' not in instData:
                instData['Bank'] = [1,1,0]
            if len(data) == len(instData) and instType == instData['Type'][0]:  #don't mix data types or lam & lam1/lam2 parms!
                instData.update(copyData)
            else:
                print (item+' not copied - instrument parameters not commensurate')
                         
    def AfterChange(invalid,value,tc):
        if invalid: return
        updateData(insVal,insRef)
        
    def NewProfile(invalid,value,tc):
        if invalid: return
        updateData(insVal,insRef)
        G2plt.PlotPeakWidths(G2frame)
        
    def OnItemRef(event):
        Obj = event.GetEventObject()
        item = RefObj[Obj.GetId()]
        insRef[item] = Obj.GetValue()
        updateData(insVal,insRef)

    def OnCopy1Val(event):
        '''Select one instrument parameter value to edit and copy to many histograms
        optionally allow values to be edited in a table
        '''
        updateData(insVal,insRef)
        G2G.SelectEdit1Var(G2frame,data,labelLst,elemKeysLst,dspLst,refFlgElem)
        insVal.update({key:data[key][1] for key in instkeys})
        insRef.update({key:data[key][2] for key in instkeys})
        wx.CallAfter(MakeParameterWindow)
        
    def lblWdef(lbl,dec,val):
        'Label parameter showing the default value'
        fmt = "%15."+str(dec)+"f"
        return " " + lbl + " (" + (fmt % val).strip() + "): "

    def RefineBox(item):
        'Define a refine checkbox with binding'
        #wid = wx.CheckBox(G2frame.dataWindow,label=' Refine?  ')
        wid = wx.CheckBox(G2frame.dataWindow,label='')
        wid.SetValue(bool(insRef[item]))
        RefObj[wid.GetId()] = item
        wid.Bind(wx.EVT_CHECKBOX, OnItemRef)
        return wid

    def OnLamPick(event):
        data['Source'][1] = lamType = event.GetEventObject().GetValue()
        if 'P' in insVal['Type']:
            insVal['Lam1'] = waves[lamType][0]
            insVal['Lam2'] = waves[lamType][1]
        elif 'S' in insVal['Type'] and 'synch' not in lamType:
            insVal['Lam'] = meanwaves[lamType]
        updateData(insVal,insRef)
        i,j= wx.__version__.split('.')[0:2]
        if int(i)+int(j)/10. > 2.8:
            pass # repaint crashes wxpython 2.9
            wx.CallLater(100, MakeParameterWindow)
            #wx.CallAfter(MakeParameterWindow)
        else:
            wx.CallAfter(MakeParameterWindow)

    def MakeParameterWindow():
        'Displays the Instrument parameters in the dataWindow frame'
        G2frame.dataWindow.ClearData()
        mainSizer = G2frame.dataWindow.GetSizer()
        instSizer = wx.FlexGridSizer(0,3,5,5)
        subSizer = wx.BoxSizer(wx.HORIZONTAL)
        if insVal['Bank'] == None:      #patch
            insVal['Bank'] = 1
        text = ' Histogram Type: %s  Bank: %d'%(insVal['Type'],insVal['Bank'])
        subSizer.Add(wx.StaticText(G2frame.dataWindow,-1,text),0,WACV)
        mainSizer.Add(subSizer)
        labelLst[:],elemKeysLst[:],dspLst[:],refFlgElem[:] = [],[],[],[]
        if 'P' in insVal['Type']:                   #powder data
            [instSizer.Add(wx.StaticText(G2frame.dataWindow,-1,txt),0,WACV) for txt in [' Name (default)',' Value','Refine?']]
            if 'C' in insVal['Type']:               #constant wavelength
                labelLst.append('Azimuth angle')
                elemKeysLst.append(['Azimuth',1])
                dspLst.append([10,2])
                refFlgElem.append(None)                   
                if 'Lam1' in insVal:
                    subSizer = wx.BoxSizer(wx.HORIZONTAL)
                    subSizer.Add(wx.StaticText(G2frame.dataWindow,-1,' Azimuth: '),0,WACV)
                    txt = '%7.2f'%(insVal['Azimuth'])
                    subSizer.Add(wx.StaticText(G2frame.dataWindow,-1,txt.strip()),0,WACV)
                    subSizer.Add(wx.StaticText(G2frame.dataWindow,-1,'   Ka1/Ka2: '),0,WACV)
                    txt = u'  %8.6f/%8.6f\xc5'%(insVal['Lam1'],insVal['Lam2'])
                    subSizer.Add(wx.StaticText(G2frame.dataWindow,-1,txt.strip()),0,WACV)
                    waveSizer = wx.BoxSizer(wx.HORIZONTAL)
                    waveSizer.Add(wx.StaticText(G2frame.dataWindow,-1,'  Source type: '),0,WACV)
                    # PATCH?: for now at least, Source is not saved anywhere before here
                    if 'Source' not in data: data['Source'] = ['CuKa','?']
                    choice = ['TiKa','CrKa','FeKa','CoKa','CuKa','MoKa','AgKa']
                    lamPick = wx.ComboBox(G2frame.dataWindow,value=data['Source'][1],choices=choice,style=wx.CB_READONLY|wx.CB_DROPDOWN)
                    lamPick.Bind(wx.EVT_COMBOBOX, OnLamPick)
                    waveSizer.Add(lamPick,0)
                    subSizer.Add(waveSizer,0)
                    mainSizer.Add(subSizer)
                    instSizer.Add(wx.StaticText(G2frame.dataWindow,-1,lblWdef('I(L2)/I(L1)',4,insDef['I(L2)/I(L1)'])),0,WACV)
                    key = 'I(L2)/I(L1)'
                    labelLst.append(key)
                    elemKeysLst.append([key,1])
                    dspLst.append([10,4])
                    refFlgElem.append([key,2])                   
                    ratVal = G2G.ValidatedTxtCtrl(G2frame.dataWindow,insVal,key,nDig=(10,4),typeHint=float,OnLeave=AfterChange)
                    instSizer.Add(ratVal,0)
                    instSizer.Add(RefineBox(key),0,WACV)
                else: # single wavelength
                    instSizer.Add(wx.StaticText(G2frame.dataWindow,-1,' Azimuth: '),0,WACV)
                    txt = '%7.2f'%(insVal['Azimuth'])
                    instSizer.Add(wx.StaticText(G2frame.dataWindow,-1,txt.strip()),0,WACV)
                    instSizer.Add((5,5),0)
                    key = 'Lam'
                    instSizer.Add(wx.StaticText(G2frame.dataWindow,-1,u' Lam (\xc5): (%10.6f)'%(insDef[key])),0,WACV)
                    waveVal = G2G.ValidatedTxtCtrl(G2frame.dataWindow,insVal,key,nDig=(10,6),typeHint=float,OnLeave=AfterChange)
                    labelLst.append(u'Lam (\xc5)')
                    elemKeysLst.append([key,1])
                    dspLst.append([10,6])
                    instSizer.Add(waveVal,0,WACV)
                    refFlgElem.append([key,2])                   
                    instSizer.Add(RefineBox(key),0,WACV)
                for item in ['Zero','Polariz.']:
                    if item in insDef:
                        labelLst.append(item)
                        elemKeysLst.append([item,1])
                        dspLst.append([10,4])
                        instSizer.Add(wx.StaticText(G2frame.dataWindow,-1,lblWdef(item,4,insDef[item])),0,WACV)
                        itemVal = G2G.ValidatedTxtCtrl(G2frame.dataWindow,insVal,item,nDig=(10,4),typeHint=float,OnLeave=AfterChange)
                        instSizer.Add(itemVal,0,WACV)
                        refFlgElem.append([item,2])
                        instSizer.Add(RefineBox(item),0,WACV)
                for item in ['U','V','W','X','Y','Z','SH/L']:
                    nDig = (10,3)
                    if item == 'SH/L':
                        nDig = (10,5)
                    labelLst.append(item)
                    elemKeysLst.append([item,1])
                    dspLst.append(nDig)
                    refFlgElem.append([item,2])
                    instSizer.Add(wx.StaticText(G2frame.dataWindow,-1,lblWdef(item,nDig[1],insDef[item])),0,WACV)
                    itemVal = G2G.ValidatedTxtCtrl(G2frame.dataWindow,insVal,item,nDig=nDig,typeHint=float,OnLeave=NewProfile)
                    instSizer.Add(itemVal,0,WACV)
                    instSizer.Add(RefineBox(item),0,WACV)
            elif 'B' in insVal['Type']:                                   #pink beam CW (x-rays & neutrons(?))
                labelLst.append('Azimuth angle')
                elemKeysLst.append(['Azimuth',1])
                dspLst.append([10,2])
                refFlgElem.append(None)                   
                instSizer.Add(wx.StaticText(G2frame.dataWindow,-1,' Azimuth: '),0,WACV)
                txt = '%7.2f'%(insVal['Azimuth'])
                instSizer.Add(wx.StaticText(G2frame.dataWindow,-1,txt.strip()),0,WACV)
                instSizer.Add((5,5),0)
                key = 'Lam'
                instSizer.Add(wx.StaticText(G2frame.dataWindow,-1,u' Lam (\xc5): (%10.6f)'%(insDef[key])),0,WACV)
                waveVal = G2G.ValidatedTxtCtrl(G2frame.dataWindow,insVal,key,nDig=(10,6),typeHint=float,OnLeave=AfterChange)
                labelLst.append(u'Lam (\xc5)')
                elemKeysLst.append([key,1])
                dspLst.append([10,6])
                instSizer.Add(waveVal,0,WACV)
                refFlgElem.append([key,2])                   
                instSizer.Add(RefineBox(key),0,WACV)
                for item in ['Zero','Polariz.']:
                    if item in insDef:
                        labelLst.append(item)
                        elemKeysLst.append([item,1])
                        dspLst.append([10,4])
                        instSizer.Add(wx.StaticText(G2frame.dataWindow,-1,lblWdef(item,4,insDef[item])),0,WACV)
                        itemVal = G2G.ValidatedTxtCtrl(G2frame.dataWindow,insVal,item,nDig=(10,4),typeHint=float,OnLeave=AfterChange)
                        instSizer.Add(itemVal,0,WACV)
                        refFlgElem.append([item,2])
                        instSizer.Add(RefineBox(item),0,WACV)
                for item in ['U','V','W','X','Y','Z','alpha-0','alpha-1','beta-0','beta-1']:
                    nDig = (10,3)
                    labelLst.append(item)
                    elemKeysLst.append([item,1])
                    dspLst.append(nDig)
                    refFlgElem.append([item,2])
                    instSizer.Add(wx.StaticText(G2frame.dataWindow,-1,lblWdef(item,nDig[1],insDef[item])),0,WACV)
                    itemVal = G2G.ValidatedTxtCtrl(G2frame.dataWindow,insVal,item,nDig=nDig,typeHint=float,OnLeave=NewProfile)
                    instSizer.Add(itemVal,0,WACV)
                    instSizer.Add(RefineBox(item),0,WACV)
            elif 'T' in insVal['Type']:                                   #time of flight (neutrons)
                subSizer = wx.BoxSizer(wx.HORIZONTAL)
                subSizer.Add(wx.StaticText(G2frame.dataWindow,-1,' Flight path: '),0,WACV)
                txt = '%8.3f'%(insVal['fltPath'])
                subSizer.Add(wx.StaticText(G2frame.dataWindow,-1,txt.strip()),0,WACV)
                labelLst.append('flight path')
                elemKeysLst.append(['fltPath',1])
                dspLst.append([10,2])
                refFlgElem.append(None)                   
                subSizer.Add(wx.StaticText(G2frame.dataWindow,-1,'  2-theta: '),0,WACV)
                txt = '%7.2f'%(insVal['2-theta'])
                subSizer.Add(wx.StaticText(G2frame.dataWindow,-1,txt.strip()),0,WACV)
                labelLst.append('2-theta')
                elemKeysLst.append(['2-theta',1])
                dspLst.append([10,2])
                refFlgElem.append(None)                   
                if 'Pdabc' in Inst2:
                    Items = ['sig-0','sig-1','sig-2','sig-q','X','Y','Z']
                    subSizer.Add(wx.StaticText(G2frame.dataWindow,-1,'  difC: '),0,WACV)
                    txt = '%8.2f'%(insVal['difC'])
                    subSizer.Add(wx.StaticText(G2frame.dataWindow,-1,txt.strip()),0,WACV)
                    labelLst.append('difC')
                    elemKeysLst.append(['difC',1])
                    dspLst.append([10,2])
                    refFlgElem.append(None)
                    subSizer.Add(wx.StaticText(G2frame.dataWindow,-1,'  alpha, beta: fixed by table'),0,WACV)
                else:
                    Items = ['difC','difA','difB','Zero','alpha','beta-0','beta-1','beta-q','sig-0','sig-1','sig-2','sig-q','X','Y','Z']
                mainSizer.Add((5,5),0)
                mainSizer.Add(subSizer)
                mainSizer.Add((5,5),0)
                for item in Items:
                    if item == '':
                        instSizer.Add((5,5),0)
                        instSizer.Add((5,5),0)
                        instSizer.Add((5,5),0)
                        continue
                    nDig = (10,3)
                    if 'beta' in item:
                        nDig = (12,6)
                    instSizer.Add(
                            wx.StaticText(G2frame.dataWindow,-1,lblWdef(item,nDig[1],insDef[item])),
                            0,WACV)
                    itemVal = G2G.ValidatedTxtCtrl(G2frame.dataWindow,insVal,item,nDig=nDig,typeHint=float,OnLeave=AfterChange)
                    instSizer.Add(itemVal,0,WACV)
                    labelLst.append(item)
                    elemKeysLst.append([item,1])
                    dspLst.append(nDig)
                    refFlgElem.append([item,2])
                    instSizer.Add(RefineBox(item),0,WACV)
            elif 'PKS' in insVal['Type']:   #peak positions only
                key = 'Lam'
                instSizer.Add(wx.StaticText(G2frame.dataWindow,-1,u' Lam (\xc5): (%10.6f)'%(insDef[key])),
                    0,WACV)
                waveVal = G2G.ValidatedTxtCtrl(G2frame.dataWindow,insVal,key,nDig=(10,6),typeHint=float,OnLeave=AfterChange)
                labelLst.append(u'Lam (\xc5)')
                elemKeysLst.append([key,1])
                dspLst.append([10,6])
                instSizer.Add(waveVal,0,WACV)
                refFlgElem.append([key,2])                   
                for item in ['Zero',]:
                    if item in insDef:
                        labelLst.append(item)
                        elemKeysLst.append([item,1])
                        dspLst.append([10,4])
                        instSizer.Add(
                            wx.StaticText(G2frame.dataWindow,-1,lblWdef(item,4,insDef[item])),
                            0,WACV)
                        itemVal = G2G.ValidatedTxtCtrl(G2frame.dataWindow,insVal,item,nDig=(10,4),typeHint=float,OnLeave=AfterChange)
                        instSizer.Add(itemVal,0,WACV)
                        refFlgElem.append([item,2])
                
        elif 'S' in insVal['Type']:                       #single crystal data
            if 'C' in insVal['Type']:               #constant wavelength
                instSizer.Add(wx.StaticText(G2frame.dataWindow,-1,u' Lam (\xc5): (%10.6f)'%(insDef['Lam'])),
                    0,WACV)
                waveVal = G2G.ValidatedTxtCtrl(G2frame.dataWindow,insVal,'Lam',nDig=(10,6),typeHint=float,OnLeave=AfterChange)
                instSizer.Add(waveVal,0,WACV)
                labelLst.append(u'Lam (\xc5)')
                waveSizer = wx.BoxSizer(wx.HORIZONTAL)
                waveSizer.Add(wx.StaticText(G2frame.dataWindow,-1,'  Source type: '),0,WACV)
                # PATCH?: for now at least, Source is not saved anywhere before here
                if 'Source' not in data: data['Source'] = ['CuKa','?']
                choice = ['synchrotron','TiKa','CrKa','FeKa','CoKa','CuKa','MoKa','AgKa']
                lamPick = wx.ComboBox(G2frame.dataWindow,value=data['Source'][1],choices=choice,style=wx.CB_READONLY|wx.CB_DROPDOWN)
                lamPick.Bind(wx.EVT_COMBOBOX, OnLamPick)
                waveSizer.Add(lamPick,0,WACV)
                instSizer.Add(waveSizer,0,WACV)
                elemKeysLst.append(['Lam',1])
                dspLst.append([10,6])
                refFlgElem.append(None)
            else:                                   #time of flight (neutrons)
                pass                                #for now
        elif insVal['Type'][0] in ['L','R',]:
            if 'C' in insVal['Type']:        
                instSizer.Add(wx.StaticText(G2frame.dataWindow,-1,u' Lam (\xc5): (%10.6f)'%(insDef['Lam'])),
                    0,WACV)
                waveVal = G2G.ValidatedTxtCtrl(G2frame.dataWindow,insVal,'Lam',nDig=(10,6),typeHint=float,OnLeave=AfterChange)
                instSizer.Add(waveVal,0,WACV)
                labelLst.append(u'Lam (\xc5)')
                elemKeysLst.append(['Lam',1])
                dspLst.append([10,6])
                refFlgElem.append(None)
                instSizer.Add(wx.StaticText(G2frame.dataWindow,-1,'  Azimuth: %7.2f'%(insVal['Azimuth'])),0,WACV)
                labelLst.append('Azimuth angle')
                elemKeysLst.append(['Azimuth',1])
                dspLst.append([10,2])
                refFlgElem.append(None)                   
            else:                                   #time of flight (neutrons)
                pass                                #for now

        mainSizer.Add(instSizer,0)
        G2frame.dataWindow.SetDataSize()
        # end of MakeParameterWindow
                
    # beginning of UpdateInstrumentGrid code    
    #patch: make sure all parameter items are lists
    patched = 0
    for key in data:
        if type(data[key]) is tuple:
            data[key] = list(data[key])
            patched += 1
    if patched: print (patched,' instrument parameters changed from tuples')
    if 'Z' not in data:
        data['Z'] = [0.0,0.0,False]
    #end of patch
    labelLst,elemKeysLst,dspLst,refFlgElem = [],[],[],[]
    instkeys = keycheck(data.keys())
    if 'P' in data['Type'][0]:          #powder data
        insVal = dict(zip(instkeys,[data[key][1] for key in instkeys]))
        insDef = dict(zip(instkeys,[data[key][0] for key in instkeys]))
        insRef = dict(zip(instkeys,[data[key][2] for key in instkeys]))
        if 'NC' in data['Type'][0]:
            del(insDef['Polariz.'])
            del(insVal['Polariz.'])
            del(insRef['Polariz.'])
    elif 'S' in data['Type'][0]:                               #single crystal data
        insVal = dict(zip(instkeys,[data[key][1] for key in instkeys]))
        insDef = dict(zip(instkeys,[data[key][0] for key in instkeys]))
        insRef = {}
    elif 'L' in data['Type'][0]:                               #low angle data
        insVal = dict(zip(instkeys,[data[key][1] for key in instkeys]))
        insDef = dict(zip(instkeys,[data[key][0] for key in instkeys]))
        insRef = {}
    elif 'R' in data['Type'][0]:                               #low angle data
        insVal = dict(zip(instkeys,[data[key][1] for key in instkeys]))
        insDef = dict(zip(instkeys,[data[key][0] for key in instkeys]))
        insRef = {}
    RefObj = {}
    #These from Intl. Tables C, Table 4.2.2.1, p. 177-179
    waves = {'CuKa':[1.54051,1.54433],'TiKa':[2.74841,2.75207],'CrKa':[2.28962,2.29351],
        'FeKa':[1.93597,1.93991],'CoKa':[1.78892,1.79278],'MoKa':[0.70926,0.713543],
        'AgKa':[0.559363,0.563775]}
    # meanwaves computed as (2*Ka1+Ka2)/3
    meanwaves = {'CuKa':1.54178,'TiKa':2.74963,'CrKa':2.29092,'FeKa':1.93728,
        'CoKa':1.79021,'MoKa':0.71069,'AgKa':0.56083}
    Inst2 = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,
            G2frame.PatternId,'Instrument Parameters'))[1]        
    G2gd.SetDataMenuBar(G2frame)
    #patch
    if 'P' in insVal['Type']:                   #powder data
        if 'C' in insVal['Type']:               #constant wavelength
            if 'Azimuth' not in insVal:
                insVal['Azimuth'] = 0.0
                insDef['Azimuth'] = 0.0
                insRef['Azimuth'] = False
#        if 'T' in insVal['Type']:
#            if 'difB' not in insVal:
#                insVal['difB'] = 0.0
#                insDef['difB'] = 0.0
#                insRef['difB'] = False
    #end of patch
    if 'P' in insVal['Type']:                   #powder data menu commands
        G2gd.SetDataMenuBar(G2frame,G2frame.dataWindow.InstMenu)
        G2frame.GetStatusBar().SetStatusText('NB: Azimuth is used for polarization only',1)
        G2frame.Bind(wx.EVT_MENU,OnCalibrate,id=G2G.wxID_INSTCALIB)
        G2frame.Bind(wx.EVT_MENU,OnLoad,id=G2G.wxID_INSTLOAD)
        G2frame.Bind(wx.EVT_MENU,OnSave,id=G2G.wxID_INSTSAVE)
        G2frame.Bind(wx.EVT_MENU,OnSaveAll,id=G2G.wxID_INSTSAVEALL)
        G2frame.Bind(wx.EVT_MENU,OnReset,id=G2G.wxID_INSTPRMRESET)
        G2frame.Bind(wx.EVT_MENU,OnInstCopy,id=G2G.wxID_INSTCOPY)
        G2frame.Bind(wx.EVT_MENU,OnInstFlagCopy,id=G2G.wxID_INSTFLAGCOPY)
        G2frame.Bind(wx.EVT_MENU,OnCopy1Val,id=G2G.wxID_INST1VAL)
    elif 'L' in insVal['Type'] or 'R' in insVal['Type']:                   #SASD data menu commands
        G2gd.SetDataMenuBar(G2frame,G2frame.dataWindow.SASDInstMenu)
        G2frame.Bind(wx.EVT_MENU,OnInstCopy,id=G2G.wxID_SASDINSTCOPY)
    MakeParameterWindow()
        
    
################################################################################
#####  Sample parameters
################################################################################           
       
def UpdateSampleGrid(G2frame,data):
    '''respond to selection of PWDR/SASD Sample Parameters
    data tree item.
    '''

    def OnSampleSave(event):
        '''Respond to the Sample Parameters Operations/Save menu
        item: writes current parameters to a .samprm file
        '''
        pth = G2G.GetExportPath(G2frame)
        dlg = wx.FileDialog(G2frame, 'Choose GSAS-II sample parameters file', pth, '', 
            'sample parameter files (*.samprm)|*.samprm',wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                # make sure extension is .samprm
                filename = os.path.splitext(filename)[0]+'.samprm'
                File = open(filename,'w')
                File.write("#GSAS-II sample parameter file\n")
                File.write("'Type':'"+str(data['Type'])+"'\n")
                File.write("'Gonio. radius':"+str(data['Gonio. radius'])+"\n")
                if data.get('InstrName'):
                    File.write("'InstrName':'"+str(data['InstrName'])+"'\n")
                File.close()
        finally:
            dlg.Destroy()
            
    def OnSampleLoad(event):
        '''Loads sample parameters from a G2 .samprm file
        in response to the Sample Parameters-Operations/Load menu
        
        Note that similar code is found in ReadPowderInstprm (GSASII.py)
        '''
        pth = G2G.GetImportPath(G2frame)
        if not pth: pth = '.'
        dlg = wx.FileDialog(G2frame, 'Choose GSAS-II sample parameters file', pth, '', 
            'sample parameter files (*.samprm)|*.samprm',wx.FD_OPEN)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                File = open(filename,'r')
                S = File.readline()
                newItems = {}
                while S:
                    if S[0] == '#':
                        S = File.readline()
                        continue
                    [item,val] = S[:-1].split(':')
                    newItems[item.strip("'")] = eval(val)
                    S = File.readline()                
                File.close()
                data.update(newItems)
                G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId,'Sample Parameters'),data)
                UpdateSampleGrid(G2frame,data)
        finally:
            dlg.Destroy()
            
    def OnAllSampleLoad(event):
        filename = ''
        pth = G2G.GetImportPath(G2frame)
        if not pth: pth = '.'
        dlg = wx.FileDialog(G2frame, 'Choose multihistogram metadata text file', pth, '', 
            'metadata file (*.*)|*.*',wx.FD_OPEN)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                File = open(filename,'r')
                S = File.readline()
                newItems = []
                itemNames = []
                Comments = []
                while S:
                    if S[0] == '#':
                        Comments.append(S)
                        S = File.readline()
                        continue
                    S = S.replace(',',' ').replace('\t',' ')
                    Stuff = S[:-1].split()
                    itemNames.append(Stuff[0])
                    newItems.append(Stuff[1:])
                    S = File.readline()                
                File.close()
        finally:
            dlg.Destroy()
        if not filename:
            G2frame.ErrorDialog('Nothing to do','No file selected')
            return
        dataDict = dict(zip(itemNames,newItems))
        ifany = False
        Controls = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.root,'Controls'))
        Names = [' ','Phi','Chi','Omega','Time','Temperature','Pressure']
        freeNames = {}
        for name in ['FreePrm1','FreePrm2','FreePrm3']:
            freeNames[Controls[name]] = name
            Names.append(Controls[name])
        #import imp
        #imp.reload(G2G)
        dlg = G2G.G2ColumnIDDialog( G2frame,' Choose multihistogram metadata columns:',
            'Select columns',Comments,Names,np.array(newItems).T)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                colNames,newData = dlg.GetSelection()
                dataDict = dict(zip(itemNames,newData.T))
                for item in colNames:
                    if item != ' ':
                        ifany = True
        finally:
            dlg.Destroy()
        if not ifany:
            G2frame.ErrorDialog('Nothing to do','No columns identified')
            return
        histList = [G2frame.GPXtree.GetItemText(G2frame.PatternId),]
        histList += GetHistsLikeSelected(G2frame)
        colIds = {}
        for i,name in enumerate(colNames):
            if name != ' ':
                colIds[name] = i
        for hist in histList:
            name = hist.split()[1]  #this is file name
            newItems = {}
            for item in colIds:
                key = freeNames.get(item,item)
                newItems[key] = float(dataDict[name][colIds[item]])
            Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,hist)
            sampleData = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,Id,'Sample Parameters'))
            sampleData.update(newItems)        
        UpdateSampleGrid(G2frame,data)        
    
    def OnSetScale(event):
        if histName[:4] in ['REFD','PWDR']:
            Scale = data['Scale'][0]
            dlg = wx.MessageDialog(G2frame,'Rescale data by %.2f?'%(Scale),'Rescale data',wx.OK|wx.CANCEL)
            try:
                if dlg.ShowModal() == wx.ID_OK:
                    pId = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,histName)
                    y,w = G2frame.GPXtree.GetItemPyData(pId)[1][1:3]
                    y *= Scale
                    w /= Scale**2
                    data['Scale'][0] = 1.0
            finally:
                dlg.Destroy()
            G2plt.PlotPatterns(G2frame,plotType=histName[:4],newPlot=True)
            UpdateSampleGrid(G2frame,data)
            return
        #SASD rescaliing                
        histList = []
        item, cookie = G2frame.GPXtree.GetFirstChild(G2frame.root)
        while item:
            name = G2frame.GPXtree.GetItemText(item)
            if 'SASD' in name and name != histName:
                histList.append(name)
            item, cookie = G2frame.GPXtree.GetNextChild(G2frame.root, cookie)
        if not len(histList):      #nothing to copy to!
            return
        dlg = wx.SingleChoiceDialog(G2frame,'Select reference histogram for scaling',
            'Reference histogram',histList)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                sel = dlg.GetSelection()
                refHist = histList[sel]
        finally:
            dlg.Destroy()
        Limits = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Limits'))
        Profile = G2frame.GPXtree.GetItemPyData(G2frame.PatternId)[1]
        Data = [Profile,Limits,data]
        refId = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,refHist)
        refSample = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,refId, 'Sample Parameters'))
        refLimits = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,refId, 'Limits'))
        refProfile = G2frame.GPXtree.GetItemPyData(refId)[1]
        refData = [refProfile,refLimits,refSample]
        G2sasd.SetScale(Data,refData)
        G2plt.PlotPatterns(G2frame,plotType='SASD',newPlot=True)
        UpdateSampleGrid(G2frame,data)
        
    def OnRescaleAll(event):
        hst = G2frame.GPXtree.GetItemText(G2frame.PatternId)
        histList = GetHistsLikeSelected(G2frame)
        x0,y0,w0 = G2frame.GPXtree.GetItemPyData(G2frame.PatternId)[1][:3]
        if not histList:
            G2frame.ErrorDialog('No match','No histograms match '+hst,G2frame)
            return
        od = {'label_1':'Scaling range min','value_1':0.0,'label_2':'Scaling range max','value_2':10.}
        dlg = G2G.G2MultiChoiceDialog(G2frame,
            'Do scaling from\n'+str(hst[5:])+' to...','Rescale histograms', histList,extraOpts=od)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                Xmin = od['value_1']
                Xmax = od['value_2']
                iBeg = np.searchsorted(x0,Xmin)
                iFin = np.searchsorted(x0,Xmax)
                if iBeg > iFin:
                    wx.MessageBox('Wrong order for Xmin, Xmax','Error',style=wx.ICON_EXCLAMATION)
                else:
                    sum0 = np.sum(y0[iBeg:iFin])
                    result = dlg.GetSelections()
                    for i in result: 
                        item = histList[i]
                        Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,item)
                        xi,yi,wi = G2frame.GPXtree.GetItemPyData(Id)[1][:3]
                        sumi = np.sum(yi[iBeg:iFin])
                        if sumi:
                            Scale = sum0/sumi
                            yi *= Scale
                            wi /= Scale**2
        finally:
            dlg.Destroy()
        G2plt.PlotPatterns(G2frame,plotType=histName[:4],newPlot=True)
        
    def OnSampleCopy(event):
        histType,copyNames = SetCopyNames(histName,data['Type'],
            addNames = ['Omega','Chi','Phi','Gonio. radius','InstrName'])
        copyDict = {}
        for parm in copyNames:
            copyDict[parm] = data[parm]
        hst = G2frame.GPXtree.GetItemText(G2frame.PatternId)
        histList = GetHistsLikeSelected(G2frame)
        if not histList:
            G2frame.ErrorDialog('No match','No histograms match '+hst,G2frame)
            return
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Copy sample params from\n'+str(hst[5:])+' to...',
            'Copy sample parameters', histList)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                result = dlg.GetSelections()
                for i in result: 
                    item = histList[i]
                    Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,item)
                    sampleData = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,Id,'Sample Parameters'))
                    sampleData.update(copy.deepcopy(copyDict))
        finally:
            dlg.Destroy()

    def OnSampleCopySelected(event):
        hst = G2frame.GPXtree.GetItemText(G2frame.PatternId)
        Controls = G2frame.GPXtree.GetItemPyData(
            G2gd.GetGPXtreeItemId(G2frame,G2frame.root, 'Controls'))
        histList = GetHistsLikeSelected(G2frame)
        if not histList:
            G2frame.ErrorDialog('No match','No histograms match '+hst,G2frame)
            return
        # Assemble a list of item labels
        TextTable = {key:label for key,label,dig in
            SetupSampleLabels(hst,data.get('Type'),Inst['Type'][0])}
        # get flexible labels
        TextTable.update({key:Controls[key] for key in Controls if key.startswith('FreePrm')})
        # add a few extra
        TextTable.update({'Type':'Diffractometer type','InstrName':'Instrument Name',})
        # Assemble a list of dict entries that would be labeled in the Sample
        # params data window (drop ranId and items not used).
        keyList = [i for i in data.keys() if i in TextTable]
        keyText = [TextTable[i] for i in keyList]
        # sort both lists together, ordered by keyText
        keyText, keyList = zip(*sorted(list(zip(keyText,keyList)))) # sort lists 
        selectedKeys = []
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Select which sample parameters\nto copy',
            'Select sample parameters', keyText)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                selectedKeys = [keyList[i] for i in dlg.GetSelections()]
        finally:
            dlg.Destroy()
        if not selectedKeys: return # nothing to copy
        copyDict = {}
        for parm in selectedKeys:
            copyDict[parm] = data[parm]
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Copy sample params from\n'+str(hst[5:])+' to...',
            'Copy sample parameters', histList)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                result = dlg.GetSelections()
                for i in result: 
                    item = histList[i]
                    Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,item)
                    sampleData = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,Id,'Sample Parameters'))
                    sampleData.update(copy.deepcopy(copyDict))
        finally:
            dlg.Destroy()            
        G2plt.PlotPatterns(G2frame,plotType=hst[:4],newPlot=False)

    def OnSampleFlagCopy(event):
        histType,copyNames = SetCopyNames(histName,data['Type'])
        flagDict = {}
        for parm in copyNames:
            flagDict[parm] = data[parm][1]
        hst = G2frame.GPXtree.GetItemText(G2frame.PatternId)
        histList = GetHistsLikeSelected(G2frame)
        if not histList:
            G2frame.ErrorDialog('No match','No histograms match '+hst,G2frame)
            return
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Copy sample ref. flags from\n'+str(hst[5:])+' to...',
            'Copy sample flags', histList)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                result = dlg.GetSelections()
                for i in result: 
                    item = histList[i]
                    Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,item)
                    sampleData = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,Id,'Sample Parameters'))
                    for name in copyNames:
                        sampleData[name][1] = copy.copy(flagDict[name])
        finally:
            dlg.Destroy()

    def OnHistoChange():
        '''Called when the histogram type is changed to refresh the window
        '''
        #wx.CallAfter(UpdateSampleGrid,G2frame,data)
        wx.CallLater(100,UpdateSampleGrid,G2frame,data)
        
    def SetNameVal():
        inst = instNameVal.GetValue()
        data['InstrName'] = inst.strip()

    def OnNameVal(event):
        event.Skip()
        wx.CallAfter(SetNameVal)
        
    def AfterChange(invalid,value,tc):
        if invalid:
            return
        if tc.key == 0 and 'SASD' in histName:          #a kluge for Scale!
            G2plt.PlotPatterns(G2frame,plotType='SASD',newPlot=True)
        elif tc.key == 'Thick':
            wx.CallAfter(UpdateSampleGrid,G2frame,data)            
            
    def OnMaterial(event):
        Obj = event.GetEventObject()
        Id = Info[Obj.GetId()]
        data['Materials'][Id]['Name'] = Obj.GetValue()
        wx.CallAfter(UpdateSampleGrid,G2frame,data)
        
    def OnVolFrac(invalid,value,tc):
        Id = Info[tc.GetId()]
        data['Materials'][not Id][key] = 1.-value
        wx.CallAfter(UpdateSampleGrid,G2frame,data)

    def OnCopy1Val(event):
        'Select one value to copy to many histograms and optionally allow values to be edited in a table'
        G2G.SelectEdit1Var(G2frame,data,labelLst,elemKeysLst,dspLst,refFlgElem)
        wx.CallAfter(UpdateSampleGrid,G2frame,data)
        
    def SearchAllComments(value,tc,*args,**kwargs):
        '''Called when the label for a FreePrm is changed: the comments for all PWDR
        histograms are searched for a "label=value" pair that matches the label (case
        is ignored) and the values are then set to this value, if it can be converted
        to a float.
        '''
        Id, cookie = G2frame.GPXtree.GetFirstChild(G2frame.root)
        while Id:
            name = G2frame.GPXtree.GetItemText(Id)
            if 'PWDR' in name:
                Comments = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,Id,'Comments'))
                Sample =   G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,Id, 'Sample Parameters'))
                for i,item in enumerate(Comments):
                    itemSp = item.split('=')
                    if value.lower() == itemSp[0].lower():
                        try:
                            Sample[tc.key] = float(itemSp[1])
                        except:
                            print('"{}" has an invalid value in Comments from {}'
                                  .format(item.strip(),name))
            Id, cookie = G2frame.GPXtree.GetNextChild(G2frame.root, cookie)
        wx.CallLater(100,UpdateSampleGrid,G2frame,data)
        
        
    ######## DEBUG #######################################################
    #import GSASIIpwdGUI
    #reload(GSASIIpwdGUI)
    #reload(G2gd)
    ######################################################################
    Inst = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(
            G2frame,G2frame.PatternId, 'Instrument Parameters'))[0]
    histName = G2frame.GPXtree.GetItemText(G2frame.PatternId)
    G2gd.SetDataMenuBar(G2frame,G2frame.dataWindow.SampleMenu)
    #G2frame.SetLabel(G2frame.GetLabel().split('||')[0]+' || '+'Sample Parameters')
    G2frame.Bind(wx.EVT_MENU, OnSetScale, id=G2G.wxID_SETSCALE)
    G2frame.Bind(wx.EVT_MENU, OnSampleCopy, id=G2G.wxID_SAMPLECOPY)
    G2frame.Bind(wx.EVT_MENU, OnSampleCopySelected, id=G2G.wxID_SAMPLECOPYSOME)
    G2frame.Bind(wx.EVT_MENU, OnSampleFlagCopy, id=G2G.wxID_SAMPLEFLAGCOPY)
    G2frame.Bind(wx.EVT_MENU, OnSampleSave, id=G2G.wxID_SAMPLESAVE)
    G2frame.Bind(wx.EVT_MENU, OnSampleLoad, id=G2G.wxID_SAMPLELOAD)
    G2frame.Bind(wx.EVT_MENU, OnCopy1Val, id=G2G.wxID_SAMPLE1VAL)
    G2frame.Bind(wx.EVT_MENU, OnAllSampleLoad, id=G2G.wxID_ALLSAMPLELOAD)
    G2frame.Bind(wx.EVT_MENU, OnRescaleAll, id=G2G.wxID_RESCALEALL)
    if histName[:4] in ['SASD','REFD','PWDR']:
        G2frame.dataWindow.SetScale.Enable(True)
    Controls = G2frame.GPXtree.GetItemPyData(
        G2gd.GetGPXtreeItemId(G2frame,G2frame.root, 'Controls'))
#patch
    if 'ranId' not in data:
        data['ranId'] = ran.randint(0,sys.maxsize)
    if not 'Gonio. radius' in data:
        data['Gonio. radius'] = 200.0
    if not 'Omega' in data:
        data.update({'Omega':0.0,'Chi':0.0,'Phi':0.0})
    if 'Azimuth' not in data:
        data['Azimuth'] = 0.0
    if type(data['Temperature']) is int:
        data['Temperature'] = float(data['Temperature'])
    if 'Time' not in data:
        data['Time'] = 0.0
    if 'FreePrm1' not in Controls:
        Controls['FreePrm1'] = 'Sample humidity (%)'
    if 'FreePrm2' not in Controls:
        Controls['FreePrm2'] = 'Sample voltage (V)'
    if 'FreePrm3' not in Controls:
        Controls['FreePrm3'] = 'Applied load (MN)'
    if 'FreePrm1' not in data:
        data['FreePrm1'] = 0.
    if 'FreePrm2' not in data:
        data['FreePrm2'] = 0.
    if 'FreePrm3' not in data:
        data['FreePrm3'] = 0.
    if 'SurfRoughA' not in data and 'PWDR' in histName:
        data['SurfRoughA'] = [0.,False]
        data['SurfRoughB'] = [0.,False]
    if 'Trans' not in data and 'SASD' in histName:
        data['Trans'] = 1.0
    if 'SlitLen' not in data and 'SASD' in histName:
        data['SlitLen'] = 0.0
    if 'Shift' not in data:
        data['Shift'] = [0.0,False]
    if 'Transparency' not in data:
        data['Transparency'] = [0.0,False]
    data['InstrName'] = data.get('InstrName','')
#patch end
    labelLst,elemKeysLst,dspLst,refFlgElem = [],[],[],[]
    parms = SetupSampleLabels(histName,data.get('Type'),Inst['Type'][0])
    G2frame.dataWindow.ClearData()
    mainSizer = G2frame.dataWindow.GetSizer()
    topSizer = wx.BoxSizer(wx.HORIZONTAL)
    topSizer.Add((-1,-1),1,WACV|wx.EXPAND)
    topSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Sample and Experimental Parameters'))
    # add help button to bring up help web page
    helpkey = G2frame.dataWindow.helpKey
    topSizer.Add((30,-1))
    topSizer.Add(G2G.HelpButton(G2frame.dataWindow,helpIndex=helpkey))
    topSizer.Add((-1,-1),1,WACV|wx.EXPAND)
    mainSizer.Add(topSizer,0,WACV|wx.EXPAND)
    nameSizer = wx.BoxSizer(wx.HORIZONTAL)
    nameSizer.Add(wx.StaticText(G2frame.dataWindow,wx.ID_ANY,' Instrument Name '),0,WACV)
    nameSizer.Add((-1,-1),1,WACV)
    instNameVal = wx.TextCtrl(G2frame.dataWindow,wx.ID_ANY,data['InstrName'],
        size=(200,-1),style=wx.TE_PROCESS_ENTER)        
    nameSizer.Add(instNameVal)
    instNameVal.Bind(wx.EVT_CHAR,OnNameVal)
    mainSizer.Add(nameSizer,0,WACV)
    mainSizer.Add((5,5),0)
    labelLst.append('Instrument Name')
    elemKeysLst.append(['InstrName'])
    dspLst.append(None)
    refFlgElem.append(None)

    if 'PWDR' in histName:
        nameSizer = wx.BoxSizer(wx.HORIZONTAL)
        nameSizer.Add(wx.StaticText(G2frame.dataWindow,wx.ID_ANY,' Diffractometer type: '),
                    0,WACV)
        if 'T' in Inst['Type'][0]:
            choices = ['Debye-Scherrer',]
        else:
            choices = ['Debye-Scherrer','Bragg-Brentano',]
        histoType = G2G.G2ChoiceButton(G2frame.dataWindow,choices,
                    strLoc=data,strKey='Type',
                    onChoice=OnHistoChange)
        nameSizer.Add(histoType)
        mainSizer.Add(nameSizer,0,WACV)
        mainSizer.Add((5,5),0)

    parmSizer = wx.FlexGridSizer(0,2,5,0)
    for key,lbl,nDig in parms:
        labelLst.append(lbl.strip().strip(':').strip())
        dspLst.append(nDig)
        if 'list' in str(type(data[key])):
            parmRef = G2G.G2CheckBox(G2frame.dataWindow,' '+lbl,data[key],1)
            parmSizer.Add(parmRef,0,WACV|wx.EXPAND)
            parmVal = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data[key],0,
                nDig=nDig,typeHint=float,OnLeave=AfterChange)
            elemKeysLst.append([key,0])
            refFlgElem.append([key,1])
        else:
            parmSizer.Add(wx.StaticText(G2frame.dataWindow,label=' '+lbl),
                0,WACV|wx.EXPAND)
            parmVal = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data,key,
                typeHint=float,OnLeave=AfterChange)
            elemKeysLst.append([key])
            refFlgElem.append(None)
        parmSizer.Add(parmVal,0,WACV)
    Info = {}
    
    for key in ('FreePrm1','FreePrm2','FreePrm3'):
        parmVal = G2G.ValidatedTxtCtrl(G2frame.dataWindow,Controls,key,typeHint=str,
                                        notBlank=False,OnLeave=SearchAllComments)
        parmSizer.Add(parmVal,1,wx.EXPAND)
        parmVal = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data,key,typeHint=float)
        parmSizer.Add(parmVal,0,WACV)
        labelLst.append(Controls[key])
        dspLst.append(None)
        elemKeysLst.append([key])
        refFlgElem.append(None)
        
    mainSizer.Add(parmSizer,0)
    mainSizer.Add((0,5),0)    
    if histName[:4] in ['SASD',]:
        rho = [0.,0.]
        anomrho = [0.,0.]
        mu = 0.
        subSizer = wx.FlexGridSizer(0,4,5,5)
        Substances = G2frame.GPXtree.GetItemPyData(
            G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Substances'))
        for Id,item in enumerate(data['Materials']):
            subSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Material: '),0,WACV)
            matsel = wx.ComboBox(G2frame.dataWindow,value=item['Name'],choices=list(Substances['Substances'].keys()),
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
            Info[matsel.GetId()] = Id
            matsel.Bind(wx.EVT_COMBOBOX,OnMaterial)        
            subSizer.Add(matsel,0,WACV)
            subSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Volume fraction: '),0,WACV)
            volfrac = G2G.ValidatedTxtCtrl(G2frame.dataWindow,item,'VolFrac',
                xmin=0.,xmax=1.,nDig=(10,3),typeHint=float,OnLeave=OnVolFrac)
            subSizer.Add(volfrac,0,WACV)
            try:
                material = Substances['Substances'][item['Name']]
            except KeyError:
                print('ERROR - missing substance: '+item['Name'])
                material = Substances['Substances']['vacuum']
            mu += item['VolFrac']*material.get('XAbsorption',0.)
            rho[Id] = material['Scatt density']
            anomrho[Id] = material.get('XAnom density',0.)
        data['Contrast'] = [(rho[1]-rho[0])**2,(anomrho[1]-anomrho[0])**2]
        mainSizer.Add(subSizer,0)
        conSizer = wx.BoxSizer(wx.HORIZONTAL)
        conSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Contrast: %10.2f '%(data['Contrast'][0])),0,WACV)
        conSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Anom. Contrast: %10.2f '%(data['Contrast'][1])),0,WACV)
        mut =  mu*data['Thick']
        conSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Transmission (calc): %10.3f  '%(np.exp(-mut))),0,WACV)
        mainSizer.Add(conSizer,0)
    G2frame.dataWindow.SetDataSize()
    
################################################################################
#####  Indexing Peaks
################################################################################           
       
def UpdateIndexPeaksGrid(G2frame, data):
    '''respond to selection of PWDR Index Peak List data
    tree item.
    '''
    bravaisSymb = ['Fm3m','Im3m','Pm3m','R3-H','P6/mmm','I4/mmm',
        'P4/mmm','Fmmm','Immm','Ammm','Bmmm','Cmmm','Pmmm','C2/m','P2/m','C1','P1']
    IndexId = G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Index Peak List')
    Inst = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Instrument Parameters'))[0]
    limitId = G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Limits')
    Limits = G2frame.GPXtree.GetItemPyData(limitId)
    
    def RefreshIndexPeaksGrid(event):
        r,c =  event.GetRow(),event.GetCol()
        peaks = G2frame.IndexPeaksTable.GetData()
        if c == 2:
            peaks[r][c] = not peaks[r][c]
            G2frame.IndexPeaksTable.SetData(peaks)
            G2frame.indxPeaks.ForceRefresh()
            if 'PKS' in G2frame.GPXtree.GetItemText(G2frame.PatternId):
                G2plt.PlotPowderLines(G2frame)
            else:
                G2plt.PlotPatterns(G2frame,plotType='PWDR')
            
    def OnReload(event):
        peaks = []
        sigs = []
        Peaks = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Peak List'))
        for ip,peak in enumerate(Peaks['peaks']):
            dsp = G2lat.Pos2dsp(Inst,peak[0])
            peaks.append([peak[0],peak[2],True,False,0,0,0,dsp,0.0])    #SS?
            try:
                sig = Peaks['sigDict']['pos'+str(ip)]
            except KeyError:
                sig = 0.
            sigs.append(sig)
        data = [peaks,sigs]
        G2frame.GPXtree.SetItemPyData(IndexId,data)
        UpdateIndexPeaksGrid(G2frame,data)
        
    def OnSave(event):
        pth = G2G.GetExportPath(G2frame)
        dlg = wx.FileDialog(G2frame, 'Choose Index peaks csv file', pth, '', 
            'indexing peaks file (*.csv)|*.csv',wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                filename = os.path.splitext(filename)[0]+'.csv'
                File = open(filename,'w')
                names = 'h,k,l,position,intensity,d-Obs,d-calc\n'
                File.write(names)
                fmt = '%d,%d,%d,%.4f,%.1f,%.5f,%.5f\n'
                for refl in data[0]:
                    if refl[3]:
                        File.write(fmt%(refl[4],refl[5],refl[6],refl[0],refl[1],refl[7],refl[8]))
                File.close()
        finally:
            dlg.Destroy()
        
    def KeyEditPickGrid(event):
        colList = G2frame.indxPeaks.GetSelectedCols()
        data = G2frame.GPXtree.GetItemPyData(IndexId)
        if event.GetKeyCode() == wx.WXK_RETURN:
            event.Skip(True)
        elif event.GetKeyCode() == wx.WXK_CONTROL:
            event.Skip(True)
        elif event.GetKeyCode() == wx.WXK_SHIFT:
            event.Skip(True)
        elif colList:
            G2frame.indxPeaks.ClearSelection()
            key = event.GetKeyCode()
            for col in colList:
                if G2frame.IndexPeaksTable.GetColLabelValue(col) in ['use',]:
                    if key == 89: #'Y'
                        for row in range(G2frame.IndexPeaksTable.GetNumberRows()): data[0][row][col]=True
                    elif key == 78:  #'N'
                        for row in range(G2frame.IndexPeaksTable.GetNumberRows()): data[0][row][col]=False
                    elif key == 83: # 'S'
                        for row in range(G2frame.IndexPeaksTable.GetNumberRows()): data[0][row][col] = not data[0][row][col]
            
    if 'PWD' in G2frame.GPXtree.GetItemText(G2frame.PatternId):
        G2gd.SetDataMenuBar(G2frame,G2frame.dataWindow.IndPeaksMenu)
        G2frame.Bind(wx.EVT_MENU, OnReload, id=G2G.wxID_INDXRELOAD)
        G2frame.Bind(wx.EVT_MENU, OnSave, id=G2G.wxID_INDEXSAVE)
    G2frame.dataWindow.IndexPeaks.Enable(False)
    G2frame.IndexPeaksTable = []
    if len(data[0]):
        G2frame.dataWindow.IndexPeaks.Enable(True)
        Unit = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Unit Cells List'))
        if Unit:
            if len(Unit) == 4:  #patch
                Unit.append({})
            if len(Unit) == 5:  #patch
                Unit.append({})
            controls,bravais,cellist,dmin,ssopt,magcells = Unit
            if 'T' in Inst['Type'][0]:   #TOF - use other limit!
                dmin = G2lat.Pos2dsp(Inst,Limits[1][0])
            else:
                dmin = G2lat.Pos2dsp(Inst,Limits[1][1])
            G2frame.HKL = []
            if ssopt.get('Use',False):
                cell = controls[6:12]
                A = G2lat.cell2A(cell)
                ibrav = bravaisSymb.index(controls[5])
                spc = controls[13]
                SGData = G2spc.SpcGroup(spc)[1]
                SSGData = G2spc.SSpcGroup(SGData,ssopt['ssSymb'])[1]
                Vec = ssopt['ModVec']
                maxH = ssopt['maxH']
                G2frame.HKL = G2pwd.getHKLMpeak(dmin,Inst,SGData,SSGData,Vec,maxH,A)
                G2frame.HKL = np.array(G2frame.HKL)
                data[0] = G2indx.IndexSSPeaks(data[0],G2frame.HKL)[1]
            else:        #select cell from table - no SS
                for i,cell in enumerate(cellist):
                    if cell[-2]:
                        ibrav = cell[2]
                        A = G2lat.cell2A(cell[3:9])
                        G2frame.HKL = G2lat.GenHBravais(dmin,ibrav,A)
                        for hkl in G2frame.HKL:
                            hkl.insert(4,G2lat.Dsp2pos(Inst,hkl[3]))
                        G2frame.HKL = np.array(G2frame.HKL)
                        data[0] = G2indx.IndexPeaks(data[0],G2frame.HKL)[1]
                        break
    rowLabels = []
    for i in range(len(data[0])): rowLabels.append(str(i+1))
    colLabels = ['position','intensity','use','indexed','h','k','l','d-obs','d-calc']
    Types = [wg.GRID_VALUE_FLOAT+':10,4',wg.GRID_VALUE_FLOAT+':10,1',]+2*[wg.GRID_VALUE_BOOL,]+ \
        3*[wg.GRID_VALUE_LONG,]+2*[wg.GRID_VALUE_FLOAT+':10,5',]
    if len(data[0]) and len(data[0][0]) > 9:
        colLabels = ['position','intensity','use','indexed','h','k','l','m','d-obs','d-calc']
        Types = [wg.GRID_VALUE_FLOAT+':10,4',wg.GRID_VALUE_FLOAT+':10,1',]+2*[wg.GRID_VALUE_BOOL,]+ \
            4*[wg.GRID_VALUE_LONG,]+2*[wg.GRID_VALUE_FLOAT+':10,5',]
    G2frame.GPXtree.SetItemPyData(IndexId,data)
    G2frame.IndexPeaksTable = G2G.Table(data[0],rowLabels=rowLabels,colLabels=colLabels,types=Types)
    G2frame.dataWindow.currentGrids = []
    G2frame.indxPeaks = G2G.GSGrid(parent=G2frame.dataWindow)                
    G2frame.indxPeaks.SetTable(G2frame.IndexPeaksTable, True)
    G2frame.indxPeaks.SetScrollRate(10,10)
    XY = []
    Sigs = []
    for r in range(G2frame.indxPeaks.GetNumberRows()):
        for c in range(G2frame.indxPeaks.GetNumberCols()):
            if c == 2:
                G2frame.indxPeaks.SetReadOnly(r,c,isReadOnly=False)
            else:
                G2frame.indxPeaks.SetReadOnly(r,c,isReadOnly=True)
        if data[0][r][2] and data[0][r][3]:
            XY.append([data[0][r][-1],data[0][r][0]])
            try:
                sig = data[1][r]
            except IndexError:
                sig = 0.
            Sigs.append(sig)
    G2frame.indxPeaks.Bind(wg.EVT_GRID_CELL_LEFT_CLICK, RefreshIndexPeaksGrid)
    G2frame.indxPeaks.Bind(wx.EVT_KEY_DOWN, KeyEditPickGrid)                 
    G2frame.indxPeaks.AutoSizeColumns(False)
    if len(XY):
        XY = np.array(XY)
        G2plt.PlotCalib(G2frame,Inst,XY,Sigs,newPlot=True)
    G2frame.dataWindow.ClearData()
    mainSizer = G2frame.dataWindow.GetSizer()
    mainSizer.Add(G2frame.indxPeaks,0,wx.ALL|wx.EXPAND,1)
    G2frame.dataWindow.SetDataSize()

################################################################################
#####  Unit cells
################################################################################

def UpdateUnitCellsGrid(G2frame, data):
    '''respond to selection of PWDR Unit Cells data tree item.
    '''
    G2frame.ifGetExclude = False
    UnitCellsId = G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Unit Cells List')
    SPGlist = G2spc.spglist
    bravaisSymb = ['Fm3m','Im3m','Pm3m','R3-H','P6/mmm','I4/mmm','P4/mmm',
        'Fmmm','Immm','Ammm','Bmmm','Cmmm','Pmmm','I2/m','C2/m','P2/m','P1','C1']
    spaceGroups = ['F m 3 m','I m 3 m','P m 3 m','R 3 m','P 6/m m m','I 4/m m m',
        'P 4/m m m','F m m m','I m m m','A m m m','B m m m','C m m m','P m m m','I 2/m','C 2/m','P 2/m','P -1','C -1']
    Inst = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Instrument Parameters'))[0]
    Limits = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Limits'))[1]
    if 'T' in Inst['Type'][0]:
        difC = Inst['difC'][1]
        dmin = G2lat.Pos2dsp(Inst,Limits[0])
    else:   #'C', 'B', or 'PKS'
        wave = G2mth.getWave(Inst)
        dmin = G2lat.Pos2dsp(Inst,Limits[1])
    
    def SetLattice(controls):
        ibrav = bravaisSymb.index(controls[5])
        if controls[5] in ['Fm3m','Im3m','Pm3m']:
            controls[7] = controls[8] = controls[6]
            controls[9] = controls[10] = controls[11] = 90.
        elif controls[5] in ['R3m','P6/mmm','I4/mmm','P4/mmm']:
            controls[7] = controls[6]
            controls[9] = controls[10] = controls[11] = 90.
            if controls[5] in ['R3-H','P6/mmm']:
                controls[11] = 120.
        elif controls[5] in ['Fmmm','Immm','Ammm','Bmmm','Cmmm','Pmmm']:
            controls[9] = controls[10] = controls[11] = 90.
        elif controls[5] in ['C2/m','P2/m','I2/m']:
            controls[9] = controls[11] = 90.  # b unique
        controls[12] = G2lat.calc_V(G2lat.cell2A(controls[6:12]))
        return ibrav
        
    def OnNcNo(event):
        controls[2] = NcNo.GetValue()
        
    def OnIfX20(event):
        G2frame.ifX20 = x20.GetValue()
        
    def OnBravais(event):
        Obj = event.GetEventObject()
        bravais[bravList.index(Obj.GetId())] = Obj.GetValue()
#        wx.CallAfter(UpdateUnitCellsGrid,G2frame,data)
                
    def OnZeroVar(event):
        controls[0] = zeroVar.GetValue()
        
    def OnSSopt(event):
        if controls[5] in ['Fm3m','Im3m','Pm3m']:
            SSopt.SetValue(False)
            G2frame.ErrorDialog('Cubic lattice','Incommensurate superlattice not possible with a cubic lattice')
            return
        ssopt['Use'] = SSopt.GetValue()
        if 'ssSymb' not in ssopt:
            ssopt.update({'ssSymb':'(abg)','ModVec':[0.1,0.1,0.1],'maxH':1})
        wx.CallAfter(UpdateUnitCellsGrid,G2frame,data)
        
    def OnSelMG(event):
        ssopt['ssSymb'] = selMG.GetValue()
        Vec = ssopt['ModVec']
        modS = G2spc.splitSSsym(ssopt['ssSymb'])[0]
        ssopt['ModVec'] = G2spc.SSGModCheck(Vec,modS)[0]
        print (' Selecting: '+controls[13]+ssopt['ssSymb']+ 'maxH:'+str(ssopt['maxH']))
        OnHklShow(event)
        wx.CallAfter(UpdateUnitCellsGrid,G2frame,data)
        
    def OnModVal(invalid,value,tc):
        OnHklShow(tc.event)
        
    def OnMoveMod(event):
        Obj = event.GetEventObject()
        ObjId = Obj.GetId()
        Id,valObj = Indx[ObjId]
        move = Obj.GetValue()*0.01
        Obj.SetValue(0)
        value = min(0.98,max(-0.98,float(valObj.GetValue())+move))
        valObj.SetValue('%.4f'%(value)) 
        ssopt['ModVec'][Id] = value
        OnHklShow(event)
        
    def OnMaxMH(event):
        ssopt['maxH'] = int(maxMH.GetValue())
        print (' Selecting: '+controls[13]+ssopt['ssSymb']+'maxH:'+str(ssopt['maxH']))
        OnHklShow(event)
        
    def OnButton(xpos,ypos):
        modSym = ssopt['ssSymb'].split(')')[0]+')'
        if modSym in ['(a0g)','(a1/2g)']:
            ssopt['ModVec'][0] = xpos
            ssopt['ModVec'][2] = ypos
        elif modSym in ['(0bg)','(1/2bg)']:
            ssopt['ModVec'][1] = xpos
            ssopt['ModVec'][2] = ypos
        elif modSym in ['(ab0)','(ab1/2)']:
            ssopt['ModVec'][0] = xpos
            ssopt['ModVec'][1] = ypos
        vec = ssopt['ModVec']
        print(' Trying: %s %s modulation vector = %.3f %.3f %.3f'%(controls[13],ssopt['ssSymb'],vec[0],vec[1],vec[2]))
        OnHklShow(None)
        wx.CallAfter(UpdateUnitCellsGrid,G2frame,data)
        
    def OnFindOneMV(event):
        Peaks = np.copy(peaks[0])
        print (' Trying: ',controls[13],ssopt['ssSymb'], ' maxH: 1')
        dlg = wx.ProgressDialog('Elapsed time','Modulation vector search',
            style = wx.PD_ELAPSED_TIME|wx.PD_AUTO_HIDE)
        try:
            ssopt['ModVec'],result = G2indx.findMV(Peaks,controls,ssopt,Inst,dlg)
            if len(result[0]) == 2:
                G2plt.PlotXYZ(G2frame,result[2],1./result[3],labelX='a',labelY='g',
                    newPlot=True,Title='Modulation vector search',buttonHandler=OnButton)
        finally:
            dlg.Destroy()
        OnHklShow(event)
        wx.CallAfter(UpdateUnitCellsGrid,G2frame,data)
        
    def OnFindMV(event):
        best = 1.
        bestSS = ''
        for ssSym in ssChoice:
            ssopt['ssSymb'] = ssSym            
            Peaks = np.copy(peaks[0])
            ssopt['ModVec'] = G2spc.SSGModCheck(ssopt['ModVec'],G2spc.splitSSsym(ssSym)[0],True)[0]
            print (' Trying: '+controls[13]+ssSym+ ' maxH: 1')
            ssopt['ModVec'],result = G2indx.findMV(Peaks,controls,ssopt,Inst,dlg=None)
            OnHklShow(event)
            if result[1] < best:
                bestSS = ssSym
                best = result[1]
        ssopt['ssSymb'] = bestSS
        ssopt['ModVec'],result = G2indx.findMV(Peaks,controls,ssopt,Inst,dlg=None)
        if len(result[0]) == 2:
            G2plt.PlotXYZ(G2frame,result[2],1./result[3],labelX='a',labelY='g',
                newPlot=True,Title='Modulation vector search')
        
        wx.CallAfter(UpdateUnitCellsGrid,G2frame,data)
        
    def OnBravSel(event):
        brav = bravSel.GetString(bravSel.GetSelection())
        controls[5] = brav
        controls[13] = SPGlist[brav][0]       
        ssopt['Use'] = False
        wx.CallLater(100,UpdateUnitCellsGrid,G2frame,data)
        
    def OnSpcSel(event):
        controls[13] = spcSel.GetString(spcSel.GetSelection())
        ssopt['SGData'] = G2spc.SpcGroup(controls[13])[1]
        ssopt['Use'] = False
        G2frame.dataWindow.RefineCell.Enable(True)
        OnHklShow(event)
        wx.CallLater(100,UpdateUnitCellsGrid,G2frame,data)
        
    def SetCellValue(Obj,ObjId,value):
        if controls[5] in ['Fm3m','Im3m','Pm3m']:
            controls[6] = controls[7] = controls[8] = value
            controls[9] = controls[10] = controls[11] = 90.0
            Obj.SetValue(controls[6])
        elif controls[5] in ['R3-H','P6/mmm','I4/mmm','P4/mmm']:
            if ObjId == 0:
                controls[6] = controls[7] = value
                Obj.SetValue(controls[6])
            else:
                controls[8] = value
                Obj.SetValue(controls[8])
            controls[9] = controls[10] = controls[11] = 90.0
            if controls[5] in ['R3-H','P6/mmm']:
                controls[11] = 120.
        elif controls[5] in ['Fmmm','Immm','Cmmm','Pmmm']:
            controls[6+ObjId] = value
            Obj.SetValue(controls[6+ObjId])
            controls[9] = controls[10] = controls[11] = 90.0
        elif controls[5] in ['I2/m','C2/m','P2/m']:
            controls[9] = controls[11] = 90.0
            if ObjId != 3:
                controls[6+ObjId] = value
                Obj.SetValue(controls[6+ObjId])
            else:
                controls[10] = value
                Obj.SetValue(controls[10])
        else:
            controls[6+ObjId] = value
            if ObjId < 3:
                Obj.SetValue(controls[6+ObjId])
            else:
                Obj.SetValue(controls[6+ObjId])
        controls[12] = G2lat.calc_V(G2lat.cell2A(controls[6:12]))
        volVal.SetValue("%.3f"%(controls[12]))
        
    def OnMoveCell(event):
        Obj = event.GetEventObject()
        ObjId = cellList.index(Obj.GetId())
        valObj = valDict[Obj.GetId()]
        inc = float(shiftChoices[shiftSel.GetSelection()][:-1])
        move = Obj.GetValue()  # +1 or -1 
        Obj.SetValue(0)
        value = float(valObj.GetValue()) * (1. + move*inc/100.)
        SetCellValue(valObj,ObjId//2,value)
        OnHklShow(event)
        
    def OnExportCells(event):
        pth = G2G.GetExportPath(G2frame)
        dlg = wx.FileDialog(G2frame, 'Choose Indexing Result csv file', pth, '', 
            'indexing result file (*.csv)|*.csv',wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                filename = os.path.splitext(filename)[0]+'.csv'
                File = open(filename,'w')
                names = 'M20,X20,Bravais,a,b,c,alpha,beta,gamma,volume\n'
                File.write(names)
                fmt = '%.2f,%d,%s,%.4f,%.4f,%.4f,%.2f,%.2f,%.2f,%.3f\n'
                for cell in cells:
                    File.write(fmt%(cell[0],cell[1],bravaisSymb[cell[2]], cell[3],cell[4],cell[5], cell[6],cell[7],cell[8],cell[9]))
                File.close()
        finally:
            dlg.Destroy()
        
    def OnCellChange(invalid,value,tc):
        if invalid:
            return
        SetCellValue(tc,Info[tc.GetId()],value)
        OnHklShow(tc.event)
        wx.CallAfter(UpdateUnitCellsGrid,G2frame,data)
        
    def OnHklShow(event):
        PatternId = G2frame.PatternId
        peaks = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Index Peak List'))
        controls,bravais,cells,dminx,ssopt,magcells = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Unit Cells List'))
        # recompute dmin in case limits were changed
        Inst = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Instrument Parameters'))[0]
        Limits = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Limits'))[1]
        if 'T' in Inst['Type'][0]:
            dmin = G2lat.Pos2dsp(Inst,Limits[0])
        else:
            dmin = G2lat.Pos2dsp(Inst,Limits[1])
        cell = controls[6:12]
        A = G2lat.cell2A(cell)
        spc = controls[13]
        SGData = ssopt.get('SGData',G2spc.SpcGroup(spc)[1])
        Symb = SGData['SpGrp']
        M20 = X20 = 0.
        if ssopt.get('Use',False) and ssopt.get('ssSymb',''):
            SSGData = G2spc.SSpcGroup(SGData,ssopt['ssSymb'])[1]
            if SSGData is None:
                SSGData = G2spc.SSpcGroup(SGData,ssopt['ssSymb'][:-1])[1]     #skip trailing 's' for mag.
            Symb = SSGData['SSpGrp']
            Vec = ssopt['ModVec']
            maxH = ssopt['maxH']
            G2frame.HKL = G2pwd.getHKLMpeak(dmin,Inst,SGData,SSGData,Vec,maxH,A)
            if len(peaks[0]):            
                peaks = [G2indx.IndexSSPeaks(peaks[0],G2frame.HKL)[1],peaks[1]]   #keep esds from peak fit
                M20,X20 = G2indx.calc_M20SS(peaks[0],G2frame.HKL)
        else:
            G2frame.HKL = G2pwd.getHKLpeak(dmin,SGData,A,Inst)
            if len(peaks[0]):
                peaks = [G2indx.IndexPeaks(peaks[0],G2frame.HKL)[1],peaks[1]]   #keep esds from peak fit
                M20,X20 = G2indx.calc_M20(peaks[0],G2frame.HKL)
        G2frame.HKL = np.array(G2frame.HKL)
        if len(G2frame.HKL):
            print (' new M20,X20: %.2f %d, fraction found: %.3f for %s'  \
                %(M20,X20,float(len(peaks[0]))/len(G2frame.HKL),Symb))
        G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Index Peak List'),peaks)
        if 'PKS' in G2frame.GPXtree.GetItemText(G2frame.PatternId):
            G2plt.PlotPowderLines(G2frame)
        else:
            G2plt.PlotPatterns(G2frame)
            
    def OnSortCells(event):
        controls,bravais,cells,dminx,ssopt,magcells = G2frame.GPXtree.GetItemPyData(UnitCellsId)
        c =  event.GetCol()
        if colLabels[c] == 'M20':
            cells = G2indx.sortM20(cells)
        elif colLabels[c] in ['X20','Bravais','a','b','c','alpha','beta','gamma','Volume']:
            if c == 1:
                c += 1  #X20 before Use
            cells = G2indx.sortCells(cells,c-1)     #an extra column (Use) not in cells
        else:
            return
        data = [controls,bravais,cells,dmin,ssopt,magcells]
        G2frame.GPXtree.SetItemPyData(UnitCellsId,data)
        wx.CallAfter(UpdateUnitCellsGrid,G2frame,data)
        
    def CopyUnitCell(event):
        controls,bravais,cells,dminx,ssopt,magcells = G2frame.GPXtree.GetItemPyData(UnitCellsId)
        controls = controls[:5]+10*[0.,]
        if len(cells):
            for Cell in cells:
                if Cell[-2]:
                    break
            cell = Cell[2:9]
            controls[4] = 1
            controls[5] = bravaisSymb[cell[0]]
            controls[6:13] = cell[1:8]
            controls[13] = spaceGroups[bravaisSymb.index(controls[5])]
            G2frame.dataWindow.RefineCell.Enable(True)
        elif magcells:
            for phase in magcells:
                if phase['Use']:
                    break
            SGData = phase['SGData']
            controls[4] = 1
            controls[5] = (SGData['SGLatt']+SGData['SGLaue']).replace('-','')
            if controls[5][1:] == 'm3': controls[5] += 'm'
            if 'P3' in controls[5] or 'P-3' in controls[5]: controls[5] = 'P6/mmm'
            if 'R' in controls[5]: controls[5] = 'R3-H'
            controls[6:13] = phase['Cell']
            controls[13] = SGData['SpGrp']
            ssopt['SGData'] = SGData
        data = [controls,bravais,cells,dminx,ssopt,magcells]
        G2frame.dataWindow.RunSubGroups.Enable(True)
        G2frame.GPXtree.SetItemPyData(UnitCellsId,data)
        OnHklShow(None)
        wx.CallAfter(UpdateUnitCellsGrid,G2frame,data)

    def LoadUnitCell(event):
        '''Called in response to a Load Phase menu command'''
        UnitCellsId = G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Unit Cells List')
        data = G2frame.GPXtree.GetItemPyData(UnitCellsId)
        if len(data) < 5:
            data.append({})
        controls,bravais,cells,dminx,ssopt = data[:5]
        magcells = []           #clear away old mag cells list (if any)
        controls = controls[:14]+[['0','0','0',' ',' ',' '],[],]
        data = controls,bravais,cells,dminx,ssopt,magcells
        G2frame.GPXtree.SetItemPyData(UnitCellsId,data)
        pId = G2gd.GetGPXtreeItemId(G2frame,G2frame.root, 'Phases')
        if not pId: return
        Phases = []
        item, cookie = G2frame.GPXtree.GetFirstChild(pId)
        while item:
            pName = G2frame.GPXtree.GetItemText(item)
            Phase = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,pId,pName))
            if not Phase['General']['SGData'].get('SGFixed',False):
                Phases.append(G2frame.GPXtree.GetItemText(item))
            item, cookie = G2frame.GPXtree.GetNextChild(pId, cookie)
        if not len(Phases):
                wx.MessageBox('NB: Magnetic phases from mcif files are not suitable for this purpose,\n because of space group symbol - operators mismatches',
                    caption='No usable space groups',style=wx.ICON_EXCLAMATION)
                return
        elif len(Phases) == 1: # don't ask questions when there is only 1 answer
            pNum = 0
        else:
            pNum = G2G.ItemSelector(Phases,G2frame,'Select phase',header='Phase')
        if pNum is None: return
        Phase = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,pId,Phases[pNum]))
        Phase['magPhases'] = G2frame.GPXtree.GetItemText(G2frame.PatternId)    #use as reference for recovering possible phases
        Cell = Phase['General']['Cell']
        SGData.update(Phase['General']['SGData'])
        if 'SGGray' not in SGData:
            SGData['SGGray'] = False
        if Phase['General']['Type'] == 'nuclear' and 'MagSpGrp' in SGData:
            SGData.update(G2spc.SpcGroup(SGData['SpGrp'])[1])
        G2frame.dataWindow.RunSubGroups.Enable(True)
        ssopt.update({'Use':False,'ssSymb':'(abg)','ModVec':[0.1,0.1,0.1],'maxH':1})
        if 'SuperSg' in Phase['General'] or SGData.get('SGGray',False):
            ssopt.update({'SGData':SGData,'ssSymb':Phase['General']['SuperSg'],'ModVec':Phase['General']['SuperVec'][0],'Use':True,'maxH':1})
            ssopt['ssSymb'] = ssopt['ssSymb'].replace(',','')
            ssSym = ssopt['ssSymb']
            if SGData.get('SGGray',False):
                ssSym = ssSym[:-1]
            if ssSym not in G2spc.SSChoice(SGData):
                ssSym = ssSym.split(')')[0]+')000'
                ssopt['ssSymb'] = ssSym
                wx.MessageBox('Super space group '+SGData['SpGrp']+ssopt['ssSymb']+' not valid;\n It is set to '+ssSym,
                    caption='Unusable super space group',style=wx.ICON_EXCLAMATION)
            G2frame.dataWindow.RunSubGroups.Enable(False)
        SpGrp = SGData['SpGrp']
        if 'mono' in SGData['SGSys']:
            SpGrp = G2spc.fixMono(SpGrp)
            if SpGrp == None:
                wx.MessageBox('Monoclinic '+SGData['SpGrp']+' not usable here',caption='Unusable space group',style=wx.ICON_EXCLAMATION)
                return
        controls[13] = SpGrp
        controls[4] = 1
        controls[5] = (SGData['SGLatt']+SGData['SGLaue']).replace('-','')
        if controls[5][1:] == 'm3': controls[5] += 'm'
        if controls[5] in ['P3','P3m1','P31m','P6/m']: controls[5] = 'P6/mmm'
        if controls[5] in ['P4/m',]: controls[5] = 'P4/mmm'
        if 'R' in controls[5]: controls[5] = 'R3-H'
        controls[6:13] = Cell[1:8]
        cx,ct,cs,cia = Phase['General']['AtomPtrs']
        controls[15] = [atom[:cx+3] for atom in Phase['Atoms']]
        if 'N' in Inst['Type'][0]:
            if not ssopt.get('Use',False):
                G2frame.dataWindow.RunSubGroupsMag.Enable(True)
        data = controls,bravais,cells,dminx,ssopt,magcells
        G2frame.GPXtree.SetItemPyData(UnitCellsId,data)
        G2frame.dataWindow.RefineCell.Enable(True)
        OnHklShow(None)
        wx.CallAfter(UpdateUnitCellsGrid,G2frame,data)
        
    def ImportUnitCell(event):
        controls,bravais,cells,dminx,ssopt = G2frame.GPXtree.GetItemPyData(UnitCellsId)[:5]
        reqrdr = G2frame.dataWindow.ReImportMenuId.get(event.GetId())
        rdlist = G2frame.OnImportGeneric(reqrdr,
            G2frame.ImportPhaseReaderlist,'phase')
        if len(rdlist) == 0: return
        rd = rdlist[0]
        Cell = rd.Phase['General']['Cell']
        SGData = rd.Phase['General']['SGData']
        if '1 1' in SGData['SpGrp']:
            wx.MessageBox('Unusable space group',caption='Monoclinic '+SGData['SpGrp']+' not usable here',style=wx.ICON_EXCLAMATION)
            return
        controls[4] = 1
        controls[5] = (SGData['SGLatt']+SGData['SGLaue']).replace('-','')
        if controls[5][1:] == 'm3': controls[5] += 'm'
        if 'P3' in controls[5] or 'P-3' in controls[5]: controls[5] = 'P6/mmm'
        if 'R' in controls[5]: controls[5] = 'R3-H'
        controls[6:13] = Cell[1:8]
        controls[13] = SGData['SpGrp']
#        G2frame.GPXtree.SetItemPyData(UnitCellsId,[controls,bravais,cells,dmin,ssopt])
#        G2frame.dataWindow.RunSubGroups.Enable(True)
        G2frame.dataWindow.RefineCell.Enable(True)
        OnHklShow(None)
        wx.CallAfter(UpdateUnitCellsGrid,G2frame,data)
                
    def RefineCell(event):
        
        def cellPrint(ibrav,A):
            cell = G2lat.A2cell(A)
            Vol = G2lat.calc_V(A)
            if ibrav in ['Fm3m','Im3m','Pm3m']:
                print (" %s%10.6f" % ('a =',cell[0]))
            elif ibrav in ['R3-H','P6/mmm','I4/mmm','P4/mmm']:
                print (" %s%10.6f %s%10.6f %s%12.3f" % ('a =',cell[0],' c =',cell[2],' volume =',Vol))
            elif ibrav in ['P4/mmm','Fmmm','Immm','Ammm','Bmmm','Cmmm','Pmmm']:
                print (" %s%10.6f %s%10.6f %s%10.6f %s%12.3f" % ('a =',cell[0],'b =',cell[1],'c =',cell[2],' volume =',Vol))
            elif ibrav in ['C2/m','P2/m']:
                print (" %s%10.6f %s%10.6f %s%10.6f %s%8.3f %s%12.3f" % ('a =',cell[0],'b =',cell[1],'c =',cell[2],'beta =',cell[4],' volume =',Vol))
            else:
                print (" %s%10.6f %s%10.6f %s%10.6f" % ('a =',cell[0],'b =',cell[1],'c =',cell[2]))
                print (" %s%8.3f %s%8.3f %s%8.3f %s%12.3f" % ('alpha =',cell[3],'beta =',cell[4],'gamma =',cell[5],' volume =',Vol))
                
        def vecPrint(Vec):
            print (' %s %10.5f %10.5f %10.5f'%('Modulation vector:',Vec[0],Vec[1],Vec[2]))
             
        PatternId = G2frame.PatternId
        peaks = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Index Peak List'))
        print (' Refine cell')
        controls,bravais,cells,dminx,ssopt,magcells = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Unit Cells List'))
        cell = controls[6:12]
        A = G2lat.cell2A(cell)
        ibrav = bravaisSymb.index(controls[5])
#        if not controls[13]: controls[13] = SPGlist[controls[5]][0]    #don't know if this is needed?   
        SGData = G2spc.SpcGroup(controls[13])[1]
        if 'T' in Inst['Type'][0]:
            if ssopt.get('Use',False):
                vecFlags = [True if x in ssopt['ssSymb'] else False for x in ['a','b','g']]
                SSGData = G2spc.SSpcGroup(SGData,ssopt['ssSymb'])[1]
                G2frame.HKL = G2pwd.getHKLMpeak(dmin,Inst,SGData,SSGData,ssopt['ModVec'],ssopt['maxH'],A)
                peaks = [G2indx.IndexSSPeaks(peaks[0],G2frame.HKL)[1],peaks[1]]   #put peak fit esds back in peaks
                Lhkl,M20,X20,Aref,Vec,Zero = \
                    G2indx.refinePeaksTSS(peaks[0],difC,Inst,SGData,SSGData,ssopt['maxH'],ibrav,A,ssopt['ModVec'],vecFlags,controls[1],controls[0])
            else:
                G2frame.HKL = G2pwd.getHKLpeak(dmin,SGData,A,Inst)
                peaks = [G2indx.IndexPeaks(peaks[0],G2frame.HKL)[1],peaks[1]]   #put peak fit esds back in peaks
                Lhkl,M20,X20,Aref,Zero = G2indx.refinePeaksT(peaks[0],difC,ibrav,A,controls[1],controls[0])            
        else:   
            if ssopt.get('Use',False):
                vecFlags = [True if x in ssopt['ssSymb'] else False for x in ['a','b','g']]
                SSGData = G2spc.SSpcGroup(SGData,ssopt['ssSymb'])[1]
                G2frame.HKL = G2pwd.getHKLMpeak(dmin,Inst,SGData,SSGData,ssopt['ModVec'],ssopt['maxH'],A)
                peaks = [G2indx.IndexSSPeaks(peaks[0],G2frame.HKL)[1],peaks[1]]   #put peak fit esds back in peaks
                Lhkl,M20,X20,Aref,Vec,Zero = \
                    G2indx.refinePeaksZSS(peaks[0],wave,Inst,SGData,SSGData,ssopt['maxH'],ibrav,A,ssopt['ModVec'],vecFlags,controls[1],controls[0])
            else:
                G2frame.HKL = G2pwd.getHKLpeak(dmin,SGData,A,Inst)
                peaks = [G2indx.IndexPeaks(peaks[0],G2frame.HKL)[1],peaks[1]]   #put peak fit esds back in peaks
                Lhkl,M20,X20,Aref,Zero = G2indx.refinePeaksZ(peaks[0],wave,ibrav,A,controls[1],controls[0])
        controls[1] = Zero
        controls[6:12] = G2lat.A2cell(Aref)
        controls[12] = G2lat.calc_V(Aref)
        cells = G2frame.GPXtree.GetItemPyData(UnitCellsId)[2]
        for cell in cells:
            cell[-2] = False
        cells.insert(0,[M20,X20,ibrav]+controls[6:13]+[True,False])
        if ssopt.get('Use',False):
            ssopt['ModVec'] = Vec
            G2frame.HKL = G2pwd.getHKLMpeak(dmin,Inst,SGData,SSGData,ssopt['ModVec'],ssopt['maxH'],A)
        else:
            G2frame.HKL = G2pwd.getHKLpeak(dmin,SGData,A,Inst)
        G2frame.HKL = np.array(G2frame.HKL)
        data = [controls,bravais,cells,dmin,ssopt,magcells]
        G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Unit Cells List'),data)
        print (" %s%10.3f" % ('refinement M20 = ',M20))
        print (' unindexed lines = %d'%X20)
        cellPrint(controls[5],Aref)
        ip = 4
        if ssopt.get('Use',False):
            vecPrint(Vec)
            ip = 5
        for hkl in G2frame.HKL:
            hkl[ip] = G2lat.Dsp2pos(Inst,hkl[ip-1])+controls[1]
        G2frame.HKL = np.array(G2frame.HKL)
        if 'PKS' in G2frame.GPXtree.GetItemText(G2frame.PatternId):
            G2plt.PlotPowderLines(G2frame)
        else:
            G2plt.PlotPatterns(G2frame)
        wx.CallAfter(UpdateUnitCellsGrid,G2frame,data)
        
    def OnIndexPeaks(event):
        PatternId = G2frame.PatternId    
        print ('Peak Indexing')
        keepcells = []
        try:
            controls,bravais,cells,dminx,ssopt,magcells = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Unit Cells List'))
            for cell in cells:
                if cell[11]:
                    cell[10] = False    #clear selection flag on keepers
                    keepcells.append(cell)
        except IndexError:
            pass
        except ValueError:
            G2frame.ErrorDialog('Error','Need to set controls in Unit Cell List first')
            return
        if ssopt.get('Use',False):
            G2frame.ErrorDialog('Super lattice error','Indexing not available for super lattices')
            return
        if True not in bravais:
            G2frame.ErrorDialog('Error','No Bravais lattices selected')
            return
        if not len(peaks[0]):
            G2frame.ErrorDialog('Error','Index Peak List is empty')
            return
        if len(peaks[0][0]) > 9:
            G2frame.ErrorDialog('Error','You need to reload Index Peaks List first')
            return
        G2frame.dataWindow.CopyCell.Enable(False)
        G2frame.dataWindow.RefineCell.Enable(False)
        dlg = wx.ProgressDialog("Generated reflections",'0 '+" cell search for "+bravaisNames[ibrav],101, 
#            style = wx.PD_ELAPSED_TIME|wx.PD_AUTO_HIDE|wx.PD_REMAINING_TIME|wx.PD_CAN_SKIP|wx.PD_CAN_ABORT) #desn't work in 32 bit versions
            style = wx.PD_ELAPSED_TIME|wx.PD_AUTO_HIDE|wx.PD_REMAINING_TIME|wx.PD_CAN_ABORT)
        try:
            OK,dmin,newcells = G2indx.DoIndexPeaks(peaks[0],controls,bravais,dlg,G2frame.ifX20)
        finally:
            dlg.Destroy()
        cells = keepcells+newcells
        cells = G2indx.sortM20(cells)
        if OK:
            cells[0][10] = True         #select best M20
            data = [controls,bravais,cells,dmin,ssopt,magcells]
            G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Unit Cells List'),data)
            bestCell = cells[0]
            if bestCell[0] > 10.:
                G2frame.HKL = G2lat.GenHBravais(dmin,bestCell[2],G2lat.cell2A(bestCell[3:9]))
                for hkl in G2frame.HKL:
                    hkl.insert(4,G2lat.Dsp2pos(Inst,hkl[3])+controls[1])
                G2frame.HKL = np.array(G2frame.HKL)
                if 'PKS' in G2frame.GPXtree.GetItemText(G2frame.PatternId):
                    G2plt.PlotPowderLines(G2frame)
                else:
                    G2plt.PlotPatterns(G2frame)
            G2frame.dataWindow.CopyCell.Enable(True)
            G2frame.dataWindow.IndexPeaks.Enable(True)
            G2frame.dataWindow.MakeNewPhase.Enable(True)
            G2frame.ifX20 = True
            wx.CallAfter(UpdateUnitCellsGrid,G2frame,data)
                
    def RefreshUnitCellsGrid(event):
        'responds when "use" is pressed in index table; generates/plots reflections'
        data = G2frame.GPXtree.GetItemPyData(UnitCellsId)
        cells,dminx = data[2:4]
        r,c =  event.GetRow(),event.GetCol()
        if cells:
            if event.GetEventObject().GetColLabelValue(c) == 'use':
                for i in range(len(cells)):
                    cells[i][-2] = False
                    UnitCellsTable.SetValue(i,c,False)
                UnitCellsTable.SetValue(r,c,True)
                gridDisplay.ForceRefresh()
                cells[r][-2] = True
                ibrav = cells[r][2]
                A = G2lat.cell2A(cells[r][3:9])
                G2frame.HKL = G2lat.GenHBravais(dmin,ibrav,A)
                for hkl in G2frame.HKL:
                    hkl.insert(4,G2lat.Dsp2pos(Inst,hkl[3])+controls[1])
                G2frame.HKL = np.array(G2frame.HKL)
                if 'PKS' in G2frame.GPXtree.GetItemText(G2frame.PatternId):
                    G2plt.PlotPowderLines(G2frame)
                else:
                    G2plt.PlotPatterns(G2frame)
            elif event.GetEventObject().GetColLabelValue(c) == 'Keep':
                if UnitCellsTable.GetValue(r,c):
                    UnitCellsTable.SetValue(r,c,False)
                    cells[r][c] = False
                else:
                    cells[r][c] = True
                    UnitCellsTable.SetValue(r,c,True)
                gridDisplay.ForceRefresh()
            G2frame.GPXtree.SetItemPyData(UnitCellsId,data)
        
    KeyList = []
    
    def ClearCurrentShowNext():
        KeepShowNext(False)
        
    KeyList += [['j',ClearCurrentShowNext,'Show next Mag. Spc. Group, clear keep flag on current']]        
    
    def KeepCurrentShowNext():
        KeepShowNext(True)
        
    KeyList += [['k',KeepCurrentShowNext,'Show next Mag. Spc. Group, keep current']]
        
    def KeepShowNext(KeepCurrent=True):
        '''Show next "keep" item in Magnetic Space Group list, possibly resetting the 
        keep flag for the current displayed cell
        '''
        for i in range(len(magcells)): # find plotted setting
            if magcells[i]['Use']: break
        else:
            return # no Try is set
        if not KeepCurrent:  # clear current
            magcells[i]['Keep'] = False
            MagCellsTable.SetValue(i,2,False)
        keeps = [j for j in range(i+1,len(magcells)) if magcells[j]['Keep']]
        if not keeps:
            if not KeepCurrent: magDisplay.ForceRefresh()
            return # no remaining Keep-flagged entries
        next = keeps[0]
        # update table
        magcells[i]['Use'] = False
        MagCellsTable.SetValue(i,1,False)
        magcells[next]['Use'] = True
        MagCellsTable.SetValue(next,1,True)
        # get SG info and plot
        SGData = magcells[next]['SGData']
        A = G2lat.cell2A(magcells[next]['Cell'][:6])  
        G2frame.HKL = G2pwd.getHKLpeak(1.0,SGData,A,Inst)
        G2plt.PlotPatterns(G2frame,extraKeys=KeyList)
        magDisplay.ForceRefresh()
        # change Scroll to display new setting
        xscroll = G2frame.dataWindow.GetScrollPos(wx.HORIZONTAL)
        yscroll = magDisplay.CellToRect(next,1)[1]/G2frame.dataWindow.GetScrollPixelsPerUnit()[1]
        G2frame.dataWindow.Scroll(xscroll,yscroll)
        
    def RefreshMagCellsGrid(event):
        controls,bravais,cells,dminx,ssopt,magcells = G2frame.GPXtree.GetItemPyData(UnitCellsId)
        r,c =  event.GetRow(),event.GetCol()
        rLab = magDisplay.GetRowLabelValue(r)
        br = baseList[r]
        phase = phaseDict[br]
        pname = '(%s) %s'%(rLab,phase['Name'])
        if magcells:
            if c == 0:
                mSGData = phase['SGData']
                text,table = G2spc.SGPrint(mSGData,AddInv=True)
                if 'magAtms' in phase:
                    msg = 'Magnetic space group information'
                    text[0] = ' Magnetic Space Group: '+mSGData['MagSpGrp']
                    text[3] = ' The magnetic lattice point group is '+mSGData['MagPtGp']
                    OprNames,SpnFlp = G2spc.GenMagOps(mSGData)
                    G2G.SGMagSpinBox(G2frame.dataWindow,msg,text,table,mSGData['SGCen'],OprNames,
                        mSGData['SpnFlp'],False).Show()
                else:
                    msg = 'Space Group Information'
                    G2G.SGMessageBox(G2frame.dataWindow,msg,text,table).Show()
            elif c == 1:
                for i in range(len(magcells)):
                    magcells[i]['Use'] = False
                for i in range(len(baseList)):
                    MagCellsTable.SetValue(i,c,False)
                MagCellsTable.SetValue(r,c,True)
                magDisplay.ForceRefresh()
                phase['Use'] = True
                mSGData = phase['SGData']
                A = G2lat.cell2A(phase['Cell'][:6])  
                G2frame.HKL = G2pwd.getHKLpeak(1.0,mSGData,A,Inst)
                G2plt.PlotPatterns(G2frame,extraKeys=KeyList)
            elif c == 2:
                if MagCellsTable.GetValue(r,c):
                    MagCellsTable.SetValue(r,c,False)
                    phase['Keep'] = False
                else:
                    phase['Keep'] = True
                    MagCellsTable.SetValue(r,c,True)
                magDisplay.ForceRefresh()
            elif c ==3:
                maxequiv = magcells[0].get('maxequiv',100)
                mSGData = phase['SGData']
                Uvec = phase['Uvec']
                Trans = phase['Trans']
                ifMag = False
                if 'magAtms' in phase:
                    ifMag = True
                    allmom = phase.get('allmom',False)
                    magAtms = phase.get('magAtms','')
                    mAtoms = TestMagAtoms(phase,magAtms,SGData,Uvec,Trans,allmom,maxequiv)
                else:
                    mAtoms = TestAtoms(phase,controls[15],SGData,Uvec,Trans,maxequiv)
                Atms = []
                AtCods = []
                atMxyz = []
                for ia,atom in enumerate(mAtoms):
                    atom[0] += '_%d'%ia
                    SytSym,Mul,Nop,dupDir = G2spc.SytSym(atom[2:5],mSGData)
                    Atms.append(atom[:2]+['',]+atom[2:5])
                    AtCods.append('1')
                    if 'magAtms' in phase:
                        MagSytSym = G2spc.MagSytSym(SytSym,dupDir,mSGData)
                        CSI = G2spc.GetCSpqinel(mSGData['SpnFlp'],dupDir)
                        atMxyz.append([MagSytSym,CSI[0]])
                    else:
                        CSI = G2spc.GetCSxinel(SytSym)
                        atMxyz.append([SytSym,CSI[0]])
                G2phsG.UseMagAtomDialog(G2frame,pname,Atms,AtCods,atMxyz,ifMag=ifMag,ifOK=True).ShowModal()
            elif c in [4,5]:
                if 'altList' not in phase: return
                if c == 4:
                    title = 'Conjugacy list for '+pname
                    items = phase['altList']
                    
                elif c == 5:
                    title = 'Super groups list for '+pname
                    items = phase['supList']
                    if not items[0]:
                        wx.MessageBox(pname+' is a maximal subgroup',caption='Super group is parent',style=wx.ICON_INFORMATION)
                        return
                    
                SubCellsDialog(G2frame,title,controls,SGData,items,phaseDict).ShowModal()
                
            data = [controls,bravais,cells,dminx,ssopt,magcells]
            G2frame.GPXtree.SetItemPyData(UnitCellsId,data)
            
    def OnRefreshKeep(event):
        controls,bravais,cells,dminx,ssopt,magcells = G2frame.GPXtree.GetItemPyData(UnitCellsId)
        c =  event.GetCol()
        E,SGData = G2spc.SpcGroup(controls[13])
        if c == 2:
            testAtoms = ['',]+list(set([atom[1] for atom in controls[15]]))
            ifMag = False
            maxequiv = magcells[0]['maxequiv']
            maximal = False
            if 'magAtms' in magcells[0]:
                ifMag = True
                allmom = magcells[0]['allmom']
                magAtms = magcells[0]['magAtms']
                dlg = G2G.MultiDataDialog(G2frame,title='Keep options',
                    prompts=['max unique','test for mag. atoms','all have moment','only maximal subgroups',],
                    values=[maxequiv,'',allmom,False],limits=[[1,100],testAtoms,[True,False],[True,False]],
                    formats=['%d','choice','bool','bool'])
            else:
                dlg = G2G.MultiDataDialog(G2frame,title='Keep options',
                    prompts=['max unique','only maximal subgroups',],
                    values=[maxequiv,False],limits=[[1,100],[True,False],],
                    formats=['%d','bool',])
            if dlg.ShowModal() == wx.ID_OK:
                if ifMag:
                    maxequiv,atype,allmom,maximal = dlg.GetValues()
                    magAtms = [atom for atom in controls[15] if atom[1] == atype]
                else:
                    maxequiv,maximal = dlg.GetValues()
            dlg = wx.ProgressDialog('Setting Keep flags','Processing '+magcells[0]['Name'],len(magcells), 
                style = wx.PD_ELAPSED_TIME|wx.PD_AUTO_HIDE|wx.PD_REMAINING_TIME)
            for ip,phase in enumerate(magcells):
                dlg.Update(ip,newmsg='Processing '+phase['Name'])
                Uvec = phase['Uvec']
                Trans = phase['Trans']
                if ifMag:
                    phase['nAtoms'] = len(TestMagAtoms(phase,magAtms,SGData,Uvec,Trans,allmom,maxequiv,maximal))
                else:
                    phase['nAtoms'] = len(TestAtoms(phase,controls[15],SGData,Uvec,Trans,maxequiv,maximal))
            dlg.Destroy()
            data = controls,bravais,cells,dminx,ssopt,magcells
            G2frame.GPXtree.SetItemPyData(UnitCellsId,data)
            wx.CallAfter(UpdateUnitCellsGrid,G2frame,data)
        
    def MakeNewPhase(event):
        if not G2gd.GetGPXtreeItemId(G2frame,G2frame.root,'Phases'):
            sub = G2frame.GPXtree.AppendItem(parent=G2frame.root,text='Phases')
        else:
            sub = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,'Phases')
        PhaseName = ''
        dlg = wx.TextEntryDialog(None,'Enter a name for this phase','Phase Name Entry','New phase',
            style=wx.OK)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                PhaseName = dlg.GetValue()
                cells = G2frame.GPXtree.GetItemPyData(UnitCellsId)[2]
                for Cell in cells:
                    if Cell[-2]:
                        break
                cell = Cell[2:10]        
                sub = G2frame.GPXtree.AppendItem(parent=sub,text=PhaseName)
                E,SGData = G2spc.SpcGroup(controls[13])
                G2frame.GPXtree.SetItemPyData(sub, \
                    G2obj.SetNewPhase(Name=PhaseName,SGData=SGData,cell=cell[1:],Super=ssopt))
                G2frame.GetStatusBar().SetStatusText('Change space group from '+str(controls[13])+' if needed',1)
        finally:
            dlg.Destroy()
            
    def OnMagSel(event):
        Obj = event.GetEventObject()
        if Obj.GetValue():
            SGData['SGSpin'] = [1,]*len(SGData['SGSpin'])
            GenSym,GenFlg,BNSsym = G2spc.GetGenSym(SGData)
            SGData['GenSym'] = GenSym
            SGData['GenFlg'] = GenFlg
            OprNames,SpnFlp = G2spc.GenMagOps(SGData)
            SGData['SpnFlp'] = SpnFlp
            SGData['MagSpGrp'] = G2spc.MagSGSym(SGData)
        else:
            del SGData['MagSpGrp']
        ssopt['SGData'] = SGData
        OnHklShow(None)
        wx.CallAfter(UpdateUnitCellsGrid,G2frame,data)
            
    def OnSpinOp(event):
        Obj = event.GetEventObject()
        isym = Indx[Obj.GetId()]+1
        spCode = {'red':-1,'black':1}                    
        SGData['SGSpin'][isym] = spCode[Obj.GetValue()]
        G2spc.CheckSpin(isym,SGData)
        GenSym,GenFlg,BNSsym = G2spc.GetGenSym(SGData)
        SGData['GenSym'] = GenSym
        SGData['GenFlg'] = GenFlg
        OprNames,SpnFlp = G2spc.GenMagOps(SGData)
        SGData['SpnFlp'] = SpnFlp
        SGData['MagSpGrp'] = G2spc.MagSGSym(SGData)
        OnHklShow(None)
        
    def OnBNSlatt(event):
        Obj = event.GetEventObject()
        SGData.update(G2spc.SpcGroup(SGData['SpGrp'])[1])
        BNSlatt = Obj.GetValue()
        if '_' in BNSlatt:
            SGData['BNSlattsym'] = [BNSlatt,BNSsym[BNSlatt]]
        else:
            SGData['BNSlattsym'] = [SGData['SGLatt'],[0.,0.,0.]]
        SGData['SGSpin'] = [1,]*len(SGData['SGSpin'])
        GenSym,GenFlg = G2spc.GetGenSym(SGData)[:2]
        SGData['GenSym'] = GenSym
        SGData['GenFlg'] = GenFlg
        SGData['MagSpGrp'] = G2spc.MagSGSym(SGData)
        G2spc.ApplyBNSlatt(SGData,SGData['BNSlattsym'])
        OprNames,SpnFlp = G2spc.GenMagOps(SGData)
        SGData['SpnFlp'] = SpnFlp
        OnHklShow(None)
            
    def OnShowSpins(event):
        msg = 'Magnetic space group information'
        text,table = G2spc.SGPrint(SGData,AddInv=True)
        text[0] = ' Magnetic Space Group: '+SGData['MagSpGrp']
        text[3] = ' The magnetic lattice point group is '+SGData['MagPtGp']
        G2G.SGMagSpinBox(G2frame.dataWindow,msg,text,table,SGData['SGCen'],OprNames,
            SGData['SpnFlp'],False).Show()
        
    def TransformUnitCell(event):
        Trans = np.eye(3)
        Uvec = np.zeros(3)
        Vvec = np.zeros(3)
        ifMag = False
        Type = 'nuclear'
        BNSlatt = ''
        E,SGData = G2spc.SpcGroup(controls[13])
        phase = {'General':{'Name':'','Type':Type,'Cell':['',]+controls[6:13],'SGData':SGData}}
        dlg = G2phsG.TransformDialog(G2frame,phase,Trans,Uvec,Vvec,ifMag,BNSlatt)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                newPhase,Trans,Uvec,Vvec,ifMag,ifConstr,Common = dlg.GetSelection()
                sgData = newPhase['General']['SGData']
                controls[5] = sgData['SGLatt']+sgData['SGLaue']
                controls[13] = sgData['SpGrp']
                ssopt['SGData'] = sgData
                controls[6:13] = newPhase['General']['Cell'][1:8]
            else:
                return
        finally:
            dlg.Destroy()
        OnHklShow(None)
        wx.CallAfter(UpdateUnitCellsGrid,G2frame,data)
        
    def OnLatSym(event):
        'Run Bilbao PsuedoLattice cell search'
        # look up a space group matching Bravais lattice (should not matter which one) 
        bravaisSPG = {'Fm3m':225,'Im3m':229,'Pm3m':221,'R3-H':146,'P6/mmm':191,
                       'I4/mmm':139,'P4/mmm':123,'Fmmm':69,'Immm':71,
                       'Cmmm':65,'Pmmm':47,'C2/m':12,'P2/m':10,'P1':2}
        pUCid = G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Unit Cells List')
        controls,bravais,cells,dminx,ssopt,magcells = G2frame.GPXtree.GetItemPyData(pUCid)
        sgNum = bravaisSPG.get(controls[5],0)
        if sgNum < 1:
            wx.MessageBox('Sorry, only standard cell settings are allowed, please transform axes',caption='Bilbao requires standard settings',style=wx.ICON_EXCLAMATION)
            return
        cell = controls[6:12]
        tolerance = 5.
        dlg = G2G.SingleFloatDialog(G2frame,'Tolerance',
                'Enter angular tolerance for search',5.0,[.1,30.],"%.1f")
        if dlg.ShowModal() == wx.ID_OK:
            tolerance = dlg.GetValue()
            dlg.Destroy()    
        else:
            dlg.Destroy()    
            return
        import SUBGROUPS as kSUB
        wx.BeginBusyCursor()
        wx.MessageBox(''' For use of PSEUDOLATTICE, please cite:
      Bilbao Crystallographic Server I: Databases and crystallographic computing programs,
      M. I. Aroyo, J. M. Perez-Mato, C. Capillas, E. Kroumova, S. Ivantchev, G. Madariaga, A. Kirov & H. Wondratschek
      Z. Krist. 221, 1, 15-27 (2006). 
      doi: https://doi.org/doi:10.1524/zkri.2006.221.1.15''', 
        caption='Bilbao PSEUDOLATTICE',style=wx.ICON_INFORMATION)
        page = kSUB.subBilbaoCheckLattice(sgNum,cell,tolerance)
        wx.EndBusyCursor()
        if not page: return
#        while cells: cells.pop() # cells.clear() is much cleaner but not Py2
        for i,(cell,mat) in enumerate(kSUB.parseBilbaoCheckLattice(page)):
            cells.append([])
            cells[-1] += [mat,0,16]
            cells[-1] += cell
            cells[-1] += [G2lat.calc_V(G2lat.cell2A(cell)),False,False]            
        G2frame.GPXtree.SetItemPyData(pUCid,data)
        G2frame.OnFileSave(event)
        wx.CallAfter(UpdateUnitCellsGrid,G2frame,data)
        
    def OnRunSubs(event):
        import SUBGROUPS as kSUB
        G2frame.dataWindow.RunSubGroupsMag.Enable(False)
        pUCid = G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Unit Cells List')
        controls,bravais,cells,dminx,ssopt,magcells = G2frame.GPXtree.GetItemPyData(pUCid)
        E,SGData = G2spc.SpcGroup(controls[13])
        Kx = [' ','0','1/2','-1/2','1/3','-1/3','2/3','1']
        Ky = [' ','0','1/2','1/3','2/3','1']
        Kz = [' ','0','1/2','3/2','1/3','2/3','1']
        kvec = [['0','0','0'],[' ',' ',' '],[' ',' ',' ',' ']]
        dlg = G2G.MultiDataDialog(G2frame,title='SUBGROUPS options',prompts=[' k-vector 1',' k-vector 2',' k-vector 3', \
            ' Use whole star',' Filter by','preserve axes','max unique'],
            values=kvec+[False,'',True,100],
            limits=[[Kx[1:],Ky[1:],Kz[1:]],[Kx,Ky,Kz],[Kx,Ky,Kz],[True,False],['',' Landau transition',' Only maximal subgroups',],
                [True,False],[1,100]],
            formats=[['choice','choice','choice'],['choice','choice','choice'],['choice','choice','choice'],'bool','choice',
                    'bool','%d',])
        if dlg.ShowModal() == wx.ID_OK:
            magcells = []
            newVals = dlg.GetValues()
            kvec[:9] = newVals[0]+newVals[1]+newVals[2]+[' ',]
            nkvec = kvec.index(' ')
            star = newVals[3]
            filterby = newVals[4]
            keepaxes = newVals[5]
            maxequiv = newVals[6]
            if 'maximal' in filterby:
                maximal = True
                Landau = False
            elif 'Landau' in filterby:
                maximal = False
                Landau = True
            else:
                maximal = False
                Landau = False            
            if nkvec not in [0,3,6,9]:
                wx.MessageBox('Error: check your propagation vector(s)',
                    caption='Bilbao SUBGROUPS setup error',style=wx.ICON_EXCLAMATION)
                return
            if nkvec in [6,9] and Landau:
                wx.MessageBox('Error, multi k-vectors & Landau not compatible',
                    caption='Bilbao SUBGROUPS setup error',style=wx.ICON_EXCLAMATION)
                return
            wx.BeginBusyCursor()
            wx.MessageBox(''' For use of SUBGROUPS, please cite:
      Symmetry-Based Computational Tools for Magnetic Crystallography,
      J.M. Perez-Mato, S.V. Gallego, E.S. Tasci, L. Elcoro, G. de la Flor, and M.I. Aroyo
      Annu. Rev. Mater. Res. 2015. 45,217-48.
      doi: https://doi.org/10.1146/annurev-matsci-070214-021008''',caption='Bilbao SUBGROUPS',style=wx.ICON_INFORMATION)
            
            SubGroups,baseList = kSUB.GetNonStdSubgroups(SGData,kvec[:9],star,Landau)
#            SUBGROUPS,baseList = kMAG.GetNonStdSubgroups(SGData,kvec[:9],star,Landau,maximal)
            wx.EndBusyCursor()
            if SubGroups is None:
                wx.MessageBox('Check your internet connection?',caption='Bilbao SUBGROUPS error',style=wx.ICON_EXCLAMATION)
                return
            if not SubGroups:
                if Landau:
                    wx.MessageBox('No results from SUBGROUPS, multi k-vectors & Landau not compatible',
                        caption='Bilbao SUBGROUPS error',style=wx.ICON_EXCLAMATION)
                else:
                    wx.MessageBox('No results from SUBGROUPS, check your propagation vector(s)',
                        caption='Bilbao SUBGROUPS error',style=wx.ICON_EXCLAMATION)
                return
            controls[14] = kvec[:9]
            try:
                controls[16] = baseList
            except IndexError:
                controls.append(baseList)
            dlg = wx.ProgressDialog('SUBGROUPS results','Processing '+SubGroups[0][0],len(SubGroups), 
                style = wx.PD_ELAPSED_TIME|wx.PD_AUTO_HIDE|wx.PD_REMAINING_TIME)
            for ir,result in enumerate(SubGroups):
                dlg.Update(ir,newmsg='Processing '+result[0])
                Trans = np.array(eval(result[1][0]))
                Uvec = np.array(eval(result[1][1]))
                phase = G2lat.makeBilbaoPhase(result,Uvec,Trans)
                phase['gid'] = result[2]
                phase['altList'] = result[3]
                phase['supList'] = eval(result[4])
                RVT = None
                if keepaxes:
                    RVT = G2lat.FindNonstandard(controls,phase)
                if RVT is not None:
                    result,Uvec,Trans = RVT
                phase.update(G2lat.makeBilbaoPhase(result,Uvec,Trans))
                phase['Cell'] = G2lat.TransformCell(controls[6:12],Trans)   
                phase['maxequiv'] = maxequiv
                phase['nAtoms'] = len(TestAtoms(phase,controls[15],SGData,Uvec,Trans,maxequiv,maximal))
                magcells.append(phase)
            dlg.Destroy()
            magcells[0]['Use'] = True
            SGData = magcells[0]['SGData']
            A = G2lat.cell2A(magcells[0]['Cell'][:6])  
            G2frame.HKL = G2pwd.getHKLpeak(1.0,SGData,A,Inst)
            G2plt.PlotPatterns(G2frame,extraKeys=KeyList)
        data = [controls,bravais,cells,dmin,ssopt,magcells]
        G2frame.GPXtree.SetItemPyData(pUCid,data)
        G2frame.OnFileSave(event)
        wx.CallAfter(UpdateUnitCellsGrid,G2frame,data)
        
    def OnRunSubsMag(event):
        import SUBGROUPS as kSUB
        G2frame.dataWindow.RunSubGroups.Enable(False)
        pUCid = G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Unit Cells List')
        controls,bravais,cells,dminx,ssopt,magcells = G2frame.GPXtree.GetItemPyData(pUCid)
        E,SGData = G2spc.SpcGroup(controls[13])
        try:
            atoms = list(set([atom[1] for atom in controls[15]]))
        except:
            wx.MessageBox('Error: Problem with phase. Use Load Phase 1st.',
                    caption='k-SUBGROUPSMAG setup error: Phase loaded?',style=wx.ICON_EXCLAMATION)
            return
        testAtoms = ['',]+[atom for atom in atoms if len(G2elem.GetMFtable([atom,],[2.0,]))]
        Kx = [' ','0','1/2','-1/2','1/3','-1/3','2/3','1']
        Ky = [' ','0','1/2','1/3','2/3','1']
        Kz = [' ','0','1/2','3/2','1/3','2/3','1']
        kvec = [['0','0','0'],[' ',' ',' '],[' ',' ',' ',' ']]
        dlg = G2G.MultiDataDialog(G2frame,title='k-SUBGROUPSMAG options',prompts=[' k-vector 1',' k-vector 2',' k-vector 3', \
            ' Use whole star',' Filter by','preserve axes','test for mag. atoms','all have moment','max unique'],
            values=kvec+[False,'',True,'',False,100],
            limits=[[Kx[1:],Ky[1:],Kz[1:]],[Kx,Ky,Kz],[Kx,Ky,Kz],[True,False],['',' Landau transition',' Only maximal subgroups',],
                [True,False],testAtoms,[True,False],[1,100]],
            formats=[['choice','choice','choice'],['choice','choice','choice'],['choice','choice','choice'],'bool','choice',
                    'bool','choice','bool','%d',])
        if dlg.ShowModal() == wx.ID_OK:
            magcells = []
            newVals = dlg.GetValues()
            kvec[:9] = newVals[0]+newVals[1]+newVals[2]+[' ',]
            nkvec = kvec.index(' ')
            star = newVals[3]
            filterby = newVals[4]
            keepaxes = newVals[5]
            atype = newVals[6]
            allmom = newVals[7]
            maxequiv = newVals[8]
            if 'maximal' in filterby:
                maximal = True
                Landau = False
            elif 'Landau' in filterby:
                maximal = False
                Landau = True
            else:
                maximal = False
                Landau = False            
            if nkvec not in [0,3,6,9]:
                wx.MessageBox('Error: check your propagation vector(s)',
                    caption='Bilbao k-SUBGROUPSMAG setup error',style=wx.ICON_EXCLAMATION)
                return
            if nkvec in [6,9] and Landau:
                wx.MessageBox('Error, multi k-vectors & Landau not compatible',
                    caption='Bilbao k-SUBGROUPSMAG setup error',style=wx.ICON_EXCLAMATION)
                return
            magAtms = [atom for atom in controls[15] if atom[1] == atype]
            wx.BeginBusyCursor()
            wx.MessageBox(''' For use of k-SUBGROUPSMAG, please cite:
      Symmetry-Based Computational Tools for Magnetic Crystallography,
      J.M. Perez-Mato, S.V. Gallego, E.S. Tasci, L. Elcoro, G. de la Flor, and M.I. Aroyo
      Annu. Rev. Mater. Res. 2015. 45,217-48.
      doi: https://doi.org/10.1146/annurev-matsci-070214-021008''',caption='Bilbao k-SUBGROUPSMAG',style=wx.ICON_INFORMATION)
            
            MAXMAGN,baseList = kSUB.GetNonStdSubgroupsmag(SGData,kvec[:9],star,Landau)
            wx.EndBusyCursor()
            if MAXMAGN is None:
                wx.MessageBox('Check your internet connection?',caption='Bilbao k-SUBGROUPSMAG error',style=wx.ICON_EXCLAMATION)
                return
            if not MAXMAGN:
                if Landau:
                    wx.MessageBox('No results from k-SUBGROUPSMAG, multi k-vectors & Landau not compatible',
                        caption='Bilbao k-SUBGROUPSMAG error',style=wx.ICON_EXCLAMATION)
                else:
                    wx.MessageBox('No results from k-SUBGROUPSMAG, check your propagation vector(s)',
                        caption='Bilbao k-SUBGROUPSMAG error',style=wx.ICON_EXCLAMATION)
                return
            controls[14] = kvec[:9]
            try:
                controls[16] = baseList
            except IndexError:
                controls.append(baseList)
            dlg = wx.ProgressDialog('k-SUBGROUPSMAG results','Processing '+MAXMAGN[0][0],len(MAXMAGN), 
                style = wx.PD_ELAPSED_TIME|wx.PD_AUTO_HIDE|wx.PD_REMAINING_TIME)
            
            for ir,result in enumerate(MAXMAGN):
                # result is SPGP,BNS,MV,itemList,altList,superList
                dlg.Update(ir,newmsg='Processing '+result[0])
                Trans = np.array(eval(result[2][0]))
                Uvec = np.array(eval(result[2][1]))
                phase = G2lat.makeBilbaoPhase(result[:2],Uvec,Trans,True)
                phase['gid'] = result[3]
                phase['altList'] = result[4]
                phase['supList'] = eval(result[5])
                RVT = None
                if keepaxes:
                    RVT = G2lat.FindNonstandard(controls,phase)
                if RVT is not None:
                    result,Uvec,Trans = RVT
                phase.update(G2lat.makeBilbaoPhase(result,Uvec,Trans,True))
                phase['Cell'] = G2lat.TransformCell(controls[6:12],Trans)   
                phase['aType'] = atype
                phase['allmom'] = allmom
                phase['magAtms'] = magAtms
                phase['maxequiv'] = maxequiv
                phase['nAtoms'] = len(TestMagAtoms(phase,magAtms,SGData,Uvec,Trans,allmom,maxequiv,maximal))
                magcells.append(phase)
            dlg.Destroy()
            magcells[0]['Use'] = True
            SGData = magcells[0]['SGData']
            A = G2lat.cell2A(magcells[0]['Cell'][:6])  
            G2frame.HKL = G2pwd.getHKLpeak(1.0,SGData,A,Inst)
            G2plt.PlotPatterns(G2frame,extraKeys=KeyList)
        data = [controls,bravais,cells,dmin,ssopt,magcells]
        G2frame.GPXtree.SetItemPyData(pUCid,data)
        G2frame.OnFileSave(event)
        wx.CallAfter(UpdateUnitCellsGrid,G2frame,data)
        
    G2gd.SetDataMenuBar(G2frame,G2frame.dataWindow.IndexMenu)
    G2frame.GetStatusBar().SetStatusText('')
    G2frame.Bind(wx.EVT_MENU, OnIndexPeaks, id=G2G.wxID_INDEXPEAKS)
    G2frame.Bind(wx.EVT_MENU, OnRunSubs, id=G2G.wxID_RUNSUB)
    G2frame.Bind(wx.EVT_MENU, OnRunSubsMag, id=G2G.wxID_RUNSUBMAG)
    G2frame.Bind(wx.EVT_MENU, OnLatSym, id=G2G.wxID_LATSYM)
    G2frame.Bind(wx.EVT_MENU, CopyUnitCell, id=G2G.wxID_COPYCELL)
    G2frame.Bind(wx.EVT_MENU, LoadUnitCell, id=G2G.wxID_LOADCELL)
    G2frame.Bind(wx.EVT_MENU, ImportUnitCell, id=G2G.wxID_IMPORTCELL)
    G2frame.Bind(wx.EVT_MENU, TransformUnitCell, id=G2G.wxID_TRANSFORMCELL)
    G2frame.Bind(wx.EVT_MENU, RefineCell, id=G2G.wxID_REFINECELL)
    G2frame.Bind(wx.EVT_MENU, MakeNewPhase, id=G2G.wxID_MAKENEWPHASE)
    G2frame.Bind(wx.EVT_MENU, OnExportCells, id=G2G.wxID_EXPORTCELLS)
        
    if len(data) < 6:
        data.append([])
    controls,bravais,cells,dminx,ssopt,magcells = data
    if len(controls) < 13:              #add cell volume if missing
        controls.append(G2lat.calc_V(G2lat.cell2A(controls[6:12])))
    if len(controls) < 14:              #add space group if missing
        controls.append(spaceGroups[bravaisSymb.index(controls[5])])
    if len(controls) < 15:
        controls.append(list(range(1,len(magcells)+1)))
    while len(bravais) < 17:
        bravais += [0,]
    SGData = ssopt.get('SGData',G2spc.SpcGroup(controls[13])[1])
    G2frame.GPXtree.SetItemPyData(UnitCellsId,data)            #update with volume
    bravaisNames = ['Cubic-F','Cubic-I','Cubic-P','Trigonal-R','Trigonal/Hexagonal-P',
        'Tetragonal-I','Tetragonal-P','Orthorhombic-F','Orthorhombic-I','Orthorhombic-A',
        'Orthorhombic-B','Orthorhombic-C','Orthorhombic-P',
        'Monoclinic-I','Monoclinic-C','Monoclinic-P','Triclinic','Triclinic',]
    cellGUIlist = [[[0,1,2],4,zip([" Unit cell: a = "," Vol = "],[(10,5),"%.3f"],[True,False],[0,0])],
    [[3,4,5,6],6,zip([" Unit cell: a = "," c = "," Vol = "],[(10,5),(10,5),"%.3f"],[True,True,False],[0,2,0])],
    [[7,8,9,10,11,12],8,zip([" Unit cell: a = "," b = "," c = "," Vol = "],[(10,5),(10,5),(10,5),"%.3f"],
        [True,True,True,False],[0,1,2,0])],
    [[13,14,15],10,zip([" Unit cell: a = "," b = "," c = "," beta = "," Vol = "],
        [(10,5),(10,5),(10,5),(10,3),"%.3f"],[True,True,True,True,False],[0,1,2,4,0])],
    [[16,17],8,zip([" Unit cell: a = "," b = "," c = "," alpha = "," beta = "," gamma = "," Vol = "],
        [(10,5),(10,5),(10,5),(10,3),(10,3),(10,3),"%.3f"],
        [True,True,True,True,True,True,False],[0,1,2,3,4,5,0])]]
    
    G2frame.dataWindow.IndexPeaks.Enable(False)
    peaks = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Index Peak List'))
    if peaks:
        G2frame.dataWindow.IndexPeaks.Enable(True)
    G2frame.dataWindow.RefineCell.Enable(False)
    if controls[12] > 1.0 and len(peaks[0]):             #if a "real" volume (i.e. not default) and peaks
        G2frame.dataWindow.RefineCell.Enable(True)    
    G2frame.dataWindow.CopyCell.Enable(False)
    G2frame.dataWindow.MakeNewPhase.Enable(False)        
    G2frame.dataWindow.ExportCells.Enable(False)
    if cells:
        G2frame.dataWindow.CopyCell.Enable(True)
        G2frame.dataWindow.MakeNewPhase.Enable(True)
        G2frame.dataWindow.ExportCells.Enable(True)
    elif magcells:
        G2frame.dataWindow.CopyCell.Enable(True)        
    if G2gd.GetGPXtreeItemId(G2frame,G2frame.root, 'Phases'):
        G2frame.dataWindow.LoadCell.Enable(True)
    G2frame.dataWindow.ClearData()
    mainSizer = G2frame.dataWindow.GetSizer()
    mainSizer.Add(wx.StaticText(parent=G2frame.dataWindow,label=' Indexing controls: '),0,WACV)
    mainSizer.Add((5,5),0)
    littleSizer = wx.FlexGridSizer(0,5,5,5)
    littleSizer.Add(wx.StaticText(parent=G2frame.dataWindow,label=' Max Nc/Nobs '),0,WACV)
    NcNo = wx.SpinCtrl(G2frame.dataWindow)
    NcNo.SetRange(2,8)
    NcNo.SetValue(controls[2])
    NcNo.Bind(wx.EVT_SPINCTRL,OnNcNo)
    littleSizer.Add(NcNo,0,WACV)
    littleSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Start Volume '),0,WACV)
    startVol = G2G.ValidatedTxtCtrl(G2frame.dataWindow,controls,3,typeHint=int,xmin=25)
    littleSizer.Add(startVol,0,WACV)
    x20 = wx.CheckBox(G2frame.dataWindow,label='Use M20/(X20+1)?')
    x20.SetValue(G2frame.ifX20)
    x20.Bind(wx.EVT_CHECKBOX,OnIfX20)
    littleSizer.Add(x20,0,WACV)
    mainSizer.Add(littleSizer,0)
    mainSizer.Add((5,5),0)
    mainSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Select Bravais Lattices for indexing: '),
        0,WACV)
    mainSizer.Add((5,5),0)
    littleSizer = wx.FlexGridSizer(0,5,5,5)
    bravList = []
    bravs = zip(bravais,bravaisNames)
    for brav,bravName in bravs:
        bravCk = wx.CheckBox(G2frame.dataWindow,label=bravName)
        bravList.append(bravCk.GetId())
        bravCk.SetValue(brav)
        bravCk.Bind(wx.EVT_CHECKBOX,OnBravais)
        littleSizer.Add(bravCk,0,WACV)
    mainSizer.Add(littleSizer,0)
    mainSizer.Add((-1,10),0)
    
    littleSizer = wx.BoxSizer(wx.HORIZONTAL)
    littleSizer.Add(wx.StaticText(parent=G2frame.dataWindow,label=' Cell Test && Refinement: '),0,WACV)
    littleSizer.Add((5,5),0)
    hklShow = wx.Button(G2frame.dataWindow,label="Show hkl positions")
    hklShow.Bind(wx.EVT_BUTTON,OnHklShow)
    littleSizer.Add(hklShow,0,WACV)    
    littleSizer.Add(wx.StaticText(G2frame.dataWindow,label=' cell step ',style=wx.ALIGN_RIGHT),0,WACV|wx.ALIGN_RIGHT)
    shiftChoices = [ '0.01%','0.05%','0.1%','0.5%', '1.0%','2.5%','5.0%']
    shiftSel = wx.Choice(G2frame.dataWindow,choices=shiftChoices)
    shiftSel.SetSelection(3)
    littleSizer.Add(shiftSel)
    mainSizer.Add(littleSizer,0)
    
    mainSizer.Add((5,5),0)
    littleSizer = wx.BoxSizer(wx.HORIZONTAL)
    littleSizer.Add(wx.StaticText(G2frame.dataWindow,label=" Bravais  \n lattice ",style=wx.ALIGN_CENTER),0,WACV,5)
    bravSel = wx.Choice(G2frame.dataWindow,choices=bravaisSymb,size=(75,-1))
    bravSel.SetSelection(bravaisSymb.index(controls[5]))
    bravSel.Bind(wx.EVT_CHOICE,OnBravSel)
    littleSizer.Add(bravSel,0,WACV)
    littleSizer.Add(wx.StaticText(G2frame.dataWindow,label=" Space  \n group  ",style=wx.ALIGN_CENTER),0,WACV,5)
    spcSel = wx.Choice(G2frame.dataWindow,choices=SPGlist[controls[5]],size=(100,-1))
    try:
        spcSel.SetSelection(SPGlist[controls[5]].index(controls[13]))
    except ValueError:
        pass
    spcSel.Bind(wx.EVT_CHOICE,OnSpcSel)
    littleSizer.Add(spcSel,0,WACV)
    if ssopt.get('Use',False):        #zero for super lattice doesn't work!
        controls[0] = False
    else:
        littleSizer.Add(wx.StaticText(G2frame.dataWindow,label=" Zero offset "),0,WACV)
        zero = G2G.ValidatedTxtCtrl(G2frame.dataWindow,controls,1,nDig=(10,4),typeHint=float,
                                    xmin=-5.,xmax=5.,size=(50,-1))
        littleSizer.Add(zero,0,WACV)
        zeroVar = wx.CheckBox(G2frame.dataWindow,label="Refine?")
        zeroVar.SetValue(controls[0])
        zeroVar.Bind(wx.EVT_CHECKBOX,OnZeroVar)
        littleSizer.Add(zeroVar,0,WACV)
    SSopt = wx.CheckBox(G2frame.dataWindow,label="Modulated?")
    SSopt.SetValue(ssopt.get('Use',False))
    SSopt.Bind(wx.EVT_CHECKBOX,OnSSopt)
    littleSizer.Add(SSopt,0,WACV)
    if 'N' in Inst['Type'][0]:
        MagSel = wx.CheckBox(G2frame.dataWindow,label="Magnetic?")
        MagSel.SetValue('MagSpGrp' in SGData)
        MagSel.Bind(wx.EVT_CHECKBOX,OnMagSel)
        littleSizer.Add(MagSel,0,WACV)
    mainSizer.Add(littleSizer,0)
    mainSizer.Add((5,5),0)
    if 'N' in Inst['Type'][0]:
        neutSizer = wx.BoxSizer(wx.HORIZONTAL)
        if 'MagSpGrp' in SGData:
            Indx = {}
            GenSym,GenFlg,BNSsym = G2spc.GetGenSym(SGData)
            SGData['GenSym'] = GenSym
            SGData['SGGray'] = False
            neutSizer.Add(wx.StaticText(G2frame.dataWindow,label=' BNS lattice: '),0,WACV)
            BNSkeys = [SGData['SGLatt'],]+list(BNSsym.keys())
            BNSkeys.sort()
            try:        #this is an ugly kluge - bug in wx.ComboBox
                if SGData['BNSlattsym'][0][2] in ['a','b','c']:
                    BNSkeys.reverse()
            except:
                pass
            BNS = wx.ComboBox(G2frame.dataWindow,value=SGData['BNSlattsym'][0],
                choices=BNSkeys,style=wx.CB_READONLY|wx.CB_DROPDOWN)
            BNS.Bind(wx.EVT_COMBOBOX,OnBNSlatt)
            neutSizer.Add(BNS,0,WACV)
            spinColor = ['black','red']
            spCode = {-1:'red',1:'black'}
            for isym,sym in enumerate(GenSym[1:]):
                neutSizer.Add(wx.StaticText(G2frame.dataWindow,label=' %s: '%(sym.strip())),0,WACV)                
                spinOp = wx.ComboBox(G2frame.dataWindow,value=spCode[SGData['SGSpin'][isym+1]],choices=spinColor,
                    style=wx.CB_READONLY|wx.CB_DROPDOWN)                
                Indx[spinOp.GetId()] = isym
                spinOp.Bind(wx.EVT_COMBOBOX,OnSpinOp)
                neutSizer.Add(spinOp,0,WACV)
            OprNames,SpnFlp = G2spc.GenMagOps(SGData)
            SGData['SpnFlp'] = SpnFlp
            showSpins = wx.Button(G2frame.dataWindow,label=' Show spins?')
            showSpins.Bind(wx.EVT_BUTTON,OnShowSpins)
            neutSizer.Add(showSpins,0,WACV)
        mainSizer.Add(neutSizer,0)
        mainSizer.Add((5,5),0)
    ibrav = SetLattice(controls)
    for cellGUI in cellGUIlist:
        if ibrav in cellGUI[0]:
            useGUI = cellGUI
    cellList = []
    valDict = {}
    Info = {}
    littleSizer = wx.FlexGridSizer(0,min(6,useGUI[1]),5,5)
    for txt,fmt,ifEdit,Id in useGUI[2]:
        littleSizer.Add(wx.StaticText(G2frame.dataWindow,label=txt,style=wx.ALIGN_RIGHT),0,WACV|wx.ALIGN_RIGHT)
        if ifEdit:          #a,b,c,etc.
            cellVal = G2G.ValidatedTxtCtrl(G2frame.dataWindow,controls,6+Id,nDig=fmt,OnLeave=OnCellChange)
            Info[cellVal.GetId()] = Id
            valSizer = wx.BoxSizer(wx.HORIZONTAL)
            valSizer.Add(cellVal,0,WACV)
            cellSpin = wx.SpinButton(G2frame.dataWindow,style=wx.SP_VERTICAL,size=wx.Size(20,20))
            cellSpin.SetValue(0)
            cellSpin.SetRange(-1,1)
            cellSpin.Bind(wx.EVT_SPIN, OnMoveCell)
            valSizer.Add(cellSpin,0,WACV)
            littleSizer.Add(valSizer,0,WACV)
            cellList.append(cellVal.GetId())
            cellList.append(cellSpin.GetId())
            valDict[cellSpin.GetId()] = cellVal
        else:               #volume
            volVal = wx.TextCtrl(G2frame.dataWindow,value=(fmt%(controls[12])),style=wx.TE_READONLY)
            volVal.SetBackgroundColour(VERY_LIGHT_GREY)
            littleSizer.Add(volVal,0,WACV)
        
    mainSizer.Add(littleSizer,0)
    if ssopt.get('Use',False):        #super lattice display
        indChoice = ['1','2','3','4',]
        if 'MagSpGrp' in SGData:    #limit to one for magnetic SS for now
            indChoice = ['1',]
        SpSg = controls[13]
        SGData = G2spc.SpcGroup(SpSg)[1]
        ssChoice = G2spc.SSChoice(SGData)
        if ssopt['ssSymb'] not in ssChoice:
            ssopt['ssSymb'] = ssopt['ssSymb'][:-1]
        ssSizer = wx.BoxSizer(wx.HORIZONTAL)
        ssSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Supersymmetry space group: '+SpSg+' '),0,WACV)
        selMG = wx.ComboBox(G2frame.dataWindow,value=ssopt['ssSymb'],
                choices=ssChoice,style=wx.CB_READONLY|wx.CB_DROPDOWN)
        selMG.Bind(wx.EVT_COMBOBOX, OnSelMG)
        ssSizer.Add(selMG,0,WACV)
        ssSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Mod. vector: '),0,WACV)
        modS = G2spc.splitSSsym(ssopt['ssSymb'])[0]
        ssopt['ModVec'],ifShow = G2spc.SSGModCheck(ssopt['ModVec'],modS)
        Indx = {}
        for i,[val,show] in enumerate(zip(ssopt['ModVec'],ifShow)):
            if show:
                valSizer = wx.BoxSizer(wx.HORIZONTAL)
                modVal = G2G.ValidatedTxtCtrl(G2frame.dataWindow,ssopt['ModVec'],i,
                    xmin=-.98,xmax=.98,nDig=(10,4),typeHint=float,OnLeave=OnModVal)
                valSizer.Add(modVal,0,WACV)
                modSpin = wx.SpinButton(G2frame.dataWindow,style=wx.SP_VERTICAL,size=wx.Size(20,20))
                modSpin.SetValue(0)
                modSpin.SetRange(-1,1)
                modSpin.Bind(wx.EVT_SPIN, OnMoveMod)
                valSizer.Add(modSpin,0,WACV)
                ssSizer.Add(valSizer,0,WACV)
                Indx[modVal.GetId()] = i
                Indx[modSpin.GetId()] = [i,modVal]
            else:
                modVal = wx.TextCtrl(G2frame.dataWindow,value=('%.3f'%(val)),
                    size=wx.Size(50,20),style=wx.TE_READONLY)
                modVal.SetBackgroundColour(VERY_LIGHT_GREY)
                ssSizer.Add(modVal,0,WACV)
        ssSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Max. M: '),0,WACV)
        maxMH = wx.ComboBox(G2frame.dataWindow,value=str(ssopt['maxH']),
            choices=indChoice,style=wx.CB_READONLY|wx.CB_DROPDOWN)
        maxMH.Bind(wx.EVT_COMBOBOX, OnMaxMH)
        ssSizer.Add(maxMH,0,WACV)
        findMV = wx.Button(G2frame.dataWindow,label="Find mod. vec.?")
        findMV.Bind(wx.EVT_BUTTON,OnFindOneMV)
        ssSizer.Add(findMV,0,WACV)
        findallMV = wx.Button(G2frame.dataWindow,label="Try all?")
        findallMV.Bind(wx.EVT_BUTTON,OnFindMV)
        ssSizer.Add(findallMV,0,WACV)
        mainSizer.Add(ssSizer,0)

    G2frame.dataWindow.currentGrids = []
    if cells:
        mode = 0
        try: # for Cell sym, 1st entry is cell xform matrix
            len(cells[0][0])
            mode = 1
        except:
            pass
        if mode:
            mainSizer.Add(wx.StaticText(parent=G2frame.dataWindow,label='\n Cell symmetry search:'),0,WACV)
            colLabels = ['use']
            Types = [wg.GRID_VALUE_BOOL]
        else:
            mainSizer.Add(wx.StaticText(parent=G2frame.dataWindow,label='\n Indexing Result:'),0,WACV)
            colLabels = ['M20','X20','use','Bravais']
            Types = [wg.GRID_VALUE_FLOAT+':10,2',wg.GRID_VALUE_NUMBER,
                         wg.GRID_VALUE_BOOL,wg.GRID_VALUE_STRING]
        rowLabels = []
        colLabels += ['a','b','c','alpha','beta','gamma','Volume','Keep']
        Types += (3*[wg.GRID_VALUE_FLOAT+':10,5',]+
                  3*[wg.GRID_VALUE_FLOAT+':10,3',]+
                  [wg.GRID_VALUE_FLOAT+':10,2',wg.GRID_VALUE_BOOL])
        table = []
        for cell in cells:
            rowLabels.append('')
            if mode:
                row = [cell[-2]]+cell[3:10]+[cell[11],]
            else:
                row = cell[0:2]+[cell[-2]]+[bravaisSymb[cell[2]]]+cell[3:10]+[cell[11],]
            if cell[-2]:
                A = G2lat.cell2A(cell[3:9])
                G2frame.HKL = G2lat.GenHBravais(dmin,cell[2],A)
                for hkl in G2frame.HKL:
                    hkl.insert(4,G2lat.Dsp2pos(Inst,hkl[3])+controls[1])
                G2frame.HKL = np.array(G2frame.HKL)
            table.append(row)
        UnitCellsTable = G2G.Table(table,rowLabels=rowLabels,colLabels=colLabels,types=Types)
        gridDisplay = G2G.GSGrid(G2frame.dataWindow)
        gridDisplay.SetTable(UnitCellsTable, True)
        G2frame.dataWindow.CopyCell.Enable(True)
        gridDisplay.Bind(wg.EVT_GRID_CELL_LEFT_CLICK,RefreshUnitCellsGrid)
        gridDisplay.Bind(wg.EVT_GRID_LABEL_LEFT_DCLICK,OnSortCells)
        gridDisplay.SetRowLabelSize(0)
        gridDisplay.AutoSizeColumns(False)
        for r in range(gridDisplay.GetNumberRows()):
            for c in range(gridDisplay.GetNumberCols()):
                if c == 2:
                    gridDisplay.SetReadOnly(r,c,isReadOnly=False)
                else:
                    gridDisplay.SetReadOnly(r,c,isReadOnly=True)
        mainSizer.Add(gridDisplay,0,WACV)
    if magcells and len(controls) > 16:
        itemList = [phase.get('gid',ip+1) for ip,phase in enumerate(magcells)]
        phaseDict = dict(zip(itemList,magcells))
        G2frame.dataWindow.CopyCell.Enable(False)
        kvec1 = ','.join(controls[14][:3])
        kvec2 = ','.join(controls[14][3:6])
        kvec3 = ','.join(controls[14][6:])
        baseList = controls[16]
        if 'magAtms' in magcells[0]:
            G2frame.dataWindow.RunSubGroupsMag.Enable(True)
            Label = '\n Magnetic subgroup cells from Bilbao k-SUBGROUPSMAG for %s; kvec1=(%s)'%(controls[13],kvec1)
        else:
            G2frame.dataWindow.RunSubGroups.Enable(True)
            Label = '\n Subgroup cells from Bilbao SUBGROUPS for %s; kvec1=(%s)'%(controls[13],kvec1)
        if ' ' not in kvec2:
            Label += ', kvec2=(%s)' % kvec2
        if ' ' not in kvec3:
            Label += ', kvec3=(%s)' % kvec3
        Label += ':'
        mainSizer.Add(wx.StaticText(parent=G2frame.dataWindow,label=Label),0,WACV)
        rowLabels = [str(i+1) for i in range(len(baseList))]
        colLabels = ['Space Gp','Try','Keep','Uniq','nConj','nSup','Trans','Vec','a','b','c','alpha','beta','gamma','Volume']
        Types = [wg.GRID_VALUE_STRING,]+2*[wg.GRID_VALUE_BOOL,]+3*[wg.GRID_VALUE_LONG,]+2*[wg.GRID_VALUE_STRING,]+ \
            3*[wg.GRID_VALUE_FLOAT+':10,5',]+3*[wg.GRID_VALUE_FLOAT+':10,3',]+[wg.GRID_VALUE_FLOAT+':10,2']
        table = []
        for ip in baseList:
            phase = phaseDict[ip]
            natms = phase.get('nAtoms',1)
            try:
                nConj = len(phase['altList'])
                nSup = len(phase['supList'])
            except KeyError:
                nConj = 0
                nSup = 0
            cell  = list(phase['Cell'])
            trans = G2spc.Trans2Text(phase['Trans'])
            vec = G2spc.Latt2text([phase['Uvec'],])
            row = [phase['Name'],phase['Use'],phase['Keep'],natms,nConj,nSup,trans,vec]+cell
            table.append(row)
        MagCellsTable = G2G.Table(table,rowLabels=rowLabels,colLabels=colLabels,types=Types)
        G2frame.GetStatusBar().SetStatusText(
                'Double click Keep to refresh Keep flags; click Space Gp to see sym. ops., Uniq to see unique atoms list; Try to trigger K & J keys on plot',1)
        magDisplay = G2G.GSGrid(G2frame.dataWindow)
        magDisplay.SetTable(MagCellsTable, True)
        magDisplay.Bind(wg.EVT_GRID_CELL_LEFT_CLICK,RefreshMagCellsGrid)
        magDisplay.Bind(wg.EVT_GRID_LABEL_LEFT_DCLICK,OnRefreshKeep)
        magDisplay.AutoSizeColumns(False)
        for r in range(magDisplay.GetNumberRows()):
            for c in range(magDisplay.GetNumberCols()):
                if c in [1,2]:
                    magDisplay.SetReadOnly(r,c,isReadOnly=False)
                else:
                    magDisplay.SetReadOnly(r,c,isReadOnly=True)
        mainSizer.Add(magDisplay,0,WACV)
        
    G2frame.dataWindow.SetDataSize()
    
################################################################################
#####  Reflection list
################################################################################           
       
def UpdateReflectionGrid(G2frame,data,HKLF=False,Name=''):
    '''respond to selection of PWDR Reflections data tree item by displaying
    a table of reflections in the data window.
    '''
    Controls = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.root, 'Controls'))
    dMin = 0.05
    if 'UsrReject' in Controls:
        dMin = Controls['UsrReject'].get('MinD',0.05)

    def OnPlot1DHKL(event):
        phaseName = G2frame.RefList
        if phaseName not in ['Unknown',]:
            pId = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,'Phases')
            phaseId =  G2gd.GetGPXtreeItemId(G2frame,pId,phaseName)
            General = G2frame.GPXtree.GetItemPyData(phaseId)['General']
            Super = General.get('Super',0)
        else:
            Super = 0
        if 'list' in str(type(data)):   #single crystal data is 2 dict in list
            refList = data[1]['RefList']
        else:                           #powder data is a dict of dicts; each same structure as SC 2nd dict
            if 'RefList' in data[phaseName]:
                refList = np.array(data[phaseName]['RefList'])
            else:
                wx.MessageBox('No reflection list - do Refine first',caption='Reflection plotting')
                return
        G2plt.Plot1DSngl(G2frame,newPlot=True,hklRef=refList,Super=Super,Title=phaseName)

    def OnPlotHKL(event):
        '''Plots a layer of reflections
        '''
        phaseName = G2frame.RefList
        if phaseName not in ['Unknown',]:
            pId = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,'Phases')
            phaseId =  G2gd.GetGPXtreeItemId(G2frame,pId,phaseName)
            General = G2frame.GPXtree.GetItemPyData(phaseId)['General']
            Super = General.get('Super',0)
            SuperVec = General.get('SuperVec',[])
        else:
            Super = 0
            SuperVec = []       
        if 'list' in str(type(data)):   #single crystal data is 2 dict in list
            refList = data[1]['RefList']
        else:                           #powder data is a dict of dicts; each same structure as SC 2nd dict
            if 'RefList' in data[phaseName]:
                refList = np.array(data[phaseName]['RefList'])
            else:
                wx.MessageBox('No reflection list - do Refine first',caption='Reflection plotting')
                return
        FoMax = np.max(refList.T[8+Super])
        Hmin = np.array([int(np.min(refList.T[0])),int(np.min(refList.T[1])),int(np.min(refList.T[2]))])
        Hmax = np.array([int(np.max(refList.T[0])),int(np.max(refList.T[1])),int(np.max(refList.T[2]))])
        controls = {'Type' : 'Fo','ifFc' : True,'HKLmax' : Hmax,'HKLmin' : Hmin,
            'FoMax' : FoMax,'Zone' : '001','Layer' : 0,'Scale' : 1.0,'Super':Super,'SuperVec':SuperVec}
        G2plt.PlotSngl(G2frame,newPlot=True,Data=controls,hklRef=refList,Title=phaseName)
        
    def OnPlot3DHKL(event):
        '''Plots the reflections in 3D
        '''
        phaseName = G2frame.RefList
        Super = 0
        SuperVec = []
        if phaseName not in ['Unknown',]:
            pId = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,'Phases')
            phaseId =  G2gd.GetGPXtreeItemId(G2frame,pId,phaseName)
            General = G2frame.GPXtree.GetItemPyData(phaseId)['General']
            if General.get('Modulated',False):
                Super = 1
                SuperVec = General['SuperVec']
        if 'list' in str(type(data)):   #single crystal data is 2 dict in list
            refList = data[1]['RefList']
        else:                           #powder data is a dict of dicts; each same structure as SC 2nd dict
            if 'RefList' in data[phaseName]:
                refList = np.array(data[phaseName]['RefList'])
            else:
                wx.MessageBox('No reflection list - do Refine first',caption='Reflection plotting')
                return
        refList.T[3+Super] = np.where(refList.T[4+Super]<dMin,-refList.T[3+Super],refList.T[3+Super])
        FoMax = np.max(refList.T[8+Super])
        Hmin = np.array([int(np.min(refList.T[0])),int(np.min(refList.T[1])),int(np.min(refList.T[2]))])
        Hmax = np.array([int(np.max(refList.T[0])),int(np.max(refList.T[1])),int(np.max(refList.T[2]))])
        Vpoint = np.array([int(np.mean(refList.T[0])),int(np.mean(refList.T[1])),int(np.mean(refList.T[2]))])
        controls = {'Type':'Fosq','Iscale':False,'HKLmax':Hmax,'HKLmin':Hmin,'Zone':False,'viewKey':'L',
            'FoMax' : FoMax,'Scale' : 1.0,'Drawing':{'viewPoint':[Vpoint,[]],'default':Vpoint[:],
            'backColor':[0,0,0],'depthFog':False,'Zclip':10.0,'cameraPos':10.,'Zstep':0.05,'viewUp':[0,1,0],
            'Scale':1.0,'oldxy':[],'viewDir':[0,0,1]},'Super':Super,'SuperVec':SuperVec}
        G2plt.Plot3DSngl(G2frame,newPlot=True,Data=controls,hklRef=refList,Title=phaseName)
        
    def MakeReflectionTable(phaseName):
        '''Returns a wx.grid table (G2G.Table) containing a list of all reflections
        for a phase.        
        '''
        Super = 0
        if phaseName not in ['Unknown',]:
            pId = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,'Phases')
            if pId: # phase section missing from file (unusual)
                phaseId =  G2gd.GetGPXtreeItemId(G2frame,pId,phaseName)
                if phaseId:         #is phase deleted?
                    General = G2frame.GPXtree.GetItemPyData(phaseId)['General']
                    G,g = G2lat.cell2Gmat(General['Cell'][1:7])
                    GA,GB = G2lat.Gmat2AB(G)    #Orthogonalization matricies
                    SGData = General['SGData']
                    if General.get('Modulated',False):
                        Super = 1
                    try:
                        Histograms = G2frame.GPXtree.GetItemPyData(phaseId)['Histograms']
                        histName = G2frame.GPXtree.GetItemText(G2frame.PatternId)
                        histData = Histograms[histName]
                    except:
                        if GSASIIpath.GetConfigValue('debug'):
                            print('Reflection table problem: histogram {} not found in phase {}'.format(histName,phaseName))
                        return
        rowLabels = []
        if HKLF:
            refList = data[1]['RefList']
            refs = refList
        else:
            muStrData = histData['Mustrain']
            sizeData = histData['Size']
            if len(data) > 1:
                G2frame.dataWindow.SelectPhase.Enable(True)
            try:            #patch for old reflection lists
                if not len(data[phaseName]):
                    return None
                refList = np.array(data[phaseName]['RefList'])
                I100 = refList.T[8+Super]*refList.T[11+Super]
            except TypeError:
                refList = np.array([refl[:11+Super] for refl in data[phaseName]])
                I100 = refList.T[8+Super]*np.array([refl[11+Super] for refl in data[phaseName]])
            MuStr = G2pwd.getMustrain(refList.T[:3],G,SGData,muStrData)
            CrSize = G2pwd.getCrSize(refList.T[:3],G,GB,sizeData)
            Imax = np.max(I100)
            if Imax:
                I100 *= 100.0/Imax
            if 'C' in Inst['Type'][0]:
                refs = np.vstack((refList.T[:15+Super],I100,MuStr,CrSize)).T
            elif 'T' in Inst['Type'][0]:
                refs = np.vstack((refList.T[:18+Super],I100,MuStr,CrSize)).T
            elif 'B' in Inst['Type'][0]:
                refs = np.vstack((refList.T[:17+Super],I100,MuStr,CrSize)).T
        rowLabels = [str(i) for i in range(len(refs))]
        Types = (4+Super)*[wg.GRID_VALUE_LONG,]+4*[wg.GRID_VALUE_FLOAT+':10,4',]+ \
            2*[wg.GRID_VALUE_FLOAT+':10,2',]+[wg.GRID_VALUE_FLOAT+':10,3',]+ \
            [wg.GRID_VALUE_FLOAT+':10,3',]
        if HKLF:
            colLabels = ['H','K','L','flag','d','Fosq','sig','Fcsq','FoTsq','FcTsq','phase','ExtC',]
            if 'T' in Inst['Type'][0]:
                colLabels = ['H','K','L','flag','d','Fosq','sig','Fcsq','FoTsq','FcTsq','phase','ExtC','wave','tbar']
                Types += 2*[wg.GRID_VALUE_FLOAT+':10,3',]
            if Super:
                colLabels.insert(3,'M')
        else:
            if 'C' in Inst['Type'][0]:
                colLabels = ['H','K','L','mul','d','pos','sig','gam','Fosq','Fcsq','phase','Icorr','Prfo','Trans','ExtP','I100','mustrain','Size']
                Types += 6*[wg.GRID_VALUE_FLOAT+':10,3',]
            elif 'T' in Inst['Type'][0]:
                colLabels = ['H','K','L','mul','d','pos','sig','gam','Fosq','Fcsq','phase','Icorr','alp','bet','wave','Prfo','Abs','Ext','I100','mustrain','Size']
                Types += 9*[wg.GRID_VALUE_FLOAT+':10,3',]
            elif 'B' in Inst['Type'][0]:
                colLabels = ['H','K','L','mul','d','pos','sig','gam','Fosq','Fcsq','phase','Icorr','alp','bet','Prfo','Abs','Ext','I100','mustrain','Size']
                Types += 8*[wg.GRID_VALUE_FLOAT+':10,3',]
            if Super:
                colLabels.insert(3,'M')
        refs.T[3+Super] = np.where(refs.T[4+Super]<dMin,-refs.T[3+Super],refs.T[3+Super])
        return G2G.Table(refs,rowLabels=rowLabels,colLabels=colLabels,types=Types)

    def ShowReflTable(phaseName):
        '''Posts a table of reflections for a phase, creating the table
        if needed using MakeReflectionTable
        '''
        def setBackgroundColors(im,it):
            for r in range(G2frame.refTable[phaseName].GetNumberRows()):
                if HKLF:
                    if float(G2frame.refTable[phaseName].GetCellValue(r,3+im)) <= 0.:
                        G2frame.refTable[phaseName].SetCellBackgroundColour(r,3+im,wx.RED)
                    Fosq = float(G2frame.refTable[phaseName].GetCellValue(r,5+im))
                    Fcsq = float(G2frame.refTable[phaseName].GetCellValue(r,7+im))
                    sig = float(G2frame.refTable[phaseName].GetCellValue(r,6+im))
                    rat = 11.
                    if sig:
                        rat = abs(Fosq-Fcsq)/sig
                    if  rat > 10.:
                        G2frame.refTable[phaseName].SetCellBackgroundColour(r,7+im,wx.RED)
                    elif rat > 3.0:
                        G2frame.refTable[phaseName].SetCellBackgroundColour(r,7+im,wx.Colour(255,255,0))
                else:   #PWDR
                    if float(G2frame.refTable[phaseName].GetCellValue(r,12+im+itof)) < 0.:
                        G2frame.refTable[phaseName].SetCellBackgroundColour(r,12+im+itof,wx.RED)
                    if float(G2frame.refTable[phaseName].GetCellValue(r,3+im)) < 0:
                        G2frame.refTable[phaseName].SetCellBackgroundColour(r,8+im,wx.RED)
                        
                                                  
        if not HKLF and not len(data[phaseName]):
            return          #deleted phase?
        G2frame.RefList = phaseName
        if HKLF:
            G2frame.GetStatusBar().SetStatusText('abs(DF)/sig > 10 red; > 3 yellow; flag:>0 twin no., 0 sp.gp absent, -1 user rejected, -2 Rfree',1)
        else:
            G2frame.GetStatusBar().SetStatusText('Prfo < 0. in red; if excluded Fosq in red & mul < 0',1)
        itof = 0
        if HKLF:
            im = data[1].get('Super',0)
        else:
            if 'T' in data[phaseName].get('Type',''):
                itof = 3
            im = data[phaseName].get('Super',0)
        # has this table already been displayed?
        if G2frame.refTable[phaseName].GetTable() is None:
            PeakTable = MakeReflectionTable(phaseName)
            if not PeakTable: return
            G2frame.refTable[phaseName].SetTable(PeakTable, True)
            G2frame.refTable[phaseName].EnableEditing(False)
            G2frame.refTable[phaseName].SetMargins(0,0)
            G2frame.refTable[phaseName].AutoSizeColumns(False)
            setBackgroundColors(im,itof)
        if HKLF:
            refList = np.array([refl[:6+im] for refl in data[1]['RefList']])
        else:
            refList = np.array([refl[:6+im] for refl in data[phaseName]['RefList']])
        G2frame.HKL = np.vstack((refList.T)).T    #build for plots
        # raise the tab (needed for 1st use and from OnSelectPhase)
        for PageNum in range(G2frame.refBook.GetPageCount()):
            if phaseName == G2frame.refBook.GetPageText(PageNum):
                G2frame.refBook.SetSelection(PageNum)
                break
        else:
            print (phaseName)
            print (phases)
            raise Exception("how did we not find a phase name?")
        
    def OnPageChanged(event):
        '''Respond to a press on a phase tab by displaying the reflections. This
        routine is needed because the reflection table may not have been created yet.
        '''
        G2frame.refBook.SetSize(G2frame.dataWindow.GetClientSize())    #TODO -almost right
        page = event.GetSelection()
        phaseName = G2frame.refBook.GetPageText(page)
        ShowReflTable(phaseName)

    def OnSelectPhase(event):
        '''For PWDR, selects a phase with a selection box. Called from menu.
        '''
        if len(phases) < 2: return
        dlg = wx.SingleChoiceDialog(G2frame,'Select','Phase',phases)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                sel = dlg.GetSelection()
                ShowReflTable(phases[sel])
        finally:
            dlg.Destroy()
            
    if not data:
        print ('No phases, no reflections')
        return
    if HKLF:
        G2frame.RefList = 1
        phaseName = IsHistogramInAnyPhase(G2frame,Name)
        if not phaseName:
            phaseName = 'Unknown'
        phases = [phaseName]
    else:
        phaseName = G2frame.RefList
        phases = list(data.keys())
    Inst = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Instrument Parameters'))[0]
    G2gd.SetDataMenuBar(G2frame,G2frame.dataWindow.ReflMenu)
    if HKLF:
        G2frame.Bind(wx.EVT_MENU, OnPlotHKL, id=G2G.wxID_PWDHKLPLOT)
        G2frame.Bind(wx.EVT_MENU, OnPlot1DHKL, id=G2G.wxID_1DHKLSTICKPLOT)
        G2frame.Bind(wx.EVT_MENU, OnPlot3DHKL, id=G2G.wxID_PWD3DHKLPLOT)
        G2frame.dataWindow.SelectPhase.Enable(False)
    else:
        G2frame.Bind(wx.EVT_MENU, OnSelectPhase, id=G2G.wxID_SELECTPHASE)
        G2frame.Bind(wx.EVT_MENU, OnPlot1DHKL, id=G2G.wxID_1DHKLSTICKPLOT)
        G2frame.Bind(wx.EVT_MENU, OnPlotHKL, id=G2G.wxID_PWDHKLPLOT)
        G2frame.Bind(wx.EVT_MENU, OnPlot3DHKL, id=G2G.wxID_PWD3DHKLPLOT)
        G2frame.dataWindow.SelectPhase.Enable(False)
            
    G2frame.dataWindow.ClearData()
    G2frame.refBook = G2G.GSNoteBook(parent=G2frame.dataWindow)
    G2frame.dataWindow.GetSizer().Add(G2frame.refBook,1,wx.ALL|wx.EXPAND,1)
    G2frame.refTable = {}
    G2frame.dataWindow.currentGrids = []
    for tabnum,phase in enumerate(phases):
        if isinstance(data,list):           #single crystal HKLF
            G2frame.refTable[phase] = G2G.GSGrid(parent=G2frame.refBook)
            G2frame.refBook.AddPage(G2frame.refTable[phase],phase)
            G2frame.refTable[phase].SetScrollRate(10,10) # reflection grids (inside tab) need scroll bars 
        elif len(data[phase]):              #else dict for PWDR
            G2frame.refTable[phase] = G2G.GSGrid(parent=G2frame.refBook)
            G2frame.refBook.AddPage(G2frame.refTable[phase],phase)
            G2frame.refTable[phase].SetScrollRate(10,10) # as above
        else:       #cleanup deleted phase reflection lists
            del data[phase]
            if len(data):
                G2frame.RefList = list(data.keys())[0]
                phaseName = G2frame.RefList
            else:
                G2frame.RefList = ''
                phaseName = ''
    if phaseName: ShowReflTable(phaseName)
    G2frame.refBook.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, OnPageChanged)
    G2frame.dataWindow.SetDataSize()
    
################################################################################
#####  SASD/REFD Substances 
################################################################################
           
def UpdateSubstanceGrid(G2frame,data):
    '''respond to selection of SASD/REFD Substance data tree item.
    '''
    import Substances as substFile
    
    def LoadSubstance(name):

        subst = substFile.Substances[name]
        ElList = subst['Elements'].keys()
        for El in ElList:
            Info = G2elem.GetAtomInfo(El.strip().capitalize())
            Info.update(subst['Elements'][El])
            data['Substances'][name]['Elements'][El] = Info
            if 'Volume' in subst:
                data['Substances'][name]['Volume'] = subst['Volume']
                data['Substances'][name]['Density'] = \
                    G2mth.Vol2Den(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'])
            elif 'Density' in subst:
                data['Substances'][name]['Density'] = subst['Density']
                data['Substances'][name]['Volume'] = \
                    G2mth.Den2Vol(data['Substances'][name]['Elements'],data['Substances'][name]['Density'])
            else:
                data['Substances'][name]['Volume'] = G2mth.El2EstVol(data['Substances'][name]['Elements'])
                data['Substances'][name]['Density'] = \
                    G2mth.Vol2Den(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'])
            if 'X' in Inst['Type'][0]:
                data['Substances'][name]['Scatt density'] = \
                    G2mth.XScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'])[0]
                recontrst,absorb,imcontrst = G2mth.XScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'],wave)
            elif 'NC' in Inst['Type'][0]:
                isotopes = list(Info['Isotopes'].keys())
                isotopes.sort()
                data['Substances'][name]['Elements'][El]['Isotope'] = isotopes[-1]
                data['Substances'][name]['Scatt density'] = \
                    G2mth.NCScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'])[0]
                recontrst,absorb,imcontrst = G2mth.NCScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'],wave)
            data['Substances'][name]['XAnom density'] = recontrst
            data['Substances'][name]['XAbsorption'] = absorb
            data['Substances'][name]['XImag density'] = imcontrst
            
    def OnReloadSubstances(event):
        
        for name in data['Substances'].keys():
            if name not in ['vacuum','unit scatter']:
                if 'X' in Inst['Type'][0]:
                    data['Substances'][name]['Scatt density'] = \
                        G2mth.XScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'])[0]
                    recontrst,absorb,imcontrst = G2mth.XScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'],wave)
                elif 'NC' in Inst['Type'][0]:
                    data['Substances'][name]['Scatt density'] = \
                        G2mth.NCScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'])[0]
                    recontrst,absorb,imcontrst = G2mth.NCScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'],wave)
                data['Substances'][name]['XAnom density'] = recontrst
                data['Substances'][name]['XAbsorption'] = absorb
                data['Substances'][name]['XImag density'] = imcontrst
        UpdateSubstanceGrid(G2frame,data)
    
    def OnLoadSubstance(event):
        
        names = list(substFile.Substances.keys())
        names.sort()
        dlg = wx.SingleChoiceDialog(G2frame, 'Which substance?', 'Select substance', names, wx.CHOICEDLG_STYLE)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                name = names[dlg.GetSelection()]
            else:
                return
        finally:
            dlg.Destroy()
            
        data['Substances'][name] = {'Elements':{},'Volume':1.0,'Density':1.0,
            'Scatt density':0.0,'Real density':0.0,'XAbsorption':0.0,'XImag density':0.0}
        LoadSubstance(name)            
        UpdateSubstanceGrid(G2frame,data)
        
    def OnCopySubstance(event):
        hst = G2frame.GPXtree.GetItemText(G2frame.PatternId)
        histList = GetHistsLikeSelected(G2frame)
        if not histList:
            G2frame.ErrorDialog('No match','No histograms match '+hst,G2frame)
            return
        copyList = []
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Copy substances from\n'+hst[5:]+' to...',
            'Copy substances', histList)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                for i in dlg.GetSelections(): 
                    copyList.append(histList[i])
        finally:
            dlg.Destroy()        
        for item in copyList:
            Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,item)
            Inst = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,Id, 'Instrument Parameters'))[0]
            wave = G2mth.getWave(Inst)
            ndata = copy.deepcopy(data)
            for name in ndata['Substances'].keys():
                if name not in ['vacuum','unit scatter']:
                    if 'X' in Inst['Type'][0]:
                        recontrst,absorb,imcontrst = G2mth.XScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'],wave)
                    elif 'NC' in Inst['Type'][0]:
                        recontrst,absorb,imcontrst = G2mth.NCScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'],wave)
                    ndata['Substances'][name]['XAnom density'] = recontrst
                    ndata['Substances'][name]['XAbsorption'] = absorb
                    ndata['Substances'][name]['XImag density'] = imcontrst
            G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,Id,'Substances'),ndata)
    
    def OnAddSubstance(event):
        dlg = wx.TextEntryDialog(None,'Enter a name for this substance','Substance Name Entry','New substance',
            style=wx.OK|wx.CANCEL)
        if dlg.ShowModal() == wx.ID_OK:
            Name = dlg.GetValue()
            data['Substances'][Name] = {'Elements':{},'Volume':1.0,'Density':1.0,
                'Scatt density':0.0,'XAnom density':0.,'XAbsorption':0.,'XImag density':0.}
            AddElement(Name)
        else:
            return
        dlg.Destroy()
        if not data['Substances'][Name]['XAbsorption']:
            del data['Substances'][Name]
        UpdateSubstanceGrid(G2frame,data)
        
    def OnDeleteSubstance(event):
        TextList = []
        for name in data['Substances']:
            if name not in ['vacuum','unit scatter']:
                TextList += [name,]
        if not TextList:
            return
        dlg = wx.SingleChoiceDialog(G2frame, 'Which substance?', 'Select substance to delete', TextList, wx.CHOICEDLG_STYLE)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                name = TextList[dlg.GetSelection()]
            else:
                return
        finally:
            dlg.Destroy()
        del(data['Substances'][name])
        UpdateSubstanceGrid(G2frame,data)        
                
    def OnAddElement(event):        
        TextList = []
        for name in data['Substances']:
            if name not in ['vacuum','unit scatter']:
                TextList += [name,]
        if not TextList:
            return
        dlg = wx.SingleChoiceDialog(G2frame, 'Which substance?', 'Select substance', TextList, wx.CHOICEDLG_STYLE)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                name = TextList[dlg.GetSelection()]
                AddElement(name)
            else:
                return
        finally:
            dlg.Destroy()
        UpdateSubstanceGrid(G2frame,data)
        
    def AddElement(name):
        ElList = list(data['Substances'][name]['Elements'].keys())
        dlg = G2elemGUI.PickElements(G2frame,ElList)
        if dlg.ShowModal() == wx.ID_OK:
            for El in dlg.Elem:
                El = El.strip().capitalize()
                Info = G2elem.GetAtomInfo(El)
                Info.update({'Num':1.})
                data['Substances'][name]['Elements'][El] = Info
                isotopes = list(Info['Isotopes'].keys())
                isotopes.sort()
                data['Substances'][name]['Elements'][El]['Isotope'] = isotopes[-1]
            data['Substances'][name]['Volume'] = G2mth.El2EstVol(data['Substances'][name]['Elements'])
            data['Substances'][name]['Density'] = \
                G2mth.Vol2Den(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'])
            if 'X' in Inst['Type'][0]:
                data['Substances'][name]['Scatt density'] = \
                    G2mth.XScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'])[0]
                recontrst,absorb,imcontrst = G2mth.XScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'],wave)
            elif 'NC' in Inst['Type'][0]:
                data['Substances'][name]['Scatt density'] = \
                    G2mth.NCScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'])[0]
                recontrst,absorb,imcontrst = G2mth.NCScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'],wave)
            data['Substances'][name]['XAnom density'] = recontrst
            data['Substances'][name]['XAbsorption'] = absorb
            data['Substances'][name]['XImag density'] = imcontrst
        else:
            return
        dlg.Destroy()
        
    def OnDeleteElement(event):
        TextList = []
        for name in data['Substances']:
            if name not in ['vacuum','unit scatter']:
                TextList += [name,]
        if not TextList:
            return
        dlg = wx.SingleChoiceDialog(G2frame, 'Which substance?', 'Select substance', TextList, wx.CHOICEDLG_STYLE)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                name = TextList[dlg.GetSelection()]
            else:
                return
        finally:
            dlg.Destroy()
        ElList = list(data['Substances'][name]['Elements'].keys())
        if len(ElList):
            DE = G2elemGUI.DeleteElement(G2frame,ElList)
            if DE.ShowModal() == wx.ID_OK:
                El = DE.GetDeleteElement().strip().upper()
                del(data['Substances'][name]['Elements'][El])
                data['Substances'][name]['Volume'] = G2mth.El2EstVol(data['Substances'][name]['Elements'])
                data['Substances'][name]['Density'] = \
                    G2mth.Vol2Den(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'])
                if 'X' in Inst['Type'][0]:
                    data['Substances'][name]['Scatt density'] = \
                        G2mth.XScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'])[0]
                    recontrst,absorb,imcontrst = G2mth.XScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'],wave)
                elif 'NC' in Inst['Type'][0]:
                    data['Substances'][name]['Scatt density'] = \
                        G2mth.NCScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'])[0]
                    recontrst,absorb,imcontrst = G2mth.NCScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'],wave)
                data['Substances'][name]['XAnom density'] = recontrst
                data['Substances'][name]['XAbsorption'] = absorb
                data['Substances'][name]['XImag density'] = imcontrst
        UpdateSubstanceGrid(G2frame,data)
                
    def SubstSizer():
        
        def OnNum(invalid,value,tc):
            if invalid: return
            name,El,keyId = Indx[tc.GetId()]
            data['Substances'][name]['Volume'] = G2mth.El2EstVol(data['Substances'][name]['Elements'])
            data['Substances'][name]['Density'] = \
                G2mth.Vol2Den(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'])
            if 'X' in Inst['Type'][0]:
                recontrst,absorb,imcontrst = G2mth.XScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'],wave)
            elif 'NC' in Inst['Type'][0]:
                recontrst,absorb,imcontrst = G2mth.NCScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'],wave)
            data['Substances'][name]['XAnom density'] = recontrst
            data['Substances'][name]['XAbsorption'] = absorb
            data['Substances'][name]['XImag density'] = imcontrst
            wx.CallAfter(UpdateSubstanceGrid,G2frame,data)
            
        def OnVolDen(invalid,value,tc):
            if invalid: return
            name,keyId = Indx[tc.GetId()]
            if keyId in 'Volume':
                data['Substances'][name]['Density'] = \
                    G2mth.Vol2Den(data['Substances'][name]['Elements'],value)
            elif keyId in 'Density':
                data['Substances'][name]['Volume'] = \
                    G2mth.Den2Vol(data['Substances'][name]['Elements'],value)
            if 'X' in Inst['Type'][0]:
                data['Substances'][name]['Scatt density'] = \
                    G2mth.XScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'])[0]
                recontrst,absorb,imcontrst = G2mth.XScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'],wave)
            elif 'NC' in Inst['Type'][0]:
                data['Substances'][name]['Scatt density'] = \
                    G2mth.NCScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'])[0]
                recontrst,absorb,imcontrst = G2mth.NCScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'],wave)
            data['Substances'][name]['XAnom density'] = recontrst
            data['Substances'][name]['XAbsorption'] = absorb
            data['Substances'][name]['XImag density'] = imcontrst
            wx.CallAfter(UpdateSubstanceGrid,G2frame,data)
            
        def OnIsotope(event):
            Obj = event.GetEventObject()
            El,name = Indx[Obj.GetId()]
            data['Substances'][name]['Elements'][El]['Isotope'] = Obj.GetValue()
            recontrst,absorb,imcontrst = G2mth.NCScattDen(data['Substances'][name]['Elements'],data['Substances'][name]['Volume'],wave)
            data['Substances'][name]['XAnom density'] = recontrst
            data['Substances'][name]['XAbsorption'] = absorb
            data['Substances'][name]['XImag density'] = imcontrst
            wx.CallAfter(UpdateSubstanceGrid,G2frame,data)
        
        Indx = {}
        substSizer = wx.BoxSizer(wx.VERTICAL)
        substSizer.Add(wx.StaticText(parent=G2frame.dataWindow,label=' Substance list: wavelength: %.5fA'%(wave)),
            0,WACV)
        for name in data['Substances']:
            G2G.HorizontalLine(substSizer,G2frame.dataWindow)    
            substSizer.Add(wx.StaticText(parent=G2frame.dataWindow,label=' Data for '+name+':'),0)
            if name == 'vacuum':
                substSizer.Add(wx.StaticText(parent=G2frame.dataWindow,label='        Not applicable'),0)
            elif name == 'unit scatter':
                substSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Scattering density,f: %.3f *10%scm%s'%(data['Substances'][name]['Scatt density'],Pwr10,Pwrm2)),0)
            else:    
                elSizer = wx.FlexGridSizer(0,8,5,5)
                Substance = data['Substances'][name]
                Elems = Substance['Elements']
                for El in Elems:    #do elements as pull downs for isotopes for neutrons
                    elSizer.Add(wx.StaticText(parent=G2frame.dataWindow,label=' '+El+': '),
                        0,WACV)
                    num = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Substances'][name]['Elements'][El],'Num',
                        nDig=(10,2,'f'),typeHint=float,OnLeave=OnNum)
                    Indx[num.GetId()] = [name,El,'Num']
                    elSizer.Add(num,0,WACV)
                    if 'N' in Inst['Type'][0]:
                        elSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Isotope: '),0,WACV)
                        isotopes = list(Elems[El]['Isotopes'].keys())
                        isotope = wx.ComboBox(G2frame.dataWindow,choices=isotopes,value=Elems[El].get('Isotope','Nat. Abund.'),
                            style=wx.CB_READONLY|wx.CB_DROPDOWN)
                        Indx[isotope.GetId()] = [El,name]
                        isotope.Bind(wx.EVT_COMBOBOX,OnIsotope)
                        elSizer.Add(isotope,0,WACV)
                substSizer.Add(elSizer,0)
                vdsSizer = wx.FlexGridSizer(0,4,5,5)
                vdsSizer.Add(wx.StaticText(parent=G2frame.dataWindow,label=' Volume: '),
                    0,WACV)
                vol = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Substances'][name],'Volume',nDig=(10,2),typeHint=float,OnLeave=OnVolDen)
                Indx[vol.GetId()] = [name,'Volume']
                vdsSizer.Add(vol,0,WACV)                
                vdsSizer.Add(wx.StaticText(parent=G2frame.dataWindow,label=' Density: '),
                    0,WACV)
                den = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Substances'][name],'Density',nDig=(10,2),typeHint=float,OnLeave=OnVolDen)
                Indx[den.GetId()] = [name,'Density']
                vdsSizer.Add(den,0,WACV)
                substSizer.Add(vdsSizer,0)
                denSizer = wx.FlexGridSizer(0,2,0,0)
                denSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Scattering density,f'),0,WACV)
                denSizer.Add(wx.StaticText(G2frame.dataWindow,label=': %.3f *10%scm%s'%(Substance['Scatt density'],Pwr10,Pwrm2)),0,WACV)
                denSizer.Add(wx.StaticText(G2frame.dataWindow,label=" Real density,f+f'"),0,WACV)
                denSizer.Add(wx.StaticText(G2frame.dataWindow,label=': %.3f *10%scm%s'%(Substance['XAnom density'],Pwr10,Pwrm2)),0,WACV)
                denSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Imaginary density,f"'),0,WACV)
                denSizer.Add(wx.StaticText(G2frame.dataWindow,label=': %.3g *10%scm%s'%(Substance['XImag density'],Pwr10,Pwrm2)),0,WACV)
                denSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Absorption'),0,WACV)
                denSizer.Add(wx.StaticText(G2frame.dataWindow,label=': %.3g cm%s'%(Substance['XAbsorption'],Pwrm1)),0,WACV)
                substSizer.Add(denSizer)
        return substSizer
            
    Inst = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Instrument Parameters'))[0]
    wave = G2mth.getWave(Inst)
    G2gd.SetDataMenuBar(G2frame,G2frame.dataWindow.SubstanceMenu)
    G2frame.Bind(wx.EVT_MENU, OnLoadSubstance, id=G2G.wxID_LOADSUBSTANCE)    
    G2frame.Bind(wx.EVT_MENU, OnReloadSubstances, id=G2G.wxID_RELOADSUBSTANCES)    
    G2frame.Bind(wx.EVT_MENU, OnAddSubstance, id=G2G.wxID_ADDSUBSTANCE)
    G2frame.Bind(wx.EVT_MENU, OnCopySubstance, id=G2G.wxID_COPYSUBSTANCE)
    G2frame.Bind(wx.EVT_MENU, OnDeleteSubstance, id=G2G.wxID_DELETESUBSTANCE)    
    G2frame.Bind(wx.EVT_MENU, OnAddElement, id=G2G.wxID_ELEMENTADD)
    G2frame.Bind(wx.EVT_MENU, OnDeleteElement, id=G2G.wxID_ELEMENTDELETE)
    G2frame.dataWindow.ClearData()
    mainSizer = G2frame.dataWindow.GetSizer()
    mainSizer.Add(SubstSizer(),0)
    G2frame.dataWindow.SetDataSize()

################################################################################
#####  SASD Models 
################################################################################           
       
def UpdateModelsGrid(G2frame,data):
    '''respond to selection of SASD Models data tree item.
    '''
    #patches
    if 'Current' not in data:
        data['Current'] = 'Size dist.'
    if 'logBins' not in data['Size']:
        data['Size']['logBins'] = True
    if 'MinMaxDiam' in data['Size']:
        data['Size']['MinDiam'] = 50.
        data['Size']['MaxDiam'] = 10000.
        del data['Size']['MinMaxDiam']
    if isinstance(data['Size']['MaxEnt']['Sky'],float):
        data['Size']['MaxEnt']['Sky'] = -3
    if 'Power' not in data['Size']['IPG']:
        data['Size']['IPG']['Power'] = -1
    if 'Matrix' not in data['Particle']:
        data['Particle']['Matrix'] = {'Name':'vacuum','VolFrac':[0.0,False]}
    if 'BackFile' not in data:
        data['BackFile'] = ''
    if 'Pair' not in data:
        data['Pair'] = {'Method':'Moore','MaxRadius':100.,'NBins':100,'Errors':'User','Result':[],
            'Percent error':2.5,'Background':[0,False],'Distribution':[],'Moore':10,'Dist G':100.,}  
    if 'Shapes' not in data:
        data['Shapes'] = {'outName':'run','NumAA':100,'Niter':1,'AAscale':1.0,'Symm':1,'bias-z':0.0,
            'inflateV':1.0,'AAglue':0.0,'pdbOut':False,'boxStep':4.0}
    if 'boxStep' not in data['Shapes']:
        data['Shapes']['boxStep'] = 4.0
    plotDefaults = {'oldxy':[0.,0.],'Quaternion':[0.,0.,0.,1.],'cameraPos':150.,'viewDir':[0,0,1],}

    #end patches
    
    def RefreshPlots(newPlot=False):
        PlotText = G2frame.G2plotNB.nb.GetPageText(G2frame.G2plotNB.nb.GetSelection())
        if 'Powder' in PlotText:
            G2plt.PlotPatterns(G2frame,plotType='SASD',newPlot=newPlot)
        elif 'Size' in PlotText:
            G2plt.PlotSASDSizeDist(G2frame)
        elif 'Pair' in PlotText:
            G2plt.PlotSASDPairDist(G2frame)
            
                
    def OnAddModel(event):
        if data['Current'] == 'Particle fit':
            material = 'vacuum'
            if len(data['Particle']['Levels']):
                material = data['Particle']['Levels'][-1]['Controls']['Material']
            data['Particle']['Levels'].append({
                'Controls':{'FormFact':'Sphere','DistType':'LogNormal','Material':material,
                    'FFargs':{},'SFargs':{},'NumPoints':50,'Cutoff':0.01,'Contrast':0.0,
                    'SlitSmear':[0.0,False],'StrFact':'Dilute'},    #last 2 not used - future?
                'LogNormal':{'Volume':[0.05,False],'Mean':[1000.,False],'StdDev':[0.5,False],'MinSize':[10.,False],},
                'Gaussian':{'Volume':[0.05,False],'Mean':[1000.,False],'StdDev':[300.,False],},
                'LSW':{'Volume':[0.05,False],'Mean':[1000.0,False],},
                'Schulz-Zimm':{'Volume':[0.05,False],'Mean':[1000.,False],'StdDev':[300.,False],},
                'Unified':{'G':[1.e3,False],'Rg':[100,False],'B':[1.e-5,False],'P':[4,False],'Cutoff':[1e-5,False],},
                'Porod':{'B':[1.e-4,False],'P':[4,False],'Cutoff':[1e-5,False],},
                'Monodisperse':{'Volume':[0.05,False],'Radius':[100,False],},   #OK for spheres
                'Bragg':{'PkInt':[100,False],'PkPos':[0.2,False],
                    'PkSig':[10,False],'PkGam':[10,False],},        #reasonable 31A peak
                })
            G2sasd.ModelFxn(Profile,ProfDict,Limits,Sample,data)
            RefreshPlots(True)
                    
        wx.CallAfter(UpdateModelsGrid,G2frame,data)
        
    def OnCopyModel(event):
        hst = G2frame.GPXtree.GetItemText(G2frame.PatternId)
        histList = GetHistsLikeSelected(G2frame)
        if not histList:
            G2frame.ErrorDialog('No match','No histograms match '+hst,G2frame)
            return
        copyList = []
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Copy models from\n'+hst[5:]+' to...',
            'Copy models', histList)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                for i in dlg.GetSelections(): 
                    copyList.append(histList[i])
        finally:
            dlg.Destroy()        
        for item in copyList:
            Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,item)
            newdata = copy.deepcopy(data)
            G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,Id,'Models'),newdata)
            if newdata['BackFile']:
                Profile = G2frame.GPXtree.GetItemPyData(Id)[1]
                BackId = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,newdata['BackFile'])
                BackSample = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,BackId, 'Sample Parameters'))
                Profile[5] = BackSample['Scale'][0]*G2frame.GPXtree.GetItemPyData(BackId)[1][1]
        UpdateModelsGrid(G2frame,newdata)  
        wx.CallAfter(UpdateModelsGrid,G2frame,data)
        RefreshPlots(True)
                
    def OnCopyFlags(event):
        thisModel = copy.deepcopy(data)
        hst = G2frame.GPXtree.GetItemText(G2frame.PatternId)
        histList = GetHistsLikeSelected(G2frame)
        if not histList:
            G2frame.ErrorDialog('No match','No histograms match '+hst,G2frame)
            return
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Copy sample ref. flags from\n'+str(hst[5:])+' to...',
            'Copy sample flags', histList)
        distChoice = ['LogNormal','Gaussian','LSW','Schulz-Zimm','Bragg','Unified',
            'Porod','Monodisperse',]
        parmOrder = ['Volume','Radius','Mean','StdDev','G','Rg','B','P',
            'Cutoff','PkInt','PkPos','PkSig','PkGam','VolFr','Dist',]
        try:
            if dlg.ShowModal() == wx.ID_OK:
                result = dlg.GetSelections()
                for i in result: 
                    item = histList[i]
                    Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,item)
                    newModel = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,Id,'Models'))
                    newModel['Back'][1] = copy.copy(thisModel['Back'][1])
                    for ilev,level in enumerate(newModel['Particle']['Levels']):
                        for form in level:
                            if form in distChoice:
                                thisForm = thisModel['Particle']['Levels'][ilev][form]                               
                                for item in parmOrder:
                                    if item in thisForm:
                                       level[form][item][1] = copy.copy(thisForm[item][1])
                            elif form == 'Controls':
                                thisForm = thisModel['Particle']['Levels'][ilev][form]['SFargs']
                                for item in parmOrder:
                                    if item in thisForm:
                                        level[form]['SFargs'][item][1] = copy.copy(thisForm[item][1])
        finally:
            dlg.Destroy()
                
    def OnFitModelAll(event):
        choices = G2gd.GetGPXtreeDataNames(G2frame,['SASD',])
        od = {'label_1':'Copy to next','value_1':False,'label_2':'Reverse order','value_2':False}
        dlg = G2G.G2MultiChoiceDialog(G2frame, 'Sequential SASD refinement',
             'Select dataset to include',choices,extraOpts=od)
        names = []
        if dlg.ShowModal() == wx.ID_OK:
            for sel in dlg.GetSelections():
                names.append(choices[sel])
            Id =  G2gd.GetGPXtreeItemId(G2frame,G2frame.root,'Sequential SASD results')
            if Id:
                SeqResult = G2frame.GPXtree.GetItemPyData(Id)
            else:
                SeqResult = {}
                Id = G2frame.GPXtree.AppendItem(parent=G2frame.root,text='Sequential SASD results')
            SeqResult = {'SeqPseudoVars':{},'SeqParFitEqList':[]}
            SeqResult['histNames'] = names
        else:
            dlg.Destroy()
            return
        dlg.Destroy()
        dlg = wx.ProgressDialog('SASD Sequential fit','Data set name = '+names[0],len(names), 
            style = wx.PD_ELAPSED_TIME|wx.PD_AUTO_HIDE|wx.PD_REMAINING_TIME|wx.PD_CAN_ABORT)
        wx.BeginBusyCursor()
        if od['value_2']:
            names.reverse()
        JModel = None
        try:
            for i,name in enumerate(names):
                print (' Sequential fit for '+name)
                GoOn = dlg.Update(i,newmsg='Data set name = '+name)[0]
                if not GoOn:
                    break
                sId =  G2gd.GetGPXtreeItemId(G2frame,G2frame.root,name)
                if i and od['value_1']:
                    G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,sId, 'Models'),JModel)
                IProfDict,IProfile = G2frame.GPXtree.GetItemPyData(sId)[:2]
                IModel = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,sId, 'Models'))
                ISample = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,sId, 'Sample Parameters'))
                ILimits = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,sId, 'Limits'))
                IfOK,result,varyList,sig,Rvals,covMatrix,parmDict,Msg = G2sasd.ModelFit(IProfile,IProfDict,ILimits,ISample,IModel)
                JModel = copy.deepcopy(IModel)
                if not IfOK:
                    G2frame.ErrorDialog('Failed sequential refinement for data '+name,
                        ' Msg: '+Msg+'\nYou need to rethink your selection of parameters\n'+    \
                        ' Model restored to previous version for'+name)
                    SeqResult['histNames'] = names[:i]
                    dlg.Destroy()
                    break
                else:
                    G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,sId, 'Models'),copy.deepcopy(IModel))
                
                G2sasd.ModelFxn(IProfile,IProfDict,ILimits,ISample,IModel)
                SeqResult[name] = {'variables':result[0],'varyList':varyList,'sig':sig,'Rvals':Rvals,
                    'covMatrix':covMatrix,'title':name,'parmDict':parmDict}
            else:
                dlg.Destroy()
                print (' ***** Small angle sequential refinement successful *****')
        finally:
            wx.EndBusyCursor()    
        G2frame.GPXtree.SetItemPyData(Id,SeqResult)
        G2frame.GPXtree.SelectItem(Id)
        
    def OnFitModel(event):
        if data['Current'] == 'Size dist.':
            if not any(Sample['Contrast']):
                G2frame.ErrorDialog('No contrast; your sample is a vacuum!',
                    'You need to define a scattering substance!\n'+    \
                    ' Do Substances and then Sample parameters')
                return
            G2sasd.SizeDistribution(Profile,ProfDict,Limits,Sample,data)
            G2plt.PlotSASDSizeDist(G2frame)
            RefreshPlots(True)
            
        elif data['Current'] == 'Particle fit':
            SaveState()
            Results = G2sasd.ModelFit(Profile,ProfDict,Limits,Sample,data)
            if not Results[0]:
                    G2frame.ErrorDialog('Failed refinement',
                        ' Msg: '+Results[-1]+'\nYou need to rethink your selection of parameters\n'+    \
                        ' Model restored to previous version')
            G2sasd.ModelFxn(Profile,ProfDict,Limits,Sample,data)
            RefreshPlots(True)
            wx.CallAfter(UpdateModelsGrid,G2frame,data)
            
        elif data['Current'] == 'Pair distance':
            SaveState()
            G2sasd.PairDistFxn(Profile,ProfDict,Limits,Sample,data)
            RefreshPlots(True)
            G2plt.PlotSASDPairDist(G2frame)
            wx.CallAfter(UpdateModelsGrid,G2frame,data)
            
        elif data['Current'] == 'Shapes':
            SaveState()
            wx.MessageBox(''' For use of SHAPES, please cite:
      A New Algroithm for the Reconstruction of Protein Molecular Envelopes
      from X-ray Solution Scattering Data, 
      J. Badger, Jour. of Appl. Chrystallogr. 2019, 52, 937-944.
      doi: https://doi.org/10.1107/S1600576719009774''',
      caption='Program Shapes',style=wx.ICON_INFORMATION)
            dlg = wx.ProgressDialog('Running SHAPES','Cycle no.: 0 of 160',161, 
                style = wx.PD_ELAPSED_TIME|wx.PD_AUTO_HIDE|wx.PD_REMAINING_TIME)
                
            data['Pair']['Result'] = []       #clear old results (if any) for now
            data['Pair']['Result'] = G2shapes.G2shapes(Profile,ProfDict,Limits,data,dlg)
            wx.CallAfter(UpdateModelsGrid,G2frame,data)
            
    def OnUnDo(event):
        DoUnDo()
        data = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,
            G2frame.PatternId,'Models'))
        G2frame.dataWindow.SasdUndo.Enable(False)
        UpdateModelsGrid(G2frame,data)
        G2sasd.ModelFxn(Profile,ProfDict,Limits,Sample,data)
        RefreshPlots(True)

    def DoUnDo():
        print ('Undo last refinement')
        file = open(G2frame.undosasd,'rb')
        PatternId = G2frame.PatternId
        G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Models'),cPickle.load(file))
        print (' Models recovered')
        file.close()
        
    def SaveState():
        G2frame.undosasd = os.path.join(G2frame.dirname,'GSASIIsasd.save')
        file = open(G2frame.undosasd,'wb')
        PatternId = G2frame.PatternId
        for item in ['Models']:
            cPickle.dump(G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId,item)),file,1)
        file.close()
        G2frame.dataWindow.SasdUndo.Enable(True)
        
    def OnSelectFit(event):
        data['Current'] = fitSel.GetValue()
        wx.CallAfter(UpdateModelsGrid,G2frame,data)
        
    def OnCheckBox(event):
        Obj = event.GetEventObject()
        item,ind = Indx[Obj.GetId()]
        item[ind] = Obj.GetValue()
        
    def OnIntVal(event):
        event.Skip()
        Obj = event.GetEventObject()
        item,ind,minVal = Indx[Obj.GetId()]
        try:
            value = int(Obj.GetValue())
            if value <= minVal:
                raise ValueError
        except ValueError:
            value = item[ind]
        Obj.SetValue(str(value))
        item[ind] = value

    def SizeSizer():
        
        def OnShape(event):
            data['Size']['Shape'][0] = partsh.GetValue()
            wx.CallAfter(UpdateModelsGrid,G2frame,data)
            
        def OnMethod(event):
            data['Size']['Method'] = method.GetValue()
            wx.CallAfter(UpdateModelsGrid,G2frame,data)
            
        sizeSizer = wx.BoxSizer(wx.VERTICAL)
        sizeSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Size distribution parameters: '),0)
        binSizer = wx.FlexGridSizer(0,7,5,5)
        binSizer.Add(wx.StaticText(G2frame.dataWindow,label=' No. size bins: '),0,WACV)
        bins = ['50','100','150','200']
        nbins = wx.ComboBox(G2frame.dataWindow,value=str(data['Size']['Nbins']),choices=bins,
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        Indx[nbins.GetId()] = [data['Size'],'Nbins',0]
        nbins.Bind(wx.EVT_COMBOBOX,OnIntVal)        
        binSizer.Add(nbins,0,WACV)
        binSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Min diam.: '),0,WACV)
        minDias = ['10','25','50','100','150','200']
        mindiam = wx.ComboBox(G2frame.dataWindow,value=str(data['Size']['MinDiam']),choices=minDias,
            style=wx.CB_DROPDOWN)
        mindiam.Bind(wx.EVT_LEAVE_WINDOW,OnIntVal)
        mindiam.Bind(wx.EVT_TEXT_ENTER,OnIntVal)        
        mindiam.Bind(wx.EVT_KILL_FOCUS,OnIntVal)
        Indx[mindiam.GetId()] = [data['Size'],'MinDiam',0]
        binSizer.Add(mindiam,0,WACV)
        binSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Max diam.: '),0,WACV)
        maxDias = [str(1000*(i+1)) for i in range(10)]
        maxdiam = wx.ComboBox(G2frame.dataWindow,value=str(data['Size']['MaxDiam']),choices=maxDias,
            style=wx.CB_DROPDOWN)
        maxdiam.Bind(wx.EVT_LEAVE_WINDOW,OnIntVal)
        maxdiam.Bind(wx.EVT_TEXT_ENTER,OnIntVal)        
        maxdiam.Bind(wx.EVT_KILL_FOCUS,OnIntVal)
        Indx[maxdiam.GetId()] = [data['Size'],'MaxDiam',0]
        binSizer.Add(maxdiam,0,WACV)
        logbins = wx.CheckBox(G2frame.dataWindow,label='Log bins?')
        Indx[logbins.GetId()] = [data['Size'],'logBins']
        logbins.SetValue(data['Size']['logBins'])
        logbins.Bind(wx.EVT_CHECKBOX, OnCheckBox)
        binSizer.Add(logbins,0,WACV)
        sizeSizer.Add(binSizer,0)
        sizeSizer.Add((5,5),0)
        partSizer = wx.BoxSizer(wx.HORIZONTAL)
        partSizer.Add(wx.StaticText(G2frame.dataWindow,label='Particle description: '),0,WACV)
        shapes = {'Spheroid':' Aspect ratio: ','Cylinder':' Diameter ','Cylinder AR':' Aspect ratio: ',
            'Unified sphere':'','Unified rod':' Diameter: ','Unified rod AR':' Aspect ratio: ',
            'Unified disk':' Thickness: ', 'Spherical shell': ' Shell thickness'}
        partsh = wx.ComboBox(G2frame.dataWindow,value=str(data['Size']['Shape'][0]),choices=list(shapes.keys()),
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        partsh.Bind(wx.EVT_COMBOBOX,OnShape)        
        partSizer.Add(partsh,0,WACV)
        if data['Size']['Shape'][0] not in ['Unified sphere',]:
            partSizer.Add(wx.StaticText(G2frame.dataWindow,label=shapes[data['Size']['Shape'][0]]),0,WACV)
            partprm = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Size']['Shape'],1,
                nDig=(10,3),typeHint=float,xmin=0.)
            partSizer.Add(partprm,0,WACV)
        sizeSizer.Add(partSizer,0)
        sizeSizer.Add((5,5),0)
        fitSizer = wx.BoxSizer(wx.HORIZONTAL)
        methods = ['MaxEnt','IPG',]
        fitSizer.Add(wx.StaticText(G2frame.dataWindow,label='Fitting method: '),0,WACV)
        method = wx.ComboBox(G2frame.dataWindow,value=data['Size']['Method'],choices=methods,
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        method.Bind(wx.EVT_COMBOBOX,OnMethod)
        fitSizer.Add(method,0,WACV)
        iters = ['10','25','50','100','150','200']        
        fitSizer.Add(wx.StaticText(G2frame.dataWindow,label=' No. iterations: '),0,WACV)
        Method = data['Size']['Method']
        iter = wx.ComboBox(G2frame.dataWindow,value=str(data['Size'][Method]['Niter']),choices=iters,
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        Indx[iter.GetId()] = [data['Size'][Method],'Niter',0]
        iter.Bind(wx.EVT_COMBOBOX,OnIntVal)
        fitSizer.Add(iter,0,WACV)
        if 'MaxEnt' in data['Size']['Method']:
            fitSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Log floor factor: '),0,WACV)
            floors = [str(-i) for i in range(9)]
            floor = wx.ComboBox(G2frame.dataWindow,value=str(data['Size']['MaxEnt']['Sky']),choices=floors,
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
            Indx[floor.GetId()] = [data['Size']['MaxEnt'],'Sky',-10]
            floor.Bind(wx.EVT_COMBOBOX,OnIntVal)
            fitSizer.Add(floor,0,WACV)
        elif 'IPG' in data['Size']['Method']:
            fitSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Q power weight (-1 for sigma): '),0,WACV)
            choices = ['-1','0','1','2','3','4']
            power = wx.ComboBox(G2frame.dataWindow,value=str(data['Size']['IPG']['Power']),choices=choices,
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
            Indx[power.GetId()] = [data['Size']['IPG'],'Power',-2]
            power.Bind(wx.EVT_COMBOBOX,OnIntVal)
            fitSizer.Add(power,0,WACV)
        sizeSizer.Add(fitSizer,0)

        return sizeSizer
        
    def PairSizer():
                
        def OnMethod(event):
            data['Pair']['Method'] = method.GetValue()
            wx.CallAfter(UpdateModelsGrid,G2frame,data)
            
        def OnError(event):
            data['Pair']['Errors'] = error.GetValue()
            wx.CallAfter(UpdateModelsGrid,G2frame,data)
            
        def OnMaxRadEst(event):
            Results = G2sasd.RgFit(Profile,ProfDict,Limits,Sample,data)
            if not Results[0]:
                    G2frame.ErrorDialog('Failed refinement',
                        ' Msg: '+Results[-1]+'\nYou need to rethink your selection of parameters\n'+    \
                        ' Model restored to previous version')
            RefreshPlots(True)
            wx.CallAfter(UpdateModelsGrid,G2frame,data)                    
                        
        def OnMooreTerms(event):
            data['Pair']['Moore'] = int(round(Limits[1][1]*data['Pair']['MaxRadius']/np.pi))-1
            wx.CallAfter(UpdateModelsGrid,G2frame,data)

        def OnNewVal(invalid,value,tc):
            if invalid: return
            parmDict = {'Rg':data['Pair']['MaxRadius']/2.5,'G':data['Pair']['Dist G'],
                'B':data['Pair'].get('Dist B',Profile[1][-1]*Profile[0][-1]**4),
                'Back':data['Back'][0]}
            Profile[2] = G2sasd.getSASDRg(Profile[0],parmDict)
            RefreshPlots(True)
            
        pairSizer = wx.BoxSizer(wx.VERTICAL)
        pairSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Pair distribution parameters: '),0)
        binSizer = wx.FlexGridSizer(0,6,5,5)
        binSizer.Add(wx.StaticText(G2frame.dataWindow,label=' No. R bins: '),0,WACV)
        bins = ['50','100','150','200']
        nbins = wx.ComboBox(G2frame.dataWindow,value=str(data['Pair']['NBins']),choices=bins,
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        Indx[nbins.GetId()] = [data['Pair'],'NBins',0]
        nbins.Bind(wx.EVT_COMBOBOX,OnIntVal)        
        binSizer.Add(nbins,0,WACV)
        binSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Max diam.: '),0,WACV)
        maxdiam = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Pair'],'MaxRadius',xmin=10.,nDig=(10,1),OnLeave=OnNewVal)
        binSizer.Add(maxdiam,0,WACV)
        maxest = wx.Button(G2frame.dataWindow,label='Make estimate')
        maxest.Bind(wx.EVT_BUTTON,OnMaxRadEst)
        binSizer.Add(maxest,0,WACV)
        pairSizer.Add(binSizer,0)
        pairSizer.Add((5,5),0)
        fitSizer = wx.BoxSizer(wx.HORIZONTAL)
        methods = ['Moore',]            #'Regularization',
        fitSizer.Add(wx.StaticText(G2frame.dataWindow,label='Fitting method: '),0,WACV)
        method = wx.ComboBox(G2frame.dataWindow,value=data['Pair']['Method'],choices=methods,
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        method.Bind(wx.EVT_COMBOBOX,OnMethod)
        fitSizer.Add(method,0,WACV)
        if data['Pair']['Method'] == 'Moore':
            fitSizer.Add(wx.StaticText(G2frame.dataWindow,label=" P.B. Moore, J. Appl. Cryst., 13, 168-175 (1980)"),0,WACV)
        else:
            fitSizer.Add(wx.StaticText(G2frame.dataWindow,label=" D.I. Svergun, J. Appl. Cryst., 24, 485-492 (1991)"),0,WACV)
        pairSizer.Add(fitSizer,0)
        if 'Moore' in data['Pair']['Method']:
            mooreSizer = wx.BoxSizer(wx.HORIZONTAL)
            mooreSizer.Add(wx.StaticText(G2frame.dataWindow,label='Number of functions: '),0,WACV)
            moore = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Pair'],'Moore',xmin=2,xmax=20)
            mooreSizer.Add(moore,0,WACV)
            mooreterms = wx.Button(G2frame.dataWindow,label = 'Auto determine?')
            mooreterms.Bind(wx.EVT_BUTTON,OnMooreTerms)
            mooreSizer.Add(mooreterms,0,WACV)
            pairSizer.Add(mooreSizer,0)
        errorSizer = wx.BoxSizer(wx.HORIZONTAL)
        errorSizer.Add(wx.StaticText(G2frame.dataWindow,label='Error method: '),0,WACV)
        errors = ['User','Sqrt','Percent']
        error = wx.ComboBox(G2frame.dataWindow,value=data['Pair']['Errors'],choices=errors,
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        error.Bind(wx.EVT_COMBOBOX,OnError)
        if 'Percent' in data['Pair']['Errors']:
            percent = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Pair'],'Percent error',xmin=0.5,nDig=(10,1))
            errorSizer.Add(percent,0,WACV)
        errorSizer.Add(error,0,WACV)
        pairSizer.Add(errorSizer,0)
        return pairSizer    
    
    def ShapesSizer():
        
#        def OnPDBout(event):
#            data['Shapes']['pdbOut'] = not data['Shapes']['pdbOut']
            
        def OnShapeSelect(event):
            r,c =  event.GetRow(),event.GetCol()
            for i in [1,2]:
                for j in range(len(Patterns)):
                    shapeTable.SetValue(j,i,False)
            shapeTable.SetValue(r,c,True)
            ShapesResult.ForceRefresh()
            Limits = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Limits'))[1]
            ProfDict,Profile = G2frame.GPXtree.GetItemPyData(G2frame.PatternId)[:2]
            iBeg = np.searchsorted(Profile[0],Limits[0])
            iFin = np.searchsorted(Profile[0],Limits[1])
            pattern = Patterns[r]
            Profile[3][iBeg:iFin+1] = np.array(pattern[2])
            selAtoms = Atoms[2*r+(c-1)]
            prCalc = PRcalc[r][2]
            prDelt= np.diff(PRcalc[r][0])[0]
            prsum = np.sum(prCalc)
            prCalc /= prsum*prDelt
            data['Pair']['Pair Calc'] = np.array([PRcalc[r][0],prCalc]).T
            print('%s %d'%('num. beads',len(selAtoms[1])))
            print('%s %.3f'%('selected r value',pattern[-1]))
            print('%s %.3f'%('selected Delta P(r)',PRcalc[r][-1]))
            PDBtext = 'P(R) dif: %.3f r-value: %.3f Nbeads: %d'%(PRcalc[r][-1],pattern[-1],len(selAtoms[1]))
#            RefreshPlots(True)
            G2plt.PlotPatterns(G2frame,plotType='SASD',newPlot=True)
            G2plt.PlotSASDPairDist(G2frame)
            G2plt.PlotBeadModel(G2frame,selAtoms,plotDefaults,PDBtext)
        
        shapeSizer = wx.BoxSizer(wx.VERTICAL)
        shapeSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Shape parameters:'),0)
        parmSizer = wx.FlexGridSizer(0,4,5,5)
#1st row        
        parmSizer.Add(wx.StaticText(G2frame.dataWindow,label=' No. amino acids: '),0,WACV)
        numAA = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Shapes'],'NumAA',xmin=10)
        parmSizer.Add(numAA,0,WACV)
        parmSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Nballs=no. amino acids*'),0,WACV)        
        scaleAA = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Shapes'],'AAscale',xmin=0.01,xmax=10.,nDig=(10,2))
        parmSizer.Add(scaleAA,0,WACV)
#2nd row        
        parmSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Inflate by (1.-1.4): '),0,WACV)        
        inflate = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Shapes'],'inflateV',xmin=1.,xmax=1.4,nDig=(10,2))
        parmSizer.Add(inflate,0,WACV)
        parmSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Axial symmetry (1-12): '),0,WACV)        
        symm = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Shapes'],'Symm',xmin=1,xmax=12)
        parmSizer.Add(symm,0,WACV)
#3rd row
        parmSizer.Add(wx.StaticText(G2frame.dataWindow,label=' z-axis bias (-2 to 2): '),0,WACV)        
        zaxis = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Shapes'],'bias-z',xmin=-2.,xmax=2.,nDig=(10,2))
        parmSizer.Add(zaxis,0,WACV)
        parmSizer.Add(wx.StaticText(G2frame.dataWindow,label=' elongation (0-20): '),0,WACV)        
        glue = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Shapes'],'AAglue',xmin=0.,xmax=20.,nDig=(10,2))
        parmSizer.Add(glue,0,WACV)
#4th row
        parmSizer.Add(wx.StaticText(G2frame.dataWindow,label=' No. iterations (1-10): '),0,WACV)        
        niter = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Shapes'],'Niter',xmin=1,xmax=10)
        parmSizer.Add(niter,0,WACV)
        parmSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Output name: '),0,WACV)        
        name = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Shapes'],'outName')
        parmSizer.Add(name,0,WACV)
#last row
        parmSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Bead separation (3.5-5): '),0,WACV)
        beadsep = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Shapes'],'boxStep',xmin=3.5,xmax=5,nDig=(10,1))
        parmSizer.Add(beadsep,0,WACV)        
#        pdb = wx.CheckBox(G2frame.dataWindow,label=' Save as pdb files?: ')
#        pdb.SetValue(data['Shapes']['pdbOut'])
#        pdb.Bind(wx.EVT_CHECKBOX, OnPDBout)       
#        parmSizer.Add(pdb,0,WACV)
        
        shapeSizer.Add(parmSizer)
        
        if len(data['Pair'].get('Result',[])):
            shapeSizer.Add(wx.StaticText(G2frame.dataWindow,label=' SHAPES run results:'),0)
            Atoms,Patterns,PRcalc = data['Pair']['Result']
            colLabels = ['name','show beads','show shape','Rvalue','P(r) dif','Nbeads','Nshape']
            Types = [wg.GRID_VALUE_STRING,]+2*[wg.GRID_VALUE_BOOL,]+2*[wg.GRID_VALUE_FLOAT+':10,3',]+2*[wg.GRID_VALUE_LONG,]
            rowLabels = [str(i) for i in range(len(Patterns))]
            tableVals = []
            for i in range(len(Patterns)):
                tableVals.append([Atoms[2*i][0],False,False,Patterns[i][-1],PRcalc[i][-1],len(Atoms[2*i][1]),len(Atoms[2*i+1][1])])
            shapeTable = G2G.Table(tableVals,rowLabels=rowLabels,colLabels=colLabels,types=Types)
            ShapesResult = G2G.GSGrid(G2frame.dataWindow)
            ShapesResult.SetTable(shapeTable,True)
            ShapesResult.AutoSizeColumns(False)
            ShapesResult.Bind(wg.EVT_GRID_CELL_LEFT_CLICK, OnShapeSelect)
            for r in range(len(Patterns)):
                for c in range(7):
                    if c in [1,2]:
                        ShapesResult.SetReadOnly(r,c,isReadOnly=False)
                    else:
                        ShapesResult.SetReadOnly(r,c,isReadOnly=True)
    
            shapeSizer.Add(ShapesResult,0)
        return shapeSizer

    def PartSizer():
        
        FormFactors = {'Sphere':{},'Spheroid':{'Aspect ratio':[1.0,False]},
            'Cylinder':{'Length':[100.,False]},'Cylinder diam':{'Diameter':[100.,False]},
            'Cylinder AR':{'Aspect ratio':[1.0,False]},'Unified sphere':{},
            'Unified rod':{'Length':[100.,False]},'Unified rod AR':{'Aspect ratio':[1.0,False]},
            'Unified disk':{'Thickness':[100.,False]},
            'Unified tube':{'Length':[100.,False],'Thickness':[10.,False]},
            'Spherical shell':{'Shell thickness':[1.5,False] }, }
                
        StructureFactors = {'Dilute':{},'Hard sphere':{'VolFr':[0.1,False],'Dist':[100.,False]},
            'Sticky hard sphere':{'VolFr':[0.1,False],'Dist':[100.,False],'epis':[0.05,False],'Sticky':[0.2,False]},
            'Square well':{'VolFr':[0.1,False],'Dist':[100.,False],'Depth':[0.1,False],'Width':[1.,False]},
            'InterPrecipitate':{'VolFr':[0.1,False],'Dist':[100.,False]},}
                
        ffDistChoices =  ['Sphere','Spheroid','Cylinder','Cylinder diam',
            'Cylinder AR','Unified sphere','Unified rod','Unified rod AR',
            'Unified disk','Unified tube','Spherical shell',]
                
        ffMonoChoices = ['Sphere','Spheroid','Cylinder','Cylinder AR',]
        
        sfChoices = ['Dilute','Hard sphere','Sticky hard sphere','Square well','InterPrecipitate',]
            
        slMult = 1000.
                  
        def OnValue(event):
            event.Skip()
            Obj = event.GetEventObject()
            item,key,sldrObj = Indx[Obj.GetId()]
            try:
                value = float(Obj.GetValue())
                if value <= 0.:
                    raise ValueError
            except ValueError:
                value = item[key][0]
            item[key][0] = value
            Obj.SetValue('%.3g'%(value))
            if key in ['P','epis','Sticky','Depth','Width','VolFr','Dist']:
                sldrObj.SetValue(slMult*value)
            else:
                logv = np.log10(value)
                valMinMax = [logv-1,logv+1]
                sldrObj.SetRange(slMult*valMinMax[0],slMult*valMinMax[1])
                sldrObj.SetValue(slMult*logv)
            G2sasd.ModelFxn(Profile,ProfDict,Limits,Sample,data)
            RefreshPlots(True)
            
        def OnSelect(event):
            Obj = event.GetEventObject()
            item,key = Indx[Obj.GetId()]
            if key in ['NumPoints',]:
                item[key] = int(Obj.GetValue())
            else:
                item[key] = Obj.GetValue()
            if 'Refine' not in Obj.GetLabel():
                if 'FormFact' in key :
                    item['FFargs'] = FormFactors[Obj.GetValue()]
                elif 'StrFact' in key:
                    item['SFargs'] = StructureFactors[Obj.GetValue()]
                wx.CallAfter(UpdateModelsGrid,G2frame,data)
                G2sasd.ModelFxn(Profile,ProfDict,Limits,Sample,data)
                RefreshPlots(True)
                
        def OnDelLevel(event):
            Obj = event.GetEventObject()
            item = Indx[Obj.GetId()]
            del data['Particle']['Levels'][item]
            wx.CallAfter(UpdateModelsGrid,G2frame,data)
            G2sasd.ModelFxn(Profile,ProfDict,Limits,Sample,data)
            RefreshPlots(True)
            
        def OnParmSlider(event):
            Obj = event.GetEventObject()
            item,key,pvObj = Indx[Obj.GetId()]
            slide = Obj.GetValue()
            if key in ['P','epis','Sticky','Depth','Width','VolFr','Dist']:
                value = float(slide/slMult)
            else:
                value = 10.**float(slide/slMult)
            item[key][0] = value
            pvObj.SetValue('%.3g'%(item[key][0]))
            G2sasd.ModelFxn(Profile,ProfDict,Limits,Sample,data)
            RefreshPlots(True)
            
        def SizeSizer():
            sizeSizer = wx.FlexGridSizer(0,4,5,5)
            sizeSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Distribution: '),0,WACV)
            Distchoice = ['LogNormal','Gaussian','LSW','Schulz-Zimm','Bragg','Unified','Porod','Monodisperse',]
            distChoice = wx.ComboBox(G2frame.dataWindow,value=level['Controls']['DistType'],choices=Distchoice,
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
            Indx[distChoice.GetId()] = [level['Controls'],'DistType']
            distChoice.Bind(wx.EVT_COMBOBOX,OnSelect)
            sizeSizer.Add(distChoice,0,WACV)    #put structure factor choices here
            if level['Controls']['DistType'] not in ['Bragg','Unified','Porod',]:
                sizeSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Form Factor: '),0,WACV)
                if 'Mono' in level['Controls']['DistType']:
                    ffChoice = wx.ComboBox(G2frame.dataWindow,value=level['Controls']['FormFact'],choices=ffMonoChoices,
                        style=wx.CB_READONLY|wx.CB_DROPDOWN)
                else:
                    ffChoice = wx.ComboBox(G2frame.dataWindow,value=level['Controls']['FormFact'],choices=ffDistChoices,
                        style=wx.CB_READONLY|wx.CB_DROPDOWN)
                Indx[ffChoice.GetId()] = [level['Controls'],'FormFact']
                ffChoice.Bind(wx.EVT_COMBOBOX,OnSelect)
                sizeSizer.Add(ffChoice,0,WACV)
                
                sizeSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Material: '),0,WACV)
                matSel = wx.ComboBox(G2frame.dataWindow,value=level['Controls']['Material'],
                    choices=list(Substances['Substances'].keys()),style=wx.CB_READONLY|wx.CB_DROPDOWN)
                Indx[matSel.GetId()] = [level['Controls'],'Material']
                matSel.Bind(wx.EVT_COMBOBOX,OnSelect)        
                sizeSizer.Add(matSel,0,WACV) #do neutron test here?
                rho = Substances['Substances'][level['Controls']['Material']].get('XAnom density',0.0)
                level['Controls']['Contrast'] = contrast = (rho-rhoMat)**2                 
                sizeSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Resonant X-ray contrast: '),0,WACV)
                sizeSizer.Add(wx.StaticText(G2frame.dataWindow,label='  %.2f 10%scm%s'%(contrast,Pwr20,Pwrm4)),0,WACV)
                if 'Mono' not in level['Controls']['DistType']:
                    sizeSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Num. radii: '),0,WACV)
                    radii = ['25','50','75','100','200']
                    nRadii = wx.ComboBox(G2frame.dataWindow,value=str(level['Controls']['NumPoints']),choices=radii,
                        style=wx.CB_READONLY|wx.CB_DROPDOWN)
                    Indx[nRadii.GetId()] = [level['Controls'],'NumPoints']
                    nRadii.Bind(wx.EVT_COMBOBOX,OnSelect)
                    sizeSizer.Add(nRadii,0,WACV)
                    sizeSizer.Add(wx.StaticText(G2frame.dataWindow,label=' R dist. cutoff: '),0,WACV)
                    rCutoff = G2G.ValidatedTxtCtrl(G2frame.dataWindow,level['Controls'],'Cutoff',
                        xmin=0.001,xmax=0.1,typeHint=float)
                    sizeSizer.Add(rCutoff,0,WACV)
            elif level['Controls']['DistType']  in ['Unified',]:
                Parms = level['Unified']
                Best = G2sasd.Bestimate(Parms['G'][0],Parms['Rg'][0],Parms['P'][0])
                sizeSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Estimated Dist B: %12.4g'%(Best)),0,WACV)
            return sizeSizer
            
        def ParmSizer():
            parmSizer = wx.FlexGridSizer(0,3,5,5)
            parmSizer.AddGrowableCol(2,1)
            parmSizer.SetFlexibleDirection(wx.HORIZONTAL)
            Parms = level[level['Controls']['DistType']]
            FFargs = level['Controls']['FFargs']
            SFargs = level['Controls'].get('SFargs',{})
            parmOrder = ['Volume','Radius','Mean','StdDev','MinSize','G','Rg','B','P','Cutoff',
                'PkInt','PkPos','PkSig','PkGam',]
            for parm in parmOrder:
                if parm in Parms:
                    if parm == 'MinSize':
                        parmSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Dist '+parm),0,wx.ALIGN_CENTER)
                    else:
                        parmVar = wx.CheckBox(G2frame.dataWindow,label='Refine? Dist '+parm) 
                        parmVar.SetValue(Parms[parm][1])
                        parmVar.Bind(wx.EVT_CHECKBOX, OnSelect)
                        parmSizer.Add(parmVar,0,WACV)
                        Indx[parmVar.GetId()] = [Parms[parm],1]
#        azmthOff = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data,'azmthOff',nDig=(10,2),typeHint=float,OnLeave=OnAzmthOff)
                    parmValue = wx.TextCtrl(G2frame.dataWindow,value='%.3g'%(Parms[parm][0]),
                        style=wx.TE_PROCESS_ENTER)
                    parmValue.Bind(wx.EVT_TEXT_ENTER,OnValue)        
                    parmValue.Bind(wx.EVT_KILL_FOCUS,OnValue)
                    parmSizer.Add(parmValue,0,WACV)
                    if parm == 'P':
                        value = Parms[parm][0]
                        valMinMax = [0.1,4.2]
                    else:
                        value = np.log10(Parms[parm][0])
                        valMinMax = [value-1,value+1]
                    parmSldr = wx.Slider(G2frame.dataWindow,minValue=slMult*valMinMax[0],
                        maxValue=slMult*valMinMax[1],value=slMult*value)
                    Indx[parmValue.GetId()] = [Parms,parm,parmSldr]
                    Indx[parmSldr.GetId()] = [Parms,parm,parmValue]
                    parmSldr.Bind(wx.EVT_SLIDER,OnParmSlider)
                    parmSizer.Add(parmSldr,1,wx.EXPAND)
            if level['Controls']['DistType'] not in ['Bragg']:
                parmOrder = ['Aspect ratio','Length','Diameter','Thickness','VolFr','Dist','epis','Sticky','Depth','Width','Shell thickness',]
                fTypes = ['FF ','SF ']
                for iarg,Args in enumerate([FFargs,SFargs]):
                    for parm in parmOrder:
                        if parm in Args:
                            parmVar = wx.CheckBox(G2frame.dataWindow,label='Refine? '+fTypes[iarg]+parm) 
                            parmVar.SetValue(Args[parm][1])
                            Indx[parmVar.GetId()] = [Args[parm],1]
                            parmVar.Bind(wx.EVT_CHECKBOX, OnSelect)
                            parmSizer.Add(parmVar,0,WACV)
#        azmthOff = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data,'azmthOff',nDig=(10,2),typeHint=float,OnLeave=OnAzmthOff)
                            parmValue = wx.TextCtrl(G2frame.dataWindow,value='%.3g'%(Args[parm][0]),
                                style=wx.TE_PROCESS_ENTER)
                            parmValue.Bind(wx.EVT_TEXT_ENTER,OnValue)        
                            parmValue.Bind(wx.EVT_KILL_FOCUS,OnValue)
                            parmSizer.Add(parmValue,0,WACV)
                            value = Args[parm][0]
                            if parm == 'epis':
                                valMinMax = [0,.1]
                            elif parm in ['Sticky','Width',]:
                                valMinMax = [0,1.]
                            elif parm == 'Depth':
                                valMinMax = [-2.,2.]
                            elif parm == 'Dist':
                                valMinMax = [100.,1000.]
                            elif parm == 'VolFr':
                                valMinMax = [1.e-4,1.]
                            else:
                                value = np.log10(Args[parm][0])
                                valMinMax = [value-1,value+1]
                            parmSldr = wx.Slider(G2frame.dataWindow,minValue=slMult*valMinMax[0],
                                maxValue=slMult*valMinMax[1],value=slMult*value)
                            Indx[parmVar.GetId()] = [Args[parm],1]
                            Indx[parmValue.GetId()] = [Args,parm,parmSldr]
                            Indx[parmSldr.GetId()] = [Args,parm,parmValue]
                            parmSldr.Bind(wx.EVT_SLIDER,OnParmSlider)
                            parmSizer.Add(parmSldr,1,wx.EXPAND)
            return parmSizer

        Indx = {}
        partSizer = wx.BoxSizer(wx.VERTICAL)
        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        topSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Particle fit parameters: '),0,WACV)
        topSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Matrix: '),0,WACV)
        matsel = wx.ComboBox(G2frame.dataWindow,value=data['Particle']['Matrix']['Name'],
            choices=list(Substances['Substances'].keys()),style=wx.CB_READONLY|wx.CB_DROPDOWN)
        Indx[matsel.GetId()] = [data['Particle']['Matrix'],'Name'] 
        matsel.Bind(wx.EVT_COMBOBOX,OnSelect) #Do neutron test here?
        rhoMat = Substances['Substances'][data['Particle']['Matrix']['Name']].get('XAnom density',0.0)        
        topSizer.Add(matsel,0,WACV)
        topSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Volume fraction: '),0,WACV)
        volfrac = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Particle']['Matrix']['VolFrac'],0,
                typeHint=float)
        topSizer.Add(volfrac,0,WACV)
        volVar = wx.CheckBox(G2frame.dataWindow,label=' Refine?')
        volVar.SetValue(data['Particle']['Matrix']['VolFrac'][1])
        Indx[volVar.GetId()] = [data['Particle']['Matrix']['VolFrac'],1]
        volVar.Bind(wx.EVT_CHECKBOX, OnSelect)
        topSizer.Add(volVar,0,WACV)
        partSizer.Add(topSizer,0,)
        for ilev,level in enumerate(data['Particle']['Levels']):
            G2G.HorizontalLine(partSizer,G2frame.dataWindow)
            topLevel = wx.BoxSizer(wx.HORIZONTAL)
            topLevel.Add(wx.StaticText(G2frame.dataWindow,label=' Model component %d: '%(ilev)),0,WACV)
            delBtn = wx.Button(G2frame.dataWindow,label=' Delete?')
            Indx[delBtn.GetId()] = ilev
            delBtn.Bind(wx.EVT_BUTTON,OnDelLevel)
            topLevel.Add(delBtn,0,WACV)
            partSizer.Add(topLevel,0)
            partSizer.Add(SizeSizer())
            if level['Controls']['DistType'] not in ['Bragg','Unified','Porod',]:
                topLevel.Add(wx.StaticText(G2frame.dataWindow,label=' Structure factor: '),0,WACV)
                strfctr = wx.ComboBox(G2frame.dataWindow,value=level['Controls']['StrFact'],
                    choices=sfChoices,style=wx.CB_READONLY|wx.CB_DROPDOWN)
                Indx[strfctr.GetId()] = [level['Controls'],'StrFact']
                strfctr.Bind(wx.EVT_COMBOBOX,OnSelect)
                topLevel.Add(strfctr,0,WACV)
            partSizer.Add(ParmSizer(),0,wx.EXPAND)
        return partSizer
        
    def OnEsdScale(event):
        event.Skip()
        try:
            value = float(esdScale.GetValue())
            if value <= 0.:
                raise ValueError
        except ValueError:
            value = 1./np.sqrt(ProfDict['wtFactor'])
        ProfDict['wtFactor'] = 1./value**2
        esdScale.SetValue('%.3f'%(value))
        RefreshPlots(True)
        
    def OnBackChange(invalid,value,tc):
        Profile[4][:] = value
        RefreshPlots()
        
    def OnBackFile(event):  #multiple backgrounds?
        data['BackFile'] = backFile.GetValue()
        if data['BackFile']:
            BackId = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,data['BackFile'])
            BackSample = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,BackId, 'Sample Parameters'))
            Profile[5] = BackSample['Scale'][0]*G2frame.GPXtree.GetItemPyData(BackId)[1][1]
        else:
            Profile[5] = np.zeros(len(Profile[5]))
        RefreshPlots(True)
            
    Sample = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Sample Parameters'))
    Limits = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Limits'))
    Substances = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Substances'))
    ProfDict,Profile = G2frame.GPXtree.GetItemPyData(G2frame.PatternId)[:2]
    if data['BackFile']:
        BackId = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,data['BackFile'])
        BackSample = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,BackId, 'Sample Parameters'))
        Profile[5] = BackSample['Scale'][0]*G2frame.GPXtree.GetItemPyData(BackId)[1][1]
    G2gd.SetDataMenuBar(G2frame,G2frame.dataWindow.ModelMenu)
    G2frame.dataWindow.ClearData()
    G2frame.Bind(wx.EVT_MENU, OnCopyModel, id=G2G.wxID_MODELCOPY)
    G2frame.Bind(wx.EVT_MENU, OnCopyFlags, id=G2G.wxID_MODELCOPYFLAGS)
    G2frame.Bind(wx.EVT_MENU, OnFitModel, id=G2G.wxID_MODELFIT)
    G2frame.Bind(wx.EVT_MENU, OnFitModelAll, id=G2G.wxID_MODELFITALL)
    G2frame.Bind(wx.EVT_MENU, OnUnDo, id=G2G.wxID_MODELUNDO)
    G2frame.Bind(wx.EVT_MENU, OnAddModel, id=G2G.wxID_MODELADD)
    Indx = {}
    G2frame.dataWindow.ClearData()
    mainSizer = G2frame.dataWindow.GetSizer()
    topSizer = wx.BoxSizer(wx.HORIZONTAL)
    models = ['Size dist.','Particle fit','Pair distance',]
    if len(data['Pair']['Distribution']):
        models += ['Shapes',]
    topSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Modeling by: '),0,WACV)
    fitSel = wx.ComboBox(G2frame.dataWindow,value=data['Current'],choices=models,
        style=wx.CB_READONLY|wx.CB_DROPDOWN)
    fitSel.Bind(wx.EVT_COMBOBOX,OnSelectFit)        
    topSizer.Add(fitSel,0,WACV)
    topSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Error multiplier: '),0,WACV)
#        azmthOff = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data,'azmthOff',nDig=(10,2),typeHint=float,OnLeave=OnAzmthOff)
    esdScale = wx.TextCtrl(G2frame.dataWindow,value='%.3f'%(1./np.sqrt(ProfDict['wtFactor'])),style=wx.TE_PROCESS_ENTER)
    esdScale.Bind(wx.EVT_TEXT_ENTER,OnEsdScale)        
    esdScale.Bind(wx.EVT_KILL_FOCUS,OnEsdScale)
    topSizer.Add(esdScale,0,WACV)
    mainSizer.Add(topSizer)
    G2G.HorizontalLine(mainSizer,G2frame.dataWindow)
    if 'Size' in data['Current']:
        G2frame.dataWindow.SasSeqFit.Enable(False)
        if 'MaxEnt' in data['Size']['Method']:
            G2frame.GetStatusBar().SetStatusText('Size distribution by Maximum entropy',1)
        elif 'IPG' in data['Size']['Method']:
            G2frame.GetStatusBar().SetStatusText('Size distribution by Interior-Point Gradient',1)
        mainSizer.Add(SizeSizer())        
    elif 'Particle' in data['Current']:
        G2frame.dataWindow.SasSeqFit.Enable(True)
        mainSizer.Add(PartSizer(),1,wx.ALIGN_LEFT|wx.EXPAND)
    elif 'Pair' in data['Current']:
        G2frame.dataWindow.SasSeqFit.Enable(False)
        mainSizer.Add(PairSizer(),1,wx.ALIGN_LEFT|wx.EXPAND)
    elif 'Shape' in data['Current']:
        G2frame.dataWindow.SasSeqFit.Enable(False)
        mainSizer.Add(ShapesSizer(),1,wx.ALIGN_LEFT|wx.EXPAND)
    G2G.HorizontalLine(mainSizer,G2frame.dataWindow)    
    backSizer = wx.BoxSizer(wx.HORIZONTAL)
    backSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Background:'),0,WACV)
    backVal = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Back'],0,
        nDig=(10,3,'g'),OnLeave=OnBackChange)
    backSizer.Add(backVal,0,WACV)
    if 'Shape' not in data['Current']:
        backVar = wx.CheckBox(G2frame.dataWindow,label='Refine?')
        Indx[backVar.GetId()] = [data['Back'],1]
        backVar.SetValue(data['Back'][1])
        backVar.Bind(wx.EVT_CHECKBOX, OnCheckBox)
        backSizer.Add(backVar,0,WACV)
        #multiple background files?
    backSizer.Add(wx.StaticText(G2frame.dataWindow,-1,' Background file: '),0,WACV)
    Choices = ['',]+G2gd.GetGPXtreeDataNames(G2frame,['SASD',])
    backFile = wx.ComboBox(parent=G2frame.dataWindow,value=data['BackFile'],choices=Choices,
        style=wx.CB_READONLY|wx.CB_DROPDOWN)
    backFile.Bind(wx.EVT_COMBOBOX,OnBackFile)
    backSizer.Add(backFile)    
    mainSizer.Add(backSizer)
    G2frame.dataWindow.SetDataSize()

################################################################################
#####  REFD Models 
################################################################################           
       
def UpdateREFDModelsGrid(G2frame,data):
    '''respond to selection of REFD Models data tree item.
    '''
    def OnCopyModel(event):
        hst = G2frame.GPXtree.GetItemText(G2frame.PatternId)
        histList = GetHistsLikeSelected(G2frame)
        if not histList:
            G2frame.ErrorDialog('No match','No histograms match '+hst,G2frame)
            return
        copyList = []
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Copy reflectivity models from\n'+str(hst[5:])+' to...',
            'Copy parameters', histList)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                for i in dlg.GetSelections():
                    copyList.append(histList[i])
        finally:
            dlg.Destroy()
        for item in copyList:
            Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,item)
            G2frame.GPXtree.SetItemPyData(
                G2gd.GetGPXtreeItemId(G2frame,Id,'Models'),copy.deepcopy(data))
        
    def OnFitModel(event):
        
        SaveState()
        G2pwd.REFDRefine(Profile,ProfDict,Inst,Limits,Substances,data)
        x,xr,y = G2pwd.makeSLDprofile(data,Substances)
        ModelPlot(data,x,xr,y)
        G2plt.PlotPatterns(G2frame,plotType='REFD')
        wx.CallAfter(UpdateREFDModelsGrid,G2frame,data)
        
    def OnModelPlot(event):
        hst = G2frame.GPXtree.GetItemText(G2frame.PatternId)
        histList = GetFileList(G2frame,'REFD')
#        histList = [hst,]
#        histList += GetHistsLikeSelected(G2frame)
        if not histList:
            G2frame.ErrorDialog('No match','No histograms match '+hst,G2frame)
            return
        plotList = []
        od = {'label_1':'Zero at substrate','value_1':False,'label_2':'Show layer transitions','value_2':True}
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Plot reflectivity models for:',
            'Plot SLD models', histList,extraOpts=od)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                for i in dlg.GetSelections():
                    plotList.append(histList[i])
            else:
                dlg.Destroy()
                return
        finally:
            dlg.Destroy()
        XY = []
        LinePos = []
        for item in plotList:
            mId = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,item)
            model = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,mId,'Models'))
            Substances = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,mId,'Substances'))['Substances']       
            x,xr,y = G2pwd.makeSLDprofile(model,Substances)
            if od['value_1']:
                XY.append([xr,y])
                disLabel = r'$Distance\ from\ substrate,\ \AA$'
            else:
                XY.append([x,y])
                disLabel = r'$Distance\ from\ top\ surface,\ \AA$'
            if od['value_2']:
                laySeq = model['Layer Seq'].split()
                nLines = len(laySeq)+1
                linePos = np.zeros(nLines)
                for ilay,lay in enumerate(np.fromstring(data['Layer Seq'],dtype=int,sep=' ')):
                    linePos[ilay+1:] += model['Layers'][lay].get('Thick',[0.,False])[0]
                if od['value_1']:
                    linePos = linePos[-1]-linePos
                LinePos.append(linePos)
        G2plt.PlotXY(G2frame,XY,labelX=disLabel,labelY=r'$SLD,\ 10^{10}cm^{-2}$',newPlot=True,   
                      Title='Scattering length density',lines=True,names=[],vertLines=LinePos)
        
    def OnFitModelAll(event):
        choices = G2gd.GetGPXtreeDataNames(G2frame,['REFD',])
        od = {'label_1':'Copy to next','value_1':False,'label_2':'Reverse order','value_2':False}
        dlg = G2G.G2MultiChoiceDialog(G2frame, 'Sequential REFD refinement',
             'Select dataset to include',choices,extraOpts=od)
        names = []
        if dlg.ShowModal() == wx.ID_OK:
            for sel in dlg.GetSelections():
                names.append(choices[sel])
            Id =  G2gd.GetGPXtreeItemId(G2frame,G2frame.root,'Sequential REFD results')
            if Id:
                SeqResult = G2frame.GPXtree.GetItemPyData(Id)
            else:
                SeqResult = {}
                Id = G2frame.GPXtree.AppendItem(parent=G2frame.root,text='Sequential REFD results')
            SeqResult = {'SeqPseudoVars':{},'SeqParFitEqList':[]}
            SeqResult['histNames'] = names
        else:
            dlg.Destroy()
            return
        dlg.Destroy()
        dlg = wx.ProgressDialog('REFD Sequential fit','Data set name = '+names[0],len(names), 
            style = wx.PD_ELAPSED_TIME|wx.PD_AUTO_HIDE|wx.PD_REMAINING_TIME|wx.PD_CAN_ABORT)
        wx.BeginBusyCursor()
        if od['value_2']:
            names.reverse()
        JModel = None
        try:
            for i,name in enumerate(names):
                print (' Sequential fit for '+name)
                GoOn = dlg.Update(i,newmsg='Data set name = '+name)[0]
                if not GoOn:
                    break
                sId =  G2gd.GetGPXtreeItemId(G2frame,G2frame.root,name)
                if i and od['value_1']:
                    G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,sId, 'Models'),JModel)
                IProfDict,IProfile = G2frame.GPXtree.GetItemPyData(sId)[:2]
                IModel = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,sId, 'Models'))
                ISubstances = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,sId, 'Substances'))['Substances']
                ILimits = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,sId, 'Limits'))
                IfOK,result,varyList,sig,Rvals,covMatrix,parmDict,Msg = G2pwd.REFDRefine(IProfile,IProfDict,Inst,ILimits,ISubstances,IModel)
                JModel = copy.deepcopy(IModel)
                if not IfOK:
                    G2frame.ErrorDialog('Failed sequential refinement for data '+name,
                        ' Msg: '+Msg+'\nYou need to rethink your selection of parameters\n'+    \
                        ' Model restored to previous version for'+name)
                    SeqResult['histNames'] = names[:i]
                    dlg.Destroy()
                    break
                else:
                    G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,sId, 'Models'),copy.deepcopy(IModel))
                
                SeqResult[name] = {'variables':result[0],'varyList':varyList,'sig':sig,'Rvals':Rvals,
                    'covMatrix':covMatrix,'title':name,'parmDict':parmDict}
            else:
                dlg.Destroy()
                print (' ***** Small angle sequential refinement successful *****')
        finally:
            wx.EndBusyCursor()    
        G2frame.GPXtree.SetItemPyData(Id,SeqResult)
        G2frame.GPXtree.SelectItem(Id)
                
    def ModelPlot(data,x,xr,y):
        laySeq = data['Layer Seq'].split()
        nLines = len(laySeq)+1
        linePos = np.zeros(nLines)
        for ilay,lay in enumerate(np.fromstring(data['Layer Seq'],dtype=int,sep=' ')):
            linePos[ilay+1:] += data['Layers'][lay].get('Thick',[0.,False])[0]
        if data['Zero'] == 'Top':
            XY = [[x,y],]
            disLabel = r'$Distance\ from\ top\ surface,\ \AA$'
        else:
            XY = [[xr,y],]
            linePos = linePos[-1]-linePos
            disLabel = r'$Distance\ from\ substrate,\ \AA$'
        G2plt.PlotXY(G2frame,XY,labelX=disLabel,labelY=r'$SLD,\ 10^{10}cm^{-2}$',newPlot=True,
            Title='Scattering length density',lines=True,names=[],vertLines=[linePos,])
        
    def OnUnDo(event):
        DoUnDo()
        data = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,
            G2frame.PatternId,'Models'))
        G2frame.dataWindow.REFDUndo.Enable(False)
        G2pwd.REFDModelFxn(Profile,Inst,Limits,Substances,data)
        x,xr,y = G2pwd.makeSLDprofile(data,Substances)
        ModelPlot(data,x,xr,y)
        G2plt.PlotPatterns(G2frame,plotType='REFD')
        wx.CallLater(100,UpdateREFDModelsGrid,G2frame,data)

    def DoUnDo():
        print ('Undo last refinement')
        file = open(G2frame.undorefd,'rb')
        PatternId = G2frame.PatternId
        G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'Models'),cPickle.load(file))
        print (' Model recovered')
        file.close()
        
    def SaveState():
        G2frame.undorefd = os.path.join(G2frame.dirname,'GSASIIrefd.save')
        file = open(G2frame.undorefd,'wb')
        PatternId = G2frame.PatternId
        cPickle.dump(G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId,'Models')),file,1)
        file.close()
        G2frame.dataWindow.REFDUndo.Enable(True)
    
    def ControlSizer():
        
        def OnRefPos(event):
            data['Zero'] = refpos.GetValue()
            x,xr,y = G2pwd.makeSLDprofile(data,Substances)
            ModelPlot(data,x,xr,y)
            
        def OnMinSel(event):
            data['Minimizer'] = minSel.GetValue()
            
        def OnWeight(event):
            data['2% weight'] = weight.GetValue()
            
        def OnSLDplot(event):
            x,xr,y = G2pwd.makeSLDprofile(data,Substances)
            ModelPlot(data,x,xr,y)
            
#        def OnQ4fftplot(event):
#            q4fft.SetValue(False)
#            R,F = G2pwd.makeRefdFFT(Limits,Profile)
#            XY = [[R[:2500],F[:2500]],]
#            G2plt.PlotXY(G2frame,XY,labelX='thickness',labelY='F(R)',newPlot=True,
#                Title='Fourier transform',lines=True)
            
        def OndQSel(event):
            data['dQ type'] = dQSel.GetStringSelection()
            Recalculate()
            
        def NewRes(invalid,value,tc):
            Recalculate()
            
        def Recalculate():
            G2pwd.REFDModelFxn(Profile,Inst,Limits,Substances,data)
            x,xr,y = G2pwd.makeSLDprofile(data,Substances)
            ModelPlot(data,x,xr,y)
            G2plt.PlotPatterns(G2frame,plotType='REFD')
            
        controlSizer = wx.BoxSizer(wx.VERTICAL)
        resol = wx.BoxSizer(wx.HORIZONTAL)
        choice = ['None','const '+GkDelta+'Q/Q',]
        if ProfDict['ifDQ']:
            choice += [GkDelta+'Q/Q in data']
        dQSel = wx.RadioBox(G2frame.dataWindow,wx.ID_ANY,'Instrument resolution type:',choices=choice,
            majorDimension=0,style=wx.RA_SPECIFY_COLS)
        dQSel.SetStringSelection(data['dQ type'])
        dQSel.Bind(wx.EVT_RADIOBOX,OndQSel)
        resol.Add(dQSel,0,WACV)
        resol.Add(wx.StaticText(G2frame.dataWindow,label=' (FWHM %): '),0,WACV)
        resol.Add(G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Resolution'],0,nDig=(10,3),xmin=0.,xmax=5.,OnLeave=NewRes),0,WACV)
        controlSizer.Add(resol,0)
        minimiz = wx.BoxSizer(wx.HORIZONTAL)
        minimiz.Add(wx.StaticText(G2frame.dataWindow,label=' Minimizer: '),0,WACV)
        minlist = ['LMLS','Basin Hopping','MC/SA Anneal','L-BFGS-B',]
        minSel = wx.ComboBox(G2frame.dataWindow,value=data['Minimizer'],choices=minlist,
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        minSel.Bind(wx.EVT_COMBOBOX, OnMinSel)
        minimiz.Add(minSel,0,WACV)
        minimiz.Add(wx.StaticText(G2frame.dataWindow,label=' Bounds factor: '),0,WACV)
        minimiz.Add(G2G.ValidatedTxtCtrl(G2frame.dataWindow,data,'Toler',nDig=(10,2),xmax=0.99,xmin=0.1),0,WACV)
        weight = wx.CheckBox(G2frame.dataWindow,label='Use 2% sig. weights')
        weight.SetValue(data.get('2% weight',False))
        weight.Bind(wx.EVT_CHECKBOX, OnWeight)
        minimiz.Add(weight,0,WACV)
        controlSizer.Add(minimiz,0)
        plotSizer = wx.BoxSizer(wx.HORIZONTAL)
        plotSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Plot controls: '),0,WACV)
        sld = wx.Button(G2frame.dataWindow,label='Plot SLD?')
        sld.Bind(wx.EVT_BUTTON, OnSLDplot)
        plotSizer.Add(sld,0,WACV)
        plotSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Zero position location: '),0,WACV)
        poslist = ['Top','Bottom']
        refpos = wx.ComboBox(G2frame.dataWindow,value=data['Zero'],choices=poslist,
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        refpos.Bind(wx.EVT_COMBOBOX, OnRefPos)
        plotSizer.Add(refpos,0,WACV)
#        q4fft = wx.CheckBox(G2frame.dataWindow,label='Plot fft?')
#        q4fft.Bind(wx.EVT_CHECKBOX, OnQ4fftplot)
#        plotSizer.Add(q4fft,0,WACV)
        controlSizer.Add(plotSizer,0)
        return controlSizer
    
    def OverallSizer():
#'DualFitFile':'', 'DualFltBack':[0.0,False],'DualScale':[1.0,False] future for neutrons - more than one?
        
        def OnScaleRef(event):
            data['Scale'][1] = scaleref.GetValue()
            
        def OnBackRef(event):
            data['FltBack'][1] = backref.GetValue()
            
        def Recalculate(invalid,value,tc):
            if invalid:
                return
            
            G2pwd.REFDModelFxn(Profile,Inst,Limits,Substances,data)
            x,xr,y = G2pwd.makeSLDprofile(data,Substances)
            ModelPlot(data,x,xr,y)
            G2plt.PlotPatterns(G2frame,plotType='REFD')

        overall = wx.BoxSizer(wx.HORIZONTAL)
        overall.Add(wx.StaticText(G2frame.dataWindow,label=' Scale: '),0,WACV)
        overall.Add(G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Scale'],0,
            nDig=(10,2),typeHint=float,OnLeave=Recalculate),0,WACV)
        scaleref = wx.CheckBox(G2frame.dataWindow,label=' Refine?  ')
        scaleref.SetValue(data['Scale'][1])
        scaleref.Bind(wx.EVT_CHECKBOX, OnScaleRef)
        overall.Add(scaleref,0,WACV)
        overall.Add(wx.StaticText(G2frame.dataWindow,label=' Flat bkg.: '),0,WACV)
        overall.Add(G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['FltBack'],0,
            nDig=(10,2,'g'),typeHint=float,OnLeave=Recalculate),0,WACV)
        backref = wx.CheckBox(G2frame.dataWindow,label=' Refine?  ')
        backref.SetValue(data['FltBack'][1])
        backref.Bind(wx.EVT_CHECKBOX, OnBackRef)
        overall.Add(backref,0,WACV)        
        return overall
        
    def LayerSizer():
    #'Penetration':[0.,False]?

        def OnSelect(event):
            Obj = event.GetEventObject()
            item = Indx[Obj.GetId()]
            Name = Obj.GetValue()
            data['Layers'][item]['Name'] = Name
            if 'Rough' not in data['Layers'][item]:
                data['Layers'][item]['Rough'] = [0.,False]
            if 'Thick' not in data['Layers'][item]:
                data['Layers'][item]['Thick'] = [10.,False]
            if 'N' in Inst['Type'][0]:
                data['Layers'][item]['Mag SLD'] = [0.,False]
            if Name == 'unit scatter':
                data['Layers'][item]['iDenMul'] = [0.,False]
            G2pwd.REFDModelFxn(Profile,Inst,Limits,Substances,data)
            G2plt.PlotPatterns(G2frame,plotType='REFD')
            wx.CallAfter(UpdateREFDModelsGrid,G2frame,data)
            
        def OnCheckBox(event):
            Obj = event.GetEventObject()
            item,parm = Indx[Obj.GetId()]
            data['Layers'][item][parm][1] = Obj.GetValue()
            
        def OnInsertLayer(event):
            Obj = event.GetEventObject()
            ind = Indx[Obj.GetId()]
            data['Layers'].insert(ind+1,{'Name':'vacuum','DenMul':[1.0,False],})
            data['Layer Seq'] = ' '.join([str(i+1) for i in range(len(data['Layers'])-2)])
            G2pwd.REFDModelFxn(Profile,Inst,Limits,Substances,data)
            G2plt.PlotPatterns(G2frame,plotType='REFD')
            wx.CallAfter(UpdateREFDModelsGrid,G2frame,data)
            
        def OnDeleteLayer(event):
            Obj = event.GetEventObject()
            ind = Indx[Obj.GetId()]
            del data['Layers'][ind]
            data['Layer Seq'] = ' '.join([str(i+1) for i in range(len(data['Layers'])-2)])
            G2pwd.REFDModelFxn(Profile,Inst,Limits,Substances,data)
            G2plt.PlotPatterns(G2frame,plotType='REFD')
            wx.CallAfter(UpdateREFDModelsGrid,G2frame,data) 

        def Recalculate(invalid,value,tc):
            if invalid:
                return
            G2pwd.REFDModelFxn(Profile,Inst,Limits,Substances,data)
            x,xr,y = G2pwd.makeSLDprofile(data,Substances)
            ModelPlot(data,x,xr,y)
            G2plt.PlotPatterns(G2frame,plotType='REFD')
#            wx.CallLater(100,UpdateREFDModelsGrid,G2frame,data) 

        Indx = {}                       
        layerSizer = wx.BoxSizer(wx.VERTICAL)
        
        for ilay,layer in enumerate(data['Layers']):
            if not ilay:
                layerSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Top layer (superphase):'),0)
            elif ilay < len(data['Layers'])-1:
                layerSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Layer no. %d'%(ilay)),0)
            else:
                layerSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Bottom layer (substrate):'),0)
            midlayer = wx.BoxSizer(wx.HORIZONTAL)
            midlayer.Add(wx.StaticText(G2frame.dataWindow,label=' Substance: '),0,WACV)
            midName = data['Layers'][ilay]['Name']
            midSel = wx.ComboBox(G2frame.dataWindow,value=midName,
                choices=list(Substances.keys()),style=wx.CB_READONLY|wx.CB_DROPDOWN)
            Indx[midSel.GetId()] = ilay
            midSel.Bind(wx.EVT_COMBOBOX,OnSelect)
            midlayer.Add(midSel,0,WACV)
            if midName != 'vacuum':
                if midName != 'unit scatter':
                    midlayer.Add(wx.StaticText(G2frame.dataWindow,label=' Den. Mult.: '),0,WACV)
                    midlayer.Add(G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Layers'][ilay]['DenMul'],0,
                        nDig=(10,4),OnLeave=Recalculate),0,WACV)
                    varBox = wx.CheckBox(G2frame.dataWindow,label='Refine?')
                    Indx[varBox.GetId()] = [ilay,'DenMul']
                    varBox.SetValue(data['Layers'][ilay]['DenMul'][1])
                    varBox.Bind(wx.EVT_CHECKBOX, OnCheckBox)
                    midlayer.Add(varBox,0,WACV)
                    realScatt = data['Layers'][ilay]['DenMul'][0]*Substances[midName]['Scatt density']
                    midlayer.Add(wx.StaticText(G2frame.dataWindow,
                        label=' Real scat. den.: %.4g'%(realScatt)),0,WACV)
                    imagScatt = data['Layers'][ilay]['DenMul'][0]*Substances[midName]['XImag density']
                    midlayer.Add(wx.StaticText(G2frame.dataWindow,
                        label=' Imag scat. den.: %.4g'%(imagScatt)),0,WACV)
                else:
                    realScatt = data['Layers'][ilay]['DenMul'][0]
                    midlayer.Add(wx.StaticText(G2frame.dataWindow,
                        label=' Real scat. den.: %.4g'%(realScatt)),0,WACV)
                    imagScatt = data['Layers'][ilay]['iDenMul'][0]
                    midlayer.Add(wx.StaticText(G2frame.dataWindow,
                        label=' Imag scat. den.: %.4g'%(imagScatt)),0,WACV)                    
            else:
                midlayer.Add(wx.StaticText(G2frame.dataWindow,label=', air or gas'),0,WACV)
            layerSizer.Add(midlayer)
            if midName == 'unit scatter':
                nxtlayer = wx.BoxSizer(wx.HORIZONTAL)
                nxtlayer.Add(wx.StaticText(G2frame.dataWindow,label=' Real Den. : '),0,WACV)                
                nxtlayer.Add(G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Layers'][ilay]['DenMul'],0,
                    nDig=(10,4),OnLeave=Recalculate),0,WACV)
                varBox = wx.CheckBox(G2frame.dataWindow,label='Refine?')
                Indx[varBox.GetId()] = [ilay,'DenMul']
                varBox.SetValue(data['Layers'][ilay]['DenMul'][1])
                varBox.Bind(wx.EVT_CHECKBOX, OnCheckBox)
                nxtlayer.Add(varBox,0,WACV)
                nxtlayer.Add(wx.StaticText(G2frame.dataWindow,label=' Imag Den. : '),0,WACV)                
                nxtlayer.Add(G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Layers'][ilay]['iDenMul'],0,
                    nDig=(10,4),OnLeave=Recalculate),0,WACV)
                varBox = wx.CheckBox(G2frame.dataWindow,label='Refine?')
                Indx[varBox.GetId()] = [ilay,'iDenMul']
                varBox.SetValue(data['Layers'][ilay]['iDenMul'][1])
                varBox.Bind(wx.EVT_CHECKBOX, OnCheckBox)
                nxtlayer.Add(varBox,0,WACV)
                layerSizer.Add(nxtlayer)
            if midName != 'vacuum':
                if 'N' in Inst['Type'][0] and midName not in ['vacuum','unit scatter']:
                    magLayer = wx.BoxSizer(wx.HORIZONTAL)
                    magLayer.Add(wx.StaticText(G2frame.dataWindow,label=' Magnetic SLD: '),0,WACV)
                    magLayer.Add(G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Layers'][ilay]['Mag SLD'],0,
                        nDig=(10,4),OnLeave=Recalculate),0,WACV)
                    varBox = wx.CheckBox(G2frame.dataWindow,label='Refine?')
                    Indx[varBox.GetId()] = [ilay,'Mag SLD']
                    varBox.SetValue(data['Layers'][ilay]['Mag SLD'][1])
                    varBox.Bind(wx.EVT_CHECKBOX, OnCheckBox)
                    magLayer.Add(varBox,0,WACV)
                    magLayer.Add(wx.StaticText(G2frame.dataWindow,
                        label=' Real+mag scat. den.: %.4g'%(realScatt+data['Layers'][ilay]['Mag SLD'][0])),0,WACV)
                    layerSizer.Add(magLayer)
                if ilay:
                    names = {'Rough':'Upper surface Roughness, '+Angstr,'Thick':'Layer Thickness, '+Angstr}
                    parmsline = wx.BoxSizer(wx.HORIZONTAL)
                    parms= ['Rough','Thick']
                    if ilay == len(data['Layers'])-1:
                        parms = ['Rough',]
                    for parm in parms:
                        parmsline.Add(wx.StaticText(G2frame.dataWindow,label=' %s: '%(names[parm])),0,WACV)
                        parmsline.Add(G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['Layers'][ilay][parm],0,
                            nDig=(10,2),OnLeave=Recalculate),0,WACV)
                        varBox = wx.CheckBox(G2frame.dataWindow,label='Refine?')
                        Indx[varBox.GetId()] = [ilay,parm]
                        varBox.SetValue(data['Layers'][ilay][parm][1])
                        varBox.Bind(wx.EVT_CHECKBOX, OnCheckBox)
                        parmsline.Add(varBox,0,WACV)
                    layerSizer.Add(parmsline)
            if ilay < len(data['Layers'])-1:
                newlayer = wx.BoxSizer(wx.HORIZONTAL)
                insert = wx.Button(G2frame.dataWindow,label='Insert')
                Indx[insert.GetId()] = ilay
                insert.Bind(wx.EVT_BUTTON,OnInsertLayer)
                newlayer.Add(insert)
                delet = wx.Button(G2frame.dataWindow,label='Delete')
                Indx[delet.GetId()] = ilay
                delet.Bind(wx.EVT_BUTTON,OnDeleteLayer)
                newlayer.Add(delet)
                layerSizer.Add(newlayer)
                G2G.HorizontalLine(layerSizer,G2frame.dataWindow)   
        
        return layerSizer
        
    def OnRepSeq(event):
        event.Skip()
        stack = repseq.GetValue()
        nstar = stack.count('*')
        if nstar:
            try:
                newstack = ''
                Istar = 0
                for star in range(nstar):
                    Istar = stack.index('*',Istar+1)
                    iB = stack[:Istar].rfind(' ')
                    if iB == -1:
                        mult = int(stack[:Istar])
                    else:
                        mult = int(stack[iB:Istar])
                    pattern = stack[Istar+2:stack.index(')',Istar)]+' '
                    newstack += mult*pattern
                stack = newstack
            except ValueError:
                stack += ' Error in string'
                wx.MessageBox(stack,'Error',style=wx.ICON_EXCLAMATION)
                repseq.SetValue(data['Layer Seq'])
                return
        try:
            Slist = np.array(stack.split(),dtype=int)
        except ValueError:
            stack += ' Error in string'
            repseq.SetValue(data['Layer Seq'])
            wx.MessageBox(stack,'Error',style=wx.ICON_EXCLAMATION)
            return
        if len(Slist) < 1:
            stack += ' Error in sequence - too short!'
        Stest = np.arange(1,Nlayers-1)
        if not np.all(np.array([item in Stest for item in Slist])):
            stack += ' Error: invalid layer selection'
        elif not np.all(np.ediff1d(Slist)):
            stack += ' Error: Improbable sequence or bad string'
        if 'Error' in stack:
            repseq.SetValue(data['Layer Seq'])
            wx.MessageBox(stack,'Error',style=wx.ICON_EXCLAMATION)
            return
        else:
            data['Layer Seq'] = stack
            repseq.SetValue(stack)
            G2pwd.REFDModelFxn(Profile,Inst,Limits,Substances,data)
            x,xr,y = G2pwd.makeSLDprofile(data,Substances)
            ModelPlot(data,x,xr,y)
            G2plt.PlotPatterns(G2frame,plotType='REFD')
    
    Substances = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Substances'))['Substances']
    ProfDict,Profile,Name = G2frame.GPXtree.GetItemPyData(G2frame.PatternId)[:3]
    if 'ifDQ' not in ProfDict:
        ProfDict['ifDQ'] = np.any(Profile[5])
        data['dQ type'] = 'None'
    Limits = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Limits'))
    Inst = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.PatternId, 'Instrument Parameters'))[0]
    G2gd.SetDataMenuBar(G2frame,G2frame.dataWindow.REFDModelMenu)
    G2frame.dataWindow.ClearData()
    G2frame.Bind(wx.EVT_MENU, OnCopyModel, id=G2G.wxID_MODELCOPY)
    G2frame.Bind(wx.EVT_MENU, OnModelPlot, id=G2G.wxID_MODELPLOT)
    G2frame.Bind(wx.EVT_MENU, OnFitModel, id=G2G.wxID_MODELFIT)
    G2frame.Bind(wx.EVT_MENU, OnFitModelAll, id=G2G.wxID_MODELFITALL)
    G2frame.Bind(wx.EVT_MENU, OnUnDo, id=G2G.wxID_MODELUNDO)
    G2frame.dataWindow.ClearData()
    mainSizer = G2frame.dataWindow.GetSizer()
    mainSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Reflectometry fitting for: '+Name),0,WACV)
    mainSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Controls:'),0,WACV)
    mainSizer.Add(ControlSizer())
    G2G.HorizontalLine(mainSizer,G2frame.dataWindow)   
    mainSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Global parameters:'),0,WACV)
    mainSizer.Add(OverallSizer()) 
    G2G.HorizontalLine(mainSizer,G2frame.dataWindow)
    Nlayers = len(data['Layers'])
    if Nlayers > 2:
        if 'Layer Seq' not in data:
            data['Layer Seq'] = ' '.join([str(i+1) for i in range(Nlayers-2)])
        lineSizer = wx.BoxSizer(wx.HORIZONTAL)
        lineSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Layer sequence: '),0,WACV)
        repseq = wx.TextCtrl(G2frame.dataWindow,value = data['Layer Seq'],style=wx.TE_PROCESS_ENTER,size=(500,25))
        repseq.Bind(wx.EVT_TEXT_ENTER,OnRepSeq)        
        repseq.Bind(wx.EVT_KILL_FOCUS,OnRepSeq)
        lineSizer.Add(repseq,0,WACV)
        mainSizer.Add(lineSizer)
        Str = ' Use sequence nos. from:'
        for ilay,layer in enumerate(data['Layers'][1:-1]):
            Str += ' %d: %s'%(ilay+1,layer['Name'])
        mainSizer.Add(wx.StaticText(G2frame.dataWindow,label=Str),0,WACV)
        mainSizer.Add(wx.StaticText(G2frame.dataWindow,label=' NB: Repeat sequence by e.g. 6*(1 2) '),0,WACV)
    G2G.HorizontalLine(mainSizer,G2frame.dataWindow)    
    mainSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Layers: scatt. densities are 10%scm%s = 10%s%s%s'%(Pwr10,Pwrm2,Pwrm6,Angstr,Pwrm2)),0,WACV)
    mainSizer.Add(LayerSizer())
    G2frame.dataWindow.SetDataSize()
    
################################################################################
#####  PDF controls
################################################################################           
def computePDF(G2frame,data):
    '''Calls :func:`GSASIIpwd.CalcPDF` to compute the PDF and put into the data tree array.
    Called from OnComputePDF and OnComputeAllPDF and OnComputeAllPDF in
    GSASIIimgGUI.py
    '''

    xydata = {}
    problem = False
    for key in ['Sample','Sample Bkg.','Container','Container Bkg.']:
        name = data[key]['Name']
        if name.strip():
            pId = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,name)
            if not pId:
                print(key,'Entry',name,'Not found.')
                problem = True
                continue                
            xydata[key] = G2frame.GPXtree.GetItemPyData(pId)
    if problem:
        print('PDF computation aborted')
        return
    powId = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,data['Sample']['Name'])
    limits = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,powId,'Limits'))[1]
    inst = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,powId,'Instrument Parameters'))[0]
    auxPlot = G2pwd.CalcPDF(data,inst,limits,xydata)
    data['I(Q)'] = xydata['IofQ']
    data['S(Q)'] = xydata['SofQ']
    data['F(Q)'] = xydata['FofQ']
    data['G(R)'] = xydata['GofR']
    data['g(r)'] = xydata['gofr']
    return auxPlot

def OptimizePDF(G2frame,data,showFit=True,maxCycles=5):
    '''Optimize the PDF to minimize the difference between G(r) and the expected value for
    low r (-4 pi r #density). 
    '''
    xydata = {}
    for key in ['Sample','Sample Bkg.','Container','Container Bkg.']:
        name = data[key]['Name']
        if name:
            xydata[key] = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,G2frame.root,name))
    powName = data['Sample']['Name']
    powId = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,powName)
    limits = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,powId,'Limits'))[1]
    inst = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,powId,'Instrument Parameters'))[0]
    res = G2pwd.OptimizePDF(data,xydata,limits,inst,showFit,maxCycles)
    return res['success']
    
def UpdatePDFGrid(G2frame,data):
    '''respond to selection of PWDR PDF data tree item.
    '''    
    
    def PDFFileSizer():
        
        def FillFileSizer(fileSizer,key):
            #fileSizer is a FlexGridSizer(3,4)
            
            def OnSelectFile(event):
                Obj = event.GetEventObject()
                fileKey,itemKey,fmt = itemDict[Obj.GetId()]
                if itemKey == 'Name':
                    value = Obj.GetValue()
                Obj.SetValue(fmt%(value))
                data[fileKey][itemKey] = value
                data[fileKey]['Mult'] = GetExposure(value)
                mult.SetValue(data[fileKey]['Mult'])
                ResetFlatBkg()
                wx.CallAfter(OnComputePDF,None)
                
            def OnMoveMult(event):
                data[key]['Mult'] += multSpin.GetValue()*0.01
                mult.SetValue(data[key]['Mult'])
                multSpin.SetValue(0)
                wx.CallAfter(OnComputePDF,None)
                            
            def OnMult(invalid,value,tc):
                if invalid: return
                ResetFlatBkg()
                wx.CallAfter(OnComputePDF,None)
                
            def OnRefMult(event):
                item['Refine'] = refMult.GetValue()
                if item['Refine']:
                    G2frame.GetStatusBar().SetStatusText('Be sure Mult is close to anticipated value. '+   \
                        'Suggest setting Flat Bkg. to 0 before Optimize Mult',1)
            
            def GetExposure(backFile):
                dataId = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,'PWDR'+dataFile[4:])
                dataComments = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,dataId,'Comments'))
                if not backFile:
                    return -1.
                backId = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,backFile)
                backComments = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,backId,'Comments'))
                expTime = 1.
                sumExp = 1.
                for item in dataComments:
                    if 'exposureTime' in item:
                        expTime = float(item.split('=')[1])
                    if 'summedExposures' in item:
                        sumExp = float(item.split('=')[1])
                dataExp = expTime*sumExp
                expTime = 1.
                sumExp = 1.
                for item in backComments:
                    if 'exposureTime' in item:
                        expTime = float(item.split('=')[1])
                    if 'summedExposures' in item:
                        sumExp = float(item.split('=')[1])
                backExp = expTime*sumExp
                return -dataExp/backExp
            
            item = data[key]
            fileList = [''] + GetFileList(G2frame,'PWDR')
            fileSizer.Add(wx.StaticText(parent=G2frame.dataWindow,label=' '+key+' file:'),0,WACV)
            fileName = wx.ComboBox(G2frame.dataWindow,value=item['Name'],choices=fileList,
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
            itemDict[fileName.GetId()] = [key,'Name','%s']
            fileName.Bind(wx.EVT_COMBOBOX,OnSelectFile)        
            fileSizer.Add(fileName,0,)
            fileSizer.Add(wx.StaticText(parent=G2frame.dataWindow,label='Multiplier:'),0,WACV)
            mulBox = wx.BoxSizer(wx.HORIZONTAL)
            mult = G2G.ValidatedTxtCtrl(G2frame.dataWindow,item,'Mult',nDig=(10,3),
                typeHint=float,OnLeave=OnMult)
            mulBox.Add(mult,0,)
            multSpin = wx.SpinButton(G2frame.dataWindow,style=wx.SP_VERTICAL,size=wx.Size(20,25))
            multSpin.SetRange(-1,1)
            multSpin.SetValue(0)
            multSpin.Bind(wx.EVT_SPIN, OnMoveMult)
            mulBox.Add(multSpin,0,WACV)
            fileSizer.Add(mulBox,0,WACV)
            if 'Refine' in item and item['Name'] and 'Sample' in key:
                refMult = wx.CheckBox(parent=G2frame.dataWindow,label='Refine?')
                refMult.SetValue(item['Refine'])
                refMult.Bind(wx.EVT_CHECKBOX, OnRefMult)
                fileSizer.Add(refMult,0,WACV)
            else:
                fileSizer.Add((5,5),0)
                            
        def ResetFlatBkg():
            Smin = np.min(G2frame.GPXtree.GetItemPyData(
                G2gd.GetGPXtreeItemId(G2frame,G2frame.root,'PWDR'+dataFile[4:]))[1][1])
            Bmin = 0; Cmin = 0.; Cmul = 0.; CBmin = 0.
            if data['Sample Bkg.']['Name']:
                Bmin = np.min(G2frame.GPXtree.GetItemPyData(
                G2gd.GetGPXtreeItemId(G2frame,G2frame.root,data['Sample Bkg.']['Name']))[1][1])
                Smin += Bmin*data['Sample Bkg.']['Mult']
            if data['Container']['Name']:
                Cmin = np.min(G2frame.GPXtree.GetItemPyData(
                G2gd.GetGPXtreeItemId(G2frame,G2frame.root,data['Container']['Name']))[1][1])
                Cmul = data['Container']['Mult']
                if data['Container Bkg.']['Name']:
                    CBmin = np.min(G2frame.GPXtree.GetItemPyData(
                        G2gd.GetGPXtreeItemId(G2frame,G2frame.root,data['Container Bkg.']['Name']))[1][1])
                    Cmin += CBmin*data['Container Bkg.']['Mult']
                Smin += Cmul*Cmin
            data['Flat Bkg'] = max(0,Smin)
            G2frame.flatBkg.SetValue(data['Flat Bkg'])
                            
        PDFfileSizer = wx.BoxSizer(wx.VERTICAL)
        PDFfileSizer.Add(wx.StaticText(parent=G2frame.dataWindow,label=' PDF data files: '),0)
        PDFfileSizer.Add((5,5),0)    
        if 'C' in inst['Type'][0]:
            str = ' Sample file: PWDR%s   Wavelength, A: %.5f  Energy, keV: %.3f  Polariz.: %.2f '%(dataFile[4:],wave,keV,polariz)
            PDFfileSizer.Add(wx.StaticText(parent=G2frame.dataWindow,label=str),0)
        PDFfileSizer.Add((5,5),0)
        fileSizer = wx.FlexGridSizer(0,5,5,1)
        select = ['Sample Bkg.','Container']
        if data['Container']['Name']:
            select.append('Container Bkg.')
        for key in select:
            FillFileSizer(fileSizer,key)
        PDFfileSizer.Add(fileSizer,0)
        return PDFfileSizer
        
    def SampleSizer():
    
        def FillElemSizer(elemSizer,ElData):
            
            def AfterChange(invalid,value,tc):
                if invalid: return
                data['Form Vol'] = max(10.0,SumElementVolumes())
                wx.CallAfter(UpdatePDFGrid,G2frame,data)
                wx.CallAfter(OnComputePDF,tc.event)
                    
            elemSizer.Add(wx.StaticText(parent=G2frame.dataWindow,
                label=' Element: '+'%2s'%(ElData['Symbol'])+' * '),0,WACV)
            num = G2G.ValidatedTxtCtrl(G2frame.dataWindow,ElData,'FormulaNo',nDig=(10,3),xmin=0.0,
                typeHint=float,OnLeave=AfterChange)
            elemSizer.Add(num,0,WACV)
            elemSizer.Add(wx.StaticText(parent=G2frame.dataWindow,
                label="f': %.3f"%(ElData['fp'])+' f": %.3f'%(ElData['fpp'])+' mu: %.2f barns'%(ElData['mu']) ),
                0,WACV)
            
        def AfterChange(invalid,value,tc):
            if invalid: return
            wx.CallAfter(UpdatePDFGrid,G2frame,data)
            wx.CallAfter(OnComputePDF,tc.event)
        
        def OnGeometry(event):
            data['Geometry'] = geometry.GetValue()
            wx.CallAfter(UpdatePDFGrid,G2frame,data)
            #UpdatePDFGrid(G2frame,data)
            wx.CallAfter(OnComputePDF,event)
        
        sampleSizer = wx.BoxSizer(wx.VERTICAL)
        if not ElList:
            sampleSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Sample information: fill in this 1st'),0)
        else:
            sampleSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Sample information: '),0)
        sampleSizer.Add((5,5),0)    
        Abs = G2lat.CellAbsorption(ElList,data['Form Vol'])
        Trans = G2pwd.Transmission(data['Geometry'],Abs*data['Pack'],data['Diam'])
        elemSizer = wx.FlexGridSizer(0,3,5,1)
        for El in ElList:
            FillElemSizer(elemSizer,ElList[El])
        sampleSizer.Add(elemSizer,0)
        sampleSizer.Add((5,5),0)    
        midSizer = wx.BoxSizer(wx.HORIZONTAL)
        midSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Formula volume: '),0,WACV)
        formVol = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data,'Form Vol',nDig=(10,3),xmin=10.0,
            typeHint=float,OnLeave=AfterChange)
        midSizer.Add(formVol,0)
        midSizer.Add(wx.StaticText(G2frame.dataWindow,
            label=' Theoretical absorption: %.4f cm-1 Sample absorption: %.4f cm-1'%(Abs,Abs*data['Pack'])),
            0,WACV)
        sampleSizer.Add(midSizer,0)
        sampleSizer.Add((5,5),0)
        geoBox = wx.BoxSizer(wx.HORIZONTAL)
        geoBox.Add(wx.StaticText(G2frame.dataWindow,label=' Sample geometry: '),0,WACV)
        if 'C' in inst['Type'][0]:
            choice = ['Cylinder','Bragg-Brentano','Tilting flat plate in transmission','Fixed flat plate']
        else:
            choice = ['Cylinder',]
        geometry = wx.ComboBox(G2frame.dataWindow,value=data['Geometry'],choices=choice,
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
        geometry.Bind(wx.EVT_COMBOBOX, OnGeometry)
        geoBox.Add(geometry,0)
        geoBox.Add(wx.StaticText(G2frame.dataWindow,label=' Sample diameter/thickness, mm: '),0,WACV)
        diam = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data,'Diam',nDig=(10,3),xmin=0.01,
            typeHint=float,OnLeave=AfterChange)
        geoBox.Add(diam,0)
        sampleSizer.Add(geoBox,0)
        sampleSizer.Add((5,5),0)    
        geoBox = wx.BoxSizer(wx.HORIZONTAL)
        geoBox.Add(wx.StaticText(G2frame.dataWindow,label=' Packing: '),0,WACV)
        pack = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data,'Pack',nDig=(10,2),xmin=0.01,
            typeHint=float,OnLeave=AfterChange)
        geoBox.Add(pack,0)
        geoBox.Add(wx.StaticText(G2frame.dataWindow,label=' Sample transmission: %.3f %%'%(Trans)),0,WACV)    
        sampleSizer.Add(geoBox,0)
        return sampleSizer
        
    def SFGctrlSizer():
        
        def OnOptimizePDF(event):
            '''Optimize Flat Bkg, BackRatio & Ruland corrections to remove spurious
            "intensity" from portion of G(r) with r<Rmin.
            Invoked by Optimize PDF button and from menu command.
            '''
            if not data['ElList']:
                G2frame.ErrorDialog('PDF error','Chemical formula not defined')
                return
            G2frame.GetStatusBar().SetStatusText('',1)
            wx.BeginBusyCursor()
            try:
                OptimizePDF(G2frame,data)
            finally:
                wx.EndBusyCursor()
            OnComputePDF(event)
            wx.CallAfter(UpdatePDFGrid,G2frame,data)
                        
        def AfterChangeNoRefresh(invalid,value,tc):
            if invalid: return
            wx.CallAfter(OnComputePDF,None)
        
        def OnDetType(event):
            data['DetType'] = detType.GetValue()
            wx.CallAfter(UpdatePDFGrid,G2frame,data)
            wx.CallAfter(OnComputePDF,None)
        
        def OnFlatSpin(event):
            data['Flat Bkg'] += flatSpin.GetValue()*0.01*data['IofQmin']
            G2frame.flatBkg.SetValue(data['Flat Bkg'])
            flatSpin.SetValue(0)        
            wx.CallAfter(OnComputePDF,None)
                
        def OnBackSlider(event):
            value = int(backSldr.GetValue())/100.
            data['BackRatio'] = value
            backVal.SetValue(data['BackRatio'])
            wx.CallAfter(OnComputePDF,None)
        
        def OnRulSlider(event):
            value = int(rulandSldr.GetValue())/1000.
            data['Ruland'] = max(0.001,value)
            rulandWdt.SetValue(data['Ruland'])
            wx.CallAfter(OnComputePDF,None)
        
        def NewQmax(invalid,value,tc):
            if invalid: return
            data['QScaleLim'][0] = 0.9*value
            SQmin.SetValue(data['QScaleLim'][0])
            wx.CallAfter(OnComputePDF,None)
        
        def OnResetQ(event):
            data['QScaleLim'][1] = qLimits[1]
            SQmax.SetValue(data['QScaleLim'][1])
            data['QScaleLim'][0] = 0.9*qLimits[1]
            SQmin.SetValue(data['QScaleLim'][0])
            wx.CallAfter(OnComputePDF,None)
            
        def OnLorch(event):
            data['Lorch'] = lorch.GetValue()
            wx.CallAfter(OnComputePDF,None)
                            
        def OnNoRing(event):
            data['noRing'] = not data['noRing']
            wx.CallAfter(OnComputePDF,None)

        sfgSizer = wx.BoxSizer(wx.VERTICAL)         
        sqBox = wx.BoxSizer(wx.HORIZONTAL)
        sqBox.Add(wx.StaticText(G2frame.dataWindow,label=' S(Q)->F(Q)->G(r) controls: '),0,WACV)
        sqBox.Add((1,1),1,wx.EXPAND,1)
        optB = wx.Button(G2frame.dataWindow,label='Optimize PDF',style=wx.BU_EXACTFIT)
        optB.Bind(wx.EVT_BUTTON, OnOptimizePDF)
        sqBox.Add(optB,0,WACV|wx.ALIGN_RIGHT)
        sfgSizer.Add(sqBox,0,wx.EXPAND)
        
        sfgSizer.Add((5,5),0)
        sqBox = wx.BoxSizer(wx.HORIZONTAL)
        sqBox.Add(wx.StaticText(G2frame.dataWindow,label=' Detector type: '),0,WACV)
        choice = ['Area detector','Point detector']
        detType = wx.ComboBox(G2frame.dataWindow,value=data['DetType'],choices=choice,
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
        detType.Bind(wx.EVT_COMBOBOX, OnDetType)
        sqBox.Add(detType,0)
        if data['DetType'] == 'Area detector':
            sqBox.Add(wx.StaticText(G2frame.dataWindow,label=' IP transmission coeff.: '),0,WACV)
            obliqCoeff = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data,'ObliqCoeff',nDig=(10,3),xmin=0.0,xmax=1.0,
                typeHint=float,OnLeave=AfterChangeNoRefresh)
            sqBox.Add(obliqCoeff,0)
        sqBox.Add(wx.StaticText(G2frame.dataWindow,label=' Flat Bkg.: '),0,WACV)
        G2frame.flatBkg = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data,'Flat Bkg',nDig=(10,0),xmin=0,
                typeHint=float,OnLeave=AfterChangeNoRefresh)
        sqBox.Add(G2frame.flatBkg,0)
        flatSpin = wx.SpinButton(G2frame.dataWindow,style=wx.SP_VERTICAL,size=wx.Size(20,25))
        flatSpin.SetRange(-1,1)
        flatSpin.SetValue(0)
        flatSpin.Bind(wx.EVT_SPIN, OnFlatSpin)
        sqBox.Add(flatSpin,0,WACV)
        sqBox.Add((1,1),1,wx.EXPAND,1)
        sqBox.Add(wx.StaticText(G2frame.dataWindow,label='Rmin: '),0,WACV|wx.ALIGN_RIGHT)
        rmin = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data,'Rmin',nDig=(5,1),
                typeHint=float,size=wx.Size(50,20))
        sqBox.Add(rmin,0,WACV|wx.ALIGN_RIGHT)
        sfgSizer.Add(sqBox,0,wx.EXPAND)
            
        bkBox = wx.BoxSizer(wx.HORIZONTAL)
        bkBox.Add(wx.StaticText(G2frame.dataWindow,label=' Background ratio: '),0,WACV)    
        backSldr = wx.Slider(parent=G2frame.dataWindow,style=wx.SL_HORIZONTAL,
            value=int(100*data['BackRatio']))
        bkBox.Add(backSldr,1,wx.EXPAND)
        backSldr.Bind(wx.EVT_SLIDER, OnBackSlider)
        backVal = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data,'BackRatio',nDig=(10,3),xmin=0.0,xmax=1.0,
            typeHint=float,OnLeave=AfterChangeNoRefresh)
        bkBox.Add(backVal,0,WACV)    
        sfgSizer.Add(bkBox,0,wx.ALIGN_LEFT|wx.EXPAND)

        if 'XC' in inst['Type'][0]:
            sqBox = wx.BoxSizer(wx.HORIZONTAL)
            sqBox.Add(wx.StaticText(G2frame.dataWindow,label=' Ruland width: '),0,WACV)    
            rulandSldr = wx.Slider(parent=G2frame.dataWindow,style=wx.SL_HORIZONTAL,
                value=int(1000*data['Ruland']))
            sqBox.Add(rulandSldr,1,wx.EXPAND)
            rulandSldr.Bind(wx.EVT_SLIDER, OnRulSlider)
            rulandWdt = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data,'Ruland',nDig=(10,3),xmin=0.001,xmax=1.0,
                typeHint=float,OnLeave=AfterChangeNoRefresh)
            sqBox.Add(rulandWdt,0,WACV)    
            sfgSizer.Add(sqBox,0,wx.ALIGN_LEFT|wx.EXPAND)
        
        sqBox = wx.BoxSizer(wx.HORIZONTAL)
        sqBox.Add(wx.StaticText(G2frame.dataWindow,label=' Scaling Q-range: '),0,WACV)
        SQmin = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['QScaleLim'],0,nDig=(10,3),
            xmin=qLimits[0],xmax=.95*data['QScaleLim'][1],
            typeHint=float,OnLeave=AfterChangeNoRefresh)
        sqBox.Add(SQmin,0,WACV)
        sqBox.Add(wx.StaticText(G2frame.dataWindow,label=' to Qmax '),0,WACV)
        SQmax = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data['QScaleLim'],1,nDig=(10,3),
            xmin=qLimits[0],xmax=qLimits[1],typeHint=float,OnLeave=NewQmax)
        sqBox.Add(SQmax,0,WACV)
        resetQ = wx.Button(G2frame.dataWindow,label='Reset?',style=wx.BU_EXACTFIT)
        sqBox.Add(resetQ,0,WACV)
        resetQ.Bind(wx.EVT_BUTTON, OnResetQ)
        sqBox.Add(wx.StaticText(G2frame.dataWindow,label=' Plot Rmax: '),0,WACV)
        rmax = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data,'Rmax',nDig=(10,1),xmin=10.,xmax=200.,
            typeHint=float,OnLeave=AfterChangeNoRefresh,size=wx.Size(50,20))
        sqBox.Add(rmax,0,WACV)
        lorch = wx.CheckBox(parent=G2frame.dataWindow,label='Lorch damping?')
        lorch.SetValue(data['Lorch'])
        lorch.Bind(wx.EVT_CHECKBOX, OnLorch)
        sqBox.Add(lorch,0,WACV)
        noRing = wx.CheckBox(parent=G2frame.dataWindow,label='Suppress G(0) ringing?')
        noRing.SetValue(data['noRing'])
        noRing.Bind(wx.EVT_CHECKBOX, OnNoRing)
        sqBox.Add(noRing,0,WACV)
        sfgSizer.Add(sqBox,0)
        return sfgSizer
        
    def DiffSizer():
        
        def OnSelectGR(event):
            newName = grName.GetValue()
            if newName:
                data['delt-G(R)'] = copy.deepcopy(data['G(R)'])
                Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,newName)
                pId = G2gd.GetGPXtreeItemId(G2frame,Id,'PDF Controls')
                subData = G2frame.GPXtree.GetItemPyData(pId)['G(R)']
                if subData[1][0][-1] != data['G(R)'][1][0][-1]:
                    G2frame.ErrorDialog('delt-G(R) Error',' G(R) for '+newName+' not same R range')
                    grName.SetValue(data['diffGRname'])
                    return
                data['diffGRname'] = newName
                data['delt-G(R)'][1] = np.array([subData[1][0],data['G(R)'][1][1]-subData[1][1]])
                data['delt-G(R)'][2] += ('-\n'+subData[2])
                G2plt.PlotISFG(G2frame,data,newPlot=True,plotType='delt-G(R)')
                wx.CallAfter(UpdatePDFGrid,G2frame,data)
                
        def OnMult(invalid,value,tc):
            if invalid: return
            Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,data['diffGRname'])
            if Id == 0: return
            pId = G2gd.GetGPXtreeItemId(G2frame,Id,'PDF Controls')
            if pId == 0: return
            subData = G2frame.GPXtree.GetItemPyData(pId)['G(R)']
            data['delt-G(R)'][1] = np.array([subData[1][0],data['G(R)'][1][1]-data['diffMult']*subData[1][1]])
            G2plt.PlotISFG(G2frame,data,newPlot=True,plotType='delt-G(R)')
        
        diffSizer = wx.BoxSizer(wx.HORIZONTAL)
        fileList = [''] + GetFileList(G2frame,'PDF')
        diffSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Subtract G(R) for: '),0,WACV)
        grName = wx.ComboBox(G2frame.dataWindow,value=data['diffGRname'],choices=fileList,
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        grName.Bind(wx.EVT_COMBOBOX,OnSelectGR)        
        diffSizer.Add(grName,0,WACV)
        if data['diffGRname']:
            diffSizer.Add(wx.StaticText(G2frame.dataWindow,label=' Mult: '),0,WACV)
            mult = G2G.ValidatedTxtCtrl(G2frame.dataWindow,data,'diffMult',nDig=(10,3),
                    typeHint=float,OnLeave=OnMult)
            diffSizer.Add(mult,0,WACV)
            OnMult(False,None,None)
        return diffSizer
            
    def SumElementVolumes():
        sumVol = 0.
        ElList = data['ElList']
        for El in ElList:
            Avol = (4.*math.pi/3.)*ElList[El]['Drad']**3
            sumVol += Avol*ElList[El]['FormulaNo']
        return sumVol
        wx.CallAfter(OnComputePDF,None)
        
    def OnCopyPDFControls(event):
        import copy
        TextList = GetFileList(G2frame,'PDF')
        Source = G2frame.GPXtree.GetItemText(G2frame.PatternId)
        if len(TextList) == 1:
            G2frame.ErrorDialog('Nothing to copy controls to','There must be more than one "PDF" pattern')
            return
        od = {'label_1':'Only refine flag','value_1':False,'label_2':'Only Lorch flag','value_2':False}
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Copy PDF controls','Copy controls from '+Source+' to:',TextList,extraOpts=od)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                PDFlist = [TextList[i] for i in dlg.GetSelections()]
                for item in PDFlist:
                    Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,item)
                    olddata = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,Id, 'PDF Controls'))
                    if od['value_1']:
                        olddata['Sample Bkg.']['Refine'] = data['Sample Bkg.']['Refine']    #only one flag
                    elif od['value_2']:
                        olddata['Lorch'] = data['Lorch']    #only one flag                        
                    else:
                        sample = olddata['Sample']
                        olddata.update(copy.deepcopy(data))
                        olddata['Sample'] = sample
                    G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,Id, 'PDF Controls'),olddata)
                G2frame.GetStatusBar().SetStatusText('PDF controls copied',1)
        finally:
            dlg.Destroy()
                
    def OnSavePDFControls(event):
        pth = G2G.GetExportPath(G2frame)
        dlg = wx.FileDialog(G2frame, 'Choose GSAS-II PDF controls file', pth, '', 
            'PDF controls files (*.pdfprm)|*.pdfprm',wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                # make sure extension is .pdfprm
                filename = os.path.splitext(filename)[0]+'.pdfprm'
                File = open(filename,'w')
                File.write("#GSAS-II PDF controls file; do not add/delete items!\n")
                for item in data:
                    if item[:] not in ['Sample','I(Q)','S(Q)','F(Q)','G(R)']:
                        File.write(item+':'+data[item]+'\n')
                File.close()
                print ('PDF controls saved to: '+filename)
        finally:
            dlg.Destroy()
                
    def OnLoadPDFControls(event):
        pth = G2G.GetExportPath(G2frame)
        dlg = wx.FileDialog(G2frame, 'Choose GSAS-II PDF controls file', pth, '', 
            'PDF controls files (*.pdfprm)|*.pdfprm',wx.FD_OPEN)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                File = open(filename,'r')
                newdata = {}
                S = File.readline()
                while S:
                    if '#' in S:
                        S = File.readline()
                        continue
                    key,val = S.split(':',1)
                    try:
                        newdata[key] = eval(val)
                    #except SyntaxError:
                    except:
                        newdata[key] = val.strip()
                    S = File.readline()
                File.close()
                data.update(newdata)
        finally:
            dlg.Destroy()
        OnComputePDF(event)                
        wx.CallAfter(UpdatePDFGrid,G2frame,data)
        
    def OnAddElement(event):
        ElList = data['ElList']
        choice = list(ElList.keys())
        PE = G2elemGUI.PickElements(G2frame,choice)
        if PE.ShowModal() == wx.ID_OK:
            for El in PE.Elem:
                if El not in ElList:
                    try:
                        data['ElList'][El] = G2elem.GetElInfo(El,inst)
                        data['ElList'][El]['FormulaNo'] = 1.0
                    except IndexError: # happens with element Q
                        pass
            data['Form Vol'] = max(10.0,SumElementVolumes())
        PE.Destroy()
        wx.CallAfter(UpdatePDFGrid,G2frame,data)
        
    def OnDeleteElement(event):
        ElList = data['ElList']
        choice = list(ElList.keys())
        dlg = G2elemGUI.DeleteElement(G2frame,choice=choice)
        if dlg.ShowModal() == wx.ID_OK:
            del ElList[dlg.GetDeleteElement()]
        dlg.Destroy()
        wx.CallAfter(UpdatePDFGrid,G2frame,data)

    def OnComputePDF(event):
        '''Compute and plot PDF, in response to a menu command or a change to a
        computation parameter.
        '''
        if not data['ElList']:
            G2frame.ErrorDialog('PDF error','Chemical formula not defined')
            OnAddElement(event)
        auxPlot = computePDF(G2frame,data)
        if auxPlot is None: return
        G2frame.GetStatusBar().SetStatusText('PDF computed',1)
        for plot in auxPlot:
            XY = np.array(plot[:2])
            G2plt.PlotXY(G2frame,[XY,],Title=plot[2])
        if event is not None:
            G2plt.PlotISFG(G2frame,data,newPlot=True,plotType='I(Q)')
            G2plt.PlotISFG(G2frame,data,newPlot=True,plotType='S(Q)')
            G2plt.PlotISFG(G2frame,data,newPlot=True,plotType='F(Q)')
            G2plt.PlotISFG(G2frame,data,newPlot=True,plotType='G(R)')
            G2plt.PlotISFG(G2frame,data,newPlot=True,plotType='g(r)')
        else:
            G2plt.PlotISFG(G2frame,data,newPlot=False)
        
    def OnComputeAllPDF(event):
        print('Calculating PDFs...')
        choices = []
        if G2frame.GPXtree.GetCount():
            Id, cookie = G2frame.GPXtree.GetFirstChild(G2frame.root)
            while Id:
                Name = G2frame.GPXtree.GetItemText(Id)
                if Name.startswith('PDF '):
                    Data = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,Id,'PDF Controls'))
                    if not Data['ElList']:
                        print('  No chemical formula for {}'.format(Name))
                    else:
                        choices.append(Name)
                Id, cookie = G2frame.GPXtree.GetNextChild(G2frame.root, cookie)
        if not choices:
            print('  No PDFs to compute\n')
            return
        od = {'label_1':'Optimize PDFs','value_1':True}
        dlg = G2G.G2MultiChoiceDialog(G2frame, 'Select PDFs to compute','Select PDFs',
            choices,extraOpts=od)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                results = dlg.GetSelections()
            else:
                return
        finally:
            dlg.Destroy()
        if not results:
            print('  No PDFs to compute\n')
            return
        Names = [choices[i] for i in results]
        pgbar = wx.ProgressDialog('Compute PDF','PDFs done: 0',len(Names)+1, 
            style = wx.PD_ELAPSED_TIME|wx.PD_AUTO_HIDE|wx.PD_CAN_ABORT)
        notConverged = 0
        Id, cookie = G2frame.GPXtree.GetFirstChild(G2frame.root)
        N = 0
        try:
            while Id:
                Name = G2frame.GPXtree.GetItemText(Id)
                if Name in Names:
                    N += 1
                    msg = 'PDFs done: {} of {}'.format(N-1,len(Names))
                    if not pgbar.Update(N,msg)[0]:
                        pgbar.Destroy()
                        break
                    pId = G2gd.GetGPXtreeItemId(G2frame,Id,'PDF Controls')
                    Data = G2frame.GPXtree.GetItemPyData(pId)
                    print('  Computing {}'.format(Name))
                    computePDF(G2frame,Data)
                    if od['value_1']:
                        notConverged += not OptimizePDF(G2frame,Data,maxCycles=10)
                    computePDF(G2frame,Data)
                    G2frame.GPXtree.SetItemPyData(pId,Data)
                Id, cookie = G2frame.GPXtree.GetNextChild(G2frame.root, cookie)
        finally:
            pgbar.Destroy()
        if od['value_1']:
            msg = '{}/{} PDFs computed; {} unconverged'.format(N,len(Names),notConverged)
        else:
            msg = '{}/{} PDFs computed'.format(N,len(Names))
        G2frame.GetStatusBar().SetStatusText(msg,1)
        print(msg)
        # what item is being plotted? -- might be better to select from tree
        G2plt.PlotISFG(G2frame,data,newPlot=True,plotType='I(Q)')
        G2plt.PlotISFG(G2frame,data,newPlot=True,plotType='S(Q)')
        G2plt.PlotISFG(G2frame,data,newPlot=True,plotType='F(Q)')
        G2plt.PlotISFG(G2frame,data,newPlot=True,plotType='G(R)')
        G2plt.PlotISFG(G2frame,data,newPlot=True,plotType='g(r)')

    # Routine UpdatePDFGrid starts here
    global inst
    tth2q = lambda t,w:4.0*math.pi*sind(t/2.0)/w
    tof2q = lambda t,C:2.0*math.pi*C/t
    dataFile = G2frame.GPXtree.GetItemText(G2frame.PatternId)
    powName = 'PWDR'+dataFile[4:]
    powId = G2gd.GetGPXtreeItemId(G2frame,G2frame.root, powName)
    if powId: # skip if no matching PWDR entry
        fullLimits,limits = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,powId, 'Limits'))[:2]
        inst = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,powId, 'Instrument Parameters'))[0]
        if 'C' in inst['Type'][0]:
            wave = G2mth.getWave(inst)
            keV = 12.397639/wave
            qLimits = [tth2q(fullLimits[0],wave),tth2q(fullLimits[1],wave)]
            polariz = inst['Polariz.'][1]
        else:   #'T'of
            qLimits = [tof2q(fullLimits[1],inst['difC'][1]),tof2q(fullLimits[0],inst['difC'][1])]
            polariz = 1.0
        data['QScaleLim'][1] = min(qLimits[1],data['QScaleLim'][1])
        if data['QScaleLim'][0]:
            data['QScaleLim'][0] = max(qLimits[0],data['QScaleLim'][0])
        else:                                #initial setting at 90% of max Q
            data['QScaleLim'][0] = 0.90*data['QScaleLim'][1]
        itemDict = {}
        #patch
        if 'BackRatio' not in data:
            data['BackRatio'] = 0.
        if 'noRing' not in data:
            data['noRing'] = False
        if 'Rmax' not in data:
            data['Rmax'] = 100.
        if 'Flat Bkg' not in data:
            data['Flat Bkg'] = 0.
        if 'IofQmin' not in data:
            data['IofQmin'] = 1.0        
        if 'Rmin' not in data:
            data['Rmin'] = 1.5
        if data['DetType'] == 'Image plate':
            data['DetType'] = 'Area detector'
        if 'Refine' not in data['Sample Bkg.']:
            data['Sample Bkg.']['Refine'] = False
        if 'diffGRname' not in data:
            data['diffGRname'] = ''
        if 'diffMult' not in data:
            data['diffMult'] = 1.0
    G2gd.SetDataMenuBar(G2frame,G2frame.dataWindow.PDFMenu)
    if powId:
        G2frame.dataWindow.PDFMenu.EnableTop(0,enable=True)
    else:
        G2frame.dataWindow.PDFMenu.EnableTop(0,enable=False)
    G2frame.Bind(wx.EVT_MENU, OnCopyPDFControls, id=G2G.wxID_PDFCOPYCONTROLS)
    G2frame.Bind(wx.EVT_MENU, OnSavePDFControls, id=G2G.wxID_PDFSAVECONTROLS)
    G2frame.Bind(wx.EVT_MENU, OnLoadPDFControls, id=G2G.wxID_PDFLOADCONTROLS)
    G2frame.Bind(wx.EVT_MENU, OnAddElement, id=G2G.wxID_PDFADDELEMENT)
    G2frame.Bind(wx.EVT_MENU, OnDeleteElement, id=G2G.wxID_PDFDELELEMENT)
    G2frame.Bind(wx.EVT_MENU, OnComputePDF, id=G2G.wxID_PDFCOMPUTE)
    G2frame.Bind(wx.EVT_MENU, OnComputeAllPDF, id=G2G.wxID_PDFCOMPUTEALL)

    G2frame.dataWindow.ClearData()
    mainSizer = G2frame.dataWindow.GetSizer()
    if powId:
        ElList = data['ElList']
        mainSizer.Add(PDFFileSizer(),0,WACV)
        G2G.HorizontalLine(mainSizer,G2frame.dataWindow)
        mainSizer.Add(SampleSizer(),0,WACV)
        G2G.HorizontalLine(mainSizer,G2frame.dataWindow)
        mainSizer.Add(SFGctrlSizer(),0,WACV)
        G2G.HorizontalLine(mainSizer,G2frame.dataWindow)
        mainSizer.Add(DiffSizer(),0,WACV)
    else:
        mainSizer.Add(wx.StaticText(G2frame.dataWindow,wx.ID_ANY,
                                     powName+' not in Tree'))
    G2frame.dataWindow.SetDataSize()

###############################################################################################################
#UpdatePDFPeaks: peaks in G(r)
###############################################################################################################
def UpdatePDFPeaks(G2frame,peaks,data):
    
    def limitSizer():
        
        def NewLim(invalid,value,tc):
            if invalid:
                return
            G2plt.PlotISFG(G2frame,data,newPlot=False,plotType='G(R)',peaks=peaks)
                        
        limitBox = wx.BoxSizer(wx.HORIZONTAL)
        limitBox.Add(wx.StaticText(G2frame.dataWindow,label=' PDF Limits: '),0,WACV)
        lowLim = G2G.ValidatedTxtCtrl(G2frame.dataWindow,peaks['Limits'],0,nDig=(10,3),
            xmin=0.,xmax=10.,typeHint=float,OnLeave=NewLim)
        limitBox.Add(lowLim,0,WACV)
        highLim = G2G.ValidatedTxtCtrl(G2frame.dataWindow,peaks['Limits'],1,nDig=(10,3),
            xmin=peaks['Limits'][0],xmax=10.,typeHint=float,OnLeave=NewLim)
        limitBox.Add(highLim,0,WACV)
        return limitBox
        
    def backSizer():
        
        def NewBack(invalid,value,tc):
            if invalid:
                return
            G2plt.PlotISFG(G2frame,data,newPlot=False,plotType='G(R)',peaks=peaks)
            
        def OnRefBack(event):
            peaks['Background'][2] = refbk.GetValue()
        
        backBox = wx.BoxSizer(wx.HORIZONTAL)
        backBox.Add(wx.StaticText(G2frame.dataWindow,label=' Background slope: '),0,WACV)
        slope = G2G.ValidatedTxtCtrl(G2frame.dataWindow,peaks['Background'][1],1,nDig=(10,3),
            xmin=-4.*np.pi,xmax=0.,typeHint=float,OnLeave=NewBack)
        backBox.Add(slope,0,WACV)
        refbk = wx.CheckBox(parent=G2frame.dataWindow,label=' Refine?')
        refbk.SetValue(peaks['Background'][2])
        refbk.Bind(wx.EVT_CHECKBOX, OnRefBack)
        backBox.Add(refbk,0,WACV)
        return backBox
        
    def peakSizer():
        
        def PeaksRefine(event):
            c =  event.GetCol()
            if PDFPeaks.GetColLabelValue(c) == 'refine':
                choice = ['P - position','M - magnitude','S - standrd deviation']
                dlg = wx.MultiChoiceDialog(G2frame,'Select','Refinement controls',choice)
                if dlg.ShowModal() == wx.ID_OK:
                    sel = dlg.GetSelections()
                    parms = ''
                    for x in sel:
                        parms += choice[x][0]
                    for peak in peaks['Peaks']:
                        peak[3] = parms
                dlg.Destroy()
                wx.CallAfter(UpdatePDFPeaks,G2frame,peaks,data)
                
        def ElTypeSelect(event):
            r,c =  event.GetRow(),event.GetCol()
            if 'Atom' in PDFPeaks.GetColLabelValue(c):
                PE = G2elemGUI.PickElement(G2frame)
                if PE.ShowModal() == wx.ID_OK:
                    el = PE.Elem.strip()
                    peaks['Peaks'][r][c] = el
                    PDFPeaks.SetCellValue(r,c,el)
                PE.Destroy()                
        
        colLabels = ['position','magnitude','sig','refine','Atom A','Atom B','Bond No.']
        Types = 3*[wg.GRID_VALUE_FLOAT+':10,3',]+[wg.GRID_VALUE_CHOICE+': ,P,M,S,PM,PS,MS,PMS',]+     \
            2*[wg.GRID_VALUE_STRING,]+[wg.GRID_VALUE_FLOAT+':10,3',]
        rowLabels = [str(i) for i in range(len(peaks['Peaks']))]
        peakTable = G2G.Table(peaks['Peaks'],rowLabels=rowLabels,colLabels=colLabels,types=Types)
        PDFPeaks = G2G.GSGrid(G2frame.dataWindow)
        PDFPeaks.SetTable(peakTable,True)
        PDFPeaks.AutoSizeColumns(False)
        PDFPeaks.Bind(wg.EVT_GRID_LABEL_LEFT_DCLICK, PeaksRefine)
        PDFPeaks.Bind(wg.EVT_GRID_CELL_LEFT_DCLICK, ElTypeSelect)

        peakBox = wx.BoxSizer(wx.VERTICAL)
        peakBox.Add(wx.StaticText(G2frame.dataWindow,label=' PDF Peaks:'),0)
        peakBox.Add(PDFPeaks,0)
        
        return peakBox
        
    def OnCopyPDFPeaks(event):
        import copy
        TextList = GetFileList(G2frame,'PDF')
        Source = G2frame.GPXtree.GetItemText(G2frame.PatternId)
        if len(TextList) == 1:
            G2frame.ErrorDialog('Nothing to copy PDF peaks to','There must be more than one "PDF" pattern')
            return
        od = {'label_1':'Only refine flags','value_1':False}
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Copy PDF peaks','Copy peaks from '+Source+' to:',TextList,extraOpts=od)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                PDFlist = [TextList[i] for i in dlg.GetSelections()]
                for item in PDFlist:
                    Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,item)
                    olddata = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,Id, 'PDF Peaks'))
                    if od['value_1']:
                        olddata['Background'][2] = peaks['Background'][2]
                        for ip,peak in enumerate(olddata['Peaks']):
                            peak[3] = peaks['Peaks'][ip][3]
                    else:
                        olddata.update(copy.deepcopy(peaks))
                    G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,Id, 'PDF Peaks'),olddata)
                G2frame.GetStatusBar().SetStatusText('PDF peaks copied',1)
        finally:
            dlg.Destroy()
        
    def OnFitPDFpeaks(event):
        PatternId = G2frame.PatternId
        data = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'PDF Controls'))
        peaks = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'PDF Peaks'))
        if not peaks:
            G2frame.ErrorDialog('No peaks!','Nothing to fit!')
            return
        newpeaks = G2pwd.PDFPeakFit(peaks,data['G(R)'])[0]
        print ('PDF peak fit finished')
        G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,PatternId, 'PDF Peaks'),newpeaks)
        G2plt.PlotISFG(G2frame,data,peaks=newpeaks,newPlot=False)
        wx.CallAfter(UpdatePDFPeaks,G2frame,newpeaks,data)
        
    def OnFitAllPDFpeaks(event):
        Names = G2gd.GetGPXtreeDataNames(G2frame,['PDF ',])
        od = {'label_1':'Copy to next','value_1':False,'label_2':'Reverse order','value_2':False}
        dlg = G2G.G2MultiChoiceDialog(G2frame,'PDF peak fitting','Select PDFs to fit:',Names,extraOpts=od)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                Id =  G2gd.GetGPXtreeItemId(G2frame,G2frame.root,'Sequential PDF peak fit results')
                if Id:
                    SeqResult = G2frame.GPXtree.GetItemPyData(Id)
                else:
                    SeqResult = {}
                    Id = G2frame.GPXtree.AppendItem(parent=G2frame.root,text='Sequential PDF peak fit results')
                SeqResult = {'SeqPseudoVars':{},'SeqParFitEqList':[]}
                items = dlg.GetSelections()
                if od['value_2']:
                    items.reverse()
                newpeaks = None
                G2frame.EnablePlot = False
                for item in items:
                    name = Names[item]
                    pId = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,name)
                    data = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,pId, 'PDF Controls'))
                    if od['value_1'] and newpeaks is not None:
                        peaks = copy.deepcopy(newpeaks)
                    else:
                        peaks = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,pId,'PDF Peaks'))
                    newpeaks,vals,varyList,sigList,parmDict,Rvals = G2pwd.PDFPeakFit(peaks,data['G(R)'])
                    if vals is None:
                        print ('Nothing varied!')
                        dlg.Destroy()
                        return
                    SeqResult[name] = {'variables':vals,'varyList':varyList,'sig':sigList,'Rvals':Rvals,
                        'covMatrix':np.eye(len(varyList)),'title':name,'parmDict':parmDict}
                    G2frame.GPXtree.SetItemPyData(G2gd.GetGPXtreeItemId(G2frame,pId, 'PDF Peaks'),newpeaks)
                SeqResult['histNames'] = Names
                G2frame.G2plotNB.Delete('Sequential refinement')    #clear away probably invalid plot
                G2plt.PlotISFG(G2frame,data,peaks=newpeaks,newPlot=False)
                G2frame.GPXtree.SetItemPyData(Id,SeqResult)
                G2frame.GPXtree.SelectItem(Id)
                print ('All PDFs peak fitted - results in Sequential PDF peak fit results')
            else:
                print ('Sequential fit cancelled')
        finally:
            dlg.Destroy()
        
    def OnClearPDFpeaks(event):
        peaks['Peaks'] = []
        G2plt.PlotISFG(G2frame,data,peaks=peaks,newPlot=False)
        wx.CallAfter(UpdatePDFPeaks,G2frame,peaks,data)

    G2gd.SetDataMenuBar(G2frame,G2frame.dataWindow.PDFPksMenu)
    G2frame.Bind(wx.EVT_MENU, OnCopyPDFPeaks, id=G2G.wxID_PDFCOPYPEAKS)
    G2frame.Bind(wx.EVT_MENU, OnFitPDFpeaks, id=G2G.wxID_PDFPKSFIT)
    G2frame.Bind(wx.EVT_MENU, OnFitAllPDFpeaks, id=G2G.wxID_PDFPKSFITALL)
    G2frame.Bind(wx.EVT_MENU, OnClearPDFpeaks, id=G2G.wxID_CLEARPDFPEAKS)
    G2frame.dataWindow.ClearData()
    mainSizer = G2frame.dataWindow.GetSizer()
    mainSizer.Add((5,5),0) 
    mainSizer.Add(wx.StaticText(G2frame.dataWindow,label=' PDF peak fit controls:'),0,WACV)
    mainSizer.Add((5,5),0) 
    mainSizer.Add(limitSizer(),0,WACV) 
    mainSizer.Add((5,5),0) 
    mainSizer.Add(backSizer())
    if len(peaks['Peaks']):
        mainSizer.Add((5,5),0)
        mainSizer.Add(peakSizer())
    G2frame.dataWindow.SetDataSize()
    
