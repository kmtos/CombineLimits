import os
import sys
import logging
import itertools
import numpy as np
import argparse
import math
import errno
from array import array

import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch()
ROOT.gROOT.ProcessLine(".L ../../Limits/macros/DoubleCrystalBall.cpp")

import CombineLimits.Limits.Models as Models
from CombineLimits.Limits.Limits import Limits
from CombineLimits.HaaLimits.HaaLimits import HaaLimits
from CombineLimits.Limits.utilities import *

class HaaLimits2D(HaaLimits):
    '''
    Create the Haa Limits workspace
    '''

    YRANGE = [50,1000]
    YLABEL = 'm_{#mu#mu#tau_{#mu}#tau_{h}}'

    def __init__(self,histMap,tag=''):
        '''
        Required arguments:
            histMap = histogram map. the structure should be:
                histMap[region][shift][process] = ROOT.TH1()
                where:
                    region  : 'PP' or 'FP' for regions A and B, respectively
                    shift   : '', 'shiftName', 'shiftNameUp', or 'shiftNameDown'
                        ''                   : central value
                        'shiftName'          : a symmetric shift (ie, jet resolution)
                        'shiftName[Up,Down]' : an asymmetric shift (ie, fake rate, lepton efficiencies, etc)
                        shiftName            : the name the uncertainty will be given in the datacard
                    process : the name of the process
                        signal must be of the form 'HToAAH{h}A{a}'
                        data = 'data'
                        background = 'datadriven'
        '''
        super(HaaLimits2D,self).__init__(histMap,tag=tag)

        self.plotDir = 'figures/HaaLimits2D{}'.format('_'+tag if tag else '')
        python_mkdir(self.plotDir)


    ###########################
    ### Workspace utilities ###
    ###########################
    def initializeWorkspace(self):
        self.addX(*self.XRANGE,unit='GeV',label=self.XLABEL)
        self.addY(*self.YRANGE,unit='GeV',label=self.YLABEL)
        self.addMH(*self.SPLINERANGE,unit='GeV',label=self.SPLINELABEL)

    def _buildYModel(self,region='PP',**kwargs):
        tag = kwargs.pop('tag',region)

        cont1 = Models.Exponential('cont1',
            x = 'y',
            #lamb = [-0.20,-1,0], # kinfit
            lamb = [-0.1,-0.5,0], # visible
        )
        nameC1 = 'cont1{}'.format('_'+tag if tag else '')
        cont1.build(self.workspace,nameC1)

        # higgs fit (mmtt)
        if self.YRANGE[1]>100:
            erf1 = Models.Erf('erf1',
                x = 'y',
                erfScale = [0.01,0,1],
                erfShift = [100,0,1000],
            )
            nameE1 = 'erf1{}'.format('_'+tag if tag else '')
            erf1.build(self.workspace,nameE1)

            bg = Models.Prod('bg',
                nameE1,
                nameC1,
            )
        # pseudo fit (tt)
        else:
            erf1 = Models.Erf('erf1',
                x = 'y',
                erfScale = [0.01,0,1],
                erfShift = [1,0,20],
            )
            nameE1 = 'erf1{}'.format('_'+tag if tag else '')
            erf1.build(self.workspace,nameE1)

            erfc1 = Models.Prod('erfc1',
                nameE1,
                nameC1,
            )
            nameEC1 = 'erfc1{}'.format('_'+tag if tag else '')
            erfc1.build(self.workspace,nameEC1)

            # add a guassian summed for tt ?
            gaus1 = Models.Gaussian('gaus1',
                x = 'y',
                mean = [2,0,20],
                sigma = [0.1,0,2],
            )
            nameG1 = 'gaus1{}'.format('_'+tag if tag else '')
            gaus1.build(self.workspace,nameG1)

            bg = Models.Sum('bg',
                **{ 
                    nameEC1    : [0.5,0,1],
                    nameG1     : [0.5,0,1],
                    'recursive': True,
                }
            )

        name = 'bg_{}'.format(region)
        bg.build(self.workspace,name)

    def _buildXModel(self,region='PP',**kwargs):
        super(HaaLimits2D,self).buildModel(region,**kwargs)

    def buildModel(self,region='PP',**kwargs):
        tag = kwargs.pop('tag',region)

        # build the x variable
        self._buildXModel(region+'_x',**kwargs)

        # build the y variable
        self._buildYModel(region+'_y',**kwargs)

        # the 2D model
        bg = Models.Prod('bg',
            'bg_{}_x'.format(region),
            'bg_{}_y'.format(region),
        )

        name = 'bg_{}'.format(region)
        bg.build(self.workspace,name)


    def buildSpline(self,h,region='PP',shift='',yFitFunc="G", **kwargs):
        '''
        Get the signal spline for a given Higgs mass.
        Required arguments:
            h = higgs mass
        '''
        ygausOnly = kwargs.get('ygausOnly',False)
        fit = kwargs.get('fit',False)
        dobgsig = kwargs.get('doBackgroundSignal',False)
        amasses = self.AMASSES
        if h>125: amasses = [a for a in amasses if a not in ['3p6',4,6]]
        avals = [float(str(x).replace('p','.')) for x in amasses]
        histMap = self.histMap[region][shift]
        tag= '{}{}'.format(region,'_'+shift if shift else '')
        # initial fit
        results = {}
        errors = {}
        results[h] = {}
        errors[h] = {}
        for a in amasses:
            aval = float(str(a).replace('p','.'))
            ws = ROOT.RooWorkspace('sig')
            ws.factory('x[{0}, {1}]'.format(*self.XRANGE))
            ws.var('x').setUnit('GeV')
            ws.var('x').setPlotLabel(self.XLABEL)
            ws.var('x').SetTitle(self.XLABEL)
            ws.factory('y[{0}, {1}]'.format(*self.YRANGE))
            ws.var('y').setUnit('GeV')
            ws.var('y').setPlotLabel(self.YLABEL)
            ws.var('y').SetTitle(self.YLABEL)
            modelx = Models.Voigtian('sigx',
                mean  = [aval,0,30],
                width = [0.01*aval,0.001,5],
                sigma = [0.01*aval,0.001,5],
            )
            modelx.build(ws, 'sigx')
            if self.YRANGE[1]>100: # y variable is h mass
                if yFitFunc == "G": 
                    modely = Models.Gaussian('sigy',
                        x = 'y',
                        mean  = [h,0,1.25*h],
                        sigma = [0.1*h,0.01,0.5*h],
                    )
                elif yFitFunc == "V":
                    modely = Models.Voigtian('sigy',
                        x = 'y',
                        mean  = [h,0.1,1000],
                        width = [0.1*h,0.01,0.5*h],
                        sigma = [0.1*h,0.01,0.5*h],
                    )
                elif yFitFunc == "CB":
                    modely = Models.CrystalBall('sigy',
                        x = 'y',
                        mean  = [h,0.1,1000],
                        sigma = [0.1*h,0.01,0.5*h],
                        a = [1.0,.5,5],
                        n = [0.5,.1,1.5],
                    )
                elif yFitFunc == "DCB":
                    modely = Models.DoubleCrystalBall('sigy',
                        x = 'y',
                        mean  = [h,0.1,1000],
                        sigma = [0.1*h,0.01,0.5*h],
                        a1 = [1.0,0.1,6],
                        n1 = [0.9,0.1,6],
                        a2 = [2.0,0.1,10],
                        n2 = [1.5,0.1,10],
                    )
                elif yFitFunc == "DG":
                    modely = Models.DoubleSidedGaussian('sigy',
                        x = 'y',
                        mean  = [h,0.1,1000],
                        sigma1 = [0.03*h,0.01,0.5*h],
                        sigma2 = [0.06*h,0.01,0.5*h],
                    )
                elif yFitFunc == "DV":
                    modely = Models.DoubleSidedVoigtian('sigy',
                        x = 'y',
                        mean  = [h,0.01,1000],
                        sigma1 = [0.03*h,0.01,0.5*h],
                        sigma2 = [0.06*h,0.01,0.5*h],
                        width1 = [0.03*h,0.01,0.5*h],
                        width2 = [0.06*h,0.01,0.5*h],
                    )
                modely.build(ws, 'sigy')
                model = Models.Prod('sig',
                    'sigx',
                    'sigy',
                )
            else: # y variable is tt
                # simple voitian
                if yFitFunc == "G":
                    modely_sig = Models.Gaussian('sigy',
                        x = 'y',
                        mean  = [aval,0,1.25*aval],
                        sigma = [0.1*aval,0.01,0.5*aval],
                    )
                elif yFitFunc == "V":
                    modely_sig = Models.Voigtian('sigy',
                        x = 'y',
                        mean  = [aval,0,30],
                        width = [0.1*aval,0.01,5],
                        sigma = [0.1*aval,0.01,5],
                    )
                elif yFitFunc == "CB":
                    modely_sig = Models.CrystalBall('sigy',
                        x = 'y',
                        mean  = [aval,0,30],
                        sigma = [0.1*aval,0,5],
                        a = [1.0,0.5,5],
                        n = [0.5,0.1,1.5],
                    )
                elif yFitFunc == "DCB":
                    modely_sig = Models.DoubleCrystalBall('sigy',
                        x = 'y',
                        mean  = [aval,0,30],
                        sigma = [0.1*aval,0,5],
                        a1 = [1.0,0.1,6],
                        n1 = [0.9,0.1,6],
                        a2 = [2.0,0.1,10],
                        n2 = [1.5,0.1,10],
                    )
                elif yFitFunc == "DG":
                    modely_sig = Models.DoubleSidedGaussian('sigy',
                        x = 'y',
                        mean  = [aval,0,30],
                        sigma1 = [0.1*aval,0.5,0.4*aval],
                        sigma2 = [0.3*aval,0.5,0.4*aval],
                    )
                elif yFitFunc == "DV":
                    modely_sig = Models.DoubleSidedVoigtian('sigy',
                        x = 'y',
                        mean  = [aval,0,30],
                        sigma1 = [0.1*aval,0.01,5],
                        sigma2 = [0.3*aval,0.01,5],
                        width1 = [0.1*aval,0.01,5],
                        width2 = [0.3*aval,0.01,5],
                    )

                modely_sig.build(ws, 'sigy')

                if region=='PP' or not dobgsig:
                    model = Models.Prod('sig',
                        'sigx',
                        'sigy',
                    )
                else:
                    conty = Models.Exponential('conty',
                        x = 'y',
                        lamb = [-0.25,-1,-0.001], # visible
                    )
                    conty.build(ws,'conty')

                    erfy = Models.Erf('erfy',
                        x = 'y',
                        erfScale = [0.1,0.01,10],
                        erfShift = [2,0,10],
                    )
                    erfy.build(ws,'erfy')

                    erfc = Models.Prod('erfcy',
                        'erfy',
                        'conty',
                    )
                    erfc.build(ws,'erfcy')

                    modely = Models.Sum('bgsigy',
                        **{ 
                            'erfcy'    : [0.5,0,1],
                            'sigy'     : [0.5,0,1],
                            'recursive': True,
                        }
                    )
                    modely.build(ws,'bgsigy')

                    model = Models.Prod('sig',
                        'sigx',
                        'bgsigy',
                    )

            ws.Print("v")
            model.build(ws, 'sig')
            hist = histMap[self.SIGNAME.format(h=h,a=a)]
            saveDir = '{}/{}'.format(self.plotDir,shift if shift else 'central')
            results[h][a], errors[h][a] = model.fit2D(ws, hist, 'h{}_a{}_{}'.format(h,a,tag), saveDir=saveDir, save=True, doErrors=True)
            print h, a, results[h][a], errors[h][a]
    

        # Fit using ROOT rather than RooFit for the splines
        if yFitFunc == "V":
            fitFuncs = {
              'xmean' : 'pol1',  
              'xwidth': 'pol2',
              'xsigma': 'pol2',
              'ymean' : 'pol1',
              'ywidth': 'pol2',
              'ysigma': 'pol2',
          }
        elif yFitFunc == "G":
            fitFuncs = {
              'xmean' : 'pol1',  
              'xwidth': 'pol2',
              'xsigma': 'pol2',
              'ymean' : 'pol1',
              'ysigma': 'pol2',
          }
        elif yFitFunc == "CB":
            fitFuncs = {
              'xmean' : 'pol1',  
              'xwidth': 'pol2',
              'xsigma': 'pol2',
              'ymean' : 'pol1',
              'ysigma': 'pol2',
              'ya': 'pol2',
              'yn': 'pol2',
          }
        elif yFitFunc == "DCB":
            fitFuncs = {
              'xmean' : 'pol1',  
              'xwidth': 'pol2',
              'xsigma': 'pol2',
              'ymean' : 'pol1',
              'ysigma': 'pol2',
              'ya1': 'pol2',
              'yn1': 'pol2',
              'ya2': 'pol2',
              'yn2': 'pol2',
          }
        elif yFitFunc == "DG":
            fitFuncs = {
              'xmean' : 'pol1',  
              'xwidth': 'pol2',
              'xsigma': 'pol2',
              'ymean' : 'pol1',
              'ysigma1': 'pol2',
              'ysigma2': 'pol2',
          }
        elif yFitFunc == "DV":
            fitFuncs = {
              'xmean' : 'pol1',  
              'xwidth': 'pol2',
              'xsigma': 'pol2',
              'ymean' : 'pol1',
              'ysigma1': 'pol2',
              'ysigma2': 'pol2',
              'ywidth1': 'pol2',
              'ywidth2': 'pol2',
          }

        xs = []
        x = self.XRANGE[0]
        while x<=self.XRANGE[1]:
            xs += [x]
            x += float(self.XRANGE[1]-self.XRANGE[0])/100
        ys = []
        y = self.YRANGE[0]
        while y<=self.YRANGE[1]:
            ys += [y]
            y += float(self.YRANGE[1]-self.YRANGE[0])/100
        fittedParams = {}
        if   yFitFunc == "V":   yparameters = ['mean','width','sigma']
        elif yFitFunc == "G":   yparameters = ['mean', 'sigma']
        elif yFitFunc == "CB":  yparameters = ['mean', 'sigma', 'a', 'n']
        elif yFitFunc == "DCB": yparameters = ['mean', 'sigma', 'a1', 'n1', 'a2', 'n2']
        elif yFitFunc == "DG":  yparameters = ['mean', 'sigma1', 'sigma2']
        elif yFitFunc == "DV":  yparameters = ['mean', 'sigma1', 'sigma2','width1','width2']
        for param in ['mean','width','sigma']:
            name = '{}_{}{}'.format('x'+param,h,tag)
            xerrs = [0]*len(amasses)
            vals = [results[h][a]['{}_sigx'.format(param)] for a in amasses]
            errs = [errors[h][a]['{}_sigx'.format(param)] for a in amasses]
            graph = ROOT.TGraphErrors(len(avals),array('d',avals),array('d',vals),array('d',xerrs),array('d',errs))
            savename = '{}/{}/{}_Fit'.format(self.plotDir,shift if shift else 'central',name)
            canvas = ROOT.TCanvas(savename,savename,800,800)
            graph.Draw()
            graph.SetTitle('')
            graph.GetHistogram().GetXaxis().SetTitle(self.SPLINELABEL)
            graph.GetHistogram().GetYaxis().SetTitle(param)
            if fit:
                fitResult = graph.Fit(fitFuncs['x'+param])
                func = graph.GetFunction(fitFuncs['x'+param])
                fittedParams['x'+param] = [func.Eval(x) for x in xs]
            canvas.Print('{}.png'.format(savename))

        for param in yparameters:
            name = '{}_{}{}'.format('y'+param,h,tag)
            xerrs = [0]*len(amasses)
            vals = [results[h][a]['{}_sigy'.format(param)] for a in amasses]
            errs = [errors[h][a]['{}_sigy'.format(param)] for a in amasses]
            graph = ROOT.TGraphErrors(len(avals),array('d',avals),array('d',vals),array('d',xerrs),array('d',errs))
            savename = '{}/{}/{}_Fit'.format(self.plotDir,shift if shift else 'central',name)
            canvas = ROOT.TCanvas(savename,savename,800,800)
            graph.Draw()
            graph.SetTitle('')
            graph.GetHistogram().GetXaxis().SetTitle(self.SPLINELABEL)
            graph.GetHistogram().GetYaxis().SetTitle(param)
            if fit:
                fitResult = graph.Fit(fitFuncs['y'+param])
                func = graph.GetFunction(fitFuncs['y'+param])
                fittedParams['y'+param] = [func.Eval(y) for y in ys]
            canvas.Print('{}.png'.format(savename))
    
        # create model
        for a in amasses:
            print h, a, results[h][a]
        if fit:
            modelx = Models.VoigtianSpline(self.SPLINENAME.format(h=h)+'_x',
                **{
                    'masses' : xs,
                    'means'  : fittedParams['xmean'],
                    'widths' : fittedParams['xwidth'],
                    'sigmas' : fittedParams['xsigma'],
                }
            )
        else:
            modelx = Models.VoigtianSpline(self.SPLINENAME.format(h=h)+'_x',
                **{
                    'masses' : avals,
                    'means'  : [results[h][a]['mean_sigx'] for a in amasses],
                    'widths' : [results[h][a]['width_sigx'] for a in amasses],
                    'sigmas' : [results[h][a]['sigma_sigx'] for a in amasses],
                }
            )
        modelx.build(self.workspace,'{}_{}'.format(self.SPLINENAME.format(h=h),tag+'_x'))
        ym = Models.GaussianSpline if ygausOnly else Models.VoigtianSpline
        if fit:
            model = ym(self.SPLINENAME.format(h=h)+'_y',
                **{
                    'x'      : 'y',
                    'masses' : ys,
                    'means'  : fittedParams['ymean'],
                    'widths' : [] if ygausOnly else fittedParams['ywidth'],
                    'sigmas' : fittedParams['ysigma'],
                }
            )
        else:
            if yFitFunc == "V":
                model = Models.VoigtianSpline(self.SPLINENAME.format(h=h),
                    **{
                      'masses' : avals,
                      'means'  : [results[h][a]['mean_sigy'] for a in amasses],
                      'widths' : [results[h][a]['width_sigy'] for a in amasses],
                      'sigmas' : [results[h][a]['sigma_sigy'] for a in amasses],
                    }
                )
            elif yFitFunc == "G":
                model = Models.GaussianSpline(self.SPLINENAME.format(h=h),
                    **{
                      'masses' : avals,
                      'means'  : [results[h][a]['mean_sigy'] for a in amasses],
                      'sigmas' : [results[h][a]['sigma_sigy'] for a in amasses],
                    }
                )
            elif yFitFunc == "CB":
                model = Models.CrystalBallSpline(self.SPLINENAME.format(h=h),
                    **{
                      'masses' : avals,
                      'means'  : [results[h][a]['mean_sigy'] for a in amasses],
                      'sigmas' : [results[h][a]['sigma_sigy'] for a in amasses],
                      'a_s' :    [results[h][a]['a_sigy'] for a in amasses],
                      'n_s' :    [results[h][a]['n_sigy'] for a in amasses],
                    }
                )
            elif yFitFunc == "DCB":
                model = Models.DoubleCrystalBallSpline(self.SPLINENAME.format(h=h),
                    **{
                      'masses' : avals,
                      'means'  : [results[h][a]['mean_sigy'] for a in amasses],
                      'sigmas' : [results[h][a]['sigma_sigy'] for a in amasses],
                      'a1s' :   [results[h][a]['a1_sigy'] for a in amasses],
                      'n1s' :   [results[h][a]['n1_sigy'] for a in amasses],
                      'a2s' :   [results[h][a]['a2_sigy'] for a in amasses],
                      'n2s' :   [results[h][a]['n2_sigy'] for a in amasses],
                    }
                )
            elif yFitFunc == "DG":
                model = Models.DoubleSidedGaussianSpline(self.SPLINENAME.format(h=h),
                    **{
                      'masses' :  avals,
                      'means'  :  [results[h][a]['mean_sigy'] for a in amasses],
                      'sigma1s' : [results[h][a]['sigma1_sigy'] for a in amasses],
                      'sigma2s' : [results[h][a]['sigma2_sigy'] for a in amasses],
                    }
                )
            elif yFitFunc == "DV":
                model = Models.DoubleSidedVoigtianSpline(self.SPLINENAME.format(h=h),
                    **{
                      'masses' :  avals,
                      'means'  :  [results[h][a]['mean_sigy'] for a in amasses],
                      'sigma1s' : [results[h][a]['sigma1_sigy'] for a in amasses],
                      'sigma2s' : [results[h][a]['sigma2_sigy'] for a in amasses],
                      'width1s' : [results[h][a]['width1_sigy'] for a in amasses],
                      'width2s' : [results[h][a]['width2_sigy'] for a in amasses],
                    }
                )
        model.build(self.workspace,'{}_{}'.format(self.SPLINENAME.format(h=h),tag+'_y'))
        model = Models.ProdSpline(self.SPLINENAME.format(h=h),
            '{}_{}'.format(self.SPLINENAME.format(h=h),tag+'_x'),
            '{}_{}'.format(self.SPLINENAME.format(h=h),tag+'_y'),
        )

        if self.binned:
            integrals = [histMap[self.SIGNAME.format(h=h,a=a)].Integral() for a in amasses]
        else:
            integrals = [histMap[self.SIGNAME.format(h=h,a=a)].sumEntries('x>{} && x<{} && y>{} && y<{}'.format(*self.XRANGE+self.YRANGE)) for a in amasses]
        print 'Integrals', tag, h, integrals

        param = 'integral'
        funcname = 'pol2'
        name = '{}_{}{}'.format(param,h,tag)
        vals = integrals
        graph = ROOT.TGraph(len(avals),array('d',avals),array('d',vals))
        savename = '{}/{}/{}_Fit'.format(self.plotDir,shift if shift else 'central',name)
        canvas = ROOT.TCanvas(savename,savename,800,800)
        graph.Draw()
        graph.SetTitle('')
        graph.GetHistogram().GetXaxis().SetTitle(self.SPLINELABEL)
        graph.GetHistogram().GetYaxis().SetTitle('integral')
        if fit:
            fitResult = graph.Fit(funcname)
            func = graph.GetFunction(funcname)
            newintegrals = [func.Eval(x) for x in xs]
            # dont fit integrals
            #model.setIntegral(xs,newintegrals)
        canvas.Print('{}.png'.format(savename))
        model.setIntegral(avals,integrals)

        model.build(self.workspace,'{}_{}'.format(self.SPLINENAME.format(h=h),tag))
        model.buildIntegral(self.workspace,'integral_{}_{}'.format(self.SPLINENAME.format(h=h),tag))

    def fitBackground(self,region='PP',shift='',setUpsilonLambda=False,addUpsilon=True,logy=False):

        if region=='control':
            return super(HaaLimits2D, self).fitBackground(region=region, shift=shift, setUpsilonLambda=setUpsilonLambda,addUpsilon=addUpsilon,logy=logy)

        model = self.workspace.pdf('bg_{}'.format(region))
        name = 'data_prefit_{}{}'.format(region,'_'+shift if shift else '')
        hist = self.histMap[region][shift]['dataNoSig']
        print "region=", region, "\tshift=", shift, "\t", hist.GetName()
        if hist.InheritsFrom('TH1'):
            data = ROOT.RooDataHist(name,name,ROOT.RooArgList(self.workspace.var('x'),self.workspace.var('y')),hist)
        else:
            data = hist.Clone(name)

        data.Print("v")
        print "DataSetName=", data.GetName()
        fr = model.fitTo(data,ROOT.RooFit.Save(),ROOT.RooFit.SumW2Error(True))

        xFrame = self.workspace.var('x').frame()
        data.plotOn(xFrame)
        # continuum
        model.plotOn(xFrame,ROOT.RooFit.Components('cont1_{}_x'.format(region)),ROOT.RooFit.LineStyle(ROOT.kDashed))
        model.plotOn(xFrame,ROOT.RooFit.Components('cont2_{}_x'.format(region)),ROOT.RooFit.LineStyle(ROOT.kDashed))
        if self.XRANGE[0]<4:
            # extended continuum when also fitting jpsi
            model.plotOn(xFrame,ROOT.RooFit.Components('cont3_{}_x'.format(region)),ROOT.RooFit.LineStyle(ROOT.kDashed))
            model.plotOn(xFrame,ROOT.RooFit.Components('cont4_{}_x'.format(region)),ROOT.RooFit.LineStyle(ROOT.kDashed))
            # jpsi
            model.plotOn(xFrame,ROOT.RooFit.Components('jpsi1S'),ROOT.RooFit.LineColor(ROOT.kRed))
            model.plotOn(xFrame,ROOT.RooFit.Components('jpsi2S'),ROOT.RooFit.LineColor(ROOT.kRed))
        # upsilon
        model.plotOn(xFrame,ROOT.RooFit.Components('upsilon1S'),ROOT.RooFit.LineColor(ROOT.kRed))
        model.plotOn(xFrame,ROOT.RooFit.Components('upsilon2S'),ROOT.RooFit.LineColor(ROOT.kRed))
        model.plotOn(xFrame,ROOT.RooFit.Components('upsilon3S'),ROOT.RooFit.LineColor(ROOT.kRed))
        # combined model
        model.plotOn(xFrame)

        canvas = ROOT.TCanvas('c','c',800,800)
        xFrame.Draw()
        #canvas.SetLogy()
        canvas.Print('{}/model_fit_{}{}_xproj.png'.format(self.plotDir,region,'_'+shift if shift else ''))

        yFrame = self.workspace.var('y').frame()
        data.plotOn(yFrame)
        # continuum
        model.plotOn(yFrame,ROOT.RooFit.Components('cont1_{}_y'.format(region)),ROOT.RooFit.LineStyle(ROOT.kDashed))
        # combined model
        model.plotOn(yFrame)

        canvas = ROOT.TCanvas('c','c',800,800)
        yFrame.Draw()
        #canvas.SetLogy()
        canvas.Print('{}/model_fit_{}{}_yproj.png'.format(self.plotDir,region,'_'+shift if shift else ''))

        pars = fr.floatParsFinal()
        vals = {}
        errs = {}
        for p in range(pars.getSize()):
            vals[pars.at(p).GetName()] = pars.at(p).getValV()
            errs[pars.at(p).GetName()] = pars.at(p).getError()
        for v in sorted(vals.keys()):
            print '  ', v, vals[v], '+/-', errs[v]


    ###############################
    ### Add things to workspace ###
    ###############################
    def addData(self,asimov=False,addSignal=False,**kwargs):
        mh = kwargs.pop('h',125)
        ma = kwargs.pop('a',15)
        for region in self.REGIONS:
            name = 'data_obs_{}'.format(region)
            hist = self.histMap[region]['']['data']
            if asimov:
                # generate a toy data observation from the model
                # TODO addSignal
                model = self.workspace.pdf('bg_{}'.format(region))
                h = self.histMap[region]['']['dataNoSig']
                if h.InheritsFrom('TH1'):
                    integral = h.Integral() # 2D integral?
                else:
                    integral = h.sumEntries('x>{} && x<{} && y>{} && y<{}'.format(*self.XRANGE+self.YRANGE))
                data_obs = model.generate(ROOT.RooArgSet(self.workspace.var('x'),self.workspace.var('y')),int(integral))
                if addSignal:
                    self.workspace.var('MH').setVal(ma)
                    model = self.workspace.pdf('{}_{}'.format(self.SPLINENAME.format(h=mh),region))
                    integral = self.workspace.function('integral_{}_{}'.format(self.SPLINENAME.format(h=mh),region)).getVal()
                    sig_obs = model.generate(ROOT.RooArgSet(self.workspace.var('x'),self.workspace.var('y')),int(integral))
                    data_obs.append(sig_obs)
                data_obs.SetName(name)
            else:
                # use the provided data
                if hist.InheritsFrom('TH1'):
                    data_obs = ROOT.RooDataHist(name,name,ROOT.RooArgList(self.workspace.var('x'),self.workspace.var('y')),self.histMap[region]['']['data'])
                else:
                    data_obs = hist.Clone(name)
            self.wsimport(data_obs)

    def addBackgroundModels(self, fixAfterControl=False, fixAfterFP=False, addUpsilon=True, setUpsilonLambda=False, voigtian=False, logy=False):
        if fixAfterControl:
            self.fix()
        for region in self.REGIONS:
            self.buildModel(region=region, addUpsilon=addUpsilon, setUpsilonLambda=setUpsilonLambda, voigtian=voigtian)
            self.workspace.factory('bg_{}_norm[1,0,2]'.format(region))
            self.fitBackground(region=region, setUpsilonLambda=setUpsilonLambda, addUpsilon=addUpsilon, logy=logy)
        if fixAfterControl:
            self.fix(False)

    def addSignalModels(self,yFitFunc="V",**kwargs):
        for region in self.REGIONS:
            for shift in ['']+self.SHIFTS:
                for h in self.HMASSES:
                    print "IN addSignalModel", region, shift, h
                    if shift == '':
                        self.buildSpline(h,region=region,shift=shift,yFitFunc=yFitFunc,**kwargs)
                    else:
                        self.buildSpline(h,region=region,shift=shift+'Up',yFitFunc=yFitFunc,**kwargs)
                        self.buildSpline(h,region=region,shift=shift+'Down',yFitFunc=yFitFunc,**kwargs)
            self.workspace.factory('{}_{}_norm[1,0,9999]'.format(self.SPLINENAME.format(h=h),region))

    ######################
    ### Setup datacard ###
    ######################
    def setupDatacard(self, addControl=False):

        # setup bins
        for region in self.REGIONS:
            self.addBin(region)

        # add processes
        self.addProcess('bg')

        for proc in [self.SPLINENAME.format(h=h) for h in self.HMASSES]:
            self.addProcess(proc,signal=True)

        # set expected
        for region in self.REGIONS:
            h = self.histMap[region]['']['dataNoSig']
            if h.InheritsFrom('TH1'):
                integral = h.Integral() # 2D restricted integral?
            else:
                integral = h.sumEntries('x>{} && x<{} && y>{} && y<{}'.format(*self.XRANGE+self.YRANGE))
            self.setExpected('bg',region,integral)

            for proc in [self.SPLINENAME.format(h=h) for h in self.HMASSES]:
                self.setExpected(proc,region,1) # TODO: how to handle different integrals
                self.addRateParam('integral_{}_{}'.format(proc,region),region,proc)
                
            self.setObserved(region,-1) # reads from histogram

        if addControl:
            region = 'control'

            self.addBin(region)

            h = self.histMap[region]['']['dataNoSig']
            if h.InheritsFrom('TH1'):
                integral = h.Integral(h.FindBin(self.XRANGE[0]),h.FindBin(self.XRANGE[1]))
            else:
                integral = h.sumEntries('x>{} && x<{}'.format(*self.XRANGE))
            self.setExpected('bg',region,integral)

            self.setObserved(region,-1) # reads from histogram

    ###################
    ### Systematics ###
    ###################
    def addSystematics(self):
        self.sigProcesses = tuple([self.SPLINENAME.format(h=h) for h in self.HMASSES])
        self._addLumiSystematic()
        self._addMuonSystematic()
        self._addTauSystematic()
        self._addShapeSystematic()
        self._addControlSystematics()

    ###################################
    ### Save workspace and datacard ###
    ###################################
    def save(self,name='mmmt', subdirectory=''):
        processes = {}
        for h in self.HMASSES:
            processes[self.SIGNAME.format(h=h,a='X')] = [self.SPLINENAME.format(h=h)] + ['bg']
        if subdirectory == '':
          self.printCard('datacards_shape/MuMuTauTau/{}'.format(name),processes=processes,blind=False,saveWorkspace=True)
        else:
          self.printCard('datacards_shape/MuMuTauTau/' + subdirectory + '{}'.format(name),processes=processes,blind=False,saveWorkspace=True)

