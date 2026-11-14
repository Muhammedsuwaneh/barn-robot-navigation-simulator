import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: pane
    property string label: ""
    property string imageSource: ""
    property string emptyMessage: "No image loaded"
    property var viewModel: null
    property bool showPathOverlay: false

    Layout.fillWidth: true
    Layout.fillHeight: true
    Layout.minimumWidth: 180
    radius: 5
    color: "#15221D"
    border.color: "#293A31"
    clip: true

    Image {
        id: previewImage
        objectName: pane.label === "ORIGINAL INPUT" ? "originalImagePreview" : "processedImagePreview"
        anchors.fill: parent
        anchors.margins: 10
        source: pane.imageSource
        fillMode: Image.PreserveAspectFit
        asynchronous: true
        cache: false
        visible: pane.imageSource.length > 0
    }

    Canvas {
        id: pathOverlay
        objectName: pane.showPathOverlay ? "originalPathOverlay" : "previewPathOverlay"
        anchors.centerIn: previewImage
        width: previewImage.paintedWidth
        height: previewImage.paintedHeight
        visible: pane.showPathOverlay
            && pane.viewModel !== null
            && pane.viewModel.gridReady
            && width > 0
            && height > 0
        z: 2

        onPaint: {
            var context = getContext("2d")
            context.clearRect(0, 0, width, height)
            if (!pane.viewModel || !pane.viewModel.gridReady
                    || pane.viewModel.sourceImageWidth <= 0
                    || pane.viewModel.sourceImageHeight <= 0)
                return

            var sourceWidth = pane.viewModel.sourceImageWidth
            var sourceHeight = pane.viewModel.sourceImageHeight
            var scaleX = width / sourceWidth
            var scaleY = height / sourceHeight
            var cellSize = pane.viewModel.gridCellSizePx

            function cellBounds(cell) {
                var left = cell[1] * cellSize
                var top = cell[0] * cellSize
                return {
                    x: left * scaleX,
                    y: top * scaleY,
                    width: Math.min(cellSize, sourceWidth - left) * scaleX,
                    height: Math.min(cellSize, sourceHeight - top) * scaleY
                }
            }
            function cellCenter(cell) {
                var bounds = cellBounds(cell)
                return [bounds.x + bounds.width / 2, bounds.y + bounds.height / 2]
            }

            var path = pane.viewModel.pathCells
            if (path.length > 0) {
                context.lineCap = "round"
                context.lineJoin = "round"
                context.beginPath()
                var firstCenter = cellCenter(path[0])
                context.moveTo(firstCenter[0], firstCenter[1])
                for (var lineIndex = 1; lineIndex < path.length; lineIndex++) {
                    var center = cellCenter(path[lineIndex])
                    context.lineTo(center[0], center[1])
                }
                context.strokeStyle = "rgba(18, 21, 20, 0.96)"
                context.lineWidth = Math.max(5, Math.min(width, height) * 0.025)
                context.stroke()
                context.strokeStyle = "#FF3030"
                context.lineWidth = Math.max(2.5, Math.min(width, height) * 0.012)
                context.stroke()
            }

            function drawEndpoint(cell, fill, letter) {
                var center = cellCenter(cell)
                var radius = Math.max(7, Math.min(width, height) * 0.022)
                context.beginPath()
                context.arc(center[0], center[1], radius, 0, 2 * Math.PI)
                context.fillStyle = fill
                context.fill()
                context.lineWidth = 2
                context.strokeStyle = "#FFFFFF"
                context.stroke()
                context.fillStyle = "#17231D"
                context.font = "bold " + Math.max(9, radius) + "px sans-serif"
                context.textAlign = "center"
                context.textBaseline = "middle"
                context.fillText(letter, center[0], center[1])
            }

            if (pane.viewModel.hasStart)
                drawEndpoint([pane.viewModel.startRow, pane.viewModel.startColumn], "#E6A23C", "S")
            if (pane.viewModel.hasGoal)
                drawEndpoint([pane.viewModel.goalRow, pane.viewModel.goalColumn], "#4CA6A0", "G")
        }

        Connections {
            target: pane.viewModel
            function onSearchChanged() { pathOverlay.requestPaint() }
            function onGridChanged() { pathOverlay.requestPaint() }
            function onImageChanged() { pathOverlay.requestPaint() }
        }
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
    }

    Text {
        anchors.centerIn: parent
        width: parent.width - 36
        text: pane.emptyMessage
        color: "#A1B0A6"
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.WordWrap
        font.family: "Bahnschrift"
        font.pixelSize: 11
        visible: pane.imageSource.length === 0
    }

    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.margins: 9
        width: pane.label === "ORIGINAL INPUT" ? 102 : 112
        height: 23
        radius: 3
        color: "#24362D"
        z: 3
        Text {
            anchors.centerIn: parent
            text: pane.label
            color: "#C2CEC6"
            font.family: "Bahnschrift"
            font.pixelSize: 8
            font.bold: true
            font.letterSpacing: 0.6
        }
    }
}