.. currentmodule:: peekingduck

.. _glossary:

Glossary of Common Resources, Information
=========================================

This glossary consolidates all the peripheral information required for a deeper
understanding of how PeekingDuck works.


.. glossary::

    keypoint indices
        This table provides the associated indices for each keypoint

        +-----------------+---------------+-----------------+----------------+-----------------+---------------+-----------------+---------------+
        | Keypoint number | Keypoint name | Keypoint number | Keypoint name  | Keypoint number | Keypoint name | Keypoint number | Keypoint name |
        +=================+===============+=================+================+=================+===============+=================+===============+
        | 0               | nose          | 5               | left shoulder  | 10              | right wrist   | 15              | left ankle    |
        +-----------------+---------------+-----------------+----------------+-----------------+---------------+-----------------+---------------+
        | 1               | left eye      | 6               | right shoulder | 11              | left hip      | 16              | right ankle   |
        +-----------------+---------------+-----------------+----------------+-----------------+---------------+-----------------+---------------+
        | 2               | right eye     | 7               | left elbow     | 12              | right hip     |                 |               |
        +-----------------+---------------+-----------------+----------------+-----------------+---------------+-----------------+---------------+
        | 3               | leftEar       | 8               | right elbow    | 13              | left knee     |                 |               |
        +-----------------+---------------+-----------------+----------------+-----------------+---------------+-----------------+---------------+
        | 4               | right ear     | 9               | left wrist     | 14              | right knee    |                 |               |
        +-----------------+---------------+-----------------+----------------+-----------------+---------------+-----------------+---------------+


    object detection indices
        This table provides the associated indices for each class in object detectors.

        +---------------+---------------+-----------------------+----------------+---------------+-----------------------+
        | Class name    | YOLO Class ID | EfficientDet Class ID | Class name     | YOLO Class ID | EfficientDet Class ID |
        +===============+===============+=======================+================+===============+=======================+
        | person        | 0             | 0                     | elephant       | 20            | 21                    |
        +---------------+---------------+-----------------------+----------------+---------------+-----------------------+
        | bicycle       | 1             | 1                     | bear           | 21            | 22                    |
        +---------------+---------------+-----------------------+----------------+---------------+-----------------------+
        | car           | 2             | 2                     | zebra          | 22            | 23                    |
        +---------------+---------------+-----------------------+----------------+---------------+-----------------------+
        | motorcycle    | 3             | 3                     | giraffe        | 23            | 24                    |
        +---------------+---------------+-----------------------+----------------+---------------+-----------------------+
        | aeroplane     | 4             | 4                     | backpack       | 24            | 26                    |
        +---------------+---------------+-----------------------+----------------+---------------+-----------------------+
        | bus           | 5             | 5                     | umbrella       | 25            | 27                    |
        +---------------+---------------+-----------------------+----------------+---------------+-----------------------+
        | train         | 6             | 6                     | handbag        | 26            | 30                    |
        +---------------+---------------+-----------------------+----------------+---------------+-----------------------+
        | truck         | 7             | 7                     | tie            | 27            | 31                    |
        +---------------+---------------+-----------------------+----------------+---------------+-----------------------+
        | boat          | 8             | 8                     | suitcase       | 28            | 32                    |
        +---------------+---------------+-----------------------+----------------+---------------+-----------------------+
        | traffic light | 9             | 9                     | frisbee        | 29            | 33                    |
        +---------------+---------------+-----------------------+----------------+---------------+-----------------------+
        | fire hydrant  | 10            | 10                    | skis           | 30            | 34                    |
        +---------------+---------------+-----------------------+----------------+---------------+-----------------------+
        | stop sign     | 11            | 12                    | snowboard      | 31            | 35                    |
        +---------------+---------------+-----------------------+----------------+---------------+-----------------------+
        | parking meter | 12            | 13                    | sports ball    | 32            | 36                    |
        +---------------+---------------+-----------------------+----------------+---------------+-----------------------+
        | bench         | 13            | 14                    | kite           | 33            | 37                    |
        +---------------+---------------+-----------------------+----------------+---------------+-----------------------+
        | bird          | 14            | 15                    | baseball bat   | 34            | 38                    |
        +---------------+---------------+-----------------------+----------------+---------------+-----------------------+
        | cat           | 15            | 16                    | baseball glove | 35            | 39                    |
        +---------------+---------------+-----------------------+----------------+---------------+-----------------------+
        | dog           | 16            | 17                    | skateboard     | 36            | 40                    |
        +---------------+---------------+-----------------------+----------------+---------------+-----------------------+
        | horse         | 17            | 18                    | surfboard      | 37            | 41                    |
        +---------------+---------------+-----------------------+----------------+---------------+-----------------------+
        | sheep         | 18            | 19                    | tennis racket  | 38            | 42                    |
        +---------------+---------------+-----------------------+----------------+---------------+-----------------------+
        | cow           | 19            | 20                    | bottle         | 39            | 43                    |
        +---------------+---------------+-----------------------+----------------+---------------+-----------------------+

        +--------------+---------------+-----------------------+--------------+---------------+-----------------------+
        + Class name   | YOLO Class ID | EfficientDet Class ID | Class name   | YOLO Class ID | EfficientDet Class ID |
        +==============+===============+=======================+==============+===============+=======================+
        + wine glass   | 40            | 45                    | dining table | 60            | 66                    |
        +--------------+---------------+-----------------------+--------------+---------------+-----------------------+
        + cup          | 41            | 46                    | toilet       | 61            | 69                    |
        +--------------+---------------+-----------------------+--------------+---------------+-----------------------+
        + fork         | 42            | 47                    | tv           | 62            | 71                    |
        +--------------+---------------+-----------------------+--------------+---------------+-----------------------+
        + knife        | 43            | 48                    | laptop       | 63            | 72                    |
        +--------------+---------------+-----------------------+--------------+---------------+-----------------------+
        + spoon        | 44            | 49                    | mouse        | 64            | 73                    |
        +--------------+---------------+-----------------------+--------------+---------------+-----------------------+
        + bowl         | 45            | 50                    | remote       | 65            | 74                    |
        +--------------+---------------+-----------------------+--------------+---------------+-----------------------+
        + banana       | 46            | 51                    | keyboard     | 66            | 75                    |
        +--------------+---------------+-----------------------+--------------+---------------+-----------------------+
        + apple        | 47            | 52                    | cell phone   | 67            | 76                    |
        +--------------+---------------+-----------------------+--------------+---------------+-----------------------+
        + sandwich     | 48            | 53                    | microwave    | 68            | 77                    |
        +--------------+---------------+-----------------------+--------------+---------------+-----------------------+
        + orange       | 49            | 54                    | oven         | 69            | 78                    |
        +--------------+---------------+-----------------------+--------------+---------------+-----------------------+
        + broccoli     | 50            | 55                    | toaster      | 70            | 79                    |
        +--------------+---------------+-----------------------+--------------+---------------+-----------------------+
        + carrot       | 51            | 56                    | sink         | 71            | 80                    |
        +--------------+---------------+-----------------------+--------------+---------------+-----------------------+
        + hot dog      | 52            | 57                    | refrigerator | 72            | 81                    |
        +--------------+---------------+-----------------------+--------------+---------------+-----------------------+
        + pizza        | 53            | 58                    | book         | 73            | 83                    |
        +--------------+---------------+-----------------------+--------------+---------------+-----------------------+
        + donut        | 54            | 59                    | clock        | 74            | 84                    |
        +--------------+---------------+-----------------------+--------------+---------------+-----------------------+
        + cake         | 55            | 60                    | vase         | 75            | 85                    |
        +--------------+---------------+-----------------------+--------------+---------------+-----------------------+
        + chair        | 56            | 61                    | scissors     | 76            | 86                    |
        +--------------+---------------+-----------------------+--------------+---------------+-----------------------+
        + couch        | 57            | 62                    | teddy bear   | 77            | 87                    |
        +--------------+---------------+-----------------------+--------------+---------------+-----------------------+
        + potted plant | 58            | 63                    | hair drier   | 78            | 88                    |
        +--------------+---------------+-----------------------+--------------+---------------+-----------------------+
        + bed          | 59            | 64                    | toothbrush   | 79            | 89                    |
        +--------------+---------------+-----------------------+--------------+---------------+-----------------------+