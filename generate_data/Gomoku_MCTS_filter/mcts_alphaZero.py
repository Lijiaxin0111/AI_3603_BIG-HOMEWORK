# -*- coding: utf-8 -*-
"""
Monte Carlo Tree Search in AlphaGo Zero style, which uses a policy-value
network to guide the tree search and evaluate the leaf nodes

@author: Junxiao Song
"""

import numpy as np
import copy
import time
from concurrent.futures import ThreadPoolExecutor
import threading

from config.options import *
import sys
from config.utils import *
from some_Gomoku_trick.board_cut import board_cut

def softmax(x):
    probs = np.exp(x - np.max(x))
    probs /= np.sum(probs)
    return probs


class TreeNode(object):
    """A node in the MCTS tree.

    Each node keeps track of its own value Q, prior probability P, and
    its visit-count-adjusted prior score u.
    """

    def __init__(self, parent, prior_p):
        self._parent = parent
        self._children = {}  # a map from action to TreeNode
        self._n_visits = 0
        self._Q = 0
        self._u = 0
        self._P = prior_p

    def expand(self, action_priors):
        """Expand tree by creating new children.
        action_priors: a list of tuples of actions and their prior probability
            according to the policy function.
        """
        for action, prob in action_priors:
            if action not in self._children:
                self._children[action] = TreeNode(self, prob)

    def select(self, c_puct):
        """Select action among children that gives maximum action value Q
        plus bonus u(P).
        Return: A tuple of (action, next_node)
        """
        return max(self._children.items(),
                   key=lambda act_node: act_node[1].get_value(c_puct))

    def update(self, leaf_value):
        """Update node values from leaf evaluation.
        leaf_value: the value of subtree evaluation from the current player's
            perspective.
        """
        # Count visit.
        self._n_visits += 1
        # Update Q, a running average of values for all visits.
        self._Q += 1.0 * (leaf_value - self._Q) / self._n_visits

    def update_recursive(self, leaf_value):
        """Like a call to update(), but applied recursively for all ancestors.
        """
        # If it is not root, this node's parent should be updated first.
        if self._parent:
            self._parent.update_recursive(-leaf_value)
        self.update(leaf_value)

    def get_value(self, c_puct):
        """Calculate and return the value for this node.
        It is a combination of leaf evaluations Q, and this node's prior
        adjusted for its visit count, u.
        c_puct: a number in (0, inf) controlling the relative impact of
            value Q, and prior probability P, on this node's score.
        """
        self._u = (c_puct * self._P *
                   np.sqrt(self._parent._n_visits) / (1 + self._n_visits))
        return self._Q + self._u

    def is_leaf(self):
        """Check if leaf node (i.e. no nodes below this have been expanded)."""
        return self._children == {}

    def is_root(self):
        return self._parent is None


