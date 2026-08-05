# scripture Nodes
A comfy UI custom node collection with the main purpose for automatized story generation (SOON^tm) as full workflow with a few utility nodes

I got annoyed from all the node suits and base comfy that all noticed that comfy is lacking functionality, then developing it and then only covering half of the missing functionality - requiring more plugins that are - OFCOURSE - often not compatible for whatever reasons. 

Maybe I'm dumb but there is not much that someone can make wrong with a simple STRING or IMAGE type yet I far too often have issues slapping together something that is a 5 minut thing with other node systems but take days (as a full time employed guy) so I thought I can do it better. 

aaaaAAAAND here it is my slightly excentric node collection with the goal of providing a bit of compatibility to other systems as well:

## Checkpoint + Ksampler Save Load Settings
There are barely ones with settings storage, and none with an easy to use way that is thoroughly explained. Crazy nobody did that absurdly obvious thing

### Save Load Functionality
###### saving settings *pretty simple*: 
- select you're checkpoint, set the settings you like (yes ofcourse I created a checkpoint with Ksampler settings) 
- in Preset_name give the settings a name
- click save and it's stored.

###### load settings *even simpler*
- on preset_select select the one you want, done.

###### delete settings *almost as simple*
- select the preset you want to delete
- delete the preset name (for dummies: so there is no sign in the field)
- click save and it's deleted

(no rename option but I wanted to keep it as simple and natural as possible if you want to rename, use you're second hand and type a new one delete the old one)

*WhAt iS aLl ThAt SeTtInG sAvInG gOoD fOr iT's nO kSaMpLeR, DUH*
Guess what, smoothbrain, I have a Ksampler for that

### KSampler Sync
It's a classic Ksampler but with a SYNC toggle!
Does exactly what you think it does:
- It syncs the Ksampler to the Settings on the checkpoint loader
- It also provides the data that are saved for more minimalistic checkpoints
- It automatically get's the data when you load settings from a checkpoint

if you don't want that anymore, uncheck the sync toggle

### Checkpoint Minimal
Classic Checkpoint just with save load functionality

### Checkpoint Simple
Similar to minimal but also provide Checkpoint name and paths

### Checkpoint w/ Prompts
yes. This node suite also saves prompts with your checkpoints, so you don't even need to type the specific Quality tags for each of your different nodes.
The rest is similar to the other two.

### Checkpoint w/ Settings *need to get a better name, checkpoint\* maybe?*
This holds everything in one place you would want to save with your checkpoint (imo) Ksampler settings, checkpoint settings and prompts



Future features:
- want to implement a VAE check if a checkpoint is missing a VAE it provides a field for selecting one
- sending the prompts somewhere else
- adding conditioning so you don't have to do this for prompts yourself 


## Pipeline system
yeah I add a pipe system similar to levelpixel or easy use but less limited (srsly why has easy use pipeout a seed, but pipeIn not?!) and also supporting them 

### Checkpoint+Ksampler Piped
It's pretty much a Checkpoint w/ settings just with pipe output. 
Doesn't contain latent because triggers an update of the checkpoint and settings loading and comfy can't separate the update within a single node.



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
