import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    required property var viewModel
    property real zoom: 1.0
    readonly property bool wideLayout: width >= 600
    property string emptyMessage: "Generate a grid from the processed image."
    implicitHeight: wideLayout ? 400 : controlsLayout.implicitHeight + gridHeader.implicitHeight + 330
    signal comparisonRequested()

    Layout.fillWidth: true
    Layout.fillHeight: true
    Layout.minimumWidth: 280
    Layout.minimumHeight: implicitHeight
    radius: 10
    color: "#FFFFFF"
    border.color: "#DDE4DE"

    GridLayout {
        anchors.fill: parent
        anchors.margins: 10
        columns: root.wideLayout ? 2 : 1
        columnSpacing: 12
        rowSpacing: 10

        RowLayout {
            id: gridHeader
            Layout.columnSpan: root.wideLayout ? 2 : 1
            Layout.fillWidth: true
            Text {
                text: "OCCUPANCY GRID"
                color: "#45534A"
                font.family: "Bahnschrift"
                font.pixelSize: 9
                font.bold: true
                font.letterSpacing: 0.5
            }
            Item { Layout.fillWidth: true }
            Text {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignRight
                text: root.viewModel.gridReady ? root.viewModel.gridDimensions : "NOT GENERATED"
                color: "#78847C"
                font.family: "Bahnschrift"
                font.pixelSize: 10
                elide: Text.ElideRight; Layout.minimumWidth: 0
            }
        }

        Rectangle {
            objectName: "gridViewportFrame"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 280
            color: "#EDF2EE"
            radius: 3
            clip: true

            Flickable {
                id: viewport
                anchors.fill: parent
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                contentWidth: Math.max(width, gridImage.width)
                contentHeight: Math.max(height, gridImage.height)

                Image {
                    id: gridImage
                    objectName: "occupancyGridPreview"
                    property real fitCellSize: root.viewModel.gridReady
                        ? Math.min(viewport.width / root.viewModel.gridColumns,
                                   viewport.height / root.viewModel.gridRows)
                        : 1
                    x: Math.max(0, (viewport.width - width) / 2)
                    y: Math.max(0, (viewport.height - height) / 2)
                    width: root.viewModel.gridReady
                        ? fitCellSize * root.zoom * root.viewModel.gridColumns
                        : 0
                    height: root.viewModel.gridReady
                        ? fitCellSize * root.zoom * root.viewModel.gridRows
                        : 0
                    source: root.viewModel.occupancyGridPreviewUrl
                    fillMode: Image.Stretch
                    smooth: false
                    cache: false
                }

                Canvas {
                    id: searchOverlay
                    objectName: "searchVisualizationOverlay"
                    x: gridImage.x
                    y: gridImage.y
                    width: gridImage.width
                    height: gridImage.height
                    z: 1
                    onPaint: {
                        var context = getContext("2d")
                        context.clearRect(0, 0, width, height)
                        if (!root.viewModel.gridReady || width <= 0 || height <= 0)
                            return

                        var cellWidth = width / root.viewModel.gridColumns
                        var cellHeight = height / root.viewModel.gridRows
                        if (root.viewModel.showExploredCells) {
                            var explored = root.viewModel.exploredCells
                            context.fillStyle = "#6048A879"
                            for (var index = 0; index < explored.length; index++) {
                                context.fillRect((explored[index][1] + 0.1) * cellWidth,
                                                 (explored[index][0] + 0.1) * cellHeight,
                                                 cellWidth * 0.8, cellHeight * 0.8)
                            }
                        }
                        var path = root.viewModel.pathCells
                        if (path.length > 0) {
                            context.beginPath()
                            context.moveTo((path[0][1] + 0.5) * cellWidth,
                                           (path[0][0] + 0.5) * cellHeight)
                            for (var routeIndex = 1; routeIndex < path.length; routeIndex++) {
                                context.lineTo((path[routeIndex][1] + 0.5) * cellWidth,
                                               (path[routeIndex][0] + 0.5) * cellHeight)
                            }
                            context.lineCap = "round"
                            context.lineJoin = "round"
                            context.strokeStyle = "#171B19"
                            context.lineWidth = Math.max(3, Math.min(cellWidth, cellHeight) * 0.65)
                            context.stroke()
                            context.strokeStyle = "#FF3030"
                            context.lineWidth = Math.max(1.5, Math.min(cellWidth, cellHeight) * 0.34)
                            context.stroke()
                        }
                    }
                    Connections {
                        target: root.viewModel
                        function onSearchChanged() { searchOverlay.requestPaint() }
                        function onGridChanged() { searchOverlay.requestPaint() }
                    }
                    onWidthChanged: requestPaint()
                    onHeightChanged: requestPaint()
                }

                Rectangle {
                    id: startMarker
                    objectName: "startCellMarker"
                    property real cellWidth: root.viewModel.gridReady
                        ? gridImage.width / root.viewModel.gridColumns
                        : 0
                    width: Math.min(24, Math.max(8, cellWidth * 0.82))
                    height: width
                    radius: width / 2
                    x: gridImage.x + (root.viewModel.startColumn + 0.5) * cellWidth - width / 2
                    y: gridImage.y + (root.viewModel.startRow + 0.5) * cellWidth - height / 2
                    visible: root.viewModel.hasStart && cellWidth > 0
                    z: 2
                    color: "#E6A23C"
                    border.color: "#FFFFFF"
                    border.width: 2
                    Text {
                        anchors.centerIn: parent
                        text: "S"
                        color: "#17231D"
                        font.family: "Bahnschrift"
                        font.pixelSize: 9
                        font.bold: true
                    }
                }

                Rectangle {
                    id: goalMarker
                    objectName: "goalCellMarker"
                    property real cellWidth: root.viewModel.gridReady
                        ? gridImage.width / root.viewModel.gridColumns
                        : 0
                    width: Math.min(24, Math.max(8, cellWidth * 0.82))
                    height: width
                    radius: width / 2
                    x: gridImage.x + (root.viewModel.goalColumn + 0.5) * cellWidth - width / 2
                    y: gridImage.y + (root.viewModel.goalRow + 0.5) * cellWidth - height / 2
                    visible: root.viewModel.hasGoal && cellWidth > 0
                    z: 2
                    color: "#4CA6A0"
                    border.color: "#FFFFFF"
                    border.width: 2
                    Text {
                        anchors.centerIn: parent
                        text: "G"
                        color: "#102A28"
                        font.family: "Bahnschrift"
                        font.pixelSize: 9
                        font.bold: true
                    }
                }

                MouseArea {
                    objectName: "gridSelectionMouseArea"
                    anchors.fill: gridImage
                    enabled: root.viewModel.gridReady
                        && root.viewModel.selectionMode !== "none"
                        && !root.viewModel.searchBusy
                    cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                    acceptedButtons: Qt.LeftButton
                    z: 3
                    onClicked: function(mouse) {
                        if (gridImage.width <= 0 || gridImage.height <= 0)
                            return
                        root.viewModel.selectGridPosition(
                            mouse.x / gridImage.width,
                            mouse.y / gridImage.height
                        )
                    }
                }

                Text {
                    anchors.centerIn: parent
                    width: parent.width - 24
                    text: root.emptyMessage
                    color: "#69776E"
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    font.family: "Bahnschrift"
                    font.pixelSize: 9
                    visible: !root.viewModel.gridReady
                }
            }
        }

        ScrollView {
            id: controlsScroll
            objectName: "gridControlsScroll"
            Layout.fillWidth: !root.wideLayout
            Layout.fillHeight: root.wideLayout
            Layout.preferredWidth: root.wideLayout ? 248 : -1
            Layout.minimumWidth: root.wideLayout ? 248 : 0
            Layout.maximumWidth: root.wideLayout ? 248 : Infinity
            Layout.preferredHeight: root.wideLayout ? -1 : controlsLayout.implicitHeight
            clip: true
            contentWidth: availableWidth
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                id: controlsLayout
                width: controlsScroll.availableWidth
                spacing: 12
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    Text {
                        text: root.viewModel.gridReady
                            ? root.viewModel.gridOccupiedCount + " occupied · " + root.viewModel.gridFreeCount + " free"
                            : "No grid"
                        color: "#66736A"
                        font.family: "Bahnschrift"
                        font.pixelSize: 10
                        Layout.fillWidth: true
                        elide: Text.ElideRight; Layout.minimumWidth: 0
                    }
                    CompactButton {
                        Layout.preferredWidth: 32
                        text: "-"
                        enabled: root.viewModel.gridReady && root.zoom > 0.5
                        onClicked: root.zoom = Math.max(0.5, root.zoom - 0.25)
                        ToolTip.visible: hovered
                        ToolTip.text: "Zoom out"
                    }
                    CompactButton {
                        Layout.preferredWidth: 40
                        text: "Fit"
                        enabled: root.viewModel.gridReady
                            && !root.viewModel.searchBusy
                        onClicked: root.zoom = 1.0
                        ToolTip.visible: hovered
                        ToolTip.text: "Fit the complete grid in the preview"
                    }
                    CompactButton {
                        Layout.preferredWidth: 32
                        text: "+"
                        enabled: root.viewModel.gridReady && root.zoom < 4.0
                        onClicked: root.zoom = Math.min(4.0, root.zoom + 0.25)
                        ToolTip.visible: hovered
                        ToolTip.text: "Zoom in"
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 5
                    CompactButton {
                        objectName: "setStartButton"
                        Layout.fillWidth: true
                        text: "Set Start"
                        checkable: true
                        checked: root.viewModel.selectionMode === "start"
                        enabled: root.viewModel.gridReady
                            && !root.viewModel.searchBusy
                        font.family: "Bahnschrift"
                        font.pixelSize: 10
                        onClicked: root.viewModel.setSelectionMode(checked ? "start" : "none")
                    }
                    CompactButton {
                        objectName: "setGoalButton"
                        Layout.fillWidth: true
                        text: "Set Goal"
                        checkable: true
                        checked: root.viewModel.selectionMode === "goal"
                        enabled: root.viewModel.gridReady && !root.viewModel.searchBusy
                        font.family: "Bahnschrift"
                        font.pixelSize: 10
                        onClicked: root.viewModel.setSelectionMode(checked ? "goal" : "none")
                    }
                    CompactButton {
                        objectName: "clearSelectionButton"
                        text: "Clear"
                        enabled: !root.viewModel.searchBusy
                            && (root.viewModel.hasStart || root.viewModel.hasGoal || root.viewModel.selectionMode !== "none")
                        font.family: "Bahnschrift"
                        font.pixelSize: 10
                        onClicked: root.viewModel.clearSelection()
                        ToolTip.visible: hovered
                        ToolTip.text: "Clear both start and goal selections"
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        objectName: "startCoordinateLabel"
                        Layout.fillWidth: true
                        text: "START  " + root.viewModel.startCoordinate
                        color: "#A66B1D"
                        font.family: "Bahnschrift"
                        font.pixelSize: 10
                        elide: Text.ElideRight; Layout.minimumWidth: 0
                    }
                    Text {
                        objectName: "goalCoordinateLabel"
                        Layout.fillWidth: true
                        text: "GOAL  " + root.viewModel.goalCoordinate
                        color: "#26736D"
                        font.family: "Bahnschrift"
                        font.pixelSize: 10
                        elide: Text.ElideRight; Layout.minimumWidth: 0
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    ComboBox {
                        objectName: "algorithmSelector"
                        Layout.minimumWidth: 0
                        Layout.preferredHeight: 32
                        Layout.fillWidth: true
                        model: root.viewModel.availableAlgorithms
                        currentIndex: model.indexOf(root.viewModel.selectedAlgorithm)
                        enabled: root.viewModel.gridReady && !root.viewModel.searchBusy
                        font.family: "Bahnschrift"
                        font.pixelSize: 10
                        onActivated: root.viewModel.selectedAlgorithm = currentText
                        ToolTip.visible: hovered
                        ToolTip.text: "Choose the search algorithm"
                    }
                    ColumnLayout {
                        spacing: 1
                        visible: root.viewModel.selectedAlgorithm === "DLS"
                            || root.viewModel.selectedAlgorithm === "IDS"
                        Text {
                            text: "DEPTH"
                            color: "#657269"
                            font.family: "Bahnschrift"
                            font.pixelSize: 10
                            font.bold: true
                        }
                        CompactSpinBox {
                            objectName: "depthLimitInput"
                            Layout.preferredWidth: 88
                            Layout.preferredHeight: 32
                            from: 0
                            to: 512
                            value: root.viewModel.depthLimit
                            enabled: parent.visible && !root.viewModel.searchBusy
                            onValueModified: root.viewModel.depthLimit = value
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    CheckBox {
                        objectName: "showExploredCellsCheckBox"
                        Layout.fillWidth: true
                        text: "Show explored cells"
                        checked: root.viewModel.showExploredCells
                        enabled: root.viewModel.hasSearchResult
                        font.family: "Bahnschrift"
                        font.pixelSize: 10
                        onToggled: root.viewModel.showExploredCells = checked
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    CompactButton {
                        objectName: "runSearchButton"
                        primary: true
                        Layout.fillWidth: true
                        text: root.viewModel.searchBusy
                            ? "Searching..."
                            : "Run " + root.viewModel.selectedAlgorithm
                        enabled: root.viewModel.canRunSearch
                        onClicked: root.viewModel.runSearch()
                        font.family: "Bahnschrift"
                        font.pixelSize: 10
                        ToolTip.visible: hovered && !enabled
                        ToolTip.text: "Generate a grid and set distinct free start and goal cells first"
                    }
                    CompactButton {
                        objectName: "compareAlgorithmsButton"
                        Layout.fillWidth: true
                        text: root.viewModel.comparisonBusy ? "Comparing..." : "Compare"
                        enabled: root.viewModel.canRunSearch && !root.viewModel.comparisonBusy
                        onClicked: root.comparisonRequested()
                        font.family: "Bahnschrift"
                        font.pixelSize: 10
                        ToolTip.visible: hovered && !enabled
                        ToolTip.text: "Choose algorithms to compare on the same map and endpoints"
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    CompactButton {
                        Layout.fillWidth: true
                        objectName: "resetSearchButton"
                        text: "Reset"
                        enabled: root.viewModel.hasSearchResult && !root.viewModel.searchBusy
                        onClicked: root.viewModel.resetSearchVisualization()
                        font.family: "Bahnschrift"
                        font.pixelSize: 10
                    }
                    CompactButton {
                        objectName: "cancelSearchButton"
                        text: "Cancel"
                        visible: root.viewModel.searchBusy && !root.viewModel.comparisonBusy
                        onClicked: root.viewModel.cancelSearch()
                        font.pixelSize: 10
                    }
                }

                Text {
                    objectName: "bfsResultSummary"
                    Layout.fillWidth: true
                    text: root.viewModel.searchBusy
                        ? root.viewModel.searchSummary
                        : root.viewModel.hasSearchResult
                            ? root.viewModel.searchSummary
                            : root.viewModel.selectedAlgorithm + " ready when start and goal are set"
                    color: root.viewModel.searchSucceeded ? "#286247" : "#69776E"
                    elide: Text.ElideRight; Layout.minimumWidth: 0
                    font.family: "Bahnschrift"
                    font.pixelSize: 10
                }

                GridLayout {
                    columns: 2
                    Layout.fillWidth: true
                    columnSpacing: 8
                    rowSpacing: 5
                    Text { Layout.fillWidth: true; text: "PATH/COST  " + (root.viewModel.pathLength < 0 ? "--" : root.viewModel.pathLength + " / " + root.viewModel.pathCost); color: "#66736A"; font.family: "Bahnschrift"; font.pixelSize: 10; elide: Text.ElideRight; Layout.minimumWidth: 0 }
                    Text { Layout.fillWidth: true; text: "EXPANDED  " + root.viewModel.nodesExpanded; color: "#66736A"; font.family: "Bahnschrift"; font.pixelSize: 10; elide: Text.ElideRight; Layout.minimumWidth: 0 }
                    Text { Layout.fillWidth: true; text: "FRONTIER  " + root.viewModel.peakFrontierSize; color: "#66736A"; font.family: "Bahnschrift"; font.pixelSize: 10; elide: Text.ElideRight; Layout.minimumWidth: 0 }
                    Text { Layout.fillWidth: true; text: "TIME  " + root.viewModel.searchElapsedMs.toFixed(2) + " ms"; color: "#66736A"; font.family: "Bahnschrift"; font.pixelSize: 10; elide: Text.ElideRight; Layout.minimumWidth: 0 }
                }
            }
        }
    }
}
