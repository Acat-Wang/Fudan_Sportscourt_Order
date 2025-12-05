var h = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

function c(t) {
    var e, i, r = "";
    for (e = 0; e + 3 <= t.length; e += 3)
        i = parseInt(t.substring(e, e + 3), 16),
            r += h.charAt(i >> 6) + h.charAt(63 & i);
    for (e + 1 == t.length ? (i = parseInt(t.substring(e, e + 1), 16),
        r += h.charAt(i << 2)) : e + 2 == t.length && (i = parseInt(t.substring(e, e + 2), 16),
        r += h.charAt(i >> 2) + h.charAt((3 & i) << 4)); 0 < (3 & r.length);)
        r += "=";
    return r
}
