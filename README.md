# Multi-tier cache simulator for NDN
Implemented a multi-tier cache simulator in python with: ARC, LRU, LFU and Random policies.

This simulator is based on Simpy. All the requirements for this project are mentioned in 'requirements.txt'.

The simulation needs to run: 
#### 1. A trace:
You can either create it synthetically by the simulator using several parameters (number of unique items, alpha of the distribution Zipf, lambda of the poisson distribution, etc.). The file is in 'traces/trace_creator.py'.
Or you can download and use your own trace by creating your own trace parser class. 
#### 2. Each tier description:
Also taking several parameters (name, size, read and write throughput, etc.). The file 'forwarder_structures.py' has the Tier class.

#### Once done you can run the 'main'.
