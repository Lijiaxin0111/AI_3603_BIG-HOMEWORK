@echo off



set train_options=--expri test_Alphazero_high_collect ^
--split train ^
--Player 0 ^
--batch_size 512 ^
--play_batch_size 1 ^
--board_width 9 ^
--board_height 9 ^
--use_gpu 0 ^
--mood 0  ^
--highplayer_collect 1 ^


--game_batch_num 2000 ^


set run_cmd=python -u main_worker.py %train_options%

echo %run_cmd%
%run_cmd%