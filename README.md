# FiBS - A Light Weight Fi(le) B(atch) S(ystem)

FiBS is very simple batch system which uses a locking mechanism as batch manager and engines that freely request a lock to pull there work of a list which is stored in a file. The task the batch manager executes has a configuration file and an initialization file and will be excuted using the entries in the provided list.

This system is extremely simple but of course has many limitations. It is ideal to execute a large number of parallel tasks that do not require a lot of resources and can run in parallel on machines that are busy with more heavy computing. Transfering files is an ideal task for FiBS.

## Prerequisits

Install pdsh as root

    yum install -y pdsh

## Installation

To download the software use git clone:

    git clone https://github.com/cpausmit/FiBS

## Running a simple task: fake

Make sure to execute install.sh so setup.sh will be made

    ./Fibs/install.sh

Edit the setup.sh file to your needs. and make sure to source it so the environment is set. You will have to add this to your .bashrc file so that FiBS is always setup when login in. 

    emacs -nw ./FiBS/setup.sh
    source    ./FiBS/setup.sh
    emacs -nw ~/.bashrc


Make directories named $FIBS_WORK and $FIBS_LOGS which are defined in the setup.sh script:

    mkdir -p $FIBS_WORK $FIBS_LOGS

Make an executable task, and a configure executable. In the task write what you want to do with the task, and with the configure executable for the task write a task name (it should be the same as the task executable name) make a list for the task to run, make the nuber of entries that the task completes at a time, write a error code, then write a list of workers to execute the task, and then assign the number of processes the workers take in. This is an example of the configurement of a task named fake:
 
    [general]
    task = fake.py
    list = fake.list
    nentries = 2

    [io]
    outerr = fake

    [workers]
    list = submit00.mit.edu submit01.mit.edu
    nprocesses = 2

Once everything is written run one test task to see whther it works:

     ./FiBS/task/fake.py fake-argument

Now prepare a list of tasks inside the FIBS_WORK name it fake.list, and inside it could look like this:

    argument-1
    argument-2
    argument-3
    argument-4

Now start the batch system to process those tasks:

    fibsService.py start fake

Check the status with:

    fibeService.py status fake
    
## Trouble Shooting

If at any point some of the commands do not work check the environment, and make sure the setup was in the .bashrc file and where sourced

Make sure that you do not need to type in any password to access any of the workers

You can also stop the batch system. It is recommened to do so once all work is done because it keeps running until you tell it to stop.

## Sub directories

### ./bin

A sub-directory full of executables to preform services relating to FiBS

### ./config

A sub-directory with executabels to make, upload, and check files

### ./python

A sub-directory with code for running python scripts for tasks

### ./tasks

