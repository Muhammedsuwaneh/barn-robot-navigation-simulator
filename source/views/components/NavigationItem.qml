import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Button {
    id: control
    property string label: ""
    property string indexLabel: ""
    property bool selected: false

    implicitHeight: 42
    hoverEnabled: true

    background: Rectangle {
        radius: 4
        color: control.selected ? "#EAF2ED" : (control.hovered && control.enabled ? "#F5F7F5" : "transparent")
    }

    contentItem: RowLayout {
        spacing: 11
        Rectangle {
            Layout.preferredWidth: 27
            Layout.preferredHeight: 25
            radius: 4
            color: control.selected ? "#D7E7DC" : "transparent"
            Text {
                anchors.centerIn: parent
                text: control.indexLabel
                color: control.selected ? "#286247" : "#8C9790"
                font.family: "Bahnschrift"
                font.pixelSize: 9
                font.bold: true
            }
        }
        Text {
            Layout.fillWidth: true
            text: control.label
            color: !control.enabled ? "#A8B0AA" : (control.selected ? "#1F5039" : "#526057")
            font.family: "Bahnschrift"
            font.pixelSize: 12
            font.bold: control.selected
        }
        Text {
            visible: !control.enabled
            text: "SOON"
            color: "#A1AAA3"
            font.family: "Bahnschrift"
            font.pixelSize: 8
            font.bold: true
        }
    }
}