# official_verdict

## Baseline Statement
- tag `mvp-rc3`, commit `7ffb5e04a022f7b905b002719dca35ef330e5b90`, config hashes: `097677bd851ca5ec3cdb49fe04fc3a868e67c55443e051decfbd6d099be63007`, `1d80826a79da5bd1637e75b8ddb9bb191827c6f2c156183ad3a5bed02d3264cc`, `3862f7b216c7f051a4f4b101d1072f17f40457cc0e11c9127e34f3383706ec3c`, `39f7f39971f0182514f51aca70e4806bfa71ed3f9edebef36de376e8e6b04c68`, `472e6d4612dcb65b7867c93346ed5585f2b7430bf17d2e592391805f4757c1a2`, `475c1d1ee338b48676cc61b8b573ab8fa95579a2242d4e8aa85b44939fa89b7c`, `8abda84adcb86be4f2ab31abd8be31f1fd352b386b5451815d9d33103542ab7c`, `a479c009c89d7bb39e460e6c746fc035bb8f4a4620e3527953d61a4dadb82ea7`, `b90a1e3af613726886fa4c7d8dfb17a4b068075d33aebc133edcd3e4e3ba58a4`, `c12697d2bc425323db85392efdebc9fad55d96ce0a3d1e53d85a7c7201ab862b`, `d9ee2b5da70f040a8583c95509b31dd7a6765c94fc5398a1d9e5d89eec22de9b`, `e76856cc1ab811b75dfdce77744315ff71aa29866b72b4e5ccb411ce2d9f5736`

