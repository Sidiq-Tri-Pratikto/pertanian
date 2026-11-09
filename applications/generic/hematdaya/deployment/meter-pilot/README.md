# Shelly Plug PM Gen3 private bench

This runbook covers the single-channel Shelly Plug PM Gen3 on an isolated lab network. The pilot is disabled by default. Keep the lab credentials, certificates, database, and data separate from public or saved-user deployments.

## Broker and site setup

1. Prepare a private broker host reachable by the meter and the worker. Use Mosquitto 2.0, a server certificate with the broker hostname in its subject alternative names, and the issuing CA trusted by the worker and Shelly. Restrict port 8883 to the lab network.
2. Set `PILOT_CONFIG` to the absolute path of a private configuration directory. Copy [mosquitto.conf](mosquitto.conf) and [pilot.acl.example](pilot.acl.example) there, renaming the ACL copy to `pilot.acl`. Place the server certificate and key at `tls/broker.pem` and `tls/broker.key` within that directory. Set `METER_ID="$(uuidgen | tr '[:upper:]' '[:lower:]')"` and replace the sample UUID on both ACL lines with its value. Add one explicit stanza for each meter.
3. Run `mosquitto_passwd -c "$PILOT_CONFIG/pilot.passwd" hematdaya-worker` to create the password file once. Run `mosquitto_passwd "$PILOT_CONFIG/pilot.passwd" "$METER_ID"` for each meter. Use independent random passwords and the interactive prompts. Restrict the key, ACL, and password file to the broker service account. The worker can subscribe to all reading topics; each device credential can publish only to its own reading topic. Serve no other applications or command topics on this broker.
4. Start the broker with that directory mounted at `/mosquitto/config`. For the official Docker image, run the broker as UID 1883 and make its configuration readable to that UID. Set `LAB_BROKER_BIND` to the lab interface address before running:

   ```sh
   docker run --rm --name hematdaya-meter-broker --user 1883:1883 \
     --mount "type=bind,src=$PILOT_CONFIG,dst=/mosquitto/config,readonly" \
     -p "$LAB_BROKER_BIND:8883:8883" --entrypoint /bin/sh eclipse-mosquitto:2.0 \
     -c 'exec mosquitto -c /mosquitto/config/mosquitto.conf'
   ```

5. In the [API directory](../../applications/hematdaya-api/README.md), apply database migrations and set `METER_PILOT_ENABLED=true` for the lab API and worker. Set `METER_MQTT_HOST` to the certificate hostname, `METER_MQTT_PORT` to 8883 (the default), `METER_MQTT_CA_FILE` to the issuing CA file, and `METER_MQTT_USERNAME` and `METER_MQTT_PASSWORD` to the worker credential. Use the same lab database for the API, worker, and operator commands. Launch the API normally and run the following from its directory:

   ```sh
   uv run python -m app.meter_pilot.operator provision --site-name "Meter lab" --meter-id "$METER_ID"
   uv run python -m app.meter_pilot.worker
   ```

   Save the returned site ID for revocation or renewal with `uv run python -m app.meter_pilot.operator renew-access --site-id "$SITE_ID"`. Renewal replaces the previous code. Give the eight-hour pilot access code to the authorized user through a secure channel. Enter the code in HematDaya to start the meter setup. The app never needs the broker passwords.

## Device setup

1. Confirm the model is **Shelly Plug PM Gen3**. Record the firmware version and installation. Connect the meter to the private lab Wi-Fi and confirm its clock is synchronized.
2. In the local Shelly device settings, enable MQTT with the broker hostname and port 8883. Use the assigned UUID as the username and its meter password. Select TLS with CA validation. Use the built-in trust bundle for a publicly trusted certificate or load the lab CA and select the user CA. Disable MQTT RPC, MQTT control, RPC notifications, and component status notifications.
3. Create a Shelly script from [shelly-plug-pm-gen3.js](shelly-plug-pm-gen3.js). Replace the initial UUID placeholder with the same assigned UUID. Save the script, enable startup, and start it while HematDaya is waiting for the first reading.

The script publishes cumulative active energy from `PM1:0` every 60 seconds, including unchanged or zero values. It sends each sample to `hematdaya/v1/meters/<meter_id>/readings` at QoS 1, with retain disabled. The body contains an observation time in Unix seconds and energy in Wh as a decimal string, for example `{"measured_at":1783000000,"energy_wh":"12.375"}`. There is no device or site field in the body. The broker account and exact topic determine the meter identity. Firmware MQTT online indicators, if emitted, are outside the reading ACL and are ignored. The first reading establishes the counter baseline. A later reading from the same counter segment supplies interval energy.

## Evidence and shutdown

- Run the [script test](verify-shelly-script.cjs) with `node --test verify-shelly-script.cjs`. With the official Mosquitto 2.0 image already present, run `sh verify-broker.sh` to check TLS, access limits, and revocation on a container loopback network with throwaway credentials.
- On the physical meter, record at least three consecutive samples at zero load and at steady load. Check the timestamps and observe the first reading, binding confirmation, and interval energy in the app. Compare the meter's interval kWh and HematDaya's kWh against an independent reference over the same time window. Record the reference model, tolerance agreed before the test, load, window, values, and difference. Pause telemetry for longer than two expected intervals and verify the app marks the last reading as stale. Keep the pilot private until these checks and the release gates pass.
- To revoke a meter, run `uv run python -m app.meter_pilot.operator revoke-meter --meter-id "$METER_ID"`. Remove its stanza from `pilot.acl` and remove the password with `mosquitto_passwd -D "$PILOT_CONFIG/pilot.passwd" "$METER_ID"`. Reload the broker with SIGHUP after updating both files. Removing only the password can leave an existing connection active. Verify that the connected client cannot publish and a new connection with the old credentials fails.
- To revoke the operator bearer, run `uv run python -m app.meter_pilot.operator revoke-access --site-id "$SITE_ID"`. Set `METER_PILOT_ENABLED=false` and restart the API with that setting to close the pilot, then stop the worker and broker.

References: [Shelly Plug PM Gen3](https://shelly-api-docs.shelly.cloud/gen2/Devices/Gen3/ShellyPlugPMG3/), [PM1 energy fields](https://shelly-api-docs.shelly.cloud/gen2/ComponentsAndServices/PM1/), [Shelly MQTT configuration](https://shelly-api-docs.shelly.cloud/gen2/ComponentsAndServices/Mqtt/), [Mosquitto configuration](https://www.mosquitto.org/man/mosquitto-conf-5.html).
