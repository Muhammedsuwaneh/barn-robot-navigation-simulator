import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: pane
    property string label: ""
    property string imageSource: ""
    property string emptyMessage: "No image loaded"

    Layout.fillWidth: true
    Layout.fillHeight: true
    Layout.minimumWidth: 180
    radius: 5
    color: "#15221D"
    border.color: "#293A31"
    clip: true

    Image {
        objectName: pane.label === "ORIGINAL INPUT" ? "originalImagePreview" : "processedImagePreview"
        anchors.fill: parent
        anchors.margins: 10
        source: pane.imageSource
        fillMode: Image.PreserveAspectFit
        asynchronous: true
        cache: false
        visible: pane.imageSource.length > 0
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