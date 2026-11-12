# Phase 04 — Occupancy-Grid Generation

Continue from the existing image-processing implementation.

## Objective

Convert processed binary environment images into discrete occupancy-grid maps suitable for classical pathfinding algorithms.

## Occupancy-Grid Representation

Establish one consistent representation throughout the application.

Each cell must represent either:

- Free space.
- Occupied space (obstacle).

Clearly define:
- Numeric or Boolean encoding.
- Grid dimensions.
- Row and column indexing.
- Coordinate conventions.
- How image pixels map to grid cells.

Use the same convention in the UI and all future search algorithms.

## Grid Generation

Implement:

1. Conversion of binary images into occupancy grids.
2. Configurable grid resolution or cell size.
3. Obstacle-percentage threshold for classifying grid cells.
4. Grid validation.
5. Grid visualization.

When a region contains both obstacle and free pixels, use a documented rule to determine whether its corresponding cell is occupied.

## Visualization

Display the generated occupancy grid in the application.

Distinguish:
- Free cells.
- Occupied cells.

Preserve the relationship between the original image and generated grid.

Support reasonable zooming or fit-to-view behavior.

## Validation

Check:
- Grid is not empty.
- Grid dimensions are valid.
- Cell values are valid.
- Grid coordinates are consistent.
- Occupied cells are not treated as traversable.

## Constraints

Do not implement pathfinding yet.

Do not add automatic start or goal detection.

Keep the original image, processed image, and occupancy grid as separate representations.

## Deliverables

1. Occupancy-grid data model.
2. Image-to-grid conversion functionality.
3. Grid visualization.
4. Grid-resolution controls.
5. Validation and error handling.
6. Unit tests.
7. Documentation of occupancy-grid conventions.

Demonstrate the complete workflow from image upload to occupancy-grid generation.