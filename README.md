<div align="center">

# Datapacks

Generates Minecraft datapacks for a chosen version.

</div>


## Overview

Small datapacks to modify the vanilla play experience.

### Bogged Drop Mud

A datapack for Minecraft 1.21+ that gives the Bogged mob a chance to drop Mud or Moss blocks when killed. It also gives it a small chance to drop an Azalea Bush, Flowering Azalea Bush, Mangrove Propagule, Glowberry, Red Mushroom, or Brown Mushroom.

### Husk Drop Sand

A datapack for Minecraft 1.13+ that gives the Husk mob a chance to drop Sand or Red Sand blocks when killed. It also gives it a small chance to drop a Dead Bush, Cactus, Cactus Flower, or Sugarcane. Cactus flowers are gated to Minecraft 1.21.5+.

### Stray Drop Ice

A datapack for Minecraft 1.13+ that gives the Stray mob a chance to drop Snowballs, Snow Blocks, or Ice blocks when killed. It also gives it a small chance to drop a Packed Ice, Blue Ice, or Powder Snow Bucket. Powder Snow Buckets are gated to Minecraft 1.17+.

### Spirit Flight

A datapack for Minecraft 1.21.6+ that introduces a new enchantment called "Spirit Flight" for the Happy Ghast Harness that increases the equipped Happy Ghast's speed. It can be obtained on Enchanted Books through the Enchanting Table at about the same rarity as Infinity or Silk Touch. It can also be obtained from chests in Bastions (average approx. two books or harnesses per Bastion) or from Piglin Bartering (about the same rarity as Fire Resistance Potions).

## Quickstart

```sh
# build the pack (and its distributable zip)
uv run datapacks bogged-drop-mud -f 48 -z

# put the zip in your datapack folder
mv bogged-drop-mud_0.1.1+mc1.21-1.21.1.zip ~/.local/share/PrismLauncher/instances/1.21.1/minecraft/saves/"New World"/datapacks/
```

