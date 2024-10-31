
# PANav: Toward Privacy-Aware Robot Navigation via Vision-Language Models

This is our latest work. We proposed a new framework to achieve more privacy navigation performance in the public environment. Our work implemented in PyTorch.

**Author:** Bangguo Yu, Hamidreza Kasaei, and Ming Cao

**Affiliation:** University of Groningen

## Abstract

Navigating robots discreetly in human work environments while considering the possible privacy implications of robotic tasks presents significant challenges. Such scenarios are increasingly common, for instance, when robots transport sensitive objects that demand high levels of privacy in spaces crowded with human activities. While extensive research has been conducted on robotic path planning and social awareness, current robotic systems still lack the functionality of privacy-aware navigation in public environments.
To address this, we propose a new framework for mobile robot navigation that leverages vision-language models to incorporate privacy awareness into adaptive path planning. Specifically, all potential paths from the starting point to the destination are generated using the A* algorithm. Concurrently, the vision-language model is used to infer the optimal path for privacy-awareness, given the environmental layout and the navigational instruction. This approach aims to minimize the robot's exposure to human activities and preserve the privacy of the robot and its surroundings.
Experimental results on the S3DIS dataset demonstrate that our framework significantly enhances mobile robots' privacy awareness of navigation in human-shared public environments. Furthermore, we demonstrate the practical applicability of our framework by successfully navigating a robotic platform through real-world office environments. 

![image-20200706200822807](img/framework.png)

## Installation

The code has been tested only with Python 3.10.8.

1. Installing Dependencies

- Installing habitat-sim:
```
git clone https://github.com/ybgdgh/Privacy-Aware-Nav
pip install -r requirements.txt; 
```

2. Download S3DIS datasets:

#### Habitat Matterport
Download [HM3D](https://aihabitat.org/datasets/hm3d/) dataset using download utility and [instructions](https://github.com/facebookresearch/habitat-sim/blob/main/DATASETS.md#habitat-matterport-3d-research-dataset-hm3d):
```
python -m habitat_sim.utils.datasets_download --username <api-token-id> --password <api-token-secret> --uids hm3d_minival_v0.2
```

3. Download additional datasets

Download the [segmentation model](https://drive.google.com/file/d/1U0dS44DIPZ22nTjw0RfO431zV-lMPcvv/view?usp=share_link) in RedNet/model path.


## Setup
Clone the repository and install other requirements:
```
git clone https://github.com/ybgdgh/Privacy-Aware-Nav
cd Privacy-Aware-Nav/
pip install -r requirements.txt
```

### Setting up datasets
The code requires the datasets in a `data` folder in the following format (same as habitat-lab):
```
Co-NavGPT/
  data/
    scene_datasets/
    matterport_category_mappings.tsv
    object_norm_inv_perplexity.npy
    versioned_data
    objectgoal_hm3d/
        train/
        val/
        val_mini/
```


### For evaluation: 
For evaluating the framework, you need to setup your openai api keys in the 'chat_utils.py', then you can run the code in run_3.ipynb, run_4.ipynb, run_5a.ipynb.



## Demo Video

[video](https://sites.google.com/view/co-navgpt)
