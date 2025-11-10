function setCursor(pos) {
    var txtArea = $('#text');
    txtArea.focus().get(0).setSelectionRange(pos, pos);
}

setCursor(0);