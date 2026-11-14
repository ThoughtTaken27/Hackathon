# Where Kettle fails: real mistakes from the dev folds

Each is the most confident wrong answer (out-of-fold, single mic) for a common confusion. 'Likely cause' was written before looking at examples; the sounds the encoder heard are printed so you can judge it.

## 1. Eating heard as Cooking
- Clip `DevNode2_ex69_23` (session s69, DevNode2, fold 2); 8 dev clips made this same mistake.
- Kettle's probabilities: Cooking 0.88, Washing up 0.10, Eating 0.01
- Sounds the encoder heard: Dishes, pots, and pans 0.21, Cupboard open or close 0.17, Glass 0.09
- Likely cause: Eating and cooking share plate, cutlery and tap sounds; the SINS authors note eating is hard to hear.

## 2. Cooking heard as Eating
- Clip `DevNode2_ex44_3` (session s44, DevNode2, fold 2); 6 dev clips made this same mistake.
- Kettle's probabilities: Eating 0.86, Washing up 0.13, Cooking 0.01
- Sounds the encoder heard: Dishes, pots, and pans 0.28, Cutlery, silverware 0.13, Chink, clink 0.11
- Likely cause: Quiet stretches of cooking (stirring, waiting) sound like a meal at the table.

## 3. Moving about heard as Quiet
- Clip `DevNode1_ex87_13` (session s87, DevNode1, fold 4); 91 dev clips made this same mistake.
- Kettle's probabilities: Quiet 0.93, Moving about 0.05, Working (typing) 0.03
- Sounds the encoder heard: Silence 0.24, Rustle 0.10, Tick-tock 0.04
- Likely cause: 'Moving about' is often a few soft footsteps or a door in an otherwise quiet room.

## 4. Quiet heard as Moving about
- Clip `DevNode3_ex26_263` (session s26, DevNode3, fold 1); 35 dev clips made this same mistake.
- Kettle's probabilities: Moving about 0.91, Quiet 0.05, Working (typing) 0.02
- Sounds the encoder heard: Silence 0.06, Rustle 0.01, Music 0.01
- Likely cause: A single bump or creak in a quiet room looks like someone moving about.

## 5. TV heard as Conversation
- Clip `DevNode4_ex229_102` (session s229, DevNode4, fold 4); 12 dev clips made this same mistake.
- Kettle's probabilities: Conversation 0.88, TV 0.11, Eating 0.00
- Sounds the encoder heard: Speech 0.87, Silence 0.05, Television 0.02
- Likely cause: TV audio is mostly people talking; the model can't always tell a broadcast from a conversation.

## 6. Conversation heard as TV
- Clip `DevNode2_ex202_321` (session s202, DevNode2, fold 3); 14 dev clips made this same mistake.
- Kettle's probabilities: TV 0.89, Conversation 0.11, Moving about 0.01
- Sounds the encoder heard: Speech 0.77, Television 0.12, Radio 0.09
- Likely cause: A conversation with background music or a raised voice sounds like TV.

## 7. Washing up heard as Cooking
- Clip `DevNode3_ex63_12` (session s63, DevNode3, fold 1); 16 dev clips made this same mistake.
- Kettle's probabilities: Cooking 0.81, Washing up 0.19, Eating 0.00
- Sounds the encoder heard: Dishes, pots, and pans 0.20, Cutlery, silverware 0.04, Sizzle 0.02
- Likely cause: Taps and clattering pans happen during both cooking and washing up.

## 8. Cooking heard as Washing up
- Clip `DevNode2_ex46_83` (session s46, DevNode2, fold 2); 63 dev clips made this same mistake.
- Kettle's probabilities: Washing up 0.98, Cooking 0.01, Eating 0.01
- Sounds the encoder heard: Door 0.18, Dishes, pots, and pans 0.17, Drawer open or close 0.13
- Likely cause: Rinsing and running water during cooking sounds like washing up.

## 9. Working (typing) heard as Quiet
- Clip `DevNode2_ex260_16` (session s260, DevNode2, fold 4); 108 dev clips made this same mistake.
- Kettle's probabilities: Quiet 0.94, Working (typing) 0.03, Moving about 0.02
- Sounds the encoder heard: Silence 0.31, Rustle 0.06, Tick-tock 0.04
- Likely cause: Slow or quiet typing leaves a window that is mostly room noise.

## 10. Working (typing) heard as Moving about
- Clip `DevNode1_ex238_32` (session s238, DevNode1, fold 2); 100 dev clips made this same mistake.
- Kettle's probabilities: Moving about 0.99, Cooking 0.01, Washing up 0.00
- Sounds the encoder heard: Walk, footsteps 0.40, Shuffle 0.26, Drawer open or close 0.03
- Likely cause: Shuffling papers or moving a chair while working sounds like moving about.
