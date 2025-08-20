"""
Fixed SRVGGNetCompact architecture for Real-ESRGAN
Compatible with official Real-ESRGAN models
"""

import torch
import torch.nn as nn


class SRVGGNetCompact(nn.Module):
    """VGG-style network for super-resolution (fixed version)"""
    
    def __init__(self, num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4, act_type='prelu'):
        super(SRVGGNetCompact, self).__init__()
        
        self.num_in_ch = num_in_ch
        self.num_out_ch = num_out_ch
        self.num_feat = num_feat
        self.num_conv = num_conv
        self.upscale = upscale
        
        # First conv
        self.conv_first = nn.Conv2d(num_in_ch, num_feat, 3, 1, 1)
        
        # Body convs - must be registered individually for state_dict compatibility
        self.body = nn.ModuleList()
        for i in range(num_conv):
            self.body.append(nn.Conv2d(num_feat, num_feat, 3, 1, 1, bias=True))
            if act_type == 'prelu':
                self.body.append(nn.PReLU(num_parameters=num_feat))
            elif act_type == 'leakyrelu':
                self.body.append(nn.LeakyReLU(0.2, True))
        
        # Last conv before upsampling  
        self.conv_body = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        
        # Upsampling
        self.upsampler = nn.ModuleList()
        if upscale == 2:
            self.upsampler.append(nn.Conv2d(num_feat, num_feat * 4, 3, 1, 1))
            self.upsampler.append(nn.PixelShuffle(2))
        elif upscale == 3:
            self.upsampler.append(nn.Conv2d(num_feat, num_feat * 9, 3, 1, 1))
            self.upsampler.append(nn.PixelShuffle(3))
        elif upscale == 4:
            self.upsampler.append(nn.Conv2d(num_feat, num_feat * 4, 3, 1, 1))
            self.upsampler.append(nn.PixelShuffle(2))
            self.upsampler.append(nn.Conv2d(num_feat, num_feat * 4, 3, 1, 1))
            self.upsampler.append(nn.PixelShuffle(2))
        
        # High resolution conv
        self.conv_hr = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        
        # Final conv
        self.conv_last = nn.Conv2d(num_feat, num_out_ch, 3, 1, 1)
        
        # Activation for HR
        if act_type == 'prelu':
            self.act = nn.PReLU(num_parameters=num_feat)
        elif act_type == 'leakyrelu':
            self.act = nn.LeakyReLU(0.2, True)
        else:
            self.act = nn.Identity()
    
    def forward(self, x):
        # First conv
        feat = self.conv_first(x)
        body_feat = feat
        
        # Body
        for i in range(0, len(self.body), 2):
            body_feat = self.body[i](body_feat)
            if i + 1 < len(self.body):
                body_feat = self.body[i + 1](body_feat)
        
        body_feat = self.conv_body(body_feat)
        
        # Add skip connection
        feat = feat + body_feat
        
        # Upsampling
        for layer in self.upsampler:
            feat = layer(feat)
        
        # HR conv
        feat = self.conv_hr(feat)
        feat = self.act(feat)
        out = self.conv_last(feat)
        
        return out