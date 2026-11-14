import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Dialogs
import QtQuick.Layouts 1.15
import "components"

ApplicationWindow {
    id: window
    objectName: "mainWindow"
    required property var navigationViewModel
    required property var barnViewModel
    readonly property var activeViewModel: navigationViewModel.activeSection === "barn"
        ? barnViewModel : navigationViewModel
    visible: true
    flags: Qt.Window | Qt.FramelessWindowHint
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
            objectName: "customTitleBar"
            Layout.fillWidth: true
            Layout.preferredHeight: 60
            color: "#FFFFFF"
            border.color: "#DDE4DE"
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 24
                anchors.rightMargin: 16
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
                        text: window.title
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

                Button {
                    id: closeWindowButton
                    objectName: "closeWindowButton"
                    Layout.preferredWidth: 32
                    Layout.preferredHeight: 32
                    Layout.leftMargin: 10
                    text: "\u00d7"
                    hoverEnabled: true
                    Accessible.name: "Close window"
                    onClicked: window.close()

                    contentItem: Text {
                        text: closeWindowButton.text
                        color: "#FFFFFF"
                        font.pixelSize: 22
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        radius: width / 2
                        color: closeWindowButton.down ? "#A82632"
                            : closeWindowButton.hovered ? "#D94350" : "#C93442"
                        border.width: closeWindowButton.visualFocus ? 2 : 0
                        border.color: "#174D3A"
                    }
                    ToolTip.visible: hovered
                    ToolTip.text: "Close window"
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            Rectangle {
                Layout.fillHeight: true
                Layout.preferredWidth: 188
                color: "#FFFFFF"
                border.color: "#DDE4DE"
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.topMargin: 22
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
                        objectName: "customImagesNavigation"
                        Layout.fillWidth: true
                        label: "Custom images"
                        indexLabel: "01"
                        selected: window.navigationViewModel.activeSection === "workspace"
                        onClicked: window.navigationViewModel.selectSection("workspace")
                    }

                    NavigationItem {
                        objectName: "barnLibraryNavigation"
                        Layout.fillWidth: true
                        label: "BARN library"
                        indexLabel: "02"
                        selected: window.navigationViewModel.activeSection === "barn"
                        onClicked: window.navigationViewModel.selectSection("barn")
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
                Layout.margins: 18
                spacing: 14

                StackLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    currentIndex: window.navigationViewModel.activeSection === "barn" ? 1 : 0

                    ImageProcessingPanel {
                        objectName: "customImagesPage"
                        viewModel: window.navigationViewModel
                        onComparisonRequested: comparisonDialog.open()
                        onLoadImageRequested: imageDialog.open()
                    }

                    BarnLibraryPage {
                        objectName: "barnLibraryPage"
                        viewModel: window.barnViewModel
                        onComparisonRequested: comparisonDialog.open()
                        onDirectoryRequested: barnFolderDialog.open()
                    }
                }
            }
        }
    }

    FolderDialog {
        id: barnFolderDialog
        objectName: "barnFolderDialog"
        title: "Select BARN dataset folder (or grid_files / cspace_files)"
        onAccepted: window.barnViewModel.scanBarnDirectory(selectedFolder.toString())
    }

    ComparisonDialog {
        id: comparisonDialog
        objectName: "comparisonDialog"
        parent: Overlay.overlay
        viewModel: window.activeViewModel
        onExportRequested: function(format) {
            comparisonExportDialog.exportFormat = format
            comparisonExportDialog.open()
        }
    }

    FileDialog {
        id: comparisonExportDialog
        objectName: "comparisonExportDialog"
        property string exportFormat: "csv"
        title: "Export comparison to a new file"
        fileMode: FileDialog.SaveFile
        defaultSuffix: exportFormat
        nameFilters: exportFormat === "csv" ? ["CSV files (*.csv)"] : ["JSON files (*.json)"]
        onAccepted: window.activeViewModel.exportComparison(selectedFile.toString(), exportFormat)
    }

    FileDialog {
        id: imageDialog
        title: "Select an environment image"
        fileMode: FileDialog.OpenFile
        nameFilters: ["Image files (*.png *.jpg *.jpeg)", "PNG images (*.png)", "JPEG images (*.jpg *.jpeg)"]
        onAccepted: window.navigationViewModel.loadImage(selectedFile.toString())
    }
}
