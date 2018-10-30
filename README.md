# CombineLimits
Standalone limits to run with combine in the CMSSW framework

## Setup

```bash
cmsrel CMSSW_8_1_0
cd CMSSW_8_1_0/src
cmsenv
git cms-init
git clone git@github.com:dntaylor/CombineLimits.git
./CombineLimits/recipe/recipe.sh
```

## Kyle's stuff

Devin, you have your own wrapper and way of running the fitting and what not. I'll cover the background systematic stuff here.  

To Generate:
```bash
combine datacards_shape/MuMuTauTau/Final_VisibleHiggs_cont_150to1200/mmmt_mm_parametric_HToAAH300AX.txt  -M GenerateOnly --toysFrequentist -t 100 --expectSignal 10 --saveToys -m 7 --seed=1234567890
```

To FitDiagnostic:
```bash
combine datacards_shape/MuMuTauTau/Final_VisibleHiggs_2cont_150to1200/mmmt_mm_parametric_HToAAH300AX.txt  -M FitDiagnostics --rMin -10 --rMax 10 --toysFile higgsCombineTest.GenerateOnly.mH7.1234567890.root -t 100 -m 7 --seed=1234567890
```

Any scripts I used to fit didn't properly display the fit, so here are the commands executed in a root terminal to get the fit:

```bash
TFile f("CombineFitDiagnostics750.root");
TCanvas c;
TH1 *H = (TH1*)f.Get("h1");
H->Fit("gaus","");
gStyle->SetOptFit(1);
```

To get the overlays for the fits for the tail of the Visible higgs distribution, I fitted the samples separately, and then executed the file "RootFitYProj.py". Here, you need to set the parameters to whatever value is stored in the fitParams/ directory, since otherwise it will try to fit the newly specified region.

I don't believe there is anything else that is unique to my code from this directory that you don't have implemented yourself. To fit a specific region of the YRANGE, nothing needed to be done other than just to hard set the global variable in the HaaLimits class.