class MCTS(object):
    """An implementation of Monte Carlo Tree Search."""

    def __init__(self, policy_value_fn, c_puct=5, n_playout=10000):
        """
        policy_value_fn: a function that takes in a board state and outputs
            a list of (action, probability) tuples and also a score in [-1, 1]
            (i.e. the expected value of the end game score from the current
            player's perspective) for the current player.
        c_puct: a number in (0, inf) that controls how quickly exploration
            converges to the maximum-value policy. A higher value means
            relying on the prior more.
        """
        self._root = TreeNode(None, 1.0)
        self._policy = policy_value_fn
        self._c_puct = c_puct
        self._n_playout = n_playout

    def _playout(self, state, lock=None):
        """Run a single playout from the root to the leaf, getting a value at
        the leaf and propagating it back through its parents.
        State is modified in-place, so a copy must be provided.
        """
        node = self._root

        if lock is not None:
            lock.acquire()
        while (1):
            if node.is_leaf():
                break
            # Greedily select next move.
            action, node = node.select(self._c_puct)
            # print("alpha action: ",action)
            # print("avai:", state.availables)
            state.do_move(action)


        if lock is not None:
            lock.release()
        # Evaluate the leaf using a network which outputs a list of
        # (action, probability) tuples p and also a score v in [-1, 1]
        # for the current player.
        action_probs, leaf_value = self._policy(state)
        # Check for end of game.
        end, winner = state.game_end()
        if lock is not None:
            lock.acquire()
        if not end:
            node.expand(action_probs)
        else:
            # for end state，return the "true" leaf_value
            if winner == -1:  # tie
                leaf_value = 0.0
            else:
                leaf_value = (
                    1.0 if winner == state.get_current_player() else -1.0
                )

        # Update value and visit count of nodes in this traversal.
        node.update_recursive(-leaf_value)
        if lock is not None:
            lock.release()

    def get_move_probs(self, state, temp=1e-3):
        """Run all playouts sequentially and return the available actions and
        their corresponding probabilities.
        state: the current game state
        temp: temperature parameter in (0, 1] controls the level of exploration
        """

        start_time_averge = 0

        ### test multi-thread
        # lock = threading.Lock()
        # with ThreadPoolExecutor(max_workers=4) as executor:
        #     for n in range(self._n_playout):
        #         start_time = time.time()

        #         state_copy = copy.deepcopy(state)
        #         executor.submit(self._playout, state_copy, lock)
        #         start_time_averge += (time.time() - start_time)
        ### end test multi-thread

        t = time.time()
        #  ---------
        act_probs, leaf_value = self._policy(state)
        
        act_probs =  list(act_probs)

        # leaf_value = leaf_value.detach().numpy()[0][0]
        
        # print(list(act_probs))
        porbs = [prob  for act,prob in (act_probs)]
        # print("net ",porbs)
        # print("net_arg:",np.argmax(porbs))
        
        #  ---------

        
        for n in range(self._n_playout):
            start_time = time.time()
            

            state_copy = copy.deepcopy(state)
            self._playout(state_copy)
            start_time_averge += (time.time() - start_time)
        total_time = time.time() - t
        # print('!!time!!:', time.time() - t)

        print(f" My MCTS sum_time: {total_time}, total_simulation: {self._n_playout}")

        # calc the move probabilities based on visit counts at the root node
        act_visits = [(act, node._n_visits)
                      for act, node in self._root._children.items()]

        acts, visits = zip(*act_visits)

        act_probs = softmax(1.0 / temp * np.log(np.array(visits) + 1e-10))
     
        return 0, acts, act_probs, total_time

    def update_with_move(self, last_move):
        """Step forward in the tree, keeping everything we already know
        about the subtree.
        """
        if last_move in self._root._children:
            self._root = self._root._children[last_move]
            self._root._parent = None
        else:
            self._root = TreeNode(None, 1.0)

    def __str__(self):
        return "MCTS"


class MCTSPlayer(object):
    """AI player based on MCTS"""

    def __init__(self, policy_value_function,
                 c_puct=5, n_playout=2000, is_selfplay=0):
        self.mcts = MCTS(policy_value_function, c_puct, n_playout)
        self._is_selfplay = is_selfplay

    def set_player_ind(self, p):
        self.player = p

    def reset_player(self):
        self.mcts.update_with_move(-1)

    def get_action(self, board, temp=1e-3, return_prob=0, return_time=False):
        sensible_moves = board.availables
        # the pi vector returned by MCTS as in the alphaGo Zero paper
        move_probs = np.zeros(board.width * board.height)
        if len(sensible_moves) > 0:
            _, acts, probs, simul_mean_time = self.mcts.get_move_probs(board, temp)

            move_probs[list(acts)] = probs
            # print("return", move_probs)
            # print("return_max", np.argmax(move_probs))

    
            if opts.board_cut :
                move_probs = board_cut(board,move_probs)
                probs =  move_probs[list(acts)]

            if self._is_selfplay:
                # add Dirichlet Noise for exploration (needed for
                # self-play training)
                move = np.random.choice(
                    acts,
                    p=0.75 * probs + 0.25 * np.random.dirichlet(0.3 * np.ones(len(probs)))
                )
                # update the root node and reuse the search tree
                self.mcts.update_with_move(move)
            else:
                # with the default temp=1e-3, it is almost equivalent
                # to choosing the move with the highest prob
                move = np.random.choice(acts, p=probs)
                # reset the root node
                self.mcts.update_with_move(-1)
            
            #                location = board.move_to_location(move)
            #                print("AI move: %d,%d\n" % (location[0], location[1]))
            
            
#                location = board.move_to_location(move)
#                print("AI move: %d,%d\n" % (location[0], location[1]))
            # print("final move", move)


            if return_time:

                if return_prob:

                    return move, move_probs, simul_mean_time
                else:
                    return move, simul_mean_time
            else:

                if return_prob:

                    return move, move_probs
                else:
                    return move
        else:
            print("WARNING: the board is full")

    def __str__(self):
        return "MCTS {}".format(self.player)
