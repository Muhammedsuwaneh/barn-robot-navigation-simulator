import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    required property var viewModel
    property real zoom: 1.0

    Layout.fillWidth: true
    Layout.fillHeight: true
    Layout.minimumWidth: 180
    radius: 5
    color: "#FFFFFF"
    border.color: "#DDE4DE"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 7

        RowLayout {
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
                text: root.viewModel.gridReady ? root.viewModel.gridDimensions : "NOT GENERATED"
                color: "#78847C"
                font.family: "Bahnschrift"
                font.pixelSize: 8
                elide: Text.ElideRight
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 180
            color: "#E6EBE7"
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

                Text {
                    anchors.centerIn: parent
                    width: parent.width - 24
                    text: "Generate a grid from the processed image."
                    color: "#69776E"
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    font.family: "Bahnschrift"
                    font.pixelSize: 9
                    visible: !root.viewModel.gridReady
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 4
            Text {
                text: root.viewModel.gridReady
                    ? root.viewModel.gridOccupiedCount + " occupied · " + root.viewModel.gridFreeCount + " free"
                    : "No grid"
                color: "#66736A"
                font.family: "Bahnschrift"
                font.pixelSize: 8
                Layout.fillWidth: true
                elide: Text.ElideRight
            }
            Button {
                text: "-"
                enabled: root.viewModel.gridReady && root.zoom > 0.5
                onClicked: root.zoom = Math.max(0.5, root.zoom - 0.25)
                ToolTip.visible: hovered
                ToolTip.text: "Zoom out"
            }
            Button {
                text: "Fit"
                enabled: root.viewModel.gridReady
                onClicked: root.zoom = 1.0
                ToolTip.visible: hovered
                ToolTip.text: "Fit the complete grid in the preview"
            }
            Button {
                text: "+"
                enabled: root.viewModel.gridReady && root.zoom < 4.0
                onClicked: root.zoom = Math.min(4.0, root.zoom + 0.25)
                ToolTip.visible: hovered
                ToolTip.text: "Zoom in"
            }
        }
    }
}