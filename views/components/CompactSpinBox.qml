import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

SpinBox {
    id: control
    implicitWidth: 104
    implicitHeight: 32
    Layout.preferredHeight: 32
    font.family: "Bahnschrift"
    font.pixelSize: 11

    up.indicator: Rectangle {
        x: control.width - width
        width: 24
        height: control.height
        radius: 5
        color: control.up.pressed ? "#D7E7DC" : "#EAF0EC"
        Text {
            anchors.centerIn: parent
            text: "+"
            color: control.enabled ? "#304D3E" : "#98A39C"
            font.pixelSize: 17
        }
    }
    down.indicator: Rectangle {
        width: 24
        height: control.height
        radius: 5
        color: control.down.pressed ? "#D7E7DC" : "#EAF0EC"
        Text {
            anchors.centerIn: parent
            text: "\u2212"
            color: control.enabled ? "#304D3E" : "#98A39C"
            font.pixelSize: 17
        }
    }
    background: Rectangle {
        radius: 5
        color: control.enabled ? "#FFFFFF" : "#F3F6F4"
        border.color: control.activeFocus ? "#2D805D" : "#DCE5DF"
    }
}
