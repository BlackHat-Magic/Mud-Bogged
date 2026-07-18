<div align="center">

# Datapacks

Generates Minecraft datapacks for a chosen version.

</div>


## Overview

Small datapacks to modify the vanilla play experience.

### Features

- [x] Bogged drop mud
- [x] Husks drop sand
- [x] Strays drop ice
- [ ] "Spirit Flight" Happy Ghast Harness Enchantment

## Quickstart

```sh
# build the pack
uv run datapacks bogged-drop-mud -f 48

# create the zip file
cd Bogged-Drop-Mud
zip --recurse-paths ../Bogged-Drop-Mud.zip .

# put in your datapack folder
cd ..
mv Bogged-Drop-Mud.zip ~/.local/share/PrismLauncher/instances/1.21.1/minecraft/saves/"New World"/datapacks/
```

