# Phase 01 — Repository Audit and Project Architecture

You are a senior Python desktop application engineer helping me develop my Artificial Intelligence course project.

## Project Overview

**Title:** Image-Based Robot Navigation Using Image Processing and AI Search Algorithms.

**Objective:** Develop an offline desktop application that processes static environment images into occupancy-grid maps using OpenCV and applies classical AI search algorithms to find paths between user-defined start and goal positions.

**Technology Stack:**
- Python
- PyQt6
- Qt Quick/QML
- OpenCV
- NumPy

**Algorithms:**
- Breadth-First Search (BFS)
- Depth-First Search (DFS)
- Depth-Limited Search (DLS)
- Iterative Deepening Search (IDS)
- Uniform-Cost Search (UCS)

## Your Task

Before writing any code, inspect the existing repository thoroughly.

1. Identify existing files, modules, dependencies, and application entry points.
2. Identify existing implementations that should be preserved.
3. Propose a clean, modular architecture.
4. Separate application logic, image processing, occupancy-grid management, search algorithms, evaluation, and UI.
5. Define the common occupancy-grid representation.
6. Define a shared result structure for all search algorithms.
7. Explain how Python objects will communicate with QML through PyQt6.
8. Recommend a suitable folder structure.
9. Identify dependencies and prepare a proposed requirements.txt.
10. Provide a phased development plan.

## Architectural Expectations

The architecture should support:
- Loading custom environment images.
- Processing images with OpenCV.
- Generating occupancy grids.
- Selecting start and goal positions.
- Running different search algorithms.
- Visualizing explored cells and final paths.
- Comparing algorithm performance.
- Importing compatible BARN maps separately.

Keep the architecture practical. Avoid unnecessary abstractions and overengineering.

## Important Constraints

- This is an offline static navigation simulator.
- No physical robot deployment.
- No real-time camera or sensor processing.
- No ROS or Gazebo.
- No deep learning or model training.
- No cloud services.

## Deliverables

Provide:
1. Repository audit.
2. Proposed architecture.
3. Folder structure.
4. Core data models and interfaces.
5. Dependency recommendations.
6. Development roadmap.

Do not implement the entire application yet. Wait for my approval before proceeding to Phase 02.

- Remove unnecessary folders in the project directory