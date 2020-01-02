from VapScanFunc import *
import pymysql
from ThorlabsPM100 import ThorlabsPM100, USBTMC
import matplotlib as mpl

mpl.rcParams["savefig.directory"] = os.chdir(os.path.dirname("/home/inqnet4/Desktop/CQNET/Alice"))

db = pymysql.connect(host = "192.168.0.125", #Wired IPv4 Address
					user ="INQNET4", # this user only has access to CP
					password="Teleport1536!", # your password
					database="teleportcommission",
					charset='utf8mb4',
					#port = 5025,
					cursorclass=pymysql.cursors.DictCursor) #name of the data

inst = USBTMC(device="/dev/usbtmc0")
powermeter = ThorlabsPM100(inst=inst)

#DC Bias of IM
DCBias_ChannelNumber=2
print("DCBias_ChannelNumber: ", DCBias_ChannelNumber)
DCmaxP=98*10**3 #nW
#DCminP = 317 nW
#Vmin=0 #in Volts
#Vmax=22#in Volts
#Vscan = 0.01



VISAInstance=pyvisa.ResourceManager('@py')
Resource=InitiateResource()


cur = db.cursor()
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
	SetChannel(Resource,DCBias_ChannelNumber)
	cur = db.cursor()
	query = "SELECT max(id) from IM"
	cur.execute(query)
	result = cur.fetchall()
	resultDict = result[0]
	maxid=resultDict["max(id)"]
	if maxid is None:
		maxid=0
	i = maxid +1

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
	line='  ID  |  Date/Time  |   VSet DCBias (V)  |  Vin DCBias (V)  |  P (nW)  '.format(*range(7))
	print(line)
	line='-' * 100
	print(line)
	while(True):
		time.sleep(1) #Wait 1 second
		SetChannel(Resource,DCBias_ChannelNumber)
		vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
		valuesDC[0]=str(i)
		valuesDC[1]=str(datetime.now())
		valuesDC[2]="{0:.3f}".format(Va_minP)
		valuesDC[3] = str(vMeas)
		Vin.append(vMeas)
		p=10**9 * powermeter.read
		P.append(p)
		valuesDC[4]="{0:.3f}".format(p)
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
	#Pmax = max(P)
	Pmin = min(P)
	best_eRatio=-10*np.log10(Pmin/DCmaxP)
	eRatios=[]
	for p in P:
	    e = -10*np.log10(p/DCmaxP)
	    eRatios.append(e)
	eRatios=np.array(eRatios)
	fig, axs = plt.subplots(2,1, num=20, sharex=True)
	axs[0].plot(eRatios)
	axs[0].set_ylabel(r"Extinction Ratio")
	axs[0].grid()
	axs[1].plot(P)
	axs[1].set_ylabel(r"Power (nW)")
	axs[1].grid()
	axs[1].set_xlabel("Time (s)")
	fig.suptitle(r"Best Extinction Ratio: {:.3f}".format(best_eRatio)+"\n"+"Manual Max P: {:.3f} mW".format(DCmaxP*10**-6))
	figname="AliceIMManualDec5.png"
	plt.savefig(figname)
	plt.show()

	Resource.write("SYSTEM:LOCAL")
	print("Set manual access")

db.close()
