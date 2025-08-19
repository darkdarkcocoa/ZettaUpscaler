"""
RRDBNet architecture implementation without basicsr dependency.
Compatible with Real-ESRGAN pretrained models.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class ResidualDenseBlock_5C(nn.Module):
    """Residual Dense Block with 5 Convolutions"""
    
    def __init__(self, num_feat=64, num_grow_ch=32):
        super(ResidualDenseBlock_5C, self).__init__()
        self.conv1 = nn.Conv2d(num_feat, num_grow_ch, 3, 1, 1)
        self.conv2 = nn.Conv2d(num_feat + num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv3 = nn.Conv2d(num_feat + 2 * num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv4 = nn.Conv2d(num_feat + 3 * num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv5 = nn.Conv2d(num_feat + 4 * num_grow_ch, num_feat, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(negative_slope=0.2, inplace=True)

    def forward(self, x):
        x1 = self.lrelu(self.conv1(x))
        x2 = self.lrelu(self.conv2(torch.cat((x, x1), 1)))
        x3 = self.lrelu(self.conv3(torch.cat((x, x1, x2), 1)))
        x4 = self.lrelu(self.conv4(torch.cat((x, x1, x2, x3), 1)))
        x5 = self.conv5(torch.cat((x, x1, x2, x3, x4), 1))
        return x5 * 0.2 + x


class RRDB(nn.Module):
    """Residual in Residual Dense Block"""
    
    def __init__(self, num_feat, num_grow_ch=32):
        super(RRDB, self).__init__()
        self.rdb1 = ResidualDenseBlock_5C(num_feat, num_grow_ch)
        self.rdb2 = ResidualDenseBlock_5C(num_feat, num_grow_ch)
        self.rdb3 = ResidualDenseBlock_5C(num_feat, num_grow_ch)

    def forward(self, x):
        out = self.rdb1(x)
        out = self.rdb2(out)
        out = self.rdb3(out)
        return out * 0.2 + x


class RRDBNet(nn.Module):
    """RRDBNet architecture for Real-ESRGAN"""
    
    def __init__(self, num_in_ch=3, num_out_ch=3, num_feat=64, 
                 num_block=23, num_grow_ch=32, scale=4):
        super(RRDBNet, self).__init__()
        self.scale = scale
        
        # First convolution
        self.conv_first = nn.Conv2d(num_in_ch, num_feat, 3, 1, 1)
        
        # RRDB blocks
        self.body = nn.ModuleList()
        for _ in range(num_block):
            self.body.append(RRDB(num_feat, num_grow_ch))
        
        # Trunk conv
        self.trunk_conv = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        
        # Upsampling
        if scale == 2:
            self.upconv1 = nn.Conv2d(num_feat, num_feat * 4, 3, 1, 1)
            self.pixel_shuffle = nn.PixelShuffle(2)
        elif scale == 4:
            self.upconv1 = nn.Conv2d(num_feat, num_feat * 4, 3, 1, 1)
            self.upconv2 = nn.Conv2d(num_feat, num_feat * 4, 3, 1, 1)
            self.pixel_shuffle = nn.PixelShuffle(2)
        
        # Final layers
        self.HRconv = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_last = nn.Conv2d(num_feat, num_out_ch, 3, 1, 1)
        
        # Activation
        self.lrelu = nn.LeakyReLU(negative_slope=0.2, inplace=True)

    def forward(self, x):
        # First conv
        feat = self.conv_first(x)
        body_feat = feat
        
        # RRDB blocks
        for block in self.body:
            body_feat = block(body_feat)
        
        # Trunk conv
        body_feat = self.trunk_conv(body_feat)
        feat = feat + body_feat
        
        # Upsampling
        if self.scale == 2:
            feat = self.lrelu(self.pixel_shuffle(self.upconv1(feat)))
        elif self.scale == 4:
            feat = self.lrelu(self.pixel_shuffle(self.upconv1(feat)))
            feat = self.lrelu(self.pixel_shuffle(self.upconv2(feat)))
        
        # Final conv
        out = self.conv_last(self.lrelu(self.HRconv(feat)))
        
        return out


def load_rrdbnet_from_state_dict(state_dict, scale=4, strict=False):
    """Load RRDBNet from state dict, inferring architecture parameters"""
    
    # Infer parameters from state dict
    num_feat = state_dict['conv_first.weight'].shape[0]
    num_in_ch = state_dict['conv_first.weight'].shape[1]
    
    # Count RRDB blocks
    num_block = 0
    for key in state_dict.keys():
        if key.startswith('body.') and '.rdb1.conv1.weight' in key:
            num_block += 1
    
    # Default to 23 if detection fails
    if num_block == 0:
        num_block = 23
    
    # Get grow channels from first RDB
    if 'body.0.rdb1.conv1.weight' in state_dict:
        num_grow_ch = state_dict['body.0.rdb1.conv1.weight'].shape[0]
    else:
        num_grow_ch = 32
    
    # Output channels
    num_out_ch = state_dict['conv_last.weight'].shape[0]
    
    # Create model
    model = RRDBNet(
        num_in_ch=num_in_ch,
        num_out_ch=num_out_ch,
        num_feat=num_feat,
        num_block=num_block,
        num_grow_ch=num_grow_ch,
        scale=scale
    )
    
    # Load weights
    model.load_state_dict(state_dict, strict=strict)
    
    return model