The RL algorithm is GRPO. For each question it samples a group of outputs, scores each with a rule-based reward, and normalizes rewards within the group to get the advantage. The key move: the group mean is the baseline, so GRPO drops PPO's value network — one fewer large model to train.

Key points: GRPO = clipped ratio + KL; group-mean baseline, no critic.
Time: 1:10
