# Copyright 2021 AI Singapore
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
Draw bounding boxes over detected object
"""

from typing import Any, Dict
from peekingduck.pipeline.nodes.node import AbstractNode
from peekingduck.pipeline.nodes.model.tensorrtv1.detector import Detector


class Node(AbstractNode):
    """Draw bounding boxes on image.

    The draw bbox node uses the bboxes and, optionally, the bbox labels from the model
    predictions to draw the bbox predictions onto the image.
    For better understanding of the usecase, refer to the
    `object counting usecase <use_cases/object_counting.html>`_.

    Inputs:

        |img|

        |bboxes|

        |bbox_labels|

    Outputs:
        |none|

    Configs:
        show_labels (:obj:`bool`): **default = False**
            Show class label, e.g. "person", above bounding box
    """

    def __init__(self, config: Dict[str, Any] = None, **kwargs: Any) -> None:
        super().__init__(config, node_path=__name__, **kwargs)
        self.model = Detector(self.config)

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Function that reads the image input and returns the bboxes
        of the specified objects chosen to be detected

        Args:
            inputs (Dict): Dictionary of inputs with key "img"
        Returns:
            outputs (Dict): bbox output in dictionary format with keys
            "bboxes", "bbox_labels" and "bbox_scores"
        """

        bboxes, labels, scores = self.model.predict(inputs["img"])
        output = {
            "bboxes": bboxes,
            "bbox_scores": scores,
            "bbox_labels": labels,
        }

        return output
