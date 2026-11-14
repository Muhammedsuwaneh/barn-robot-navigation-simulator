import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    required property var viewModel
    signal loadImageRequested()
    signal comparisonRequested()

    ScrollView {
        id: pageScroll
        objectName: "customPageScroll"
        anchors.fill: parent
        clip: true
        contentWidth: availableWidth
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        ColumnLayout {
            id: pageLayout
            width: pageScroll.availableWidth
            spacing: 12

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 52
                spacing: 12

                ColumnLayout {
                    spacing: 3
                    Text {
                        text: "Custom image maps"
                        color: "#19251E"
                        font.family: "Bahnschrift"
                        font.pixelSize: 22
                        font.bold: true
                    }
                    Text {
                        text: "IMAGE UPLOAD / PREPROCESSING / OCCUPANCY GRID"
                        color: "#738078"
                        font.family: "Bahnschrift"
                        font.pixelSize: 9
                        font.letterSpacing: 0.8
                    }
                }

                Item { Layout.fillWidth: true }

                Button {
                    id: loadImageButton
                    objectName: "loadImageButton"
                    Layout.preferredWidth: 180
                    Layout.preferredHeight: 38
                    text: "Load environment image"
                    font.family: "Bahnschrift"
                    font.pixelSize: 11
                    onClicked: root.loadImageRequested()
                    background: Rectangle {
                        radius: 4
                        color: loadImageButton.down ? "#123C2D" : (loadImageButton.hovered ? "#236548" : "#174D3A")
                    }
                    contentItem: Text {
                        text: loadImageButton.text
                        color: "#FFFFFF"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font: loadImageButton.font
                    }
                    ToolTip.visible: hovered
                    ToolTip.text: "Choose a PNG, JPG, or JPEG image from this computer"
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 34
                radius: 4
                color: root.viewModel.errorMessage.length > 0 ? "#F9ECE8" : "#EAF2ED"
                border.color: root.viewModel.errorMessage.length > 0 ? "#EBC8BE" : "#DCE9DF"
                visible: true

                Text {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight; Layout.minimumWidth: 0
                    text: root.viewModel.errorMessage.length > 0
                          ? root.viewModel.errorMessage
                          : root.viewModel.statusMessage
                    color: root.viewModel.errorMessage.length > 0 ? "#9B4632" : "#3F6650"
                    font.family: "Bahnschrift"
                    font.pixelSize: 10
                }
            }

            Rectangle {
                Layout.fillWidth: true
                objectName: "customPreviewPanel"
                Layout.preferredHeight: Math.max(customGrid.implicitHeight + 90, root.height - processingPanel.implicitHeight - 130)
                Layout.minimumHeight: customGrid.implicitHeight + 90
                radius: 6
                color: "#FFFFFF"
                border.color: "#DDE4DE"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 9

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: "MAP PREVIEW"
                            color: "#45534A"
                            font.family: "Bahnschrift"
                            font.pixelSize: 10
                            font.bold: true
                            font.letterSpacing: 1
                        }
                        Item { Layout.fillWidth: true }
                        Text {
                            text: root.viewModel.imageName
                            color: "#78847C"
                            font.family: "Bahnschrift"
                            font.pixelSize: 10
                            elide: Text.ElideMiddle
                            Layout.maximumWidth: 340
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 10

                        PreviewPane {
                            label: "ORIGINAL INPUT"
                            imageSource: root.viewModel.originalPreviewUrl
                            emptyMessage: "Load a static environment image to inspect the source."
                            viewModel: root.viewModel
                            showPathOverlay: true
                        }
                        PreviewPane {
                            label: "BINARY PREVIEW"
                            imageSource: root.viewModel.processedPreviewUrl
                            emptyMessage: "The thresholded result will appear here."
                        }
                        GridPreviewPane {
                            id: customGrid
                            onComparisonRequested: root.comparisonRequested()
                            viewModel: root.viewModel
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: "SIZE  " + root.viewModel.imageDimensions
                            color: "#77837B"
                            font.family: "Bahnschrift"
                            font.pixelSize: 9
                            font.letterSpacing: 0.4
                        }
                        Item { Layout.fillWidth: true }
                        Text {
                            text: "BLACK = OBSTACLE    WHITE = FREE"
                            color: "#438261"
                            font.family: "Bahnschrift"
                            font.pixelSize: 9
                            font.bold: true
                            font.letterSpacing: 0.3
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                id: processingPanel
                objectName: "processingPanel"
                implicitHeight: processingLayout.implicitHeight + 28
                Layout.preferredHeight: implicitHeight
                Layout.minimumHeight: implicitHeight
                radius: 6
                color: "#FFFFFF"
                border.color: "#DDE4DE"

                ColumnLayout {
                    id: processingLayout
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 8

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: "PROCESSING CONTROLS"
                            color: "#35443B"
                            font.family: "Bahnschrift"
                            font.pixelSize: 10
                            font.bold: true
                            font.letterSpacing: 0.8
                        }
                        Item { Layout.fillWidth: true }
                        Text {
                            text: "BLACK = OBSTACLE / WHITE = FREE"
                            color: "#438261"
                            font.family: "Bahnschrift"
                            font.pixelSize: 9
                            font.bold: true
                            font.letterSpacing: 0.4
                        }
                    }

                    GridLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        columns: pageScroll.availableWidth >= 1100 ? 3 : 2
                        columnSpacing: 18
                        rowSpacing: 8

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 5
                            RowLayout {
                                Layout.fillWidth: true
                                Text {
                                    text: "FIXED THRESHOLD"
                                    color: "#657269"
                                    font.family: "Bahnschrift"
                                    font.pixelSize: 10
                                    font.bold: true
                                    font.letterSpacing: 0.5
                                }
                                Item { Layout.fillWidth: true }
                                Text {
                                    text: root.viewModel.threshold.toString()
                                    color: "#286247"
                                    font.family: "Bahnschrift"
                                    font.pixelSize: 10
                                    font.bold: true
                                }
                            }
                            Slider {
                                objectName: "thresholdSlider"
                                Layout.fillWidth: true
                                from: 0
                                to: 255
                                stepSize: 1
                                value: root.viewModel.threshold
                                enabled: root.viewModel.hasImage
                                    && !root.viewModel.adaptiveThreshold
                                    && !root.viewModel.otsuThreshold
                                onMoved: root.viewModel.threshold = Math.round(value)
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                Text { text: "DARKER"; color: "#87928A"; font.family: "Bahnschrift"; font.pixelSize: 10 }
                                Item { Layout.fillWidth: true }
                                Text { text: "LIGHTER"; color: "#87928A"; font.family: "Bahnschrift"; font.pixelSize: 10 }
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            CheckBox {
                                objectName: "otsuThresholdSwitch"
                                Layout.fillWidth: true
                                text: "Automatic Otsu threshold"
                                checked: root.viewModel.otsuThreshold
                                enabled: root.viewModel.hasImage
                                font.family: "Bahnschrift"
                                font.pixelSize: 9
                                onToggled: root.viewModel.otsuThreshold = checked
                            }
                            Switch {
                                objectName: "adaptiveThresholdSwitch"
                                Layout.fillWidth: true
                                text: "Adaptive threshold"
                                checked: root.viewModel.adaptiveThreshold
                                enabled: root.viewModel.hasImage
                                font.family: "Bahnschrift"
                                font.pixelSize: 9
                                onToggled: root.viewModel.adaptiveThreshold = checked
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 3
                                    Text { text: "BLOCK SIZE"; color: "#657269"; font.family: "Bahnschrift"; font.pixelSize: 10; font.bold: true }
                                    SpinBox {
                                        objectName: "adaptiveBlockSizeInput"
                                        Layout.fillWidth: true
                                        from: 3
                                        to: 51
                                        stepSize: 2
                                        value: root.viewModel.adaptiveBlockSize
                                        enabled: root.viewModel.hasImage && root.viewModel.adaptiveThreshold
                                        onValueModified: root.viewModel.adaptiveBlockSize = value
                                    }
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 3
                                    Text { text: "ADAPTIVE C"; color: "#657269"; font.family: "Bahnschrift"; font.pixelSize: 10; font.bold: true }
                                    SpinBox {
                                        objectName: "adaptiveCInput"
                                        Layout.fillWidth: true
                                        from: -50
                                        to: 50
                                        value: root.viewModel.adaptiveC
                                        enabled: root.viewModel.hasImage && root.viewModel.adaptiveThreshold
                                        onValueModified: root.viewModel.adaptiveC = value
                                    }
                                }
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 5
                            Text { text: "MORPHOLOGY"; color: "#657269"; font.family: "Bahnschrift"; font.pixelSize: 10; font.bold: true }
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                ComboBox {
                                    objectName: "morphologySelector"
                                    Layout.fillWidth: true
                                    model: ["None", "Opening", "Closing"]
                                    currentIndex: ["none", "open", "close"].indexOf(root.viewModel.morphologyMode)
                                    enabled: root.viewModel.hasImage
                                    font.family: "Bahnschrift"
                                    font.pixelSize: 9
                                    onActivated: root.viewModel.morphologyMode = currentText.toLowerCase() === "opening" ? "open" : currentText.toLowerCase() === "closing" ? "close" : "none"
                                }
                                SpinBox {
                                    objectName: "morphologyKernelInput"
                                    Layout.preferredWidth: 82
                                    from: 1
                                    to: 15
                                    stepSize: 2
                                    value: root.viewModel.morphologyKernelSize
                                    enabled: root.viewModel.hasImage && root.viewModel.morphologyMode !== "none"
                                    onValueModified: root.viewModel.morphologyKernelSize = value
                                }
                            }
                            Text {
                                text: "Opening removes specks; closing fills gaps."
                                color: "#87928A"
                                font.family: "Bahnschrift"
                                font.pixelSize: 10
                                wrapMode: Text.WordWrap
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 5
                            CheckBox {
                                objectName: "lightObstacleCheckBox"
                                Layout.fillWidth: true
                                text: "White pixels are obstacles"
                                checked: root.viewModel.lightPixelsAreObstacles
                                enabled: root.viewModel.hasImage
                                font.family: "Bahnschrift"
                                font.pixelSize: 9
                                onToggled: root.viewModel.lightPixelsAreObstacles = checked
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                Text {
                                    Layout.fillWidth: true
                                    text: "Inspect the preview; thresholding is not scene understanding."
                                    color: "#78847C"
                                    wrapMode: Text.WordWrap
                                    font.family: "Bahnschrift"
                                    font.pixelSize: 10
                                }
                                Button {
                                    objectName: "resetProcessingButton"
                                    text: "Reset"
                                    enabled: root.viewModel.hasImage
                                    font.family: "Bahnschrift"
                                    font.pixelSize: 9
                                    onClicked: root.viewModel.resetProcessing()
                                }
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 5
                            Text {
                                text: "GRID RESOLUTION"
                                color: "#657269"
                                font.family: "Bahnschrift"
                                font.pixelSize: 10
                                font.bold: true
                                font.letterSpacing: 0.4
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 2
                                    Text { text: "CELL SIZE · PX"; color: "#87928A"; font.family: "Bahnschrift"; font.pixelSize: 9 }
                                    SpinBox {
                                        objectName: "gridCellSizeInput"
                                        Layout.fillWidth: true
                                        from: 1
                                        to: 512
                                        value: root.viewModel.gridCellSizePx
                                        enabled: root.viewModel.hasImage
                                        onValueModified: root.viewModel.gridCellSizePx = value
                                    }
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 2
                                    Text { text: "OBSTACLE · %"; color: "#87928A"; font.family: "Bahnschrift"; font.pixelSize: 9 }
                                    SpinBox {
                                        objectName: "obstacleThresholdInput"
                                        Layout.fillWidth: true
                                        from: 1
                                        to: 100
                                        value: root.viewModel.obstacleThresholdPercent
                                        enabled: root.viewModel.hasImage
                                        onValueModified: root.viewModel.obstacleThresholdPercent = value
                                    }
                                }
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 5
                            Text {
                                text: "GRID GENERATION"
                                color: "#657269"
                                font.family: "Bahnschrift"
                                font.pixelSize: 10
                                font.bold: true
                                font.letterSpacing: 0.4
                            }
                            Button {
                                id: generateGridButton
                                objectName: "generateGridButton"
                                Layout.fillWidth: true
                                Layout.preferredHeight: 34
                                text: root.viewModel.gridReady ? "Regenerate grid" : "Generate occupancy grid"
                                enabled: root.viewModel.hasImage
                                font.family: "Bahnschrift"
                                font.pixelSize: 9
                                font.bold: true
                                onClicked: root.viewModel.generateOccupancyGrid()
                                background: Rectangle {
                                    radius: 4
                                    color: generateGridButton.enabled
                                        ? (generateGridButton.hovered ? "#236548" : "#174D3A")
                                        : "#A8B8AE"
                                }
                                contentItem: Text {
                                    text: generateGridButton.text
                                    color: "#FFFFFF"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    font: generateGridButton.font
                                }
                            }
                            Text {
                                Layout.fillWidth: true
                                text: "Mixed cells are occupied at or above the selected percentage."
                                color: "#78847C"
                                wrapMode: Text.WordWrap
                                font.family: "Bahnschrift"
                                font.pixelSize: 10
                            }
                        }
                    }
                }
            }
        }
    }
}
