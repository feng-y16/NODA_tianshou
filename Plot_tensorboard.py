import sys
import os
import numpy as np
import argparse
import gym
import matplotlib.pyplot as plt
from tensorboard.backend.event_processing import event_accumulator
import time
import pdb


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--task', type=str, default='Pendulum-v0')
    parser.add_argument('--postfix', type=str, default='default')
    args = parser.parse_known_args()[0]
    return args


def sort_file_by_time(file_path):
    abspath = os.path.abspath(file_path) + '/'
    files = os.listdir(abspath)
    for file in files:
        if os.path.isdir(abspath + file):
            files.remove(file)
    if not files:
        return
    else:
        files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(file_path, x)))
        return files


def main(args=get_args()):
    env = gym.make(args.task)
    if args.task == 'Pendulum-v0':
        env.spec.reward_threshold = -250
    reward_threshold = env.spec.reward_threshold
    log_dir = 'log/' + args.task + '/sac/'
    newest_file_baseline = sort_file_by_time(log_dir + 'baseline/')[-1]
    ea_sac = event_accumulator.EventAccumulator(log_dir + 'baseline/' + newest_file_baseline)
    ea_sac.Reload()
    # print(ea_sac.scalars.Keys())
    rew_sac_item_mean = ea_sac.scalars.Items('test_NODAE/rew')
    rew_sac_item_std = ea_sac.scalars.Items('test_NODAE/rew_std')
    step_sac = []
    rew_sac_mean = []
    rew_sac_std = []
    assert len(rew_sac_item_mean) == len(rew_sac_item_std)
    for i in range(len(rew_sac_item_mean)):
        step_sac.append(rew_sac_item_mean[i].step)
        rew_sac_mean.append(rew_sac_item_mean[i].value)
        rew_sac_std.append(rew_sac_item_std[i].value)

    newest_file = sort_file_by_time(log_dir)[-1]
    ea_ssac = event_accumulator.EventAccumulator(log_dir + newest_file)
    ea_ssac.Reload()
    rew_ssac_item_mean = ea_ssac.scalars.Items('test_NODAE/rew')
    rew_ssac_item_std = ea_ssac.scalars.Items('test_NODAE/rew_std')
    step_ssac = []
    rew_ssac_mean = []
    rew_ssac_std = []
    assert len(rew_ssac_item_mean) == len(rew_ssac_item_std)
    start_step = ea_ssac.scalars.Items('simulator/start_step')[0].value
    for i in range(len(rew_ssac_item_mean)):
        step_ssac.append(rew_ssac_item_mean[i].step)
        rew_ssac_mean.append(rew_ssac_item_mean[i].value)
        rew_ssac_std.append(rew_ssac_item_std[i].value)

    start_index = 0
    for i in range(len(step_sac)):
        if step_sac[i] >= start_step:
            start_index = i
            break
    step_sac = np.array(step_sac)[start_index:]
    rew_sac_mean = np.array(rew_sac_mean)[start_index:]
    rew_sac_std = np.array(rew_sac_std)[start_index:]
    step_ssac = np.array(step_ssac)[start_index:]
    rew_ssac_mean = np.array(rew_ssac_mean)[start_index:]
    rew_ssac_std = np.array(rew_ssac_std)[start_index:]

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(step_sac, rew_sac_mean, label='SAC')
    ax.fill_between(step_sac, rew_sac_mean - rew_sac_std, rew_sac_mean + rew_sac_std, alpha=0.3)
    ax.plot(step_ssac, rew_ssac_mean, label='NODAE-SAC')
    ax.fill_between(step_ssac, rew_ssac_mean - rew_ssac_std, rew_ssac_mean + rew_ssac_std, alpha=0.3)

    if len(step_sac) > len(step_ssac):
        step = step_sac
    else:
        step = step_ssac
    reward_threshold = np.ones(len(step)) * reward_threshold
    ax.plot(step, reward_threshold, label='Threshold', linestyle='--')

    ax.set_xlabel('Step')
    ax.set_ylabel('Reward')
    ax.legend(loc='best')
    save_path = os.path.abspath('results/') + '/'
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    plt.savefig(save_path + 'SAC-NODAE-comparison-' + args.task + '-' + args.postfix + '.pdf')
    plt.close()


if __name__ == '__main__':
    plt.rcParams.update({'figure.autolayout': True})
    plt.rc('font', size=14)
    main()
