- Recap of results
  - Our training recipe does achieve positive results at specific matched eval temps
  - But it does not cleanly improve over the best baseline eval temp (also in pass@4 and on hard samples)
  - Probes show us some tokens behave like SSD predicts
  - But also some tokens behave like classical training
- Interpretation
  - Training worked, but was confounded by a non-SSD effect
  - The SSD effect itself might be too small to detect with the amount of validation we had, and/or hard to separate (see the special-casing we had to do on forks to see the expected top-1 increase)
  - One likely explanation:
    - we trained at seq len 32k but filtered out overlong rows
    - this biases the model towards thinking for shorter lengths
    - We can see this from the error class of the models: trained only improves
      on length stops, not on reasoning.
- Next steps
  - Scale up
    - bigger model size was reported to be more consistent
    - SSD effect at 4k training examples is hard to find, 8k might be easier
      (even at same performance)
    - Longer training seq lengths
      - We did 48k but again filtered out length stops; it behaved similarly
        (could be an effect of few overlong rows)
      - Increasing to 64k for train & eval could help