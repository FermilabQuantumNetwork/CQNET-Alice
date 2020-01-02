#This script maximizes Alice's IM extinction ratio by minimizing the IM's output
#optical power and prevents drifting.
# It scans over the tuning voltage for Alice's intensity modulator (IM) and
#finds the tuning voltage corresponding to the minimum output power, then
#periodically does fine range scans to find and keep the IM at min power.
#Alice has a 21 dB IM with one tuning voltage pin.
#Requirements: Python3, AliceScanFunc.py in same directory, packages listed below
# and in AliceScanFunc
from AliceScanFunc import *
import pymysql
import pyvisa as visa
import time
import math
from ThorlabsPM100 import ThorlabsPM100, USBTMC
import matplotlib.pyplot as plt
import matplotlib as mpl
#Need to allow permission: sudo chown inqnet4:inqnet4 /dev/usbtmc0

#Sets directory for saving figures produced by this script
mpl.rcParams["savefig.directory"] = os.chdir(os.path.dirname("/home/inqnet4/Desktop/CQNET/Alice"))

#Connect to mysql database
db = pymysql.connect(host = "192.168.0.125",  #IP of computer with database. Local host if is same computer.
					user ="INQNET4", # username
					password="Teleport1536!", # your password
					database="teleportcommission", #name of database
					charset='utf8mb4',
					cursorclass=pymysql.cursors.DictCursor)



#Connect to powermeter
VISAInstance=pyvisa.ResourceManager('@py')
resourceName='USB0::4883::32888::P0024508::0::INSTR'
inst=VISAInstance.open_resource(resourceName)
print(inst.ask("*IDN?"))
powermeter = ThorlabsPM100(inst=inst)
Vscan = 0.03 #Range of fine scan for intensity modulator (IM)
numV=400 #Number of points to divide initial scan range for IM
Vmin=0 #in Volts
Vmax=15#in Volts
feedbackPause = 60  #How long to wait between fine scans
#Connect to powersupply
VISAInstance=pyvisa.ResourceManager('@py')
Resource=InitiateResource() #See AliceScanFunc.py


#Channel number corresponding to Alice's tuning pin.
ChannelNumber=1
print("DCBias_ChannelNumber: ", ChannelNumber)


#Create cursor to select data from mysql.
cur = db.cursor()
#Option to back up data to textfile
backup = False
print("Back up to text file: " + str(backup))
if backup:
	txtFile = open("VapVinPIM.txt","w")


#Mysql commands to get the index of the last entry of IM table
query = "SELECT max(id) from IM"
cur.execute(query)
result = cur.fetchall()
resultDict = result[0]
maxid=resultDict["max(id)"]
if maxid is None:
	maxid=0
i = maxid +1

