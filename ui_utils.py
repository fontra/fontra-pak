from PyQt6.QtWidgets import QWidget

def refreshStyle(widget):
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()

    for child in widget.findChildren(QWidget):
        child.style().unpolish(child)
        child.style().polish(child)
        child.update()

def addClass(widget, *class_names: str):
    current = (widget.property("class") or "").split()
    changed = False
    for name in class_names:
        if name not in current:
            current.append(name)
            changed = True
    if changed:
        widget.setProperty("class", " ".join(current))
        refreshStyle(widget)

def removeClass(widget, *class_names: str):
    current = (widget.property("class") or "").split()
    changed = False
    for name in class_names:
        if name in current:
            current.remove(name)
            changed = True
    if changed:
        widget.setProperty("class", " ".join(current))
        refreshStyle(widget)
