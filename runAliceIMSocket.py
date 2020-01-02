#Starter code for remotely controlling powersupply using "socket" package.
#Not functional.


from VapScanFunc import *
import pymysql
import pyvisa as visa
import socket
import time
import math
from ThorlabsPM100 import ThorlabsPM100, USBTMC
import matplotlib.pyplot as plt
import matplotlib as mpl
#Need to allow permission: sudo chown inqnet4:inqnet4 /dev/usbtmc0

mpl.rcParams["savefig.directory"] = os.chdir(os.path.dirname("/home/inqnet4/Desktop/CQNET/Alice"))


db = pymysql.connect(host="<IP ADDRESS>",  #Replace <IP ADDRESS> with the IP of computer with database. Local host if is same computer.
					 user="<USERNAME>", #Replace <USERNAME> with your username
					 passwd="<PASSWORD>",  #Replace <PASSWORD> with your password
					 database="teleportcommission",
					 charset='utf8mb4',
					 #port = 5025,
					 cursorclass=pymysql.cursors.DictCursor) #name of the data

input_buffer = 1024#4096 #Temp buffer for rec data.
exRat = 0

pna = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
pna.connect(("192.168.0.177", 5025))
#
byt="*idn?"+r"\n"
byt=byt.encode('utf-8')
pna.send(byt)#,("192.168.0.177", 5025))
msg=pna.recv(input_buffer)
#data, addr = pna.recvfrom(input_buffer)
msg=msg.decode('utf-8')
#conn, addr = pna.accept()
#id = conn.recv(input_buffer)

inst = USBTMC(device="/dev/usbtmc0")
powermeter = ThorlabsPM100(inst=inst)
#ChannelNumber=2
numV=400
Vmin=0 #in Volts
Vmax=15#in Volts
Vscan = 0.03
feedbackPause = 60  #s
VISAInstance=pyvisa.ResourceManager('@py')
Resource=InitiateResource()



ChannelNumber=2
print("DCBias_ChannelNumber: ", ChannelNumber)



