# Phase 03 — Image Loading and OpenCV Preprocessing

Continue from the existing application.

## Objective

Implement the image-loading and preprocessing functionality using OpenCV.

The application should allow users to upload static environment images and prepare them for occupancy-grid generation.

## Image Loading

Implement:
- Local image selection.
- Image validation.
- Support for common formats such as PNG, JPG, and JPEG.
- Original image preview.
- Error handling for invalid or unsupported files.

## Image Processing

Use OpenCV to implement:

1. Grayscale conversion.
2. Binary thresholding.
3. Adjustable threshold values.
4. Optional adaptive thresholding.
5. Morphological operations where appropriate.
6. Processed image preview.

## User Interface

Add:
- Upload image button.
- Original image preview.
- Processed image preview.
- Threshold adjustment controls.
- Processing options.
- Reset functionality.

The user should be able to adjust preprocessing parameters and immediately see the resulting binary image.

## Important Considerations

Clearly define the pixel interpretation.

For example:
- Black pixels represent obstacles.
- White pixels represent free space.

However, allow the user to change the interpretation if necessary because different environment images may use different conventions.

Do not assume every uploaded photograph can automatically produce a reliable navigation map.

This is classical image processing, not object detection or semantic scene understanding.

## Constraints

- No deep learning.
- No neural networks.
- No model training.
- Do not implement pathfinding yet.

## Deliverables

1. Image loading functionality.
2. OpenCV preprocessing module.
3. Original and processed image previews.
4. Adjustable preprocessing parameters.
5. Unit tests.
6. Updated documentation.

Ensure the preprocessing functions can be tested independently of the graphical interface.