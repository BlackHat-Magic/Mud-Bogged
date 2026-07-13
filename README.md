<div align="center">

# Loot Table Datapacks

Simple loot table tweak datapacks

</div>


## Overview

Maked the bogged drop mud, husks drop sand, etc.

### Features

- [x] Bogged drop mud
- [x] Husks drop sand
- [x] Strays drop ice

## Quickstart

```sh
# build the pack
uv run loot-table-datapacks bogged-drop-mud -f 48

# create the zip file
cd Bogged-Drop-Mud
zip --recurse-paths ../"Bogged Drop Mud.zip" .

# put in your datapack folder
cd ..
mv "Bogged Drop Mud.zip" ~/.local/share/PrismLauncher/instances/1.21.1/minecraft/saves/"New World"/datapacks/
```

