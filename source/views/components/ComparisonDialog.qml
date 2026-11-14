import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Dialog {
    id: dialog
    required property var viewModel
    signal exportRequested(string format)

    modal: true
    title: "Algorithm comparison"
    width: Math.min(1280, parent ? parent.width - 48 : 1100)
    height: Math.min(900, parent ? parent.height - 48 : 760)
    anchors.centerIn: parent
    standardButtons: Dialog.Close
    padding: 18

    contentItem: ScrollView {
        id: comparisonScroll
        clip: true
        contentWidth: availableWidth
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        ColumnLayout {
            width: comparisonScroll.availableWidth
            spacing: 12

            Flow {
                Layout.fillWidth: true
                spacing: 8
                Repeater {
                    id: algorithmChoices
                    model: dialog.viewModel.availableAlgorithms
                    CheckBox {
                        required property string modelData
                        objectName: "compare" + modelData + "CheckBox"
                        text: modelData
                        checked: true
                        enabled: !dialog.viewModel.searchBusy
                    }
                }
                Text { text: "DLS / IDS depth"; font.pixelSize: 10; color: "#526057" }
                SpinBox {
                    objectName: "comparisonDepthInput"
                    from: 0
                    to: 512
                    value: dialog.viewModel.depthLimit
                    enabled: !dialog.viewModel.searchBusy
                    onValueModified: dialog.viewModel.depthLimit = value
                }
                Button {
                    objectName: "runComparisonButton"
                    text: dialog.viewModel.comparisonBusy ? "Comparing..." : "Run comparison"
                    enabled: dialog.viewModel.canRunSearch
                    onClicked: {
                        var selected = []
                        for (var i = 0; i < algorithmChoices.count; i++) {
                            var choice = algorithmChoices.itemAt(i)
                            if (choice.checked)
                                selected.push(choice.modelData)
                        }
                        dialog.viewModel.runSelectedComparison(selected)
                    }
                }
                Button {
                    objectName: "cancelComparisonButton"
                    text: "Cancel"
                    visible: dialog.viewModel.comparisonBusy
                    onClicked: dialog.viewModel.cancelComparison()
                }
            }

            Text {
                objectName: "comparisonSummary"
                Layout.fillWidth: true
                text: dialog.viewModel.comparisonSummary
                wrapMode: Text.WordWrap
                color: "#526057"
                font.pixelSize: 11
            }

            Text {
                Layout.fillWidth: true
                visible: text.length > 0
                text: dialog.viewModel.errorMessage
                wrapMode: Text.WordWrap
                color: "#9B4632"
                font.pixelSize: 11
            }

            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 3
                    Text {
                        text: "Same grid · same start · same goal"
                        color: "#25342B"
                        font.family: "Bahnschrift"
                        font.pixelSize: 14
                        font.bold: true
                    }
                    Text {
                        text: dialog.viewModel.imageName + " · " + dialog.viewModel.gridDimensions
                        color: "#78847C"
                        font.family: "Bahnschrift"
                        font.pixelSize: 10
                    }
                }
                Button {
                    text: "Export CSV"
                    enabled: dialog.viewModel.hasComparisonResults
                    onClicked: dialog.exportRequested("csv")
                }
                Button {
                    text: "Export JSON"
                    enabled: dialog.viewModel.hasComparisonResults
                    onClicked: dialog.exportRequested("json")
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: timingWarning.implicitHeight + 16
                radius: 4
                color: "#F4F7F4"
                border.color: "#E2E8E3"
                Text {
                    id: timingWarning
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    verticalAlignment: Text.AlignVCenter
                    text: "Execution time varies with system load; compare repeated trials before drawing conclusions. A single run does not establish a universally superior algorithm."
                    color: "#69776E"
                    font.family: "Bahnschrift"
                    font.pixelSize: 9
                    wrapMode: Text.WordWrap
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 34
                color: "#EAF0EB"
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    spacing: 6
                    Text { Layout.fillWidth: true; Layout.minimumWidth: 0; elide: Text.ElideRight; Layout.preferredWidth: 62; text: "ALGORITHM"; font.family: "Bahnschrift"; font.pixelSize: 8; font.bold: true; color: "#56645B" }
                    Text { Layout.fillWidth: true; Layout.minimumWidth: 0; elide: Text.ElideRight; Layout.preferredWidth: 68; text: "SUCCESS"; font.family: "Bahnschrift"; font.pixelSize: 8; font.bold: true; color: "#56645B" }
                    Text { Layout.fillWidth: true; Layout.minimumWidth: 0; elide: Text.ElideRight; Layout.preferredWidth: 74; text: "RATE*"; font.family: "Bahnschrift"; font.pixelSize: 8; font.bold: true; color: "#56645B" }
                    Text { Layout.fillWidth: true; Layout.minimumWidth: 0; elide: Text.ElideRight; Layout.preferredWidth: 72; text: "LENGTH"; font.family: "Bahnschrift"; font.pixelSize: 8; font.bold: true; color: "#56645B" }
                    Text { Layout.fillWidth: true; Layout.minimumWidth: 0; elide: Text.ElideRight; Layout.preferredWidth: 72; text: "COST"; font.family: "Bahnschrift"; font.pixelSize: 8; font.bold: true; color: "#56645B" }
                    Text { Layout.fillWidth: true; Layout.minimumWidth: 0; Layout.preferredWidth: 110; elide: Text.ElideRight; text: "TIME (MS)"; font.family: "Bahnschrift"; font.pixelSize: 8; font.bold: true; color: "#56645B" }
                    Text { Layout.fillWidth: true; Layout.minimumWidth: 0; elide: Text.ElideRight; Layout.preferredWidth: 80; text: "EXPANDED"; font.family: "Bahnschrift"; font.pixelSize: 8; font.bold: true; color: "#56645B" }
                    Text { Layout.fillWidth: true; Layout.minimumWidth: 0; elide: Text.ElideRight; Layout.preferredWidth: 76; text: "PEAK FRONTIER"; font.family: "Bahnschrift"; font.pixelSize: 8; font.bold: true; color: "#56645B" }
                }
            }

            ListView {
                id: resultsList
                objectName: "comparisonResultsTable"
                Layout.fillWidth: true
                Layout.preferredHeight: 188
                clip: true
                model: dialog.viewModel.comparisonRows
                spacing: 2
                delegate: Rectangle {
                    required property var modelData
                    width: resultsList.width
                    height: 34
                    radius: 2
                    color: modelData.success ? "#FFFFFF" : "#FBF3F0"
                    border.color: "#E8ECE9"
                    MouseArea {
                        anchors.fill: parent
                        enabled: !dialog.viewModel.searchBusy
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            dialog.viewModel.inspectComparisonPath(modelData.record_id)
                            dialog.close()
                        }
                    }
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 10
                        spacing: 6
                        Text { Layout.fillWidth: true; Layout.minimumWidth: 0; elide: Text.ElideRight; Layout.preferredWidth: 62; text: modelData.algorithm; font.family: "Bahnschrift"; font.pixelSize: 10; font.bold: true; color: "#2C3B32" }
                        Text { Layout.fillWidth: true; Layout.minimumWidth: 0; elide: Text.ElideRight; Layout.preferredWidth: 68; text: modelData.success ? "Yes" : "No"; font.family: "Bahnschrift"; font.pixelSize: 9; color: modelData.success ? "#286247" : "#9B4632" }
                        Text { Layout.fillWidth: true; Layout.minimumWidth: 0; elide: Text.ElideRight; Layout.preferredWidth: 74; text: (modelData.success_rate * 100).toFixed(0) + "%"; font.family: "Bahnschrift"; font.pixelSize: 9; color: "#526057" }
                        Text { Layout.fillWidth: true; Layout.minimumWidth: 0; elide: Text.ElideRight; Layout.preferredWidth: 72; text: modelData.path_length === null ? "N/A" : modelData.path_length; font.family: "Bahnschrift"; font.pixelSize: 9; color: "#526057" }
                        Text { Layout.fillWidth: true; Layout.minimumWidth: 0; elide: Text.ElideRight; Layout.preferredWidth: 72; text: modelData.path_cost === null ? "N/A" : modelData.path_cost; font.family: "Bahnschrift"; font.pixelSize: 9; color: "#526057" }
                        Text { Layout.fillWidth: true; Layout.minimumWidth: 0; Layout.preferredWidth: 110; elide: Text.ElideRight; text: Number(modelData.execution_time_ms).toFixed(3); font.family: "Bahnschrift"; font.pixelSize: 9; color: "#526057" }
                        Text { Layout.fillWidth: true; Layout.minimumWidth: 0; elide: Text.ElideRight; Layout.preferredWidth: 80; text: modelData.nodes_expanded; font.family: "Bahnschrift"; font.pixelSize: 9; color: "#526057" }
                        Text { Layout.fillWidth: true; Layout.minimumWidth: 0; elide: Text.ElideRight; Layout.preferredWidth: 76; text: modelData.peak_frontier_size; font.family: "Bahnschrift"; font.pixelSize: 9; color: "#526057" }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 180
                Layout.minimumHeight: 120
                radius: 4
                color: "#F6F8F6"
                border.color: "#E5EAE6"
                Canvas {
                    id: timeChart
                    anchors.fill: parent
                    anchors.margins: 12
                    onPaint: {
                        var context = getContext("2d")
                        context.clearRect(0, 0, width, height)
                        var rows = dialog.viewModel.comparisonRows
                        if (rows.length === 0)
                            return
                        var maxTime = 0
                        for (var index = 0; index < rows.length; index++)
                            maxTime = Math.max(maxTime, Number(rows[index].execution_time_ms))
                        var slotWidth = width / rows.length
                        var barWidth = Math.min(42, slotWidth * 0.48)
                        for (var barIndex = 0; barIndex < rows.length; barIndex++) {
                            var value = Number(rows[barIndex].execution_time_ms)
                            var barHeight = maxTime > 0 ? Math.max(2, (value / maxTime) * (height - 24)) : 2
                            var x = barIndex * slotWidth + (slotWidth - barWidth) / 2
                            context.fillStyle = "#39815E"
                            context.fillRect(x, height - 19 - barHeight, barWidth, barHeight)
                            context.fillStyle = "#526057"
                            context.font = "10px sans-serif"
                            context.textAlign = "center"
                            context.fillText(rows[barIndex].algorithm, x + barWidth / 2, height - 4)
                        }
                    }
                    Connections {
                        target: dialog.viewModel
                        function onComparisonChanged() { timeChart.requestPaint() }
                    }
                    Component.onCompleted: requestPaint()
                    onWidthChanged: requestPaint()
                    onHeightChanged: requestPaint()
                }
            }

            Text {
                Layout.fillWidth: true
                text: "Execution time (ms), relative bar heights. Click a table row to inspect its path and explored cells on the map.\n* Each row is one trial: success rate is 100% or 0%. Repeated-run statistics are not computed. Length counts moves; cost is the sum of unit movement costs. N/A means no path was found."
                color: "#7A867E"
                wrapMode: Text.WordWrap
                font.family: "Bahnschrift"
                font.pixelSize: 9
            }
        }
    }
}
