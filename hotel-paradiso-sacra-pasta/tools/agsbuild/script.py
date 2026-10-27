"""Compiling AGS script with the AGS command-line compiler (agscc)."""
import os
import subprocess
import tempfile

# the 3.6.1 editor defines these for a new game; agscc only knows up to v360
EXTRA_MACROS = ['SCRIPT_API_v36026', 'SCRIPT_API_v361']


def compile_script(agscc, source_text, headers, name, workdir):
    """headers: list of (filename, text) in order. Returns the compiled bytes."""
    os.makedirs(workdir, exist_ok=True)
    hpaths = []
    for hname, text in headers:
        p = os.path.join(workdir, hname)
        with open(p, 'w') as f:
            f.write(text)
        hpaths.append(p)
    src = os.path.join(workdir, name)
    with open(src, 'w') as f:
        f.write(source_text)
    out = os.path.splitext(src)[0] + '.o'   # agscc's default output name
    if os.path.exists(out):
        os.remove(out)
    cmd = [agscc, src, '-H', ':'.join(hpaths)]
    for m in EXTRA_MACROS:
        cmd += ['-D', m]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out):
        raise SystemExit('script compile failed: %s\n%s%s' % (name, r.stdout, r.stderr))
    with open(out, 'rb') as f:
        return f.read()
