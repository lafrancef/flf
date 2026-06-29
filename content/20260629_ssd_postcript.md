+++
title = "Self-distillation on math: postscript"
description = "Some personal notes of what I found interesting or unexpected in the SSD project, and what I would do differently next time."
date = 2026-06-29
+++

For this post, I want to focus less on the scientific and experimental side of things, and more on the engineering and operational aspects. I ran this project in my free time and on my own budget, which led me to some intersting situations that I want to look at in more detail.

## The cost of getting compute

I have a quite beefy local setup (my [HuggingFace profile](https://huggingface.co/lafrancef) tells me I'm solidly in "GPU rich" territory), but even that wasn't enough for the experiments I wanted to run. Therefore, I did not do any training locally beyond pre-flight checks before running on rented compute. I wanted to minimize the amount of time wasted on setup so I tested the infra with the 0.8B scale model which did fit. I was very concerned about getting everything to work under a single H100 (80 GiB VRAM) to simplify the setup and cost. This is one of the main reasons I went with a small scale of 4B. I learned about and applied many small tricks to reduce the VRAM usage during training, in particular:

  * Gradient checkpointing and accumulation
  * Fully memory-optimized bf16 optimizer state (store the moments in bf16 and no fp32 master weights, for 8 bytes / param)
  * Fused chunked cross-entropy kernel to avoid a large VRAM spike in the last layer
  
Of these, not all were equally successful. Two of them were even harmful:

  * Because I had a very interesting noise-dominated training landscape with low loss, many gradient updates were very small, often falling below the bf16 quantum. With fp32 master weights and moments, this is not a problem, but in my case it caused the proportion of changed weights during training to drop to almost zero after a few steps. Switching back to the standard AdamW fp32 doubled optimizer VRAM but restored training dynamics. I threw away several experiments because of this. In the future I'll know to reach for the weights-changed diagnotic if training seems stalled.
  * Since I was using only text prompts, ChatGPT suggested and implemented a method to remove the multimodal input module from the model, saving a couple extra GiBs of VRAM. Except that this path had a a couple bugs that prevented trained models tfrom reloading properly (one bug was a token ID mismatch and the other was something else that forced the model into endless thinking). This was easily the most vibed area of the code so I don't blame the model because I also had no idea what was going on. I spent quite some time debugging this and in the end just reverted the optimization, which was never big enough to matter anyway.

Basically, I got a bit carried away with the optimization in order to make sure I could fit under my self-imposed VRAM target. I made it work, but that became irrelevant anyway because...

### Compute bottlenecks

This is something that surprised me: sampling (either training data or responses for evals) took something like 80% of all the GPU time I paid for. Once I saw this, I decided I should optimize my sampler as well, but there's only so much one guy can do to make vLLM faster. So I focused on another axis: just scaling up compute. At first I did simple data parallelism, but then I figured out the obvious thing: I was running very short prompts with very long generations, so entirely decode-bound. This meant I didn't want more compute in general, I wanted more bandwidth. Which meant I had to consider...

### Tradeoff between price and performance

Each on-demand GPU cloud solution has a variety of options to offer, where the price is supposed to align with the performance. My question was: is it worth it to pay for the more expensive GPUs because they will finish the job faster? As it turned out, for sampling specifically, the total price of a job was very similar across different GPUs with different hourly rates (I guess this makes sense in an efficient-markety sort of way, assuming compute is roughly fungible). So it was not a question of how much I had to pay for a job, but whether I wanted the results sooner than later. That's a no-brainer, so I switched from H100s to B200s, which incidentally have so much VRAM that I wouldn't need to worry at all about usage!

### Moral of the story

Overall, this is a classic case of premature optimization. I feel like I was justified by wanting to reduce costs, but it's true that I did not realize what the true bottleneck was at the start and I made some assumptions that did not help much. Instead I should have aimed for a stable setup first, with proven good training dynamics, then measured what was taking time in that stable setup.

## Operations

I set up my workspace so that I just had to clone my repo on the remote machine and sync the environment to get started. But at some point I also wanted the AI to take over monitoring of experiments (to catch issues like: I made a typo and reserved 84 GiB of disk instead of 384, so training will crash two hours in when I'm asleep). So I had it write a small server that it could connect to using my API key. This server exposed commands that mirrored the CLI tool I was using to run experiments locally: check available configs and hardware, run stages one by one or all at once, checking job progress and logs, etc. I thought I was being clever and making things easy, but a couple times the server went down for some reason and the agent merrily carried on by using `runpodctl` and SSH (I had previously given it an SSH key for this purpose) to control the remote, with no apparent issues. So the server idea was cool, but perhaps unnecessary. Overall, maybe setting up a Docker image would have saved more time, but I never got around to it.

## Themes

I would say the main thing I would change on this project would be: less overengineering and more focus on quality. Even though I ran experiments reasonably fast (given my spotty schedule), I got sidetracked a couple times on these optimization sidequests that seemed important at the time but didn't matter much in the end. I would have gotten results faster by focusing on the experimental side:

  1. Start running an experiment.
  2. While it runs, think of what to do given the possible results.
  3. Only if you have time here, think of improving the infra, cost, performance, etc.

Or simply ABE: **A**lways **B**e **E**xperimenting.
