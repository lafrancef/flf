+++
title = "Self-distillation on math: conclusion"
description = "Reflecting on what we learned while working on simple self-distillation for competitive math."
date = 2026-06-20
+++

[Last time](20260619_ssd_probe.md) we took our trained models and compared their output probability distributions against the baselines, looking for the SSD effect directly. Now let's wrap up the project and discuss what we learned.

## Recap

Let's go over the results once more:

  - Our training recipe does achieve positive results against high temperature-matched baselines. Several evident ablations (learning rate, data, sequence length) do not immediately reveal a better recipe (whether on task performance or health).
  - Getting a learning signal is hard, since the model is already very close to its training data.
  - Our best trained model appears to improve over the best naive temperature tuning, but not by a significant margin.
  - Probes show us that the models exhibit some of the behavior predicted by SSD, but also some differences that are best explained by generic training effects.

## Interpretation

My interpretation is: training worked, but the results are confounded by a non-SSD effect. If there was an SSD effect, it might have been too small to detect, and/or too hard to separate from the generic training effect (see for example the special-casing we had to do with locks last time to see the expected top-1 increase).

### Training effect description

When I speak of a training effect, I mean that simply training the model on more math reasoning traces will guide it towards a more math-oriented position, at the expense of other subjects. In the SSD paper, they do verify that performance does not degrade on other subjects, and that some statistics agree with their proposed effects (top mass increases, and so does survivor set size), but they do not probe output distributions on real data.

On our side, when we ran the probe, we observed that some tokens had a distribution shift that was different from what SSD would predict (e.g. that locks will sharpen). This is what I mean by "training effect". Here is one training effect that could explain why we saw an increase in performance despite no correctness verification:

  - We trained at sequence length 32k, and filtered out overlong rows.
  - This biases the model by showing it only regular and short thinking traces, not overlong ones. The model is incentivized to think for a shorter amount of time.
  - This directly addresses one of the failure modes of Qwen3.5-4B, namely that it tends to get stuck in thinking loops often.

This explanation is more mundane, but consistent with what we observed: the trained model improves mainly on rows where the baseline was thinking for too long, and `Wait` / self-correction tokens that were classified as locks primarily end up getting swapped instead of sharpened.

### Potential reasons for the absence or small magnitude of an SSD effect

Here are a few possible reasons why I might not have been able to conclusively reproduce the SSD effect in my experiments:

  - My hypothesis does not hold, and math does not have a fork/lock structure;
  - Too little scale (see below);
  - Too-small model to have a consistent effect;
  - Too few sweep cells to gather enough data;
  - Differences between my infra setup and theirs;
  - Some bug;
  - There is another, non-SSD explanation for the gains they report (note: I believe this is unlikely compared to the other explanations, since I did see some tokens with an SSD effect in probing)

## Next steps

The obvious next step is scale: the SSD paper reported more consistent results with larger scale models. At the same time, the 32k training sequence length combined with overlong filtering might be introducing a bias. We tried increasing training sequence length to 48k and did not see improvements on task performance, but this was at a reduced training data scale. In fact, I ran only one experiment at >4k data samples, which might not have been enough to rule out scale effects.

Therefore, if I had more budget and time, I would try scaling up in data size and sequence length, as well as run more sweeps. Confirming that the model was learning properly in the noise-dominated regime initially took some effort, but probing turned out to be an effective mechanism for this. I'm optimistic that if there's an effect on math, we'll be able to find it at the 4B scale, but it might also be easier at larger model scales.

## Last word

That's it for this project! I hope you enjoyed the writeup, even though the conclusion is a bit of a let-down. I'll have a postscript where I discuss some of the more operational details as well as what I would have done differently to get results faster.
