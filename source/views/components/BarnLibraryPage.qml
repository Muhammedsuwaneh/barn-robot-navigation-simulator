import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    required property var viewModel
    signal directoryRequested()
    signal comparisonRequested()

    ScrollView {
        id: pageScroll
        objectName: "barnPageScroll"
        anchors.fill: parent
        clip: true
        contentWidth: availableWidth
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        ColumnLayout {
            width: pageScroll.availableWidth
            spacing: 12

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4
                Text {
                    text: "BARN library"
                    color: "#19251E"
                    font.family: "Bahnschrift"
                    font.pixelSize: 22
                    font.bold: true
                }
                Text {
                    Layout.fillWidth: true
                    text: "Select a raw occupancy or C-space map, then choose start and goal cells."
                    color: "#738078"
                    font.family: "Bahnschrift"
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                ComboBox {
                    id: barnMapSelector
                    objectName: "barnMapSelector"
                    Layout.fillWidth: true
                    Layout.minimumWidth: 100
                    model: root.viewModel.barnMaps
                    textRole: "label"
                    valueRole: "path"
                    enabled: count > 0 && !root.viewModel.searchBusy
                    displayText: count > 0 ? currentText : "Choose a BARN dataset folder"
                }
                Text {
                    text: root.viewModel.barnMaps.length + " maps"
                    color: "#69776E"
                    font.pixelSize: 10
                }
                Button {
                    objectName: "chooseBarnFolderButton"
                    text: "Dataset folder"
                    onClicked: root.directoryRequested()
                    ToolTip.visible: hovered
                    ToolTip.text: root.viewModel.barnDirectory
                }
                Button {
                    objectName: "importBarnMapButton"
                    text: "Import BARN map"
                    enabled: barnMapSelector.count > 0 && barnMapSelector.currentIndex >= 0 && !root.viewModel.searchBusy
                    onClicked: root.viewModel.importBarnMap(barnMapSelector.currentValue)
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: statusText.implicitHeight + 20
                color: root.viewModel.errorMessage.length > 0 ? "#F9ECE8" : "#EAF2ED"
                radius: 4
                Text {
                    id: statusText
                    anchors.fill: parent
                    anchors.margins: 10
                    text: root.viewModel.errorMessage.length > 0 ? root.viewModel.errorMessage
                        : root.viewModel.gridReady ? root.viewModel.statusMessage
                        : "Choose a BARN map and click Import BARN map to begin."
                    color: root.viewModel.errorMessage.length > 0 ? "#9B4632" : "#3F6650"
                    font.family: "Bahnschrift"
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                }
            }

            GridPreviewPane {
                objectName: "barnGridViewer"
                Layout.preferredHeight: Math.max(implicitHeight, root.height - 210)
                viewModel: root.viewModel
                emptyMessage: "Select a BARN map above and click Import BARN map."
                onComparisonRequested: root.comparisonRequested()
            }

            Text {
                Layout.fillWidth: true
                text: root.viewModel.gridReady
                    ? root.viewModel.imageName + " · " + root.viewModel.gridDimensions
                    : "BARN occupancy maps are imported directly. Use Custom images for uploaded images."
                color: "#69776E"
                font.family: "Bahnschrift"
                font.pixelSize: 10
                wrapMode: Text.WordWrap
            }
        }
    }
}
