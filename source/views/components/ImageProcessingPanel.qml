import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    required property var viewModel
    signal loadImageRequested()

    ColumnLayout {
        anchors.fill: parent
        spacing: 16

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 54
            spacing: 12

            ColumnLayout {
                spacing: 3
                Text {
                    text: "Image preprocessing"
                    color: "#19251E"
                    font.family: "Bahnschrift"
                    font.pixelSize: 23
                    font.bold: true
                }
                Text {
                    text: "STATIC ENVIRONMENT / OPENCV BINARY PREVIEW"
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
                Layout.preferredWidth: 164
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
            Layout.preferredHeight: 36
            radius: 4
            color: root.viewModel.errorMessage.length > 0 ? "#F9ECE8" : "#EAF2ED"
            border.color: root.viewModel.errorMessage.length > 0 ? "#EBC8BE" : "#DCE9DF"
            visible: true

            Text {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
                text: root.viewModel.errorMessage.length > 0
                      ? root.viewModel.errorMessage
                      : root.viewModel.statusMessage
                color: root.viewModel.errorMessage.length > 0 ? "#9B4632" : "#3F6650"
                font.family: "Bahnschrift"
                font.pixelSize: 10
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 14

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumWidth: 390
                radius: 6
                color: "#FFFFFF"
                border.color: "#DDE4DE"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 11

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: "PREVIEW"
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
                            Layout.maximumWidth: 260
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
                        }
                        PreviewPane {
                            label: "BINARY PREVIEW"
                            imageSource: root.viewModel.processedPreviewUrl
                            emptyMessage: "The thresholded result will appear here."
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
                Layout.fillHeight: true
                Layout.preferredWidth: 312
                Layout.minimumWidth: 290
                radius: 6
                color: "#FFFFFF"
                border.color: "#DDE4DE"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 9

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: "PROCESSING OPTIONS"
                            color: "#35443B"
                            font.family: "Bahnschrift"
                            font.pixelSize: 10
                            font.bold: true
                            font.letterSpacing: 0.8
                        }
                        Item { Layout.fillWidth: true }
                        Button {
                            objectName: "resetProcessingButton"
                            text: "Reset"
                            enabled: root.viewModel.hasImage
                            flat: true
                            font.family: "Bahnschrift"
                            font.pixelSize: 10
                            onClicked: root.viewModel.resetProcessing()
                        }
                    }

                    Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: "#E8ECE9" }

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: "FIXED THRESHOLD"
                            color: "#657269"
                            font.family: "Bahnschrift"
                            font.pixelSize: 9
                            font.bold: true
                            font.letterSpacing: 0.6
                        }
                        Item { Layout.fillWidth: true }
                        Text {
                            text: root.viewModel.threshold.toString()
                            color: "#286247"
                            font.family: "Bahnschrift"
                            font.pixelSize: 11
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
                        enabled: root.viewModel.hasImage && !root.viewModel.adaptiveThreshold
                        onMoved: root.viewModel.threshold = Math.round(value)
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "DARKER"; color: "#87928A"; font.family: "Bahnschrift"; font.pixelSize: 8 }
                        Item { Layout.fillWidth: true }
                        Text { text: "LIGHTER"; color: "#87928A"; font.family: "Bahnschrift"; font.pixelSize: 8 }
                    }

                    Switch {
                        objectName: "adaptiveThresholdSwitch"
                        Layout.fillWidth: true
                        text: "Adaptive threshold"
                        checked: root.viewModel.adaptiveThreshold
                        enabled: root.viewModel.hasImage
                        font.family: "Bahnschrift"
                        font.pixelSize: 10
                        onToggled: root.viewModel.adaptiveThreshold = checked
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        ColumnLayout {
                            Layout.fillWidth: true
                            Text { text: "BLOCK SIZE"; color: "#657269"; font.family: "Bahnschrift"; font.pixelSize: 8; font.bold: true }
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
                            Text { text: "ADAPTIVE C"; color: "#657269"; font.family: "Bahnschrift"; font.pixelSize: 8; font.bold: true }
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

                    Text {
                        text: "MORPHOLOGY"
                        color: "#657269"
                        font.family: "Bahnschrift"
                        font.pixelSize: 8
                        font.bold: true
                    }

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
                            font.pixelSize: 10
                            onActivated: root.viewModel.morphologyMode = currentText.toLowerCase() === "opening" ? "open" : currentText.toLowerCase() === "closing" ? "close" : "none"
                        }
                        SpinBox {
                            objectName: "morphologyKernelInput"
                            Layout.preferredWidth: 90
                            from: 1
                            to: 15
                            stepSize: 2
                            value: root.viewModel.morphologyKernelSize
                            enabled: root.viewModel.hasImage && root.viewModel.morphologyMode !== "none"
                            onValueModified: root.viewModel.morphologyKernelSize = value
                        }
                    }

                    CheckBox {
                        objectName: "lightObstacleCheckBox"
                        Layout.fillWidth: true
                        text: "White source pixels are obstacles"
                        checked: root.viewModel.lightPixelsAreObstacles
                        enabled: root.viewModel.hasImage
                        font.family: "Bahnschrift"
                        font.pixelSize: 9
                        onToggled: root.viewModel.lightPixelsAreObstacles = checked
                    }

                    Item { Layout.fillHeight: true }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 65
                        radius: 4
                        color: "#F4F7F4"
                        border.color: "#E5EAE6"
                        Text {
                            anchors.fill: parent
                            anchors.margins: 10
                            text: "Thresholding is a visual aid, not scene understanding. Inspect the binary preview before using an image as a map."
                            color: "#6F7C73"
                            wrapMode: Text.WordWrap
                            verticalAlignment: Text.AlignVCenter
                            font.family: "Bahnschrift"
                            font.pixelSize: 9
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: "Path planning is not implemented in this phase."
                        color: "#87928A"
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap
                        font.family: "Bahnschrift"
                        font.pixelSize: 9
                    }
                }
            }
        }
    }
}