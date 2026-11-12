import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: card
    property string label: ""
    property string value: "--"
    property string detail: ""
    property color accent: "#54856A"

    Layout.preferredHeight: 88
    radius: 6
    color: "#FFFFFF"
    border.color: "#DDE4DE"
    border.width: 1

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 16
        anchors.rightMargin: 16
        spacing: 12

        Rectangle {
            Layout.preferredWidth: 3
            Layout.preferredHeight: 42
            radius: 2
            color: card.accent
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            Text {
                text: card.label
                color: "#768279"
                font.family: "Bahnschrift"
                font.pixelSize: 9
                font.bold: true
                font.letterSpacing: 0.7
            }
            Text {
                text: card.detail
                color: "#A0A9A2"
                font.family: "Bahnschrift"
                font.pixelSize: 10
            }
        }

        Text {
            text: card.value
            color: "#26352C"
            font.family: "Bahnschrift"
            font.pixelSize: 20
            font.bold: true
        }
    }
}