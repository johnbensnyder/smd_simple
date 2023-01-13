torchrun --nproc_per_node=4 src/train.py \
    --train_data_src s3://[your-bucket]/data/imagenet/train \
    --val_data_src s3://[your-bucket]/data/imagenet/val \
    --num_epochs 2 \
    --learning_rate 0.004 \
    --batch_size 128 \
    --precision float16 \
    --dataloader_workers 0