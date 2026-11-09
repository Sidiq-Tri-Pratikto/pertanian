#!/bin/sh
# Exercise the pilot broker with throwaway credentials on a container's loopback interface.
set -eu

cd "$(dirname "$0")"
test_config="$(mktemp -d)"
trap 'rm -rf "$test_config"' EXIT
mkdir "$test_config/tls"
cp mosquitto.conf pilot.acl.example "$test_config"
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -sha256 -subj /CN=localhost \
  -addext subjectAltName=DNS:localhost \
  -keyout "$test_config/tls/broker.key" -out "$test_config/tls/broker.pem" >/dev/null 2>&1
# The isolated container reads only this temporary directory. These files are never used by a real broker.
chmod 755 "$test_config" "$test_config/tls"
chmod 644 "$test_config/tls/broker.key"

docker run --rm -i --pull=never --network none --user 1883:1883 \
  --mount "type=bind,src=$test_config,dst=/mosquitto/config,readonly" \
  --entrypoint /bin/sh eclipse-mosquitto:2.0 -es <<'BROKER_TEST'
umask 077
meter_a=11111111-1111-4111-8111-111111111111
meter_b=22222222-2222-4222-8222-222222222222
topic_a="hematdaya/v1/meters/$meter_a/readings"
topic_b="hematdaya/v1/meters/$meter_b/readings"
worker=hematdaya-worker
sample='{"measured_at":1783000000,"energy_wh":"12.375"}'

sed 's|/mosquitto/config/pilot\.|/tmp/pilot.|g' /mosquitto/config/mosquitto.conf >/tmp/mosquitto.conf
cp /mosquitto/config/pilot.acl.example /tmp/pilot.acl
printf '\nuser %s\ntopic write %s\n' "$meter_b" "$topic_b" >>/tmp/pilot.acl
mosquitto_passwd -b -c /tmp/pilot.passwd "$worker" worker-test-only
mosquitto_passwd -b /tmp/pilot.passwd "$meter_a" meter-a-test-only
mosquitto_passwd -b /tmp/pilot.passwd "$meter_b" meter-b-test-only

mosquitto -c /tmp/mosquitto.conf >/tmp/broker.log 2>&1 &
broker_pid=$!
cleanup() {
  result=$?
  if [ "$result" -ne 0 ]; then
    cat /tmp/broker.log /tmp/publisher.log >&2 2>/dev/null || true
  fi
  kill "$broker_pid" 2>/dev/null || true
}
trap cleanup EXIT

publish() {
  mosquitto_pub -h localhost -p 8883 --cafile /mosquitto/config/tls/broker.pem -V mqttv5 -q 1 "$@"
}

subscribe() {
  mosquitto_sub -h localhost -p 8883 --cafile /mosquitto/config/tls/broker.pem -V mqttv5 -q 1 "$@"
}

expect_denied() {
  reply="$(publish -d "$@" 2>&1 || true)"
  if ! printf '%s\n' "$reply" | grep -Eq 'RC:135|Publish .*Not authorized'; then
    printf '%s\n' 'Expected the broker to deny a forbidden publication.' >&2
    exit 1
  fi
}

attempt=0
until publish -u "$meter_a" -P meter-a-test-only -t "$topic_a" -m "$sample" 2>/dev/null; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 20 ]; then
    cat /tmp/broker.log >&2
    exit 1
  fi
  sleep 0.2
done

expect_denied -u "$meter_a" -P meter-a-test-only -t "$topic_b" -m "$sample"
expect_denied -u "$meter_a" -P meter-a-test-only -t "hematdaya/v1/meters/$meter_a/command" -m 'forbidden'
expect_denied -u "$worker" -P worker-test-only -t "$topic_a" -m "$sample"

if publish -t "$topic_a" -m "$sample" >/dev/null 2>&1; then
  printf '%s\n' 'Expected an anonymous connection to be denied.' >&2
  exit 1
fi
if mosquitto_pub -h 127.0.0.1 -p 8883 --cafile /mosquitto/config/tls/broker.pem \
  -V mqttv5 -q 1 -u "$meter_a" -P meter-a-test-only -t "$topic_a" -m "$sample" >/dev/null 2>&1; then
  printf '%s\n' 'Expected a TLS hostname mismatch to be denied.' >&2
  exit 1
fi

subscribe -u "$meter_a" -P meter-a-test-only -t "$topic_b" -C 1 -W 2 >/tmp/foreign-subscriber 2>/dev/null &
foreign_subscriber_pid=$!
sleep 0.3
publish -u "$meter_b" -P meter-b-test-only -t "$topic_b" -m "$sample"
wait "$foreign_subscriber_pid" || true
test ! -s /tmp/foreign-subscriber

subscribe -u "$worker" -P worker-test-only -t 'hematdaya/v1/meters/+/readings' -C 1 -W 5 >/tmp/worker-reading &
worker_pid=$!
mkfifo /tmp/meter-stream
publish -d -u "$meter_a" -P meter-a-test-only -t "$topic_a" -l </tmp/meter-stream >/tmp/publisher.log 2>&1 &
publisher_pid=$!
exec 3>/tmp/meter-stream
sleep 0.3
printf '%s\n' "$sample" >&3
wait "$worker_pid"
test "$(cat /tmp/worker-reading)" = "$sample"

# Remove the ACL as well as the password, because password reload does not disconnect an active publisher.
sed "/^user $meter_a$/,+1d" /tmp/pilot.acl >/tmp/pilot.next
mv /tmp/pilot.next /tmp/pilot.acl
mosquitto_passwd -D /tmp/pilot.passwd "$meter_a"
kill -HUP "$broker_pid"
sleep 0.3
if publish -u "$meter_a" -P meter-a-test-only -t "$topic_a" -m "$sample" >/dev/null 2>&1; then
  printf '%s\n' 'Expected the revoked meter to be denied a fresh connection.' >&2
  exit 1
fi
subscribe -u "$worker" -P worker-test-only -t "$topic_a" -C 1 -W 2 >/tmp/revoked-reading 2>/dev/null &
revocation_subscriber_pid=$!
sleep 0.3
printf '%s\n' '{"measured_at":1783000060,"energy_wh":"13.375"}' >&3
exec 3>&-
wait "$publisher_pid" || true
wait "$revocation_subscriber_pid" || true
# Depending on the broker version, reload rejects the next publish or disconnects the active client.
grep -Eq 'RC:135|CONNACK \(135\)|Publish .*Not authorized' /tmp/publisher.log
test ! -s /tmp/revoked-reading

printf '%s\n' 'Passed TLS, worker delivery, cross-meter isolation, denied control/publication, and active revocation.'
BROKER_TEST
