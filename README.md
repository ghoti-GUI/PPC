# Simulation of energy markets
## objective
We have simulated a model with multiple households and an energy market in python. Each household has a certain capacity to produce and consume energy, and will buy energy from the market when it runs low. The behaviour of each household with respect to excess energy varies, with some only selling energy to the market, others only giving it away to other households, and others depending on circumstances. The market shows the price of energy for the month, which is determined by a number of factors (energy sold in the previous month, weather in the month, external events, etc.).

## Method of realization:
We create and simulate multiple households using thread pools, simulate the market using processes, simulate weather and external events using shared memory and signal, implement energy exchange between multiple households using message queue, and implement energy transactions between each household and the market using sockets, multithreading and thread locks.
