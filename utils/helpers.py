"""Small formatting helpers."""
PALETTE = ["#c4f06a", "#c5b3f2", "#ffa3c4", "#84d9e0", "#ffcc62", "#ff9970", "#a9b4f9", "#9be3b0"]


def fmt_int(n):
    return f"{int(n):,}"


def pct(x, digits=1):
    return f"{x * 100:.{digits}f}%"


def pid_color(index):
    if index < len(PALETTE):
        return PALETTE[index]
    import colorsys
    h = (index * 0.618033) % 1.0
    r, g, b = colorsys.hls_to_rgb(h, 0.74, 0.7)
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


def resource_names(m):
    return [chr(65 + i) if i < 26 else f"R{i}" for i in range(m)]
