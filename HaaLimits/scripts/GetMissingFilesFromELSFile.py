import string


values =[10, 10.1 , 10.2 , 10.3 , 10.4 , 10.5 , 10.6 , 10.7 , 10.8 , 10.9 , 11, 11.1 , 11.2 , 11.3 , 11.4 , 11.5 , 11.6 , 11.7 , 11.8 , 11.9 , 12, 12.1 , 12.2 , 12.3 , 12.4 , 12.5 , 12.6 , 12.7 , 12.8 , 12.9 , 13, 13.1 , 13.2 , 13.3 , 13.4 , 13.5 , 13.6 , 13.7 , 13.8 , 13.9 , 14, 14.1 , 14.2 , 14.3 , 14.4 , 14.5 , 14.6 , 14.7 , 14.8 , 14.9 , 15, 15.1 , 15.2 , 15.3 , 15.4 , 15.5 , 15.6 , 15.7 , 15.8 , 15.9 , 16, 16.1 , 16.2 , 16.3 , 16.4 , 16.5 , 16.6 , 16.7 , 16.8 , 16.9 , 17, 17.1 , 17.2 , 17.3 , 17.4 , 17.5 , 17.6 , 17.7 , 17.8 , 17.9 , 18, 18.1 , 18.2 , 18.3 , 18.4 , 18.5 , 18.6 , 18.7 , 18.8 , 18.9 , 19, 19.1 , 19.2 , 19.3 , 19.4 , 19.5 , 19.6 , 19.7 , 19.8 , 19.9 , 20, 20.1 , 20.2 , 20.3 , 20.4 , 20.5 , 20.6 , 20.7 , 20.8 , 20.9 , 21, 3.7 , 3.8 , 3.9 , 4, 4.1 , 4.2 , 4.3 , 4.4 , 4.5 , 4.6 , 4.7 , 4.8 , 4.9 , 5, 5.1 , 5.2 , 5.3 , 5.4 , 5.5 , 5.6 , 5.7 , 5.8 , 5.9 , 6, 6.1 , 6.2 , 6.3 , 6.4 , 6.5 , 6.6 , 6.7 , 6.8 , 6.9 , 7, 7.1 , 7.2 , 7.3 , 7.4 , 7.5 , 7.6 , 7.7 , 7.8 , 7.9 , 8, 8.1 , 8.2 , 8.3 , 8.4 , 8.5 , 8.6 , 8.7 , 8.8 , 8.9 , 9, 9.1 , 9.2 , 9.3 , 9.4 , 9.5 , 9.6 , 9.7 , 9.8 , 9.9]

fileLists = ['OUTPUT_DevVersion_mumu_SEP5_RooDataSet_x2.5to30_NODE.out', 'OUTPUT_mumufourBody_SEP5_DCB_NODE.out', 'OUTPUT_mumufourBody_SEP5_DG_All_NODE.out', 'OUTPUT_mumufourBody_SEP5_DG_DiffNorm_NODE.out', 'OUTPUT_mumufourBody_SEP5_DG_Final_NODE.out', 'OUTPUT_mumufourBody_SEP5_PPyDG_FPyDCB_NODE.out', 'OUTPUT_mumutautau_SEP5_PPyLmin0p75_FPyVmin0p75_NODE.out']


for f in  fileLists:
  f_r = open (f, "r")
  f_w = open ("ToCommit_" + f, "w+")
  print "\n\n", f
  numbers = []
  for line in f_r:
    pos = line.find("mH")
    #print line, pos, len(line)
    numbers.append(line[pos+2:len(line)-6] )
  print numbers
  for num in values:
    if str(num) in numbers: continue
    print num
    f_w.write(str(num)+"\n" )