## Key Findings
| input | phase | compared | metric | preferred | full | compared | delta |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
| official_wave1 | core | no_fast | survival_steps_mean | full | 93.8723 | 51.3120 | 42.5603 |
| official_wave1 | core | no_fast | mean_energy_deficit | full | 0.3814 | 0.5731 | -0.1917 |
| official_wave1 | core | no_fast | mean_water_deficit | full | 0.3060 | 0.3743 | -0.0683 |
| official_wave1 | core | no_interoception | survival_steps_mean | full | 93.8723 | 69.9167 | 23.9557 |
| official_wave1 | core | no_interoception | steps_to_first_needed_resource_mean | no_interoception | 10.3497 | 8.3560 | 1.9937 |
| official_wave1 | core | no_interoception | return_steps_to_seen_resource_mean | no_interoception | 10.3497 | 8.3560 | 1.9937 |
| official_wave1 | core | no_interoception | mean_energy_deficit | no_interoception | 0.3814 | 0.2051 | 0.1763 |
| official_wave1 | core | no_interoception | mean_water_deficit | full | 0.3060 | 0.5072 | -0.2013 |
| official_wave1 | core | no_slow | survival_steps_mean | full | 93.8723 | 84.5950 | 9.2773 |
| official_wave1 | core | no_slow | steps_to_first_needed_resource_mean | full | 10.3497 | 22.5540 | -12.2043 |
| official_wave1 | core | no_slow | return_steps_to_seen_resource_mean | full | 10.3497 | 22.5540 | -12.2043 |
| official_wave1 | core | no_slow | mean_energy_deficit | full | 0.3814 | 0.4690 | -0.0876 |
| official_wave1 | core | no_slow | mean_water_deficit | full | 0.3060 | 0.3090 | -0.0030 |
| official_wave1 | relocation | no_fast | survival_steps_mean | full | 93.7160 | 51.3960 | 42.3200 |
| official_wave1 | relocation | no_fast | post_relocation_life_mean | full | 48.7160 | 6.3960 | 42.3200 |
| official_wave1 | relocation | no_fast | relocation_recovery_success_rate | full | 0.7040 | 0.0000 | 0.7040 |
| official_wave1 | relocation | no_fast | mean_energy_deficit | full | 0.3811 | 0.5732 | -0.1920 |
| official_wave1 | relocation | no_fast | mean_water_deficit | full | 0.3081 | 0.3747 | -0.0666 |
| official_wave1 | relocation | no_interoception | survival_steps_mean | full | 93.7160 | 69.9380 | 23.7780 |
| official_wave1 | relocation | no_interoception | steps_to_first_needed_resource_mean | no_interoception | 10.2140 | 8.2140 | 2.0000 |
| official_wave1 | relocation | no_interoception | return_steps_to_seen_resource_mean | no_interoception | 10.2140 | 8.2140 | 2.0000 |
| official_wave1 | relocation | no_interoception | post_relocation_life_mean | full | 48.7160 | 24.9380 | 23.7780 |
| official_wave1 | relocation | no_interoception | relocation_recovery_success_rate | full | 0.7040 | 0.0000 | 0.7040 |
| official_wave1 | relocation | no_interoception | mean_energy_deficit | no_interoception | 0.3811 | 0.2048 | 0.1764 |
| official_wave1 | relocation | no_interoception | mean_water_deficit | full | 0.3081 | 0.5072 | -0.1991 |
| official_wave1 | relocation | no_slow | survival_steps_mean | full | 93.7160 | 84.3960 | 9.3200 |
| official_wave1 | relocation | no_slow | steps_to_first_needed_resource_mean | full | 10.2140 | 22.3520 | -12.1380 |
| official_wave1 | relocation | no_slow | return_steps_to_seen_resource_mean | full | 10.2140 | 22.3520 | -12.1380 |
| official_wave1 | relocation | no_slow | post_relocation_life_mean | full | 48.7160 | 39.3960 | 9.3200 |
| official_wave1 | relocation | no_slow | relocation_recovery_success_rate | full | 0.7040 | 0.5620 | 0.1420 |
| official_wave1 | relocation | no_slow | relocation_recovery_steps_mean | full | 2.6935 | 6.3971 | -3.7036 |
| official_wave1 | relocation | no_slow | mean_energy_deficit | full | 0.3811 | 0.4668 | -0.0856 |
| official_wave1 | relocation | no_slow | mean_water_deficit | full | 0.3081 | 0.3243 | -0.0161 |
| relocation_stress | core | no_fast | survival_steps_mean | full | 94.1100 | 51.2567 | 42.8533 |
| relocation_stress | core | no_fast | mean_energy_deficit | full | 0.3824 | 0.5729 | -0.1906 |
| relocation_stress | core | no_fast | mean_water_deficit | full | 0.3059 | 0.3738 | -0.0679 |
| relocation_stress | relocation | no_fast | survival_steps_mean | full | 91.8600 | 51.3600 | 40.5000 |
| relocation_stress | relocation | no_fast | post_relocation_life_mean | full | 56.8600 | 16.3600 | 40.5000 |
| relocation_stress | relocation | no_fast | relocation_recovery_success_rate | full | 0.9600 | 0.0000 | 0.9600 |
| relocation_stress | relocation | no_fast | mean_energy_deficit | full | 0.3721 | 0.5730 | -0.2010 |
| relocation_stress | relocation | no_fast | mean_water_deficit | full | 0.2896 | 0.3743 | -0.0847 |
| wave2a | core | full_observation | survival_steps_mean | full | 93.8723 | 69.5820 | 24.2903 |
| wave2a | core | full_observation | mean_energy_deficit | full | 0.3814 | 0.5094 | -0.1280 |
| wave2a | core | full_observation | mean_water_deficit | full | 0.3060 | 0.5042 | -0.1982 |
| wave2a | core | no_rough_cost | survival_steps_mean | full | 93.8723 | 92.8407 | 1.0317 |
| wave2a | core | no_rough_cost | steps_to_first_needed_resource_mean | full | 10.3497 | 10.3570 | -0.0073 |
| wave2a | core | no_rough_cost | return_steps_to_seen_resource_mean | full | 10.3497 | 10.3570 | -0.0073 |
| wave2a | core | no_rough_cost | mean_energy_deficit | full | 0.3814 | 0.4014 | -0.0200 |
| wave2a | core | no_rough_cost | mean_water_deficit | full | 0.3060 | 0.3247 | -0.0187 |
| wave2a | relocation | full_observation | survival_steps_mean | full | 93.7160 | 69.5180 | 24.1980 |
| wave2a | relocation | full_observation | post_relocation_life_mean | full | 48.7160 | 24.5180 | 24.1980 |
| wave2a | relocation | full_observation | relocation_recovery_success_rate | full | 0.7040 | 0.0000 | 0.7040 |
| wave2a | relocation | full_observation | mean_energy_deficit | full | 0.3811 | 0.5089 | -0.1278 |
| wave2a | relocation | full_observation | mean_water_deficit | full | 0.3081 | 0.5037 | -0.1956 |
| wave2a | relocation | no_rough_cost | survival_steps_mean | full | 93.7160 | 92.6660 | 1.0500 |
| wave2a | relocation | no_rough_cost | post_relocation_life_mean | full | 48.7160 | 47.6660 | 1.0500 |
| wave2a | relocation | no_rough_cost | relocation_recovery_success_rate | full | 0.7040 | 0.1120 | 0.5920 |
| wave2a | relocation | no_rough_cost | relocation_recovery_steps_mean | full | 2.6935 | 4.8575 | -2.1640 |
| wave2a | relocation | no_rough_cost | mean_energy_deficit | full | 0.3811 | 0.4003 | -0.0191 |
| wave2a | relocation | no_rough_cost | mean_water_deficit | full | 0.3081 | 0.3233 | -0.0151 |

## Control Checks
- `full_slow_gt_zero`: `True`
- `no_slow_slow_near_zero`: `True`
- `no_fast_fast_near_zero`: `True`

## Known Limitations
- Wave 1 and assembled follow-up runs operated exclusively on `BiomeId.B` due to a defect in `_pick_biome` (numpy random choice interaction with str-Enum types).
- Current effects remain valid as within-biome comparisons. Biome generalization is not demonstrated here and is scheduled for v2-rc4.
- `full_observation` in `wave2a` showed a pathological pattern: `steps_to_first_needed_resource_mean` stayed missing across phases, `relocation_recovery_success_rate` stayed `0.0`, and relocation survival was worse than `full`.
- Root cause was not investigated inside frozen rc3. Candidate causes include metric events not firing when resources are visible from t=0, exploration/visibility interactions, or stale belief-map state after relocation. This is scheduled for v2-rc4 alongside `_pick_biome`.

## Verdict
- GO for v2 baseline freeze with documented limitations.