# ScriptureNodes
A comfy UI custom node collection with the main purpose for automatized story generation as full workflow with a few utility nodes

# Samplers Save/Load Checkpoint Settings
I'm annoyed that nobody has created this logical thing, to save and load the settings of a checkpoint. Since we have so many different systems it's crazy to me that nobody implemented a thing like this, so I got annoyed enough to create them: 

All Sampler I create have the purpose to save and reload settings per checkpoint without hassle. The settings are automatically established on the Ksampler when interacting with the save load functionality of the Checkpoint.

## Save Load Functionality
Simply set a preset name or use the default, just click save to create an entry for the settings

To load the settings for a specific checkpoint, just select the checkpoint, and in the dropdown select the preset you want to load and click load.

## Checkpoint /w settings
this node is a regular Checkpoint with additional Ksampler settings to unify the settings onto one node.

## KSampler sync
When loading settings of the checkpoint this node applies the Ksampler settings automatically without wiring.
Unchecking the sync button prevents the node from syncing


# Future features:
- New only checkpoint data save load 
- Checkpoint save load with Pipe support
- Checkpoints with Lora Manager support
- Loading applies automatically when preset is changed or checkpoint is placed
- Enable Ksampler save settings Currently only the data on the checkpoint is saved.
