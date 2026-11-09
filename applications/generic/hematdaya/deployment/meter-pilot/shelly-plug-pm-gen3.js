// Set this to the UUID assigned by the pilot operator. MQTT credentials live in the device settings.
let meterId = "REPLACE_WITH_METER_UUID";
if (meterId === "REPLACE_WITH_METER_UUID") {
  throw new Error("Set the assigned meter UUID before starting the script.");
}

let readingsTopic = "hematdaya/v1/meters/" + meterId + "/readings";

function publishReading() {
  if (!MQTT.isConnected()) return;

  let clock = Shelly.getComponentStatus("sys");
  let meter = Shelly.getComponentStatus("pm1", 0);
  if (!clock || typeof clock.unixtime !== "number" || clock.unixtime <= 0 ||
      !meter || !meter.aenergy || (meter.errors && meter.errors.length > 0)) return;

  let cumulativeWh = meter.aenergy.total;
  if (typeof cumulativeWh !== "number" || !isFinite(cumulativeWh) || cumulativeWh < 0) return;

  let reading = {
    measured_at: clock.unixtime,
    energy_wh: cumulativeWh.toFixed(3),
  };
  MQTT.publish(readingsTopic, JSON.stringify(reading), 1, false);
}

publishReading();
Timer.set(60000, true, publishReading);
