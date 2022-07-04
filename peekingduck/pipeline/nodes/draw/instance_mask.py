# Copyright 2022 AI Singapore
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

"""
Draws instance segmentation masks.
"""

import colorsys
import logging
from random import randint
from typing import Any, Dict, List, Tuple, Union, cast

import cv2
import numpy as np

from peekingduck.pipeline.nodes.abstract_node import AbstractNode
from peekingduck.pipeline.nodes.base import ThresholdCheckerMixin
from peekingduck.pipeline.nodes.draw.utils.constants import (
    SATURATION_STEPS,
    SATURATION_MINIMUM,
    ALPHA,
    CLASS_COLORS,
    DEFAULT_CLASS_COLOR,
)


class Node(
    AbstractNode, ThresholdCheckerMixin
):  # pylint: disable=too-few-public-methods
    """Draws instance segmentation masks on image.

    The :mod:`draw.mask` node draws instance segmentation masks onto the
    detected object instances.

    Inputs:
        |img_data|

        |masks_data|

        |bbox_labels_data|

        |bbox_scores_data|

    Outputs:
        |img_data|

    Configs:
        instance_color_scheme (:obj:`str`): **{"random", "hue_family"}, 
            default="hue_family"** |br|
            This defines what colors to use for the standard masks.
            "hue_family": use the same hue for each instance belonging to
            the same class, but with a slightly different saturation.
            "random": use a random color for all instances.

        effect (:obj:`dict`): **{"standard_mask", "contrast", "brightness",
            "gamma_correction", "blur", "mosaic"}**. |br|
            This defines the effect (if any) to apply to either the masked or
            unmasked areas of the image. |br|
            "standard_mask" (:obj:`bool`): Draws a "standard" instance
            segmentation mask. |br|
            "contrast" (:obj:`float`): **[0, 3], default = 1**. Adjusts
            contrast using this value as the "alpha" parameter. |br|
            "brightness" (:obj:`int`): **[-100, 100], default = 0**. Adjusts
            brightness using this value as the "beta" parameter. |br|
            "gamma_correction" (:obj:`float`): Adjusts gamma using this value
            as the "gamma" parameter. |br|
            "blur" (:obj:`int`): Blurs the masks using this value as the
            "blur_kernel_size" parameter. Larger values gives more intense
            blurring. |br|
            "mosaic" (:obj:`int`): Mosaics the masks using this value as the
            resolution of a mosaic filter (width |times| height). The number
            corresponds to the number of rows and columns used to create a
            mosaic. For example, the setting (``mosaic: 25``) creates a
            :math:`25 \\times 25` mosaic filter. Increasing the number
            increases the intensity of pixelization over an area. |br|

        effect_area (:obj:`str`): **{"objects", "background"}, 
            default = "objects"**. |br|
            This defines where the effect should be applied. |br|
            "objects": the effect is applied to the masked areas of the image. |br|
            "background": the effect is applied to the unmasked areas of the image. |br|

        contours (:obj:`dict`): **{"show", "thickness"}**. |br|
            "show" (:obj:`bool`): **default = False**. |br|
                This determines whether to show the contours of the masks.
            "thickness" (:obj:`int`): **default = 3**. |br|
                This defines the thickness of the contours.
    """

    def __init__(self, config: Dict[str, Any] = None, **kwargs: Any) -> None:
        super().__init__(config, node_path=__name__, **kwargs)

        self.class_instance_color_state: Dict[str, Tuple[int, int, int]] = {}
        self._validate_configs()

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Reads an input image and returns the image (1) with the instance
        segmentation masks drawn over the detected object instances, or
        (2) with a visual effect mask applied to it. The visual effect can be
        applied to the masked areas of the image or to the unmasked areas.

        Args:
            inputs (dict): Dictionary of inputs with keys "img", "masks,
            "bbox_labels", "bbox_scores".

        Returns:
            outputs (dict): Output in dictionary format with key "img".
        """
        for effect in self.config["effect"]:
            if self.config['effect'][effect] is not None:
                if effect == "standard_mask":
                    output_img = self._draw_standard_masks(
                        inputs["img"],
                        inputs["masks"],
                        inputs["bbox_labels"],
                        inputs["bbox_scores"],
                    )
                else:
                    output_img = self._mask_apply_effect(
                        inputs["img"],
                        inputs["masks"],
                        effect,
                    )
                break   # only apply the first effect

        return {"img": output_img}

    def _validate_configs(self):
        self.check_valid_choice("instance_color_scheme", {"random", "hue_family"})

        effects = ("standard_mask", "contrast", "brightness", "gamma_correction", "blur", "mosaic")
        has_effect = False
        for k, v in self.config["effect"].items():
            if k not in effects:
                raise ValueError(f"{k} must be one of {effects}")
            if v:
                has_effect = True

        if not has_effect:
            raise ValueError("At least one effect must be enabled in the config.")

        self.check_valid_choice("effect_area", {"objects", "background"})

        self._check_type(self.config["effect"]["contrast"], float)
        self._check_number_range(self.config["effect"]["contrast"], "[0, 3]")
        self._check_type(self.config["effect"]["brightness"], int)
        self._check_number_range(self.config["effect"]["brightness"], "[-100, 100]")
        self._check_type(self.config["effect"]["gamma_correction"], float)
        self._check_number_range(self.config["effect"]["gamma_correction"], "[0, +inf]")
        self._check_type(self.config["effect"]["blur"], int)
        self._check_number_range(self.config["effect"]["blur"], "[1, +inf]")
        self._check_type(self.config["effect"]["mosaic"], int)
        self._check_number_range(self.config["effect"]["mosaic"], "[1, +inf]")
        self._check_type(self.config["contours"]["show"], bool)
        self._check_type(self.config["contours"]["thickness"], int)
        self._check_number_range(self.config["contours"]["thickness"], "[1, +inf]")

    def _check_type(self, var: Any, var_type: Any) -> None:
        if var is not None and not isinstance(var, var_type):
            raise ValueError(
                f"Config: '{var}' must be a {var_type.__name__} value."
            )

    def _check_number_range(self, var: Any, number_range: List[Union[str, int]]) -> None:
        if var is not None:
            lower, upper = [float(value.strip()) for value in number_range[1:-1].split(",")]
            if not lower <= var <= upper:
                raise ValueError(
                    f"Config: '{var}' must be within the range of {number_range}."
                )

    def _draw_standard_masks(  # pylint: disable-msg=too-many-locals
        self,
        image: np.ndarray,
        masks: np.ndarray,
        bbox_labels: np.ndarray,
        bbox_scores: np.ndarray,
    ) -> np.ndarray:
        """Draws instance segmentation masks over detected objects.

        Args:
            image (numpy.ndarray): Input image.
            masks (numpy.ndarray): NumPy array of binary (0/1) masks, one mask
                for each detected object, in the same order as bbox_labels.
            bbox_labels (numpy.ndarray): NumPy array of strings representing
                the labels of detected objects. The order corresponds to
                ``masks``.
            bbox_scores (numpy.ndarray): Mask confidence scores. The order
                corresponds to ``masks``.

        Returns:
            numpy.ndarray: Input image with instance segmentation masks
                applied to it.
        """
        full_sized_canvas = np.zeros(image.shape, image.dtype)
        ret_image = image.copy()

        # draw masks in ascending order of confidence scores, on the
        # assumption that objects with higher scores are positioned nearer to
        # the camera c.f. objects with lower scores
        scores_with_indexes = [(score, i) for i, score in enumerate(bbox_scores)]
        scores_with_indexes.sort(key=lambda x: x[0])

        for _, index in scores_with_indexes:
            color = self._get_instance_color(bbox_labels[index])

            # convert colorspace from RGB to BGR to use in OpenCV
            color_bgr = color[::-1]
            full_sized_canvas[:, :] = color_bgr

            coloured_seg_mask = cv2.bitwise_and(
                full_sized_canvas, full_sized_canvas, mask=masks[index]
            )
            masked_area = cv2.bitwise_and(image, image, mask=masks[index])
            masked_area_colored = cv2.addWeighted(
                coloured_seg_mask, ALPHA, masked_area, 1 - ALPHA, 0
            )

            # get the inverted mask i.e. image outside of the masked area
            mask_inv = 1 - masks[index]
            # remove masked area from image to be returned
            ret_image = cv2.bitwise_and(ret_image, ret_image, mask=mask_inv)
            ret_image = cv2.add(ret_image, masked_area_colored)

            if self.config["contours"]["show"]:
                ret_image = self._draw_contours_single_mask(
                    masks, index, ret_image, color
                )

        return ret_image

    def _get_instance_color(self, instance_class: str) -> Tuple[int, int, int]:
        """Returns color to use for next segmentation instance, depending on
        chosen color scheme:

        "random" - Random color.

        "hue_family" - Each object class uses a certain pre-assigned hue. Then
            each new instance will use the same hue, but with a slightly
            different saturation.

        Args:
            instance_class (str): Class of detected object.

        Returns:
            Tuple[int,int,int]: Color to use for next instance, in RGB.
        """
        if self.config["instance_color_scheme"] == "random":
            color_hsv = (randint(0, 179), randint(100, 255), 255)
            color = self._hsv_to_rgb(color_hsv)
        elif self.config["instance_color_scheme"] == "hue_family":
            color = self.class_instance_color_state.get(instance_class)  # type: ignore
            if not color:
                color = CLASS_COLORS.get(instance_class, DEFAULT_CLASS_COLOR)
            else:
                color_hsv = self._rgb_to_hsv(color)
                # we use a minimum saturation of 100 to avoid too light colors,
                # thus we increment saturation by step size of (256-100)/8.
                saturation = (color_hsv[1] + (256 - SATURATION_MINIMUM) / SATURATION_STEPS) % 256
                if saturation < SATURATION_MINIMUM:
                    saturation += SATURATION_MINIMUM
                color_hsv = (color_hsv[0], int(saturation), color_hsv[2])
                color = self._hsv_to_rgb(color_hsv)
            self.class_instance_color_state.update({instance_class: color})

        return color

    def _draw_contours_single_mask(
        self,
        masks: np.ndarray,
        index: int,
        image: np.ndarray,
        instance_color: Tuple[int, int, int],
    ) -> np.ndarray:
        """Draws the contour around a single instance segmentation mask."""
        ret_image = image.copy()
        contour, _ = cv2.findContours(masks[index], cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # use a darker/lighter saturation of instance hue for the
        # contour so that it is more visible
        hsv = Node._rgb_to_hsv(instance_color)
        contour_color_hsv = (hsv[0], int((hsv[1] + 127) % 256), hsv[2])
        contour_color_rgb = Node._hsv_to_rgb(contour_color_hsv)
        contour_color_bgr = contour_color_rgb[::-1]
        cv2.drawContours(
            ret_image,
            contour,
            -1,
            contour_color_bgr,
            self.config["contours"]["thickness"],
        )

        return ret_image

    def _draw_contours_all_masks(
        self,
        masks: np.ndarray,
        image: np.ndarray,
        contour_color: Tuple[int, int, int] = (128, 128, 128),
    ) -> np.ndarray:
        """Draws contours around all instance segmentation masks."""
        ret_image = image.copy()
        contour_color_bgr = contour_color[::-1]
        for i in range(masks.shape[0]):
            contour, _ = cv2.findContours(masks[i], cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(
                ret_image,
                contour,
                -1,
                contour_color_bgr,
                self.config["contours"]["thickness"],
            )

        return ret_image

    def _mask_apply_effect(self, image: np.ndarray, masks: np.ndarray, effect: str) -> np.ndarray:
        """Applies the chosen effect to the image and masks."""
        combined_masks = np.zeros(image.shape[:2], dtype="uint8")
        # combine all the individual masks
        for mask in masks:
            np.putmask(combined_masks, mask, 1)

        if self.config["effect_area"] == "objects":
            effect_area = combined_masks
        else:  # effect_area == "background"
            effect_area = 1 - combined_masks

        if effect in ["contrast", "brightness"]:
            full_image_with_effect = self._adjust_contrast_brightness(image, effect)
        elif effect == "gamma_correction":
            full_image_with_effect = self._gamma_correction(image)
        elif effect == "blur":
            full_image_with_effect = cv2.blur(
                image,
                (self.config["effect"]["blur"], self.config["effect"]["blur"]),
            )
        elif effect == "mosaic":
            full_image_with_effect = self._mosaic_image(image)

        effect_area_with_effect = cv2.bitwise_and(
            full_image_with_effect, full_image_with_effect, mask=effect_area
        )
        # get the inverted mask
        effect_area_inv = 1 - effect_area
        # remove effect area from original image
        image_empty_effect_area = cv2.bitwise_and(image, image, mask=effect_area_inv)
        # add both images together
        ret_image = cv2.add(image_empty_effect_area, effect_area_with_effect)

        if self.config["contours"]["show"]:
            ret_image = self._draw_contours_all_masks(masks, ret_image)

        return ret_image

    def _adjust_contrast_brightness(self, image: np.ndarray, effect: str) -> np.ndarray:
        if effect == "contrast":
            alpha = self.config["effect"]["contrast"]
            beta = 0
        else:    # i.e. effect == "brightness"
            alpha = 1
            beta = self.config["effect"]["brightness"]

        return cv2.convertScaleAbs(
                image, alpha=alpha, beta=beta
            )

    def _gamma_correction(self, image: np.ndarray) -> np.ndarray:
        lookup_table = np.empty((1, 256), np.uint8)
        for i in range(256):
            lookup_table[0, i] = np.clip(
                pow(i / 255.0, self.config["effect"]["gamma_correction"]) * 255.0, 0, 255
            )

        image_gamma_corrected = cv2.LUT(image, lookup_table)

        return image_gamma_corrected

    def _mosaic_image(self, image: np.ndarray) -> np.ndarray:
        height, width = image.shape[:2]
        ret_image = cv2.resize(
            image,
            (self.config["effect"]["mosaic"], self.config["effect"]["mosaic"]),
            interpolation=cv2.INTER_LANCZOS4,
        )
        ret_image = cv2.resize(
            ret_image, (width, height), interpolation=cv2.INTER_NEAREST
        )

        return ret_image

    @staticmethod
    def _rgb_to_hsv(rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
        hsv_norm = colorsys.rgb_to_hsv(*[x / 255 for x in rgb])
        hsv = (int(hsv_norm[0] * 127), int(hsv_norm[1] * 255), int(hsv_norm[2] * 255))

        return hsv

    @staticmethod
    def _hsv_to_rgb(hsv: Tuple[int, int, int]) -> Tuple[int, int, int]:
        rgb_norm = colorsys.hsv_to_rgb(hsv[0] / 127, hsv[1] / 255, hsv[2] / 255)
        rgb = cast(Tuple[int, int, int], tuple((int(x * 255) for x in rgb_norm)))

        return rgb