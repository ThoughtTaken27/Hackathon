# Where Kettle fails: real mistakes from the dev folds

Each is the most confident wrong answer (out-of-fold, single mic) for a common confusion. 'Likely cause' was written before looking at examples; the sounds the encoder heard are printed so you can judge it.

## 1. Eating heard as Cooking
- Clip `DevNode1_ex69_23` (session s69, DevNode1, fold 2); 1 dev clips made this same mistake.
- Kettle's probabilities: Cooking 0.66, Washing up 0.31, Eating 0.01
- Sounds the encoder heard: Dishes, pots, and pans 0.24, Cupboard open or close 0.21, Glass 0.12
- Likely cause: Eating and cooking share plate, cutlery and tap sounds; the SINS authors note eating is hard to hear.

## 2. Cooking heard as Eating
- Clip `DevNode1_ex44_3` (session s44, DevNode1, fold 2); 2 dev clips made this same mistake.
- Kettle's probabilities: Eating 0.85, Washing up 0.12, Cooking 0.02
- Sounds the encoder heard: Dishes, pots, and pans 0.34, Cutlery, silverware 0.17, Glass 0.09
- Likely cause: Quiet stretches of cooking (stirring, waiting) sound like a meal at the table.

## 3. Moving about heard as Quiet
- Clip `DevNode1_ex87_13` (session s87, DevNode1, fold 4); 43 dev clips made this same mistake.
- Kettle's probabilities: Quiet 0.90, Moving about 0.07, Working (typing) 0.03
- Sounds the encoder heard: Silence 0.24, White noise 0.20, Rustle 0.10
- Likely cause: 'Moving about' is often a few soft footsteps or a door in an otherwise quiet room.

## 4. Quiet heard as Moving about
- Clip `DevNode1_ex10_2` (session s10, DevNode1, fold 3); 15 dev clips made this same mistake.
- Kettle's probabilities: Moving about 0.81, Working (typing) 0.15, Quiet 0.02
- Sounds the encoder heard: White noise 0.22, Hum 0.09, Silence 0.08
- Likely cause: A single bump or creak in a quiet room looks like someone moving about.

## 5. TV heard as Conversation
- Clip `DevNode2_ex229_151` (session s229, DevNode2, fold 4); 3 dev clips made this same mistake.
- Kettle's probabilities: Conversation 0.71, TV 0.25, Eating 0.03
- Sounds the encoder heard: Speech 0.84, Narration, monologue 0.23, Drawer open or close 0.10
- Likely cause: TV audio is mostly people talking; the model can't always tell a broadcast from a conversation.

## 6. Conversation heard as TV
- Clip `DevNode2_ex202_321` (session s202, DevNode2, fold 3); 7 dev clips made this same mistake.
- Kettle's probabilities: TV 0.86, Conversation 0.14, Moving about 0.01
- Sounds the encoder heard: Speech 0.77, Television 0.12, Radio 0.09
- Likely cause: A conversation with background music or a raised voice sounds like TV.

## 7. Washing up heard as Cooking
- Clip `DevNode1_ex58_18` (session s58, DevNode1, fold 2); 6 dev clips made this same mistake.
- Kettle's probabilities: Cooking 0.67, Washing up 0.30, Eating 0.01
- Sounds the encoder heard: Dishes, pots, and pans 0.24, Drawer open or close 0.11, Cupboard open or close 0.07
- Likely cause: Taps and clattering pans happen during both cooking and washing up.

## 8. Cooking heard as Washing up
- Clip `DevNode1_ex51_39` (session s51, DevNode1, fold 3); 22 dev clips made this same mistake.
- Kettle's probabilities: Washing up 0.97, Cooking 0.02, Eating 0.01
- Sounds the encoder heard: Drawer open or close 0.09, Inside, small room 0.07, Cupboard open or close 0.06
- Likely cause: Rinsing and running water during cooking sounds like washing up.

## 9. Working (typing) heard as Quiet
- Clip `DevNode2_ex260_16` (session s260, DevNode2, fold 4); 52 dev clips made this same mistake.
- Kettle's probabilities: Quiet 0.90, Working (typing) 0.06, Moving about 0.03
- Sounds the encoder heard: Silence 0.31, White noise 0.24, Rustle 0.06
- Likely cause: Slow or quiet typing leaves a window that is mostly room noise.

## 10. Working (typing) heard as Moving about
- Clip `DevNode1_ex238_32` (session s238, DevNode1, fold 2); 58 dev clips made this same mistake.
- Kettle's probabilities: Moving about 0.98, Washing up 0.01, Cooking 0.01
- Sounds the encoder heard: Walk, footsteps 0.40, Shuffle 0.26, Inside, small room 0.06
- Likely cause: Shuffling papers or moving a chair while working sounds like moving about.
