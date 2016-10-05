#!/usr/bin/env python
import os, re, pprint, subprocess, sys, datetime

usage = "\n   usage:  makeCatalog.py  <mitcfg> <version> <dataset> \n"

# global
alwaysDeleteAgeHours = 6

#===================================================================================================
#  H E L P E R S
#===================================================================================================
def catalogFile(file):
    # perfrom cataloging operation on one file (return the entry)

    cmd = 'catalogFile.sh ' + file
    list = cmd.split(" ")
    p = subprocess.Popen(list,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (out, err) = p.communicate()
    rc = p.returncode

    entry = ''
    lines = out.split("\n")
    for line in lines:
        if 'XX-CATALOG-XX 0000' in line:
            entry = line.replace('XX-CATALOG-XX 0000 ','')

    return entry

def numberOfEventsInEntry(entry):
    # extract the number of events in a given catalog entry

    f = entry.split(" ")
    nEvents = -1
    if len(f)>1: 
        nEvents = int(f[1])

    return nEvents

def getId(file):
    # extract the unique file id

    f = file.split('/')
    fileId = (f.pop()).replace('.root','')
    fileId = fileId.replace('_tmp','')         # maybe this is a temporary file

    return fileId
    

def loadEnv():
    # make sure to setup the environment
    rc = 0
    base = os.environ.get('FIBS_BASE')
    if os.path.exists(base + '/config/makeCatalog.bash'):
        cmd = 'bash -c ' + base + '/config/makeCatalog.bash'
        list = cmd.split(" ")
        p = subprocess.Popen(list,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (out, err) = p.communicate()
        rc = p.returncode
        for line in out.split("\n"):
            (key, _, value) = line.partition("=")
            os.environ[key] = value
        print ' INFO - special environment for makeCatalog.py was loaded.'
    else:
        print ' INFO - special environment needed.'

    return rc

def loadCatalog(catalog,mitcfg,version,dataset):
    # load the unique file ids of the existing catalog for existence checks (careful)

    # first make sure the catalog is compact
    cmd = "extractCatalog.py  --dataset=%s --mitCfg=%s --version=%s --compact > /dev/null"\
        %(dataset,mitcfg,version)
    os.system(cmd)

    # now read the raw information
    catalogFileIds = []
    if os.path.exists(catalog + '/' + dataset + '/RawFiles.00'):
        with open(catalog + '/' + dataset + '/RawFiles.00','r') as fH:
            for line in fH:
                f = line[:-1].split(" ")
                if len(f) > 0:
                    fileId = getId(f[0])
                    catalogFileIds.append(fileId)
    else:
        if not os.path.exists(catalog + '/' + dataset):
            os.makedirs(catalog + '/' + dataset)
        os.system('touch ' + catalog + '/' + dataset + '/RawFiles.00')
    
    return catalogFileIds
    
def loadLfns(dataset):
    # load the unique file ids of the official dataset and the number of events

    # now read the raw information
    lfnFileIds = {}
    if os.path.exists('/home/cmsprod/cms/jobs/lfns/%s.lfns'%(dataset)):
        with open('/home/cmsprod/cms/jobs/lfns/%s.lfns'%(dataset),'r') as fH:
            for line in fH:
                f = line[:-1].split(" ")
                if len(f) > 2:
                    fileId = getId(f[1])
                    lfnFileIds[fileId] = int(f[2])
    else:
        print ' ERROR -- could not find the official lfn information.'
        
    return lfnFileIds
    
def loadFilesToCatalog(hadoop,dataset):
    # load the files from an existing temporary directory for cataloging and checks

    files = []
    ages = []

    cmd = 't2tools.py --action ls --options=-l --source ' + hadoop + '/' + dataset + '/crab_0*'
    list = cmd.split(" ")
    p = subprocess.Popen(list,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (out, err) = p.communicate()
    rc = p.returncode
    
    lines = out.split("\n")
    for line in lines:        
        if not 'root' in line or 'miniaod' in line:
            continue
        f = line.split(" ") 

        if len(f) > 7:
            thisFile = f.pop()
            thisTime = datetime.datetime.strptime(f[5] + " " + f[6], "%Y-%m-%d %H:%M")
            now = datetime.datetime.now()
            delta = now-thisTime
            ageSeconds = delta.days * 86400 + delta.seconds
            if ageSeconds > 1 * 3600:
                files.append(thisFile)
                ages.append(ageSeconds)

    onlyTmp = os.getenv('MAKECATALOG_TMP_ONLY','')

    if onlyTmp == '':
        cmd = 't2tools.py --action ls --source ' + hadoop + '/' + dataset
        list = cmd.split(" ")
        p = subprocess.Popen(list,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (out, err) = p.communicate()
        rc = p.returncode
        
        lines = out.split("\n")
        for line in lines:
            if not 'root' in line or 'miniaod' in line:
                continue
            f = line.split(" ") 
            if len(f) > 1:
                files.append(f[1])
                ages.append(-1)

    return (files, ages)

def regenerateCatalog(catalog,mitcfg,version,dataset):
    # the raw file is now updated and will be used to regenerate the catalog

    cmd = "extractCatalog.py  --dataset=%s --mitCfg=%s --version=%s --compact > /dev/null"\
        %(dataset,mitcfg,version)
    os.system(cmd)
    cmd = "generateCatalog.py --rawFile=%s/%s --nFilesPerSet=20 > /dev/null"%(catalog,dataset)
    os.system(cmd)

    return

def updateXrootdName(fileName):
    # adjust entry for the file moving

    newFileName = fileName.replace('root://xrootd.cmsaf.mit.edu/','/cms')
    return newFileName

def updateEntry(entry):
    # adjust entry for the file moving

    newEntry = ''
    if entry != '':
        newEntry = entry.replace('_tmp.root','.root')
        if '/crab_0' in newEntry:
            f = newEntry.split('/')
            newEntry = "/".join(f[:-2]) + '/' + f[-1]

    return newEntry

#===================================================================================================
#  M A I N
#===================================================================================================
# make sure command line is complete
if len(sys.argv) < 4:
    print " ERROR -- " + usage
    sys.exit(1)

# make sure the environment is what we want
loadEnv()

# command line variables
mitcfg = sys.argv[1]
version = sys.argv[2]
dataset = sys.argv[3]
option = ""
if len(sys.argv) > 4:
    option = sys.argv[4]
print " INFO - makeCatalog %s %s %s %s"%(mitcfg,version,dataset,option)     

# derived vaiables
book = mitcfg + '/' + version
catalog = "/home/cmsprod/catalog/t2mit/" +book
hadoop = "/cms/store/user/paus/" + book

# find the list of files to consider
catalogFileIds = loadCatalog(catalog,mitcfg,version,dataset)
# find the number of events we should find for each fileid
lfnFileIds =  loadLfns(dataset)

(files, ages) = loadFilesToCatalog(hadoop,dataset)

# loop over the files
nFiles = len(files)
i = 0
entries = []
for file,age in zip(files,ages):
    i += 1
    print "   -- next file: %s (%d of %d -- age[hrs]: %.1f)"%(file,i,nFiles,age/3600.)

    fileId = getId(file)
    if fileId not in lfnFileIds:
        print ' ERROR -- found Id that does not exist as lfn: %s'%(fileId)
        sys.exit(0)

    oldFile = updateXrootdName(file)

    lRemove = False

    if fileId in catalogFileIds:
        print "     INFO - This file is already cataloged."
        if '/crab_0' in file:
            catalogedFile = file.replace('_tmp','')
            catalogedFile = re.sub('crab_.*/','',catalogedFile)
            print ' FAKE REMOVE: ' + file
            print ' FAKE KEEP: ' + catalogedFile
            lRemove = True
            #if os.path.exists(catalogedFile):
            #    cmd = "t2tools.py --action rm --source " + file
            #    print ' REMOVE: ' + cmd
            #    print ' KEEP: ' + catalogedFile
            #    #os.system(cmd)
        else:
          continue
            
    # doing the cataloging here
    entry = catalogFile(file)
    newEntry = updateEntry(entry)
    nEvents = numberOfEventsInEntry(newEntry)
    if newEntry == '':
        cmd = "t2tools.py --action rm --source " + oldFile
        print "     ERROR - File seems corrupted. Skip? " + cmd
        if option == 'remove' or age/3600. > alwaysDeleteAgeHours:
            print ' REMOVE: '+ cmd
            os.system(cmd)
        continue

    if nEvents != lfnFileIds[fileId]:
        print ' ERROR -- wrong number of entries:  %d != %d  %s'%(nEvents,lfnFileIds[fileId],fileId)
    else:
        print ' INFO -- found matching number of events: %d'%(nEvents)


    entries.append(newEntry)

    newFile = updateEntry(oldFile)
    if newFile != oldFile:
        cmd = "t2tools.py --action mv --source " +  oldFile + " --target " + newFile + " >/dev/null"
        print ' MOVE: '+ cmd
        os.system(cmd)
        if lRemove:
            cmd = "t2tools.py --action rm --source " +  oldFile + " >/dev/null"
            print ' REMOVE REMAINDERS: '+ cmd
            os.system(cmd)

    with open(catalog + '/' + dataset + '/RawFiles.00','a') as fH:
         fH.write(newEntry + '\n')

regenerateCatalog(catalog,mitcfg,version,dataset)
