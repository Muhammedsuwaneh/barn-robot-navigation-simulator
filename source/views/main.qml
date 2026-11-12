import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Dialogs
import QtQuick.Layouts 1.15
import "components"

ApplicationWindow {
    id: window
    objectName: "mainWindow"
    required property var navigationViewModel
    visible: true
    width: 1440
    height: 900
    minimumWidth: 1080
    minimumHeight: 720
    title: window.navigationViewModel.applicationName
    color: "#F1F4F1"
    font.family: "Bahnschrift"
    font.pixelSize: 14

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 72
            color: "#FFFFFF"
            border.color: "#DDE4DE"
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 24
                anchors.rightMargin: 28
                spacing: 14

                Rectangle {
                    Layout.preferredWidth: 38
                    Layout.preferredHeight: 38
                    radius: 8
                    color: "#174D3A"

                    Text {
                        anchors.centerIn: parent
                        text: "NR"
                        color: "#FFFFFF"
                        font.family: window.font.family
                        font.pixelSize: 13
                        font.bold: true
                    }
                }

                ColumnLayout {
                    spacing: 2
                    Text {
                        text: "NAVIGATION LAB"
                        color: "#17231D"
                        font.family: window.font.family
                        font.pixelSize: 15
                        font.bold: true
                    }
                    Text {
                        text: window.navigationViewModel.phaseLabel
                        color: "#728078"
                        font.family: window.font.family
                        font.pixelSize: 10
                        font.letterSpacing: 1
                    }
                }

                Item { Layout.fillWidth: true }

                Rectangle {
                    Layout.preferredWidth: 106
                    Layout.preferredHeight: 30
                    radius: 15
                    color: "#EAF2ED"
                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 7
                        Rectangle {
                            Layout.preferredWidth: 7
                            Layout.preferredHeight: 7
                            radius: 4
                            color: "#2D805D"
                        }
                        Text {
                            text: "OFFLINE"
                            color: "#286247"
                            font.family: window.font.family
                            font.pixelSize: 10
                            font.bold: true
                            font.letterSpacing: 1
                        }
                    }
                }

                Rectangle {
                    Layout.preferredWidth: 1
                    Layout.preferredHeight: 28
                    color: "#E1E6E2"
                }

                Text {
                    text: "LOCAL SESSION"
                    color: "#78837C"
                    font.family: window.font.family
                    font.pixelSize: 10
                    font.letterSpacing: 1
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            Rectangle {
                Layout.fillHeight: true
                Layout.preferredWidth: 220
                color: "#FFFFFF"
                border.color: "#DDE4DE"
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.topMargin: 28
                    anchors.leftMargin: 16
                    anchors.rightMargin: 16
                    anchors.bottomMargin: 18
                    spacing: 8

                    Text {
                        Layout.leftMargin: 10
                        Layout.bottomMargin: 8
                        text: "WORKSPACE"
                        color: "#849088"
                        font.family: window.font.family
                        font.pixelSize: 10
                        font.bold: true
                        font.letterSpacing: 1.2
                    }

                    NavigationItem {
                        Layout.fillWidth: true
                        label: "Navigation"
                        indexLabel: "01"
                        selected: window.navigationViewModel.activeSection === "workspace"
                        onClicked: window.navigationViewModel.selectSection("workspace")
                    }

                    NavigationItem {
                        Layout.fillWidth: true
                        label: "Map library"
                        indexLabel: "02"
                        enabled: false
                    }

                    NavigationItem {
                        Layout.fillWidth: true
                        label: "Run history"
                        indexLabel: "03"
                        enabled: false
                    }

                    Item { Layout.fillHeight: true }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 84
                        radius: 6
                        color: "#F4F7F4"
                        border.color: "#E5EAE6"

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            spacing: 5
                            Text {
                                text: "SESSION MODE"
                                color: "#87928A"
                                font.family: window.font.family
                                font.pixelSize: 9
                                font.bold: true
                                font.letterSpacing: 1
                            }
                            Text {
                                text: "Offline / static maps"
                                color: "#29372F"
                                font.family: window.font.family
                                font.pixelSize: 12
                            }
                            Text {
                                text: "No sensors connected"
                                color: "#89938C"
                                font.family: window.font.family
                                font.pixelSize: 10
                            }
                        }
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.margins: 24
                spacing: 18

                ImageProcessingPanel {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    viewModel: window.navigationViewModel
                    onLoadImageRequested: imageDialog.open()
                }

                RowLayout {
                    visible: false
                    Layout.fillWidth: true
                    Layout.preferredHeight: 58
                    spacing: 12

                    ColumnLayout {
                        spacing: 3
                        Text {
                            text: "Navigation workspace"
                            color: "#19251E"
                            font.family: window.font.family
                            font.pixelSize: 23
                            font.bold: true
                        }
                        Text {
                            text: "STATIC ENVIRONMENT / PATH PLANNING"
                            color: "#738078"
                            font.family: window.font.family
                            font.pixelSize: 10
                            font.letterSpacing: 1
                        }
                    }

                    Item { Layout.fillWidth: true }

                    Text {
                        text: window.navigationViewModel.statusMessage
                        color: "#78847C"
                        font.family: window.font.family
                        font.pixelSize: 11
                    }
                }

                RowLayout {
                    visible: false
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 16

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.minimumWidth: 440
                        radius: 7
                        color: "#FFFFFF"
                        border.color: "#DDE4DE"
                        border.width: 1

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 14
                            spacing: 12

                            RowLayout {
                                Layout.fillWidth: true
                                Text {
                                    text: "ENVIRONMENT VIEW"
                                    color: "#45534A"
                                    font.family: window.font.family
                                    font.pixelSize: 10
                                    font.bold: true
                                    font.letterSpacing: 1
                                }
                                Item { Layout.fillWidth: true }
                                Text {
                                    text: "GRID / 4-CONNECTED"
                                    color: "#849088"
                                    font.family: window.font.family
                                    font.pixelSize: 9
                                    font.letterSpacing: 0.6
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                radius: 4
                                clip: true
                                color: "#15221D"

                                Canvas {
                                    id: mapGrid
                                    anchors.fill: parent
                                    onPaint: {
                                        var context = getContext("2d")
                                        context.clearRect(0, 0, width, height)
                                        context.strokeStyle = "#26362F"
                                        context.lineWidth = 1
                                        for (var x = 0; x <= width; x += 32) {
                                            context.beginPath()
                                            context.moveTo(x, 0)
                                            context.lineTo(x, height)
                                            context.stroke()
                                        }
                                        for (var y = 0; y <= height; y += 32) {
                                            context.beginPath()
                                            context.moveTo(0, y)
                                            context.lineTo(width, y)
                                            context.stroke()
                                        }
                                    }
                                    onWidthChanged: requestPaint()
                                    onHeightChanged: requestPaint()
                                }

                                ColumnLayout {
                                    anchors.centerIn: parent
                                    spacing: 11

                                    Rectangle {
                                        Layout.alignment: Qt.AlignHCenter
                                        Layout.preferredWidth: 48
                                        Layout.preferredHeight: 48
                                        radius: 24
                                        color: "#20342B"
                                        border.color: "#385246"
                                        Text {
                                            anchors.centerIn: parent
                                            text: "+"
                                            color: "#91B5A0"
                                            font.family: window.font.family
                                            font.pixelSize: 23
                                            font.weight: Font.Light
                                        }
                                    }
                                    Text {
                                        Layout.alignment: Qt.AlignHCenter
                                        text: "No environment loaded"
                                        color: "#E5ECE7"
                                        font.family: window.font.family
                                        font.pixelSize: 15
                                        font.bold: true
                                    }
                                    Text {
                                        Layout.alignment: Qt.AlignHCenter
                                        text: "Map rendering will be available in a later phase."
                                        color: "#98A89E"
                                        font.family: window.font.family
                                        font.pixelSize: 11
                                    }
                                }

                                Rectangle {
                                    anchors.left: parent.left
                                    anchors.top: parent.top
                                    anchors.margins: 12
                                    width: 66
                                    height: 24
                                    radius: 3
                                    color: "#24362D"
                                    Text {
                                        anchors.centerIn: parent
                                        text: "NO MAP"
                                        color: "#A8B9AE"
                                        font.family: window.font.family
                                        font.pixelSize: 9
                                        font.bold: true
                                        font.letterSpacing: 0.7
                                    }
                                }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 20
                                Text {
                                    text: "SOURCE  NONE"
                                    color: "#77837B"
                                    font.family: window.font.family
                                    font.pixelSize: 9
                                    font.letterSpacing: 0.6
                                }
                                Text {
                                    text: "DIMENSIONS  --"
                                    color: "#77837B"
                                    font.family: window.font.family
                                    font.pixelSize: 9
                                    font.letterSpacing: 0.6
                                }
                                Item { Layout.fillWidth: true }
                                Text {
                                    text: "OFFLINE"
                                    color: "#438261"
                                    font.family: window.font.family
                                    font.pixelSize: 9
                                    font.bold: true
                                    font.letterSpacing: 0.7
                                }
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillHeight: true
                        Layout.preferredWidth: 304
                        Layout.minimumWidth: 280
                        radius: 7
                        color: "#FFFFFF"
                        border.color: "#DDE4DE"
                        border.width: 1

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 18
                            spacing: 13

                            RowLayout {
                                Layout.fillWidth: true
                                Text {
                                    text: "RUN CONFIGURATION"
                                    color: "#35443B"
                                    font.family: window.font.family
                                    font.pixelSize: 10
                                    font.bold: true
                                    font.letterSpacing: 1
                                }
                                Item { Layout.fillWidth: true }
                                Text {
                                    text: "LOCKED"
                                    color: "#9A6A32"
                                    font.family: window.font.family
                                    font.pixelSize: 9
                                    font.bold: true
                                    font.letterSpacing: 0.8
                                }
                            }

                            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: "#E8ECE9" }

                            Text {
                                text: "ENVIRONMENT IMAGE"
                                color: "#657269"
                                font.family: window.font.family
                                font.pixelSize: 9
                                font.bold: true
                                font.letterSpacing: 0.7
                            }

                            Button {
                                id: loadMapButton
                                objectName: "loadMapButton"
                                Layout.fillWidth: true
                                Layout.preferredHeight: 40
                                enabled: false
                                text: "Load environment image"
                                font.family: window.font.family
                                font.pixelSize: 11
                                background: Rectangle {
                                    radius: 4
                                    color: "#F1F4F1"
                                    border.color: "#DDE4DE"
                                }
                                contentItem: Text {
                                    text: loadMapButton.text
                                    color: "#8B958E"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    font: loadMapButton.font
                                }
                            }

                            Text {
                                Layout.fillWidth: true
                                text: "Image import is not part of this phase."
                                color: "#909A93"
                                font.family: window.font.family
                                font.pixelSize: 10
                                wrapMode: Text.WordWrap
                            }

                            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: "#E8ECE9" }

                            Text {
                                text: "SEARCH ALGORITHM"
                                color: "#657269"
                                font.family: window.font.family
                                font.pixelSize: 9
                                font.bold: true
                                font.letterSpacing: 0.7
                            }

                            ComboBox {
                                objectName: "algorithmSelector"
                                Layout.fillWidth: true
                                Layout.preferredHeight: 38
                                enabled: false
                                model: ["Select an algorithm"]
                                font.family: window.font.family
                                font.pixelSize: 11
                            }

                            Text {
                                text: "Start and goal"
                                color: "#657269"
                                font.family: window.font.family
                                font.pixelSize: 9
                                font.bold: true
                                font.letterSpacing: 0.7
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 10
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 5
                                    Text { text: "START"; color: "#87928A"; font.family: window.font.family; font.pixelSize: 9; font.bold: true }
                                    TextField {
                                        Layout.fillWidth: true
                                        enabled: false
                                        placeholderText: "Not set"
                                        font.family: window.font.family
                                        font.pixelSize: 11
                                    }
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 5
                                    Text { text: "GOAL"; color: "#87928A"; font.family: window.font.family; font.pixelSize: 9; font.bold: true }
                                    TextField {
                                        Layout.fillWidth: true
                                        enabled: false
                                        placeholderText: "Not set"
                                        font.family: window.font.family
                                        font.pixelSize: 11
                                    }
                                }
                            }

                            Item { Layout.fillHeight: true }

                            Button {
                                id: runNavigationButton
                                objectName: "runNavigationButton"
                                Layout.fillWidth: true
                                Layout.preferredHeight: 42
                                enabled: false
                                text: "Run navigation"
                                font.family: window.font.family
                                font.pixelSize: 12
                                font.bold: true
                                background: Rectangle {
                                    radius: 4
                                    color: "#A8B8AE"
                                }
                                contentItem: Text {
                                    text: runNavigationButton.text
                                    color: "#FFFFFF"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    font: runNavigationButton.font
                                }
                            }

                            Text {
                                Layout.fillWidth: true
                                text: "Navigation execution becomes available after search is implemented."
                                color: "#909A93"
                                horizontalAlignment: Text.AlignHCenter
                                wrapMode: Text.WordWrap
                                font.family: window.font.family
                                font.pixelSize: 9
                            }
                        }
                    }
                }

                RowLayout {
                    visible: false
                    Layout.fillWidth: true
                    Layout.preferredHeight: 88
                    spacing: 12

                    MetricCard {
                        Layout.fillWidth: true
                        label: "EXPANDED NODES"
                        value: "--"
                        detail: "No run data"
                        accent: "#54856A"
                    }
                    MetricCard {
                        Layout.fillWidth: true
                        label: "PATH LENGTH"
                        value: "--"
                        detail: "No route available"
                        accent: "#B38343"
                    }
                    MetricCard {
                        Layout.fillWidth: true
                        label: "ELAPSED TIME"
                        value: "--"
                        detail: "No run data"
                        accent: "#5C7F8B"
                    }
                }
            }
        }
    }

    FileDialog {
        id: imageDialog
        title: "Select an environment image"
        fileMode: FileDialog.OpenFile
        nameFilters: ["Image files (*.png *.jpg *.jpeg)", "PNG images (*.png)", "JPEG images (*.jpg *.jpeg)"]
        onAccepted: window.navigationViewModel.loadImage(selectedFile.toString())
    }
}