#This plots Alice's extinction ratio over time.
#It retrieves data stored from the corresponding table in the database and then plots the data.
#Requirements: Python3, mysql, packages listed below

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import math
import pymysql
import os
import matplotlib as mpl

#Start and end datetimes that define range of data to retrieve from mysql table
START_TIME = '2019-12-09 17:03:08'
END_TIME = '2019-12-09 18:00:00'


TABLE_NAME = 'ratiorecord'


#Connect to mysql database
db = pymysql.connect(host="192.168.0.125",  #IP of computer with database. Local host if is same computer.
					 user="inqnet1", #username
					 passwd="Teleport1536!",  # your password
					 db="extinctionR", #name of the database
					 charset='utf8mb4',
					 cursorclass=pymysql.cursors.DictCursor)

#Arrays to fill with data from mysql table
ExRatioArr=[]
datetimeArr=[]
vmaxArr=[]
vavArr=[]

mpl.rcParams["savefig.directory"] = os.chdir(os.path.dirname("/home/inqnet1/Desktop/CQNET/CQNET-Interf"))


try:
	#Create cursor to select data from mysql.
	with db.cursor() as cur:
		#Mysql command to select data from each column
		query = "SELECT vmax,vav,datetime FROM "+TABLE_NAME+" WHERE datetime BETWEEN {ts %s} AND {ts %s}"
		#Execute query, then store data from columns in arrays
		cur.execute(query,(START_TIME,END_TIME,))
		row = cur.fetchone() #Retrieves row of table at START_TIME
		while row is not None: #Iterates through valid rows
			vmax = row["vmax"]
			vmaxArr.append(1000*vmax)
			vav = row["vav"]
			vavArr.append(1000*vav)
			eRat = -10*np.log10(vav/vmax)
			ExRatioArr.append(eRat)
			datetimeArr.append(row["datetime"])
			row = cur.fetchone()
finally: #Once store the data of each column in separate arrays, close the database
	db.close()

vmaxArr=np.array(vmaxArr)
vavArr=np.array(vavArr)
ExRatioArr=np.array(ExRatioArr)
datetimeArr=np.array(datetimeArr)

#Get the first and last datetimes of the extinction ratio data. The retrieved data falls within the
#bounds of the start and end times that were specified, but may not be exactly the same.
datetime_first = str(datetimeArr[0])
datetime_last = str(datetimeArr[-1])
first_time = datetime.datetime.strptime(datetime_first,'%Y-%m-%d %H:%M:%S')
datetime_dt = []
datetime_el = []

#Create the elapsed time array for extinction ratio
for t in datetimeArr:
	t=str(t)
	datime=datetime.datetime.strptime(t,'%Y-%m-%d %H:%M:%S')
	elapsed = datime- first_time
	datetime_dt.append(datime)
	datetime_el.append((elapsed.total_seconds())/60) #Convert elapsed time from seconds to minutes

#Plot data
#Stacked plot of all data
fig, axs = plt.subplots(3,1, num=1, sharex=True)
#Vapplied Plot
axs[0].plot(datetime_el, ExRatioArr,  linestyle = 'none', marker = '.', markersize = 2)
axs[0].set_ylabel(r"Ext Ratio")
axs[0].grid()
#Vin Plot
axs[1].plot(datetime_el, vavArr,  linestyle = 'none', marker = '.', markersize = 2)
axs[1].set_ylabel(r"$V_{min,av}$ (mV)")
axs[1].grid()
#Phase Plot
axs[2].plot(datetime_el, vmaxArr,  linestyle = 'none', marker = '.', markersize = 2)
axs[2].set_ylabel(r"$V_{max}$ (mV)")
axs[2].grid()
xmin1=0
xmax1=0
fig.suptitle("Alice's Pulse Extinction Ratio from \n"+str(datetimeArr[0]+datetime.timedelta(minutes=xmin1))+" to "+str(datetimeArr[-1]+datetime.timedelta(minutes=-xmax1)))
plt.xlabel('Elapsed time (min)', fontsize =16)
plt.show()
