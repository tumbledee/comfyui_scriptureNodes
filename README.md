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

## Checkpoint Pipe
seed and latents need to be placed somewhere else at it reapplies the checkpoint with each change

## KSampler Sync
When loading settings of the checkpoint this node applies the Ksampler settings automatically without wiring.
Unchecking the sync button prevents the node from syncing


## Future Sampler features:
- ~~New only checkpoint data save load ~~
- ~~Checkpoint save load with Pipe support~~
- ~~Checkpoints with Lora Manager support~~
- ~~Loading applies automatically when preset is changed or checkpoint is placed~~
- ~~Enable Ksampler save settings Currently only the data on the checkpoint is saved.~~


# Scrolls
Scrolls are a collection of nodes to fully assemble a selfcontained automatically unfolding story.
The goal is to structure all the complex setup actions into one single node system

### Scroll of Character

### Scroll of Parties

### Scroll of Scenery

### Scroll of Narration

### Scroll of Collapse

### Scroll of Visuals

### Scroll of Quality
This node 

## Other Nodes
.. tba

## Features:
### Main Features: 
- Character Assembly
-   Simplyfied Character assembly
-   Layer Actions for character
- Story solver
- Visuals node
- Quality Node
- Narrative Collapse
-   
- Checkpoint node
### Future Features
- Multicharacter identifier (low first iteration, selection, continue with detection couple) 
-   SAM3 option
-   character detection implementation
- Full Checkpoint Settings node with detail selection
-   changes KSampler settings, quality values with checkpoint
-   Multi option selections
- Wildcard support
- Detection Couple Support
- Lora Support
- Lora Manager Support
- Prompt Control Support and full implementations
- 

### References and implementations
- Prompt Control https://github.com/asagi4/comfyui-prompt-control
- Dynamic Prompts
- Attention Couple https://github.com/pamparamm/ComfyUI-ppm
- SAM3
