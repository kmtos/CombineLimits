import os
import sys
import logging
import itertools
import numpy as np
import argparse
import math
import errno

import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch()

def getDataset(ds,weight='w',selection='1',xRange=[],yRange=[]):
   args = ds.get()
   if xRange:
     args.find('x').setRange(*xRange)
   if args.find('y1'):
     args.find('y1').SetName('y')
     args.find('y').SetTitle('y')
   if yRange:
     args.find('y').setRange(*yRange)
   ds = ROOT.RooDataSet(ds.GetName(),ds.GetTitle(),ds,args,selection,weight)
   return ds

ws = ROOT.RooWorkspace("ws")
f_FakeRateRegionB = ROOT.TFile.Open("/eos/cms/store/user/ktos/ShapeDifferences/MiniAOD_SingleMu_MedIsoMu2_TauDMAntiMedIso_SEP2_BItself_Plots.root")
ds = f_FakeRateRegionB.Get("mumufourBodymass_dataset")
ds = getDataset(ds, selection='', xRange=[0,30], yRange=[150,1200])
canvas = ROOT.TCanvas('c','c',800,800)
args = ds.get()
yFrame = args.find("y").frame()
canvas.cd()
ds.plotOn(yFrame)
yFrame.Draw()
canvas.Print("TESTYTEST.png")
#h1 = ds.createHistogram(args.find("y"), '', "h1")
h2 = ds.createHistogram(args.find("x"), args.find("y"), '', 'h2')
h1 = h2.ProjectionY("h1")
outFile = ROOT.TFile("TESTYTEST.root", 'recreate')
outFile.cd()
h1.Write()
h2.Write()

f1 = ROOT.TF1("f1", "[0]+[1]*x",150,1200)
f1.SetParameter(0, 15.74)
f1.SetParameter(1, -0.0336115)
f2 = ROOT.TF1("f2", "[0]+[1]*x+[2]*x*x",150,1200)
f2.SetParameter(0, 85.35)
f2.SetParameter(1, -0.412)
f2.SetParameter(2, 0.000492209)
f3 = ROOT.TF1("f3", "[0]+[1]*x+[2]*x*x+[3]*x*x*x",150,1200)
f3.SetParameter(0, 251.123)
f3.SetParameter(1, -1.87283)
f3.SetParameter(2, 0.00460389)
f3.SetParameter(3,-3.71114e-06)
f4 = ROOT.TF1("f4", "[0]+[1]*x+[2]*x*x+[3]*x*x*x+[4]*x*x*x*x",150,1200)
f4.SetParameter(0, 554.088)
f4.SetParameter(1, -5.61481)
f4.SetParameter(2,  0.0211566)
f4.SetParameter(3, .0211566)
f4.SetParameter(4, 2.14178e-08)
f5 = ROOT.TF1("f5", "[0]+[1]*x+[2]*x*x+[3]*x*x*x+[4]*x*x*x*x+[5]*x*x*x*x*x",150,1200)
f5.SetParameter(0, 965.043)
f5.SetParameter(1, -12.2521)
f5.SetParameter(2, 0.0624003)
f5.SetParameter(3, -0.000158721)
f5.SetParameter(4, 2.01178e-07)
f5.SetParameter(5, -1.01467e-10)

f1.SetLineColor(ROOT.kRed) 
f2.SetLineColor(ROOT.kBlue) 
f3.SetLineColor(ROOT.kYellow+3) 
f4.SetLineColor(ROOT.kGreen+2) 
f5.SetLineColor(ROOT.kOrange) 

canvas1 = ROOT.TCanvas('c1','c',800,800)
canvas1.cd()
h1.Draw()
f1.Draw("SAME")
f2.Draw("SAME")
f3.Draw("SAME")
f4.Draw("SAME")
f5.Draw("SAME")
canvas1.Write()

#hp5 = h1.Clone()
#hp4 = h1.Clone()
#hp3 = h1.Clone()
#hp2 = h1.Clone()
#hp1 = h1.Clone()

#print "poly 5"
#hp5.Fit("pol5")
#
#print "poly 4"
#hp4.Fit("pol4")
#
#print "poly 3"
#hp3.Fit("pol3")
#
#print "poly 2"
#hp2.Fit("pol2")
#
#print "poly1"
#hp1.Fit("pol1")
#
#hp5.Write()
#hp4.Write()
#hp3.Write()
#hp2.Write()
#hp1.Write()
#
#print "type(h1)=", type(h1)
outFile.Write()
outFile.Close()
