# Modifications copyright 2022 AI Singapore
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Original Copyright From PyTorch:
#
# Copyright (c) 2016-     Facebook, Inc            (Adam Paszke)
# Copyright (c) 2014-     Facebook, Inc            (Soumith Chintala)
# Copyright (c) 2011-2014 Idiap Research Institute (Ronan Collobert)
# Copyright (c) 2012-2014 Deepmind Technologies    (Koray Kavukcuoglu)
# Copyright (c) 2011-2012 NEC Laboratories America (Koray Kavukcuoglu)
# Copyright (c) 2011-2013 NYU                      (Clement Farabet)
# Copyright (c) 2006-2010 NEC Laboratories America (Ronan Collobert, Leon Bottou, Iain Melvin, Jason Weston)
# Copyright (c) 2006      Idiap Research Institute (Samy Bengio)
# Copyright (c) 2001-2004 Idiap Research Institute (Ronan Collobert, Samy Bengio, Johnny Mariethoz)
#
# From Caffe2:
#
# Copyright (c) 2016-present, Facebook Inc. All rights reserved.
#
# All contributions by Facebook:
# Copyright (c) 2016 Facebook Inc.
#
# All contributions by Google:
# Copyright (c) 2015 Google Inc.
# All rights reserved.
#
# All contributions by Yangqing Jia:
# Copyright (c) 2015 Yangqing Jia
# All rights reserved.
#
# All contributions by Kakao Brain:
# Copyright 2019-2020 Kakao Brain
#
# All contributions by Cruise LLC:
# Copyright (c) 2022 Cruise LLC.
# All rights reserved.
#
# All contributions from Caffe:
# Copyright(c) 2013, 2014, 2015, the respective contributors
# All rights reserved.
#
# All other contributions:
# Copyright(c) 2015, 2016 the respective contributors
# All rights reserved.
#
# Caffe2 uses a copyright model similar to Caffe: each contributor holds
# copyright over their contributions to Caffe2. The project versioning records
# all such contribution and copyright details. If a contributor wants to further
# mark their specific copyright on a particular contribution, they should
# indicate their copyright solely in the commit message of the change when it is
# committed.
#
# All rights reserved.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""Multi-scale RoI Align class to handle RoIAlign for Mask-RCNN"""

from typing import Dict, List, Optional, Tuple, Union
import torch
from torch import nn, Tensor
import torchvision
from peekingduck.pipeline.nodes.model.mask_rcnnv1.mask_rcnn_files import (
    roi_align,
    boxes as box_ops,
)


# copying result_idx_in_level to a specific index in result[]
# is not supported by ONNX tracing yet.
# _onnx_merge_levels() is an implementation supported by ONNX
# that merges the levels to the right indices
@torch.jit.unused
def _onnx_merge_levels(levels: Tensor, unmerged_results: List[Tensor]) -> Tensor:
    first_result = unmerged_results[0]
    dtype, device = first_result.dtype, first_result.device
    res = torch.zeros(
        (
            levels.size(0),
            first_result.size(1),
            first_result.size(2),
            first_result.size(3),
        ),
        dtype=dtype,
        device=device,
    )
    for level in range(len(unmerged_results)):
        index = torch.where(levels == level)[0].view(-1, 1, 1, 1)
        index = index.expand(
            index.size(0),
            unmerged_results[level].size(1),
            unmerged_results[level].size(2),
            unmerged_results[level].size(3),
        )
        res = res.scatter(0, index, unmerged_results[level])
    return res


def initLevelMapper(
    k_min: int,
    k_max: int,
    canonical_scale: int = 224,
    canonical_level: int = 4,
    eps: float = 1e-6,
):
    return LevelMapper(k_min, k_max, canonical_scale, canonical_level, eps)


