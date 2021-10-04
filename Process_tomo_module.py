#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 20 18:29:05 2021

@author: basnetn2
"""
import numpy as np
import os
import glob
import subprocess
import starfile
import pandas as pd
import shutil
from pathlib import Path

##################################################################################################

#Input

kv = 300  #krios=300kv glacios = 200kv
pix = 1.678 ## for motioncorr # raw files are binned during motion corr(superresolution)
cs = 2.7 # spherical aberration
ampc = 0.1 # amplitude contrast

R_pix= pix*2   ###change binning factor if needed, if not acquired at superresoultion binning factor is 1

gain_file = " " # if no gain file leave it empty

def_file = " " # if no defect file leave it empty

rot = 0 # no rotation of gain file

flip = 0 # no flip of gain file

bin_f = 2 # normally 2 for the superresoultion file

##################################################################################################

def motioncor(df,gain=gain_file,defect=def_file,Rot=rot, Flip=flip,Bin=bin_f):
      for i in df['frames']:
            cmd = 'MotionCor2 -InTiff ' + i.strip() + ' -OutMrc ' + i.split('.')[0]+'.mrc' + ' -Patch 7,5'  + ' -Iter 10' + ' -Tol 0.5 ' + ' -Kv ' + str(kv) + ' -PixSize ' + str (pix) + ' -Gpu 0 ' + ' -Bft 500 150  ' + '-LogFile  ' +  i.split('.')[0]+'.log ' + '-Gain '+ gain_file + ' DefectFile ' + def_file  + ' -RotGain '+ str(Rot) + ' -FlipGain '+ str(flip) + ' -FtBin '+ str(bin_f)

            subprocess.run(cmd,shell=True)


def make_stack(df):
      section = 0
      total_images = len(df['aligned_frames'])
      newstack_image_file = [total_images]
      for i in df_tomo['aligned_frames']:
            try:
                  newstack_image_file.append(i)
                  newstack_image_file.append(section)
                  np.savetxt('images.txt',np.array([newstack_image_file]).swapaxes(1,0),fmt='%s')
                  stack = 'newstack ' + '-filei images.txt ' + 'stack.mrc'
                  subprocess.run(stack,shell=True)
            except:
                  pass



def rearrange_gctf(gctf_file, df):
      """
      Re-arranges the gdct output file as per tilt angle
      Parameters
      ----------
      gctf_file :str
            name of gctf file
      df : dataframe
            dataframe which consists list osrted as per tilt angle,used as reference for ctf file

      Returns
      -------
      None.

      """
      if gctf_file.is_file():
            gctf_star =starfile.open('micrographs_all_gctf.star')
            gctf_star = gctf_star.set_index('rlnMicrographName')
            gctf_star = gctf_star.reindex(index=df['aligned_frames'])
            gctf_star = gctf_star.reset_index()
            starfile.write(gctf_star,'ctf.star')
      else:
            pass

##################################################################################################

cwd = os.getcwd()

tomographs = np.loadtxt('tomograph.log',dtype=str)

for l in  tomographs:
      os.chdir(l[0:-9]+'/Motioncorr')
      #print(os.getcwd())
      print('Running Motioncor2..')
      shutil.copy(f'../{l[0:-9]}.txt',os.getcwd())
      shutil.copy('../missing_frames.txt',os.getcwd())
      df_tomo = pd.read_csv(f'{l[0:-9]}.txt')
      tilt = df_tomo['tilts']
      tilt.to_csv(f'{l[0:-9]}_motion_corr_dosefilt.rawtlt', header=False,index=False)

      ########Run motioncorr
      motioncor(df_tomo)

      ########Run ctffind
      print('Running Ctffind')
      ctf_cmd = 'Gctf --apix '+ str(R_pix) + ' --kV ' + str(kv) + ' --Cs ' + str(cs) + ' --ac ' + str(ampc) + ' -defS 500 --astm 1000 --resL 50 --resH 5 ' + '*.mrc' + ' --boxsize 512 --resL 30 --resH 5 --defL  5000 --defH 50000 --defS  500 --astm 100'
      subprocess.run(ctf_cmd,shell=True)

      #gctf_file_name = Path('micrographs_all_gctf.star') ##no need to change

      #rearrange_gctf(gctf_file_name, df_tomo)

      #os.rename('ctf.star',f'{l[0:-9]}_ctf.star')

######make stack for no-dosefilter

      count = len(open('missing_frames.txt').readlines())

      if count == 0:
            make_stack(df_tomo)

      else:
            pass
            print('You have missing frame'+l[0:-9])

      os.rename('stack.mrc',f'{l[0:-9]}_motion_corr_nofilt.mrc')

######## Dose-filtering

      df_dose = df_tomo[['pre-dose','dose']]
      df_dose.to_csv(l[0:-9]+'dose.txt',sep = ' ',index=False,header=False)
      
      mtfilter = f" mtffilter -InputFile {l[0:-9]}_motion_corr_nofilt.mrc -OutputFile {l[0:-9]}_motion_corr_dosefilt.mrc -TypeOfDoseFile 3 -DoseWeightingFile {l[0:-9]}dose.txt -PixelSize {R_pix/10}"

      subprocess.run(mtfilter,shell=True)

########## move the stacks

      shutil.move(f'{l[0:-9]}_motion_corr_nofilt.mrc', f'{cwd}/{l[0:-9]}/{l[0:-9]}_motion_corr_nofilt.mrc')
      shutil.move(f'{l[0:-9]}_motion_corr_dosefilt.mrc', f'{cwd}/{l[0:-9]}/{l[0:-9]}_motion_corr_dosefilt.mrc')
      shutil.move(f'{l[0:-9]}_motion_corr_dosefilt.rawtlt',f'{cwd}/{l[0:-9]}/{l[0:-9]}_motion_corr_dosefilt.rawtlt')


      os.chdir(cwd)





