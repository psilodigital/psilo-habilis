#!/bin/sh
set -eu

PAPERCLIP_HOME="${PAPERCLIP_HOME:-/paperclip}"
PORT="${PORT:-3100}"
PAPERCLIP_PUBLIC_URL="${PAPERCLIP_PUBLIC_URL:-http://localhost:${PORT}}"
PAPERCLIP_DEPLOYMENT_MODE="${PAPERCLIP_DEPLOYMENT_MODE:-authenticated}"
CONFIG_PATH="${PAPERCLIP_HOME}/instances/default/config.json"
BOOTSTRAP_SENTINEL="${PAPERCLIP_HOME}/instances/default/.bootstrap-ceo-issued"

mkdir -p "${PAPERCLIP_HOME}"

if [ ! -f "${CONFIG_PATH}" ]; then
  echo "[paperclip] No config found, bootstrapping with paperclipai onboard --yes --bind lan"
  paperclipai onboard --yes --bind lan
fi

issue_bootstrap_invite() {
  if [ "${PAPERCLIP_DEPLOYMENT_MODE}" != "authenticated" ]; then
    return 0
  fi

  if [ -f "${BOOTSTRAP_SENTINEL}" ]; then
    return 0
  fi

  attempt=1
  while [ "${attempt}" -le 30 ]; do
    output="$(paperclipai auth bootstrap-ceo --base-url "${PAPERCLIP_PUBLIC_URL}" 2>&1)" && status=0 || status=$?

    case "${output}" in
      *"relation \"instance_user_roles\" does not exist"*|*"start the Paperclip server and run this command again"*)
        sleep 2
        ;;
      *"Created bootstrap CEO invite."*|*"Instance already has an admin user."*)
        printf '%s\n' "${output}"
        date -u +"%Y-%m-%dT%H:%M:%SZ" > "${BOOTSTRAP_SENTINEL}"
        return 0
        ;;
      *)
        echo "[paperclip] bootstrap-ceo attempt ${attempt} returned status ${status}; retrying"
        printf '%s\n' "${output}"
        sleep 2
        ;;
    esac

    attempt=$((attempt + 1))
  done

  echo "[paperclip] bootstrap-ceo did not succeed automatically; run 'paperclipai auth bootstrap-ceo --base-url ${PAPERCLIP_PUBLIC_URL}' in the container if no admin exists yet"
}

issue_bootstrap_invite &

exec paperclipai run --no-repair