class LevelMapper(object):
    """Determine which FPN level each RoI in a set of RoIs should map to based
    on the heuristic in the FPN paper.

    Args:
        k_min (int)
        k_max (int)
        canonical_scale (int)
        canonical_level (int)
        eps (float)
    """

    def __init__(
        self,
        k_min: int,
        k_max: int,
        canonical_scale: int = 224,
        canonical_level: int = 4,
        eps: float = 1e-6,
    ):
        self.k_min = k_min
        self.k_max = k_max
        self.s0 = canonical_scale
        self.lvl0 = canonical_level
        self.eps = eps

    def __call__(self, boxlists: List[Tensor]) -> Tensor:
        """
        Args:
            boxlists (list[BoxList])
        """
        # Compute level ids
        s = torch.sqrt(torch.cat([box_ops.box_area(boxlist) for boxlist in boxlists]))

        # Eqn.(1) in FPN paper
        target_lvls = torch.floor(
            self.lvl0 + torch.log2(s / self.s0) + torch.tensor(self.eps, dtype=s.dtype)
        )
        target_lvls = torch.clamp(target_lvls, min=self.k_min, max=self.k_max)
        return (target_lvls.to(torch.int64) - self.k_min).to(torch.int64)


class MultiScaleRoIAlign(nn.Module):
    """
    Multi-scale RoIAlign pooling, which is useful for detection with or without FPN.

    It infers the scale of the pooling via the heuristics specified in eq. 1
    of the `Feature Pyramid Network paper <https://arxiv.org/abs/1612.03144>`_.
    They keyword-only parameters ``canonical_scale`` and ``canonical_level``
    correspond respectively to ``224`` and ``k0=4`` in eq. 1, and
    have the following meaning: ``canonical_level`` is the target level of the pyramid from
    which to pool a region of interest with ``w x h = canonical_scale x canonical_scale``.

    Args:
        featmap_names (List[str]): the names of the feature maps that will be used
            for the pooling.
        output_size (List[Tuple[int, int]] or List[int]): output size for the pooled region
        sampling_ratio (int): sampling ratio for ROIAlign
        canonical_scale (int, optional): canonical_scale for LevelMapper
        canonical_level (int, optional): canonical_level for LevelMapper
    """

    __annotations__ = {
        "scales": Optional[List[float]],
        "map_levels": Optional[LevelMapper],
    }

    def __init__(
        self,
        featmap_names: List[str],
        output_size: Union[int, Tuple[int], List[int]],
        sampling_ratio: int,
        *,
        canonical_scale: int = 224,
        canonical_level: int = 4,
    ):
        super(MultiScaleRoIAlign, self).__init__()
        if isinstance(output_size, int):
            output_size = (output_size, output_size)
        self.featmap_names = featmap_names
        self.sampling_ratio = sampling_ratio
        self.output_size = tuple(output_size)
        self.scales = None
        self.map_levels = None
        self.canonical_scale = canonical_scale
        self.canonical_level = canonical_level

    def convert_to_roi_format(self, boxes: List[Tensor]) -> Tensor:
        concat_boxes = torch.cat(boxes, dim=0)
        device, dtype = concat_boxes.device, concat_boxes.dtype
        ids = torch.cat(
            [
                torch.full_like(
                    b[:, :1], i, dtype=dtype, layout=torch.strided, device=device
                )
                for i, b in enumerate(boxes)
            ],
            dim=0,
        )
        rois = torch.cat([ids, concat_boxes], dim=1)
        return rois

    def infer_scale(self, feature: Tensor, original_size: List[int]) -> float:
        # assumption: the scale is of the form 2 ** (-k), with k integer
        size = feature.shape[-2:]
        possible_scales: List[float] = []
        for s1, s2 in zip(size, original_size):
            approx_scale = float(s1) / float(s2)
            scale = 2 ** float(torch.tensor(approx_scale).log2().round())
            possible_scales.append(scale)
        assert possible_scales[0] == possible_scales[1]
        return possible_scales[0]

    def setup_scales(
        self,
        features: List[Tensor],
        image_shapes: List[Tuple[int, int]],
    ) -> None:
        assert len(image_shapes) != 0
        max_x = 0
        max_y = 0
        for shape in image_shapes:
            max_x = max(shape[0], max_x)
            max_y = max(shape[1], max_y)
        original_input_shape = (max_x, max_y)

        scales = [self.infer_scale(feat, original_input_shape) for feat in features]
        # get the levels in the feature map by leveraging the fact that the network always
        # downsamples by a factor of 2 at each level.
        lvl_min = -torch.log2(torch.tensor(scales[0], dtype=torch.float32)).item()
        lvl_max = -torch.log2(torch.tensor(scales[-1], dtype=torch.float32)).item()
        self.scales = scales
        self.map_levels = initLevelMapper(
            int(lvl_min),
            int(lvl_max),
            canonical_scale=self.canonical_scale,
            canonical_level=self.canonical_level,
        )

    def forward(
        self,
        x: Dict[str, Tensor],
        boxes: List[Tensor],
        image_shapes: List[Tuple[int, int]],
    ) -> Tensor:
        """
        Args:
            x (OrderedDict[Tensor]): feature maps for each level. They are assumed to have
                all the same number of channels, but they can have different sizes.
            boxes (List[Tensor[N, 4]]): boxes to be used to perform the pooling operation, in
                (x1, y1, x2, y2) format and in the image reference size, not the feature map
                reference. The coordinate must satisfy ``0 <= x1 < x2`` and ``0 <= y1 < y2``.
            image_shapes (List[Tuple[height, width]]): the sizes of each image before they
                have been fed to a CNN to obtain feature maps. This allows us to infer the
                scale factor for each one of the levels to be pooled.
        Returns:
            result (Tensor)
        """
        x_filtered = []
        for k, v in x.items():
            if k in self.featmap_names:
                x_filtered.append(v)
        num_levels = len(x_filtered)
        rois = self.convert_to_roi_format(boxes)
        if self.scales is None:
            self.setup_scales(x_filtered, image_shapes)

        scales = self.scales
        assert scales is not None

        if num_levels == 1:
            return roi_align(
                x_filtered[0],
                rois,
                output_size=self.output_size,
                spatial_scale=scales[0],
                sampling_ratio=self.sampling_ratio,
            )

        mapper = self.map_levels
        assert mapper is not None

        levels = mapper(boxes)

        num_rois = len(rois)
        num_channels = x_filtered[0].shape[1]

        dtype, device = x_filtered[0].dtype, x_filtered[0].device
        result = torch.zeros(
            (
                num_rois,
                num_channels,
            )
            + self.output_size,
            dtype=dtype,
            device=device,
        )

        tracing_results = []
        for level, (per_level_feature, scale) in enumerate(zip(x_filtered, scales)):
            idx_in_level = torch.where(levels == level)[0]
            rois_per_level = rois[idx_in_level]

            result_idx_in_level = roi_align.roi_align(
                per_level_feature,
                rois_per_level,
                output_size=self.output_size,
                spatial_scale=scale,
                sampling_ratio=self.sampling_ratio,
            )

            if torchvision._is_tracing():
                tracing_results.append(result_idx_in_level.to(dtype))
            else:
                # result and result_idx_in_level's dtypes are based on dtypes of different
                # elements in x_filtered.  x_filtered contains tensors output by different
                # layers.  When autocast is active, it may choose different dtypes for
                # different layers' outputs.  Therefore, we defensively match result's dtype
                # before copying elements from result_idx_in_level in the following op.
                # We need to cast manually (can't rely on autocast to cast for us) because
                # the op acts on result in-place, and autocast only affects out-of-place ops.
                result[idx_in_level] = result_idx_in_level.to(result.dtype)

        if torchvision._is_tracing():
            result = _onnx_merge_levels(levels, tracing_results)

        return result

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(featmap_names={self.featmap_names}, "
            f"output_size={self.output_size}, sampling_ratio={self.sampling_ratio})"
        )