cur = db.cursor()
backup = False
print("Back up to text file: " + str(backup))
if backup:
	txtFile = open("VapVinPIM.txt","w")


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
	values = [0]*6
	Vapplied=VoltageRamp(Vmin,Vmax,numV)
	t=np.arange(1,1+len(Vapplied))
	Vin=[]
	P=[]
	Va=[]
	Vmax=[]
	Vav_min=[]
	ExtRatioArr=[]
	print('Writing and reading applied/input voltage values, press Ctrl-C to quit...')
	line='  ID  |   Date/Time   |    Bias Voltage Applied (V)    |    Voltage Measured (V)    |    Power (nW)    |    ExtRatio     '.format(*range(5))
	print(line)
	if backup:
		txtFile.write(line+"\n")
	line='-' * 120
	print(line)
	#print(Vapplied[0])
	SetVoltage(Resource,ChannelNumber,Vapplied[0])
	time.sleep(3)
	if backup:
		txtFile.write(line+"\n")
	for Vap in Vapplied:
		values[0]=str(i)
		values[1]= str(datetime.now())
		values[2]="{0:.3f}".format(Vap)
		SetVoltage(Resource,ChannelNumber,Vap)
		time.sleep(0.05) #Wait
		vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
		Vin.append(vMeas)
		values[3]=str(vMeas)
		p=10**9*powermeter.read
		P.append(p)
		values[4]="{0:.3f}".format(p)
		pna.send("meas:vmax? chan3" + "\n")
		vmax = pna.recv(input_buffer)
		vmax=float(vmax)
		Vmax.append(vmax)
		pna.send("meas:vav? disp,func1" + "\n")
		vav = pna.recv(input_buffer)
		vav=float(vav)
		Vav_min.append(vav)
		rat=vmax/vav
		exRat = 10 * math.log(rat,10)
		ExtRatioArr.append(exRat)
		values[5]=exRat
		line=' {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6} | {5:>6} '.format(*values)
		print(line)
		if backup:
			 txtFile.write(line+"\n")
		query="INSERT INTO IM(datetime, DCVap, DCVin, P, ExtRatio) values(NOW(), +"+values[2]+","+values[3]+","+values[4]+","+values[5]+");"
		cur.execute(query)
		db.commit()
		i+=1
	Vin = np.array(Vin)
	P=np.array(P)
	Pmin = np.amin(P)
	Pmax = np.amax(P)
	DCmaxP=Pmax
	eRatio=-10*np.log10(Pmin/Pmax)
	print("Power Exinction Ratio Lower Bound: ", eRatio)

	#Initial scan
	fig, axs = plt.subplots(1,1,num="1")
	PmW=[]
	for pnW in P:
		PmW.append(pnW*10**-6)
	PmW=np.array(PmW)
	axs.plot(Vapplied,PmW, label = "Power Extinction Ratio = "+str(eRatio))
	axs.grid()
	axs.set_xlabel("Applied Voltage (V)")
	axs.set_ylabel(r"Power ($n W$)")
	figname="AliceInitScanDec5.png"
	#plt.savefig(figname)


	PminIndex = np.where(P==Pmin)
	PminIndex=PminIndex[0]
	Va_minP=Vapplied[PminIndex[0]]
	PmaxIndex = np.where(P==Pmax)
	PmaxIndex=PmaxIndex[0]
	Va_maxP=Vapplied[PmaxIndex[0]]
	print("Va for min P: ",Va_minP)
	print("Pmin: ",Pmin)
	print("Va for max P: ",Va_maxP)
	print("Pmax: ",Pmax)
	SetVoltage(Resource,ChannelNumber,Va_minP)
	time.sleep(10)
	print("Vin after setting Va for min P: ",float(Resource.query("MEAS:VOLT?").rstrip()))
	print("P (nW): ",10**9*powermeter.read)
	starttime=datetime.now()
	curtime=starttime
	line='  ID  |   Date/Time   |    Voltage Applied (V)    |    Voltage Measured (V)    |    Power (nW)    |    ExtRatio     |    Feedback?     '.format(*range(5))
	print(line)
	line='-' * 120
	print(line)
	n=0
	values = [0]*7
	while True:
		curtime = datetime.now()
		vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
		if (curtime-starttime) > timedelta(seconds=1):
			starttime=curtime
			values[0]=str(i)
			values[1]=str(datetime.now())
			values[2]="{0:.3f}".format(Va_minP)
			VapArr.append(Va_minP)
			values[3] = str(vMeas)
			p=10**9 * powermeter.read
			values[4]="{0:.3f}".format(p)
			Parr.append(p)
			pna.send("meas:vmax? chan3" + "\n")
			vmax = pna.recv(input_buffer)
			vmax=float(vmax)
			Vmax.append(vmax)
			pna.send("meas:vav? disp,func1" + "\n")
			vav = pna.recv(input_buffer)
			vav=float(vav)
			Vav_min.append(vav)
			rat=vmax/vav
			exRat = 10 * math.log(rat,10)
			ExtRatioArr.append(exRat)
			values[5]=exRat
			values[6]="yes"
			line=' {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6}  | {5:>6}  | {6:>6} '.format(*values)
			print(line)
			if backup:
				txtFile.write(line+"\n")
			query="INSERT INTO IM(datetime, DCVap, DCVin, P, ExtRatio) values(NOW(), +"+values[2]+","+values[3]+","+values[4]+","+values[5]+");"
			cur.execute(query)
			db.commit()
			i+=1
		P=[]
		Vin=[]
		Vapplied = VoltageRamp(vMeas-Vscan/2, vMeas+Vscan/2,40)
		SetVoltage(Resource,ChannelNumber,Vapplied[0])
		time.sleep(0.1)
		for Vap in Vapplied:
			SetVoltage(Resource,ChannelNumber,Vap)
			vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
			Vin.append(vMeas)
			p=0
			for s in range(10):
				p=10**9*powermeter.read
				p=p+p
			p=p/10
			P.append(p)
		P=np.array(P)
		Vin=np.array(Vin)
		Pmin = np.amin(P)
		PminIndex = np.where(P==Pmin)
		PminIndex=PminIndex[0]
		Va_minP=Vapplied[PminIndex[0]]
		SetVoltage(Resource,ChannelNumber,Va_minP)
		for k in range(1,int(round(feedbackPause))):
			time.sleep(1)
			curtime = datetime.now()
			vMeas = float(Resource.query("MEAS:VOLT?").rstrip())
			if (curtime-starttime) > timedelta(seconds=5):
				starttime=curtime
				values[0]=str(i)
				values[1]=str(datetime.now())
				values[2]="{0:.3f}".format(Va_minP)
				VapArr.append(Va_minP)
				values[3] = str(vMeas)
				p=10**9 * powermeter.read
				values[4]="{0:.3f}".format(p)
				Parr.append(p)
				pna.send("meas:vmax? chan3" + "\n")
				vmax = pna.recv(input_buffer)
				vmax=float(vmax)
				Vmax.append(vmax)
				pna.send("meas:vav? disp,func1" + "\n")
				vav = pna.recv(input_buffer)
				vav=float(vav)
				Vav_min.append(vav)
				rat=vmax/vav
				exRat = 10 * math.log(rat,10)
				ExtRatioArr.append(exRat)
				values[5]=exRat
				values[6]="nope"
				line=' {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6}  | {5:>6}  | {6:>6} '.format(*values)
				print(line)
				query="INSERT INTO IM(datetime, DCVap, DCVin, P, ExtRatio) values(NOW(), +"+values[2]+","+values[3]+","+values[4]+","+values[5]+");"
				cur.execute(query)
				db.commit()
				i+=1
except KeyboardInterrupt:
	print("")
	print("Quit")
	Parr = np.array(Parr)
	VapArr = np.array(VapArr)
	Pmin=min(Parr)
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
	fig, axs = plt.subplots(4,1, num=20, sharex=True)
	axs[0].plot(t,eRatios)
	axs[0].set_ylabel(r"Power Extinction Ratio")
	axs[0].grid()
	axs[1].plot(t,ExtRatioArr)
	axs[1].set_ylabel(r"Power Extinction Ratio")
	axs[1].grid()
	axs[2].plot(t,Parr)
	axs[2].set_ylabel(r"Power (nW)")
	axs[2].grid()
	axs[3].plot(t,VapArr)
	axs[3].set_ylabel(r"DC Bias Voltage (V)")
	axs[3].grid()
	axs[3].set_xlabel("Index") #4 seconds
	fig.suptitle(r"Best Power Extinction Ratio: {:.3f}".format(best_eRatio)+"\n"+"Max P: {:.3f} mW".format(DCmaxP*10**-6))
	figname="AliceIMFeedbackDec6.png"
	#plt.savefig(figname)
	plt.show()
	#DisableLVOutput(Resource)
if backup:
	txtFile.close()
plt.show()
db.close()
