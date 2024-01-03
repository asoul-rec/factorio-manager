from .explorer import SavesExplorer
# References:
# [level.dat format] https://forums.factorio.com/viewtopic.php?t=8568
#   - someone gave a py script as parser, but only works <= v0.16
#   - a staff posted something but seems also outdated
#
# [[Technical] Save Format Questions] https://forums.factorio.com/viewtopic.php?t=47014
#   - people complains it's hard to know about the savefile format
#   - a staff said they didn't obscure it intentionally, but the format do changes fast between different versions
#
# [Text tutorial for re-enabling achievements after using the console]
# https://www.reddit.com/r/factorio/comments/rlprxh/text_tutorial_for_reenabling_achievements_after/
#   - someone create a static HTML page to pack/unpack the level.datX, but seems just a js app for zlib
#   - this indicates the new (>= 1.1, probably) saves uses zlib to compress the data in several parts
#
# [Factorio Server Manager] https://github.com/OpenFactorioServerManager/factorio-server-manager
#   - interesting tool, but not actively maintained
#   - commit/be35959144cd1ea2717cd1c4af0ad6f9c4cbc5d7 said "added compatibility to factorio >= 1.1.14 savefiles".
#     Files changed in this commit are a parser written with Go.
#   - Didn't read carefully, but seems can only load the levels-init.
#
# Other important facts discovered during testing by myself
#   - level-init.dat have the same format with level.datx but NOT compressed. Maybe used for "restart from beginning"
#   - If delete anything else and rename level-init.dat to level.dat, the game can start with no problem as a new game.
#   - If delete anything else except level.dat0 and level.datmetadata, we can preview the game but cannot start it.
#   - The game will always check the first 8 bytes (4 little-endian uint16) to get the version, even if it's insane
#   - The savefile will definitely change in v2.0. At least, the ticks will be stored as uint64 (uint32 now)
#   - There are 3 ticks value serialized adjacently in the savefile. Most of the time they are the same, but the middle
#     one is different in my SE save. If they are modified externally and load & save, the 3 ticks will increase
#     simultaneously. The time shown in the saves explorer is the 3rd tick. (the real meaning of them is unknown)
