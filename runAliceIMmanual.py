#NOTE: currently just sets channel voltage to same voltage continuously

#This script maximizes Alice's IM extinction ratio by minimizing the IM's output
#optical power and prevents drifting.
# Instead of doing an initial scan (like in runAliceIM.py), this starts doing
# fine scans/feedback with the current channel/tuning voltage setting. The user
# is expected to have manually found the tuning voltage corresponding to the
# min power.It periodically does fine range scans to find, and keep the IM at min power.
#Alice has a 21 dB IM with one tuning voltage pin.
#Requirements: Python3, AliceScanFunc.py in same directory, packages listed below
# and in AliceScanFunc

from AliceScanFunc import *
import pymysql
from ThorlabsPM100 import ThorlabsPM100, USBTMC
import matplotlib as mpl

#Sets directory for saving figures produced by this script
mpl.rcParams["savefig.directory"] = os.chdir(os.path.dirname("/home/inqnet4/Desktop/CQNET/Alice"))


#Connect to mysql database
db = pymysql.connect(host = "192.168.0.125",  #IP of computer with database. Local host if is same computer.
					user ="INQNET4", # username
					password="Teleport1536!", # your password
					database="teleportcommission", #name of database
					charset='utf8mb4',
					cursorclass=pymysql.cursors.DictCursor) #name of the data


#Connect to powermeter
inst = USBTMC(device="/dev/usbtmc0")
powermeter = ThorlabsPM100(inst=inst)

#Channel that DC tuning pin of IM is connected to
DCBias_ChannelNumber=2
print("DCBias_ChannelNumber: ", DCBias_ChannelNumber)
DCmaxP=98*10**3 #nW
#DCminP = 317 nW
#Vmin=0 #in Volts
#Vmax=22#in Volts
#Vscan = 0.01


#Connect to powersupply
VISAInstance=pyvisa.ResourceManager('@py')
Resource=InitiateResource() #See AliceScanFunc.py

#Create cursor to select data from mysql.
cur = db.cursor()

#Mysql commands to get the index of the last entry of IM table
query = "SELECT max(id) from IM"
cur.execute(query)
result = cur.fetchall()
resultDict = result[0]
maxid=resultDict["max(id)"]
if maxid is None:
	maxid=0
i = maxid +1

valuesDC = [0]*5
values = []
try:
	SetChannel(Resource,DCBias_ChannelNumber) #See AliceScanFunc.py
	cur = db.cursor()
	query = "SELECT max(id) from IM"
	cur.execute(query)
	result = cur.fetchall()
	resultDict = result[0]
	maxid=resultDict["max(id)"]
	if maxid is None:
		maxid=0
	i = maxid +1

	#Get current voltage of channel
	Va_minP = float(Resource.query("MEAS:VOLT?").rstrip())
	print(Va_minP)
	print("Vin after setting to DCBiasGuessMin ",float(Resource.query("MEAS:VOLT?").rstrip()))
	print("P (nW): ",10**9*powermeter.read)
	starttime=datetime.now()
	curtime=starttime

	#Vapplied=VoltageStairs(1.275,1.245,8,1)#5*60)

	P=[]
	Vin=[]
	print('Writing and reading applied/input voltage values, press Ctrl-C to quit...')
	# Print nice channel column headers.
	line='  ID  |  Date/Time  |   VSet DCBias (V)  |  Vin DCBias (V)  |  P (nW)  '.format(*range(7))
	print(line)
	line='-' * 100
	print(line)
	while(True):
		time.sleep(1) #Wait 1 second
		SetChannel(Resource,DCBias_ChannelNumber)
		vMeas = float(Resource.query("MEAS:VOLT?").rstrip()) #Get current channel voltage
		valuesDC[0]=str(i)
		valuesDC[1]=str(datetime.now())
		valuesDC[2]="{0:.3f}".format(Va_minP)
		valuesDC[3] = str(vMeas)
		Vin.append(vMeas)
		p=10**9 * powermeter.read #Measure power from powermeter
		P.append(p)
		valuesDC[4]="{0:.3f}".format(p)
		#SQL command to insert data into database
		query="INSERT INTO IM(datetime, DCVap, DCVin, P) values(NOW(), +"+valuesDC[2]+","+valuesDC[3]+","+valuesDC[4]+");"
		values = [valuesDC[0], valuesDC[1], valuesDC[2],valuesDC[3],valuesDC[4]]
		line=' {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6} '.format(*values)
		print(line)
		cur.execute(query)
		db.commit()
		i+=1
except KeyboardInterrupt:
	print("")
	print("Quit")
	P=np.array(P)
	Pmin = min(P)
	#Get the maximum extinction ratio from the run
	best_eRatio=-10*np.log10(Pmin/DCmaxP)
	eRatios=[]
	for p in P:
	    e = -10*np.log10(p/DCmaxP)
	    eRatios.append(e)
	eRatios=np.array(eRatios)
	fig, axs = plt.subplots(2,1, num=20, sharex=True)
	#Plot extinction ratios over times
	axs[0].plot(eRatios)
	axs[0].set_ylabel(r"Extinction Ratio")
	axs[0].grid()
	axs[1].plot(P)
	axs[1].set_ylabel(r"Power (nW)")
	axs[1].grid()
	axs[1].set_xlabel("Time (s)")
	fig.suptitle(r"Best Extinction Ratio: {:.3f}".format(best_eRatio)+"\n"+"Manual Max P: {:.3f} mW".format(DCmaxP*10**-6))
	plt.show() #Shows all figures produced by script

	Resource.write("SYSTEM:LOCAL") #Sets powersupply to manual control
	print("Set manual access")

db.close()
