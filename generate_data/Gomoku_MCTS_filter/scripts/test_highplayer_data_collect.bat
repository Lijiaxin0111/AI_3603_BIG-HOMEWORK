@echo off



set train_options=--expri test_teaching_learning_collect ^
--split train ^
--Player 0 ^
--mood 0  ^
--batch_size 512 ^
--play_batch_size 1 ^
--board_width 20 ^
--board_height 20 ^
--use_gpu 0 ^
--data_collect 2 ^
--check_freq 10 ^
--game_batch_num 2000 


set run_cmd=python -u main_worker.py %train_options%

echo %run_cmd%
%run_cmd%