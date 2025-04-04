_base_ = [
    '../../_base_/default_runtime.py'
]

#para
num_classes=1
img_scale=(512,512)
lr=0.0005
warmup_iters=500
max_epochs=12
lr_step=[8, 11]

# model settings
model = dict(
    type='Box2CdCondInst',
    backbone=dict(
        type='ResNet_Cd',
        depth=50,
        num_stages=4,
        out_indices=(0, 1, 2, 3),
        frozen_stages=1,
        zero_init_residual=False,
        norm_cfg=dict(type='BN', requires_grad=True),
        norm_eval=True,
        style='pytorch',
        init_cfg=dict(type='Pretrained', checkpoint='torchvision://resnet50')),
    neck=dict(
        type='FPN',
        in_channels=[256, 512, 1024, 2048],
        out_channels=256,
        start_level=1,
        add_extra_convs='on_output',  # use P5
        num_outs=5,
        relu_before_extra_convs=True),
    bbox_head=dict(
        type='CondInstBoxHead',
        num_classes=num_classes,
        in_channels=256,
        center_sampling=True,
        center_sample_radius=1.5,
        norm_on_bbox=True,
        stacked_convs=4,
        feat_channels=256,
        strides=[8, 16, 32, 64, 128],
        loss_cls=dict(
            type='FocalLoss',
            use_sigmoid=True,
            gamma=2.0,
            alpha=0.25,
            loss_weight=1.0),
        loss_bbox=dict(type='GIoULoss', loss_weight=1.0),
        loss_centerness=dict(
            type='CrossEntropyLoss', use_sigmoid=True, loss_weight=1.0)),
    mask_branch=dict(
        type='CondInstMaskBranch',
        in_channels=256,
        in_indices=[0, 1, 2],
        strides=[8, 16, 32],
        branch_convs=4,
        branch_channels=128,
        branch_out_channels=16),
    mask_head=dict(
        type='CondInstMaskHead',
        in_channels=16,
        in_stride=8,
        out_stride=4,
        dynamic_convs=3,
        dynamic_channels=8,
        disable_rel_coors=False,
        bbox_head_channels=256,
        sizes_of_interest=[64, 128, 256, 512, 1024],
        max_proposals=-1,
        topk_per_img=64,
        boxinst_enabled=True,
        bottom_pixels_removed=10,
        pairwise_size=3,
        pairwise_dilation=2,
        pairwise_color_thresh=0.3,
        pairwise_warmup=10000),
    # training and testing settings
    train_cfg=dict(
        assigner=dict(
            type='MaxIoUAssigner',
            pos_iou_thr=0.5,
            neg_iou_thr=0.4,
            min_pos_iou=0,
            ignore_iof_thr=-1),
        allowed_border=-1,
        pos_weight=-1,
        debug=False),
    test_cfg=dict(
        nms_pre=2000,
        min_bbox_size=0,
        score_thr=0.05,
        nms=dict(type='nms', iou_threshold=0.5),
        max_per_img=2000,
        output_segm=False))
# dataset settings
dataset_type = 'LEVIRcdDataset'
data_root = './data/LEVIR_CD_split/'
img_norm_cfg = dict(
    mean=[123.675, 116.28, 103.53], std=[58.395, 57.12, 57.375], to_rgb=True)
train_pipeline = [
    dict(type='LoadImageFromFile_cd'),
    dict(type='LoadAnnotations', with_bbox=True, with_mask=True),
    dict(type='Resize_cd', img_scale=img_scale, keep_ratio=True),
    dict(type='RandomFlip_cd', flip_ratio=0.5),
    dict(type='Normalize_cd', **img_norm_cfg),
    dict(type='Pad_cd', size_divisor=32),
    dict(type='DefaultFormatBundle_cd2'),
    dict(type='Collect_cd', keys=['img_1','img_2', 'gt_bboxes', 'gt_labels', 'gt_masks']),
]
test_pipeline = [
    dict(type='LoadImageFromFile_cd'),
    dict(
        type='MultiScaleFlipAug',
        img_scale=img_scale,
        flip=False,
        transforms=[
            dict(type='Resize', keep_ratio=True),
            dict(type='RandomFlip'),
            dict(type='Normalize', **img_norm_cfg),
            dict(type='Pad', size_divisor=32),
            dict(type='ImageToTensor', keys=['img_1','img_2']),
            dict(type='Collect_cd', keys=['img_1','img_2']),
        ])
]
data = dict(
    samples_per_gpu=2,
    workers_per_gpu=2,
    train=dict(
        type=dataset_type,
        ann_file=data_root + 'annotations/LEVIR_train.json',
        img_prefix=data_root + 'train',
        pipeline=train_pipeline),
    val=dict(
        type=dataset_type,
        ann_file=data_root + 'annotations/LEVIR_val.json',
        img_prefix=data_root + 'val',
        pipeline=test_pipeline),
    test=dict(
        type=dataset_type,
        ann_file=data_root + 'annotations/LEVIR_val.json',
        img_prefix=data_root + 'val',
        pipeline=test_pipeline))

optimizer = dict(type='SGD', lr=lr, momentum=0.9, weight_decay=0.0001)
optimizer_config = dict(grad_clip=None)
# learning policy
lr_config = dict(
    policy='step',
    warmup='linear',
    warmup_iters=warmup_iters,
    warmup_ratio=0.001,
    step=lr_step)

runner = dict(type='EpochBasedRunner', max_epochs=max_epochs)
evaluation = dict(interval=1, metric=['segm'])
checkpoint_config = dict(interval=1)
work_dir = './work_dirs/box2cd_inst_levir_r50_fpn'
load_from = None
resume_from = None
