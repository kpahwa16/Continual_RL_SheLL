import math
import torch.nn as nn
import numpy as np
from config import Config
from core.logger import TensorBoardLogger
from core.util import get_output_folder, get_common_membuf_location
from tester import Tester
import pickle
import random
import json
import gym
import pdb
import os

class Trainer:
    def __init__(self, agent, env, config, loss_fn=None, test_env=None, 
                 eval_model=False, num_test_times=1,
                 sample_thres=.9, sim_agent=None):
        self.agent = agent
        self.env = env
        self.env_name = env.unwrapped.spec.id
        self.config = config
        self.test_env = test_env
        self.eval_model = eval_model
        self.sim_agent = sim_agent

        # non-Linear epsilon decay
        epsilon_final = self.config.epsilon_min
        epsilon_start = self.config.epsilon
        epsilon_decay = self.config.eps_decay
        self.epsilon_by_frame = lambda frame_idx: epsilon_final + (epsilon_start - epsilon_final) * math.exp(
            -1. * frame_idx / epsilon_decay)
        self.outputdir = get_output_folder(self.config.output, self.config.env)
        self.agent.save_config(self.outputdir)
        self.board_logger = TensorBoardLogger(self.outputdir)
        self.loss_fn = nn.MSELoss() if loss_fn is None else loss_fn
        self.num_test_times = 1
        self.agent_id = self.config.agent_id
        self.task_no = self.config.task_no
        self.apply_sample_thres = self.config.apply_sample_thres
        self.apply_lsc_membuf = self.config.apply_lsc_membuf
        self.sample_thres = self.config.sample_thres
        if self.config.use_membuf:
            self.membufdir = get_common_membuf_location(self.config.membuf_parent_savedir, self.config.membuf_savedir)
        
    def train(self, 
              pre_fr=0, 
              apply_ewc=False, 
              learn_new_env=True, 
              use_membuf=False,
              use_simnet=False):
        losses = []
        all_rewards = []
        all_train_rewards = []
        train_mean_rewards = []
        test_rewards = []
        episode_reward = 0
        ep_num = 0
        is_win = False
        final_fr = -1
        state = self.env.reset()
        self.agent.save_model(self.outputdir, 'init_{}'.format(self.env_name))
        
        self.agent.buffer.set_curr_idx(self.agent.buffer.size())
        shared_buffer_path = os.path.join(self.membufdir, "membuf_lsc_{}_task-{}.pkl".format(self.env_name, self.config.task_no))
        if self.config.apply_lsc_membuf and not os.path.exists(shared_buffer_path):
            with open(shared_buffer_path, 'wb') as f:
                pickle.dump(self.agent.buffer.shared_buffer, f)
        
        for fr in range(pre_fr + 1, self.config.frames + 1):
            epsilon = self.epsilon_by_frame(fr)
            
            if learn_new_env:
                action = self.agent.act(state, epsilon, apply_ewc=apply_ewc)
                next_state, reward, done, _ = self.env.step(action)
                self.agent.buffer.add(state, action, reward, next_state, done)
                state = next_state
                episode_reward += reward
            else:
                state, action, reward, next_state, done = self.agent.buffer.get_past_buffer_samples()
                self.agent.buffer.add(state[0], action, reward, next_state[0], done)
                episode_reward += reward
            
            #action = self.agent.act(state, epsilon, apply_ewc=apply_ewc)
            #next_state, reward, done, _ = self.env.step(action)
            #self.agent.buffer.add(state, action, reward, next_state, done)
            #state = next_state
            #episode_reward += reward
            
            loss = 0
            buffer_size = self.agent.buffer.size()
            # pdb.set_trace()
            if self.apply_sample_thres and (buffer_size - self.agent.buffer.curr_start_idx) > self.config.batch_size:
                # pdb.set_trace()
                # if random.random() >= self.sample_thres:
                #     loss = self.agent.learning(fr, self.loss_fn, apply_ewc=apply_ewc, focus_curr=True)
                # else:
                #     loss = self.agent.learning(fr, self.loss_fn, apply_ewc=apply_ewc, focus_curr=False)
                loss = self.learn_by_thres(fr, apply_ewc=apply_ewc)
            elif self.apply_lsc_membuf and (buffer_size - self.agent.buffer.curr_start_idx) > self.config.batch_size:
                # pdb.set_trace()
                loss = self.learn_by_thres(fr, apply_ewc=apply_ewc, apply_lsc=self.apply_lsc_membuf)
            elif buffer_size > self.config.batch_size: # without biasing towards samples of current task
                loss = self.agent.learning(fr, self.loss_fn, apply_ewc=apply_ewc)
            losses.append(loss)
            self.board_logger.scalar_summary('Loss per frame', fr, loss)
            
            # low-switching cost on memory
            if fr % self.config.num_frames_save_buf == 0:
                print("save contents to shared buffer")
                self.agent.buffer.update_shared_buffer(self.config.num_frames_save_buf, shared_buffer_path)
            if fr % self.config.num_frames_load_buf == 0:
                print("load contents from shared buffer")
                self.agent.buffer.load_shared_buffer(shared_buffer_path)
            if fr % self.config.print_interval == 0:
                print("frames: %5d, reward: %5f, loss: %4f episode: %4d" % (fr, np.mean(all_rewards[-100:]), loss, ep_num))
                train_mean_rewards.append((fr, np.mean(all_rewards[-100:])))
            if fr % self.config.log_interval == 0:
                # print('Reward per episode: ep_num = {}, reward = {}'.format(ep_num, all_rewards[-1]))
                self.board_logger.scalar_summary('Reward per episode', ep_num, all_rewards[-1])
            if self.config.checkpoint and fr % self.config.checkpoint_interval == 0:
                self.agent.save_checkpoint(fr, self.outputdir)
            if fr % 10000 == 0:
                self.agent.save_model(self.outputdir, 'fr_{}_{}'.format(fr, self.env_name))
                if self.eval_model:
                    test_avg_reward = self.evaluate(num_episodes=self.num_test_times) # default is 1
                    test_rewards.append(test_avg_reward)
                    print("frames {}: test reward {}, on {}".format(fr, test_avg_reward, self.test_env.unwrapped.spec.id))
            if done:
                state = self.env.reset()
                all_rewards.append(episode_reward)
                episode_reward = 0
                ep_num += 1
                avg_reward = float(np.mean(all_rewards[-100:]))
                bst_reward = float(np.max(all_rewards[-100:]))
                self.board_logger.scalar_summary('Best 100-episodes average reward', ep_num, avg_reward)
                if len(all_rewards) >= 100 and avg_reward >= self.config.win_reward and all_rewards[-1] > self.config.win_reward: # and all_rewards[-1] > best_reward:
                    best_reward = all_rewards[-1]
                    is_win = True
                    self.agent.save_model(self.outputdir, 'best_{}'.format(self.env_name))
                    final_fr = fr # update final frame number for saving fisher matrix
                    print('Ran %d episodes best 100-episodes average reward is %3f. Best 100-episode reward is %3f. Solved after %d trials ✔' % (ep_num, avg_reward, bst_reward, ep_num - 100))
                    if self.config.win_break:
                        break
        
        if use_membuf:
            # get portion of buffer that has samples of the current task
            self.agent.buffer.update_prev_buffer()
            # save history memory buffer
            with open(os.path.join(self.outputdir, "membuf_history_{}_agent-{}.pkl".format(self.env_name, self.agent_id)), 'wb') as f:
                pickle.dump(self.agent.buffer.buffer, f)
            # save memory buffer for this task only
            with open(os.path.join(self.outputdir, "membuf_{}_agent-{}-task-{}.pkl".format(self.env_name, self.agent_id, self.task_no)), 'wb') as f:
                pickle.dump(self.agent.buffer.prev_buffer, f)            
            with open(os.path.join(self.membufdir, "membuf_{}_agent-{}-task-{}.pkl".format(self.env_name, self.agent_id, self.task_no)), 'wb') as f:
                pickle.dump(self.agent.buffer.prev_buffer, f)

        if apply_ewc:
            with open(os.path.join(self.outputdir, "debug_ewc_loss.json"), 'w') as f6:
                json.dump(self.agent.debug_ewc_loss, f6)
            self.agent.estimate_fisher_matrix(self.agent.config.batch_size, self.loss_fn)
            self.agent.save_fisher_matrix(final_fr, self.outputdir)

        with open(os.path.join(self.outputdir, "all_rewards_{}.json".format(self.env_name)), 'w') as f:
            json.dump(all_rewards, f)
        with open(os.path.join(self.outputdir, "test_rewards_{}.json".format(self.env_name)), 'w') as f2:
            json.dump(test_rewards, f2)
        with open(os.path.join(self.outputdir, "train_mean_reward_per_{}_frame_{}.json".format(self.config.print_interval, self.env_name)), 'w') as f4:
            json.dump(train_mean_rewards, f4)
        with open(os.path.join(self.outputdir, "debug_task2_loss.json"), 'w') as f5:
            json.dump(self.agent.debug_task2_loss, f5)
        if not is_win:
            print('Did not solve after %d episodes' % ep_num)
            self.agent.save_model(self.outputdir, 'last_{}'.format(self.env_name))
        
    def evaluate(self, debug=False, num_episodes=50, test_ep_steps=600000): # now the dafault is 1
        avg_reward = 0
        policy = lambda x: self.agent.act(x)
        for episode in range(num_episodes):
            s0 = self.test_env.reset()
            episode_steps = 0
            episode_reward = 0.
            done = False
            while not done:
                action = policy(s0)
                s0, reward, done, info = self.test_env.step(action)
                episode_reward += reward
                episode_steps += 1
                if episode_steps + 1 > test_ep_steps:
                    done = True
            if debug:
                print('[Test] episode: %3d, episode_reward: %5f' % (episode, episode_reward))
            avg_reward += episode_reward
        avg_reward /= num_episodes 
        return avg_reward
    
    def learn_by_thres(self, fr, apply_ewc=False, apply_lsc=False):
        if random.random() >= self.sample_thres:
            print("enter!")
            if apply_lsc:
                return self.agent.learning(fr, self.loss_fn, apply_ewc=apply_ewc, focus_curr=False, use_lsc=apply_lsc)
            else:
                return self.agent.learning(fr, self.loss_fn, apply_ewc=apply_ewc, focus_curr=True)
        else:
            print("nope!")
            return self.agent.learning(fr, self.loss_fn, apply_ewc=apply_ewc, focus_curr=False)
        