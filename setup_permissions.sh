#!/usr/bin/env bash
# setup-permissions.sh
# Lets the user logged in at this computer create virtual keyboards/mice
# through /dev/uinput. Needed on the Pop!_OS (client) machine only.
set -euo pipefail

RULE_FILE=/etc/udev/rules.d/99-parasite-uinput.rules
MODULE_FILE=/etc/modules-load.d/parasite-uinput.conf
RULE='KERNEL=="uinput", SUBSYSTEM=="misc", TAG+="uaccess", OPTIONS+="static_node=uinput"'

usage() {
  cat <<'EOF'
setup-permissions.sh - allow ProjectParasite to type and click on this machine

WHAT IT DOES
  Gives the user logged in at this computer permission to open /dev/uinput,
  the kernel interface for creating virtual keyboards and mice.
  Without it, client.py fails with "PermissionError: /dev/uinput".

  It changes exactly two files, and loads one kernel module:
    /etc/udev/rules.d/99-parasite-uinput.rules   (the permission rule)
    /etc/modules-load.d/parasite-uinput.conf     (load 'uinput' at boot)

USAGE
  ./setup-permissions.sh              Install (asks before changing anything)
  ./setup-permissions.sh -y           Install without the confirmation prompt
  ./setup-permissions.sh --check      Only report the current status
  ./setup-permissions.sh --uninstall  Remove everything this script added
  ./setup-permissions.sh -h | --help  Show this help

STEPS
  1. Run this on the Pop!_OS machine, as your normal user (NOT with sudo).
     The script calls sudo itself, only for the lines that need it.
  2. Read the summary and type y.
  3. Run  ./setup-permissions.sh --check  . Every line should say ok.
  4. Start the client:  uv run python -m projectparasite.client <MAC_IP>

IMPORTANT
  * Run it from the desktop session on the machine (or a terminal inside it).
    The permission goes to the user at the physical seat, so a plain SSH
    session may still get "permission denied".
  * After this, any program running as your user can type and click as you.
    Only run software you trust. See the WARNING section in README.md.
  * Never use "chmod 666 /dev/uinput" as a shortcut. It opens the device
    to every account and process on the machine.

TROUBLESHOOTING
  "No such file /dev/uinput"   ->  sudo modprobe uinput
  Still permission denied      ->  log out and back in, then --check again
  Want it gone                 ->  ./setup-permissions.sh --uninstall, then reboot
EOF
}

die() { echo "error: $*" >&2; exit 1; }

require_linux_and_sudo() {
  [[ "$(uname -s)" == "Linux" ]] || die "this script is for the Linux (Pop!_OS) machine, not macOS."
  [[ "${EUID}" -ne 0 ]] || die "do not run this with sudo. Run it as your normal user; it calls sudo itself."
  command -v sudo >/dev/null 2>&1 || die "sudo is not installed."
  command -v udevadm >/dev/null 2>&1 || die "udevadm not found (is this a systemd/udev system?)."
}

confirm() {
  local ans
  read -r -p "$1 [y/N] " ans
  [[ "${ans}" == "y" || "${ans}" == "Y" ]]
}

do_check() {
  local ok=0
  if [[ -f "${RULE_FILE}" ]]; then echo "ok       udev rule present"; else echo "MISSING  udev rule (${RULE_FILE})"; ok=1; fi
  if [[ -f "${MODULE_FILE}" ]]; then echo "ok       uinput loads at boot"; else echo "MISSING  boot module file (${MODULE_FILE})"; ok=1; fi
  if [[ -e /dev/uinput ]]; then echo "ok       /dev/uinput exists"; else echo "MISSING  /dev/uinput (try: sudo modprobe uinput)"; ok=1; fi
  if [[ -w /dev/uinput ]]; then
    echo "ok       you can write to /dev/uinput"
  else
    echo "MISSING  you cannot write to /dev/uinput yet (log out/in, or run from the desktop session)"
    ok=1
  fi
  [[ -e /dev/uinput ]] && ls -l /dev/uinput
  return "${ok}"
}

do_install() {
  cat <<EOF
This will let the user logged in at this computer create virtual
keyboards and mice (/dev/uinput). Any program that user runs will then be
able to type and click as them.

Changes (needs sudo):
  write  ${RULE_FILE}
  write  ${MODULE_FILE}
  load   kernel module 'uinput'
  reload udev rules

EOF
  if [[ "${ASSUME_YES}" -ne 1 ]]; then
    confirm "Continue?" || { echo "Aborted. Nothing changed."; exit 1; }
  fi

  printf '%s\n' "${RULE}" | sudo tee "${RULE_FILE}" >/dev/null
  printf '%s\n' "uinput" | sudo tee "${MODULE_FILE}" >/dev/null
  sudo modprobe uinput
  sudo udevadm control --reload-rules
  sudo udevadm trigger
  sudo udevadm settle || true

  echo
  echo "Done. Checking status:"
  if do_check; then
    echo
    echo "All good. You can now run the client."
  else
    echo
    echo "Installed, but access is not active yet. Log out and back in, then run: $0 --check"
    exit 1
  fi
}

do_uninstall() {
  cat <<EOF
This will remove:
  ${RULE_FILE}
  ${MODULE_FILE}

EOF
  if [[ "${ASSUME_YES}" -ne 1 ]]; then
    confirm "Continue?" || { echo "Aborted. Nothing changed."; exit 1; }
  fi
  sudo rm -f "${RULE_FILE}" "${MODULE_FILE}"
  sudo udevadm control --reload-rules
  sudo udevadm trigger
  echo "Removed. Reboot to fully reset (the uinput module stays loaded until then)."
}

ACTION=install
ASSUME_YES=0
for arg in "$@"; do
  case "${arg}" in
    -h|--help)   usage; exit 0 ;;
    --check)     ACTION=check ;;
    --uninstall) ACTION=uninstall ;;
    -y|--yes)    ASSUME_YES=1 ;;
    *) echo "error: unknown option '${arg}'" >&2; echo "Try: $0 --help" >&2; exit 2 ;;
  esac
done

require_linux_and_sudo
case "${ACTION}" in
  install)   do_install ;;
  check)     do_check ;;
  uninstall) do_uninstall ;;
esac