Parr=[]
VapArr = []
eRatios=[]
try:
	values = [0]*5
	#Returns array of Vap elements for initial scan of IM algorithm
	Vapplied=VoltageRamp(Vmin,Vmax,numV)
	t=np.arange(1,1+len(Vapplied))
	Vin=[]
	P=[]
	Va=[]
	Vmax=[]
	Vav_min=[]
	ExtRatioArr=[]
	print('Writing and reading applied/input voltage values, press Ctrl-C to quit...')
	# Print nice channel column headers.
	line='  ID  |   Date/Time   |    Bias Voltage Applied (V)    |    Voltage Measured (V)    |    Power (nW)    '.format(*range(5))
	print(line)
	if backup:
		txtFile.write(line+"\n")
	line='-' * 120
	print(line)
	SetVoltage(Resource,ChannelNumber,Vapplied[0])
	time.sleep(3)
	if backup:
		txtFile.write(line+"\n")

	#Loops through elements in Vapplied array for initial scan, sets power supply to each element.
	for Vap in Vapplied:
		values[0]=str(i)
		values[1]= str(datetime.now())
		values[2]="{0:.3f}".format(Vap)
		SetVoltage(Resource,ChannelNumber,Vap) #Set channel voltage of power supply
		time.sleep(0.05) #Wait
		vMeas = float(Resource.query("MEAS:VOLT?").rstrip()) #Channel voltage reported by power supply
		Vin.append(vMeas)
		values[3]=str(vMeas)
		p=10**9*powermeter.read
		P.append(p)
		values[4]="{0:.3f}".format(p)
		line=' {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6} '.format(*values)
		print(line)
		if backup:
			 txtFile.write(line+"\n")
		#SQL command to insert data into database
		query="INSERT INTO IM(datetime, DCVap, DCVin, P) values(NOW(), +"+values[2]+","+values[3]+","+values[4]+");"
		cur.execute(query)
		db.commit()
		i+=1
	Vin = np.array(Vin)
	P=np.array(P)
	Pmin = np.amin(P)
	Pmax = np.amax(P)
	DCmaxP=Pmax
	eRatio=-10*np.log10(Pmin/Pmax)
	print("Power Exinction Ratio Lower Bound: ", eRatio) #Max extinction ratio (ER) from initial scan

	#Plots Power vs Applied Voltage from initial scan
	fig, axs = plt.subplots(1,1,num="1")
	PmW=[]
	for pnW in P:
		PmW.append(pnW*10**-6)
	PmW=np.array(PmW)
	axs.plot(Vapplied,PmW, label = "Power Extinction Ratio = "+str(eRatio))
	axs.grid()
	axs.set_xlabel("Applied Voltage (V)")
	axs.set_ylabel(r"Power ($n W$)")


	#Get index corresponding to min of power from init scan
	PminIndex = np.where(P==Pmin)
	PminIndex=PminIndex[0]
	Va_minP=Vapplied[PminIndex[0]] #Find voltage value corresponding to min power
	#Get index corresponding to max of power from init scan
	PmaxIndex = np.where(P==Pmax)
	PmaxIndex=PmaxIndex[0]
	Va_maxP=Vapplied[PmaxIndex[0]] #Find voltage value corresponding to max power
	print("Va for min P: ",Va_minP)
	print("Pmin: ",Pmin)
	print("Va for max P: ",Va_maxP)
	print("Pmax: ",Pmax)

	#Set powersupply voltage to max power
	SetVoltage(Resource,ChannelNumber,Va_minP)
	time.sleep(10) #Wait to settle at the max voltage
	print("Vin after setting Va for min P: ",float(Resource.query("MEAS:VOLT?").rstrip()))
	print("P (nW): ",10**9*powermeter.read)
	starttime=datetime.now()
	curtime=starttime
	line='  ID  |   Date/Time   |    Voltage Applied (V)    |    Voltage Measured (V)    |    Power (nW)    |    Feedback?     '.format(*range(5))
	print(line)
	line='-' * 120
	print(line)
	n=0
	values = [0]*6
	while True: #Periodic fine scan loop
		curtime = datetime.now()
		vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
		#if at least one second has passed, record data:
		if (curtime-starttime) > timedelta(seconds=1):
			starttime=curtime
			values[0]=str(i)
			values[1]=str(datetime.now())
			values[2]="{0:.3f}".format(Va_minP) #Channel set voltage
			VapArr.append(Va_minP)
			values[3] = str(vMeas) #Channel voltage as reported by power supply
			p=10**9 * powermeter.read #Measure power from powermeter
			values[4]="{0:.3f}".format(p)
			Parr.append(p)
			values[5]="yes" #indicates that going to do fine scan on this iteration
			# Print nice channel column headers.
			line=' {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6}  | {5:>6}  '.format(*values)
			print(line)
			if backup:
				txtFile.write(line+"\n")
			#SQL command to insert data into database
			query="INSERT INTO IM(datetime, DCVap, DCVin, P) values(NOW(), +"+values[2]+","+values[3]+","+values[4]+");"
			cur.execute(query)
			db.commit()
			i+=1

		P=[] #Array for power measurements from fine scan
		Vin=[] #Array for channel voltage measurements from fine scan
		#Fine scan voltage array.
		Vapplied = VoltageRamp(vMeas-Vscan/2, vMeas+Vscan/2,40) #See AliceScanFunc.py
		SetVoltage(Resource,ChannelNumber,Vapplied[0]) #See AliceScanFunc.py
		time.sleep(0.1)
		#Loops through elements in fine scan Vapplied array, sets power supply to each element.
		for Vap in Vapplied:
			SetVoltage(Resource,ChannelNumber,Vap)
			vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
			Vin.append(vMeas)
			p=0
			#Gets average of 10 powermeter measurements in rapid succession
			for s in range(10):
				p=10**9*powermeter.read
				p=p+p
			p=p/10
			P.append(p)
		P=np.array(P)
		Vin=np.array(Vin)
		#Get min power from fine scan
		Pmin = np.amin(P)
		#Get index of min power from fine scan
		PminIndex = np.where(P==Pmin)
		PminIndex=PminIndex[0]
		#Get channel voltage corresponding to min power from fine scan
		Va_minP=Vapplied[PminIndex[0]]
		#Set channel voltage to voltage corresponding to min power from fine scan
		SetVoltage(Resource,ChannelNumber,Va_minP)
		#Records voltages every 5 seconds over total of period of "feedbackPause",
		#which is time period before next fine scan
		for k in range(1,int(round(feedbackPause))):
			time.sleep(1)
			curtime = datetime.now()
			vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
			if (curtime-starttime) > timedelta(seconds=5):
				starttime=curtime
				values[0]=str(i)
				values[1]=str(datetime.now())
				values[2]="{0:.3f}".format(Va_minP) #Channel set voltage from most recent fine scan
				VapArr.append(Va_minP)
				values[3] = str(vMeas)
				p=10**9 * powermeter.read #Power measured from power meter
				values[4]="{0:.3f}".format(p)
				Parr.append(p)
				values[5]="nope" #indicates that not doing fine scan on this iteration
				# Print nice channel column headers.
				line=' {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6}  | {5:>6}  '.format(*values)
				print(line)
				#SQL command to insert data into database
				query="INSERT INTO IM(datetime, DCVap, DCVin, P) values(NOW(), +"+values[2]+","+values[3]+","+values[4]+");"
				cur.execute(query)
				db.commit()
				i+=1
