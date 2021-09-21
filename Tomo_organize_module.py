#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 20 16:59:06 2021

@author: basnetn2
"""

import glob
import os
import shutil
import numpy as np
from datetime import datetime
import math
import pandas as pd

##########################################################################################

#Input

raw_data = 'c44-1-mmongrid1' # directory containing the raw data file like mrc.mdoc files and mrc files

frames = 'moongrid_frames' # directory containing frames

files = raw_data+'/'+"*.mrc.mdoc" ##no need to change if anything else it wont work

prefix = 'tomo' # prefix of the tomograms he prefix used for tomo,it should be similar for all tomograms,for eg. prefix for tomo01.mrc,tomo02.mrc will be "tomo"

e_dose = 1.57 ## electron_dose per frame in A2

##########################################################################################


def tomolist(tomo_prefix,files):
      """
      creates a list of tomogram needed for processing

      Parameters
      ----------
      files : str
            *.mrc.mdoc,*.mrc.mdoc file are created by the serail em for each tomogram
      
      tomo_prefix:  str
      the prefix used for tomo,it should be similar for all tomograms,for eg. prefix for tomo01.mrc,tomo02.mrc
      will be tomo
      sometimes there willbe other rawdata files like gridmap.mrc or other .mrc files which are not tomograms

      Returns
      -------
      list of tomograms

      """

      tomos = []
      tomo_pref = tomo_prefix   ###### Master input ###make sure it finds absoultye value not tomogram

      for k in glob.glob(files):
            if tomo_pref in k:
                  tomos.append(k.split('/')[-1])

      return tomos


def get_tomolist(f1):

      """
      This functions extract all necessary information from the mdoc files and makes an table.
      This contains various metadata information for various processes
      """
      co1 = []
      frames = []
      image = []
      time = []
      frame_number= []
      file = open(f1)
      for line in file:
            if 'TiltAngle' in line:
                (col1,col2)=line.split('=')
                #print (col2)
                co1.append(float(col2))
        
            elif 'DateTime' in line:
                (ind, date_time) = line.split('=')
                time.append(date_time.strip())

            elif 'NumSubFrames' in line:
                  subframes = line.split('=')[-1]
                  frame_number.append(subframes)

            if 'SubFramePath' in line:
                (col1,col2)=line.split('=')
                name=col2.split('\\')[-1]
                aligned_frame = name.split('.')[0]+'.mrc'

                frames.append(name)
                image.append(aligned_frame)

      
      array = np.array([co1,frames,image,time,frame_number]).swapaxes(1,0)
      return (array)
      file.close()


def dose_info(array,dose_perframe):

      """
      Description: This will take array created by function get_tomolist and dose per frame and calulates dose information for each tilt.
      the output will be array with the two dose information for each tilt: prior cumulative dose and cumulative dose at the end of the image


      Parameters
      ----------
      array : numpy array
            output of function get_tomolist
      dose_perframe : dose per frame in e/A2
             float value

      Returns
      -------
      array 

      """

      #sort according to date and time.Important fortomograms ran with dose symmetric data collection

      sortedArray = np.array(sorted(array, key=lambda x: datetime.strptime(x[3], '%d-%b-%y %H:%M:%S')))


      dose_per_tilt = []
      prior_tilt_dose = []
      dose = 0
      new_dose = []
      for i in sortedArray:
          prior_tilt_dose.append(dose)
          #dose_O = float(i[3])*dose_perframe
          dose_t = (1/math.cos(abs(float(i[0])*math.pi/180)))*dose_perframe
          dose_per_tilt.append(dose_t)
          cum_dose = dose_t + dose
          new_dose.append(cum_dose)
          dose = cum_dose
          print(dose)

      array_dose = np.array([prior_tilt_dose,new_dose]).swapaxes(1, 0)
      array_dose = np.append(sortedArray,array_dose,axis=1)
      sorted_dose_array = np.array(sorted(array_dose, key=lambda l:float(l[0]))) #sort according to tilt angles
      return(sorted_dose_array)


def organize_data(raw_data,frames,l):
      """
      

      Parameters
      ----------
      raw_data : str
            path/name of directory which contains raw data. ".mrc files or .mrc.mdoc files"
      frames : str
            path/name of directory which contains frames
      l : list
      name containing the list of tomograms

      Returns
      -------
      None.
      creates subdirectory for each tomograms 

      """

      cwd = os.getcwd()
      
      os.chdir(cwd+'/'+raw_data)

      os.chdir(cwd)


      os.makedirs(l[0:-9])

      os.chdir(l[0:-9])

      os.makedirs('Motioncorr')

      shutil.move(cwd+'/'+raw_data+'/'+l, os.getcwd())

      shutil.move(cwd+'/'+raw_data+'/'+l[0:-5], os.getcwd())

      array_sort = get_tomolist(l)  #local modules

      array_dose = dose_info(array_sort, e_dose)

      np.savetxt ('tomolist.log',array_sort,fmt = '%s',delimiter=" ")
      df_tomo = pd.DataFrame(array_dose, columns = ['tilts','frames','aligned_frames', 'time', 'subframes','pre-dose','dose'])
      df_tomo.to_csv(l[0:-9]+'.txt')

      missing_frames = []

      print(l)

      for j in range(len(array_sort)):
            try:
                  mrc_file = str(array_sort[j][1]).strip()

                  shutil.move(cwd+'/'+frames+'/'+mrc_file, "Motioncorr")
            except:
                  missing_frames.append(mrc_file)
                  pass

      missing_frames = np.array([missing_frames]).swapaxes(1, 0)
      np.savetxt('missing_frames.txt',missing_frames,fmt='%s')
      os.chdir(cwd)

      return

##########################################################################################

def main():
      tomographs = tomolist(prefix,files)
      for i in tomographs:
            organize_data(raw_data, frames,i)

      tomograph_array = np.array([tomographs]).swapaxes(1,0)

      np.savetxt('tomograph.log',tomograph_array, fmt='%s')


if __name__ == "__main__":
      main()




