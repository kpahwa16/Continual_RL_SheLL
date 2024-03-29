
To run the pipeline, use run_one_agent.py.

run_one_agent.py supports two modes: 1). training 1 agent to learn 10 taska without sharing and 2). training 5 agents to collaboratively learn 10 tasks with sharing

Note that to running N-agent system, it is recommended the time between kicking off two consecutive agent processes on two devices should not be more than 5 seconds.
If one needs to customize the time interval between running every two agents, adjust duration arguments in wait_execution() in lines 381-482 accordingly.

######################### Locally on Xavier #########################
To run single-agent training on Xavier, one needs two step
1. kick off Atari remote server with a specified port number. Open one server for each agent. Therefore, in step 2, you should run 5 processes of below commands for the 5 agents you spin up. 
    python3 gym_server_multithread_0303.py  PORT_NUMBER (e.g. 4101)
    
    E.g.
    Agent 1: python3 gym_server_multithread_0303.py 5101
    Agent 2: python3 gym_server_multithread_0303.py 5102
    Agent 3: python3 gym_server_multithread_0303.py 5103
    Agent 4: python3 gym_server_multithread_0303.py 5104
    Agent 5: python3 gym_server_multithread_0303.py 5105
    

2. create a folder (for saving experimental results of this run) and kick off run_one_agent.py inside:
    Syntax: python3  PATH_TO_REPO/run_one_agent.py --send_first --open_atari_server --atari_server_port ATARI_PORT --agent_id AGENT_ID --frames 1000 --use_membuf --membuf_parent_savedir task_sim --batch_size 128
    
    Example: python3  ../CANAL_0316/run_one_agent.py --send_first --open_atari_server --atari_server_port 6000 --agent_id 1 --frames 1000 --use_membuf --membuf_parent_savedir task_sim --batch_size 128
    

Running 5-agent training requires on Xavier one few more steps
1. kick off Atari remote server with a specified port number: 
    python3 gym_server_multithread_0303.py  PORT_NUMBER (e.g. 4101)

2. create a folder for every agent. But note that agents must be run in the order of first agent to the fifth agent due to communication topology.
    Syntax: python3  PATH_TO_REPO/run_one_agent.py --send_XXX --share_info --open_atari_server --atari_server_port ATARI_PORT --agent_id AGENT_ID --frames 1000 --use_membuf --membuf_loadpath where --membuf_parent_savedir task_sim --membuf_savedir foo --simnet_weight_dir simnet --batch_size 128
    
    Example: 
        python3  ../CANAL_0316/run_one_agent.py --send_first --share_info --open_atari_server --atari_server_port 5101 --agent_id 1 --frames 1000 --use_membuf --membuf_loadpath where --membuf_parent_savedir task_sim --membuf_savedir foo --simnet_weight_dir simnet --batch_size 128
        python3  ../CANAL_0316/run_one_agent.py --send_second --share_info --open_atari_server --atari_server_port 5102 --agent_id 2 --frames 1000 --use_membuf --membuf_loadpath where --membuf_parent_savedir task_sim --membuf_savedir foo --simnet_weight_dir simnet --batch_size 128
        python3  ../CANAL_0316/run_one_agent.py --send_third --share_info --open_atari_server --atari_server_port 5103 --agent_id 3 --frames 1000 --use_membuf --membuf_loadpath where --membuf_parent_savedir task_sim --membuf_savedir foo --simnet_weight_dir simnet --batch_size 128
        python3  ../CANAL_0316/run_one_agent.py --send_fourth --share_info --open_atari_server --atari_server_port 5104 --agent_id 4 --frames 1000 --use_membuf --membuf_loadpath where --membuf_parent_savedir task_sim --membuf_savedir foo --simnet_weight_dir simnet --batch_size 128
        python3  ../CANAL_0316/run_one_agent.py --send_fifth --share_info --open_atari_server --atari_server_port 5105 --agent_id 5 --frames 1000 --use_membuf --membuf_loadpath where --membuf_parent_savedir task_sim --membuf_savedir foo --simnet_weight_dir simnet --batch_size 128




######################### Distributed Nano+Xavier #########################
To run CANAL pipeline on Nano, one needs to make the following modifications on CANAL pipeline:
1. Refer to the latest commit as of May 6, 2022. A new argument, --atari_server_hostname, is added to customize IP address of the device that runs Atari servers.
2. On run_one_agent.py, set config.use_cuda = False (line 282). The latest repo update has already so. The reason is the computational capability of GPU on Nanos is meager. Setting the option to True usually leads to collapse.
3. Use IP of each deployed Nano device by adding arguments of "--host_[one-five]" when kicking off training.
4. Specify IP of device that runs Atari server using the argument --atari_server_hostname



Step 1. On a device (preferably Xavier), kick off Atari remote server with a specified port number. Open one server for each agent 
    Syntax: python3 PATH_TO_REPO/gym_server_multithread_0303.py  PORT_NUMBER (e.g. 3000)
    
    Example:
    Agent 1: python3 PATH_TO_REPO/gym_server_multithread_0303.py 3000
    Agent 2: python3 PATH_TO_REPO/gym_server_multithread_0303.py 3001
    Agent 3: python3 PATH_TO_REPO/gym_server_multithread_0303.py 3002
    Agent 4: python3 PATH_TO_REPO/gym_server_multithread_0303.py 3003
    Agent 5: python3 PATH_TO_REPO/gym_server_multithread_0303.py 3004
    

Step 2. Create a folder (for saving experimental results of this run) and kick off run_one_agent.py inside:

Case 1: single-agent training
    Syntax: python3 PATH_TO_REPO/run_one_agent.py --send_[first-fifth] --open_atari_server --atari_server_hostname ATARI_SERVER_HOSTNAME --atari_server_port ATARI_PORT --agent_id AGENT_ID --frames 1000 --use_membuf --membuf_parent_savedir task_sim --batch_size 128
    
    Example: assuming the IP address of Atari server is 10.161.159.142:
    python3  PATH_TO_REPO/run_one_agent.py --send_first --open_atari_server --atari_server_port 3000 --atari_server_hostname 10.161.159.142 --agent_id 1 --frames 1000 --use_membuf --membuf_parent_savedir task_sim --batch_size 128
    
    
Case 1: 5-agent training
    1. Assume Atari server is run at: 10.161.159.142 

    Syntax for Agent X: python3 PATH_TO_REPO/run_one_agent.py --send_[first-fifth] --open_atari_server --atari_server_hostname ATARI_SERVER_HOSTNAME --atari_server_port ATARI_PORT --agent_id AGENT_ID --frames 1000 --use_membuf --membuf_parent_savedir task_sim --batch_size 128 --host_one HOST_ONE_IP --host_two HOST_TWO_IP --host_three HOST_THREE_IP --host_four HOST_FOUR_IP --host_five HOST_FIVE_IP --port_one_two PORT_ONE_TWO --port_one_three PORT_TWO_THREE --port_one_four PORT_ONE_FOUR --port_one_five PORT_ONE_FIVE --port_two_three PORT_TWO_THREE --port_two_four PORT_TWO_FOUR --port_two_five PORT_TWO_FIVE --port_three_four PORT_THREE_FOUR --port_three_five PORT_THREE_FIVE --port_four_five PORT_FOUR_FIVE

    Example:
    Agent 1: 
    python3  PATH_TO_REPO/run_one_agent.py --send_first --share_info --open_atari_server --atari_server_port 3000 --atari_server_hostname 10.161.159.142 --agent_id 1 --frames 1000 --use_membuf --membuf_loadpath where --membuf_parent_savedir task_sim --membuf_savedir foo --simnet_weight_dir simnet --batch_size 128 --host_one 10.161.159.142 --host_two 10.161.159.201 --host_three 10.161.159.131 --host_four 10.161.159.130 --host_five 10.161.159.148 --port_one_two 5000 --port_one_three 5001 --port_one_four 5002 --port_one_five 5003 --port_two_three 5004 --port_two_four 5005 --port_two_five 5006 --port_three_four 5007 --port_three_five 5008 --port_four_five 5009

    Agent 2:
    python3  PATH_TO_REPO/run_one_agent.py --send_second --share_info --open_atari_server --atari_server_port 3001 --atari_server_hostname 10.161.159.142 --agent_id 1 --frames 1000 --use_membuf --membuf_loadpath where --membuf_parent_savedir task_sim --membuf_savedir foo --simnet_weight_dir simnet --batch_size 128 --host_one 10.161.159.142 --host_two 10.161.159.201 --host_three 10.161.159.131 --host_four 10.161.159.130 --host_five 10.161.159.148 --port_one_two 5000 --port_one_three 5001 --port_one_four 5002 --port_one_five 5003 --port_two_three 5004 --port_two_four 5005 --port_two_five 5006 --port_three_four 5007 --port_three_five 5008 --port_four_five 5009

    Agent 3:
    python3  PATH_TO_REPO/run_one_agent.py --send_third --share_info --open_atari_server --atari_server_port 3002 --atari_server_hostname 10.161.159.142 --agent_id 1 --frames 1000 --use_membuf --membuf_loadpath where --membuf_parent_savedir task_sim --membuf_savedir foo --simnet_weight_dir simnet --batch_size 128 --host_one 10.161.159.142 --host_two 10.161.159.201 --host_three 10.161.159.131 --host_four 10.161.159.130 --host_five 10.161.159.148 --port_one_two 5000 --port_one_three 5001 --port_one_four 5002 --port_one_five 5003 --port_two_three 5004 --port_two_four 5005 --port_two_five 5006 --port_three_four 5007 --port_three_five 5008 --port_four_five 5009

    Agent 4:
    python3  PATH_TO_REPO/run_one_agent.py --send_fourth --share_info --open_atari_server --atari_server_port 3003 --atari_server_hostname 10.161.159.142 --agent_id 1 --frames 1000 --use_membuf --membuf_loadpath where --membuf_parent_savedir task_sim --membuf_savedir foo --simnet_weight_dir simnet --batch_size 128 --host_one 10.161.159.142 --host_two 10.161.159.201 --host_three 10.161.159.131 --host_four 10.161.159.130 --host_five 10.161.159.148 --port_one_two 5000 --port_one_three 5001 --port_one_four 5002 --port_one_five 5003 --port_two_three 5004 --port_two_four 5005 --port_two_five 5006 --port_three_four 5007 --port_three_five 5008 --port_four_five 5009

    Agent 5:
    python3  PATH_TO_REPO/run_one_agent.py --send_fifth --share_info --open_atari_server --atari_server_port 3004 --atari_server_hostname 10.161.159.142 --agent_id 1 --frames 1000 --use_membuf --membuf_loadpath where --membuf_parent_savedir task_sim --membuf_savedir foo --simnet_weight_dir simnet --batch_size 128 --host_one 10.161.159.142 --host_two 10.161.159.201 --host_three 10.161.159.131 --host_four 10.161.159.130 --host_five 10.161.159.148 --port_one_two 5000 --port_one_three 5001 --port_one_four 5002 --port_one_five 5003 --port_two_three 5004 --port_two_four 5005 --port_two_five 5006 --port_three_four 5007 --port_three_five 5008 --port_four_five 5009