except KeyboardInterrupt:
	print("")
	print("Quit")
	Parr = np.array(Parr)
	VapArr = np.array(VapArr)
	Pmin=min(Parr)
	#Get the maximum extinction ratio from the run
	best_eRatio=-10*np.log10(Pmin/DCmaxP)
	eRatios=[]
	t=[]
	i=1
	for p in Parr:
		t.append(i*feedbackPause)
		e = -10*np.log10(p/DCmaxP)
		eRatios.append(e)
		i=i+1
	eRatios=np.array(eRatios)
	ExtRatioArr=np.array(ExtRatioArr)
	t=np.array(t)
	#Plot extinction ratios over times
	fig, axs = plt.subplots(3,1, num=20, sharex=True)
	axs[0].plot(t,ExtRatioArr)
	axs[0].set_ylabel(r"Power Extinction Ratio")
	axs[0].grid()
	axs[1].plot(t,Parr)
	axs[1].set_ylabel(r"Power (nW)")
	axs[1].grid()
	axs[2].plot(t,VapArr)
	axs[2].set_ylabel(r"DC Bias Voltage (V)")
	axs[2].grid()
	axs[2].set_xlabel("Index") #4 seconds
	fig.suptitle(r"Best Power Extinction Ratio: {:.3f}".format(best_eRatio)+"\n"+"Max P: {:.3f} mW".format(DCmaxP*10**-6))
	plt.show() #Shows all figures produced by script
if backup:
	txtFile.close()
plt.show()
db.close()
