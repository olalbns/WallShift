# Publish `wallshift-git` to the AUR

WallShift source code is hosted at <https://github.com/olalbns/WallShift>.
The AUR repository contains only `PKGBUILD` and `.SRCINFO`.

## Test locally

```bash
cd ~/WallShift/aur/wallshift-git
rm -rf src pkg
makepkg -si
makepkg --printsrcinfo > .SRCINFO
```

## First AUR publication

Register at <https://aur.archlinux.org/register/>, add your SSH public key in
**My Account**, then use the mandatory `master` branch:

```bash
project_dir="$HOME/WallShift"
git clone ssh://aur@aur.archlinux.org/wallshift-git.git /tmp/wallshift-git-aur
cp "$project_dir/aur/wallshift-git/PKGBUILD" /tmp/wallshift-git-aur/
cp "$project_dir/aur/wallshift-git/.SRCINFO" /tmp/wallshift-git-aur/
cd /tmp/wallshift-git-aur
git checkout -B master
git add PKGBUILD .SRCINFO
git commit -m 'Initial AUR package'
git push -u origin master
```

Once indexed, install with:

```bash
yay -S wallshift-git
```

## Updating the package

After pushing source changes to GitHub:

```bash
cd ~/WallShift/aur/wallshift-git
makepkg --printsrcinfo > .SRCINFO
cp PKGBUILD .SRCINFO /tmp/wallshift-git-aur/
cd /tmp/wallshift-git-aur
git add PKGBUILD .SRCINFO
git commit -m 'Update wallshift-git'
git push
```
