"""
SRVGGNetCompact architecture for Real-ESRGAN
Simplified version without basicsr dependency
"""

import torch
import torch.nn as nn


class SRVGGNetCompact(nn.Module):
    """VGG-style network for super-resolution"""
    
    def __init__(self, num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=16, upscale=4, act_type='prelu'):
        super(SRVGGNetCompact, self).__init__()
        self.num_in_ch = num_in_ch
        self.num_out_ch = num_out_ch
        self.num_feat = num_feat
        self.num_conv = num_conv
        self.upscale = upscale
        
        # Activation
        if act_type == 'prelu':
            self.act = nn.PReLU(num_parameters=1)
        else:
            self.act = nn.LeakyReLU(0.2, True)
        
        # First conv
        self.conv_first = nn.Conv2d(num_in_ch, num_feat, 3, 1, 1)
        
        # Body convs
        body = []
        for _ in range(num_conv):
            body.append(nn.Conv2d(num_feat, num_feat, 3, 1, 1))
            body.append(self.act)
        self.body = nn.Sequential(*body)
        
        # Last conv before upsampling
        self.conv_body = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        
        # Upsampling
        if upscale == 2:
            self.upsampler = nn.Sequential(
                nn.Conv2d(num_feat, num_feat * 4, 3, 1, 1),
                nn.PixelShuffle(2)
            )
        elif upscale == 3:
            self.upsampler = nn.Sequential(
                nn.Conv2d(num_feat, num_feat * 9, 3, 1, 1),
                nn.PixelShuffle(3)
            )
        elif upscale == 4:
            self.upsampler = nn.Sequential(
                nn.Conv2d(num_feat, num_feat * 4, 3, 1, 1),
                nn.PixelShuffle(2),
                nn.Conv2d(num_feat, num_feat * 4, 3, 1, 1),
                nn.PixelShuffle(2)
            )
        
        # Final conv
        self.conv_last = nn.Conv2d(num_feat, num_out_ch, 3, 1, 1)
        
    def forward(self, x):
        feat = self.act(self.conv_first(x))
        body_feat = self.body(feat)
        body_feat = self.conv_body(body_feat)
        
        # Skip connection
        feat = feat + body_feat
        
        # Upsampling
        feat = self.upsampler(feat)
        out = self.conv_last(feat)
        
        # Add input if same size (for residual learning)
        if self.upscale == 1:
            out = out + x
            
        return out