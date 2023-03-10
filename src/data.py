import os
from pathlib import Path
import re
import numpy as np

from s3fs import S3FileSystem

s3 = S3FileSystem()

import torch
import torchvision as tv

import webdataset as wds

def mixup_data(x, y, alpha=1.0):
    
    if alpha>0:
        lam = np.random.beta(alpha, alpha)
    else:
        lam = 1
    batch_size = x.size()[0]
    index = torch.randperm(batch_size).cuda()
    mixed_x = lam * x + (1 - lam) * x[index, :]
    y_a, y_b = y, y[index]
    return mixed_x, y_a, y_b, lam

def mixup_criterion(criterion, pred, y_a, y_b, lam):
    return lam * criterion(pred, y_a) + (1 - lam) * criterion(pred, y_b)

train_preproc = tv.transforms.Compose([
                    tv.transforms.ToTensor(),
                    tv.transforms.RandomResizedCrop(224, scale=(0.8, 1.0), 
                                                    ratio=(0.75, 1.33)),
                    tv.transforms.Normalize((0.485, 0.456, 0.406), 
                                            (0.229, 0.224, 0.225)),
                    tv.transforms.RandomRotation((-5., 5.)),
                    tv.transforms.RandomHorizontalFlip(),
                ])

val_preproc = tv.transforms.Compose([
                    tv.transforms.ToTensor(),
                    tv.transforms.Normalize((0.485, 0.456, 0.406), 
                                            (0.229, 0.224, 0.225)),
                    tv.transforms.Resize(224),
                    tv.transforms.CenterCrop(224),
                ])

def build_dataloader(data_dir, batch_size=128, num_workers=4, train=True):
    # get training environment
    local_rank = int(os.environ.get("LOCAL_RANK", 0))
    rank = int(os.environ.get("RANK", 0))
    world_size = int(os.environ.get("WORLD_SIZE", 1))
    local_size = int(os.environ.get("LOCAL_WORLD_SIZE", 1))
    is_s3 = data_dir.startswith("s3")
    
    '''paths = s3.ls(data_dir) if is_s3 else list(Path(data_dir).glob("*"))
    file_nums = [int(re.findall(r'\d+', Path(i).stem)[0]) for i in paths]
    base_name = Path(paths[0]).stem
    base_name = base_name.replace(re.findall(r'\d+', base_name)[0], '')
    files_per_rank = len(paths)//world_size'''
    
    trainsize = 1281167 if train else 50000 # number of images in imagenet
    num_batches = trainsize // (batch_size * world_size)
    base_name = "train_" if train else "val_"
    # start_file = files_per_rank * rank
    # end_file = files_per_rank * (rank + 1) - 1
    max_file = 2047 if train else 127
    if is_s3:
        wds_file_pattern = 'pipe:aws s3 cp {0}{{{1:04d}..{2:04d}}}.tar -'.format(os.path.join(data_dir, base_name), 0, max_file)
    else:
        wds_file_pattern = '{0}{{{1:04d}..{2:04d}}}.tar'.format(os.path.join(data_dir, base_name), 0, max_file)
    
    preproc = train_preproc if train else val_preproc
    
    dataset = wds.WebDataset(wds_file_pattern) \
                        .shuffle(True).decode("pil") \
                        .to_tuple("jpeg", "cls", "__key__").map_tuple(preproc, lambda x:x, lambda x:x) \
                        .batched(batch_size, partial=False)
    
    loader = wds.WebLoader(
            dataset, batch_size=None, shuffle=False, num_workers=num_workers,
        )
    
    loader = loader.repeat(2).slice(num_batches)
    
    loader.length = num_batches
    
    # return torch.utils.data.DataLoader(dataset, 
    #                                    num_workers=num_workers, 
    #                                    batch_size=batch_size,
    #                                    pin_memory=True,
    #                                    prefetch_factor=2)
    
    return loader