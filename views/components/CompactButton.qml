import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Button {
    id: control
    property bool primary: false
    implicitWidth: Math.max(32, contentItem.implicitWidth + 24)
    implicitHeight: 32
    Layout.minimumWidth: 0
    Layout.preferredHeight: 32
    padding: 6
    horizontalPadding: 12
    hoverEnabled: true
    font.family: "Bahnschrift"
    font.pixelSize: 11

    contentItem: Text {
        text: control.text
        font: control.font
        color: !control.enabled ? "#8A9890"
            : control.primary || control.checked ? "#FFFFFF" : "#304D3E"
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    background: Rectangle {
        radius: 7
        color: !control.enabled ? "#EEF2EF"
            : control.down ? "#123C2D"
            : control.primary || control.checked ? (control.hovered ? "#236548" : "#174D3A")
            : control.hovered ? "#E4EEE7" : "#F4F7F5"
        border.width: control.visualFocus ? 2 : 1
        border.color: control.visualFocus ? "#2D805D" : "#DCE5DF"
    }
}
