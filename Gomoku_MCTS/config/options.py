
import os
import argparse
import yaml

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

# basic settings
parser.add_argument('--seed', default=1234, type=int)
parser.add_argument('--savepath', type=str, default="blip_uni_cross_mu", help='')


# board settings
parser.add_argument("--board_width", type=int,default=9)
parser.add_argument("--board_height", type=int,default=9)
parser.add_argument("--n_in_row", type=int,default=5,help="the condition of winning")


# device settings
parser.add_argument('--config', type=str, default='config/config.yaml', help='Path to the config file.')
parser.add_argument('--gpu_num', type=int, default=1)
parser.add_argument('--gpu_id', type=str, default='2')
parser.add_argument('--device', type=str, default='cuda:2')
parser.add_argument('--use_gpu', type = int, default= 1)



# save options
parser.add_argument('--clear_visualizer', dest='clear_visualizer', action='store_true')
parser.add_argument('--std_log', dest='std_log', action='store_true')


# mode settings
parser.add_argument("--split",type=str,default="train",help="the mode of woker")


# train settings
parser.add_argument("--expri",type=str, default="",help="the name of experiment")
parser.add_argument("--learn_rate", type=float,default=2e-3)
parser.add_argument("--l2_const",type=float,default=1e-4)
# ???
parser.add_argument("--lr_multiplier", type=float,default= 1.0 ,help="adaptively adjust the learning rate based on KL")
parser.add_argument("--buffer_size",type=int,default=10000,help="The size of collection of game data ")
parser.add_argument("--batch_size",type=int,default=512) #512
parser.add_argument("--play_batch_size",type=int, default=1,help="The time of selfplaying when collect the data")
parser.add_argument("--epochs",type=int,default= 5,help="num of train_steps for each update") # 5
parser.add_argument("--kl_targ",type=float,default=0.02,help="the target kl distance between the old decision function and the new decision function ")
parser.add_argument("--check_freq",type=int,default=10,help='the frequence of the checking the win ratio when training')
parser.add_argument("--game_batch_num",type=int,default=1000,help =  "the total training times") #1500
parser.add_argument("--data_collect",type=int,default=2,help =  "the source of data : 1: high play 2: outfile 0: self_play ")
parser.add_argument("--high_player", type=str, choices=["pure mcts", "gomokubot"], default="pure_mcts", help="the high player")
parser.add_argument("--data_augment",type=int,default=0, help =  "0: None data augment;  > 0: data augment , the number of data in one episode // 3")
parser.add_argument("--use_kill", action = "store_true", default= False, help = "use kill or not")
parser.add_argument("--increase_playout", action = "store_true", default= False, help = "increase the playout of puremcts by epochs when testing in training process")
parser.add_argument("--stage", type=int, default=1, choices=[1,2,3], help="choose the model according to the stage of training. 1: Imitation Learning; 2: Self-Play; 3: VS Master")
parser.add_argument("--n_game", type=int, default=10, help = "the number of games when testing in training process")
# parser.add_argument("--l2_const",type=float,default=1e-4,help=" coef of l2 penalty")
parser.add_argument("--distributed",type=bool,default=False)

# preload_model setting
parser.add_argument("--preload_model",type=str, default="")
parser.add_argument("--model_type",type=str, default="duel", choices=["duel","biased","normal","gumbel","pure_mcts"])

# some trick setting
parser.add_argument("--board_cut",type=int, default=0)

# MCTSPlayer setting
parser.add_argument("--Player", type=int,default= 0 ,help="the player set:=  0: Alphazero ;  1: Gumbel_Alphazero ")
parser.add_argument("--mood", type=int,default= 0 ,help="the test mood:=  0: Alphazero Vs Pure;  1: Gumbel_Alphazero Vs Pure; 2:Alphazero Vs Gumbel_Alphazero  ")

# Alphazero  agent setting
parser.add_argument("--temp", type=float,default= 1.0 ,help="the temperature parameter when calculate the decision function getting the next action")
parser.add_argument("--n_playout",type=int, default=200, help="num of simulations for each move ")
parser.add_argument("--c_puct",type=int, default=5, help= "the balance parameter between exploration and exploitative for player1" )
parser.add_argument("--c_puct2", type=int, default=5, help="the balance parameter between exploration and exploitative for player2 ")
parser.add_argument("--res_num", type=int,default= 5 ,help="the number of residual block in the network")
# GumbelAlphazero agent setting
parser.add_argument("--action_m",type=int, default=8, help="num of simulations for each move ")

# GomokuBot agent setting
parser.add_argument("--start_edge", action="store_true", default=False, help="start with an edge move or not when using GomokuBot as highplayer")

# prue_mcts agent setting
parser.add_argument("--pure_mcts_playout_num",type=int, default=2000)

# test && game settings
parser.add_argument('--test_ckpt', type=str, default=None, help='ckpt absolute path')
parser.add_argument('--shown', type= int, default = 0,help="show the board in the game: 1: True; 0: False")
parser.add_argument("--game_player", type=str, choices=["duel","biased", "gumbel", "normal", "gomokubot"], default="duel", help="choose the player to test in the game.py")

opts = parser.parse_args()

# additional parameters
current_path = os.path.abspath(__file__)
grandfather_path = os.path.abspath(os.path.dirname(os.path.dirname(current_path)) + os.path.sep + ".")
with open(os.path.join(grandfather_path, opts.config), 'r') as stream:
    config = yaml.full_load(stream)
