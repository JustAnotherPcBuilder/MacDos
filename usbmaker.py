import subprocess
import zipfile
import os
import shutil




formatting = False
curdir = os.getcwd() + '\\'

#-----------------------------------------------
#1. Check usb devices and convert to dictionary
#-----------------------------------------------

diskcommand = 'wmic logicaldisk get freespace, name, size, volumename'
logicaldisk = subprocess.check_output(diskcommand, shell = True).decode().strip()
volumes = logicaldisk.replace('\r\r\n','\n').splitlines()
volumes.pop(0)#removes unnecessary labels from cmd output

#converts disk size from bytes to gigabytes and adds a label
def conv(numstr):
	return str(round((int(numstr) / 1000000000) , 2)) + " GB"

drives = []	
for volume in volumes:
	vlist = volume.split()
	vdict = dict(letter=vlist[1][0], name=vlist[3], size=conv(vlist[2]), freespace=conv(vlist[0]))
	drives.append(vdict)

if not drives:
	input('???...No Drives found...Press Enter to exit.')
	quit()
print(len(drives), "drive(s) found:")
print('{0:<15}{1:<15}{2:<15}{3:<15}'.format('Letter:', 'Name:', 'Size:', 'Free Space:'))
for drive in drives:
	#print('{0}\t\t{1}\t\t{2}\t\t{3}'.format((value for value in drive.values())))
	print('{0:<15}{1:<15}{2:<15}{3:<15}'.format(*[value for value in drive.values()]))



#--------------------------------  
#2. ask for the volume to format
#--------------------------------  

count, valid = 3, False

while not valid:
	dletter = input("\nEnter your USB Drive LETTER (exit to end):").upper()
	if dletter == 'EXIT':
		quit()
	for drive in drives:
		if dletter == drive.get("letter"):
			valid = True
			mydrive = drive
			break
	if not valid:
		if count != 0:
			print("ERROR! Invalid input!", count, "tries remaining.")
		else:
			input("Program Terminated, press Enter to exit.")
			quit()
		count -=1

print('Drive', mydrive.get('letter'), 'selected\n')




#---------------------------------------------------------------
#3. Download OpenCore and extract macrecovery.py into downloads
#---------------------------------------------------------------

default = '0.6.5'
ver = default
oclink = 'https://github.com/acidanthera/OpenCorePkg/releases/latest'
newlink = subprocess.check_output('curl -s ' + oclink, shell = True).decode()

try: 
	cver = newlink.split('tag/')[1][:5]
	if float(cver[2:]) > float(default[2:]):
		ver = cver
except:
	print('An error occurred when checking current OC version. Using default version: 0.6.5')

print('Downloading Opencore version', ver, '...')
os.makedirs('./downloads', exist_ok=True)
ocpath = './downloads/oc.zip'
opencorelink = 'https://github.com/acidanthera/OpenCorePkg/releases/download/' + ver + '/OpenCore-' + ver + '-RELEASE.zip' 
dlcommand = 'curl -o ' + ocpath + ' -L ' + opencorelink

subprocess.check_output(dlcommand, shell = True)
print('Extracting files...')


oczipfile = zipfile.ZipFile(ocpath)
oczipinfo = oczipfile.infolist()

for zipinfo in oczipinfo:
	if zipinfo.filename.endswith('.py'):
		zipsplit = zipinfo.filename.split('/')
		last = len(zipsplit) - 1
		zipinfo.filename = 'downloads/' + zipsplit[last]
		oczipfile.extract(zipinfo)

print('macrecovery extracted successfully...')




#--------------------------------------
# 4. Select macOS version and download
#--------------------------------------

f = open('macOSversion.txt', 'r')
oslist = ''
for line in f:
	if '#' in line:
		oslist += line.replace('#', '')

while True:
	print('Supported MacOS Versions:\n')
	print(oslist)
	inputver = input('Select MacOS version number (i.e. 10.15):')
	if inputver.strip() != '11':
		if '.' in inputver:
			try: 
				n1 , n2 = inputver.split('.')
				if int(n1) != 10:
					raise ValueError
				if int(n2) < 7 or int(n2) > 15:
					raise ValueError
			except ValueError:
				print('ERROR: Invalid input, try again...\n\n')
			else:
				break
	else:
		break

f.seek(0)
recoverycmd = ''
startcommand = False
for line in f: 
	if startcommand:
		if '#' in line:
			break
		else:
			recoverycmd += line
	if inputver in line: 
		startcommand = True
f.close()
print('downloading MacOS', inputver, 'please wait...')
recoverycmd = recoverycmd.replace('macrecovery.py', 'downloads/macrecovery.py')

subprocess.check_output(recoverycmd, shell = True)
print('recovery files downloaded successfully!')




#---------------------------------------------
# 5. Format Drive and Transfer Recovery Files
#---------------------------------------------

shrinkdrive = False
if float(mydrive.get('size').replace('GB','')) > 34:
	shrinkdrive = True

with open('disktemplate.txt', 'r') as template:
	lines = template.readlines()

for i, line in enumerate(lines):
	if line.startswith('select'):
		lines[i] = lines[i].replace('\n', ' ' + mydrive.get('letter') + '\n')
	if shrinkdrive:
		if line.startswith('create'):
			lines[i] = lines[i].replace('\n', ' SIZE=32000\n')
	if line.startswith('assign'):
		lines[i] += mydrive.get('letter')

with open('diskpart.txt', 'w') as outfile:
	outfile.write(''.join(lines))

dslocation = ' diskpart.txt'
diskpartcmd = 'diskpart /s' + dslocation

if formatting:
	subprocess.check_output(diskpartcmd, shell = True)

print('Moving recovery files to drive, please wait...')
outdir = mydrive.get('letter') + ':\\com.apple.recovery.boot\\'
os.makedirs(outdir, exist_ok=True)
dirlist = os.listdir()
print('Files in current directory:\n','\n'.join(dirlist))
for file in dirlist:
	if file.endswith('.chunklist') or file.endswith('.dmg'):
		shutil.move(curdir + file, outdir)
print('Finished!')