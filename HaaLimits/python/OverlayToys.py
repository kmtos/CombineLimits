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

f_toys= ROOT.TFile("higgsCombineTest.GenerateOnly.mH7.88888.root")
ds2 = f_toys.Get("toys/toy_2")
ds3 = f_toys.Get("toys/toy_3")
ds4 = f_toys.Get("toys/toy_4")
ds5 = f_toys.Get("toys/toy_5")

f = ROOT.TFile("datacards_shape/MuMuTauTau/Final_VisibleHiggs_cont_150to1200/mmmt_mm_parametric.root")
w = f.Get("w")
y = w.var("y")

pdf_PP = w.pdf("bg_PP_y")
args = pdf_PP.getVariables()
args.setRealValue("lambda_conty1_PP_y",-0.022377359071031)

yFrame2 = y.frame()
ds2.plotOn(yFrame2, ROOT.RooFit.Range(150,1200), ROOT.RooFit.Name("data"))
pdf_PP.plotOn(yFrame2, ROOT.RooFit.LineColor(ROOT.kBlue), ROOT.RooFit.LineWidth(2), ROOT.RooFit.Range(150,1200), ROOT.RooFit.Name("Erf2"))

yFrame3 = y.frame()
ds3.plotOn(yFrame3, ROOT.RooFit.Range(150,1200), ROOT.RooFit.Name("data"))
pdf_PP.plotOn(yFrame3, ROOT.RooFit.LineColor(ROOT.kBlue), ROOT.RooFit.LineWidth(2), ROOT.RooFit.Range(150,1200), ROOT.RooFit.Name("Erf3"))

yFrame4 = y.frame()
ds4.plotOn(yFrame4, ROOT.RooFit.Range(150,1200), ROOT.RooFit.Name("data"))
pdf_PP.plotOn(yFrame4, ROOT.RooFit.LineColor(ROOT.kBlue), ROOT.RooFit.LineWidth(2), ROOT.RooFit.Range(150,1200), ROOT.RooFit.Name("Erf4"))

yFrame5 = y.frame()
ds5.plotOn(yFrame5, ROOT.RooFit.Range(150,1200), ROOT.RooFit.Name("data"))
pdf_PP.plotOn(yFrame5, ROOT.RooFit.LineColor(ROOT.kBlue), ROOT.RooFit.LineWidth(2), ROOT.RooFit.Range(150,1200), ROOT.RooFit.Name("Erf5"))

leg = ROOT.TLegend(.65,.6,.85,.9)
leg.SetBorderSize(0)
leg.SetFillColor(0)
leg.SetFillStyle(0)
leg.SetTextFont(42)
leg.SetTextSize(0.035)
leg.AddEntry(yFrame2.findObject("data"), "data","EP")
leg.AddEntry(yFrame2.findObject("Erf2"),  "Erf*Exp","L")

outFile = ROOT.TFile("OverlayToys.root", 'recreate')
outFile.cd()
\
canvas2 = ROOT.TCanvas('canvas2','toy2',800,800)
canvas2.cd()
yFrame2.Draw()
leg.Draw()
canvas2.SetLogy()
canvas2.Print("toy2.png")
canvas2.Write()

canvas3 = ROOT.TCanvas('canvas3','toy3',800,800)
canvas3.cd()
yFrame3.Draw()
leg.Draw()
canvas3.SetLogy()
canvas3.Print("toy3.png")
canvas3.Write()

canvas4 = ROOT.TCanvas('canvas4','toy4',800,800)
canvas4.cd()
yFrame4.Draw()
leg.Draw()
canvas4.SetLogy()
canvas4.Print("toy4.png")
canvas4.Write()

canvas5 = ROOT.TCanvas('canvas5','toy5',800,800)
canvas5.cd()
yFrame5.Draw()
leg.Draw()
canvas5.SetLogy()
canvas5.Print("toy5.png")
canvas5.Write()

outFile.Write()
outFile.Close()



