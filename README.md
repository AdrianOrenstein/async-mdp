# Async-MDP: Formulating asynchronous problem settings for RL

Asynchronous environments do not wait for the agent to decide an action. 


## TODO

### Async Environment

- [ ] Lower the code and get the FLOPs, construct an MDP that is "total flops allowed per decision, if it is over then we skip the frame and pass what they missed".
- [ ] What about asynchronous agents? We need a blocking amount of compute use, and a non-blocking amount. 
- [ ] Can we prove that an asynchronous mdp is equivalent to a synchronous mdp if there is no delay. 

### Learning to repeat actions

**Args**
- [ ] Add an argument to no repeat (default)
- [ ] Add an arg to repeat a constant amount
- [ ] Add an arg to repeat a learned amount (expanding the action space), specifying the list of repeat amounts.

**Baseline 1: Constant action repeats**
- [ ] Make a last_action variable
- [ ] If action_repeat_amount > 0, don't select epsilon greedy or the network, just repeat the last action.

**Learning to repeat actions**
- [ ] Expand the action space of the agent so that it is actions * repeat amounts
- [ ] Demux the action the moment we call the network

**Understanding: Implications on compute usage**
- [ ] We'd like to compare against an agent that is forced to act on every frame, vs an agent that can amortise its cost across many frames. A decision is when the agent chooses to execute an epsilon-greedy action, or chooses an action via it's policy. Adding action repeats should proportionally reduce the number of decisions. 

**The goal**
- [ ] Can we offload a design decision to the agent? As the frameskip/action-repeat hyper is such an important hyper per game, per instance in the game, maybe it is better that we let our agents decide this?





**Baseline 2: Epsilon-greedy dithering**
- [ ] Temporally-extended Depsilon-greedy

**Understanding: Implications on state-space coverage**
- [ ] Temporally-extended Depsilon-greedy has a good visualisation on some toy environments to understand 

**Choice point: What do we put into the experience replay?**
- [ ] Typically we stack the last few frames, is thi
Michael Johanson. 32 to 31 was bad, smooth transitions due to some things only happening on even frames. Blending between 32 and 16. Talk to Michael more. Lots of fours in DQN. Frame skip from frame buffer from action repeats to play with them. What frames do you put into your experience replay, the most recent or the temporally extended. Figure out what discount factor per frame. Varied a lot by game. learn your hypers.



**Future work: We used 100% of the network, or 0%, can we go somewhere inbetween?**
- [ ] 